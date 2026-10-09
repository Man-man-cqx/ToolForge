"""Evaluator：对任务结果与工具表现打分（Phase 3 实现）。"""

from app.models.state import ToolForgeState


class Evaluator:
    """评估任务完成质量。"""

    def evaluate(self, state: ToolForgeState) -> ToolForgeState:
        """在状态轨迹中写入评估结果。"""
        raise NotImplementedError("Evaluator.evaluate 将在 Phase 3 实现")
