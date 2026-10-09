"""内置工具实现：read_text_file / write_text_file / list_directory。

这些工具是 ToolForge 的初始能力，不经过沙箱测试与安全审查（因为是人工编写的可信代码）。
它们通过 ToolRecord 注册到 ToolRegistry，与动态生成的工具使用相同的调用路径。
"""

from pathlib import Path

from app.models.tool import ToolRecord, ToolSpec, ToolStatus

# ---- 工具源码字符串（注册到 Registry 时使用） ----

READ_TEXT_FILE_CODE = '''
def read_text_file(path: str) -> str:
    """读取文本文件内容并返回。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
'''

WRITE_TEXT_FILE_CODE = '''
def write_text_file(path: str, content: str) -> bool:
    """将内容写入文本文件，返回是否成功。"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True
'''

LIST_DIRECTORY_CODE = '''
def list_directory(path: str) -> list[str]:
    """列出目录中的文件和子目录名。"""
    import os
    return sorted(os.listdir(path))
'''


# ---- ToolSpec 定义 ----

READ_TEXT_FILE_SPEC = ToolSpec(
    name="read_text_file",
    description="读取文本文件内容并返回字符串。",
    input_schema={"path": "str"},
    output_schema={"return": "str"},
    constraints=["只读", "UTF-8 编码"],
)

WRITE_TEXT_FILE_SPEC = ToolSpec(
    name="write_text_file",
    description="将字符串内容写入文件，返回是否成功。",
    input_schema={"path": "str", "content": "str"},
    output_schema={"return": "bool"},
    constraints=["覆盖写入", "UTF-8 编码"],
)

LIST_DIRECTORY_SPEC = ToolSpec(
    name="list_directory",
    description="列出指定目录中的文件和子目录名称列表。",
    input_schema={"path": "str"},
    output_schema={"return": "list[str]"},
    constraints=["只读", "按名称排序"],
)


# ---- ToolRecord 构造 ----

def _make_record(spec: ToolSpec, code: str) -> ToolRecord:
    return ToolRecord(
        name=spec.name,
        spec=spec,
        code=code.strip(),
        status=ToolStatus.REGISTERED,
    )


BUILTIN_TOOL_RECORDS: list[ToolRecord] = [
    _make_record(READ_TEXT_FILE_SPEC, READ_TEXT_FILE_CODE),
    _make_record(WRITE_TEXT_FILE_SPEC, WRITE_TEXT_FILE_CODE),
    _make_record(LIST_DIRECTORY_SPEC, LIST_DIRECTORY_CODE),
]


def register_builtin_tools(registry) -> None:
    """将 3 个内置工具注册到给定的 ToolRegistry 实例。"""
    from app.core.registry import ToolRegistry

    assert isinstance(registry, ToolRegistry)
    for record in BUILTIN_TOOL_RECORDS:
        registry.register(record)
