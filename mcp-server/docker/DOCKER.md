# Docker 一键部署

本目录提供 cannbot-knowledge MCP 服务器的 Docker 化部署：克隆本仓后生成令牌文件、`docker compose up -d --build`，两条命令即可对外提供团队共享的 HTTP 检索服务。服务器代码零修改——所有行为由环境变量驱动（完整清单见 [README.md](../README.md)），部署形态只增加容器层的初始化与持久化约定。

## 适用场景

- 给一个团队（建议 50 人以内）提供共享 MCP HTTP 端点，一人一令牌、按令牌限流与审计
- 被部署机不想安装 Python/uv 环境：检索索引在容器内自动构建与更新，宿主机只需要 Docker
- 本地单人 stdio 接入不经过容器，仍按 [README.md](../README.md) 启动；本文件只覆盖 HTTP 团队共享形态

服务器本体说明（工具面、环境变量、日志格式、多实例边界）见 [README.md](../README.md)；客户端接入配置样例见 [MCP_CONFIG.md](../MCP_CONFIG.md)。

## 前置条件

- Docker Engine 与 Compose v2（`docker compose version` 可用）
- 本仓的一份检出（`git clone` 或已有副本），无需宿主 Python
- 宿主机 8090 端口空闲（被占用时见 FAQ）
- 运行 docker 的用户具备 daemon 访问权限（多数发行版需 `sudo usermod -aG docker <user>` 后重新登录）

## 三步部署

在本目录（`mcp-server/docker/`）内执行：

### 1. 生成令牌文件 tokens.env

HTTP 模式必填，格式与 [README.md](../README.md) 的 Streamable HTTP 一节一致（`token:label` 逗号分隔）：

```bash
# 单人（无需宿主 Python）
printf 'CANNBOT_MCP_TOKENS=cbk_%s:user1\n' "$(openssl rand -hex 32)" > tokens.env

# 或 50 人
for i in $(seq 1 50); do printf 'cbk_%s:user%02d\n' "$(openssl rand -hex 32)" "$i"; done \
  | paste -sd, | sed 's/^/CANNBOT_MCP_TOKENS=/' >> tokens.env
```

`tokens.env` 已被仓库 `.gitignore` 忽略，令牌绝不入库。文件里还可以追加其他 `CANNBOT_*` 变量（如 `CANNBOT_MCP_RATE_LIMIT`），`env_file` 会整体注入容器。

### 2. 启动

```bash
docker compose up -d --build
```

首次启动包含构建镜像与容器内构建检索索引（约 1~3 分钟），进度用 `docker compose logs -f cannbot-mcp` 观察，出现 `starting cannbot-knowledge mcp server` 即就绪。

### 3. 验证

```bash
curl -s -X POST http://127.0.0.1:8090/mcp \
  -H "Authorization: Bearer cbk_<你的令牌>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"discover","arguments":{}}}'
```

返回各维度真实覆盖计数即部署成功；令牌错误返回 401。随后按 [MCP_CONFIG.md](../MCP_CONFIG.md) 的通用 HTTP 远程接入一节，把团队客户端指向 `http://<host>:8090/mcp`，每人使用自己的令牌。

## 架构

```text
宿主机                                    容器 cannbot-mcp
──────────────────────────────────       ─────────────────────────────────────
cannbot-knowledge 检出 ──(bind, :ro)──►  /data/repo        知识卡+治理+脚本，只读
Docker 卷 cannbot-mcp-index ──────────►  /data/repo/artifacts   检索索引（容器内构建）
Docker 卷 cannbot-mcp-logs  ──────────►  /data/logs        JSONL 调用日志
宿主机 8090 ◄───────────────────────────  0.0.0.0:8090      MCP HTTP 端点
```

- **知识仓只读**：`/data/repo` 以 `:ro` 挂载，容器内任何进程写入（`artifacts` 卷除外）都会得到 `Read-only file system`。这把服务器"对知识仓严格只读"的代码约束在系统层面再锁一次。
- **docker-entrypoint.sh**（每次容器启动执行）：校验 `knowledge/` 非空（防止挂错目录后静默服务空库）→ 索引缺失或与知识卡不一致（宿主机 `git pull` 过）时在容器内重建，重建与查询均只使用镜像内置依赖（PyYAML、git——git 用于记录索引与查询的 commit provenance）→ 修正日志与索引卷属主 → 以 `setpriv` 降权到 uid 1000 启动服务器。任何一步失败容器即退出，由重启策略退避重试——服务保持 fail-closed，绝不用过期索引对外作答。
- **init: true**：容器内微型 init 进程收割僵尸进程；`search`/`discover` 每次调用经 subprocess fork 子进程，长期运行需要兜底。
- **restart: unless-stopped**：Docker daemon 重启、宿主机重启、进程崩溃都自动拉起；只有手动 `docker stop` 过才不拉。

## 配置

| 配置 | 默认 | 说明 |
|---|---|---|
| `KNOWLEDGE_ROOT` | `../..`（compose 所在目录的上两级，即仓库根） | 知识仓位置。默认值让"克隆即用"零配置；仓不在该相对位置时，在 `mcp-server/docker/.env` 写 `KNOWLEDGE_ROOT=/path/to/repo`（该文件被 gitignore） |
| `PIP_INDEX_URL` | `https://pypi.org/simple` | 构建镜像时的 pip 源。网络到官方源慢时，在 `mcp-server/docker/.env` 写 `PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`（或所在网络可达的内网镜像）后重新 `up -d --build` |
| 端口映射 | `8090:8090` | 宿主机端口冲突时改 `compose.yaml` 的 `ports` 左值，客户端地址同步调整 |
| 令牌与服务器行为 | — | `CANNBOT_MCP_TOKENS`、限流、子进程闸等全部环境变量见 [README.md](../README.md)，可写进 `tokens.env` 一并注入 |
| `CANNBOT_MCP_SUBPROC_TIMEOUT` | 镜像内固化为 `60` | 服务器默认 30 秒在慢查询下可能被打满，镜像默认放宽到 60；可在 `tokens.env` 覆盖 |

## 日常运维

### 知识库更新（git pull → restart）

```bash
cd <仓库根> && git pull
docker restart cannbot-mcp
```

重启时 entrypoint 检测到卡片变化（卡集合、size/mtime、治理指纹）自动重建索引（约 1~3 分钟），期间服务短暂不可用——与 [README.md](../README.md) 的更新窗口约定等价：宁可短暂停机，也不读新旧混合数据。知识无变化的普通重启只做校验，秒级完成。

### 令牌增删

编辑 `tokens.env` 后 `docker compose up -d`：compose 对比差异自动重建容器，索引与日志两个卷原样保留。

### 日志

```bash
docker exec cannbot-mcp ls /data/logs                  # calls-YYYY-MM-DD.jsonl 按天累积
docker volume inspect cannbot-mcp-logs                 # 卷在宿主机的真实路径
docker logs cannbot-mcp                                # 服务器自身 stderr
```

离线聚合分析（在仓库根执行；宿主机 Python 3 即可，仅标准库；卷目录为 root 属主，需要 sudo）：

```bash
sudo python3 mcp-server/analyze_logs.py --days 30 \
  --log-dir "$(sudo docker volume inspect -f '{{.Mountpoint}}' cannbot-mcp-logs)"
```

### 命令速查

| 命令 | 作用 |
|---|---|
| `docker compose up -d --build` | 构建镜像并启动 |
| `docker compose ps` | 查看状态 |
| `docker compose logs -f cannbot-mcp` | 跟踪启动/构建日志 |
| `docker compose up -d` | 改了 `tokens.env`/`.env` 后重新应用 |
| `docker restart cannbot-mcp` | 知识更新后的索引重建入口 |
| `docker compose down` | 停止并删容器（**卷保留**） |
| `docker compose down -v` | 连卷一起删（清空索引与日志，慎用） |

## 数据持久化语义

| 操作 | 知识仓（宿主机） | 索引卷 | 日志卷 |
|---|---|---|---|
| `docker restart` / daemon 重启 / 宿主机重启 | 不受影响 | 保留 | 保留 |
| `docker compose down` → `up` | 不受影响 | 保留 | 保留 |
| `docker rm -f` 后重建容器 | 不受影响 | 保留 | 保留 |
| `docker compose down -v` | 不受影响 | **删除** | **删除** |

索引是可重建产物：`down -v` 后下次启动自动重建，只损失首次启动时间。

## 迁移到另一台机器

默认 `KNOWLEDGE_ROOT=../..` 不含绝对路径，compose 文件在任意机器无需改动：

| 步骤 | 说明 |
|---|---|
| 1 | 新机安装 Docker 与 Compose v2 |
| 2 | `git clone` 本仓（推荐），或拷贝 `mcp-server/docker/` 目录（Dockerfile、compose.yaml、docker-entrypoint.sh、.dockerignore 全在其中） |
| 3 | 知识仓就位：克隆后由首次启动自动建索引；或连同 `artifacts/` 一起 rsync，跳过首次构建 |
| 4 | 生成 `tokens.env`（见三步部署） |
| 5 | `docker compose up -d --build` |
| 6 |（可选）搬旧日志：rsync 旧机 `docker volume inspect -f '{{.Mountpoint}}' cannbot-mcp-logs` 指向的目录到新机同位置 |
| 7 | curl 验证 discover，团队客户端改指新机地址（建议提前上内网域名，免逐个改配置） |

卷名显式固定为 `cannbot-mcp-index` 与 `cannbot-mcp-logs`，不受 compose 项目名（目录名）影响，换目录不会产生新空卷。

## 容量与并发

实测参考（4C/3.6G 机器、7205 张卡）：

- **索引卷**：常态约 0.4 GB；重建期间新旧副本并存，峰值约 0.8 GB
- **日志卷**：实测约 0.6 KB/次调用；50 人 × 500 次/天 ≈ 15 MB/天、一年约 5.5 GB。服务器按天写 `calls-*.jsonl` 且无自动轮转，长期运行可按保留策略定期归档
- **并发**：`CANNBOT_MCP_MAX_SUBPROCS` 默认等于 CPU 核数（`search`/`discover` 子进程闸），`search` 实测 1.7~6.3 秒/次。50 人共用一台 4C 机器在高峰会排队，建议 ≥8C/16G，或多机部署——服务 stateless，多机边界与合并分析见 [README.md](../README.md)
- **令牌规模**：清单制令牌在约 50 人量级以上应迁移 OAuth2（README 已声明该边界）

## 故障排查

| 现象 | 原因与处理 |
|---|---|
| `up` 报 `env file ... not found` | 先按三步部署生成 `tokens.env` |
| 镜像构建阶段极慢或超时 | 官方 PyPI 不可达/过慢。在 `mcp-server/docker/.env` 配置 `PIP_INDEX_URL` 为可达镜像源（见配置表）后重新 `docker compose up -d --build` |
| 容器反复重启 | `docker compose logs`：多为索引构建失败（知识卡或治理文件损坏），修复仓库后重启自动恢复；fail-closed 是预期行为 |
| 启动日志 `knowledge/ is missing or empty` | `KNOWLEDGE_ROOT` 指到了错误目录，entrypoint 显式拒绝启动，避免静默服务空知识库 |
| 查询返回 stale/missing 索引类错误 | 正处于重启重建窗口，等待完成；持续出现则查 `docker compose logs` |
| 端口占用 | 改 `compose.yaml` 的 `ports` 左值为其他宿主端口 |
| `up` 报容器名 `cannbot-mcp` 冲突 | 本机曾用其他目录/项目名部署过：`docker rm cannbot-mcp`（必要时 `docker network rm <旧项目名>_default`）后重试，卷与数据不受影响 |
| `permission denied ... docker.sock` | `sudo usermod -aG docker <user>` 后重新登录 |
| 误执行 `down -v` | 索引下次启动自动重建；日志若未提前备份则丢失 |

## 安全清单

默认面向内网。对外开放前逐项核对 [README.md](../README.md) 的外网暴露前置条件清单：TLS 由反向代理终止、令牌强度与轮换、限流确认、`auth_failed` 审计留存。服务不信任 `X-Forwarded-For`——走反代时必须在反代层做真实 IP 透传与限流，否则个别客户端的认证失败会按反代 IP 触发冷却封禁、波及全体。
