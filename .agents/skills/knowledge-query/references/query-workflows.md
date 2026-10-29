# 查询与证据工作流

复杂任务使用本文件，将检索召回和工程判断分开。单一事实问答使用主 Skill 的轻量路径即可；这里不要求额外 Agent，也不授权执行构建或实验。

## 什么时候重入检索

首次领域决策前确认目标并查覆盖；后续复用已读卡和判型证据，只在出现新 API、错误信号、平台/版本变化或尚未解决的决策时重入。每轮说明要补的缺口、检索角度和新增证据；没有变化时不重复 discover、设备探测或同义改写查询。

## 审计查询

### 自然语言到查询 Scope

Agent 负责提取，脚本不承担自然语言推断。先保留用户原意，再按下列规则组织检索：

1. 记录平台与每个候选维度的值、原文或已读配置证据，以及状态 `explicit`、`inferred`、`unknown`。置信度只描述推断把握，不能替代确认；复杂任务在审计说明中记录，轻量查询无需另建文件。这些说明不写进 Scope 对象或卡片 Frontmatter。
2. 用户直接给出的条件、用户已确认的提取结果，以及任务明确指定配置中的确定条件，可提交为 Scope；无需反复让用户确认同一句明确要求。模型名联想、优化意图和未定义数值阈值仍是推断或未知，只作文本线索。
3. 先按任务领域选择 Registry 中已注册且适用于目标路径的 Schema，再将已确认部分按该 Schema 的维度和规范值构造 Scope，不将模型推理字段套到其他领域。遗漏未知维度，不补 `any`，不把未提及特征写为 `none_of`。`any` 必须有明确不限制该维度的依据。只有推断线索时不传 Scope，保持原平台、状态、Profile 和文本检索。
4. 同一场景不同维度放进同一个 `all_of`；确实独立的备选场景分成 `any_of` 分支。不能把“Prefill+GE 或 Decode+eager”展开成允许四种组合；长上下文、batch、并发、服务模式、并行和部署拓扑分别表达。定量数值不自行映射为大/小或长/短。
5. 先宽召回；若缺失条件会改变适用结论，优先询问那个条件，并继续不依赖答案的阅读。结果说明实际用于过滤的已确认条件、只作线索的推断，以及命中分支的待确认前提。`unknown` 结果仍可相关，不能包装成“确认适用”。

| 用户表达或证据 | Scope 处理 | 阅读与提示 |
| --- | --- | --- |
| “A3 上优化 Prefill 吞吐” | 平台 A3；`phase=[prefill]`、`objective=[throughput]` | 执行模式、模型结构未知，不从吞吐推断大 batch |
| “这个模型可能是 MoE，想降低时延” | 只提交明确的 `objective=[latency]`；MoE 作文本线索 | 确认结构前不提交 `model_features`；不自动改成 TPOT/TTFT |
| “长上下文、小 batch、online” | 三个独立维度；不推导并发或 PD | 并发和部署拓扑按需要再核对 |
| “模型具有 MoE 和 MLA” | `model_features.all_of=[moe,mla]` | 卡片只要求 MoE 时可满足该特征条件；其他前提仍逐项检查 |
| “未提 MLA” | 不写 `none_of` | 只有明确不具备 MLA 才能提交查询否定条件 |
| “已启用 TP，明确未启用 CP” | `parallelism.all_of=[tp]`、`parallelism.none_of=[cp]` | 未启用 CP 不等于单卡；其他并行状态不推断 |
| “已启用 TP”，未说明 CP | 只写 `parallelism.all_of=[tp]` | 卡片要求未启用 CP 时仍为未知，不以未提及作为否定证据 |
| “Prefill+GE 或 Decode+eager” | 两个 `any_of` 分支，每个分支分别 `all_of` | 按命中分支读正文，禁止跨分支补齐证据 |
| 来源说明 FP8/MXFP4 按模块共同组成混合方案 | 现有量化枚举的 OR 不能表达该组合；卡片暂不写 `quantization` | 具体混合配置按正文核对；单一量化格式查询可召回该卡，但量化适用性仍未知 |

以上是 Agent 消费流程，尚不表示存在自动提取器或推断准确率实验。Scope 的结构、归一化与过滤仍只使用共享 Contract。

### 从相关结果到结论

检索返回不等于问题已回答。先区分机制解释、方案选择、停止启用和实际部署：机制解释应覆盖题目所需的结构与限制，不能只解释一个实现分支便宣称整个主题已经完成；方案选择还需满足会改变选择的前提。缺失前提可保留条件化结论，不以追问更多环境信息代替已能完成的解释。

- 优先读取规范入口，再按需沿正文链接补齐相关规则或实现。前五项都只有局部线索时，用主题名称或关键约束补搜；不能从某个故障卡直接拼出整个机制或通用配置。
- 区分设计目标、固定源码实际编排和已观测效果。来源写“重叠”时仍需核对分支、依赖与同步，不能从指南示意图宣称实现已在副流并行，或从局部修复推断后续状态传播已验证。
- 按目标版本核对后端接口、守卫和配置格式；同名技术的历史注册、同步或量化路径不能合并为当前通用步骤。未读的关联链接只作补证入口。
- 输出分别说明已回答的结论、仍缺的条件和未执行的验证。条件不足的回答可以有价值，但不把它计为已完成方案选择或已完成部署；指标分母为零时不虚报正确率。

### 未知原因与补证顺序

先判断候选是否能回答当前 decision，再判断适用条件。只共享“图模式”“并行”或“量化”等词、却讨论另一种机制或故障的卡片，不进入答案证据；不必为填满前五项采用它们。这个选卡步骤不改变原始搜索结果、排序或 receipt。

主题不相关不能直接判为 Scope `conflict`：冲突需要已知适用前提之间有明确矛盾。模型特征、实现或环境未说明时仍可能是 `unknown`；不能从未提及某个集合特征推导“不具备”。

对相关但适用性未知的卡片，说明具体缺口及下一步，不只重复“环境待确认”：

| 缺口 | 下一步 | 完成边界 |
| --- | --- | --- |
| 查询缺少会改变方案选择的条件 | 先读正文找出实际前提，再询问最关键的少量条件；继续可独立完成的机制解释 | 答复前保持条件化结论，不从模型名、部署惯例或优化目标补硬 Scope |
| 固定来源暂不可读或未准备 | 保留来源 URL、revision 和未读范围；需要恢复时交给维护者或资源准备流程 | Query/Lint 不自动下载；卡片引用来源不等于当前已复核该来源 |
| 来源本身没有平台、版本、效果或测量记录 | 区分已有机制证据与缺失的适用性、效果证据，记录所需材料 | 不把缺字段改成 `any`、`agnostic` 或虚构 `verified`；不能用补问用户环境代替来源证据 |
| 顶层 Scope 无法表达正文的否定或组合条件 | 逐项核对具体实现与正文，明确尚未由机器判定的前提 | 不把缺失集合成员当作“不具备”，不把 OR 当成联合方案；机器 `match` 只覆盖已声明条件 |

将一个复合问题拆成多个 decision 补搜时，各自保留查询和证据。沿链接或补搜取得的证据可以帮助完成解释，但不得回填为原始 Top5 命中；评测中仍保留原题、原分母和原始失败。

### 审计步骤

1. 建立目标边界：实体、platform、CANN version、工程形态、dtype/layout、workload 和验证边界。
2. 列出 decisions；每个 decision 只回答一个判断，例如参数单位、错误信号是否有已验证修复、性能瓶颈的主导机制。
3. 为每个 decision 运行窄查询，保存独立 receipt。互不依赖的 decision 可以并行，但 receipt 路径不能复用。
4. Agent 先根据脚本返回的路径、title 和 description 选择候选，再阅读全文；读完后决定是否沿链接查看相关卡、固定来源或 include，不要求读完所有命中或链接。记录事实、适用边界、negative evidence、conflict 和 gap。没有搜索命中不是 negative evidence；只有来源明确说明不支持、限制或失败，才能作为否定性技术证据。
5. 主任务将 decision 标为 `covered`、`conflicting`、`insufficient` 或 `gap`。只对未解决项补搜；补搜应从实体转向错误信号、从机制转向 API 契约或从现象转向验证过的修复路径。
6. 无新增证据或达到预算时停止。把 target、decision、receipt 和采用的卡片路径/指纹冻结为 `cannbot-retrieval-state.v1`；每条 receipt 必须使用与 target 完全相同的平台集合。全部 covered 后运行 `retrieval_state.py --require-ready --receipt`，它会核对完整索引 provenance 并重放过滤、评分、排序和命中；生成的 ready receipt 会绑定全部 search receipt 的 SHA-256。
7. 实现后的正确性、性能和平台实验写入 `cannbot-retrieval-outcome.v1`，绑定 state、ready receipt 和真实产物 SHA-256，再运行 `retrieval_outcome.py --require-complete --receipt`。不得修改原始 search receipt；任何改动都会使 outcome 链失效。

### 决策状态与停止

| 状态 | 证据情况 | 后续 |
|---|---|---|
| `covered` | 已读证据足以回答本决策，范围匹配且关键冲突已处理 | 可进入 ready 校验；不等于已做工程实验 |
| `conflicting` | 已读来源对同一范围给出不兼容结论 | 明确版本/重载/适用条件，未消除前不能 ready |
| `insufficient` | 有相关线索，但缺关键参数、范围或验证依据 | 只补缺失部分；停止时如实交付缺口 |
| `gap` | 当前决策没有可采用证据 | 保留有效零命中记录或具体阻塞，不制造 covered |

### 关联阅读如何进入审计链

- 沿链接读到的新卡不会自动进入原 search receipt。需要采用为 state 的 `evidence` 时，用该卡的准确标题/独特术语、适合的 Profile 和**同一目标平台集合、同一 decision ID**定向查询，保存新 receipt；实际命中该卡后才引用返回的 `path` 和 `card_sha256`。不能手填未出现在绑定 receipt 中的卡片，或修改旧 receipt 加入命中。
- 未定位 draft 补搜没有目标平台，与平台识别查询一样只作独立线索记录；不能绑定到有明确目标平台的 state 来生成 ready。无法获得符合目标边界的证据时，保持 insufficient/gap，不改写卡片或审计文件绕过校验。
- 不同平台的差异比较分别建立目标与证据链；共同适用查询使用完整的平台集合，每条 receipt 必须一致，不能把 A2 与 A3 单独结果拼成一份共同支持证明。
- 本机 SDK 头文件、固定源码与实验产物不是 Concept，不放入 state 的卡片 evidence。保留其真实路径、版本/commit、已读范围及它支撑的 decision；只有真实发生的工程验证才记录到 outcome。不要为记录“读过头文件”伪造 verified 实验。

已读内容无法闭合决策时，输出部分结论和缺口即可；不运行 ready 来“强行完成”，不把结构校验成功当作技术正确性证明。

最小 state：

```json
{
  "schema_version": "cannbot-retrieval-state.v1",
  "target": {"entity": "DataCopyPad", "platforms": ["a2"]},
  "decisions": [{
    "id": "api-contract",
    "question": "目标接口契约是什么？",
    "status": "covered",
    "receipts": ["/absolute/search.json"],
    "evidence": [{"path": "ops/ascendc/apis/example", "card_sha256": "<sha256>"}]
  }]
}
```

最小 outcome manifest：

```json
{
  "schema_version": "cannbot-retrieval-outcome.v1",
  "state": "/absolute/retrieval_state.json",
  "state_sha256": "<sha256>",
  "ready_receipt": "/absolute/retrieval_ready.json",
  "ready_receipt_sha256": "<sha256>",
  "events": [{
    "decision": "api-contract",
    "outcome": "verified",
    "summary": "目标平台验证通过",
    "observed": ["correctness passed"],
    "artifacts": [{"path": "/absolute/test.log", "sha256": "<sha256>"}]
  }]
}
```

## 输出建议

```markdown
# 结论
- <当前 decision 的结论；区分来源事实与工程判断>

## 证据
- `<card>#<anchor>`：<事实、revision 与适用边界>

## 冲突或缺口
- <只有存在时输出>

## 建议验证
- <知识证据不能替代的目标平台检查>
```

不要倾倒所有候选。正式交接可附 `cannbot-retrieval-review.v1`，其中 `state_sha256` 绑定 state、`verdict` 为 `approve|reject`；reviewer 只检查覆盖、冲突、边界、receipt 与引用文件一致性，不重新生成工程方案。
