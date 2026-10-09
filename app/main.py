"""FastAPI 应用入口。

启动方式::

    uvicorn app.main:app --port 8000
"""

from datetime import datetime, timezone

from fastapi import FastAPI

from app.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """应用工厂：构造并返回 FastAPI 实例。

    :param settings: 可选的自定义配置（测试时可注入）；默认读取单例。
    """
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="会自己造工具的 AI 智能体（MVP）",
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, object]:
        """健康检查：返回服务状态与当前 LLM 模式（mock / openai）。"""
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
            "llm_mode": settings.llm_mode,
            "server_time": datetime.now(timezone.utc).isoformat(),
        }

    return app


# 供 ``uvicorn app.main:app`` 直接引用
app = create_app()
