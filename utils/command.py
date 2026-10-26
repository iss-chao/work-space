import argparse
from dotenv import set_key, unset_key
from utils.config import API_KEY, BASE_URL, MODEL_NAME, ENV_PATH, __version__

def parse_cli_args():
    parser = argparse.ArgumentParser(description="AI Agent CLI工具", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--version", "-v", action="store_true", help="打印版本号并退出")
    parser.add_argument("--set_key", type=str, metavar="KEY", help="设置LLM API Key，保存到.env")
    parser.add_argument("--show_key", action="store_true", help="显示LM API Key")
    parser.add_argument("--rm_key", action="store_true", help="移除LLM API Key")
    parser.add_argument("--set_url", type=str, metavar="KEY", help="设置LLM Base Url，保存到.env")
    parser.add_argument("--show_url", action="store_true", help="显示LM Base Url")
    parser.add_argument("--rm_url", action="store_true", help="移除LLM Base Url")
    parser.add_argument("--set_model", type=str, metavar="KEY", help="设置LLM MODEL，保存到.env")
    parser.add_argument("--show_model", action="store_true", help="显示LM MODEL")
    parser.add_argument("--rm_model", action="store_true", help="移除LLM MODEL")
    return parser.parse_args()


def handle_commands(args):
    args = parse_cli_args()
    if args.version:
        print(f"Agent Studio CLI v{__version__}")
        return True
    if args.set_key:
        set_key(ENV_PATH, "API_KEY", args.set_key)
        return True
    if args.show_key:
        print(API_KEY)
        return True
    if args.rm_key:
        unset_key(ENV_PATH, "API_KEY")
        return True
    if args.set_url:
        set_key(ENV_PATH, "BASE_URL", args.set_url)
        return True
    if args.show_url:
        print(BASE_URL)
        return True
    if args.rm_url:
        unset_key(ENV_PATH, "BASE_URL")
        return True
    if args.set_model:
        set_key(ENV_PATH, "MODEL_NAME", args.set_model)
        return True
    if args.show_model:
        print(MODEL_NAME)
        return True
    if args.rm_model:
        unset_key(ENV_PATH, "MODEL_NAME")
        return True
    return False