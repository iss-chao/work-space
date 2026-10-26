from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import SimpleJsonOutputParser
import json
from agent.prompt import reviewer_prompt
from agent.tools import tool_desc
from agent.llm import create_chat_client
from utils.util import get_last_human_context_msgs
from utils.spinner import with_spinner

@with_spinner(text="审查中...")
async def reviewer_node(state: AgentState):
  plans = state.get("plans", [])
  messages = get_last_human_context_msgs(state.get("messages", []))
  prompt = reviewer_prompt.substitute(
    tool_desc=tool_desc,
    plans=json.dumps(plans)
  )
  reviewer_text = await create_chat_client().ainvoke(
    [SystemMessage(content=prompt)] + messages
  )
  results = SimpleJsonOutputParser().parse(reviewer_text.content)
  print("reviewer", results)
  return {
    "reviewer_result": results["verdict"],
    "reviewer_comment": results["comment"] if results["verdict"] == "reject" else ""
  }

reviewer_builder = StateGraph(AgentState)
reviewer_builder.add_node("planner", reviewer_node)

reviewer_builder.add_edge(START, "planner")
reviewer_builder.add_edge("planner", END)

reviewer_graph = reviewer_builder.compile()