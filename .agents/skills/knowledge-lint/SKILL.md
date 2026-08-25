---
name: knowledge-lint
description: 确定性校验 cannbot-knowledge 的路径、Profile、标签、平台、来源、时间、正文、导航和日志，并把知识内容、检索、图谱、编译或治理失败整理成可复现 Issue 材料。创建、导入或修改知识与基础 Skill 后、提交前门禁或用户要反馈知识库问题时使用；只读报告，不自动修复或提交。
---

# Knowledge Lint

对知识仓运行零 LLM、离线、只读、可重复的治理检查。Issue 整理属于本 Skill 的报告工作流，不增加第四个公开 Skill。

## 运行

```bash
python3 <skill-dir>/scripts/knowledge_lint.py --knowledge-root <repo>
python3 <skill-dir>/scripts/knowledge_lint.py --knowledge-root <repo> --json
python3 <skill-dir>/scripts/knowledge_lint.py --knowledge-root <repo> \
  --card knowledge/ops/ascendc/apis/example.md --strict-navigation
python3 <skill-dir>/scripts/knowledge_lint.py --knowledge-root <repo> --sample 10 --json
```

检查项、模式和错误边界见 [checks](references/checks.md)。退出码 `0` 表示无错误，`1` 表示存在治理错误，`2` 表示命令或仓库不可用。

## 工作流

1. 改动卡先用 `--card` 检查 Profile、tag、source、平台、正文和时间；有代码来源的新卡或实质更新卡同时使用 `--strict-navigation`。
2. 全库运行以检查 domain 根、`ops`/`model` route 骨架、逐层导航、Bundle 内链接和日志；统一 `check.sh` 会启用严格来源导航。`--sample` 只做确定性抽样，不代替全库门禁。
3. 执行目标 query，确认新卡可召回、draft 不进入默认结果。
4. 修改 Skill 时运行 skill-creator 的 quick validation、相关回归和本仓统一质量门禁。
5. 用户要提交或整理问题时，按 [Issue 报告](references/issue-report.md)收集原始材料；关键材料缺失则输出 `needs-info`，不凭记忆补齐。

## 边界

Lint 不联网验证 URL，不证明来源充分支持结论，也不判断技术语义、实验复现、shared 泛化或跨 DSL 等价性。全库模式要求 Registry 的本地来源获取脚本存在且可执行；来源根不存在时允许离线检查，根已恢复时才核对归档完成标记和在用文件。Lint 只执行本 Skill 所属仓的 Contract，并在目标根 Contract 版本不一致时失败，不执行目标根提供的 Python。Issue 工作流只整理事实与复现材料，不直接裁决知识正确性。
