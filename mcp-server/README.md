# cannbot-knowledge MCP 服务

本目录是知识库检索契约的 MCP（Model Context Protocol）适配层：把既有 `knowledge-query` CLI 的召回与读卡能力以**三个只读工具**暴露给任意 MCP 客户端（Claude Desktop、Cursor、Claude Code、VS Code Copilot 等）。服务器是适配层而不是新检索引擎——`search`/`discover` 经 subprocess 调用既有 CLI 并原样透传其 JSON payload（含 fail-closed 索引校验），`read_card` 在 `knowledge/` Bundle 根内代读卡片。各客户端配置样例见 [MCP_CONFIG.md](MCP_CONFIG.md)。

**做什么**：三只读工具 `discover` / `search` / `read_card`，返回候选卡定位符与卡片全文证据，供 AI 研发助手检索受治理的 Ascend C / CANN 知识。

**不做什么**：不写知识仓任何路径（不写 receipt、artifacts、索引）；索引缺失或过期时拒绝服务而不是自动重建；不对检索结果做语义加工或回答生成——选卡、阅读深度和证据采用由客户端 Agent 决定。

**故障排查**：接入、认证、运行时与索引四层的症状对照见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

## 前置条件

- **Python 3.10+** 与 [uv](https://docs.astral.sh/uv/)（或自行用 pip 建虚拟环境，依赖见 `pyproject.toml`：MCP SDK `mcp>=2,<3` 及 HTTP 传输依赖，只进本目录不进根 requirements）；
- 本地知识仓 checkout（stdio 模式；HTTP/Docker 部署在服务端）；
- 检索索引已构建（项目安装器 `install.sh` 会自动准备；索引相对当前提交过期时服务器 fail-closed 拒答，见 TROUBLESHOOTING.md）；
- HTTP 模式需预生成至少一把令牌（清单为空拒绝启动）。

## 工具面

| 工具 | 职责 |
|---|---|
| `discover` | 无参数返回知识库各维度真实覆盖计数与索引 provenance；也是 MCP 协议层最便宜的业务健康检查（编排系统探活另见下方 `GET /health`） |
| `search` | 14 个过滤参数与 CLI 一一映射（零参数改写、零默认值注入），返回排序候选卡定位器 |
| `read_card` | 按 search 结果的 path 读卡片：分页正文（默认 200 行/上限 500）、frontmatter 对象、sources/source_headers、已解析 links、images、stdio 模式附加 local_only |

三个工具均标注 `readOnlyHint`。平台纪律 fail-closed：`platform` 是可选参数，缺失且无环境变量缺省时调用报错并指导补参，而不是静默混合各平台结果。**逐参数参考与典型调用流程见 [TOOLS.md](TOOLS.md)。**

## 版本与升级

- MCP SDK 约束 `mcp>=2,<3`，依赖隔离在本目录 `pyproject.toml`，不影响仓库根环境；
- 升级 = 在知识仓 `git pull` 后重启服务器进程（stdio 重启客户端即可；Docker 部署见 [docker/DOCKER.md](docker/DOCKER.md)，容器重启会自动重建索引）；
- 破坏性变更与行为历史见仓内 `logs/`。

## 启动

### stdio（本地，默认）

```bash
uv --directory mcp-server run server.py
```

知识根解析与 CLI 同链：`CANNBOT_KNOWLEDGE_ROOT` 环境变量 → 当前目录向上查找 `.cannbot/knowledge.env` → 服务器所在仓库。stdio 模式无认证、无限流、默认不记调用日志。

### Streamable HTTP（团队共享）

```bash
export CANNBOT_MCP_TOKENS="cbk_<token1>:zhangsan,cbk_<token2>:lisi,cbk_<token3>"   # token:label 逗号分隔；裸令牌=匿名
uv --directory mcp-server run server.py --transport http
```

- 端点 `POST /mcp`，stateless Streamable HTTP（无会话粘滞）；
- 无认证探活端点 `GET /health`：固定返回 `{"status":"ok"}`，供 K8s/APISIX 等编排系统健康检查；不参与认证、限流与调用日志，业务级健康（索引与检索链路）仍用 `discover` 工具验证；
- 令牌清单为空时进程拒绝启动（退出码 2）；
- 每令牌滑动窗口限流默认关闭（`0`）；设置 `CANNBOT_MCP_RATE_LIMIT=N` 启用，超限 429 + `Retry-After`；
- 认证失败按直连 IP 冷却：1 分钟内 10 次 401 → 封禁 5 分钟（不信任 `X-Forwarded-For`）；
- HTTP 模式默认记调用日志。

令牌生成：`python3 -c "import secrets; print('cbk_' + secrets.token_urlsafe(32))"`（≥32 字节熵）。

令牌生命周期：**轮换**——生成新令牌加入 `CANNBOT_MCP_TOKENS` 清单（新旧并存）并重启进程，通知使用者全部切换后再移除旧令牌、再次重启；**撤销**——从清单移除并重启即可，令牌只在运行中的进程内存与部署环境（env / tokens.env）里存在，无服务端落库；**泄露处置**——立即从清单移除并重启，检查调用日志中该 principal 的异常调用（日志记录 principal 与查询内容明文，见「调用日志与离线分析」）；已知边界：令牌明文存于环境变量（无 UI 做不到哈希落库），label 是凭证记账不是身份认证。

### Docker（一键部署，团队共享）

无需宿主 Python：克隆本仓后在 `docker/` 目录生成令牌文件并 `docker compose up -d --build`，检索索引在容器内自动构建、知识更新后随容器重启自动重建。部署、运维、迁移与容量手册见 [docker/DOCKER.md](docker/DOCKER.md)。

容器内直接启动亦可使用 `platform-start.sh`（通用容器启动入口，自定位仓库根）：先校验检索索引（缺失或过期时容器内重建，失败即退出保持 fail-closed），随后以 HTTP 传输启动服务器；配合 `index_adopt.py` 可对持久卷上的索引做内容级采纳——全新克隆重写全部文件 mtime 时，逐卡 sha256 核验一致并恢复 mtime 即可跳过重建，任何内容差异仍走重建（fail-closed 不降级）。本地冒烟可先安装依赖并设置 `CANNBOT_MCP_TOKENS` 后直接 `bash mcp-server/platform-start.sh`。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `CANNBOT_KNOWLEDGE_ROOT` | （复用 CLI 解析链） | 知识根，与 Skill/CLI 同一解析顺序 |
| `CANNBOT_KNOWLEDGE_PLATFORM` | 空 | 缺省平台，与安装器 `.cannbot/knowledge.env` 对齐 |
| `CANNBOT_MCP_TRANSPORT` | `stdio` | `stdio` / `http`（`--transport` 参数优先） |
| `CANNBOT_MCP_HOST` / `CANNBOT_MCP_PORT` | `127.0.0.1` / `8090` | HTTP 模式绑定地址与端口 |
| `CANNBOT_MCP_TOKENS` | 空 | HTTP 令牌清单，`token:label` 逗号分隔（裸令牌=匿名）；HTTP 模式必填，清单为空拒绝启动 |
| `CANNBOT_MCP_RATE_LIMIT` | `0`（关闭） | 每令牌每分钟请求上限（滑动窗口）；`0` 关闭；超限 429 |
| `CANNBOT_MCP_LOG` / `CANNBOT_MCP_LOG_DIR` | `auto` / `~/.local/state/cannbot-knowledge/mcp` | 调用日志开关（`on`/`off`/`auto`，auto=HTTP 开、stdio 关）与目录 |
| `CANNBOT_MCP_LOG_UPLOAD_REMOTE` | `https://gitcode.com/qixingkai/cannbot-knowledeg-log.git` | 日志自动上传远端仓；与 `LOG_UPLOAD_INTERVAL` 一起启用 |
| `CANNBOT_MCP_LOG_UPLOAD_INTERVAL` | `0`（关闭） | 自动上传间隔（秒）；仅 HTTP 且日志开启时生效，`0` 不启动上传线程 |
| `CANNBOT_MCP_LOG_UPLOAD_BRANCH` | `main` | 自动上传目标分支 |
| `CANNBOT_MCP_MAX_SUBPROCS` | CPU 核数 | search/discover 子进程并发信号量上限，超出排队 |
| `CANNBOT_MCP_SUBPROC_TIMEOUT` | `30` | 子进程硬超时（秒），挂死的 CLI 被杀并返回结构化 tool error |
| `CANNBOT_MCP_HEADERS_ROOT` | 空 | 仅 stdio 模式：read_card `local_only.headers_root` 报告的本地 CANN Ascend C 组件根 |

日志目录若配置在知识仓内，日志功能拒绝启用（绝不写仓内任何路径）。

## 调用日志与离线分析

HTTP 模式默认（stdio 默认关闭，`CANNBOT_MCP_LOG=on` 可开）在仓外目录写 JSONL，按 UTC 日分文件（`calls-YYYY-MM-DD.jsonl`）：每次 `tools/call` 一行，认证失败与限流各记独立事件行（`auth_failed`/`rate_limited`）。调用行 schema 标记为 `mcp-call-log.v2`；无 schema 字段的旧行按 v1 解析。

v2 调用行字段（"来源工具"列表示该键只在对应工具的行出现）：

| 字段 | 类型 | 语义 | 来源工具 |
|---|---|---|---|
| `schema` | str | 行格式版本标记，恒为 `mcp-call-log.v2` | 全部 |
| `ts` | str | UTC 时间戳（毫秒精度） | 全部 |
| `call_id` | str | 调用事件标识：每次调用随机生成一次的短十六进制串，同一调用行唯一稳定；多实例汇聚时同一行的完全重复副本按它幂等去重，旧行无此字段按缺失解析 | 全部 |
| `boot_id` | str \| null | 进程启动标识：服务器进程启动时生成一次的随机短十六进制串，同一进程的所有调用行/事件行同值；用于多实例与 stdio 并发会话的行归组，旧行无此字段按缺失解析 | 全部 |
| `transport` | str | `stdio` / `http` | 全部 |
| `principal` | str \| null | 命中令牌的 label；匿名令牌与 stdio 为 null | 全部 |
| `tool` | str | `discover` / `search` / `read_card` | 全部 |
| `args` | object | 本次调用的工具参数原样 | 全部 |
| `ok` | bool | 调用成功与否 | 全部 |
| `count` | int \| null | search 命中数 / discover 覆盖卡片数 / read_card null | 全部 |
| `latency_ms` | number | 服务端耗时毫秒（保留 1 位小数） | 全部 |
| `request_sha256` | str \| null | CLI 请求审计摘要（search 透传）；其余与失败行为 null | 全部 |
| `index` | object \| null | 响应携带的索引 provenance；失败为 null | 全部 |
| `hits` | array \| null | search 命中卡 path 列表；其余为 null | 全部 |
| `scores` | array \| null | 与 hits 一一对应的排序分数 | 仅 search |
| `card_sha256` | str \| null | 所读卡片文件内容 SHA-256 | 仅 read_card |
| `total_lines` | int \| null | 卡片总行数 | 仅 read_card |
| `returned_lines` | int \| null | 本次返回行数 | 仅 read_card |
| `truncated` | bool \| null | 是否仍有未读内容（续读用 next_offset） | 仅 read_card |
| `response_sha256` | str \| null | 成功响应 canonical JSON 的 SHA-256（跨实例稳定，漂移检测信号；摘要前剥离实例本地路径：search 结果的 `local_path`、discover 的 `root`、read_card stdio 的 `local_only`，响应本体不变）；失败为 null | 全部 |
| `response_bytes` | int \| null | 摘要所用 canonical JSON 字节数（剥离实例本地路径后）；失败为 null | 全部 |
| `error` | str \| null | 失败时返回客户端的 tool error 文本；成功为 null | 全部 |
| `error_kind` | str \| null | 失败分类（见下）；成功为 null | 全部 |
| `jsonrpc_id` | any \| null | HTTP 请求 JSON-RPC id 原样回填；stdio 为 null | 全部 |

失败行 `error_kind` 枚举：`invalid_argument`、`path_out_of_bundle`、`path_not_indexed`、`offset_out_of_range`、`subprocess_timeout`、`cli_error`、`platform_missing`、`index_missing`、`index_stale`、`internal`。事件行只含 `schema`/`ts`/`boot_id` 与事件字段：`auth_failed`（src_ip、reason、ip_cooldown 附 retry_after_s）、`rate_limited`（principal、tool、retry_after_s）。

**留存与权限**：趋势与漂移分析建议至少保留 90 天日志，用 logrotate 等工具归档，不配置自动删除——调用日志是"用户在查什么、哪些知识被消费"的唯一事实源，删了就无法重建。日志含 `principal`（真实人名 label）与 `args` 中的查询内容明文，属敏感数据：日志目录权限应设为仅维护者可读（如 `chmod 700`），外网部署时把日志目录纳入审计范围。

离线聚合：

```bash
python3 mcp-server/analyze_logs.py --days 30 [--log-dir /path/a,/path/b] [--top 20] [--output report.json]
```

同时产出人读 Markdown 摘要（同目录同名 .md）。产出七张榜：零命中聚合（每条附 knowledge_request Issue"已尝试的检索"一节可粘贴文本）、查询词热度、卡片阅读热度、平台需求分布、读深度（阅读深度/单次阅读占比/翻页续读占比；阅读深度按会话内 offset 覆盖区间并集计算，会话 = 同 principal——匿名时同 `boot_id`——相邻调用间隔 ≤15 分钟归一段）、失败分类（`error_kind` 计数 + 每类高频查询词，`platform_missing` 的高频词即平台需求信号）、周分桶趋势（按周一~周日日期区间，如 2026-10-19~10-25），以及多实例漂移告警（同 request_sha256 不同 response_sha256）；principal 全 null 时报告头部标注匿名模式。报告默认写 `~/.local/state/cannbot-knowledge/mcp/reports/`，不自动开 Issue。

### 日志自动上传（多实例汇聚）

配置远端仓并设置非 0 间隔后，HTTP 服务器进程内起一个后台守护线程，按周期把日志目录的 `calls-*.jsonl` 推送到该仓——多实例的按日分文件名天然不冲突，全部实例的日志汇入同一仓，维护者在任一机器 analyze 前先 `git pull` 即可拿到全局数据。默认关闭（间隔 `0` 不启动线程），零配置时进程行为与现在完全一致；stdio 模式不启动（本地单机无分散问题）。

| 变量 | 默认 | 说明 |
|---|---|---|
| `CANNBOT_MCP_LOG_UPLOAD_REMOTE` | `https://gitcode.com/qixingkai/cannbot-knowledeg-log.git` | 上传目标仓 |
| `CANNBOT_MCP_LOG_UPLOAD_INTERVAL` | `0`（关闭） | 上传间隔（秒），非 0 启用 |
| `CANNBOT_MCP_LOG_UPLOAD_BRANCH` | `main` | 上传目标分支 |

工作机制与边界：

- 日志目录本身作为 git 工作区：首次上传自动 `git init` 并配置 remote；每轮 `git add calls-*.jsonl` + commit（提交信息含 hostname、`boot_id` 与日期，多实例可区分来源）+ push；无变更的轮次跳过 commit/push（幂等空转）。
- `reports/` 子目录写入 `.gitignore` 不上传（分析产物可本地再生且含人名聚合）；`calls-*.jsonl` 声明 `merge=union` 合并策略——两个实例对同一日文件并发追加时按行并集收敛，不丢行；重复行由 `analyze_logs.py` 的 `call_id` 幂等键去重（有该字段的行按 `call_id` 去重；旧行无该字段，按 `(ts, tool, principal, request_sha256)` 去重）。
- 上传失败（网络断、认证失败、远端不可达）只记 stderr 一行诊断并下轮重试，对请求路径零影响；线程为守护线程，进程退出自动终止。
- **凭证**：HTTPS 推送凭证走部署机当前用户的 git credential helper（如 `git config credential.helper store` 或系统 keyring），不进环境变量、不进服务器配置文件。
- **隐私**：上传仓应设为私有仓。日志含 `principal`（真实人名 label）与查询内容明文，汇聚仓的读权限应与上文"留存与权限"的日志目录同级对待。

## 多实例部署边界

```text
机器 A：git clone + knowledge_index.py build + mcp-server   ← 完全独立
机器 B：git clone + knowledge_index.py build + mcp-server   ← 完全独立
机器 C：git clone + knowledge_index.py build + mcp-server   ← 完全独立
```

- **零协调成立的理由**：服务 stateless（任意副本处理任意请求）；数据是纯 git 仓（clone + 建索引即完整分发）；SQLite 只读连接多进程/多机安全。实例间 commit 可短暂不一致——无害，每次响应自带索引 provenance。
- **边界 1：日志分散**——各实例各写本地 JSONL，用 `analyze_logs.py --log-dir a,b,c` 多目录合并（`call_id` 参与幂等键去重，旧行按 `(ts, tool, principal, request_sha256)`）；或开启"日志自动上传"让各实例自动汇聚到同一仓（见上节），维护者 analyze 前先 `git pull`。
- **边界 2：限流每台各限**——设 `CANNBOT_MCP_RATE_LIMIT=N` 后，N 次/分钟在 N 台实例上是"每台各 N"而非全局 N；子进程并发闸同理。需要全局限流时以 Redis 实现替换限流接口（接口已预留），或由前置 LB 统一执行。
- **更新窗口约定**：维护者显式 `git pull` 后立即连续执行索引重建（`knowledge_index.py build`），再对外提供服务；pull 与重建之间服务保持 fail-closed 拒答（实测重建约 65s，该窗口内查询返回带修复指引的 tool error，不会读到新旧混合数据）。服务器自身绝不自动更新或重建。
- **LB 建议（可选）**：Streamable HTTP stateless 下无需会话粘滞；按真实客户端 IP 的封禁/限流需在反代层配置（服务端只看直连地址，默认不信任 `X-Forwarded-For`）。

## 外网暴露前置条件清单

默认按内网部署；开放外网前逐项核对：

- [ ] **TLS**：服务自身只听 HTTP，TLS 由反向代理（nginx/Caddy 等）终止。
- [ ] **令牌强度**：每把令牌 ≥32 字节随机熵（见生成命令）；开外网前轮换全部存量令牌。
- [ ] **限流确认**：设置 `CANNBOT_MCP_RATE_LIMIT` 为非 0 正整数，并按预期用户量评估上限。
- [ ] **审计留存**：调用日志与 `auth_failed` 事件行的留存、目录权限与巡检安排（见"调用日志与离线分析"的留存与权限小节）。
- [ ] **认证失败日志核对**：确认日志目录与保留策略覆盖 IP 冷却事件。

已知未覆盖项（如实声明）：全局限流需 Redis（接口留位，v1 未实现）；`label` 是凭证记账而非身份认证（令牌转手后日志仍记原 label）；令牌清单管理在约 50 人量级以上应迁移 OAuth2。

## 依赖隔离

服务器依赖（官方 `mcp` SDK、uvicorn、PyYAML）只声明在本目录 `pyproject.toml`，由 `uv` 在本目录内解析安装；仓库根 `requirements.txt` 保持仅 PyYAML 不变。不使用 MCP 服务器的用户路径零变化。`analyze_logs.py` 仅用标准库，可直接用系统 Python 运行。

## 测试

```bash
# 端到端（进 check.sh 门禁；需要 mcp-server/.venv 或 uv）
python3 -m unittest discover -s evals -p 'test_mcp_server.py' -v

# 单元测试（需在本目录 venv 内运行）
uv --directory mcp-server run python -m unittest discover -s tests -v
```
