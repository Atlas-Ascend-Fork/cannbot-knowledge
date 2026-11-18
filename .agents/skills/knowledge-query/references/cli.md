# CLI

需要组合过滤条件、解释输出或定位知识根时读取本文件。

## 知识根

Query 按 `--knowledge-root`、`CANNBOT_KNOWLEDGE_ROOT`、当前目录祖先中的 `.cannbot/knowledge.env`、仓内脚本位置依次解析知识仓。全局参数可以放在子命令前后；配置文件同时接受 `export CANNBOT_KNOWLEDGE_ROOT=...` 和不带 `export` 的形式。

这是数据根解析规则，不是独立 Skill 打包接口。完整安装使用仓库 `init.sh` 保留到规范源的链接，脚本由此可找到同一 checkout 的 `governance/contracts/`。单独复制 Query 目录可能仍能做普通索引搜索，但索引构建、完整校验和依赖 Contract 的 API 阅读等流程不完整，不能据此宣称已安装可用的全部能力。

## 索引

项目安装器默认先恢复文档与固定提交源码，再验证并按需构建 `artifacts/indexes/knowledge.sqlite3`。知识仓维护者在卡片、Registry、Profile、Schema 或 Contract 变化后执行：

```bash
python3 <skill-dir>/scripts/knowledge_index.py --knowledge-root <repo> build
python3 <skill-dir>/scripts/knowledge_index.py --knowledge-root <repo> verify --level full
```

Query 只读索引；索引构建通过统一 Contract 拒绝重复 YAML key 等不合法卡片。普通调用执行 quick stale check，写 search receipt 和校验 retrieval state 时还会把 SQLite document/posting 行逐项绑定到知识卡，并继续使用已校验的同一只读连接。缺失、损坏、卡片集合/时间戳变化、治理指纹变化或查询表不一致都失败关闭，不退回逐文件搜索。

## 本地来源

阅读本地证据时先区分路径基准，不把所有相对路径都拼在同一个根下：

| 位置 / 字段 | 路径基准与读取方式 |
|---|---|
| 搜索结果 `path` / `local_path`、`title`、`description` | 先据此选择相关候选；`local_path` 已是绝对路径，选中后打开并阅读全文 |
| 卡片正文中的本地 Markdown / 源码链接 | 普通相对路径以当前卡目录解析；前导 `/` 的知识链接以 Bundle 根解析；`#锚点` 指向当前卡。源码仍须满足登记的固定提交来源规则 |
| Frontmatter `sources[].resource` 的本地路径 | 知识仓根；按 Registry 核对归档或仓库、commit，不相对当前工程解析 |
| Ascend C API 的 `source_headers` | CANN 包内对应的 Ascend C 组件根目录；值已带 `include/`。Agent 决定需要查看时再拼接绝对路径并读取 |
| Runtime API 的 `source_headers` | 已确认的 Runtime 源码或对应组件根；固定源码布局与实际安装包 include 布局须分别核验，不能套用 Ascend C 根 |

选中卡片后阅读全文，再决定是否查看其相关内容或 include。知识库链接是有效入口，不需要另跑链接检查；`index.md` 只是导航，Agent 可继续沿其中的链接选卡。链接有效不等于内容适用于当前问题，仍需结合平台、生命周期和版本判断。

`sources[].resource` 中的登记路径相对于知识仓根（不是调用方工程或卡片目录）；四个源码仓统一使用 `cann-ops-raw/ascendc/<仓库名>/<40位commit>/...`。仓库 Registry 保存远程 repository 与允许的 revision；需要远程核对时可还原为 `<repository>/blob/<commit>/<path>`。API 的“源码中使用此 API 的算子”区块链接对应 Operator 卡和源码行，超出自动展示上限标注“部分算子”；仅有正文证据的示例单独标注。两者都是导航，不替代读取源码。

这里的知识仓根是 `discover` 输出的 `root`，包含 `governance/` 与 `knowledge/`；`knowledge/` 本身是 Bundle root，不是源码路径基准。Ascend C API 流程使用其[路径工具](../../ascendc-api-knowledge-query/SKILL.md)解析选定卡片的原始 source 或相对链接，再读取绝对路径；工具复用同一根解析与 Contract，不扫描替代文件。

模型 Recipes 来源使用 `cann-recipes-raw/<仓库名>/<40位commit>/...`，同样从知识仓根读取。每个模型来源仓只有一个已核验的最新提交，相关卡片、正文导航和图片均使用该版本；读取前仍须核对卡内条件与该版本实现。历史版本通过 Git 历史和日志追溯。PR、Issue 链接仍为远程工作项，不能拼接成本地源码路径。

资源未恢复时，Query 不自动联网或退回扫描源码。向用户说明缺口，获准后运行仓库登记的资源获取入口；安装器支持显式离线模式，但不能声称已核对不可用源码。索引只收录知识卡正文，不收录源码树；普通卡片链接与正文一起参与检索。

## Discover

```bash
python3 <skill-dir>/scripts/knowledge_query.py --knowledge-root <repo> discover [--json]
```

输出实际 Concept 总数及 domain、technology/scope、OKF type、路径 Profile 和 status 计数。结构占位目录和只有 Registry 的分类不计入覆盖。

这些是各维度的独立计数，不是平台/技术/Profile 的交叉覆盖矩阵。同一知识根、同一任务中可复用已有 discover；后续 search 仍会检查索引有效性，语料或治理指纹变化后再刷新覆盖判断。

## Search

```bash
python3 <skill-dir>/scripts/knowledge_query.py --knowledge-root <repo> search \
  --query <text> [--alt-query <另一语言短改写>] [--domain ops] [--technology ascendc] [--type apis] \
  [--task implementation] [--tag topic.data_movement] \
  --platform a2 [--include-shared] \
  [--source-technology triton] [--target-technology ascendc] \
  [--scope-file <confirmed-scope.yaml> | --scope-json '<confirmed-scope-object>'] \
  [--status stable|draft|deprecated|all] [--match text|literal] \
  [--decision <id>] [-k 10] [--json|--text] [--receipt <new-json>]
```

`--type` 过滤路径 Profile ID（如 `apis`），输出中的 `type` 是 OKF type（如 `API`）。`-k`、`--k`、`--limit` 等价。Search 默认输出 JSON；`--text` 供 Agent 或人工阅读精简候选：带本地 Markdown 链接的标题、路径、摘要和行数，不改变过滤与排序。普通问答选卡后阅读全文，采用该卡时可直接引用标题链接；状态、平台和复核事件回到正文核对。评分、信任层级及正式审计仍使用完整 JSON/receipt，不把文本输出当作审计载荷。

安装器可把项目缺省平台写入 `.cannbot/knowledge.env` 的 `CANNBOT_KNOWLEDGE_PLATFORM`，也可直接在进程环境中设置同名变量。普通 search 省略 `--platform` 时使用该值；显式 `--platform` 优先。`discover`、平台识别查询和 `--include-unlocated` 不使用该回退。没有缺省平台时，普通 search 仍要求显式 `--platform`。

### 过滤与匹配

- 重复的 tag 和 platform 使用 AND。
- platform 入参不区分大小写，显式参数和项目缺省值均在校验、过滤前转成注册的小写 ID；`A2` 与 `a2`、`A3` 与 `a3` 等价，输出及 receipt 中的平台值也使用小写。未知平台仍报错。
- task 自动规范为 `task.*` 并校验 task 维度。
- domain、route、platform、tag 和跨技术端点必须注册；Profile 必须受支持。
- 普通搜索必须有目标 platform，可显式传 `--platform`，或由 `CANNBOT_KNOWLEDGE_PLATFORM` 提供缺省值。`--technology platforms` 可在映射产品平台时不传；未定位 draft 使用 `--include-unlocated --status draft|all`，且不能同时传 platform。
- `--include-shared` 只与具体 technology 一起使用，并只附加同领域 shared。
- Search 当前不提供 CANN 版本过滤；版本字段仍可随命中返回，具体适用边界由正文核对。
- `text` 对 title、description、tags/aliases 和正文加权；`literal` 要求完整查询串出现在这些字段中，并按精确标题、标题片段、摘要、正文的顺序降权。普通正文链接与其他正文一起进入索引，不按专用关系块标记排除内容。
- `text` 和 `literal` 的 query 匹配均不区分大小写，同一 query 的大小写变体返回相同命中、评分与顺序，输出和 receipt 中的 query 仍保留调用方原文。v3 保持原有小写分词；subword 使用规范化名称读取索引中的原始名称写法，或通过已有词项的完整分解恢复驼峰拆词。所有仅靠词表分解得到的扩展都必须有连续拆开写法的证据；首选拆分缺少证据时继续检查其他可行候选，不因词表新增较长片段而丢弃已有证据的拆分。完整词未收录时也不能仅凭分散片段猜出新名称；真实名称拆词可直接复用。只有 `Data Copy Pad` 写法的卡片仍可被 `DataCopyPad`、`datacopypad`、`DATACOPYPAD` 的 text 查询召回；只有分散 `black` / `bird` 的卡片不会被 `blackbird` 猜拆召回。literal 不扩展拆开写法。该过程只读已有索引，不修改索引结构或版本。
- 默认 status 为 `stable`，limit 必须大于零。

### 领域选择与归属补查

`--domain` 和 `--technology` 精确筛选卡片的物理归属；它们不是意图路由或同义词扩展。`index.md` 的普通导航链接只帮助阅读，不参与搜索路由。不要仅因问题包含“图编译”就加 `--domain graph`，或仅因包含“软件环境”就加 `--domain common`。

Ascend 框架模型相关知识的规范位置如下，同一主题只维护一份卡：

| 查询主题 | 规范位置 |
|---|---|
| TorchNPU、TorchAir、OpPlugin 的模型接口、编译优化和框架配套 | `model/inference` 或 `model/training`，按任务与卡片职责选择 |
| TorchAir GE 编译缓存接口 | `model/inference/apis/torchair/ge_cache_compile` |
| Ascend 框架软件栈版本与固定来源基线 | `model/inference/concepts/frameworks/ascend_software_stack_baselines` |

`graph` 保留图技术本体和独立引擎知识，`common` 保留公共平台与工具链知识；不因相同主题词自动包含上述模型框架卡。具体覆盖仍用 `discover` 和真实命中核对，不把注册目录当作已有覆盖。

Agent 按以下顺序选择过滤：

1. 用户已明确限定领域或技术时保持该限制；查不到规范卡应说明范围内未命中，不自动跨域。
2. 只有主题意图、尚未确认卡片归属时，保留查询实体和目标平台，先不加 domain/technology。若先前加的是 Agent 自行推断的分类，且结果不足以回答，也可撤销这些推断另发查询；用户确认的其他条件及 Scope 语义不变，不借补查绕过错误。
3. 根据返回的路径确认归属，再带正确的 domain/technology 收窄并阅读全文。例如下述两个主题均可用 `--domain model --technology inference` 继续核对。没有证据时再按正常零命中流程补搜，不改变状态、平台或技术适用性。

以下以已确认 `a3` 为验收平台示范不预设领域的两条查询：

```bash
python3 <skill-dir>/scripts/knowledge_query.py --knowledge-root <repo> search \
  --query "torchair GE cache_compile" --type apis --platform a3 -k 5
python3 <skill-dir>/scripts/knowledge_query.py --knowledge-root <repo> search \
  --query "软件栈 TorchNPU 产品版本 安装包版本" --type concepts --platform a3 -k 5
```

显式增加 `--domain graph --technology torch_compile` 或 `--domain common --technology toolchains` 时，对应模型规范卡必须仍被排除；这是过滤契约，不是卡片缺失。回归 `ascend_community_cases.yaml` 分别保留受限查询的排除断言、上述不预设领域的命中断言，以及正确模型领域的原有命中用例。
### 可选中英双搜

`--alt-query` 提供可选双搜：调用方保留原查询并生成另一语言的简短改写，脚本以**完全相同的过滤条件与 Scope** 跑两趟完整文本检索，按各自名次交错融合（原查询优先：original #1、alt #1、original #2……；两趟都命中的卡片按路径去重，保留更早位次），不叠加两趟的原始分数。原查询第 r 名在融合后最多退到 2r-1，改写腿头部候选必进前二。

约束：仅支持 `--match text`，`literal` 精确标识符与错误码查询不得翻译改写；改写与原查询规范化后必须不同；改写中的 API 名、错误码、芯片型号、代码符号和数值应原样保留。改写由调用方（如 Agent）生成，脚本不联网、不翻译。

输出 schema 升级为 `knowledge-search.v6`（不带 `--alt-query` 时保持 v5，行为与请求指纹完全不变）：顶层新增 `alt_query` 与 `fusion`（融合方法、顺序与 `original_hits` / `alt_hits` 两腿命中数，改写腿零命中可直接从 `alt_hits: 0` 识别而非静默降级）；每个命中新增 `bilingual`（`original_rank` / `alt_rank` 及各自原始得分，未出现的腿为 null；`score_leg` 标注 `score` 取自哪一腿）。`rank` / `count` 为融合后语义，`score` 取名次更优一趟的原始得分；v6 的 `results` 按 `rank` 排序，`score` 不再保证与名次同序，调用方不得按 `score` 重排。Receipt 与请求指纹记录原查询、改写查询、各自名次与合并结果，重放使用同一契约。双搜按需启用、非默认流程；是否设为默认待独立评测（Issue #19）。

### 显式场景 Scope

`--scope-file` 读取 JSON/YAML 文件，`--scope-json` 接收同样结构的对象文本；两者互斥。输入是 Scope 对象本身，不再包一层 `scope`。显式提交表示调用方已核对条件；脚本仅做 Registry 别名归一化，不从自然语言推断执行模式、模型特征或数值阈值。

Scope 对卡片和查询均可选，可以只提交有依据的部分条件，不要求每个维度齐全。先按领域选择 Registry 的 namespace、适用范围与匹配类型；Query 共用 Contract 内的处理器，不在此解释领域特例。目前生产 Registry 仅有 `model.inference.v1`，下例的维度不适用于其他领域。新领域或新的匹配语义按[机器契约](../../../../governance/specs/schemas.md)扩展，不在查询文件中指定脚本或可执行判断。

```yaml
schema: model.inference.v1
any_of:
  - all_of:
      phase: [decode]
      objective: [tpot]
      model_features:
        all_of: [moe]
        none_of: [mla]
      parallelism:
        all_of: [tp]
        none_of: [cp]
```

上述查询表示已确认具备 MoE、不具备 MLA、启用 TP 且未启用 CP。`model_features.none_of` 仍只用于查询，不能写入卡片；`parallelism.none_of` 可用于有来源依据的卡片及显式确认的查询，不能把未提及的特征或并行方式自动补成否定。只声明 TP 不证明 CP 已关闭；未启用 CP 也不代表单卡。正反集合可同时声明，但至少一项非空且不得相交。

查询明确启用卡片禁止的并行方式，或明确关闭卡片必需的并行方式时为 `conflict`；缺少启用/关闭证据时为 `unknown`。未声明的并行否定、其他维度的否定权限不会自动扩展。`objective` 参与精确匹配，`latency` 不自动包含 `ttft` 或 `tpot`；有来源支持时，卡片显式列出多个目标。维度使用 Registry 的 `scope_schemas`，模型推理范围见 [Frontmatter](../../../../governance/specs/frontmatter.md)。卡片使用规范值，只有显式查询接受受控别名。

未提交 Scope 时保留原查询范围、评分、排序和请求结构。提交后，先在原过滤与文本候选内排除 `conflict`，保留 `match`、`unknown`，再取前 k；评分不加 Scope 权重，同分时匹配项优先，其余仍按原路径顺序。无 Scope 的旧卡片或其他已注册 namespace 的相关卡片为未知，未注册 schema 或非法条件报错，现有平台等前置条件保持不变。

结果新增 `scope_match`，包含三态 `state`、逐对的查询/卡片场景分支、枚举交集和缺失/冲突原因；文本输出将未知项标为“适用性待确认”。顶层 `scope_filter` 回显归一化条件、启用状态、冲突过滤计数和被过滤项原因。候选条件匹配不表示全文各分支均适用，正文与证据仍需核对。

Scope 条件绑定到请求指纹和 receipt，重放使用同一契约；旧 receipt 未带 Scope 时保持原语义。查询不会回写卡片或自动准备索引；Schema、Registry、Contract 变更后仍由维护者先准备匹配版本的索引。

### Receipt

`--receipt` 原子写入 schema、完整请求、canonical 请求指纹、知识仓状态、索引版本、语料/治理指纹、命中卡片指纹和原始结果。目标目录项必须不存在；已有文件、目录和符号链接（包括悬空链接）均拒绝，不沿目标链接创建其他文件。这一约定同时适用于 search、state 和 outcome receipt。审计流程的 `--decision` 使用稳定 ID，并把文件放在调用方实验目录。State 校验会重新计算请求指纹，要求每条 receipt 的平台集合与 state 目标完全相同，核对完整当前索引 provenance，并按原请求重放过滤、评分、排序和命中；ready receipt 绑定每个 search receipt 的文件 SHA-256，outcome 校验会再次确认这些文件未变化。

每个命中包含 rank、score、Concept ID、绝对 `local_path`、正文行数、OKF type、Profile、trust tier、范围、生命周期、卡片 SHA-256 及最多两个 source。顶层 `results` 是规范字段，`hits` 是迁移兼容别名。退出码 `0` 包括零命中；非法过滤、索引陈旧、知识根不可用或 receipt 已存在时退出码为 `2`。失败时同一结构化 error JSON 同时写入 stdout 和 stderr，便于管道消费方发现参数或索引错误。

`count` 仅表示本次返回的结果数，受 limit 限制；CLI 不返回全量匹配数。达到 limit 且目标定义仍未出现时，可扩大 k 或按问题细化，不能把前 k 项说成全部 API/全部调用者。

### Runtime 全平台候选扩展

`runtime-api-knowledge-query` 可显式使用 `--domain runtime --all-platforms`。
普通 Query 不带该选项时仍要求显式或项目缺省平台；其他领域不能使用该选项。
同一请求中，它与显式/项目缺省平台、`--include-unlocated` 均互斥。
Runtime Skill 在平台缺失或无法唯一解析为登记值、且没有项目缺省平台时，可在首次 API 查询直接使用该选项，
不要求先执行一次失败查询。未解析的产品描述保留为待确认信息，不作为 `--platform` 参数。
预先核对缺省平台时，先查看进程环境的 `CANNBOT_KNOWLEDGE_PLATFORM`；无值时再只读查看从当前目录向上
找到的最近 `.cannbot/knowledge.env` 中同名值；不执行配置文件。配置非法或不可读时报告错误，不静默忽略。

Runtime Skill 还可在准确接口名的目标平台查询成功、核验候选后仍未找到准确接口定义时，
独立去掉 `--platform`、改用 `--all-platforms` 复查一次，保持其他过滤条件。
空结果、仅前缀接口或正文提及均可能触发；返回已达 k 时先扩大 k 或细化再判断，stable 与 draft 一致。
已找到准确定义或查询报错时不触发。它只诊断接口收录与声明支持范围，
不改变原目标平台，也不把跨平台命中作为目标可用或“不支持”的充分证据。
若已有项目缺省值，删除参数仍会自动补入平台：仅此诊断子进程不继承
`CANNBOT_KNOWLEDGE_PLATFORM`，工作目录及其父目录均无 `.cannbot/knowledge.env` 配置文件，
用绝对脚本路径及 `--knowledge-root <同一绝对知识根>` 固定原知识与索引。不得修改配置文件、
父进程或全局环境；原配置非法、不可读等错误不能通过此上下文绕过。审计文件使用独立绝对路径。
随后如需未定位草稿，另发 `--include-unlocated --status draft` 查询，
不带 `--all-platforms` 或 `--platform`，不得把两种补搜合并成一个请求。

该模式召回支持任一登记平台的 Runtime 候选并集，保留原排序和其他过滤条件；
不包含空平台草稿。多个显式平台仍为 AND，默认 stable 不变。
请求及其 `filters` 同时记录 `all_platforms: true`，并纳入请求指纹和重放；
普通请求不新增该字段，历史有平台 receipt 保持兼容。
全平台候选请求的 `platforms` 为 `[]`，结果仍保留各卡的实际支持范围；
它不能证明用户芯片适用，也不能生成要求明确目标平台的 ready。
确认目标后，按该平台重新查询并保存新的 receipt。

## 审计工具

两个审计入口共用 `scripts/retrieval/root.py` 的 `Audit`、JSON 对象读取和非空字符串校验；路径要求、错误结构和拒绝覆盖语义保持一致。

冻结 `cannbot-retrieval-state.v1` 后校验 receipt、decision、当前索引和证据卡片，并只在全部 decision 为 `covered` 时生成 ready receipt：

```bash
python3 <skill-dir>/scripts/retrieval_state.py <absolute-state.json> \
  --knowledge-root <repo> --require-ready --receipt <new-ready.json>
```

工程验证结束后创建 `cannbot-retrieval-outcome.v1` manifest，绑定 state、ready receipt、每个 decision 的 outcome 与实验产物 SHA-256：

```bash
python3 <skill-dir>/scripts/retrieval_outcome.py <absolute-outcome.json> \
  --require-complete --receipt <new-outcome-receipt.json>
```

完整 state/outcome 形状与停止条件见[查询与证据工作流](query-workflows.md)。
