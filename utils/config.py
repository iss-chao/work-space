# utils/config.py
import os
import sys
from dotenv import load_dotenv

# -------- 版本统一，只在这里改 --------
__version__ = "0.1.0"

# 自动获取exe/脚本所在目录，打包后自动在exe同级找.env
def get_app_root():
    if hasattr(os, "getattr") and hasattr(sys, "_MEIPASS"):
        # pyinstaller打包后
        return os.path.dirname(sys.executable)
    else:
        # 开发模式：当前脚本目录
        return os.path.abspath(os.curdir)

APP_ROOT = get_app_root()
ENV_PATH = os.path.join(APP_ROOT, ".env")

# 只加载一次！
load_dotenv(ENV_PATH)

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
