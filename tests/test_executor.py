"""Executor 测试。"""

import pytest

from app.agents.executor import Executor
from app.core.llm import MockLLM
from app.core.registry import ToolRegistry
from app.models.state import ToolForgeState
from app.models.task import Task
from app.tools.builtin import register_builtin_tools


def test_executor_success(tmp_path) -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = MockLLM()
    executor = Executor(registry, llm)

    test_file = tmp_path / "hello.txt"
    test_file.write_text("Hello!", encoding="utf-8")

    state = ToolForgeState(
        task=Task(description=f"read {test_file}"),
        plan=["read the file"],
    )
    state = executor.execute(state)

    assert state.current_step == "done"
    assert state.task.status == "completed"
    assert "Hello!" in state.task.result


def test_executor_missing_capability() -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = MockLLM()
    executor = Executor(registry, llm)

    state = ToolForgeState(
        task=Task(description="parse data/sales.csv and generate chart"),
        plan=["parse csv", "draw chart"],
    )
    state = executor.execute(state)

    assert state.current_step == "detect_missing"
    assert state.missing_capability == "csv_parser"


def test_detect_missing_confirms() -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = MockLLM()
    executor = Executor(registry, llm)

    state = ToolForgeState(
        task=Task(description="parse csv"),
        missing_capability="csv_parser",
    )
    missing = executor.detect_missing(state)
    assert missing == "csv_parser"


def test_detect_missing_false_positive() -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = MockLLM()
    executor = Executor(registry, llm)

    state = ToolForgeState(
        task=Task(description="read file"),
        missing_capability="read",  # read_text_file 已存在
    )
    missing = executor.detect_missing(state)
    assert missing is None
