"""记忆模块：ChromaDB 向量记忆 + SQLite 关系记忆（Phase 3 实现）。"""


class Memory:
    """任务轨迹与工具记录的持久化。"""

    def save(self, payload: dict) -> None:
        """保存一条记忆。"""
        raise NotImplementedError("Memory.save 将在 Phase 3 实现")
