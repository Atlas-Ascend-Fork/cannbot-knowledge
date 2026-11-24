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

授权层有两条可切换的实现（`CANNBOT_MCP_SDK_AUTH`：默认空 = 手写链，`on` = 官方 SDK 栈）；两模式端点与防护差异表见 [README.md](README.md)「授权栈模式」。下表前四行是切到 `on` 后特有的症状。

| 症状 | 原因 | 处置 |
|---|---|---|
| 开启 `CANNBOT_MCP_SDK_AUTH=on` 后，已授权用户 `/mcp` 全部 401（OAuth 流程本身能走通） | 预期的一次性迁移代价：resource 标识从基地址变为完整端点 URL（`PUBLIC_URL/mcp`），存量 JWT 的 `aud` 全部失配（SDK 验签按 RFC 8707 严格比较） | 全员重新走一次 OAuth 授权即可恢复；`cbk_live_` API Key 与静态令牌不受影响，机器接入无感 |
| 设了 `SDK_AUTH=on` 但行为没变（启动日志见 `staying on the handwritten auth chain`） | `on` 模式强制要求显式 `CANNBOT_MCP_PUBLIC_URL`（SDK 的 issuer/resource 身份由它单源推导），缺失时 fail-closed 留在手写链，不崩溃 | 配置客户端可达的 `CANNBOT_MCP_PUBLIC_URL` 后重启；看启动日志确认实际模式 |
| SDK 模式下设备码客户端按 8414 元数据 `token_endpoint` 发设备码 grant 被拒 | 已知过渡缺口：SDK `/token` 单值端点不接受设备码 grant，设备码 grant 仍由 `/oauth/device/token` 服务 | 元数据驱动的设备码客户端继续用默认（关）模式；差异见 README「授权栈模式」 |
| SDK 模式下反复 401 不再触发 IP 冷却、429 限流未按 principal 生效 | 阶段一已知边界：SDK 模式 `/mcp` 暂未接 IP 冷却、按 principal 限流与调用日志 principal 归因（调用日志本身仍开启） | 需要这些防护的部署暂用默认（关）模式；勿在 SDK 模式下放开外网暴露 |
| HTTP 401 | 令牌错误或未进入进程环境 | 在启动客户端的终端里 `echo ${CANNBOT_MCP_TOKEN:0:8}` 验证前 8 位;改完 bashrc 须开新终端或先 `source` |
| OAuth 授权后仍 401 | GitCode 验证不可达或令牌无效(GitCode 侧已撤销授权) | 先确认 GitCode 可达(浏览器能登录);再在 GitCode 设置里检查应用授权状态;内网/网关故障期间可让部署方临时 `CANNBOT_MCP_GITCODE_VERIFY=off`(纯静态令牌模式),恢复后务必移除该变量 |
| 客户端报 JSON 解析错误(如 `Unrecognized token '<'`)后授权流程无进展 | 客户端把 `authorization_servers` 指到的主机当授权服务器取 RFC 8414 元数据,该主机返回了 HTML 而非 JSON(GitCode 即如此);本服务的 9728 已指向自身 8414,出现此症状通常是网关/反代把 `/.well-known/` 路径改写到了别的页面 | 核对反代是否原样放行 `/.well-known/oauth-protected-resource` 与 `/.well-known/oauth-authorization-server`(含 `/mcp` 变体)两条路径;确认 `CANNBOT_MCP_PUBLIC_URL` 指向客户端实际可达的本服务地址 |
| 客户端报 `Incompatible auth server: does not support dynamic client registration` | GitCode 不支持 OAuth 动态客户端注册(RFC 7591),客户端又没有预注册的 client_id | 在 GitCode 注册 OAuth 应用:登录后打开 **`https://gitcode.com/setting/oauth/create`**(设置 → OAuth 应用 → 创建),填应用名与回调地址(客户端本机回环,如 `http://127.0.0.1:19876/mcp/oauth/callback`),创建后把 client_id 填进客户端 MCP 配置(如 OpenCode/cannbot 的 `oauth.clientId`,应用列表在 `/setting/oauth`);应用注册完成前,可先用 GitCode PAT 作为 `Authorization: Bearer` 头直连 |
| 客户端报元数据里授权服务器不可达 | 9728 的 `authorization_servers` 默认按 Host 头推导本服务地址,生产域名/端口与客户端所见不一致时推导错误 | 在服务端设置 `CANNBOT_MCP_PUBLIC_URL` 为客户端可达的对外地址(含协议与端口) |
| 元数据端点 404 | `CANNBOT_MCP_GITCODE_VERIFY=off`(GitCode 轨被关闭,不广播 OAuth 声明) | 属预期行为;需要 OAuth 时移除该变量并重启 |
| 401 十次后持续被拒(约 5 分钟) | 认证失败 IP 冷却:1 分钟内 10 次 401 触发封禁 | 等待 5 分钟或重启服务器;先修正令牌再重试,避免反复撞线 |
| HTTP 429 | 触发限流(仅显式设置了 `CANNBOT_MCP_RATE_LIMIT` 时;计数按 principal,同一身份多把令牌合并) | 按 `Retry-After` 头等待重试;默认限流关闭,出现 429 说明部署方显式启用了 |
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
- **`trust_tier: unverified`**:表示该卡没有发生过真实复核事件,不影响返回,采信结论时按卡片正文核对来源;
- **SDK_AUTH 切换后的存量令牌失效**:resource 标识（`aud`）随授权栈模式变化，切换 `CANNBOT_MCP_SDK_AUTH` 后旧令牌 401 是**一次性迁移代价**，重新走一次授权即恢复，不是令牌损坏或配置错误。
