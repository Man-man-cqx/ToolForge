"""应用配置：统一从环境变量与项目根目录下的 .env 文件加载。

安全约定：
- 代码中绝不硬编码任何密钥；
- OPENAI_API_KEY 使用 SecretStr 包裹，避免被日志直接打印；
- 未配置 Key 时 mock_llm 为 True，系统自动降级到 MockLLM。
"""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ToolForge 运行时配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 应用 ----
    app_name: str = "ToolForge"
    """应用名称。"""

    app_version: str = "0.1.0"
    """应用版本号。"""

    app_env: str = "dev"
    """运行环境：dev / prod。"""

    # ---- LLM ----
    openai_api_key: SecretStr | None = None
    """OpenAI 兼容接口密钥；留空时启用 MockLLM。"""

    openai_base_url: str = "https://api.openai.com/v1"
    """OpenAI 兼容接口 Base URL，可指向任意兼容网关。"""

    llm_model: str = "gpt-4o-mini"
    """默认使用的模型名称。"""

    # ---- 目录 ----
    data_dir: Path = Path("data")
    """输入数据目录。"""

    output_dir: Path = Path("output")
    """产物输出目录。"""

    traces_dir: Path = Path("data/traces")
    """JSON trace 文件目录。"""

    generated_tools_dir: Path = Path("app/tools/generated")
    """动态生成工具的落盘目录。"""

    # ---- 沙箱与记忆 ----
    sandbox_mode: str = "auto"
    """测试沙箱模式：auto（优先 Docker）/ docker / subprocess。"""

    chroma_dir: Path = Path(".chroma")
    """ChromaDB 本地持久化目录（Phase 3）。"""

    sqlite_path: Path = Path("data/toolforge.db")
    """SQLite 数据库路径（Phase 3）。"""

    @property
    def mock_llm(self) -> bool:
        """是否使用 MockLLM：未配置密钥或密钥为空时为 True。"""
        if self.openai_api_key is None:
            return True
        return not bool(self.openai_api_key.get_secret_value().strip())

    @property
    def llm_mode(self) -> str:
        """当前 LLM 模式标识：``mock`` 或 ``openai``。"""
        return "mock" if self.mock_llm else "openai"


@lru_cache
def get_settings() -> Settings:
    """返回进程级单例 Settings。"""
    return Settings()
