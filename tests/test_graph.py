"""状态机端到端测试。"""

from app.agents.coder import Coder
from app.agents.executor import Executor
from app.agents.planner import Planner
from app.agents.toolsmith import ToolSmith
from app.core.graph import StateMachine
from app.core.llm import MockLLM
from app.core.registry import ToolRegistry
from app.models.state import ToolForgeState
from app.models.task import Task
from app.tools.builtin import register_builtin_tools


def _make_machine() -> StateMachine:
    """构造包含全部 2A Agent 的状态机。"""
    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = MockLLM()
    return StateMachine(
        Planner(llm),
        Executor(registry, llm),
        ToolSmith(llm),
        Coder(llm),
    )


def test_graph_read_file_demo(tmp_path) -> None:
    """端到端：Planner 拆解 → Executor 读文件 → done。"""
    test_file = tmp_path / "hello.txt"
    test_file.write_text("Hello, ToolForge!", encoding="utf-8")

    machine = _make_machine()
    state = ToolForgeState(task=Task(description=f"读取 {test_file} 并返回内容"))
    state = machine.run(state)

    assert state.current_step == "done"
    assert state.task.status == "completed"
    assert "Hello, ToolForge!" in state.task.result


def test_graph_missing_tool_generates_spec() -> None:
    """端到端：缺工具 → detect_missing → generate_spec → generate_code → test_code(挂起)。"""
    machine = _make_machine()
    state = ToolForgeState(
        task=Task(description="parse data/sales.csv and generate bar chart")
    )
    state = machine.run(state)

    # 2A 中 test_code 是挂起节点
    assert state.current_step == "test_code"
    assert state.tool_spec is not None
    assert state.generated_tool is not None
    assert state.tool_spec.name == "parse_csv"
    assert "def parse_csv" in state.generated_tool.code
