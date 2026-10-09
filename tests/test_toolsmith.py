"""ToolSmith 测试。"""

import pytest

from app.agents.toolsmith import ToolSmith
from app.core.llm import MockLLM, TOOLSMITH_SYSTEM_PROMPT
from app.models.state import ToolForgeState
from app.models.task import Task


def test_toolsmith_generates_csv_spec() -> None:
    llm = MockLLM()
    smith = ToolSmith(llm)

    state = ToolForgeState(
        task=Task(description="parse csv"),
        missing_capability="csv_parser",
    )
    state = smith.generate_spec(state)

    assert state.tool_spec is not None
    assert state.tool_spec.name == "parse_csv"
    assert "csv" in state.tool_spec.description.lower()
    assert state.tool_spec.input_schema == {"path": "str"}
    assert state.current_step == "generate_code"
    assert len(state.trace) == 1
    assert state.trace[0]["node"] == "generate_spec"


def test_toolsmith_no_capability_raises() -> None:
    llm = MockLLM()
    smith = ToolSmith(llm)
    state = ToolForgeState(task=Task(description="x"))

    with pytest.raises(RuntimeError):
        smith.generate_spec(state)


def test_toolsmith_generates_chart_spec() -> None:
    llm = MockLLM()
    smith = ToolSmith(llm)

    state = ToolForgeState(
        task=Task(description="draw chart"),
        missing_capability="chart_generator",
    )
    state = smith.generate_spec(state)

    assert state.tool_spec is not None
    assert state.tool_spec.name == "generate_bar_chart"
    assert state.current_step == "generate_code"
