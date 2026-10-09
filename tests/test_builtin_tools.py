"""内置工具测试。"""

from app.core.registry import ToolRegistry
from app.tools.builtin import register_builtin_tools


def test_read_text_file(tmp_path) -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)

    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world", encoding="utf-8")

    result = registry.call("read_text_file", path=str(test_file))
    assert result == "hello world"


def test_write_text_file(tmp_path) -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)

    test_file = tmp_path / "out.txt"
    result = registry.call(
        "write_text_file", path=str(test_file), content="written content"
    )
    assert result is True
    assert test_file.read_text(encoding="utf-8") == "written content"


def test_list_directory(tmp_path) -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)

    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")

    result = registry.call("list_directory", path=str(tmp_path))
    assert "a.txt" in result
    assert "b.txt" in result


def test_three_builtin_tools_registered() -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)

    names = [r.name for r in registry.list_tools()]
    assert "read_text_file" in names
    assert "write_text_file" in names
    assert "list_directory" in names
    assert len(names) == 3
