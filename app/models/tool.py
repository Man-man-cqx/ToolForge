"""工具相关数据模型：规格、生成物、测试报告、安全报告、注册表记录。"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.models.task import utc_now


class ToolStatus(str, Enum):
    """工具生命周期状态。"""

    GENERATED = "generated"
    """代码已生成，尚未测试。"""

    TESTED = "tested"
    """沙箱测试通过，尚未完成安全审查/注册。"""

    PENDING_APPROVAL = "pending_approval"
    """高风险工具，等待人工审批，禁止自动注册。"""

    APPROVED = "approved"
    """人工审批通过。"""

    REGISTERED = "registered"
    """已注册到 ToolRegistry，可被 Executor 调用。"""

    REJECTED = "rejected"
    """安全审查或人工审批被拒绝。"""

    DEPRECATED = "deprecated"
    """已被弃用，不再参与调度。"""


class TestCase(BaseModel):
    """生成工具必须自带的测试用例定义。"""

    __test__ = False
    """阻止 pytest 将此类误当作测试用例收集。"""

    name: str = Field(
        description="测试用例名称。",
    )

    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="调用工具时传入的关键字参数。",
    )

    expected: Any = Field(
        default=None,
        description="期望输出；测试中据此断言。",
    )


class ToolSpec(BaseModel):
    """ToolSmith 产出的工具规格说明。"""

    name: str = Field(
        description="工具名称，必须为合法 Python 标识符且使用 snake_case。",
    )

    description: str = Field(
        description="工具能力的自然语言描述，供 Planner / Executor 检索理解。",
    )

    input_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="入参 JSON Schema（参数名 -> 类型/约束）。",
    )

    output_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="返回值 JSON Schema。",
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="工具必须遵守的约束条件（如纯函数、无网络、无文件写入）。",
    )

    test_cases: list[TestCase] = Field(
        default_factory=list,
        description="规格中声明的验收测试用例。",
    )

    requires_network: bool = Field(
        default=False,
        description="是否显式申请网络访问；为 True 时必须经人工审批。",
    )


class GeneratedTool(BaseModel):
    """Coder 根据 ToolSpec 生成的代码与测试。"""

    name: str = Field(
        description="工具名称，与 ToolSpec.name 保持一致。",
    )

    code: str = Field(
        description="工具实现的 Python 源代码字符串。",
    )

    test_code: str = Field(
        description="与工具配套的 pytest 测试源代码字符串。",
    )

    spec: ToolSpec = Field(
        description="该工具对应的规格说明。",
    )


class TestResult(BaseModel):
    """Tester 在沙箱中运行 pytest 的结果。"""

    __test__ = False
    """阻止 pytest 将此类误当作测试用例收集。"""

    passed: bool = Field(
        description="测试是否全部通过。",
    )

    stdout: str = Field(
        default="",
        description="测试运行的标准输出。",
    )

    stderr: str = Field(
        default="",
        description="测试运行的标准错误输出。",
    )

    duration: float = Field(
        default=0.0,
        description="测试耗时（秒）。",
    )

    sandbox_mode: str = Field(
        default="docker",
        description="实际使用的沙箱模式：docker 或 subprocess_degraded（非安全降级模式）。",
    )

    error: str | None = Field(
        default=None,
        description="沙箱本身异常（如容器启动失败）时的错误信息。",
    )


class SecurityReport(BaseModel):
    """Guard 基于 AST 静态审查产出的安全报告。"""

    safe: bool = Field(
        description="工具是否通过安全检查、允许自动注册。",
    )

    risks: list[str] = Field(
        default_factory=list,
        description="发现的安全风险描述列表。",
    )

    blocked_imports: list[str] = Field(
        default_factory=list,
        description="被禁止的导入（如 os、subprocess、socket）。",
    )

    blocked_calls: list[str] = Field(
        default_factory=list,
        description="被禁止的调用（如 eval、exec、open 写模式）。",
    )

    needs_approval: bool = Field(
        default=False,
        description="是否需要人工审批；为 True 时工具状态置为 pending_approval。",
    )


class ToolRecord(BaseModel):
    """Registry 中一条可复用工具的完整记录（含信誉指标）。"""

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="工具记录唯一 ID。",
    )

    name: str = Field(
        description="工具名称。",
    )

    spec: ToolSpec = Field(
        description="工具规格说明。",
    )

    code: str = Field(
        description="工具实现源代码。",
    )

    test_result: TestResult | None = Field(
        default=None,
        description="沙箱测试结果；未测试时为 None。",
    )

    security_report: SecurityReport | None = Field(
        default=None,
        description="安全审查报告；未审查时为 None。",
    )

    success_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="历史调用成功率，区间 [0, 1]。",
    )

    latency: float = Field(
        default=0.0,
        ge=0.0,
        description="平均调用延迟（毫秒）。",
    )

    cost: float = Field(
        default=0.0,
        ge=0.0,
        description="平均调用成本估算（美元）。",
    )

    reuse_count: int = Field(
        default=0,
        ge=0,
        description="被任务复用的次数。",
    )

    status: ToolStatus = Field(
        default=ToolStatus.GENERATED,
        description="工具当前的生命周期状态。",
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        description="工具记录创建时间（UTC）。",
    )
