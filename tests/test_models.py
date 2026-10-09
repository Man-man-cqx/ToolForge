"""Pydantic 数据模型测试。"""

from app.models.state import ToolForgeState
from app.models.task import Task, TaskStatus
from app.models.tool import (
    GeneratedTool,
    SecurityReport,
    TestCase,
    TestResult,
    ToolRecord,
    ToolSpec,
    ToolStatus,
)


def test_task_defaults() -> None:
    task = Task(description="hello")

    assert isinstance(task.id, str)
    assert len(task.id) == 32  # uuid4 hex
    assert task.status is TaskStatus.PENDING
    assert task.plan == []
    assert task.result is None
    assert task.error is None


def test_task_enum_serialization() -> None:
    task = Task(description="x", status=TaskStatus.COMPLETED)

    dumped = task.model_dump()
    assert dumped["status"] == "completed"


def test_tool_spec_with_test_cases() -> None:
    spec = ToolSpec(
        name="parse_csv",
        description="parse a csv file",
        input_schema={"path": "str"},
        output_schema={"rows": "list"},
        test_cases=[
            TestCase(name="basic", inputs={"path": "a.csv"}, expected=[{"a": 1}])
        ],
    )

    assert spec.requires_network is False
    assert spec.test_cases[0].inputs == {"path": "a.csv"}


def test_generated_tool_bundle() -> None:
    spec = ToolSpec(name="f", description="d")
    tool = GeneratedTool(
        name="f",
        code="def f():\n    return 1",
        test_code="def test_f(): ...",
        spec=spec,
    )

    assert tool.spec.name == "f"


def test_test_result_and_security_report_defaults() -> None:
    result = TestResult(passed=True)
    report = SecurityReport(safe=True)

    assert result.stdout == ""
    assert result.sandbox_mode == "docker"
    assert report.risks == []
    assert report.needs_approval is False


def test_tool_record_reputation_fields() -> None:
    record = ToolRecord(name="f", spec=ToolSpec(name="f", description="d"), code="")

    assert record.success_rate == 1.0
    assert record.latency == 0.0
    assert record.reuse_count == 0
    assert record.status is ToolStatus.GENERATED


def test_state_add_trace() -> None:
    state = ToolForgeState()

    assert state.current_step == "init"
    assert state.trace == []

    state.add_trace("plan", {"steps": 2})

    assert len(state.trace) == 1
    entry = state.trace[0]
    assert entry["node"] == "plan"
    assert entry["payload"] == {"steps": 2}
    assert "time" in entry
