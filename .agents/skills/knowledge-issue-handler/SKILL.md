---
name: knowledge-issue-handler
description: 处理 cannbot-knowledge 的单个或批量 GitCode Issue。复用 gitcode-issue-handler 的队列、分诊、授权、评论和回查能力，补充知识问题、知识需求、工具缺陷、治理建议与角色任命申请（Committer 提名）的仓库内路由；默认只分析和拟稿，不自动回复、指派、修改知识或关闭 Issue。
---

# Knowledge Issue Handler

本 Skill 是知识仓内的仓内专用 Skill，也是 GitCode Handler 的业务适配层，只在本仓处理 Issue 时使用。GitCode 状态机、外部操作和发布安全门禁由 `gitcode-issue-handler` 与 `gitcode-toolkit` 提供，二者以 vendored 副本内置于本仓 `.agents/skills/`（来源 `cann/cannbot-skills`，见各副本 SKILL.md 的 Vendored 声明），不依赖 cannbot-skills 仓 checkout 即可启动；知识检索由本仓 Query Skill 提供。vendored 副本保持上游原样，缺陷修复和新能力回到 cannbot-skills 上游合入后再同步副本，不在本仓直接改写其内部实现。

## 边界

- 目标仓库固定为 `cann/cannbot-knowledge`，正常 single/batch 只处理核心 open Issue。
- 默认只读调查并保存 `analysis.md`、`reply.md` 等 Handler 材料；不改知识卡、索引、治理文件、源码或 `.gitcode/`。
- 用户明确要求修复缺陷时，才在原 Handler 的代码复现、验证和交付门禁内进入代码修改；知识内容修改仍需遵守本仓贡献、来源、导航、日志和评审流程。
- 本 Skill 不提供 webhook、定时任务或无人值守运行器，不因新 Issue 或新评论自行启动。
- 配置只决定 Handler 已有能力，不扩大当前会话授权。禁止把“处理 Issue”解释为允许关闭、自动追问回复、commit、push 或创建 PR。

## 依赖与配置

1. 依赖解析顺序：优先使用本仓内置的 vendored 副本，即 `.agents/skills/gitcode-issue-handler/` 与 `.agents/skills/gitcode-toolkit/`，并将 `ISSUE_HANDLER_SKILL_ROOT` 指向本仓的 Handler 目录（`$REPO_ROOT/.agents/skills/gitcode-issue-handler`）；只有用户明确要求切换或 vendored 副本缺失时，才改为同一 Agent 客户端 user/global 级安装的外部副本。
2. 准备 Handler 要求的 Python 依赖。实际访问 GitCode 时通过 `GITCODE_TOKEN` 提供具有所需 Issue 权限的 Token；只初始化配置或查看规则不需要 Token。
3. 首次使用先进入原 Handler 的配置流程，保留已有设置。仓库默认值见 [配置模板](assets/classify_config.yaml.template)；模板是审核基线，不会自动覆盖实际配置。
4. 实际配置位于 `.cannbot/gitcode-issue-handler/config/classify_config.yaml`。`auto-response`、`auto-assign` 和 `auto-assign-fallback-user` 默认保持关闭或留空；只有用户明确要求调整自动响应方式时才修改。
5. 知识检索使用本仓现有 `knowledge-query`、按需使用 `ascendc-api-knowledge-query` 或 `runtime-api-knowledge-query`。索引缺失或 stale 时停止相关查询并报告维护缺口，不扫描全库、不静默重建。

## 选择入口

| 当前请求 | 动作 |
|---|---|
| 只询问本 Skill 的规则或模拟流程 | 读取适用参考并回答；不建运行树、不访问 API、不检查 Token |
| 初始化或调整配置 | 进入原 Handler 配置流程，复用本仓模板；本次不处理 Issue |
| 显式单个 Issue URL | 读取原 Handler 的 single/intake 入口，并叠加本 Skill 的调查规则 |
| 批量处理或续跑 | 使用原 Handler pipeline；新一轮 `resume --new-run`，续跑 `resume` |
| 怀疑 Issue 已由 PR 解决但未关联 | 先运行 PR–Issue 关联扫描，再决定回复或补关联 |
| Committer 提名或角色任命申请 | 先取本仓可核验贡献，再按提名记录式回复；不承诺任命结论，见[角色任命申请](references/role-nomination.md) |
| 只拟稿、不发送 | 正常完成调查和材料审核，不执行外部发布 |
| 自动回复、指派、关闭、修代码或创建 PR | 分别核对原 Handler 授权和本仓边界，不从其他操作推导授权 |

批量入口与原 Handler 一致：

```bash
python3 "$ISSUE_HANDLER_SKILL_ROOT/scripts/issue_pipeline.py" \
  resume --new-run --repository-root .
```

后续严格按脚本返回的 `next_action`、`required_references` 和结果契约推进。不要用本 Skill 另建一套 Issue 队列、分类 JSON 或评论执行器。

## 调查与拟稿

1. 读取原 Handler 当前阶段要求的全部参考；处理范围核查和响应材料时，另读 [Issue 路由](references/issue-routing.md)。
2. 对知识问题、知识需求及包含 CANN 技术判断的其他 Issue，另读 [知识证据与回复约束](references/knowledge-evidence.md)，在 Handler 自有知识预检之外完成本仓知识检索。两种查询的证据角色不同，不能互相替代。
3. 按诉求类型选择回复结构：缺陷、知识问题与知识需求按[回复结构（六段式）](references/reply-structure.md)组织；角色任命申请不适用该结构，改读[角色任命申请](references/role-nomination.md)的四段式；治理建议与 RFC 默认 `list-only`，不套六段式。
4. 从完整标题、正文、表单字段、评论和附件识别实际诉求；标题前缀只作路由线索。信息冲突或不足时保留未知，索要最小缺失字段。
5. 按路由形成可核验结论和回复。搜索候选、卡片标题或摘要不是最终证据；采用卡片前必须阅读全文并核对来源、平台、版本、生命周期和失效边界。
6. 默认将处理方向保持在评论答疑或补充信息请求。只有当前请求明确包含修复/交付时，才把相应任务推进到原 Handler 的代码或知识修改流程。
7. 按原结果文件契约填写 `analysis`、`reply`、`source_verdict`、`response_review` 和 `next_action`，不增加未经允许的新字段。分析中记录实际读过的卡片、来源、源码和未解决缺口；公开回复只保留提出者需要的结论与链接。
8. 发布前由原 Handler 校验目标、分类、扫描完整性、授权和实时 open 状态。`accept` 只表示材料审核完成，不等于发布授权。

## PR–Issue 关联扫描

批量分诊前、或单个 Issue 疑似已有 PR 时，先运行只读扫描，规则见 [PR–Issue 关联](references/pr-issue-linking.md)：

```bash
# 全仓扫描
python3 .agents/skills/knowledge-issue-handler/scripts/scan_pr_issue_links.py \
  --repo cann/cannbot-knowledge --issue-state open --pr-state all \
  --output-dir .cannbot/gitcode-issue-handler/data/pr-issue-links

# 只扫单个 Issue（处理单个 Issue 前先跑这个）
python3 .agents/skills/knowledge-issue-handler/scripts/scan_pr_issue_links.py \
  --repo cann/cannbot-knowledge --issue 123 \
  --output-dir .cannbot/gitcode-issue-handler/data/issue-123
```

- 输出 `pr-issue-links.md`（漏斗 + 四阶段分组）与 `pr-issue-links.json`（含逐条证据），原始快照在 `raw/`，可用 `--from-raw` 离线复跑。
- `--issue N` 只取该 Issue 的正文与评论，PR 侧仍取全量用于反向匹配；`--from-raw` 与 `--issue` 可组合，用于在既有快照上复核单条。
- 扫描按证据强度逐级下降：Issue 声明修复 PR → Issue 仅提及 PR → PR 侧反向引用 → 标题相似。上一级命中就不再上报下一级，避免同一 Issue 被弱证据刷屏。
- 只有 `可直接闭环（Issue 已声明）` 是关单候选，且 `merged_at` 非空才算合入；`PR 已关闭未合入` 与 `待核对闭环` 都不能据此关单，`疑似匹配` 只作线索。
- 报告中的评论草稿只是文本。发布、指派、关闭一律回到原 Handler 的授权与回查流程，不从扫描结果推导。
- 扫描不修改 Issue 状态、知识卡、索引或 `.gitcode/`。

## 角色任命申请（Committer 提名）

`[Requirement]` 里的 Committer/Reviewer 提名与其它治理建议不同：它需要首响，但结论由维护者定。处理时先取证再拟稿，规则见[角色任命申请](references/role-nomination.md)：

```bash
python3 .agents/skills/knowledge-issue-handler/scripts/collect_nomination_evidence.py \
  --issue 105 --draft
```

- 只读脚本，仅 GET：输出申请人本仓 PR（含 `merged_at`、文件数、卡/索引数、增删行）、本仓 Issue、master 上的责任田规模，`--draft` 另生成四段式草稿骨架；输出目录默认按 Issue 编号隔离为 `data/nomination-<issue>`。
- 「已合入」只认 `merged_at` 非空；`index.md` 单列为索引，不并入卡片数，避免把索引改写成新增卡。
- 跨仓贡献（cannbot-skills、asc-tools 等）只标注为申请人自述，不用未核验数字代为背书。
- 回复用四段式（收到并保留记录 / 已核验贡献 / 待评审口径 / 治理归属），不适用[回复结构（六段式）](references/reply-structure.md)，不加根因-复现-影响小节，不写排期与结论承诺。
- 首响后保持 open 作为提名记录；任命结论明确后才关单，不由 Handler 自行关闭。

## 自动化边界

- `auto-response: false`：保存完整回复稿，用户审核准确目标和完整正文后才发送。
- `auto-response: true`：允许原 Handler 在当前已调用任务内发布符合条件的首次响应；不代表事件驱动触发，也不授权后续追问自动回复。
- 后续追问始终按原 Handler 要求单独批准。已有有效回复不重复发送，已有负责人不覆盖。
- `auto-assign` 默认关闭；知识库维护责任人未确认时保留待办，不根据卡片作者、评论者或模型推测自动指派。
- 不自动运行 stale close。已答复咨询如需闭环，必须另走原 Handler 的独立 dry-run 和精确清单授权。

## 输出与完成

逐项复用原 Handler 的运行目录、回查证据和报告。最终汇总每个实际处理 Issue 的类型、结论、平台状态、负责人、首响状态和下一步；知识问题另列实际采用的知识卡/来源，未命中或证据不足时明确缺口。

“已回复”不等于“知识已修改”或“问题已解决”。没有实际外部写入时明确说明结果只是草稿；没有运行复现、Lint 或来源核验时不得声称已完成这些验证。

## 修改验证

修改本 Skill 后运行 `python3 -m unittest evals.test_knowledge_issue_handler evals.test_pr_issue_links evals.test_documentation`，检查所有本地 Markdown 链接、Skill frontmatter、默认安全配置、路由覆盖和扫描器契约。涉及安装器或 `.gitcode/` 的变更不属于本 Skill 的默认改造范围。
