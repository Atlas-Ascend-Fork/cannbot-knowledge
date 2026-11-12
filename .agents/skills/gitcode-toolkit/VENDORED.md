# Vendored 副本说明

## 来源

- 上游仓库：`cann/cannbot-skills`
- 上游提交：`2374941`（`infra/gitcode-toolkit`）
- 内置目标仓：`cann/cannbot-knowledge`，供内置的 `gitcode-issue-handler` 副本使用。

## 与上游的差异

本副本是**裁剪版**，不是上游原样拷贝：

1. 仅保留 `gitcode_client.py`（API 客户端，被 Handler 管线 import）、`post_issue_comment.py` 与其依赖 `_logging.py`、`parse_gitcode_url.py`（发布回复的唯一确定性入口，见 `references/issue-comment-workflow.md`）、`fcntl.py` Windows shim（上游无此文件）与 `preflight.sh`。
2. 已移除 `tests/`、`evals/`、`fetch_pr_context.py`、`trigger_pr_pipeline.sh`——Handler 保留管线均不引用它们。
3. 首次裁剪曾误删 `post_issue_comment.py` / `_logging.py` / `parse_gitcode_url.py`：它们由文档而非 import 关系引用，按 import 闭包裁剪会漏。发布能力依赖这三者，已补回并由契约测试守护。

## 同步上游的流程

同 `gitcode-issue-handler/VENDORED.md`：先提上游，再把 diff 落到保留集，最后更新本文件与契约测试。
