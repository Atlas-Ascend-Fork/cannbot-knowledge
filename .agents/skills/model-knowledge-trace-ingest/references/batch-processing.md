# 多轨迹批处理接口

所有脚本仅离线处理本地数据。模型调用、远端筛选/下载、并发、窗口会话和用量统计在外层。以下命令中的 `<SKILL_DIR>` 为同 checkout 的本 Skill；输出放 ignored `.build/`。

## 输入

已规范化目标轨迹可直接提供父目录，prepare 递归发现其中的 normalized_trace.jsonl。显式清单适合保留来源ID和family：

```json
{"schema_version":"model.trace-local-batch.v1","traces":[
  {"trace_id":"trace_a","source_family":"conversation_a","normalized_dir":"/absolute/normalized_a"},
  {"trace_id":"trace_b","source_family":"conversation_b","normalized_dir":"/absolute/normalized_b"}
]}
```

外层筛选工具也可输出 `model.trace-selected.v1`：screening.complete=true、unresolved=0，traces 中 selection.decision 必须为 target；未判定来源不能混入。local-batch/目录代表调用方明确提供的本地目标集合，不替代百万级远端筛选完成证明。

原始输入使用同一分组清单，把 normalized_dir 改为 path，format 为 auto、json、jsonl 或 text，可附带 data-processing.md 所述 mapping 对象和 layout: events|snapshots；或提供每个直接子目录代表一条目标轨迹的目录。多分片同一会话应在一个子目录中，不能把分片误当独立来源。

```bash
python3 <SKILL_DIR>/scripts/trace_batch.py normalize <raw-batch> --output <build>/normalized
python3 <SKILL_DIR>/scripts/trace_batch.py prepare <selected-list-or-normalized-parent> --output <build>/input
```

normalize 对清单中的目标逐一做确定性解析，没有模型调用；prepare 默认建立共享内容库和窗口，保留旧接口。大型输入优先使用以下引用模式，避免预生成尚不需要的全文窗口。

## 引用目录与有界证据

```bash
python3 <SKILL_DIR>/scripts/trace_batch.py prepare <selected-list-or-normalized-parent> --output <build>/input --references-only
```

此模式验证来源后只写 manifest.json 与 catalogue.json，不复制全文、不生成 SQLite 或 packets。catalogue 提供事件类型计数和开头/结尾各至多三条用户消息预览，带原字符数、截断标记及未列出的用户事件数。它是定位工具，不能据此判定知识已提取、无知识或完整范围；预览不足则补读，不能把标题或关键词命中当模型场景证据。

围绕候选选择多个事件，一次准备相邻上下文及显式 call id 对应的调用/返回：

```json
[{"trace_id":"trace_a","sequences":[12,18]},{"trace_id":"trace_b","sequences":[7]}]
```

```bash
python3 <SKILL_DIR>/scripts/batch_exchange.py evidence <build>/input --selection <work>/selection.json --output <new-evidence-dir> --max-bytes 24000 --context 1
```

`evidence.json` 记录来源、页路径/hash/字节、请求和实际包含事件、未供给区间。page_*.json 保持原角色、provenance、序号和准确字符 offset；长事件逐页完整保留，text_parts 顺序连接还原文本。每页实际 UTF-8 JSON 字节不超过 max-bytes（4096–524288，默认24000），context 是邻近事件半径（0–10）。自动邻近上下文排除未请求的 system_message/reasoning，错误与未知事件保留；显式请求仍可读取这些上下文。源码单元若跨页，读齐后才能引用。

证据包可含多来源；选择事件不等于逐轨迹建立模型任务。客户端有工具响应上限时将页预算调到可完整返回的范围；能直接供给文件内容时可增大预算。只给路径然后反复短读会增加开销。供给区间不等于语义已读，实际阅读范围由执行 Agent 记录；未提供区间不能推断没有有用知识。事件 reader 在两种 prepare 模式均可用。

## 连续事件阅读视图

模型优先读取连续的开发事件，不直接解码交错存储分块。

```bash
python3 <SKILL_DIR>/scripts/batch_exchange.py view <batch-dir> --output <new-view-dir>
```

reading.txt按来源/原始序号连续呈现完整正文，保留actor、event_type、tool和timestamp，不切碎长文本或加入hash文本引用。view.json保留完整来源hash、事件元数据、included_sequences和context_only_sequences。只把system_message与历史reasoning单列旁证；system:error、unknown和所有开发消息/工具结果继续供给。默认阅读视图最多512KiB，超限拒绝，不静默截断。此入口适合能装入一个有界上下文的目标小批；大型粗批仍由外层分窗口。

原始规范化数据和存储包不变；如需旁证可按原sequence补读。不能将旁证省略量称为无损全文压缩，也不能把准备好的视图算作语义阅读完成。调用方可采用[file-bundle输出](file-bundle.md)，外层展开标准产物、记录字段适配并离线校验。

## 数据窗口

内容库全局去重；模型数据窗口按窗口去重，跨窗口必要的文本会重复提供，以便新的有限上下文会话直接读取。stats.unique_characters/duplicate_characters 是内容库统计；packet_text_characters/shared_within_packets_characters 才是窗口实际文本量/共享量，均不是实际模型token。

默认窗口最多262144个UTF-8字节；用 prepare --packet-bytes 调整。按来源的事件/文本序号交错排布，窗口可同时包含多条轨迹。每条来源内部的顺序、角色、工具和 provenance 保留；跨来源不宣称全局时间顺序。

- `manifest.json`：`model.trace-batch.v1`，sources、packets（路径/hash/字节/成员）及统计。
- `content.sqlite3`：去重文本、事件位置与原始元数据。数据库hash绑定在批清单。
- `packets/packet_*.json`：历史数据，不含调用模型的prompt。event记录含来源与元数据；text记录含准确区间及content_sha256，每个窗口内首次出现提供text_parts，同窗重复出现给text_ref。

每个窗口的文本引用自包含，不依赖旧会话的原文缓存；同窗每个hash只需阅读一次文本，但所有事件出现位置和角色都要看；actor不同不能因文本相同而共用证据等级。同family的多版本不增加独立复现。

外层把完整窗口字节作为输入文本供给当前执行 Agent，并保存实际输入与响应记录；若只能工具读文件，使用有界证据页或先调小窗口，并核对截断。默认262144字节是存储预算，不能假设客户端一次能完整返回。

```bash
python3 <SKILL_DIR>/scripts/trace_batch.py packet <build>/input --number 1
python3 <SKILL_DIR>/scripts/trace_batch.py event <build>/input --trace-id trace_a --sequence 12 --offset 0 --characters 12000
```

packet 读取绑定hash的原数据窗口；event 为精准补证，返回原角色、provenance和逐字文本页。二者均不执行命令、不请求模型、不自动声称已读。

当一个批次超过上下文时，外层按窗口消费，用有限上下文保存候选增量、source/sequence锚点和未决项。换窗口时携带跨窗未闭合事件的角色、工具、provenance 与准确偏移等有界状态；可以换窗口会话，不能反复压缩/回放整个来源，也不能为每条轨迹建立Task。大轨迹可跨窗口，不能悄悄截断；最终报告实际未读区间。

## 批级产物

沿用 model.trace-mining.v1 候选结构；顶层 sources 可包含多个真实来源，候选用本批顶层来源索引或来源对象引用，候选内锚点仍相对于该候选的来源数组。跨两来源的同根因可写一份候选草稿，并在 source arrays 中保留两者；不能只改文字却丢失来源。

```bash
python3 <SKILL_DIR>/scripts/trace_batch.py report-template <build>/input
python3 <SKILL_DIR>/scripts/trace_batch.py check <build>/input --report <work>/batch-report.json --candidates-manifest <work>/manifest.json
```

report-template 只生成pending骨架，不生产知识或完成状态。Agent填写：

```json
{"schema_version":"model.trace-batch-report.v1","batch_manifest_sha256":"实际hash","traces":[
  {"trace_id":"trace_a","disposition":"mined","candidate_ids":["c1"],"reason":""},
  {"trace_id":"trace_b","disposition":"mined","candidate_ids":["c1"],"reason":"与a合并为同根因，来源保留"}
]}
```

同一跨来源候选可出现在两个来源的去向中，候选本身只定义一次。无候选用no_knowledge/out_of_scope并给理由；缺数据或仍未完成用deferred并给缺口。新报告的 deferred 附 `deferred_stage: unread|missing_evidence|needs_review`，区分未读、已读但缺证和待审；旧报告缺省计为 unspecified，不能谎报完成。check拒绝漏项、重复、pending、外来来源、旧hash、草稿逃逸与同family虚增复现；它核对声明与绑定，不证明Agent真实阅读或语义正确。

进入curate后，每个route的ledger增加如下私有绑定，继续使用证据校验与策展流程：

```json
{"batch_manifest":{"path":"/absolute/input/manifest.json","sha256":"实际批清单hash"}}
```

模型证据validator自动核对该绑定、来源成员与family复现上限；默认旧单来源输入仍可用。冻结subject涵盖最终ledger，不在通过后修改绑定。

## 批级收口

先对整批候选按机制预聚类，再按route策展。对每个问题簇一次Query、读取近邻全文；只有新增问题、范围变化或证据冲突才扩查。同一实际查询可支撑多个候选，但各去向、增量和来源均须保留。

拒绝/暂缓稿移出staged-cards，原始挖掘记录保留。全批的批级check、模型证据校验、真正独立审查和发布各自独立，不能互相替代；零产出也要给出逐来源去向。

续跑只携带候选索引、已读范围、原文锚点、问题与去向，避免回放整个来源。调用方若再分批，按规范化字符量和候选机制估算负载，不按来源条数平均；任务说明引用同一范围合同，保持中性，不预填目标结论。实际模型/缓存 token 和费用由外层统计，目录字节与离线页数不能换算成已节约 token。
