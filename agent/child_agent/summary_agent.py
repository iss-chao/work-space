from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from langchain_core.messages import SystemMessage
import json
from agent.prompt import summary_prompt
from agent.llm import create_chat_client
from utils.util import get_last_human_context_msgs


async def summary_node(state: AgentState):
  print("总结")
  user_query = state.get("query", "")
  messages = get_last_human_context_msgs(state.get("messages", []))
  failed_plans = state.get("failed_plans", [])
  tool_results = state.get("tool_results", [])
  prompt = summary_prompt.substitute(
    user_query=user_query,
    failed_plans=json.dumps(failed_plans),
    tool_results=json.dumps(tool_results)
  )
  summary_result = (await create_chat_client().ainvoke(
    [SystemMessage(content=prompt)] + messages
  ))
  print("summary", summary_result.content)
  return {"messages": [summary_result]}


summary_builder = StateGraph(AgentState)
summary_builder.add_node("summary", summary_node)

summary_builder.add_edge(START, "summary")
summary_builder.add_edge("summary", END)

summary_graph = summary_builder.compile()
