"""ToolForge 命令行接口。

用法::

    python -m app.cli version
    python -m app.cli run "任务描述"
    python -m app.cli list-tools
    python -m app.cli demo               # Phase 2
"""

import json

import typer
from rich.console import Console
from rich.table import Table

from app.config import get_settings
from app.core.llm import get_llm_client
from app.core.registry import ToolRegistry
from app.models.task import Task, TaskStatus
from app.models.state import ToolForgeState
from app.tools.builtin import register_builtin_tools

cli = typer.Typer(
    name="toolforge",
    help="ToolForge：会自己造工具的 AI 智能体",
    no_args_is_help=True,
)
console = Console()


@cli.callback()
def _main() -> None:
    """显式 callback：防止 Typer 在仅有一个命令时将其折叠为根命令。"""


@cli.command()
def version() -> None:
    """打印 ToolForge 版本与当前 LLM 模式。"""
    settings = get_settings()
    console.print(f"ToolForge {settings.app_version} (llm_mode={settings.llm_mode})")


@cli.command()
def run(
    task: str = typer.Argument(..., help="自然语言任务描述"),
) -> None:
    """运行一个任务。"""
    from app.agents.coder import Coder
    from app.agents.executor import Executor
    from app.agents.planner import Planner
    from app.agents.toolsmith import ToolSmith
    from app.core.graph import StateMachine

    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = get_llm_client()

    state = ToolForgeState(task=Task(description=task))
    machine = StateMachine(
        Planner(llm),
        Executor(registry, llm),
        ToolSmith(llm),
        Coder(llm),
    )
    state = machine.run(state)

    # 输出结果
    console.print()
    console.print("[bold cyan]Task Result[/bold cyan]")
    console.print(f"  status: {state.task.status if state.task else 'unknown'}")
    if state.task and state.task.result:
        console.print(f"  result: {state.task.result}")
    if state.task and state.task.error:
        console.print(f"  [red]error: {state.task.error}[/red]")
    console.print(f"  steps: {len(state.trace)}")
    console.print()
    console.print("[dim]Trace:[/dim]")
    for entry in state.trace:
        console.print(f"  [{entry['node']}] {json.dumps(entry['payload'], ensure_ascii=False)}")


@cli.command("list-tools")
def list_tools() -> None:
    """列出注册表中的全部工具。"""
    registry = ToolRegistry()
    register_builtin_tools(registry)

    table = Table(title="Registered Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")
    table.add_column("Reuse", justify="right")

    for record in registry.list_tools():
        table.add_row(
            record.name,
            record.status.value,
            record.spec.description,
            str(record.reuse_count),
        )

    console.print(table)


if __name__ == "__main__":
    cli()
