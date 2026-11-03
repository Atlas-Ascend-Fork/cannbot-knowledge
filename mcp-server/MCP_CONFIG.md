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

服务端启动见 [README.md](README.md#streamable-http团队共享)。端点为 `http://<host>:8090/mcp`，认证支持 `Authorization: Bearer <token>` 或 `X-MCP-Auth-Token: <token>` 头。

Claude Code：

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

## 接入后自检

接入后第一次调用建议用 `discover`（无参数）：返回成功即证明端点、认证与索引全部正常；随后按 `discover → search → read_card` 的节奏使用，完整示例见 [TOOLS.md](TOOLS.md#典型流程查-950-平台-datacopy-的对齐要求)。调用失败时按 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 分层定位。
