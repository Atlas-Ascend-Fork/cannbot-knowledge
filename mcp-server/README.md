# cannbot-knowledge MCP 服务

本目录提供 cannbot-knowledge 知识库的 MCP 服务，支持 Cursor、Claude Code、VS Code Copilot 等 MCP 客户端接入，供 AI 研发助手检索 Ascend C / CANN 知识。服务提供 `discover` / `search` / `read_card` 三个只读工具，分别用于浏览知识覆盖、检索候选卡片、阅读卡片全文。各客户端配置样例见 [MCP_CONFIG.md](MCP_CONFIG.md)。

**检索引擎**：`search`/`discover` 经 RetrievalEngine interface 执行既有 CLI 检索契约——默认为进程内常驻引擎（启动一次加载、按调用复用、每次调用校验索引指纹，毫秒级返回），`CANNBOT_MCP_ENGINE=subprocess` 可切回子进程 CLI 适配器用于进程级隔离诊断；索引缺失或过期时 fail-closed 拒答（不自动重建），`read_card` 在 `knowledge/` Bundle 根内代读卡片。

**故障排查**：接入、认证、运行时与索引四层的症状对照见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

## 前置条件

- **Python 3.10+** 与 [uv](https://docs.astral.sh/uv/)（或自行用 pip 建虚拟环境，依赖见 `pyproject.toml`：MCP SDK `mcp>=2,<3` 及 HTTP 传输依赖，只进本目录不进根 requirements）；
- 本地知识仓 checkout（stdio 模式；HTTP/Docker 部署在服务端）；
- 检索索引已构建（项目安装器 `install.sh` 会自动准备；索引相对当前提交过期时服务器 fail-closed 拒答，见 TROUBLESHOOTING.md）。

## 工具列表

| 工具 | 职责 |
|---|---|
| `discover` | 无参数返回知识库各维度真实覆盖计数与索引 provenance；也是 MCP 协议层最便宜的业务健康检查（编排系统探活另见下方 `GET /health`） |
| `search` | 15 个参数与 CLI 一一映射（零参数改写、零默认值注入；含 `alt_query` 双语双搜，两条查询腿名次交错融合，见 TOOLS.md），返回排序候选卡定位器 |
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

以 HTTP 服务启动，监听 `127.0.0.1:8090`（地址与端口可用 `CANNBOT_MCP_HOST` / `CANNBOT_MCP_PORT` 修改），服务端点为 `POST /mcp`：

```bash
uv --directory mcp-server run server.py --transport http
```

启动时无需配置任何令牌：用户经 GitCode OAuth 授权接入，脚本等无人值守场景经自服务 API Key 接入（见下方[认证](#认证四轨)）。需要静态引导令牌时（如首次部署、GitCode 不可达的应急场景）先设置环境变量再启动：

```bash
export CANNBOT_MCP_TOKENS="cbk_<token>:zhangsan"   # token:label 逗号分隔，可省略
uv --directory mcp-server run server.py --transport http
```

启动与日志行为：

- 三种认证配置（静态令牌、GitCode 验证、自建授权）全部关闭时拒绝启动（退出码 2）；任意一种开启即可正常启动；
- HTTP 模式默认记调用日志（格式与留存见 [调用日志与离线分析](#调用日志与离线分析)）。

#### 健康检查

| 端点 | 用途 | 说明 |
|---|---|---|
| `GET /health` | 编排系统探活 | 固定返回 `{"status":"ok"}`，无认证、不参与限流与调用日志；供 K8s/APISIX 等使用 |
| `discover` 工具 | 业务级健康检查 | 一次调用即验证索引与检索链路，比探活更全面 |

#### 认证（四轨）

`POST /mcp` 接受四种凭证，任一通过即放行，都失败返回 401：

| 凭证 | 形态 | 适用 | 验证方式 |
|---|---|---|---|
| 静态令牌 | `cbk_` 前缀，环境变量预配置 | 引导/应急通道 | 本地清单比对 |
| GitCode OAuth/PAT 令牌 | GitCode 发放的访问令牌 | 个人用户 | 调 GitCode 用户接口换用户名（缓存 60 秒） |
| 自签 JWT | `eyJ` 开头的三段式（本服务自建授权服务器签发） | 已完成 OAuth 的用户 | 本地 HS256 验签 |
| 自服务 API Key | `cbk_live_` 前缀 | 无人值守场景（CI、脚本） | 本地 scrypt 哈希校验 |

凭证分流规则：`cbk_live_` 前缀只走本地 API Key 校验、本服务自签 JWT 只走本地验签，两者**永不外发** GitCode；其余令牌走 GitCode 验证轨，失败不回退到其他轨。

##### GitCode OAuth（个人用户）

在 GitCode 上用本人账号授权后获得访问令牌，直接作为 `Authorization: Bearer` 使用，无需向运营方领静态令牌；服务端通过 GitCode 用户接口换取用户名记入调用日志 principal（结果缓存 60 秒）。令牌由 GitCode 发放（有效期以 GitCode 侧为准，通常 15 天）并自动续期；GitCode 侧撤销授权即失去访问权。完整浏览器授权前需管理员先在 GitCode 注册 OAuth 应用（一次性操作，见 [MCP_CONFIG.md](MCP_CONFIG.md)）；应用注册完成前，GitCode 个人访问令牌（PAT）同样走这条验证轨，可作过渡接入方式。

##### 自服务 API Key（无人值守接入推荐方式）

用户先走一次 OAuth（设备码或授权码流程）拿到 access JWT，然后调 `POST /api/keys`（`Authorization: Bearer <JWT>`，body `label=用途说明`）为自己生成一把只能访问本服务的专用令牌；响应中的完整 key（`cbk_live_` 前缀）仅返回一次，服务端只存 scrypt 哈希。脚本或 CI 拿这把 key 直接访问 `/mcp`，principal 记为 `owner/label`（审计能同时回答谁生成、哪个用途在用）。`GET /api/keys` 列表、`DELETE /api/keys?key_id=...` 撤销均由本人自助完成，无需管理员。每用户最多 10 把有效 key，撤销立即生效。

相比直接把 GitCode PAT 塞给 CI 的优势：key 只能访问本服务（GitCode PAT 能操作你全部仓库）、可单独撤销、审计粒度到机器槽位。

##### 静态令牌（引导/应急通道）

首次部署尚未有人完成 OAuth 时、或 GitCode 不可达的应急场景，可用环境变量静态清单引导：

- **生成**：`python3 -c "import secrets; print('cbk_' + secrets.token_urlsafe(32))"`；
- **轮换**：新令牌加入清单（新旧并存）重启，使用者切换后移除旧令牌再重启；
- **撤销**：从清单移除并重启；
- **已知边界**：令牌明文存于环境变量，label 是记账不是身份认证——长期机器接入请迁移到自服务 API Key。

##### 验证轨开关

| 变量 | 效果 |
|---|---|
| `CANNBOT_MCP_GITCODE_VERIFY=off` | 关闭 GitCode 验证轨：`/mcp` 不再外呼 GitCode 验证令牌（内网/网关不可达时临时回退） |
| `CANNBOT_MCP_AUTH_SERVER=off` | 端到端关闭自建授权服务器：设备码/授权码/激活/`/api/keys` 签发端点全部 404，`/mcp` 不再接受自签 JWT 与自服务 API Key |
| 两者都 `off` | 只剩静态令牌一种认证方式，声明端点一并 404 |

两个开关互不影响。

#### OAuth 接入无需手工配置

MCP 客户端接入时不需要手工填任何授权地址：客户端第一次连接 `/mcp` 收到 401 后，会根据响应里的指引自动获取授权地址并发起浏览器授权，全程零配置。

服务端为此公开两个只读端点（均无需认证）：`/.well-known/oauth-protected-resource` 告诉客户端"本服务需要授权、授权服务器在哪"，`/.well-known/oauth-authorization-server` 告诉客户端"授权和换取令牌的地址、支持哪些授权方式"。

这两个端点在自建授权服务器开启时（默认）返回本服务的授权入口，在 `CANNBOT_MCP_AUTH_SERVER=off` 时返回 GitCode 的授权入口。若客户端无法通过它们取到正确内容，排查方向见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

#### 限流与封禁

| 机制 | 行为 | 配置 |
|---|---|---|
| 限流 | 按身份计数的滑动窗口，超限返回 429 + `Retry-After` | `CANNBOT_MCP_RATE_LIMIT`（每身份每分钟上限，`0` 关闭） |
| 限流计数键 | 默认按 principal（同一身份多把令牌合并窗口） | `CANNBOT_MCP_RATE_KEY`（`principal` 或 `token`） |
| 认证失败封禁 | 1 分钟内 10 次 401 → 封禁该来源 IP 5 分钟（不信任 `X-Forwarded-For`） | 无（固定行为） |

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
| `CANNBOT_MCP_TOKENS` | 空 | 静态令牌清单（引导/应急通道），`token:label` 逗号分隔（裸令牌=匿名）；可为空（GitCode/自建授权默认开启时正常启动）；与 GitCode、自建授权同时关闭才拒绝启动 |
| `CANNBOT_MCP_RATE_LIMIT` | `0`（关闭） | 每 principal 每分钟请求上限（滑动窗口）；`0` 关闭；超限 429 |
| `CANNBOT_MCP_RATE_KEY` | `principal` | 限流计数键：`principal`（默认，按身份合并）或 `token`（按令牌计数） |
| `CANNBOT_MCP_GITCODE_VERIFY` | 开 | `off` 关闭 GitCode 验证轨（/mcp 不再外呼 GitCode 验证令牌）；自建授权服务器不受影响 |
| `CANNBOT_MCP_AUTH_SERVER` | 开 | `off` 端到端关闭自建授权服务器：设备码/授权码/激活/`/api/keys` 端点全部 404，`/mcp` 不再接受自签 JWT 与自服务 API Key（只剩 GitCode 验证轨 + 静态令牌）；两轨都关时发现端点一并 404 |
| `CANNBOT_MCP_SDK_AUTH` | 空（关） | 授权栈模式开关：`on` 挂载官方 MCP SDK auth 栈（必配 `CANNBOT_MCP_PUBLIC_URL`，存量 JWT 失效需重新授权）；空保持手写链。`on` 模式特有的症状与处置见 [TROUBLESHOOTING 认证一节](TROUBLESHOOTING.md#认证http) |
| `CANNBOT_MCP_GITCODE_API` | `https://api.gitcode.com` | GitCode 用户接口 base（内网代理部署可覆盖） |
| `CANNBOT_MCP_OAUTH_CLIENT_ID` / `CANNBOT_MCP_OAUTH_CLIENT_SECRET` | 空 | 预注册 GitCode OAuth 应用凭证。仅服务端使用：作为设备码/授权码流程中 GitCode 登录腿的身份源，**绝不发给任何客户端**（`/register` 返回的是本服务公共客户端注册，无 secret）；未配置时授权页退回手填用户名（仅限可信网络引导部署） |
| `CANNBOT_MCP_PUBLIC_URL` | 按 Host 头推断 | 元数据里声明的本服务对外 URL（生产域名与端口不匹配时必配；**多副本部署必须显式配置**——所有节点共享同一值，否则 JWT 的 `aud` 按各节点 Host 头各自推导、跨节点验证必然失败） |
| `CANNBOT_MCP_STATE_BACKEND` | `sqlite` | 状态后端：`sqlite`（默认，零依赖单机）或 `redis`（多副本共享全部认证状态：会话、令牌台账、限流、冷却） |
| `CANNBOT_MCP_STATE_REDIS_URL` | 空 | `STATE_BACKEND=redis` 时的连接串（必填）；Redis 不可达时进程拒绝启动（fail-closed） |
| `CANNBOT_MCP_LOG` / `CANNBOT_MCP_LOG_DIR` | `auto` / `~/.local/state/cannbot-knowledge/mcp` | 调用日志开关（`on`/`off`/`auto`，auto=HTTP 开、stdio 关）与目录 |
| `CANNBOT_MCP_LOG_UPLOAD_REMOTE` | 空（不启用） | 日志自动上传远端仓；与 `LOG_UPLOAD_INTERVAL` 一起启用，须显式配置 |
| `CANNBOT_MCP_LOG_UPLOAD_INTERVAL` | `0`（关闭） | 自动上传间隔（秒）；仅 HTTP 且日志开启时生效，`0` 不启动上传线程 |
| `CANNBOT_MCP_LOG_UPLOAD_BRANCH` | `main` | 自动上传目标分支 |
| `CANNBOT_MCP_ENGINE` | `in_process` | 检索引擎适配器：`in_process`（默认，进程内常驻引擎，按调用校验索引指纹、毫秒级返回）或 `subprocess`（子进程 CLI 透传，进程级隔离/对照诊断用） |
| `CANNBOT_MCP_ENGINE_QUEUE` | `64` | in-process 模式下引擎单 worker 的等待队列深度：1 个在执行 + N 个排队，超出立即以结构化 `engine_overload` 拒绝 |
| `CANNBOT_MCP_ENGINE_TIMEOUT` | `30` | in-process 模式下单次调用的执行期限（秒）：超时立即以结构化 `engine_timeout` 释放调用方，且下一次调用自动换新 worker（挂死线程被废弃，服务不重启自恢复） |
| `CANNBOT_MCP_MAX_SUBPROCS` | CPU 核数 | subprocess 模式下 search/discover 子进程并发信号量上限，超出排队；in-process 模式不适用 |
| `CANNBOT_MCP_SUBPROC_TIMEOUT` | `30` | subprocess 模式下子进程硬超时（秒），挂死的 CLI 被杀并返回结构化 tool error；in-process 模式不适用 |
| `CANNBOT_MCP_HEADERS_ROOT` | 空 | 仅 stdio 模式：read_card `local_only.headers_root` 报告的本地 CANN Ascend C 组件根 |

日志目录若配置在知识仓内，日志功能拒绝启用（绝不写仓内任何路径）。

## 调用日志与离线分析

HTTP 模式默认开启调用日志（stdio 默认关闭，`CANNBOT_MCP_LOG=on` 可开），写在仓外目录（默认 `~/.local/state/cannbot-knowledge/mcp`，可用 `CANNBOT_MCP_LOG_DIR` 修改），按天分文件（`calls-YYYY-MM-DD.jsonl`）。每次工具调用记一行：时间、调用者身份（principal）、工具名、参数、成功与否、耗时、命中数；认证失败与限流另记事件行。

**隐私与留存**：日志含调用者身份与查询内容明文，属敏感数据——目录权限应设为仅维护者可读（如 `chmod 700`）。建议至少保留 90 天用于趋势分析，不配置自动删除。

离线分析（标准库实现，系统 Python 直接运行）：

```bash
python3 mcp-server/analyze_logs.py --days 30 [--log-dir /path/a,/path/b] [--top 20] [--output report.json]
```

产出 JSON 报告与人读 Markdown 摘要，覆盖：零命中查询、查询词热度、卡片阅读热度、平台需求分布、阅读深度、失败分类、周趋势，以及多实例间的结果漂移告警。完整字段定义见 `analyze_logs.py` 文档字符串。

### 日志自动上传（多实例汇聚）

多实例部署时各机器日志分散，可配置自动上传：设置远端仓地址与非 0 上传间隔后，服务器按周期把日志推送到该仓，全部实例汇入同一处，维护者分析前 `git pull` 即可拿到全局数据。默认关闭。

| 变量 | 默认 | 说明 |
|---|---|---|
| `CANNBOT_MCP_LOG_UPLOAD_REMOTE` | 空（不启用） | 上传目标仓，须显式配置 |
| `CANNBOT_MCP_LOG_UPLOAD_INTERVAL` | `0`（关闭） | 上传间隔（秒），非 0 启用 |
| `CANNBOT_MCP_LOG_UPLOAD_BRANCH` | `main` | 上传目标分支 |

注意事项：

- 推送凭证走部署机当前用户的 git credential helper，不进环境变量、不进服务器配置文件；
- 上传失败只记一行诊断并下轮重试，不影响正常请求；
- 上传仓应设为私有仓：日志含调用者身份与查询内容明文，读权限与日志目录同级对待。

## 多实例部署

```text
机器 A：git clone + knowledge_index.py build + mcp-server   ← 完全独立
机器 B：git clone + knowledge_index.py build + mcp-server   ← 完全独立
机器 C：git clone + knowledge_index.py build + mcp-server   ← 完全独立
```

- **零协调成立的理由**：服务 stateless（任意副本处理任意请求）；数据是纯 git 仓（clone + 建索引即完整分发）；SQLite 只读连接多进程/多机安全。实例间 commit 可短暂不一致——无害，每次响应自带索引 provenance。
- **日志分散**：各实例各写本地日志，用 `analyze_logs.py --log-dir a,b,c` 多目录合并分析；或开启"日志自动上传"让各实例自动汇聚到同一仓（见上节），维护者分析前先 `git pull`。
- **限流与封禁的粒度**：默认 sqlite 后端下，限流与 IP 冷却按每台实例独立计数；配置 `STATE_BACKEND=redis` 后跨实例全局共享——limit=N 在 N 台实例上是全局 N。子进程并发闸始终按每台独立；默认 in-process 引擎状态随各进程生灭，各 worker 各持独立引擎。
- **多副本共享认证状态**：`CANNBOT_MCP_STATE_BACKEND=redis` + `CANNBOT_MCP_STATE_REDIS_URL` 使多节点共享**全部认证状态**（设备码/授权码会话、令牌台账、限流、IP 冷却）。三个必备项：①所有节点同一 `CANNBOT_MCP_AUTH_SECRET`（JWT 验签一致）；②所有节点同一 `CANNBOT_MCP_PUBLIC_URL`（受众绑定一致）；③Redis 对所有节点可达且不可达时进程拒绝启动（fail-closed，不静默退化）。选 redis 后端需先 `pip install redis>=5`（默认部署无此依赖）。
- **更新窗口约定**：维护者显式 `git pull` 后立即连续执行索引重建（`knowledge_index.py build`），再对外提供服务；pull 与重建之间服务保持 fail-closed 拒答（实测重建约 65s，该窗口内查询返回带修复指引的 tool error，不会读到新旧混合数据）。服务器自身绝不自动更新或重建。
- **负载均衡建议（可选）**：Streamable HTTP stateless 下无需会话粘滞；按真实客户端 IP 的封禁/限流需在反代层配置（服务端只看直连地址，默认不信任 `X-Forwarded-For`）。

## 依赖隔离

服务器依赖（官方 `mcp` SDK、uvicorn、PyYAML）只声明在本目录 `pyproject.toml`，由 `uv` 在本目录内解析安装；仓库根 `requirements.txt` 保持仅 PyYAML 不变。不使用 MCP 服务器的用户路径零变化。`analyze_logs.py` 仅用标准库，可直接用系统 Python 运行。

## 测试

```bash
# 端到端（进 check.sh 门禁；需要 mcp-server/.venv 或 uv）
python3 -m unittest discover -s evals -p 'test_mcp_server.py' -v

# 单元测试（需在本目录 venv 内运行）
uv --directory mcp-server run python -m unittest discover -s tests -v
```
