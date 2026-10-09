"""内置工具包：read_text_file / write_text_file / list_directory。"""

from app.tools.builtin.file_tools import BUILTIN_TOOL_RECORDS, register_builtin_tools

__all__ = ["BUILTIN_TOOL_RECORDS", "register_builtin_tools"]
