from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import SimpleJsonOutputParser
from langgraph.types import Command, interrupt
import json
from agent.prompt import plan_prompt
from agent.tools import tool_desc
from agent.llm import create_chat_client
from utils.spinner import with_spinner

@with_spinner(text="规划中...")
async def planner_node(state: AgentState):
  messages = state.get("messages", [])
  failed_plans = state.get("failed_plans", [])
  reviewer_comment = state.get("reviewer_comment", "")
  prompt = plan_prompt.substitute(
    tool_desc=tool_desc,
    failed_plans=json.dumps(failed_plans)
  )
  if reviewer_comment:
    feedback_block = f"""
      ===== 上一轮评审驳回反馈（你必须修正这个问题） =====
      {reviewer_comment}
      请根据上面的问题重新生成正确的JSON计划，不要再犯同样错误。
    """
  else: feedback_block = ""

  try:
    plan_result = (await create_chat_client(temperature=0).ainvoke(
      [SystemMessage(content=prompt + feedback_block)] + messages
    ))
    plan_json = SimpleJsonOutputParser().parse(plan_result.content)
    print("plan", plan_json)
    return {
      "messages": [plan_result],
      "plans": plan_json,
      "plan_text": plan_result.content,
      "last_llm_error": None
    }
  except json.JSONDecodeError as e:
    # LLM输出不是JSON
    err_text = f"[LLM_PARSE_ERROR] JSON解析失败: {str(e)}"
    Command(
      goto="reset_plan",
      update={
        "last_llm_error": err_text,
        "messages": [
          HumanMessage(content=err_text)
        ]
      }
    )
  except Exception as e:
    # 网络、超时、鉴权、服务断开等所有LLM调用异常
    err_msg = f"LLM调用异常：{type(e).__name__}: {str(e)}"
    Command(
      goto="error_node",
      update={
        "last_llm_error": f"[LLM_RUNTIME_ERROR] {err_msg}"
      }
    )

def error_node(state: AgentState):
  last_llm_error = state.get("last_llm_error", "")
  if last_llm_error:
    print("LLM错误", last_llm_error)

plan_builder = StateGraph(AgentState)
plan_builder.add_node("planner", planner_node)

plan_builder.add_edge(START, "planner")
plan_builder.add_edge("planner", END)

plan_graph = plan_builder.compile()
