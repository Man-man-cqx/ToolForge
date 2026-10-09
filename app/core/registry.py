"""工具注册表。

负责内置工具与动态生成工具的注册、检索、调用与能力检测。
Phase 3/4 将扩展 search（语义搜索）和 export_mcp_descriptions。
"""

from typing import Any

from app.models.tool import ToolRecord, ToolStatus


class ToolRegistry:
    """本地工具注册表。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolRecord] = {}

    def register(self, record: ToolRecord) -> None:
        """注册一条工具记录；同名工具将被覆盖。"""
        self._tools[record.name] = record

    def get(self, name: str) -> ToolRecord | None:
        """按名称获取工具记录。"""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolRecord]:
        """返回全部已注册工具。"""
        return list(self._tools.values())

    def call(self, name: str, **kwargs: Any) -> Any:
        """调用已注册工具。

        通过 exec 加载工具源码，提取与工具同名的函数并调用。
        若工具状态不是 REGISTERED 则抛出 RuntimeError。
        """
        record = self._tools.get(name)
        if record is None:
            raise KeyError(f"工具 '{name}' 未注册")
        if record.status not in (ToolStatus.REGISTERED, ToolStatus.APPROVED):
            raise RuntimeError(
                f"工具 '{name}' 状态为 {record.status.value}，不可调用"
            )
        namespace: dict[str, Any] = {}
        exec(record.code, namespace)  # noqa: S102
        func = namespace.get(name)
        if func is None or not callable(func):
            raise RuntimeError(f"工具代码中未找到函数 '{name}'")
        return func(**kwargs)

    def has_capability(self, keyword: str) -> bool:
        """判断注册表中是否已有与 keyword 相关的工具。

        按 spec.name + spec.description 做关键字模糊匹配（不区分大小写）。
        """
        kw = keyword.lower()
        for record in self._tools.values():
            haystack = f"{record.name} {record.spec.name} {record.spec.description}".lower()
            if kw in haystack:
                return True
        return False

    def search(self, query: str) -> list[ToolRecord]:
        """按语义检索工具（Phase 3 实现，当前返回空列表 stub）。"""
        raise NotImplementedError("ToolRegistry.search 将在 Phase 3 实现")

    def export_mcp_descriptions(self) -> list[dict]:
        """导出 MCP 兼容的工具描述列表（Phase 4 实现，当前 stub）。"""
        raise NotImplementedError("ToolRegistry.export_mcp_descriptions 将在 Phase 4 实现")
