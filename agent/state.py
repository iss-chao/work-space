from langgraph.graph import MessagesState
from typing import Annotated, List
from utils.util import overwrite_reducer

class AgentState(MessagesState):
  query: Annotated[str | None, "用户原始提问", overwrite_reducer]

  plan_text: Annotated[str | None, "planner输出的原始plan文本", overwrite_reducer]
  plans: Annotated[List[dict] | None, "当前待执行任务队列，[{name, args}]", overwrite_reducer]
  failed_plans: Annotated[List[dict] | None, "执行失败的任务列表，用于回传给planner补救规划", overwrite_reducer]

  replan_count: Annotated[int, "全局重规划次数，>=3 就进入LLM反思兜底", overwrite_reducer]
  reflection_count: Annotated[int, "全局反思次数，>=3 就进入LLM反思兜底", overwrite_reducer]

  reviewer_result: Annotated[str | None, "reviewer评审结论", overwrite_reducer]
  reviewer_comment: Annotated[str | None, "reviewer评审备注、驳回理由", overwrite_reducer]

  reflection_result: Annotated[str | None, "reflection反思结论", overwrite_reducer]
  reflection_comment: Annotated[str | None, "reflection反思备注、驳回理由", overwrite_reducer]

  tool_results: Annotated[List[dict] | None, "全部工具执行日志，成功失败都保存，供reflection节点复盘", overwrite_reducer]

  last_llm_error: Annotated[str | None, "最近一次LLM错误信息", overwrite_reducer]