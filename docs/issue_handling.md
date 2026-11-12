# 使用 Agent 处理知识库 Issue

`knowledge-issue-handler` 是 cannbot-knowledge 的仓内专用 Skill。它把通用 GitCode Issue 处理能力与本仓的知识检索、证据和治理规则组合起来，用于分析知识问题、知识需求、工具缺陷和治理建议。

默认模式是**只读调查并生成回复草稿**：不自动发送评论、不自动指派、不修改知识或源码，也不自动关闭 Issue。

## 能处理什么

| Issue 类型 | 默认行为 |
|---|---|
| 知识问题反馈 | 定位并阅读全文，核对来源、平台、版本和适用范围，确认问题或说明证据缺口 |
| 知识需求 | 检查实际知识覆盖并查重；已有内容直接答复，未覆盖则说明知识缺口 |
| 工具与 Skill 缺陷 | 核对复现材料和实际实现，形成诊断与处理方向；默认不改代码 |
| 治理建议与 RFC | 默认只列举给维护者评审，不自动回复或承诺方案 |
| 角色任命申请（Committer 提名） | 核本仓可验证贡献后给提名记录式首响；任命结论由维护者决定，不承诺、不代评 |

角色任命申请是治理类里的例外：它需要首响，但不能套知识/缺陷的根因-复现结构。先跑只读取证，再按四段式拟稿：

```bash
python3 .agents/skills/knowledge-issue-handler/scripts/collect_nomination_evidence.py \
  --issue 105 --draft
```

脚本输出申请人本仓 PR（`merged_at`、文件数、卡/索引数、增删行）、本仓 Issue 与 master 上的责任田规模，`--draft` 生成草稿骨架；输出目录默认按 Issue 编号隔离，两个申请人不会互相覆盖；跨仓贡献只标为申请人自述。口径见 [角色任命申请](../.agents/skills/knowledge-issue-handler/references/role-nomination.md)。

缺陷、知识问题和知识需求的回复主体按六段式组织：根因 / 复现 / 影响 / 修复方向 / 验证建议 / 当前进展与下一步。知识问题与知识需求按自己的语境换段名（例如「缺口定位」「入库方向」），不硬套缺陷段名；治理建议与 RFC、角色任命申请不使用该结构。各段写什么、复现与影响两段的证据分级、段落裁剪规则见 [回复结构](../.agents/skills/knowledge-issue-handler/references/reply-structure.md)。

处理结果沿用通用 Handler 的运行目录和报告。每条实际处理项包含分析、回复稿、证据、负责人/首响状态和下一步；已有有效回复不会重复发送。

## 准备依赖

需要支持 Skill 的 Agent 客户端与 Python 3.10+。`gitcode-issue-handler` 和 `gitcode-toolkit` 已以 vendored 副本内置于本仓 `.agents/skills/`（来源 `cann/cannbot-skills`，见各副本 SKILL.md 的 Vendored 声明），**无需再安装、不依赖 cannbot-skills 仓 checkout 即可启动**。适配层默认把 `ISSUE_HANDLER_SKILL_ROOT` 指向仓内副本；只有需要切换到更新版本且上游尚未同步时，才另行以 user/global 级别安装外部副本并在会话中显式切换。运行依赖 `PyYAML` 与 `requests` 已由本仓 `requirements.txt` 声明。

确认三个 Skill 均可识别：

- `gitcode-issue-handler`（仓内 vendored）；
- `gitcode-toolkit`（仓内 vendored）；
- `knowledge-issue-handler`。

实际读取或回复 GitCode Issue 时，在启动 Agent 的终端通过 `GITCODE_TOKEN` 提供 Token，并仅授予目标仓所需权限。Token 不写入仓库或配置文件。仅查看规则、初始化配置时不访问 GitCode。

## 初始化配置

在本仓根目录启动 Agent，输入：

> 使用 knowledge-issue-handler 为当前仓库初始化配置。复用知识仓默认范围，保持自动回复和自动指派关闭；本次不处理 Issue。

实际配置保存在 `.cannbot/gitcode-issue-handler/config/`，运行缓存、队列和报告也位于该本地运行树。`.cannbot/` 是本仓既有的运行时根（`install.sh` 写入的 `.cannbot/knowledge.env` 与用户级知识根 `~/.cannbot/cannbot-knowledge` 同属这一命名空间），Issue 处理只是在其下增加 `gitcode-issue-handler/` 子目录，不是独立的产品目录。该路径已在 `.gitignore` 中忽略，不会随提交进入仓库。已有配置必须保留，不能用模板覆盖。仓内审核基线位于 `.agents/skills/knowledge-issue-handler/assets/classify_config.yaml.template`。

## 处理单个 Issue

只分析和拟稿：

> 使用 knowledge-issue-handler 处理 https://gitcode.com/cann/cannbot-knowledge/issues/123，先拟稿，不发送，不改代码。

如果这条 Issue 可能已有 PR 在修，可以先只扫这一条：

```bash
python3 .agents/skills/knowledge-issue-handler/scripts/scan_pr_issue_links.py \
  --repo cann/cannbot-knowledge --issue 123
```

`--issue` 只拉这一条 Issue 的正文和评论，PR 侧仍取全量用于反向匹配；输出目录默认在 `.cannbot/` 下，换成 `--output-dir` 可单独存放。

审核草稿后，如确认发送，再明确指定同一个 Issue 和对应回复稿。后续追问始终需要单独审核，不因曾经批准首响而自动发送。

## 批量处理

新一轮分诊并准备材料：

> 使用 knowledge-issue-handler 批量拉取并处理当前仓库需要关注的 Issue，先拟稿，不发送，不改代码。

继续同一轮次：

> 使用 knowledge-issue-handler 继续当前批次，从已有队列和等待状态恢复，不重复回复。

批量任务会复用通用 Handler 的增量游标、watchlist、限流、任务队列和逐项回查。治理建议/RFC 默认只列举，知识问题与知识需求会额外执行本仓知识检索。

## 扫描已合入 PR 的关联

很多 Issue 其实已经由 PR 解决，但 Issue 与 PR 都没有写关联，导致长期停留在 open。处理前可以先跑只读扫描：

> 使用 knowledge-issue-handler 扫描当前仓库未闭环 Issue 与 PR 的关联，只出报告，不发评论、不改状态。

扫描按**证据强度逐级下降**，不是两侧证据对称投票：

| 阶段 | 判定 | 能否据此关单 |
|---|---|---|
| ① Issue 声明修复 PR（`关联 PR:` 字段、`已提交 PR #N`、同句"本 Issue + 已修复"） | 按该 PR 自身状态定 | PR 已合入时可以 |
| ② Issue 仅提及 PR（`在 PR #68 上建索引`、`与 PR #100 互补`） | 合入也只算待核对 | 不可以 |
| ③ Issue 没提 PR，由 PR 侧反向命中 | 需要读 diff | 不可以，先核对 |
| ④ 两侧都没引用，只剩标题相似 | 仅作检索线索 | 不可以 |

一条 Issue 有①时，不再上报它的②③④，避免同一 Issue 被多个"相关 PR"刷屏。

判定口径上有两点容易踩坑：

- **"PR 已关闭"不等于"已修复"**：只有 `merged_at` 非空才算合入，关闭但未合入的 PR 不能作为关单依据；
- **"已并入 PR #100"不一定是本 Issue 被修复**：`原 PR #99 已并入 PR #100` 说的是两个 PR 合并，扫描会跳过这类主语是 PR 的句子。

报告 `pr-issue-links.md` 顶部有漏斗表（每阶段命中多少 Issue，五项之和应等于扫描总数），正文按四阶段分组，并给出证据与置信度。只有 `可直接闭环（Issue 已声明）` 进入关单候选；`疑似匹配` 永远只是线索。评论草稿只是文本，发布、指派、关闭仍走通用 Handler 的授权与回查，扫描器本身只发 GET 请求。

## 开启自动首响

先用历史 Issue 验证分类、知识召回和回复质量。确认需要自动首响后，再明确要求 Agent 调整 `auto-response`；建议继续保持 `auto-assign` 关闭。

自动首响只表示：**在当前已经发起的 Agent 处理任务中，符合条件的首次回复可以经原 Handler 门禁直接发布并回查。** 它不表示：

- 新 Issue 创建后自动启动；
- 后续追问自动回复；
- 自动修改知识卡、源码或索引；
- 自动关闭、commit、push 或创建 PR。

当前改造不新增 GitCode webhook、定时工作流或无人值守机器人，也不修改 `.gitcode/`。如需这些能力，应作为独立部署任务另行设计权限、凭据、持久化和运行监控。

## 证据与失败边界

- 搜索命中只是候选，采用知识卡前必须阅读全文并核对来源和适用范围。
- 普通知识查询需要明确目标平台或项目缺省平台；平台不明时不猜测。
- 索引缺失、损坏或过期属于查询故障，不能当作“没有知识”，也不会在 Issue 流程中静默重建。
- 有效零命中只说明当前条件下未召回，不证明技术、API 或能力不存在。
- 知识问题被确认不代表已修复；知识需求被受理不代表已收录。
- 没有实际运行复现、Lint、来源核验或外部回查时，报告会保留相应缺口。

## 继续阅读

- [安装与使用](installation_and_usage.md)
- [形成可追溯回答](../recipes/answer_with_evidence.md)
- [贡献知识](../recipes/contribute_knowledge.md)
- [Knowledge Skills](../governance/specs/skills.md)
