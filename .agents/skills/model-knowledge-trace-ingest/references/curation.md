# 策展、审查和落库

由执行 Agent 完成语义判断与最终写作，脚本仅核对证据和冻结内容。

## 查重与准备

先对整批候选按问题/机制归组，使用知识库 Query 查重，包含 draft 和未知平台候选，阅读完整旧卡、来源及本批草稿，再决定 create、update、merge、defer 或 reject。比较机制、适用条件、观测和边界，同主题可以合并但不得丢失独立增量。

每个候选恰好有一个去向，合并项在 source_candidate_ids 列全体成员。复现数按实际独立实验判断，相同会话的分片、重复导出与子会话不自动算独立复现。

在调用方工作目录准备：

```text
reconstruction.json
ledger.json
staged-cards/<area>/<slug>.md
```

遵守 [runbooks-contract.md](runbooks-contract.md)。账本绑定重建、输入候选 manifest、规范化来源及批清单的实际 hash。批级报告记录所有来源的去向。拟更新卡片还须记录 expected_target_sha256，重新读取旧卡后冻结，不用盲目覆盖。

最终卡包含中文标题、摘要、一个 H1 和六个必要章节，Frontmatter 遵守仓库 Runbook Profile。新卡默认 draft，不用入库或脚本通过伪造 verified。私有轨迹锚点、来源 hash 和重建留在工作目录，公开卡只保留可复用知识及其证据边界。

## 保留证据的策展入口

完成语义决定后写 decisions.json 数组；每个本 route 的原 candidate_id 恰好一项。例如：

```json
[
  {"candidate_id":"c1","status":"published","operation":"new","target_path":"runtime/example_slug.md",
   "dedup":{"decision":"create","queries":["实际执行的查询"]},"reproduce_count":1,
   "scope_evidence":{"summary":"本机制与实际模型/框架任务的关系","anchors":[{"source":0,"sequence":1},{"source":0,"sequence":3}]},
   "validation_scope":["source_read"],
   "omit_claims":[{"claim_id":"不采纳的原claim id","reason":"真实缺证原因；没有删减时省略此字段"}]},
  {"candidate_id":"c2","status":"deferred","reason":"实际未决项"}
]
```

```bash
python3 <SKILL_DIR>/scripts/curate_candidates.py <mine>/manifest.json --decisions <work>/decisions.json --reconstruction <batch>/reconstruction.json --output <batch>/ledger.json --route <route> --batch-manifest <input>/manifest.json
```

入口把原候选完整复制为新账本，解析来源索引而不改变候选内部编号，保留性能数据和额外 claim 字段，批准标记一律 pending/false。只接受显式允许的决策字段；不会改写草稿、判断结论、创建 PASS 或写知识库。输出必须不存在，且不能放入规范化来源。没有输入批清单时可省略 --batch-manifest；重建须与输出 ledger 同目录。

该入口一项决定对应一个原候选；单个候选本身可以跨多轨迹。多个候选共用一张卡时由执行 Agent 按合同显式合并账本，保留全体 source_candidate_ids、source_claims、独立比较和重排后的锚点，再运行同一校验器。不要临时写白名单字段拼装器或自动删 claim/缩引文的修复脚本。需要改变结论时回挖掘阶段形成明确的新修订。

## 集中校验与冻结

先按[脱敏与公开自包含检查](privacy.md)检查整批待审卡及导航。归一化脱敏不构成发布豁免；标题、摘要、代码块、日志和新增解释都须重查。未公开的候选编号、同簇指代不能承载复现条件，必须补全有证据的内容或链接现存公开卡；缺证时删除依赖结论或暂缓。

```bash
python3 <SKILL_DIR>/scripts/validate_model_evidence.py <batch>/ledger.json <batch>/staged-cards --route <route> --candidates-manifest <mine>/manifest.json --report <batch>/validation-01.json
python3 <SKILL_DIR>/scripts/review_cards.py subject <batch>/ledger.json <batch>/staged-cards
```

证据检查拒绝来源变化、缺角色、非客观信号、非逐字机制、候选漏项、不可比性能口径和非法治理字段。通过不证明因果成立。subject 冻结实质账本、重建和卡片字节；它只规范化 result/verbatim_verified 两类批准标记，使审查后的标记更新不改变审查主题。

CLI 默认收集每个候选遇到的首个错误，一次报告多个候选的问题；共享依赖错误仍按批次报告。--report 写入新的完整 JSON 文件，终端只输出有界摘要；--fail-fast 恢复首错退出。校验临时缓存最近四个来源，减少同源重复解析，并在结束时重查所有采用来源的 hash。按报告集中修复，再全批验证；局部检查不能冒充最终全批通过。仓库级全量检查集中在落库收口，不为每轮引文调整重复运行。

## 独立审查

由当前运行时或调用方安排实际独立审查者，读取 [reviewer.md](reviewer.md)、冻结 subject、重建、账本、最终卡、相关原始事件与旧卡。保存审查者实际返回的原始 receipt，并核对真实运行时身份。作者不得代填 PASS；不能安排独立审查时停在待审。

正文、实质账本、重建或来源绑定发生变化须重新验证、冻结和审查。NEEDS_REVISION 回到准备阶段，不能只改 receipt。审查通过后仅将 evidence_audit.result 改为 pass、机制工件 verbatim_verified 改为 true。

```bash
python3 <SKILL_DIR>/scripts/validate_model_evidence.py <batch>/ledger.json <batch>/staged-cards --route <route> --candidates-manifest <mine>/manifest.json --approved
python3 <SKILL_DIR>/scripts/review_cards.py verify <batch>/ledger.json <batch>/staged-cards --receipt <batch>/receipt.json --sender <已核对的运行时审查者身份>
```

verify 核对冻结字节、PASS、finding 级别、时间和调用方核对的 sender。它无法自行认证运行时身份，填写 --sender 本身不构成独立审查。

新合同还要求 receipt 逐卡确认全部 claim、完整 artifact 和标题/摘要/正文覆盖。证据、范围、API、因果、比较、验证或隐私问题即使标成 minor 也不能通过；修正后重新冻结并取得真实审查，不能复制旧 PASS 到新 subject。

## 写入与收口

两项检查均通过且原始 receipt 已核对后，由执行 Agent 将审查过的字节写入 `knowledge/model/<route>/runbooks/<area>/<slug>.md`。写入前再次核对来源、最终字节和目标：

- 新建只使用不存在的目标，拒绝覆盖已有卡。
- 更新/合并核对目标当前 SHA-256 与 expected_target_sha256；不一致则重查并重审。
- 目标路径和 Frontmatter 先通过当前仓库 Contract；逐字复制 staged 内容，写后核对目标 hash，不在发布时改写知识文本。
- 路径必须位于注册的模型 route 和 runbooks area 中，不经过符号链接或越过知识根。

落库由执行 Agent 按上述前置条件完成。批次完成前不把计划 published/merged 状态当作实际入库结果；由收口者统一更新受影响的中文 index 和实际日期日志，执行全库 Lint、索引更新和目标 Query 验证。失败或未执行的检查如实记录，不扩大到无关知识。

调用方保存相对任务开始状态的实际变更路径 JSON 数组（排除之前的工作区修改），核对发布清单及已写入字节：

```bash
python3 <SKILL_DIR>/scripts/review_cards.py inventory <batch>/ledger.json <batch>/staged-cards --changed-paths <work>/operation-changed-paths.json
```

清单中的模型 Runbook 正文必须恰好等于采纳目标，公开字节须与 staged 相同；索引、日志不算新卡。此命令只读调用方提供的差异，不运行 Git、不认证差异完整性，也不执行发布。任务已有未提交修改时，不把整个 git diff 当作本批范围。

交付候选去向、实际写入路径、证据与未决项、独立审查记录和检查结果。Skill 不自动提交 Git、推送或创建远端工作项。

重建与卡片一起冻结：环境字段逐一回本来源事实锚点核对，不接受跨来源填默认值。before 配置不能代替 before 运行观测；正文判读规则须与采用的 claim 一起映射。独立审查指出重建、来源归属或未映射断言问题时，修订有关重建/候选/正文与绑定 hash，保留初次拒绝记录，重新冻结并取得新审查；不只修一张卡或复用旧 PASS。
