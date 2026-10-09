"""Coder：根据 ToolSpec 生成实现代码与 pytest 测试（Phase 2A）。

调用 LLM 产出用 ---TEST--- 分隔的代码和测试，使用鲁棒分隔符解析拆分，
构造 GeneratedTool 写入 state.generated_tool。
"""

from app.core.llm import CODER_SYSTEM_PROMPT, LLMClient, split_code_and_test
from app.models.state import ToolForgeState
from app.models.tool import GeneratedTool


class Coder:
    """根据 ToolSpec 生成代码与测试。"""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def generate_code(self, state: ToolForgeState) -> ToolForgeState:
        """在状态中写入 generated_tool 并推进到 test_code 节点。"""
        if state.tool_spec is None:
            raise RuntimeError("Coder.generate_code: state.tool_spec is None")

        spec = state.tool_spec
        prompt = (
            f"Tool spec:\n"
            f"  name: {spec.name}\n"
            f"  description: {spec.description}\n"
            f"  input_schema: {spec.input_schema}\n"
            f"  output_schema: {spec.output_schema}\n"
            f"  constraints: {spec.constraints}\n"
        )
        response = self._llm.generate(prompt, system=CODER_SYSTEM_PROMPT)

        try:
            code, test_code = split_code_and_test(response.content)
            if not code:
                raise ValueError("代码部分为空")
        except ValueError as exc:
            state.current_step = "generate_code_failed"
            if state.task:
                state.task.error = f"代码生成失败: {exc}"
            state.add_trace("generate_code_failed", {"error": str(exc)})
            return state

        tool = GeneratedTool(
            name=spec.name,
            code=code,
            test_code=test_code,
            spec=spec,
        )
        state.generated_tool = tool
        state.current_step = "test_code"
        state.add_trace("generate_code", {
            "name": tool.name,
            "code_len": len(code),
            "test_len": len(test_code),
        })
        return state
