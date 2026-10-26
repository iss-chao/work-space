from langchain_deepseek import ChatDeepSeek
from utils.config import API_KEY, BASE_URL, MODEL_NAME

def create_chat_client(**kwargs) -> ChatDeepSeek:
  return ChatDeepSeek(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    **kwargs
  )

chat_client = ChatDeepSeek(
  model=MODEL_NAME,
  api_key=API_KEY,
  base_url=BASE_URL,
  temperature=0
)