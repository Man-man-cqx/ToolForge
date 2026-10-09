"""LLM 客户端抽象与实现。

统一接口 LLMClient + 两个实现：
- 有 OPENAI_API_KEY 时走 OpenAIClient；
- 无 Key 时使用 MockLLM，返回预定义内容，保证 Demo 可跑。
所有 Agent 只依赖 LLMClient 接口，切真 Key 时零改动。
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.config import Settings, get_settings

# ---- 系统 prompt 常量 ----

PLANNER_SYSTEM_PROMPT = (
    "You are a planner. Given a task, break it into ordered steps. "
    "Return each step on a new line, numbered '1. ', '2. ', etc."
)

EXECUTOR_SYSTEM_PROMPT = (
    "You are an executor. Given a task and available tools, decide which tool to call. "
    "Reply with 'call <tool_name>(<key>=<value>)' to invoke a tool. "
    "If no available tool can handle the task, reply with '[MISSING: <capability>]'."
)

TOOLSMITH_SYSTEM_PROMPT = (
    "You are a tool smith. Given a missing capability description, "
    "produce a tool specification as JSON with keys: name, description, "
    "input_schema, output_schema, constraints, test_cases, requires_network."
)

CODER_SYSTEM_PROMPT = (
    "You are a code generator. Given a tool specification, produce two things: "
    "1) a Python function implementation string 2) a pytest test string. "
    "Separate them with '---TEST---'."
)

# ---- 统一返回结构 ----


class LLMResponse(BaseModel):
    """LLM 返回结构，真实与 Mock 完全一致。"""

    content: str = Field(description="生成的文本回复。")
    model: str = Field(description="产生此回复的模型名。")
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="token 用量（Mock 填 0）。",
    )


# ---- 抽象基类 ----


class LLMClient(ABC):
    """所有 Agent 依赖的 LLM 抽象接口。"""

    @abstractmethod
    def generate(self, prompt: str, *, system: str = "", **kwargs: Any) -> LLMResponse:
        """根据提示词生成文本回复。"""
        ...


# ---- OpenAI 实现 ----


class OpenAIClient(LLMClient):
    """OpenAI 兼容接口实现。"""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def generate(self, prompt: str, *, system: str = "", **kwargs: Any) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
        )

        choice = response.choices[0]
        usage_dict: dict[str, int] = {}
        if response.usage:
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage_dict,
        )


# ---- MockLLM 实现 ----

_MISSING_RE = re.compile(r"\[MISSING:\s*(\w+)\]")


class MockLLM(LLMClient):
    """无 Key 时的降级实现，返回预定义内容。

    返回策略：
    - system 含 "planner"：返回固定步骤
    - system 含 "executor" + prompt 含 "read"：返回 call read_text_file
    - system 含 "executor" + prompt 含 "csv"/"chart"：返回 [MISSING: csv_parser]
    - 默认：返回 "mock response"
    所有返回均包装为 LLMResponse，与真实 LLM 结构一致。
    """

    _MOCK_USAGE = {"prompt_tokens": 0, "completion_tokens": 0}

    def generate(self, prompt: str, *, system: str = "", **kwargs: Any) -> LLMResponse:
        sys_lower = system.lower()
        prompt_lower = prompt.lower()

        if "planner" in sys_lower:
            return LLMResponse(
                content="1. read the file\n2. return the content",
                model="mock-llm",
                usage=self._MOCK_USAGE,
            )

        if "executor" in sys_lower:
            if "csv" in prompt_lower or "chart" in prompt_lower:
                return LLMResponse(
                    content="[MISSING: csv_parser]",
                    model="mock-llm",
                    usage=self._MOCK_USAGE,
                )
            if "read" in prompt_lower or "读取" in prompt:
                # 尝试从 prompt 中提取路径
                path: str | None = None
                # 1. 尝试 path= 格式
                path_match = re.search(r"path[=:\s]+([^\s,)]+)", prompt, re.IGNORECASE)
                if path_match:
                    path = path_match.group(1)
                else:
                    # 2. 从 Task 行中提取包含路径分隔符或扩展名的 token
                    task_match = re.search(r"Task:\s*(.+)", prompt)
                    if task_match:
                        for token in task_match.group(1).split():
                            if "\\" in token or "/" in token or ".txt" in token.lower():
                                path = token
                                break
                if path is None:
                    path = "data/hello.txt"
                return LLMResponse(
                    content=f"call read_text_file(path={path})",
                    model="mock-llm",
                    usage=self._MOCK_USAGE,
                )

        if "tool smith" in sys_lower:
            return self._toolsmith_response(prompt)

        if "code generator" in sys_lower:
            return self._coder_response(prompt)

        return LLMResponse(
            content="mock response",
            model="mock-llm",
            usage=self._MOCK_USAGE,
        )

    # ---- MockLLM 内部：ToolSmith 分支 ----

    @staticmethod
    def _toolsmith_response(prompt: str) -> LLMResponse:
        prompt_lower = prompt.lower()
        if "csv" in prompt_lower:
            content = json.dumps({
                "name": "parse_csv",
                "description": "Parse a CSV file and return a list of row dictionaries.",
                "input_schema": {"path": "str"},
                "output_schema": {"rows": "list[dict]"},
                "constraints": ["read-only", "no-network"],
                "test_cases": [{"name": "basic", "inputs": {"path": "test.csv"}, "expected": [{"a": "1"}]}],
                "requires_network": False,
            })
        elif "chart" in prompt_lower:
            content = json.dumps({
                "name": "generate_bar_chart",
                "description": "Generate a bar chart PNG from data.",
                "input_schema": {"data": "list[dict]", "x_field": "str", "y_field": "str", "output_path": "str"},
                "output_schema": {"return": "str"},
                "constraints": ["writes-png", "uses-matplotlib"],
                "test_cases": [{"name": "basic", "inputs": {"data": [{"x": "A", "y": 10}], "x_field": "x", "y_field": "y", "output_path": "chart.png"}, "expected": "chart.png"}],
                "requires_network": False,
            })
        else:
            content = json.dumps({
                "name": "echo_tool",
                "description": "Echo the input value back.",
                "input_schema": {"value": "str"},
                "output_schema": {"return": "str"},
                "constraints": ["no-side-effects"],
                "test_cases": [{"name": "basic", "inputs": {"value": "hello"}, "expected": "hello"}],
                "requires_network": False,
            })
        return LLMResponse(content=content, model="mock-llm", usage=MockLLM._MOCK_USAGE)

    # ---- MockLLM 内部：Coder 分支 ----

    @staticmethod
    def _coder_response(prompt: str) -> LLMResponse:
        # 根据 prompt 中包含的工具名选择代码模板
        prompt_lower = prompt.lower()
        if "parse_csv" in prompt_lower:
            code = (
                "import csv\n"
                "\n"
                "def parse_csv(path):\n"
                "    with open(path, 'r', newline='', encoding='utf-8') as f:\n"
                "        reader = csv.DictReader(f)\n"
                "        return [dict(row) for row in reader]\n"
            )
            test_code = (
                "from app.tools.generated.parse_csv import parse_csv\n"
                "\n"
                "def test_parse_csv_basic(tmp_path):\n"
                '    csv_file = tmp_path / "test.csv"\n'
                '    csv_file.write_text("a,b\\n1,2\\n3,4\\n", encoding="utf-8")\n'
                "    rows = parse_csv(str(csv_file))\n"
                "    assert len(rows) == 2\n"
                '    assert rows[0] == {"a": "1", "b": "2"}\n'
            )
        elif "generate_bar_chart" in prompt_lower:
            code = (
                "import matplotlib\n"
                "matplotlib.use('Agg')\n"
                "import matplotlib.pyplot as plt\n"
                "\n"
                "def generate_bar_chart(data, x_field, y_field, output_path):\n"
                "    x_values = [item[x_field] for item in data]\n"
                "    y_values = [item[y_field] for item in data]\n"
                "    fig, ax = plt.subplots()\n"
                "    ax.bar(x_values, y_values)\n"
                "    ax.set_xlabel(x_field)\n"
                "    ax.set_ylabel(y_field)\n"
                "    fig.savefig(output_path, format='png')\n"
                "    plt.close(fig)\n"
                "    return output_path\n"
            )
            test_code = (
                "from app.tools.generated.generate_bar_chart import generate_bar_chart\n"
                "from PIL import Image\n"
                "\n"
                "def test_generate_bar_chart(tmp_path):\n"
                '    data = [{"x": "A", "y": 10}, {"x": "B", "y": 20}]\n'
                '    out = tmp_path / "chart.png"\n'
                '    result = generate_bar_chart(data, "x", "y", str(out))\n'
                "    assert result == str(out)\n"
                "    assert out.exists()\n"
                "    img = Image.open(str(out))\n"
                "    assert img.size[0] > 0 and img.size[1] > 0\n"
            )
        else:
            code = (
                "def echo_tool(value):\n"
                "    return value\n"
            )
            test_code = (
                "from app.tools.generated.echo_tool import echo_tool\n"
                "\n"
                "def test_echo_tool_basic():\n"
                '    assert echo_tool("hello") == "hello"\n'
            )
        content = code + "---TEST---\n" + test_code
        return LLMResponse(content=content, model="mock-llm", usage=MockLLM._MOCK_USAGE)


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    """工厂函数：有 Key 返回 OpenAIClient，否则 MockLLM。"""
    settings = settings or get_settings()
    if settings.mock_llm:
        return MockLLM()
    key = settings.openai_api_key.get_secret_value()  # type: ignore[union-attr]
    return OpenAIClient(
        api_key=key,
        base_url=settings.openai_base_url,
        model=settings.llm_model,
    )


def parse_missing_capability(content: str) -> str | None:
    """从 LLM 回复中提取 [MISSING: <capability>] 标记。

    返回能力关键字（小写），无匹配时返回 None。
    """
    match = _MISSING_RE.search(content)
    return match.group(1).lower() if match else None


def parse_tool_call(content: str) -> tuple[str, dict[str, str]] | None:
    """从 LLM 回复中解析 'call <tool_name>(key=value, ...)' 格式。

    返回 (tool_name, kwargs)，无匹配时返回 None。
    """
    match = re.match(
        r"call\s+(\w+)\s*\((.*)\)", content.strip(), re.IGNORECASE
    )
    if not match:
        return None
    tool_name = match.group(1)
    args_str = match.group(2).strip()
    kwargs: dict[str, str] = {}
    if args_str:
        for pair in args_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                kwargs[k.strip()] = v.strip()
    return tool_name, kwargs


def split_code_and_test(raw: str) -> tuple[str, str]:
    """从 LLM 回复中鲁棒拆分实现代码与测试代码。

    按优先级尝试 4 种分隔符匹配：
    a) 精确匹配 "---TEST---"
    b) 正则 r'---+\\s*TEST\\s*---+'
    c) 正则 r'#+\\s*Test' 大小写不敏感
    d) 全部失败 → 抛 ValueError
    """
    # a) 精确匹配
    if "---TEST---" in raw:
        parts = raw.split("---TEST---", 1)
        return parts[0].strip(), parts[1].strip()
    # b) 正则匹配含 TEST 的分隔线
    match = re.search(r'---+\s*TEST\s*---+', raw)
    if match:
        return raw[:match.start()].strip(), raw[match.end():].strip()
    # c) 正则匹配 # Test 标题
    match = re.search(r'#+\s*Test', raw, re.IGNORECASE)
    if match:
        return raw[:match.start()].strip(), raw[match.end():].strip()
    # d) 全部失败
    raise ValueError("无法在 LLM 回复中找到 code/test 分隔符")
