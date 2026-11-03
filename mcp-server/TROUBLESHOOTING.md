# MCP 接入故障排查

按症状组织,覆盖接入、认证、运行时与索引四层。工具参数语义见 [TOOLS.md](TOOLS.md),部署与配置见 [README.md](README.md)。

## 分层定位

远程(HTTP)接入按层排查:**网络可达(ping / TCP 443)→ 认证与协议(initialize / tools/list)→ 工具执行(discover)**。10 秒端到端健康检查:

```bash
curl -sS --max-time 20 -X POST "http://<host>:8090/mcp" \
  -H "Authorization: Bearer $CANNBOT_MCP_TOKEN" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -w "\nHTTP=%{http_code}\n"
```

预期 HTTP=200,tools 里出现 discover / search / read_card 三件套。stdio(本地)接入跳过网络层,直接从工具执行层查起。

K8s/APISIX 等编排系统另有**无认证探活端点** `GET /health`(固定返回 `{"status":"ok"}`,不进认证/限流/调用日志):编排探活用它,业务级健康(索引与检索链路)用 `discover` 验证——`/health` 通而 `discover` 不通,问题在索引或知识根,不在网络与认证。

## 症状 → 原因 → 处置

### 接入与启动

| 症状 | 原因 | 处置 |
|---|---|---|
| 客户端报 MCP 服务器启动超时 | 首次启动 `uv --directory mcp-server run server.py` 需解析依赖;部分客户端(如 OpenCode)默认 MCP 启动超时仅 5 秒 | 在客户端配置中显式加大超时(如 OpenCode 设 `"timeout": 120000`);或先手动 `cd mcp-server && uv sync` 预热依赖,后续启动为秒级 |
| `command not found: uv` | PATH 上没有 uv | 安装 uv(见 [uv 官方安装脚本](https://docs.astral.sh/uv/getting-started/installation/));或改用 pip/venv 启动(见 [MCP_CONFIG.md](MCP_CONFIG.md)) |
| 工具列表里没有三件套 | 客户端不热加载 MCP 配置 | 从**新终端**重启客户端;确认配置文件路径与 JSON 语法正确 |
| stdio 模式发现的知识根不对 | `CANNBOT_KNOWLEDGE_ROOT` 未设置时按解析链回退 | 显式在 env 块设 `CANNBOT_KNOWLEDGE_ROOT` 为知识仓绝对路径 |

### 认证(HTTP)

| 症状 | 原因 | 处置 |
|---|---|---|
| HTTP 401 | 令牌错误或未进入进程环境 | 在启动客户端的终端里 `echo ${CANNBOT_MCP_TOKEN:0:8}` 验证前 8 位;改完 bashrc 须开新终端或先 `source` |
| 401 十次后持续被拒(约 5 分钟) | 认证失败 IP 冷却:1 分钟内 10 次 401 触发封禁 | 等待 5 分钟或重启服务器;先修正令牌再重试,避免反复撞线 |
| HTTP 429 | 触发每令牌限流(仅显式设置了 `CANNBOT_MCP_RATE_LIMIT` 时) | 按 `Retry-After` 头等待重试;默认限流关闭,出现 429 说明部署方显式启用了 |
| 进程启动即退出(退出码 2) | HTTP 模式 `CANNBOT_MCP_TOKENS` 为空,拒绝启动 | 配置令牌清单后重启;生成:`python3 -c "import secrets; print('cbk_' + secrets.token_urlsafe(32))"` |

### 工具执行

| 症状 | 原因 | 处置 |
|---|---|---|
| search 报错、提示需要 platform | `platform` 缺失(fail-closed 设计行为) | **不是故障**:确认目标平台后带 `platform` 重试(合法值见 TOOLS.md);或在服务器 env 设 `CANNBOT_KNOWLEDGE_PLATFORM` 缺省 |
| 报 index missing / stale | 索引缺失或相对当前提交过期,服务器拒绝服务(fail-closed,不自动重建) | 交由知识仓维护者或项目安装器重建索引;stdio 本地可对正确知识根重跑安装器 |
| read_card 报 path_not_indexed | path 不在索引中(手拼路径或索引已更新) | 先 search 拿最新 `path`,再 read_card |
| read_card 报 offset_out_of_range | offset 超出卡片末行 | 续读永远传上次返回的 `next_offset`;不要自行累加行数 |
| 请求超时(约 30 秒后报 subprocess_timeout) | search/discover 子进程被硬超时杀掉 | 缩小检索范围、减小 limit 重试;持续超时交维护者查 CLI |
| search 返回 0 结果 | 合法零命中,或过滤条件过窄 | 换关键词、放宽 domain/technology/type 过滤、提高 limit;确认平台正确;仍零命中如实报告,不用其他平台卡片替代 |

### 多实例与漂移

| 症状 | 原因 | 处置 |
|---|---|---|
| 同一查询不同时间返回不同结果 | 多实例部署的知识根/索引版本不一致 | 见 README「多实例部署边界」;维护者用 analyze_logs 的漂移告警定位 |
| Pod 重建后启动 4–5 分钟才就绪 | 容器内重建检索索引(约 8,400 张卡) | 正常启动窗口;平台部署经 `mcp-server/index_adopt.py` 内容级采纳持久化索引可跳过重建,见 README Docker 节 platform-start.sh 与 index_adopt.py |

## 错误码速查(error_kind)

工具失败按结构化 `error_kind` 返回,语义见 [TOOLS.md](TOOLS.md#错误分类error_kind)。

## 什么不是故障

- **platform fail-closed**:省略 `platform` 且无缺省时报错,是防止静默混合平台的**设计行为**;
- **索引拒答(fail-closed)**:索引 stale 时拒绝服务而不是自动重建,服务器对知识仓严格只读;
- **零命中**:索引正常时零命中是有效结果,不是错误;
- **`trust_tier: unverified`**:表示该卡没有发生过真实复核事件,不影响返回,采信结论时按卡片正文核对来源。
