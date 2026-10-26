from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Command, interrupt
from typing import Annotated, List
import uuid
from agent import tools as agent_tools
from utils.util import overwrite_reducer
from agent.state import AgentState
from agent import child_agent

# 高危工具集合
DANGER_TOOLS = {"write_file"}
MAX_RETRY_COUNT = 3

def reviewer_route(state: AgentState):
    reviewer_result = state.get("reviewer_result", "")
    plans = state.get("plans", [])
    if reviewer_result == "approve":
      if plans:
        return "executor"
      else:
        return "reflection"
    else:
      return "reset_plan"
  
def should_continue_agent(state: AgentState):
    """判断Agent是否需要继续调用工具"""
    plans = state.get("plans", [])
    failed_plans = state.get("failed_plans", [])
    replan_count = state.get("replan_count", 0)
    if plans: return "executor"
    else:
      if failed_plans:
        if replan_count >= MAX_RETRY_COUNT:
          return "reflection"
        else:
          return "reset_plan"
      else: return "reflection"

def executor(state: AgentState):
  plans = state.get("plans", []).copy()
  failed_plans = state.get("failed_plans", []).copy()
  if not plans:
    return Command(goto="summary")
  
  plan = plans[0]
  print("执行计划", plan)
  plan["id"] = plan.get("id", uuid.uuid4().hex)
  plan["retry_count"] = plan.get("retry_count", 0)

  tool_plan = plan.copy()
  tool_plan.pop("retry_count")

  tool_name = plan["name"]
  if(tool_name == "write_file"):
    file_path = plan["args"]["file_path"]
    file_cont = agent_tools.read_file.invoke(file_path)
    is_tool_err = bool(file_cont and file_cont.startswith("[TOOL_ERROR]"))
    if file_cont and not is_tool_err:
      value = interrupt({"file_path": file_path})
      if value is False:
        print(f"用户拒绝了 {file_path} 的修改")
        plan["error_msg"] = f"用户拒绝了 {file_path} 的修改"
        failed_plans.append(plan.copy())
        return {
          "messages": [AIMessage(content="", tool_calls=[tool_plan])],
          "plans": plans[1:],
          "failed_plans": failed_plans
        }
  return {
    "messages": [AIMessage(content="", tool_calls=[tool_plan])]
  }

def after_call_tool(state: AgentState):
  print("计划执行结束")
  last_msg = state["messages"][-1]
  plans = state.get("plans", []).copy()
  plan = plans[0]
  failed_plans = state.get("failed_plans", []).copy()
  tool_results = state.get("tool_results", []).copy()
  if isinstance(last_msg, ToolMessage):
    content = last_msg.content
    is_tool_err = content.startswith("[TOOL_ERROR]")

    if is_tool_err:
      if plan["retry_count"] >= MAX_RETRY_COUNT:
        # 重试次数过多，直接放弃
        first = plans.pop(0)
        first["error_msg"] = content
        failed_plans.append(first)
        tool_results.append({"task": first, "result": content})
        return {
          "plans": plans,
          "failed_plans": failed_plans,
        }
      else:
        plan["retry_count"] += 1
        return {"plans": plans}
    else:
      # 直接消费
      first = plans.pop(0)
      tool_results.append({"task": first, "result": content})
      return {
        "plans": plans,
        "tool_results": tool_results
      }
    
  return {}

def reset_plan(state: AgentState):
  print("重新规划")
  replan_count = state.get("replan_count", 0)
  replan_count += 1
  return {
    "replan_count": replan_count,
    "failed_plans": []
  }

def reflection_route(state: AgentState):
  reflection_result = state.get("reflection_result", "stop")
  reflection_count = state.get("reflection_count", 0)
  if reflection_result == "stop":
    return "summary"
  else:
    if reflection_count >= MAX_RETRY_COUNT:
      return "summary"
    else:
      return "reset_reflection"

def reset_reflection(state: AgentState):
  print("重新反思审查")
  reflection_count = state.get("reflection_count", 0)
  reflection_count += 1
  return {
    "reflection_count": reflection_count,
    "replan_count": 0
  }

def error_node(state: AgentState):
  last_llm_error = state.get("last_llm_error", "")
  if last_llm_error:
    print("LLM错误", last_llm_error)

def before_end(state: AgentState):
  print("任务结束")
  return {
    "query": None,
    "plan_text": None,
    "plans": [],
    "failed_plans": [],
    "replan_count": 0,
    "reflection_count": 0,
    "reviewer_result": None,
    "reviewer_comment": None,
    "reflection_result": None,
    "reflection_comment": None,
    "tool_results": []
  }

def build_mcp_agent_graph(tools: list):
  agent_builder = StateGraph(AgentState)

  agent_builder.add_node("planner", child_agent.plan_graph)
  agent_builder.add_node("reviewer", child_agent.reviewer_graph)
  agent_builder.add_node("tools", ToolNode(tools))
  agent_builder.add_node("executor", executor)
  agent_builder.add_node("reset_plan", reset_plan)
  agent_builder.add_node("after_call_tool", after_call_tool)
  agent_builder.add_node("reflection", child_agent.reflection_graph)
  agent_builder.add_node("reset_reflection", reset_reflection)
  agent_builder.add_node("summary", child_agent.summary_graph)
  agent_builder.add_node("error", error_node)
  agent_builder.add_node("before_end", before_end)


  agent_builder.add_edge(START, "planner")
  agent_builder.add_edge("planner", "reviewer")
  agent_builder.add_conditional_edges(
    "reviewer",
    reviewer_route,
    {"reset_plan":"reset_plan", "executor": "executor", "reflection": "reflection"}
  )
  agent_builder.add_edge("executor", "tools")
  agent_builder.add_edge("tools", "after_call_tool")
  agent_builder.add_conditional_edges(
    "after_call_tool",
    should_continue_agent,
    {"reflection":"reflection", "executor": "executor", "reset_plan": "reset_plan", "summary": "summary"}
  )

  agent_builder.add_conditional_edges(
    "reflection",
    reflection_route,
    {"reset_reflection": "reset_reflection", "summary": "summary"}
  )
  agent_builder.add_edge("reset_plan", "planner")
  agent_builder.add_edge("reset_reflection", "planner")
  agent_builder.add_edge("summary", "before_end")
  agent_builder.add_edge("error", "before_end")
  agent_builder.add_edge("before_end", END)

  return agent_builder


async def initialize():
  return build_mcp_agent_graph(agent_tools.ALL_AGENT_TOOLS,)