import threading
from functools import wraps
import time
import sys

def spinner(stop_event: threading.Event, p:str = "规划中"):
  chars = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
  i = 0
  times = 0
  while not stop_event.is_set():
    sys.stdout.write(f"\r{p}... 用时 {times / len(chars)} 秒 {chars[i%len(chars)]}")
    sys.stdout.flush()
    i +=1
    time.sleep(0.1)
    times += 1
  sys.stdout.write("\r" + " "*60 + "\r")
  sys.stdout.flush()


def with_spinner(text="规划中..."):
  def decorator(async_node_func):
    @wraps(async_node_func)
    async def wrapper(*args, **kwargs):
      stop_event = threading.Event()
      t = threading.Thread(target=spinner, args=(stop_event, text))
      t.start()
      try:
        # 执行原来的节点函数
        return await async_node_func(*args, **kwargs)
      finally:
        # 不管正常返回还是抛异常，一定会停掉loading
        stop_event.set()
        t.join()
    return wrapper
  return decorator