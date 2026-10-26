from langchain_core.messages import HumanMessage, AIMessage

def overwrite_reducer(_, new):
  return new


def get_last_human_context_msgs(messages):
  last_human_idx = None
  for idx, msg in reversed(list(enumerate(messages))):
    if isinstance(msg, HumanMessage):
      last_human_idx = idx
      break

  if last_human_idx is not None:
    context_msgs = messages[last_human_idx:]
  else:
    context_msgs = messages
  return context_msgs
