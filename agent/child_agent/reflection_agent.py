from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import SimpleJsonOutputParser
import json
from agent.prompt import reflection_prompt
from agent.llm import create_chat_client
from utils.util import get_last_human_context_msgs


async def reflection(state: AgentState):
  """
    {
      "verdict": "retry" | "stop",
      "feedback": "给planner的诊断反馈"
    }
  """
  print("反思审查")
  user_query = state.get("query", "")
  messages = get_last_human_context_msgs(state.get("messages", []))
  failed_plans = state.get("failed_plans", [])
  tool_results = state.get("tool_results", [])
  prompt = reflection_prompt.substitute(
    user_query=user_query,
    failed_plans=json.dumps(failed_plans),
    tool_results=json.dumps(tool_results)
  )
  reflection_text = await create_chat_client().ainvoke(
    [SystemMessage(content=prompt)] + messages
  )
  results = SimpleJsonOutputParser().parse(reflection_text.content)
  print("reflection", results)
  return {
    "reflection_result": results["verdict"],
    "reflection_comment": results["feedback"] if results["verdict"] == "retry" else ""
  }

reflection_builder = StateGraph(AgentState)
reflection_builder.add_node("reflection", reflection)

reflection_builder.add_edge(START, "reflection")
reflection_builder.add_edge("reflection", END)

reflection_graph = reflection_builder.compile()