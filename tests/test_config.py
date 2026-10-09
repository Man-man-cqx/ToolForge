"""配置测试：有/无 OPENAI_API_KEY 时 LLM 模式的切换。"""

import pytest

from app.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    """每个测试前后清空 get_settings 的 lru_cache，避免单例污染。"""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_mock_llm_when_key_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = Settings()

    assert settings.mock_llm is True
    assert settings.llm_mode == "mock"


def test_mock_llm_when_key_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "  ")

    settings = Settings()

    assert settings.mock_llm is True


def test_openai_mode_when_key_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test-key")

    settings = Settings()

    assert settings.mock_llm is False
    assert settings.llm_mode == "openai"
