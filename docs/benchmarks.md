# 接口性能基准测试

本文记录 ai-resume 后端核心接口在本机隔离环境下的实测延迟数据（README「性能」小节的数字来源），以及完整的复现步骤。压测工具与脚本位于 [`scripts/benchmarks/`](../scripts/benchmarks/)。

## 测试环境与方法

- **被测对象**：本机隔离实例 `127.0.0.1:8004`（单进程 uvicorn，独立 SQLite 文件，Windows 11 / Python 3.11 本机回环，不经任何代理）
- **数据规模**：premium 账号名下预置 **1000 份完整简历草稿**（每份含教育/工作/项目/技能全量 JSON）
- **测延迟方法**：每个场景顺序采样（30~60 次）统计分位数；写接口建库阶段另测 4 并发吞吐；AI 场景额外做 5 用户并发排队观察
- **限流说明**：压测实例将 auth/AI 每用户限流阈值调高到压测量程（`AUTH_RATE_LIMIT_MAX_REQUESTS=1000` 等），避免限流信号污染延迟数据；限流本身的正确性由 234 个后端测试覆盖
- **AI 场景**：走真实上游模型（OpenAI 兼容中继），是端到端真实耗时，含网络与模型推理

## 实测结果（2026-09-22）

| 接口场景 | 样本 | P50 (ms) | P95 (ms) | P99 (ms) | max (ms) | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 登录全链路（send-code + login-phone 换 JWT） | 30 | 25.2 | **30.1** | 57.6 | 57.6 | 0 失败 |
| 简历就绪检查 resume/readiness | 60 | 10.7 | **14.0** | 14.5 | 17.0 | 纯计算 |
| 岗位查询 job/query（缓存命中） | 60 | 10.7 | **13.6** | 15.2 | 19.8 | 首次真实 AI 预热 17.6s |
| 简历草稿写入 draft/save（稳态） | 30 | 25.3 | **29.4** | 32.1 | 32.1 | 含额度事务校验 |
| 职业规划 career/recommend | 30 | 40.0 | **99.2** | 111.3 | 111.3 | 本地三档推荐引擎 |
| 岗位匹配 job/match（本地目录 204 岗位） | 30 | 108.1 | **187.8** | 187.9 | 187.9 | 本地匹配 + 报告分级 |
| 草稿列表 draft/list（1000 条全量） | 30 | 232.8 | **328.9** | 341.8 | 341.8 | 响应体约 **1.2MB**（1000 份完整简历） |
| AI 简历润色 light（单用户基线） | 2 | 13.5s | 28.9s | — | 28.9s | 真实模型调用 |
| AI 简历润色 light（5 用户并发） | 3 | 36.9s | 45.6s | — | 45.6s | 见下方排队分析 |

**写入吞吐**：1000 条草稿以 4 并发写入共耗时 12.8s（**78.2 req/s**），P99 = 77ms，零失败；WAL 模式下 SQLite 单写者不是该量级的瓶颈。

**AI 并发排队分析**：5 个用户同时发起 AI 润色，全部返回耗时 45.6s，单请求延迟相对单用户基线放大约 **2.2x**（上游中继按并发排队）。同一轮 5 次请求中：3 次成功、1 次被后端**事实守卫拦截**（`rewrite_fact_violation`，模型试图改写不可变更的简历事实，属预期防护行为）、1 次上游返回格式异常被降级为明确的 `ai_invalid_response` 错误——没有静默失败，也没有把上游异常透传成 500。

**已知的下一个优化点**（如实记录）：`draft/list` 会带出每份草稿的完整 payload，1000 条时响应体约 1.2MB、P95 约 330ms。列表接口返回摘要字段 + 详情按需拉取可以把响应体压缩一个数量级，这是当前架构下明确可做的下一步。

**运行间方差**：同一环境先后 3 轮完整压测，登录 P95 在 29~35ms、草稿列表 P95 在 329~406ms 之间波动；AI 预热单次耗时 15~28s 受上游负载影响明显。表格取自最后一轮完整数据。

## 复现步骤

```powershell
# 1. 启动隔离压测实例（独立 SQLite、独立端口、限流调高、不碰 8000 开发实例）
powershell -ExecutionPolicy Bypass -File scripts/benchmarks/start-bench-backend.ps1 -Port 8004 -Fresh

# 2. 跑基准（预置 1000 条草稿 → 各场景采样 → AI 并发排队）
resume-backend\.venv\Scripts\python.exe scripts\benchmarks\bench_api.py `
  --base http://127.0.0.1:8004 --db resume-backend\.bench\bench.db `
  --draft-count 1000 --samples 30 --ai-users 5
# 不想消耗真实 AI 配额时加 --skip-ai

# 3.（可选）用 Locust 做持续多用户负载，生成 HTML 报告
pip install locust
locust -f scripts/benchmarks/locustfile.py --host http://127.0.0.1:8004 `
  --headless -u 20 -r 5 -t 1m --html resume-backend/.bench/locust-report.html
```

两个脚本的分工：`bench_api.py`（零新增依赖，复用后端已装的 httpx）负责分位数延迟数据；`locustfile.py` 负责持续多用户负载下的吞吐与错误率观察。压测结束后可直接停止 8004 端口进程，`.bench/` 目录（已 gitignore）可整体删除。
