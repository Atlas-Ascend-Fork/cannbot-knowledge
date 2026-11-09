# 挖掘方法

由当前读取 Skill 的 Agent 执行。输入是外层已筛选的目标轨迹，不再对远端全量材料开展另一套筛选或调用模型流程。

## 先还原，再蒸馏

批量输入先读批清单和目录，再按候选机制组织多来源证据。小批可直接读取连续窗口，大批按 [batch-processing.md](batch-processing.md) 生成有界证据包。同窗相同文本可共享阅读，事件角色、顺序与版本逐一保留；按问题簇建立候选，不逐轨迹派子任务。建立实际用户目标、框架/模型、硬件/版本、命令与配置、源码修改、构建、运行、精度、性能和回退的时间线。区分用户转述、Agent 建议、源码观测、工具执行与产物验证；读取 outcome/result_metadata/limitations，生命周期完成、日志中的 PASS 和退出码为零均不可单独替代目标验收；截断内容不支持对被截部分下结论。不能用后来的源码解释旧日志。

按实验分别记录 before、尝试、结果和后续动作。多处同时改变时承认混杂，未证明的机制写 assumptions，缺失内容写 unknowns/limitations。相关性以实际任务和操作对象为依据；框架的环境调试调优同样在范围内，只有背景提示提及框架名则不构成任务证据。

先确认任务与操作对象，再读取候选需要的连续开发上下文、完整机制和验证输出。无需为无关长历史生成逐条报告，但不能从有限预览宣称全轨迹无知识。历史系统模板和 reasoning 可保留为 context_only；错误事件即使 actor 为 system 也不能一起排除。需要补证时合并多个事件请求，长单元跨页读齐；全文 dump、路径清单和已有摘要都不代替原文。覆盖只填实际语义已读范围，未读部分与证据确实不存在分别记录。

## 四类候选

| 形态 | 必需证据 | 适用判断 |
|---|---|---|
| repair_recipe | 失败、完整 before/after 机制单元、修后客观验证 | 修复在本轨迹内闭合 |
| diagnostic_rule | 触发、可执行探针、原始观测、可区分解释 | 根因可未最终修复，诊断分支须有证据 |
| negative_result | 完整尝试、客观失败/回退、适用边界 | 失败路线本身有可复用价值，不暗示成功 |
| validated_pattern | 完整实现/配置与实际验证 | 只声称轨迹确实完成的验证层次 |

同一根因的多轮调参、重试和重复请求历史合并；不同机制或失败条件分别保留，不按分片数量产卡。没有成功修复先检查诊断与失败形态，不能直接以“没有 after”跳过。纯问答、未执行建议、没有客观信号或没有非显然机制时可零产出。

逐条核对模型/框架专用结论：图捕获与回放路径、并行通信与同步、KV Cache/显存、量化与精度、编译后端、框架加载/兼容性、训练 offload/optimizer，以及相应环境条件。知识必须服务于真实模型或框架任务；独立算子微基准不能直接外推模型收益。

## 机制与指标

从原文找出完整函数、配置段、启动参数或诊断命令。多个 edit 片段只有在版本与顺序无缺口时才可恢复成一个单元；不能由记忆重写。工具输出带行号时可在 text 代码块保留原样，不应为代码美化删掉逐字核验所需内容。

逐字匹配失败时回原事件核对缺口。最长公共子串、任意字符数阈值、只保留一行调用都不能证明完整机制；需补读或修订挖掘候选，不能缩短 artifact 以通过校验。API 行为须同时有输入约束、参考实现/预期、实际实现及相应验证；源码中出现参数名不证明完整语义。数值显示为零与真实零、未记录与未发生必须区分。

每个采用结论给出原始来源与归一化 hash、事件锚点、对应机制 artifact 和客观 signals。Agent 自述、echo 自写结论、读取自写报告不构成设备验证。修改测试容差或固定成功日志不能当修复；它们的风险经客观观测证实时可形成诊断或失败知识。

脚本默认值不等于本次实际生效值，目录/虚拟环境名称不等于版本证据。用户提供的日志保持用户观测等级；源码复读只证明静态内容，不能升级成重跑成功。单项健康状态或缺少某类报错，不足以排除其他环境根因，诊断分支应保留仍未区分的解释。

性能改善须保留模型、硬件、精度、输入/输出长度、batch/并发、并行与测量口径，以及 baseline/candidate 的同名同单位指标。检查 warmup、同步、重复次数、统计口径和精度基线。TTFT、TPOT、服务吞吐、单 batch 与单 kernel 时延不能互换。缺乏可比基线时改述为本次观测或诊断，不写通用加速承诺。

环境与算子相关内容须给出服务于实际模型/框架任务的关系锚点；框架名、路径名和常驻系统提示不足以证明相关。验证明确区分源码读取、静态检查、CPU 参考、设备功能、端到端和性能测试，不能将前一级表述成后一级。中性地记录证据，不在阅读任务里预置应得到的根因或收益。

## 输出

全部写入 `.build/model-knowledge-trace-ingest/<run>/`。以批次为单位输出：

- `DRAFT-<area>-<n>.md`：按问题簇生成，一张草稿对应一个独立规则，可关联多条轨迹；正文按模型证据合同的六个章节组织。
- `manifest.json`：整批一份，包含完整候选清单、来源、实际阅读覆盖、skipped 与缺证据理由。
- `<route>/reconstruction.json`：每个 route 一份，traces 数组包含该 route 下所有有关来源各自的任务、环境、时间线、facts/assumptions/unknowns/limitations；同一来源跨 route 时保留各 route 实际采用部分。策展时对应 ledger 放在同目录。
- `batch-report.json`：整批一份，覆盖所有输入。无候选和暂缓来源仍保留覆盖与缺口；out_of_scope 在报告中记范围理由，不为无关任务生成领域重建或草稿。deferred 可保留待补证 candidate_ids，但不能因此进入发布。

整批只写一份候选 manifest 和 batch-report（见 [batch-processing.md](batch-processing.md)），不为每个来源分别重复生成整套报告再聚合。候选 manifest 的最小结构如下；claims、evidence_roles、sources 和 mechanism_artifacts 的具体形状复用 [runbooks-contract.md](runbooks-contract.md)，不另建一套模型响应格式。

```json
{
  "schema_version": "model.trace-mining.v1",
  "sources": [{"normalized_dir": "绝对路径", "raw_source_sha256": "实际 source hash", "normalized_trace_sha256": "实际文件 hash"}],
  "coverage": [{"source": 0, "indexed_sequence_range": [1, 100], "semantic_review_ranges": [[1, 100]], "unread_ranges": [], "limitations": []}],
  "candidates": [{
    "candidate_id": "trace1-c1",
    "route": "training",
    "draft_path": "DRAFT-runtime-1.md",
    "knowledge_form": "diagnostic_rule",
    "sources": [],
    "evidence_roles": {},
    "claims": [],
    "mechanism_artifacts": []
  }],
  "skipped": []
}
```

上面 sources/角色/claim/工件的空值只展示容器结构，有候选时必须填入真实内容。`candidate_id` 在本批唯一；批量汇总时加来源前缀。没有候选时保留真实 coverage、重建和零产出理由，candidates 为 `[]`。

候选的 `sources` 使用来源对象数组；已有 mine 产物也可用整数索引引用该原始 manifest 的顶层 `sources`。离线 `scripts/mining_sources.py` 将这类引用按候选数组的原顺序解析为来源对象，拒绝布尔值、越界索引和缺失 hash。批量汇总保留原 manifest/hash，同时在汇总副本中解析来源，不能让旧索引改指另一批次的来源。候选的角色、claim 和工件锚点中的 `source` 始终指向该候选自己的来源数组；最终策展账本必须写来源对象。

重建采用 `model.trace-reconstruction.v1`，内容与证据校验器一致：顶层 route 与 traces；每个 trace 的 source 对象与最终 ledger 的对应来源相同；task.summary、environment、timeline、facts、assumptions、unknowns、limitations、coverage 均齐全。timeline/facts 使用本来源的 event_refs；coverage 同时记录 `[1,N]` 索引范围与实际语义读取范围，不冒充全量完成。

## 来源字段与运行观测不得串用

重建逐来源填写环境和事实。每个非未知的模型、精度、并行、offload 等条件，都须在本来源 facts 中列出支持它的事件；模板、相邻来源和同簇默认配置不能填补缺失字段。区分配置明示、用户报告、源码推断和工具运行观测，缺证字段明确未知。发现重建与 facts 冲突时先修重建，不用下游暂未采用为理由保留。

before 配置仅证明曾记录该配置，不证明此前执行过它，更不证明它以某种方式失败。只有实际运行命令与结果能构成该次运行的观测；负向知识从完整尝试和实际失败提取，不为凑“触发”伪造前一次失败。正文中新增的通过标准、分支规则、环境限定和根因判断也必须进入 claim/证据映射；仅能证明失败侧时收窄到失败侧。
