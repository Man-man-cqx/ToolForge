"""Executor：工具调用执行 Agent。

尝试使用注册表中已有工具执行任务。
若 LLM 判断缺少能力，在 state.missing_capability 中标记。
Phase 1 缺工具后任务标记为 FAILED；Phase 2 将在此处衔接 ToolSmith。
"""

from app.core.llm import (
    EXECUTOR_SYSTEM_PROMPT,
    LLMClient,
    parse_missing_capability,
    parse_tool_call,
)
from app.core.registry import ToolRegistry
from app.models.state import ToolForgeState


class Executor:
    """尝试使用注册表中已有工具执行任务。"""

    def __init__(self, registry: ToolRegistry, llm: LLMClient) -> None:
        self._registry = registry
        self._llm = llm

    def execute(self, state: ToolForgeState) -> ToolForgeState:
        """执行当前任务；成功设 done，缺工具设 detect_missing，异常设 failed。"""
        if state.task is None:
            raise RuntimeError("Executor.execute: state.task is None")

        # 1. 获取已有工具列表
        tools = self._registry.list_tools()
        tool_list_str = "\n".join(
            f"- {r.name}: {r.spec.description}" for r in tools
        ) or "(no tools registered)"

        # 2. 交给 LLM 判断需要哪些工具
        prompt = (
            f"Task: {state.task.description}\n"
            f"Available tools:\n{tool_list_str}\n"
            f"Plan steps:\n{chr(10).join(state.plan)}"
        )
        response = self._llm.generate(prompt, system=EXECUTOR_SYSTEM_PROMPT)
        state.add_trace("execute", {"llm_response": response.content})

        # 3. 检查是否缺工具
        missing = parse_missing_capability(response.content)
        if missing:
            state.missing_capability = missing
            state.current_step = "detect_missing"
            state.task.error = f"缺少能力: {missing}"
            return state

        # 4. 解析并执行工具调用
        call = parse_tool_call(response.content)
        if call is None:
            state.task.error = f"无法解析 LLM 回复: {response.content}"
            state.current_step = "failed_missing"
            return state

        tool_name, kwargs = call
        try:
            result = self._registry.call(tool_name, **kwargs)
            state.task.result = str(result)
            state.task.status = "completed"
            state.current_step = "done"
            state.add_trace("execute_result", {"tool": tool_name, "result": str(result)[:200]})
        except Exception as exc:
            state.task.error = f"工具调用失败 ({tool_name}): {exc}"
            state.current_step = "failed_missing"

        return state

    def detect_missing(self, state: ToolForgeState) -> str | None:
        """检查 state.missing_capability 是否确实在注册表中不存在。

        返回缺失的能力名（确认缺失）或 None（已有能力，可能是误判）。
        """
        if state.missing_capability is None:
            return None
        if self._registry.has_capability(state.missing_capability):
            return None  # 能力已存在，可能是 LLM 误判
        return state.missing_capability
