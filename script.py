import asyncio
import sys
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from utils.color import *
from utils.command import handle_commands
from utils.print_banner import print_banner
from utils.config import BASE_URL, API_KEY


async def main():
    handled = handle_commands(sys.argv)
    if handled:
        return

    # 校验配置
    if not API_KEY:
        print(f"\n{YELLOW}[WARN] API_KEY 未配置，请使用 --set_key 设置{RESET}")
        return
    if not BASE_URL:
        print(f"\n{YELLOW}[WARN] BASE_URL 未配置，请使用 --set_url 设置{RESET}")
        return

    print_banner()

    from agent.agent_graph import initialize

    memory = MemorySaver()
    agent_builder = await initialize()
    graph = agent_builder.compile(checkpointer=memory)
    config = {"configurable": {"thread_id": 1}}

    while True:
        try:
            text = await asyncio.to_thread(input, ">>>")
            if (text == ""):
                sys.stdout.write("\033[1A\033[2K")
                sys.stdout.flush()
                continue
            res = await graph.ainvoke({"messages": [HumanMessage(content=text)], "query": text}, config=config)
            await recover_interrupt(res, graph, config)
        except Exception as e:
            print(e)


async def recover_interrupt(res, graph, config):
    current_res = res
    # 循环持续处理所有连续中断，消除递归
    while "__interrupt__" in current_res:
        file_name = current_res["__interrupt__"][0].value["file_path"]
        confirm = await asyncio.to_thread(input, f"\n{BRIGHT}准备写入" + file_name + "文件，是否允许执行? y/n >")
        resume = True if confirm.strip().lower() == "y" else False
        current_res = await graph.ainvoke(Command(resume=resume), config=config)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        ...