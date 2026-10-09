"""ToolSmith：根据缺失能力生成工具规格（Phase 2A）。

从 state.missing_capability 出发，调用 LLM 产出 JSON 格式的工具规格，
构造 ToolSpec 写入 state.tool_spec。
"""

import json

from app.core.llm import LLMClient, TOOLSMITH_SYSTEM_PROMPT
from app.models.state import ToolForgeState
from app.models.tool import ToolSpec


class ToolSmith:
    """根据缺失能力描述生成 ToolSpec。"""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def generate_spec(self, state: ToolForgeState) -> ToolForgeState:
        """在状态中写入 tool_spec 并推进到 generate_code 节点。"""
        if state.missing_capability is None:
            raise RuntimeError("ToolSmith.generate_spec: state.missing_capability is None")

        prompt = f"Missing capability: {state.missing_capability}"
        response = self._llm.generate(prompt, system=TOOLSMITH_SYSTEM_PROMPT)

        try:
            spec_dict = json.loads(response.content)
            spec = ToolSpec(**spec_dict)
        except (json.JSONDecodeError, Exception) as exc:
            state.current_step = "generate_spec_failed"
            if state.task:
                state.task.error = f"ToolSpec 生成失败: {exc}"
            state.add_trace("generate_spec_failed", {"error": str(exc)})
            return state

        state.tool_spec = spec
        state.current_step = "generate_code"
        state.add_trace("generate_spec", {"name": spec.name, "description": spec.description})
        return state
