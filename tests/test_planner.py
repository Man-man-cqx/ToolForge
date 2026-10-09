"""Planner 测试。"""

from app.agents.planner import Planner
from app.core.llm import MockLLM, PLANNER_SYSTEM_PROMPT
from app.models.state import ToolForgeState
from app.models.task import Task


def test_planner_produces_steps() -> None:
    llm = MockLLM()
    planner = Planner(llm)

    state = ToolForgeState(task=Task(description="read a file"))
    state = planner.plan(state)

    assert len(state.plan) > 0
    assert state.current_step == "execute"
    assert state.task.status == "executing"
    assert state.task.plan == state.plan
    assert len(state.trace) == 1
    assert state.trace[0]["node"] == "plan"


def test_planner_task_none_raises() -> None:
    import pytest

    llm = MockLLM()
    planner = Planner(llm)
    state = ToolForgeState()

    with pytest.raises(RuntimeError):
        planner.plan(state)
