"""LLM 客户端测试。"""

from app.config import Settings, get_settings
from app.core.llm import (
    LLMClient,
    LLMResponse,
    MockLLM,
    EXECUTOR_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    get_llm_client,
    parse_missing_capability,
    parse_tool_call,
)


def test_mock_llm_planner_response() -> None:
    llm = MockLLM()
    response = llm.generate("any task", system=PLANNER_SYSTEM_PROMPT)

    assert isinstance(response, LLMResponse)
    assert "1." in response.content
    assert response.model == "mock-llm"
    assert response.usage == {"prompt_tokens": 0, "completion_tokens": 0}


def test_mock_llm_executor_read() -> None:
    llm = MockLLM()
    response = llm.generate(
        "read data/hello.txt", system=EXECUTOR_SYSTEM_PROMPT
    )

    assert "call read_text_file" in response.content
    assert "path=" in response.content


def test_mock_llm_executor_missing() -> None:
    llm = MockLLM()
    response = llm.generate(
        "parse data/sales.csv and draw chart", system=EXECUTOR_SYSTEM_PROMPT
    )

    assert "[MISSING:" in response.content


def test_mock_llm_default() -> None:
    llm = MockLLM()
    response = llm.generate("hello")

    assert response.content == "mock response"


def test_get_llm_client_factory() -> None:
    get_settings.cache_clear()
    client = get_llm_client()
    assert isinstance(client, LLMClient)
    assert isinstance(client, MockLLM)  # 无 Key 时


def test_parse_missing_capability() -> None:
    assert parse_missing_capability("[MISSING: csv_parser]") == "csv_parser"
    assert parse_missing_capability("no missing here") is None


def test_parse_tool_call() -> None:
    result = parse_tool_call("call read_text_file(path=data/hello.txt)")
    assert result is not None
    assert result[0] == "read_text_file"
    assert result[1] == {"path": "data/hello.txt"}


def test_parse_tool_call_no_match() -> None:
    assert parse_tool_call("not a tool call") is None
