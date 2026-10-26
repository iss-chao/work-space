import sys
from utils.color import *
from utils.config import __version__

def print_banner():
    banner = f"""{BLUE}
╔═══════════════════════════════════════════════╗
║           ██████╗ ██╗   ██╗ ██████╗           ║
║           ██╔══██╗╚██╗ ██╔╝██╔═══██╗          ║
║           ██████╔╝ ╚████╔╝ ██║   ██║          ║
║           ██╔══██╗  ╚██╔╝  ██║   ██║          ║
║           ██║  ██║   ██║   ╚██████╔╝          ║
║           ╚═╝  ╚═╝   ╚═╝    ╚═════╝           ║
╠═══════════════════════════════════════════════╣
║  Agent Studio CLI                             ║
║  Version: {__version__}                               ║
║  Mode:    Local Dev                           ║
║  Status:  MCP Server Ready                    ║
╚═══════════════════════════════════════════════╝
{RESET}"""
    print(banner)
    sys.stdout.flush()