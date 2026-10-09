"""智能体全流程共享状态模型。"""

from typing import Any

from pydantic import BaseModel, Field

from app.models.task import Task, utc_now
from app.models.tool import (
    GeneratedTool,
    SecurityReport,
    TestResult,
    ToolRecord,
    ToolSpec,
)


class ToolForgeState(BaseModel):
    """在状态机各节点之间流转的全局状态。

    设计选择（详见 README「设计决策」）：使用 Pydantic BaseModel 而非
    ``TypedDict`` —— 本项目所有中间产物（Task / ToolSpec / TestResult ...）
    本身都是 Pydantic 模型，使用 BaseModel 可以获得嵌套校验、默认值安全、
    统一 ``model_dump()`` 序列化（直接写 JSON trace）以及 ``add_trace`` 等
    方法封装；TypedDict 仅做静态标注、运行时无任何保护，不符合 MVP
    「可观测、可持久化」的需要。
    """

    task: Task | None = Field(
        default=None,
        description="当前正在处理的任务对象。",
    )

    plan: list[str] = Field(
        default_factory=list,
        description="Planner 产出的执行步骤（与 task.plan 保持同步）。",
    )

    current_step: str = Field(
        default="init",
        description="状态机当前所处节点名称。",
    )

    missing_capability: str | None = Field(
        default=None,
        description="Executor 检测到的缺失能力描述。",
    )

    tool_spec: ToolSpec | None = Field(
        default=None,
        description="ToolSmith 为缺失能力生成的工具规格。",
    )

    generated_tool: GeneratedTool | None = Field(
        default=None,
        description="Coder 生成的代码与测试。",
    )

    test_result: TestResult | None = Field(
        default=None,
        description="Tester 在沙箱中得到的测试结果。",
    )

    security_report: SecurityReport | None = Field(
        default=None,
        description="Guard 的 AST 静态安全审查报告。",
    )

    registered_tool: ToolRecord | None = Field(
        default=None,
        description="注册成功后产生的工具记录。",
    )

    retry_count: int = Field(
        default=0,
        ge=0,
        description="任务因缺工具触发的重试次数。",
    )

    trace: list[dict[str, Any]] = Field(
        default_factory=list,
        description="按时间顺序记录的节点执行轨迹。",
    )

    def add_trace(self, node: str, payload: dict[str, Any] | None = None) -> None:
        """追加一条执行轨迹。

        :param node: 节点名称（如 plan / generate_code / test_code）。
        :param payload: 该节点希望记录的结构化附加信息。
        """
        self.trace.append(
            {
                "node": node,
                "time": utc_now().isoformat(),
                "payload": payload or {},
            }
        )
