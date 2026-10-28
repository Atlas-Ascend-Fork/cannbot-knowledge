---
name: knowledge-lint
description: 确定性校验 cannbot-knowledge 的路径、Profile、标签、平台、来源、时间、正文、导航和日志，并把知识内容、检索、图谱、编译或治理失败整理成可复现 Issue 材料。创建、导入或修改知识与基础 Skill 后、提交前门禁或用户要反馈知识库问题时使用；仅当用户明确要求内容审阅并指定页面时委派独立 reviewer。只读报告，不自动修复或提交。
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

检查项、等级、模式和错误边界见 [checks](references/checks.md)。退出码 `0` 表示完整执行且没有 P0，`1` 表示至少存在一个 P0，`2` 表示命令、规则或仓库不可用；P1/P2 完整报告但不阻断。

正文、链接、图片和平台检查共用 Contract 的代码围栏解析；文档归档识别也由 Contract 统一提供，避免各检查器对同一段正文采用不同边界。仅文档归档主来源的 API/Guide 镜像可保留多个 H1；辅助来源引用、普通卡片和无 H1 正文不获得例外。

生命周期检查复用 Contract 的路径推导，确认 `replaced_by` 指向 Bundle 内的真实 Concept；现有索引页不能充当替代卡，路径别名和符号链接越界也不能绕过检查。

### 工作流

日常修改只运行与变更相关的局部检查；完整检查流程集中在提交或推送上库前执行，除非用户明确要求提前全量验证。

1. 改动卡先用 `--card` 检查 Profile、tag、source、平台、正文和时间；有代码来源的新卡或实质更新卡同时使用 `--strict-navigation`。
2. 全库运行以检查 domain 根、`ops`/`model` route 骨架、逐层导航、Bundle 内链接和日志；统一 `check.sh` 会启用严格来源导航。`--sample` 只做确定性抽样，不代替全库门禁。
3. 确认知识仓维护者已按 [Query 索引维护](../knowledge-query/references/cli.md#索引)准备与改动后语料一致的索引，再执行目标 query，确认新卡可召回、draft 不进入默认结果。Lint 本身只报告，不修改或重建索引。
4. 修改 Skill 时运行 skill-creator 的 quick validation、相关回归和本仓统一质量门禁。
5. 用户要提交或整理问题时，按 [Issue 报告](references/issue-report.md)收集已有运行材料与实际复现率；补充复现仍受当前任务授权和本 Skill 只读边界约束。关键材料缺失则输出 `needs-info`，不凭记忆补齐或虚增运行次数。

可选 `scope` 由同版本 Contract 校验；允许的 Profile、namespace、路径绑定和维度配置分别以治理事实源为准。缺字段或缺少部分维度不报质量错误；非法声明仍拒绝。具体边界见 [Frontmatter](../../../governance/specs/frontmatter.md#场景适用条件scope)。

## 页面内容检查

仅当用户明确要求内容或语义检查并指定页面时使用；普通 Lint 和 Issue 工作流仍只执行确定性检查。

1. 完整读取 [Content 检查协议](references/content_check.md)、[Content 策略](references/content_check.toml) 和 [Content prompt](references/content_check_prompt.md)，不复制其中的检查项。
2. 为每个指定页面启动一个独立、只读 reviewer，工作目录设为仓库根；一个 reviewer 只检查一页并完成全部启用项，不得继续派生 reviewer，也不修改、执行、提交或发布文件。
3. reviewer 只返回 prompt 规定的页面 JSON。未完成或协议不合法时标记该页未完成，不当作空结果；汇总时把页面级未完成与仓库级运行故障分开。
4. 最终向用户返回下列 Markdown；Finding 按 P0、P1、P2、页面路径和行号排序。没有 Finding、未完成页面或运行错误时，省略相应区块。

```markdown
## ContentCheck · <✅ 通过 | ❌ 未通过 | ⚠️ 检查未完成>

- 已检查：`N` 页；未完成：`N` 页
- Findings：`N`（P0 `N` · P1 `N` · P2 `N`）

| 等级 | 检查 | 文件 | 说明 |
|---|---|---|---|
| P1 | `check_id` | `knowledge/example.md:17` | 面向作者的问题说明和修改方向 |

### 未完成页面

| 页面 | 原因 |
|---|---|
| `knowledge/example.md` | 未返回有效检查结果 |

### 运行错误

- <仓库级运行故障；没有则省略>
```

任一页面未完成或存在仓库级运行故障时为 `⚠️ 检查未完成`；否则存在 P0 时为 `❌ 未通过`，其余情况为 `✅ 通过`。P1/P2 完整报告但不改变通过状态。只有用户明确要求机器可读结果时，才在 Markdown 后附加汇总 JSON。

## 边界

Lint 不联网验证 URL，不证明来源充分支持结论，也不判断技术语义、实验复现、shared 泛化或跨 DSL 等价性。全库模式要求 Registry 的本地来源获取脚本存在且可执行；来源根不存在时允许离线检查，根已恢复时才核对归档完成标记的来源 URL 和在用文件（不校验 SHA-256）；Git 本地根还验证固定提交、远程来源、干净工作区及被引用文件，Lint 不自动获取、清理或修复源码。知识卡可链接登记的固定提交源码文件，索引仍限于 Bundle；源码链接不形成 Concept。Lint 只执行本 Skill 所属仓的 Contract，并在目标根 Contract 版本不一致时失败，不执行目标根提供的 Python。Issue 工作流只整理事实与复现材料，不直接裁决知识正确性。
