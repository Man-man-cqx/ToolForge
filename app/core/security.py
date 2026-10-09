"""AST 静态安全检查工具函数（Phase 2 实现）。

将禁止：os/subprocess/socket/shutil/ctypes 导入，eval/exec/compile/
__import__/open 写模式调用，敏感路径与密钥访问，以及未审批的网络库。
"""


def scan_code(code: str) -> dict:
    """扫描源代码并返回安全发现。"""
    raise NotImplementedError("scan_code 将在 Phase 2 实现")
