"""Coder 测试。"""

import pytest

from app.agents.coder import Coder
from app.core.llm import MockLLM, split_code_and_test
from app.models.state import ToolForgeState
from app.models.task import Task
from app.models.tool import ToolSpec


def test_coder_generates_code_and_test() -> None:
    llm = MockLLM()
    coder = Coder(llm)

    spec = ToolSpec(name="parse_csv", description="Parse a CSV file.")
    state = ToolForgeState(
        task=Task(description="parse csv"),
        tool_spec=spec,
    )
    state = coder.generate_code(state)

    assert state.generated_tool is not None
    assert state.generated_tool.name == "parse_csv"
    assert "def parse_csv" in state.generated_tool.code
    assert "def test_" in state.generated_tool.test_code
    assert state.current_step == "test_code"
    assert len(state.trace) == 1
    assert state.trace[0]["node"] == "generate_code"


def test_coder_no_spec_raises() -> None:
    llm = MockLLM()
    coder = Coder(llm)
    state = ToolForgeState(task=Task(description="x"))

    with pytest.raises(RuntimeError):
        coder.generate_code(state)


def test_coder_handles_separator_variants() -> None:
    """覆盖 3 种分隔符变体：---TEST---、--- TEST ---、# Test"""
    # a) 精确匹配
    code_a, test_a = split_code_and_test("def f():\n    return 1\n---TEST---\ndef test_f():\n    pass")
    assert "def f" in code_a
    assert "def test_f" in test_a

    # b) 正则 ---+ \s* TEST \s* ---+
    code_b, test_b = split_code_and_test("def g():\n    return 2\n--- TEST ---\ndef test_g():\n    pass")
    assert "def g" in code_b
    assert "def test_g" in test_b

    # c) 正则 #+ \s* Test (大小写不敏感)
    code_c, test_c = split_code_and_test("def h():\n    return 3\n## Test\ndef test_h():\n    pass")
    assert "def h" in code_c
    assert "def test_h" in test_c


def test_split_code_and_test_no_separator_raises() -> None:
    with pytest.raises(ValueError):
        split_code_and_test("just some code without separator")
