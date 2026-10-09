"""Tester：在沙箱中运行 pytest 验证生成工具（Phase 2 实现）。"""

from app.models.state import ToolForgeState


class Tester:
    """沙箱测试执行器。"""

    def test_code(self, state: ToolForgeState) -> ToolForgeState:
        """在状态中写入 test_result。"""
        raise NotImplementedError("Tester.test_code 将在 Phase 2 实现")
