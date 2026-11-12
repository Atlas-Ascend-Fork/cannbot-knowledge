# Vendored 副本说明

## 来源

- 上游仓库：`cann/cannbot-skills`
- 上游提交：`2374941`（`infra/gitcode-issue-handler`）
- 内置目标仓：`cann/cannbot-knowledge`，供 `knowledge-issue-handler` 在仓内启动 Issue 处理，无需 cannbot-skills checkout。

## 与上游的差异

本副本是**裁剪版**，不是上游原样拷贝：

1. 仅保留 `knowledge-issue-handler` 实际使用的核心管线（`issue_pipeline.py` 及其 import / 子进程调用闭包，共 24 个脚本 + `preflight.sh`）。
2. 新增 `scripts/fcntl.py` Windows 兼容 shim（以 `msvcrt.locking` 替代 Unix `fcntl.flock`），上游不存在。
3. `references/` 保持上游原样：它是 Handler 的操作手册，本仓不逐篇裁剪，个别篇章描述的 CLI（如 operator handoff）不在本副本中，属已知偏差。

### 已移除内容（对照上游补齐时需找回）

| 移除项 | 原因 |
|---|---|
| `tests/`、`evals/` | 上游测试资产，含上游仓布局契约（硬编码 `.agents/infra/` 路径），本仓不运行 |
| `knowledge/` | Handler 自带的内嵌知识库，与知识仓职责重复 |
| `knowledge_query.py`、`refresh_issue_knowledge.py` | 上游预检查询器与历史证据刷新器，依赖已移除的 `knowledge/`；仓内预检由本仓 `knowledge-query` Skill 承担（`references/runtime-knowledge.md` 的裁剪副本注意记录了替换口径），三个引用该脚本的文档段落已同步改写 |
| `docs/`、`README.md` | 上游安装指南（指向 npx install-helper），本副本不走该安装路径 |
| `assign_issue.py`、`associate_issue_pr.py`、`auto_close_stale_issues.py`、`operator_owner_config.py` 等 16 个脚本 | 无人值守运营 / 指派 / worktree / 知识沉淀等独立运营模式工具，`knowledge-issue-handler` 明确不做这些 |
| `preflight.sh` 之外的 bash 运营脚本 | Windows 不可用且无调用方 |

## 运行时目录说明

控制器把状态、缓存、证据和报告写在目标仓的 `.cannbot/gitcode-issue-handler/`。`.cannbot/` 是 `cann/cannbot-knowledge` **既有的运行时根**（`install.sh` 写入的 `.cannbot/knowledge.env`、用户级知识根 `~/.cannbot/cannbot-knowledge` 同属该命名空间），Issue 处理在其下新增子目录属于复用既有约定，不是独立品牌目录；该路径已在 `.gitignore` 忽略。保留上游命名可避免每次同步都产生路径分歧。

## 同步上游的流程

1. 修复与新能力先提交 `cann/cannbot-skills` 上游。
2. 对比上游 diff，将变更**只**落到保留集内对应文件。
3. 更新本文件与 `evals/test_knowledge_issue_handler.py` 的 `VendoredDependencyContractTests`。
