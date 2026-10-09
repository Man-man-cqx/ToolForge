"""Guard：基于 AST 的静态安全审查（Phase 2 实现）。"""

from app.models.state import ToolForgeState


class Guard:
    """对生成代码做静态安全检查。"""

    def review(self, state: ToolForgeState) -> ToolForgeState:
        """在状态中写入 security_report。"""
        raise NotImplementedError("Guard.review 将在 Phase 2 实现")
