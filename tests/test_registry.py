"""ToolRegistry 测试。"""

from app.core.registry import ToolRegistry
from app.models.tool import ToolSpec, ToolStatus, ToolRecord


def _make_record(name: str, description: str, code: str = "") -> ToolRecord:
    return ToolRecord(
        name=name,
        spec=ToolSpec(name=name, description=description),
        code=code or f"def {name}():\n    return True",
        status=ToolStatus.REGISTERED,
    )


def test_register_and_get() -> None:
    registry = ToolRegistry()
    record = _make_record("foo", "does foo")
    registry.register(record)

    assert registry.get("foo") is record
    assert registry.get("bar") is None


def test_list_tools() -> None:
    registry = ToolRegistry()
    registry.register(_make_record("a", "desc a"))
    registry.register(_make_record("b", "desc b"))

    assert len(registry.list_tools()) == 2


def test_call() -> None:
    registry = ToolRegistry()
    code = "def add(a, b):\n    return a + b"
    registry.register(_make_record("add", "adds two numbers", code))

    result = registry.call("add", a=2, b=3)
    assert result == 5


def test_call_unknown_tool() -> None:
    import pytest

    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.call("nonexistent", x=1)


def test_has_capability() -> None:
    registry = ToolRegistry()
    registry.register(_make_record("read_text_file", "读取文本文件内容"))

    assert registry.has_capability("read") is True
    assert registry.has_capability("csv") is False


def test_has_capability_description_match() -> None:
    registry = ToolRegistry()
    registry.register(_make_record("parse_json", "parse JSON data"))

    assert registry.has_capability("json") is True
