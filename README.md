# ToolForge：会自己造工具的 AI 智能体

> **不是让 AI 调用工具，而是让 AI 生产工具。**

ToolForge 演示这样一个闭环：当 AI 执行任务发现缺少所需工具时，会自行
生成工具规格、实现代码与 pytest 测试，在沙箱中验证、经安全审查后注册为
可复用工具，再用新工具重试完成任务，并把经验沉淀到记忆中。

```
用户任务 → Planner 拆解 → Executor 执行 → 发现缺少工具
   → ToolSmith 生成规格 → Coder 生成代码+测试 → Tester 沙箱测试
   → Guard 安全审查 → Registry 注册 → Executor 重试
   → Evaluator 评估 → Memory 沉淀
```

## 设计决策

### 为什么 ToolForgeState 使用 Pydantic BaseModel 而非 TypedDict？

状态机流转的所有中间产物（Task / ToolSpec / GeneratedTool / TestResult /
SecurityReport / ToolRecord）本身都是 Pydantic 模型。ToolForgeState 同样
使用 BaseModel，可以获得：

1. **嵌套校验**：错误状态在进入下一节点前即被发现，而不是静默传播；
2. **默认值安全**：`list/dict` 字段使用 `default_factory`，杜绝可变默认值共享；
3. **统一序列化**：`state.model_dump()` 可直接写入 JSON trace 文件；
4. **方法封装**：可在状态上提供 `add_trace()` 等辅助方法。

`TypedDict` 仅提供静态类型标注、运行时无任何校验与序列化能力，不满足 MVP
对可观测性与可持久化的要求。

## 安装与运行

要求 Python 3.11+（开发验证使用 3.12）。以下命令在 Windows PowerShell 中执行。

### 1. 创建并使用虚拟环境

```powershell
# 在项目根目录 toolforge/ 下创建 venv
py -3.12 -m venv .venv

# 无需激活脚本，直接使用 venv 中的解释器（避免执行策略限制）
.\.venv\Scripts\python.exe --version
```

### 2. 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> 也可以激活环境后使用 `pip`：`.\.venv\Scripts\Activate.ps1`
> （若提示执行策略限制，请改用上面的直接调用方式，不要修改系统执行策略）。

### 3. 配置环境变量（可选）

```powershell
Copy-Item .env.example .env
```

不设置 `OPENAI_API_KEY` 时，系统自动使用 MockLLM，完整 Demo 仍可运行。

### 4. 运行测试

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### 5. 启动服务并验证健康检查

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

另开一个终端：

```powershell
Invoke-RestMethod http://localhost:8000/health -UseBasicParsing
```

未配置 API Key 时，返回中包含 `"llm_mode": "mock"`。

### 6. CLI（逐步开放）

```powershell
.\.venv\Scripts\python.exe -m app.cli version
# run / list-tools / demo 将在后续 Phase 实现
```

## 目录结构

```
toolforge/
  app/
    main.py              # FastAPI 入口（/health）
    config.py            # 配置：环境变量 / .env，密钥不硬编码
    cli.py               # Typer CLI（Phase 0 仅 version）
    models/              # 7 个 Pydantic 数据模型
      task.py            #   Task / TaskStatus
      tool.py            #   ToolSpec / GeneratedTool / TestResult /
                         #   SecurityReport / ToolRecord / ToolStatus / TestCase
      state.py           #   ToolForgeState（全流程共享状态）
    agents/              # Planner / Executor / ToolSmith / Coder /
                         # Tester / Guard / Evaluator（分阶段实现）
    core/                # graph / llm / registry / sandbox /
                         # security / memory / mcp_server（分阶段实现）
    tools/
      builtin/           # 内置工具（Phase 1）
      generated/         # Agent 动态生成工具的落盘目录（Phase 2）
    api/                 # HTTP 路由（Phase 4）
    templates/           # Jinja2 看板模板（Phase 4）
  tests/                 # pytest 测试
  tasks/
    demo_tasks.json      # Demo 任务集
  scripts/               # run_demo.py 等脚本（Phase 5）
  docker/                # 沙箱相关 Docker 文件（Phase 2）
  data/                  # 输入数据
  output/                # 产物输出
  .env.example
  requirements.txt
```

## 安全红线

- 生成的代码**绝不直接在宿主机执行**，必须在 Docker 沙箱中运行；
  无 Docker 时降级 subprocess 并明确标记"非安全降级模式"；
- Guard 使用 Python `ast` 做静态审查：禁止危险导入（os/subprocess/socket/
  shutil/ctypes）、危险调用（eval/exec/compile/__import__/open 写模式）、
  敏感路径与密钥访问；网络能力必须显式申请且经人工审批；
- 高风险工具状态为 `pending_approval`，不能自动注册。

## Roadmap

- [x] **Phase 0**：项目骨架、配置、数据模型、/health
- [ ] **Phase 1**：LLMClient + MockLLM、ToolRegistry、内置工具、Planner/Executor、状态机
- [ ] **Phase 2**：ToolSmith/Coder/Tester/Guard、沙箱、AST 审查、动态注册、Demo 闭环
- [ ] **Phase 3**：ChromaDB + SQLite 记忆、工具信誉与 ROI 排序、工具复用
- [ ] **Phase 4**：FastAPI 路由、Jinja2 看板、MCP 描述导出、人工审批
- [ ] **Phase 5**：评估脚本、任务集批量评测、指标报告、文档完善
