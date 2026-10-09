"""任务相关数据模型。"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """返回带 UTC 时区的当前时间。"""
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    """任务生命周期状态。"""

    PENDING = "pending"
    """已创建，尚未规划。"""

    PLANNING = "planning"
    """Planner 正在拆解任务。"""

    EXECUTING = "executing"
    """Executor 正在执行任务。"""

    WAITING_APPROVAL = "waiting_approval"
    """高风险工具等待人工审批。"""

    COMPLETED = "completed"
    """任务成功完成。"""

    FAILED = "failed"
    """任务最终失败。"""


class Task(BaseModel):
    """用户提交的一次任务。"""

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="任务唯一 ID，默认使用 uuid4 的十六进制字符串。",
    )

    description: str = Field(
        description="用户输入的自然语言任务描述。",
    )

    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="任务当前所处的生命周期状态。",
    )

    plan: list[str] = Field(
        default_factory=list,
        description="Planner 拆解出的有序执行步骤。",
    )

    result: str | None = Field(
        default=None,
        description="任务成功后的结果摘要或产物路径。",
    )

    error: str | None = Field(
        default=None,
        description="任务失败时记录的错误信息。",
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        description="任务创建时间（UTC）。",
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        description="任务最近一次更新的时间（UTC）。",
    )
