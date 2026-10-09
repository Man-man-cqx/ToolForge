"""Agent 编排：自研简单状态机（不依赖 LangGraph）。

Phase 2A 节点流：
    plan → execute → detect_missing → generate_spec → generate_code → test_code(挂起)
                     ↘ failed_missing / done
Phase 2B 将解除 test_code 挂起，衔接 sandbox 测试。
"""

from app.agents.coder import Coder
from app.agents.executor import Executor
from app.agents.planner import Planner
from app.agents.toolsmith import ToolSmith
from app.models.state import ToolForgeState

# 终止节点
_TERMINAL_NODES = {
    "done",
    "failed",
    "failed_missing",
    "generate_spec_failed",
    "generate_code_failed",
}
# 挂起节点：2A 到此挂起；2B 接管后从此处移除 test_code
_SUSPEND_NODES = {"test_code"}
_MAX_STEPS = 30


class StateMachine:
    """自研简单状态机。"""

    NODES = [
        "plan", "execute", "detect_missing",
        "generate_spec", "generate_code",
        "test_code",
        "done", "failed_missing",
        "generate_spec_failed", "generate_code_failed",
    ]

    def __init__(
        self,
        planner: Planner,
        executor: Executor,
        tool_smith: ToolSmith,
        coder: Coder,
    ) -> None:
        self._planner = planner
        self._executor = executor
        self._tool_smith = tool_smith
        self._coder = coder

    def run(self, state: ToolForgeState) -> ToolForgeState:
        """循环执行节点函数，根据 state.current_step 路由。"""
        if state.current_step == "init":
            state.current_step = "plan"

        stop_nodes = _TERMINAL_NODES | _SUSPEND_NODES
        steps = 0
        while state.current_step not in stop_nodes and steps < _MAX_STEPS:
            steps += 1
            if state.current_step == "plan":
                self._planner.plan(state)
            elif state.current_step == "execute":
                self._executor.execute(state)
            elif state.current_step == "detect_missing":
                self._handle_detect_missing(state)
            elif state.current_step == "generate_spec":
                self._tool_smith.generate_spec(state)
            elif state.current_step == "generate_code":
                self._coder.generate_code(state)
            else:
                break  # 未知节点，安全退出

        if steps >= _MAX_STEPS and state.current_step not in stop_nodes:
            if state.task:
                state.task.status = "failed"
                state.task.error = f"状态机超过最大步数 {_MAX_STEPS}"
            state.current_step = "failed"

        return state

    def _handle_detect_missing(self, state: ToolForgeState) -> None:
        """处理 detect_missing 节点。

        Phase 2A：确认缺失后衔接到 generate_spec（ToolSmith）。
        """
        missing = self._executor.detect_missing(state)
        if missing:
            state.current_step = "generate_spec"
            if state.task:
                state.task.error = None  # 清除之前的错误，进入工具制造
            state.add_trace("detect_missing", {"capability": missing})
        else:
            state.missing_capability = None
            state.current_step = "execute"


def run_graph(state: ToolForgeState) -> ToolForgeState:
    """便捷入口：使用默认配置创建状态机并运行。"""
    from app.core.llm import get_llm_client
    from app.core.registry import ToolRegistry
    from app.tools.builtin import register_builtin_tools

    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = get_llm_client()
    planner = Planner(llm)
    executor = Executor(registry, llm)
    tool_smith = ToolSmith(llm)
    coder = Coder(llm)
    machine = StateMachine(planner, executor, tool_smith, coder)
    return machine.run(state)
