from langchain.tools import tool
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader, Docx2txtLoader
import sys
import os
import asyncio
from pathlib import Path
from utils.error_type import TOOL_ERROR


WORKSPACE = Path.cwd().resolve()
# 自动创建文件夹
WORKSPACE.mkdir(exist_ok=True, parents=True)


def safe_resolve(
    rel_path: str,
    check_in_workspace: bool = True,    # 是否校验不越出工作区（几乎所有工具都开）
    check_exists: bool = True,          # 是否校验文件/目录必须存在
    check_is_file: bool | None = None,  # True=必须是文件；False=必须是目录；None=不判断类型
) -> tuple[bool, Path, str]:
    """
    统一路径安全校验，按需开启校验规则
    :param rel_path: 传入的相对工作区路径
    :param check_in_workspace: 开启防路径穿越校验，默认True
    :param check_exists: 校验目标必须存在，默认True
    :param check_is_file:
        True → 要求是文件
        False → 要求是文件夹
        None → 不校验是文件还是文件夹
    返回 (ok:bool, target:Path, err_msg:str)
    """
    target = (WORKSPACE / rel_path).resolve()
    workspace_abs = WORKSPACE.resolve()

    # 1. 路径穿越校验（最高优先级，大部分工具必开）
    if check_in_workspace and not target.is_relative_to(workspace_abs):
        return False, target, f"{TOOL_ERROR} 路径不在工作区内"

    # 2. 存在性校验
    if check_exists:
        if not target.exists():
            return False, target, f"{TOOL_ERROR} 文件/目录不存在"

    # 3. 文件/目录类型校验
    if check_is_file is not None:
        if not target.exists():
            # 如果前面关了check_exists，这里不存在就跳过类型判断
            pass
        elif check_is_file is True and not target.is_file():
            return False, target, f"{TOOL_ERROR} 不是文件"
        elif check_is_file is False and not target.is_dir():
            return False, target, f"{TOOL_ERROR} 不是目录"

    return True, target, ""


@tool
def list_dir(dir_path: str) -> str:
    """
    列出指定目录内的文件和文件夹
    只能在工作区内操作
    :param dir_path: 相对workspace的目录路径
    """
    ok, target, err_msg = safe_resolve(
        dir_path,
        check_in_workspace=True,
        check_exists=True,
        check_is_file=False
    )
    if not ok:
        return err_msg
    try:
        items = []
        for item in target.iterdir():
            prefix = "[DIR]" if item.is_dir() else "[FILE]"
            items.append(f"{prefix} {item.relative_to(WORKSPACE)}")
        return "\n".join(items)
    except Exception as e:
        return f"{TOOL_ERROR}【目录遍历异常】{str(e)}"


@tool
def read_file(file_path: str) -> str:
    """
    读取文本文件内容
    只能在工作区内操作
    :param file_path: 相对workspace的文件路径
    """
    ok, target, err_msg = safe_resolve(
        file_path,
        check_in_workspace=True,
        check_exists=True,
        check_is_file=True
    )
    if not ok:
        return err_msg

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return target.read_text(encoding="gbk")
        except UnicodeDecodeError:
            return f"{TOOL_ERROR}【读取失败】该文件是二进制文件，不是文本，无法读取"
    except Exception as e:
        return f"{TOOL_ERROR}【读取异常】{str(e)}"


@tool
def read_pdf(file_path: str) -> str:
    """
    读取PDF文件
    只能在工作区内操作
    :param file_path: 相对workspace的文件路径
    """
    ok, target, err_msg = safe_resolve(
        file_path,
        check_in_workspace=True,
        check_exists=True,
        check_is_file=True
    )
    if not ok:
        return err_msg

    try:
        loader = PyMuPDFLoader(target)
        docs = loader.load()
        docs_text = "\n".join([doc.page_content for doc in docs])
        return docs_text
    except Exception as e:
        return f"{TOOL_ERROR}【PDF读取异常】{str(e)}"


@tool
def read_docx(file_path: str) -> str:
    """
    读取docx文档文件
    只能在工作区内操作
    :param file_path: 相对workspace的文件路径
    """
    ok, target, err_msg = safe_resolve(
        file_path,
        check_in_workspace=True,
        check_exists=True,
        check_is_file=True
    )
    if not ok:
        return err_msg

    try:
        loader = Docx2txtLoader(target)
        docs = loader.load()
        docs_text = "\n".join([doc.page_content for doc in docs])
        return docs_text
    except Exception as e:
        return f"{TOOL_ERROR}【docx读取异常】{str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    写入文件内容，文件不存在会新建
    只能在工作区内操作
    :param file_path: 相对workspace的文件路径
    :param content: 写入的文本内容
    """
    ok, target, err_msg = safe_resolve(
        file_path,
        check_in_workspace=True,
        check_exists=False,
        check_is_file=None
    )
    if not ok:
        return err_msg

    try:
        target.write_text(content, encoding="utf-8")
        return f"写入成功: {file_path}"
    except PermissionError:
        return f"{TOOL_ERROR} 权限不足，无法写入"
    except Exception as e:
        return f"{TOOL_ERROR}【写入异常】{str(e)}"


@tool
def mkdir(dir_path: str) -> str:
    """
    创建文件夹
    只能在工作区内操作
    :param dir_path: 相对workspace的目录路径
    """
    ok, target, err_msg = safe_resolve(
        dir_path,
        check_in_workspace=True,
        check_exists=False,
        check_is_file=False
    )
    if not ok:
        return err_msg

    try:
        target.mkdir(exist_ok=True, parents=True)
        return f"目录创建成功: {dir_path}"
    except Exception as e:
        return f"{TOOL_ERROR}【创建目录异常】{str(e)}"


@tool
def touch(file_path: str) -> str:
    """
    创建空文件
    只能在工作区内操作
    :param file_path: 相对workspace的文件路径
    """
    ok, target, err_msg = safe_resolve(
        file_path,
        check_in_workspace=True,
        check_exists=False,
        check_is_file=None
    )
    if not ok:
        return err_msg

    try:
        target.touch(exist_ok=True)
        return f"空文件创建成功: {file_path}"
    except Exception as e:
        return f"{TOOL_ERROR}【touch创建失败】{str(e)}"


@tool
def rename_file(source: str, target: str) -> str:
    """
    对文件或者文件夹进行重命名操作
    Args:
        source: 原始文件/文件夹相对路径（相对于当前工作目录）
        target: 新名称（仅名字，不是完整路径）
    """
    # 源路径校验
    ok_src, src, err_src = safe_resolve(
        source,
        check_in_workspace=True,
        check_exists=True,
        check_is_file=None
    )
    if not ok_src:
        return err_src

    parent_dir = src.parent
    dst = (parent_dir / target).resolve()
    # 目标路径防穿越
    if not dst.is_relative_to(WORKSPACE):
        return f"{TOOL_ERROR} 目标路径超出工作区，禁止操作"
    if dst.exists():
        return f"{TOOL_ERROR} 失败：目标名称已经存在 {target}，不能覆盖，请换名字"

    try:
        src.rename(dst)
        return f"重命名成功：{src.name} → {target}"
    except Exception as e:
        return f"{TOOL_ERROR} 重命名异常：{str(e)}"


@tool
async def npm_shell(command: str, cwd: str = ".") -> str:
    """
    在工作目录执行shell命令，仅允许npm相关命令，用于安装依赖、启动项目。
    Args:
        command: 需要执行的shell命令，例如 npm install，npm run dev
        cwd: 执行命令的目录，相对workspace路径，必须是文件夹
    """
    ok, cwd_target, err_msg = safe_resolve(
        cwd,
        check_in_workspace=True,
        check_exists=True,
        check_is_file=False
    )
    if not ok:
        return err_msg

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd_target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        stdout_text = stdout.decode("utf-8", errors="ignore")
        stderr_text = stderr.decode("utf-8", errors="ignore")
        return f"""命令: {command}
          stdout:
          {stdout_text}
          stderr:
          {stderr_text}
          返回码: {proc.returncode}
          返回码0代表执行成功，非0代表报错"""
    except asyncio.TimeoutError:
        return f"{TOOL_ERROR} 命令执行超时(120s)"
    except Exception as e:
        return f"{TOOL_ERROR} 命令执行异常：{str(e)}"


ALL_AGENT_TOOLS = [list_dir, read_file, read_pdf, read_docx, write_file, mkdir, touch, rename_file, npm_shell]
tool_desc = "\n".join([f"名称：{t.name}，描述：{t.description}" for t in ALL_AGENT_TOOLS])
