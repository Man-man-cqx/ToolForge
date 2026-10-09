"""沙箱执行（Phase 2 实现）。

优先使用 Docker（python:3.11-slim、默认无网络、只读挂载）运行 pytest；
无 Docker 时降级 subprocess + 超时/资源限制，并标记非安全降级模式。
"""


class Sandbox:
    """代码测试沙箱。"""

    def run_pytest(self, code: str, test_code: str) -> dict:
        """在隔离环境中运行 pytest 并返回结果字典。"""
        raise NotImplementedError("Sandbox.run_pytest 将在 Phase 2 实现")
