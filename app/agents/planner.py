"""Planner：任务拆解 Agent。

调用 LLM 将自然语言任务拆解为有序执行步骤，写入 ToolForgeState.plan。
"""

from app.core.llm import LLMClient, PLANNER_SYSTEM_PROMPT
from app.models.state import ToolForgeState


class Planner:
    """将自然语言任务拆解为有序执行步骤。"""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def plan(self, state: ToolForgeState) -> ToolForgeState:
        """在状态中写入 plan 并推进到 execute 节点。"""
        if state.task is None:
            raise RuntimeError("Planner.plan: state.task is None")

        prompt = f"Task: {state.task.description}"
        response = self._llm.generate(prompt, system=PLANNER_SYSTEM_PROMPT)

        steps = [
            line.strip()
            for line in response.content.strip().splitlines()
            if line.strip()
        ]

        state.plan = steps
        state.task.plan = steps
        state.task.status = "executing"
        state.current_step = "execute"
        state.add_trace("plan", {"steps": len(steps), "content": response.content})
        return state
