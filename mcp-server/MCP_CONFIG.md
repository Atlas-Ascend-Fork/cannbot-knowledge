# MCP 客户端接入配置

本文只收录各客户端接入 cannbot-knowledge MCP 服务器的配置样例；服务器自身的启动方式、环境变量与部署边界见 [README.md](README.md)。工具参数与典型调用流程见 [TOOLS.md](TOOLS.md)，接入故障排查见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。最省事的接入方式是项目安装器：`bash install.sh <agent> <project> --with-mcp` 会直接写入 Claude Code 项目级 `.mcp.json` 并打印下述等价片段。

以下样例中 `<knowledge-repo>` 指本地 cannbot-knowledge 检出根目录的绝对路径。

## Claude Code（stdio，本地）

项目级 `.mcp.json`（安装器 `--with-mcp` 写入的就是这份）：

```json
{
  "mcpServers": {
    "cannbot-knowledge": {
      "command": "uv",
      "args": ["--directory", "<knowledge-repo>/mcp-server", "run", "server.py"],
      "env": {"CANNBOT_KNOWLEDGE_ROOT": "<knowledge-repo>"}
    }
  }
}
```

可选：`env` 块增加 `"CANNBOT_KNOWLEDGE_PLATFORM": "<platform-id>"`（安装器 `--platform` 配置了平台时自动写入该键）。`uv --directory` 启动时 cwd 是 `mcp-server`，CLI 向上找不到项目 `.cannbot/knowledge.env`，平台须靠该键显式传入。

等价命令行：`claude mcp add cannbot-knowledge -- uv --directory <knowledge-repo>/mcp-server run server.py`。

## Claude Desktop（stdio，本地）

编辑 `claude_desktop_config.json`（macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`；Windows: `%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "cannbot-knowledge": {
      "command": "uv",
      "args": ["--directory", "<knowledge-repo>/mcp-server", "run", "server.py"],
      "env": {"CANNBOT_KNOWLEDGE_ROOT": "<knowledge-repo>"}
    }
  }
}
```

可选：`env` 块增加 `"CANNBOT_KNOWLEDGE_PLATFORM": "<platform-id>"`（安装器 `--platform` 配置时自动写入）。

## Cursor（stdio，本地）

项目级 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "cannbot-knowledge": {
      "command": "uv",
      "args": ["--directory", "<knowledge-repo>/mcp-server", "run", "server.py"],
      "env": {"CANNBOT_KNOWLEDGE_ROOT": "<knowledge-repo>"}
    }
  }
}
```

可选：`env` 块增加 `"CANNBOT_KNOWLEDGE_PLATFORM": "<platform-id>"`（安装器 `--platform` 配置时自动写入）。

## OpenCode（stdio，本地）

`~/.config/opencode/opencode.jsonc`（或项目级 `opencode.json`）。注意 OpenCode 默认 MCP 启动超时仅 5 秒，首次 `uv` 解析依赖会超时——显式设 `"timeout": 120000`，或先在 `mcp-server/` 手动 `uv sync` 预热：

```jsonc
{
  "mcp": {
    "cannbot-knowledge": {
      "type": "local",
      "command": ["uv", "--directory", "<knowledge-repo>/mcp-server", "run", "server.py"],
      "enabled": true,
      "timeout": 120000,
      "environment": {
        "CANNBOT_KNOWLEDGE_ROOT": "<knowledge-repo>"
        // 可选：安装器 --platform 配置时自动写入 "CANNBOT_KNOWLEDGE_PLATFORM": "<platform-id>"
      }
    }
  }
}
```

OpenCode 不热加载配置，修改后须从新终端重启。

## Trae（stdio，本地）

Trae 的 MCP 设置界面（设置 → MCP → 添加手动服务器）或项目级配置，命令同上：`uv --directory <knowledge-repo>/mcp-server run server.py`，环境变量 `CANNBOT_KNOWLEDGE_ROOT=<knowledge-repo>`（可选 `CANNBOT_KNOWLEDGE_PLATFORM=<platform-id>`，安装器 `--platform` 配置时自动写入）。Trae 同样建议把启动超时调到 60 秒以上。

## 无 uv 环境的启动方式（pip / venv）

宿主机没有 uv 时，用虚拟环境安装依赖后直接启动（依赖见 `mcp-server/pyproject.toml`）：

```bash
cd <knowledge-repo>/mcp-server
python3 -m venv .venv-mcp
. .venv-mcp/bin/activate
python3 -m pip install -e .
python server.py          # stdio；HTTP 加 --transport http
```

客户端配置把 `command` 换成 `<knowledge-repo>/mcp-server/.venv-mcp/bin/python`、`args` 换成 `["<knowledge-repo>/mcp-server/server.py"]`，env 块不变（可选的 `CANNBOT_KNOWLEDGE_PLATFORM` 同上；此方式 cwd 即 `mcp-server`，同样需显式传平台）。

## 通用 HTTP 远程接入（团队共享端点）

服务端启动见 [README.md](README.md#streamable-http团队共享)。端点为 `http://<host>:8090/mcp`，四轨认证：人类用户走 GitCode OAuth（下方 A），机器身份（CI、脚本、批量 Agent）优先用自服务 API Key（下方 B），静态令牌与 GitCode PAT 为备选通道（下方 C/D）；所有凭证都支持 `Authorization: Bearer <token>` 或 `X-MCP-Auth-Token: <token>` 头。

### A. GitCode OAuth（人类用户推荐）

支持 OAuth 的客户端（Claude Code 等）连接 `http://<host>:8090/mcp` 时会自动发现服务端声明的授权方式（RFC 9728/8414 元数据由本服务发布，OAuth 端点指向 GitCode）并触发浏览器授权——用本人的 GitCode 账号登录并同意即可，无需向任何人领令牌。授权后客户端自动持证访问；GitCode 侧撤销授权即失去访问。

**前置条件（一次性，管理员操作）**：在 GitCode 注册一个 OAuth 应用（`https://gitcode.com/setting/oauth/create`，回调地址填客户端本机回环，如 `http://127.0.0.1:19876/mcp/oauth/callback`；应用注册详情见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)），然后把应用凭证配到服务器环境变量：

```bash
export CANNBOT_MCP_OAUTH_CLIENT_ID="<client_id>"
export CANNBOT_MCP_OAUTH_CLIENT_SECRET="<client_secret>"
```

配置后**使用者零配置**：本服务默认以自建授权服务器模式运行，`/register` 按 RFC 7591 发放**本服务公共客户端**注册（PKCE、无 secret），客户端自动进入设备码/授权码浏览器授权——使用者全程不需要知道 client_id 的存在。应用凭证（`client_id`/`client_secret`）只在服务端使用：作为授权页 GitCode 登录腿的身份源，**绝不发给任何客户端**。未配置这两个变量时授权页退回手填用户名方式（仅限可信网络内的引导部署，见下方 B/手工方式）。

> 安全提示：应用 secret 是服务端机密。任何曾被 `/register` 代理发放过凭证的存量部署（旧版转发模式行为），升级后请在 GitCode 撤销并重新创建该 OAuth 应用、轮换 `CANNBOT_MCP_OAUTH_CLIENT_SECRET`。

回调地址说明：授权码流程的回调由各 MCP 客户端自动处理（客户端在本机监听 `localhost` 回调端口，与服务器地址无关），使用者通常无需配置任何回调；若所用客户端要求手工填写回调 URI，填其文档给出的本机回环地址（如 `http://localhost:PORT/callback`）即可，**不要**填服务器地址。

```bash
claude mcp add --transport http cannbot-knowledge http://<host>:8090/mcp
```

cannbot/OpenCode（`~/.config/opencode/opencode.jsonc`；正常情况下零配置即可——自建授权服务器模式下无需 client_id，以下 `oauth.clientId` 仅旧版兼容时可能用到）：

```jsonc
{
  "mcp": {
    "cannbot-knowledge": {
      "type": "remote",
      "url": "http://<host>:8090/mcp",
      "oauth": {"clientId": "<GitCode OAuth 应用的 client_id>"}
    }
  }
}
```

### B. 自服务 API Key（机器身份推荐）

CI、定时脚本、批量 Agent 等无人值守机器的推荐方式——不需要管理员发令牌，机器的主人自己生成：

1. 你本人先走一次 A 的浏览器授权（或用下方"自签 JWT 生成"提示里的设备码流程）拿到 access JWT；
2. 生成一把带用途标签的机器令牌：

```bash
curl -X POST http://<host>:8090/api/keys \
  -H "Authorization: Bearer <access JWT>" \
  -d "label=my-ci-runner"
# 响应 {"key": "cbk_live_...", "key_id": "..."} —— 完整 key 仅此一次返回，立即保存
```

3. 把 key 配进机器（与 C 静态令牌的用法完全相同，把 token 换成 `cbk_live_...`）。

管理：`GET /api/keys`（带 JWT）列表、`DELETE /api/keys?key_id=...` 撤销立即生效；每用户最多 10 把。相比把 GitCode PAT 直接塞给 CI：这把 key 只能访问知识库这一个服务，泄露不波及你的 GitCode 仓库，且调用日志 principal 记为 `你的用户名/机器标签`，能定位到具体哪台机器。

### C. 静态令牌（引导/应急备选）

服务器 `CANNBOT_MCP_TOKENS` 环境变量里预配置的令牌，适合首次部署引导（还没人走过 OAuth）或 GitCode 不可达的应急场景。用法：

```bash
claude mcp add --transport http cannbot-knowledge http://<host>:8090/mcp --header "Authorization: Bearer <token>"
```

Claude Desktop / Cursor（HTTP 形态）：

```json
{
  "mcpServers": {
    "cannbot-knowledge": {
      "url": "http://<host>:8090/mcp",
      "headers": {"Authorization": "Bearer <token>"}
    }
  }
}
```

任意支持 Streamable HTTP 的客户端：对 `http://<host>:8090/mcp` 发送 JSON-RPC POST（`Accept: application/json, text/event-stream`），每个请求自带 `Authorization: Bearer <token>` 头。服务以 stateless 模式运行，无需会话粘滞。

没有浏览器时也可以拿 access JWT：`curl -X POST http://<host>:8090/oauth/device/code` 取设备码，浏览器打开 `verification_uri_complete` 链接完成 GitCode 登录与允许，再轮询 `POST /oauth/device/token`（`grant_type=urn:ietf:params:oauth:grant-type:device_code`）换取令牌对。

### D. GitCode 个人访问令牌（备选）

服务器同样接受 GitCode 个人访问令牌（PAT）作为 Bearer 凭证——验证走 GitCode 用户接口，principal 记为 GitCode 用户名。适合不想等 OAuth 应用注册的个人使用者：

```jsonc
{
  "mcp": {
    "cannbot-knowledge": {
      "type": "remote",
      "url": "http://<host>:8090/mcp",
      "headers": {"Authorization": "Bearer <GitCode PAT>"}
    }
  }
}
```

与静态令牌的区别：PAT 由 GitCode 发放与撤销（在 GitCode 设置页管理），principal 是 GitCode 用户名而非机器用途名；与 OAuth 的区别：PAT 需要使用者自行在 GitCode 生成并粘贴进配置，OAuth（A）注册应用后只需浏览器点一下授权。

## 接入后自检

接入后第一次调用建议用 `discover`（无参数）：返回成功即证明端点、认证与索引全部正常；随后按 `discover → search → read_card` 的节奏使用，完整示例见 [TOOLS.md](TOOLS.md#典型流程查-950-平台-datacopy-的对齐要求)。调用失败时按 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 分层定位。
