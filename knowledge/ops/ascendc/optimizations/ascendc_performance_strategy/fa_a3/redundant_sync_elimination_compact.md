---
type: Optimization
title: AscendC 核内冗余同步识别与受证据约束的安全删减
description: 识别 AscendC 核内冗余同步，并在证据约束下安全删减。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/07-redundant-sync-elimination-compact.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：AscendC 核内冗余同步识别与受证据约束的安全删减

> **版本：2.2-compact**
> **单一优化点：** 在不改变数学公式、tiling、buffer 布局、queue 配置、跨核协议、输出格式和其他性能点的前提下，识别 AscendC kernel 中重复、低价值或已有等价顺序保证的核内同步，并删除满足静态证明、编译证据、动态正确性和性能门禁的最小同步子集。
> **核心原则：** 不是“尽量删同步”，而是“删除后所有冲突访问仍有可靠 happens-before 路径”。

---

## 0. 决策状态与硬规则

| 状态 | 含义 | 是否允许删除 |
|---|---|---|
| `KEEP` | 已确认承担必要顺序或资源生命周期职责 | 否 |
| `CANDIDATE` | 已找到替代 happens-before 路径，可进入实验 | 可以 |
| `UNKNOWN` | wrapper、地址别名、编译配置、生命周期或官方版本信息不足 | 否 |
| `OUT_OF_SCOPE` | 跨核、AIC/AIV 协议，或需要改变 queue/buffer/tiling/算法结构 | 否 |

硬规则：

```text
UNKNOWN => KEEP
OUT_OF_SCOPE => KEEP
accuracy PASS != safety proof
performance gain != correctness proof
source diff shorter != machine-code faster
rg sync hit missing from sync table => STOP
DataCopy -> EnQue -> DeQue -> SetWaitFlag is a TQue path, not a bare TBuf path
```

约束词：**必须**表示不满足即禁止实施或保留；**禁止**表示不得由本策略修改；**应当**表示默认执行；**可以**表示满足前置条件后进入实验，不代表安全。

---

## 1. 官方语义与版本边界

1. AI Core 内 Scalar、Vector、Cube、MTE 等流水可异步并行；同流水或不同流水访问冲突存储区域时，必须建立顺序。
2. `PipeBarrier<PIPE_xxx>()` 是同一流水内同步；`PIPE_ALL` 会扩大阻塞面；禁止调用 `PipeBarrier<PIPE_S>()`，Scalar 流水同步由硬件保证，该调用可能引发硬件错误。
3. `PIPE_V` 在满足自动同步条件时可由编译器插入，但不能只凭“工程默认开启 auto-sync”删除手写 barrier。
4. `PIPE_MTE2`、`PIPE_MTE3` 在搬运目的地址重叠、跨迭代复用或生命周期不明时可能仍需手写 barrier。
5. ISASI `SetFlag/WaitFlag` 用于同一核内不同流水同步，必须成对使用；`HardEvent` 命名为“源流水_目标流水”，如 `MTE2_V` 表示 V 等待 MTE2。
6. TPipe/TQue 编程模式下，event ID 必须通过 `AllocEventID` 或 `FetchEventID` 获取；`AllocEventID` 必须与 `ReleaseEventID` 配对；`FetchEventID` 不占用 ID，连续或复杂场景复用相同 ID 可能导致卡死或未定义行为，应检查是否应改用 `AllocEventID`。
7. Static Tensor 编程模式下事件 ID 管理规则不同；除非项目已有独立完整规则，否则相关同步点标记为 `UNKNOWN`。
8. `TQueSync` 也是官方同步体系的一部分，需与 ISASI `SetFlag/WaitFlag` 分开记录；应检查 `TQueSync<src,dst>` 的源/目标流水模板参数、对象生命周期和跨硬件版本兼容要求。
9. `TQue/TQueBind` 可表达流水任务间通信、同步和资源管理；queue depth 必须覆盖连续 `EnQue` 而未 `DeQue` 的最大次数；只看到 `TPipe/TQue` 声明不能证明某条路径已同步。
10. `TBuf` 只管理临时内存，不能执行 queue 入队/出队，不能把其他 queue 的同步语义套用到裸 `TBuf` 或裸 `LocalTensor` 路径。
11. 自动同步应通过 `-g --cce-auto-sync-log=<file>` 验证；依赖自动同步必须同时满足：相关函数为 `__aicore__ inline`、规范使用 AscendC 编程模型、编译器能识别 `LocalTensor` 生产/消费/别名、log 明确显示删除后仍插入所需等价同步或官方规则明确保证。
12. `SetWaitFlag`、`ConsumerAcquire` 等项目封装不是默认官方 API；遇到 wrapper、宏、模板或条件编译，必须定位定义、展开真实 `PipeBarrier/SetFlag/WaitFlag/TQueSync` 语义、记录 event ID 与生命周期；无法展开即 `UNKNOWN`。若 wrapper 形如 `SetWaitFlag<HardEvent::X_Y>()`，分析时必须按 `FetchEventID(X_Y) + SetFlag<X_Y>() + WaitFlag<X_Y>()` 展开，不得把它当作单个黑盒函数。
13. 官方 API 支持范围、自动同步行为、event ID 数量和硬件兼容性必须以项目实际 CANN、编译器、SoC、核类型和编译选项为准，不得跨版本泛化。

---

## 2. 适用范围与停止条件

适用条件必须同时满足：kernel 中存在可定位的 `PipeBarrier`、`SetFlag/WaitFlag`、`TQueSync` 或项目同步 wrapper；基线可稳定构建且全量精度稳定通过；有固定可重复的精度和性能命令；本轮只删除核内同步及已无用途的事件资源代码；能记录 CANN、编译器、SoC、核类型、auto-sync 和关键编译选项。

禁止范围：跨核同步、GM flag、workspace acquire/release、核间协议；AIC/AIV、Cube/Vector 之间的项目级生产消费协议；需要新增或重构 TQue/TQueBind 才能成立的同步替换；tiling、tile 大小、queue depth、double buffer、UB/L1/L0 布局、tensor 地址、数据类型、数学公式、舍入模式、输出格式或其他性能点修改。

出现以下任一情况即停止：基线精度不稳定；无法运行精度测试；基线有随机 hang、异常或未解释 mismatch；目标平台/编译配置不明确；已有 queue 生命周期错误、event ID 冲突、跨核竞争或 workspace 协议问题未排查。

说明：把裸 `TBuf` 路径改为 queue 路径可能是有效独立优化，但不属于“只删除同步”的本策略。

---

## 3. 安全删除的形式化条件

### 3.1 访问记录与分层地址证明

对同步点前后相关指令，至少记录：`api`、`pipe`、`memory_space(UB/L1/L0/GM/workspace/queue_slot)`、`tensor`、`base_object`、`access(READ/WRITE/READ_WRITE)`、`address_range`、`iteration(current/previous/next/unknown)`、`queue`。

地址证明分层：

| 层级 | 条件 | 处理 |
|---|---|---|
| L1 | 不同且不可别名的基础对象 | 可证明不重叠 |
| L2 | 同一基础对象但固定 offset/length | 建立符号区间 |
| L3 | 动态 offset、复杂 stride、repeat、mask、尾块、高阶 API | 查 API/展开 wrapper，计算保守包围区间 |
| L4 | 仍无法确定 | `UNKNOWN => KEEP` |

地址区间必须考虑 `LocalTensor` 切片、下标偏移、`ReinterpretCast`、数据类型字节数、同一 `TBuf/queue slot/base address` 派生 tensor、mask/stride/repeat/尾块/对齐、当前与相邻迭代 buffer 复用。

### 3.2 冲突与资源依赖

必须检查：`RAW` 前写后读、`WAR` 前读后写、`WAW` 前写后写、跨循环迭代 RAW/WAR/WAW、queue slot/event ID/临时 buffer/workspace 等资源生命周期冲突。

### 3.3 happens-before 删除判据

对同步点 `S`：

```text
只有当删除 S 后，所有访问重叠地址或共享资源的冲突操作对，
仍存在可靠 happens-before 路径时，S 才能标记为 CANDIDATE。
```

可接受替代路径仅包括：auto-sync log 证明的编译器等价同步；与实际 tensor 通路匹配的 `TQue/TQueBind/TQueSync` 生产消费边；另一组仍保留的显式同步；对当前硬件和 CANN 版本有官方依据的顺序保证。

不能作为证明：代码长期如此、小 shape 通过、删后性能更快、存在 `TQue/TPipe` 对象、工程默认开启 auto-sync、变量名不同、只失败概率低、同步点位于函数入口。

### 3.4 动态测试地位

动态测试用于发现错误，不能证明 race 不存在。最终保留同步删减必须同时满足：静态依赖证明 PASS；编译或框架同步证据 PASS；构建与静态资源检查 PASS；全量、边界、压力和重复精度 PASS；性能收益超过噪声。

---

## 4. LLM 强制预分析流程

在输出完整同步清单前，禁止修改源码。

优先执行或等价执行：

```bash
rg -n 'SetWaitFlag|SetFlag|WaitFlag|PipeBarrier|TQueSync' <kernel-dir>
rg -n 'AllocEventID|FetchEventID|ReleaseEventID' <kernel-dir>
rg -n 'AllocTensor|EnQue|DeQue|FreeTensor|TQueBind|TQue|TBuf' <kernel-dir>
rg -n 'CrossCoreSetFlag|CrossCoreWaitFlag|CrossCore|SyncAll|IBSet|IBWait|workspace|Acquire|Release' <kernel-dir>
```

同步清单覆盖门禁：

```text
任何命中 SetWaitFlag、SetFlag、WaitFlag、PipeBarrier、TQueSync 的位置都必须进入同步点清单。
若 rg 命中数与同步点清单数量不一致，禁止进入代码修改阶段；必须补齐清单或说明重复命中的合并依据。
直接命中 SetFlag/WaitFlag 和命中 SetWaitFlag wrapper 的点同等重要，均需记录真实 HardEvent。
```

wrapper 解析要求：定位宏/模板/函数定义；展开内部同步；记录 event ID 来源、生命周期和调用路径；条件编译需按目标 SoC 实际分支分析；无法解析即 `UNKNOWN`。`SetWaitFlag<HardEvent::X_Y>()` 必须展开为 `FetchEventID(X_Y) + SetFlag<X_Y>() + WaitFlag<X_Y>()`，同步点表中记录为 `ISASI_SetWaitFlag`，并注明 event ID 来源为 `FetchEventID`。

TQue 路径自检问题（实施前必须逐条回答）：

```text
是否存在 DataCopy -> EnQue -> DeQue -> SetWaitFlag 的模式？
若存在，消费者读取的是否是同一 queue DeQue 后的 tensor？
若是同一 queue 完整交接，为什么 SetWaitFlag 不是 CANDIDATE？
是否存在 chunk 尾部 MTE3_MTE2，下一轮 MTE2 访问不同 queue/不同地址，而跨核发布由 loop 外 Release 承担？
```

环境记录必须包含：

```yaml
cann_version: ...
compiler_version: ...
soc_or_npu_arch: ...
core_type: AIC | AIV | AI_CORE | ...
auto_sync_enabled: true | false | unknown
auto_sync_log_enabled: true | false
optimization_level: O0 | O2 | O3 | ...
source_revision: git commit or diff base
```

同步点记录格式：

```yaml
id: S1
location: path/file.cpp:123
syntax: TQueSync | ISASI_SetWaitFlag | PipeBarrier | project_wrapper
kind: MTE2_V | V_MTE3 | PIPE_V | PIPE_MTE2 | ...
scope: function_entry | loop_body | loop_tail | function_exit
execution_count: symbolic expression or unknown
producer: {api: DataCopy, pipe: MTE2, tensor: inputUb, access: WRITE, address_range: ...}
consumer: {api: RowMuls, pipe: V, tensor: inputUb, access: READ, address_range: ...}
hazard: RAW | WAR | WAW | RESOURCE | NONE | UNKNOWN
loop_carried: true | false | unknown
queue_path: {queue: none, alloc_enque_deque_free_complete: false}
alternative_happens_before: none | auto_sync | queue | tque_sync | other_sync | hardware
compiler_evidence: auto-sync-log line or none
event_id: {source: AllocEventID | FetchEventID | static | wrapper | none, release: location or none}
decision: KEEP | CANDIDATE | UNKNOWN | OUT_OF_SCOPE
reason: one concise, testable statement
```

---

## 5. 同步分类与决策规则

### 5.1 `PIPE_V`

标记 `KEEP`：存在 V 流水 RAW/WAR/WAW 且无已证明替代同步；wrapper/高阶 API 内部范围无法展开；相关函数非 `inline`；未规范使用 AscendC 编程模型；auto-sync 关闭/未知；tensor 别名、切片、临时 buffer 复用不明。

标记 `CANDIDATE`：A. 前后实际访问区间完全不重叠且无跨迭代复用；或 B. 存在依赖但 auto-sync 开启、调用链满足 `inline` 和编程模型约束、auto-sync log 显示删除后仍插入等价 `PIPE_V`、无编译器无法识别的别名或 wrapper。注意：B 通常是源码清理候选，不是性能优先候选；若机器码补回同一同步，不得因源码更短保留。

### 5.2 `PIPE_MTE2` / `PIPE_MTE3`

标记 `KEEP`：同一搬运流水前后目的地址重叠；跨迭代复用同一目的区域；地址范围无法确定；承担 queue slot 或 DMA 生命周期保护。标记 `CANDIDATE`：完整实际目的地址区间不重叠、无跨迭代/尾块别名、无资源生命周期职责。

### 5.2a `PIPE_M`（矩阵累加；原 11-first-accumulate-barrier-elision 已并入）

矩阵 reduce 循环的常见结构：

```cpp
for (uint32_t k = 0; k < kTiles; ++k) {
    mmadParams.cmatrixInitVal = (k == 0);
    PipeBarrier<PIPE_M>();
    Mmad(c, a, b, mmadParams);
}
```

判定规则：

```text
if barrier 位于"新输出 tile 的首次 MMAD"之前，且该 MMAD 使用 cmatrixInitVal=true（初始化语义）:
    candidate      # 同一输出 tile 无前序 MMAD 结果需要等待 → 不承担 RAW/WAW 职责（§3.3 判据实例）
else:
    keep
```

如果无法证明"freshly initialized output tile"，必须保留。改写模板：

```cpp
bool firstReduce = true;
for (uint32_t k = 0; k < kTiles; ++k) {
    if (!firstReduce) {
        PipeBarrier<PIPE_M>();
    }
    Mmad(c, a, b, firstReduce);      // cmatrixInitVal = firstReduce
    firstReduce = false;
}
```

`firstReduce` 作用域规则（多层 reduce 轴）：若 reduce loop 有多层（如 `kL1` 外层、`kL0` 内层），`firstReduce` 必须声明在**完整 reduce 轴之外**并覆盖全部迭代，不能错误重置在内层 loop——否则跨 L1 tile 的累加缺少 barrier。特例：`kTiles == 1` 的路径整个 reduce loop 不再执行任何 `PIPE_M`（每个输出 tile 删除 1 个无效首 barrier，此路径收益全部兑现）。

标记 `KEEP`（不可删）：barrier 位于两个实际相关 MMAD 之间；首次 MMAD 没有初始化输出而是累加到已有 L0C；L0C 被跨函数/跨 loop 复用，首个 MMAD 仍需等待前一使用者；barrier 实际保护的是 L0C/Fixpipe/MTE 之间的生命周期而非 MMAD 间顺序。

优先适用：reduce tile 数经常为 1；每个 task 有多个输出 micro tiles、每个 micro tile 都执行一次无效首 barrier；profiling 显示 AIC scalar 或 Cube stall 中同步开销可见。

禁止：不要删除第二次及之后累加前的 `PIPE_M`（除非有独立同步证明）；不要把 `firstReduce` 错误重置在内层 loop；不要改变 `cmatrixInitVal`/清零逻辑/累加顺序；不要把本规则扩展到 `PIPE_V`/`PIPE_MTE2`/`PIPE_MTE3`（各自独立证明）。

验收补充：覆盖 `kTiles == 1`、`kTiles > 1`、reduce tail、M/N tail、不同 dtype；记录 `removed_pipe_m_count_per_task`、`kTiles distribution`、`Cube FOPs`（不变）、`AIC scalar time`（不增）。若性能无变化但精度稳定，可保留为源码级同步清理；若性能回退则回滚。

### 5.3 `MTE2_V`

裸 `TBuf/LocalTensor` 搬入后给 V 直接读取时标记 `KEEP`：

```cpp
DataCopy(local, global, n); SetFlag/WaitFlag(MTE2_V); VectorCompute(local);
```

但以下模式不得按裸 `TBuf` 路径处理：

```cpp
DataCopy(xUb, gmOrWorkspace, n);
queue.EnQue(xUb);
xUb = queue.DeQue<T>();
SetWaitFlag<HardEvent::MTE2_V>();
VectorCompute(xUb);
```

若 `EnQue/DeQue` 是同一 `TQue`，`AllocTensor/EnQue/DeQue/FreeTensor` 生命周期完整，消费者读取的是 `DeQue` 后的同一 tensor，且没有绕过 queue 访问同一基础 buffer，则该 `MTE2_V` 必须标记为 `CANDIDATE`，理由为 `queue handoff covers MTE2->V`。`TQue` 管理的 `DataCopy -> EnQue -> DeQue` 数据通路已经提供生产者到消费者的同步；当后续紧接消费者使用同一 `DeQue` tensor 时，不应再额外插入同方向 `SetWaitFlag`。只有 queue 路径不完整、tensor 绕过 queue、depth 不足、原地复用不明或 wrapper 无法展开时，才允许标记 `KEEP/UNKNOWN`。

### 5.4 `V_MTE3`

裸 `LocalTensor/TBuf` 的 V 结果被 MTE3 直接搬出时标记 `KEEP`：

```cpp
VectorCompute(outUb); SetFlag/WaitFlag(V_MTE3); DataCopy(outGm, outUb, n);
```

若必须通过新增 queue 才能删除，标记 `OUT_OF_SCOPE`。

### 5.5 `MTE3_MTE2` / `MTE2_MTE3`

检查前后搬运是否访问或复用同一 UB/GM 地址；下一迭代是否复用前一迭代尚未完成搬出的 queue slot；`FreeTensor` 后内存是否可能在 DMA 完成前重新分配；事件是否属于跨 stage、AIC/AIV 或跨核协议。循环尾部只表示收益/风险都可能较高，不能替代依赖判断。

热循环 chunk 尾部的专门判定：

```cpp
DataCopy(producerWorkspaceSlot[...], outUb, n);
outputQue.FreeTensor(outUb);
inputQue.FreeTensor(inUb);
SetWaitFlag<HardEvent::MTE3_MTE2>();
// next iteration: DataCopy(nextInUb, unrelatedWorkspaceSlot[...], n2)
```

若前一条 MTE3 写入的 GM/workspace slot 与下一轮 MTE2 读取的 GM/workspace slot 不同，UB queue 也不同或已由各自 `TQue` 生命周期管理，且跨核/跨 stage 的发布由 loop 外 `ProducerRelease*`、`CrossCoreSetFlag` 或保留的协议同步承担，则该 chunk 尾部 `MTE3_MTE2` 必须标记为 `CANDIDATE`。若它保护的是同一 queue slot 复用、同一 UB 地址复用、`FreeTensor` 后立即重分配给 MTE2、或承担跨核可见性发布，则标记 `KEEP/OUT_OF_SCOPE`。

### 5.6 Scalar 相关事件

遇到 `V_S/S_V/MTE2_S/S_MTE3` 等事件，检查 `GetValue/SetValue` 与 Vector/MTE 访问顺序、标量值是否决定循环边界/地址/mask/搬运参数、auto-sync 是否覆盖当前通路。禁止因“Scalar 流水由硬件保证”删除跨流水事件；该保证只意味着不能调用 `PIPE_S`。

### 5.7 `TQue/TQueBind/TQueSync`

queue 或 `TQueSync` 只能为其实际路径提供证据。必须确认：producer 写入后 `EnQue/SetFlag`；consumer 使用同一 queue 的 `DeQue/WaitFlag`；`TPosition` 或 `TQueSync<src,dst>` 与实际流水一致；`AllocTensor/EnQue/DeQue/FreeTensor` 生命周期完整；depth 覆盖连续入队；没有路径绕过 queue 访问同一基础 buffer；原地操作和 depth 配置符合官方约束。

强制分类规则：只要同步点前后存在同一 tensor 的 `DataCopy -> EnQue -> DeQue -> Vector` 或 `Vector -> EnQue -> DeQue -> DataCopy` 通路，必须优先按 TQue 路径分析，不得直接套用裸 `TBuf/LocalTensor` 默认保留规则。若最终不是 `CANDIDATE`，同步点表必须写明 queue 证据失败的具体原因。

### 5.8 项目协议与跨核同步

出现 `CrossCore*`、`SyncAll`、`IBSet/IBWait`、GM/workspace flag、AIC/AIV slot/state/workspace 交接，或同步 wrapper 同时包含核间/跨 stage 协议，标记 `OUT_OF_SCOPE`。

---

## 6. 候选优先级与默认保留

优先分析顺序：1. 完整 `TQue/TQueBind/TQueSync` 交接后重复出现的同方向事件，尤其是 `DataCopy -> EnQue -> DeQue -> SetWaitFlag -> Vector`；2. 热循环 `loop_body` / `chunk_tail` 中动态执行次数高、profiling 显示造成 stall 的已证明候选；3. 静态证明无冲突依赖且删除后机器码同步数量减少的同步点；4. 前后实际地址完全不重叠且无跨迭代复用的 barrier；5. auto-sync log 补回等价同步的手写 `PIPE_V`，仅作为源码清理候选，不作为性能优先项。

动态执行优先级硬规则：

```text
loop_body sync > chunk_tail sync > loop_entry sync > function_entry sync
```

每个同步点必须填写 `execution_count` 或符号表达式。函数入口同步通常收益小，只有当所有热循环 TQue 覆盖同步和 chunk 尾同步都完成判定后，才允许作为首轮删除集合的主体。

默认保留：裸 `TBuf` MTE2→V；裸 `LocalTensor/TBuf` V→MTE3；地址重叠的 `PIPE_MTE2/PIPE_MTE3`；event 配对、ID 生命周期、`TQueSync` 对象或 wrapper 语义不明；跨迭代 buffer/queue slot 复用保护；跨核、AIC/AIV、workspace 协议同步。

收益估计：

```text
estimated_benefit ≈ dynamic_execution_count × stall_cost × overlap_opportunity
```

函数入口同步通常收益小，热循环同步通常收益大但风险也可能大；正确性只能由依赖图决定，不能由频率、位置或性能结果决定。禁止只删除低频入口同步后就判定策略无效；若热循环候选未处理，结论只能是“实施不完整”。

---

## 7. 实施流程与门禁

### 7.1 基线

记录并执行：

```bash
git status --short
git diff -- <target-files>
cmake --build <kernel-build-dir>
ASCENDC_SKIP_BUILD=1 bash scripts/evaluate_ascendc.sh <task> all
```

同时记录 source revision、CANN、编译器、SoC、核类型、编译选项、精度命令、case 集合、随机种子、重复次数、性能命令、warm-up、采样次数、设备状态、基线中位数和波动。基线不稳定即停止。

### 7.2 清单、编译证据与删除集合

完成第 4 节同步清单，禁止使用“可能没用/看起来重复/应该由编译器处理/删掉试试”等无证据结论。同步清单必须覆盖 `rg` 命中的全部 `SetWaitFlag/SetFlag/WaitFlag/PipeBarrier/TQueSync`；未覆盖时禁止修改源码。项目支持时开启并比较 baseline 与 candidate 的 `--cce-auto-sync-log`，核对同步类型和源码位置；若删除后无所需等价同步，候选退回 `KEEP/UNKNOWN`。删除集合按职责分组：queue 交接后重复事件、热循环 chunk 尾地址不重叠事件、机器码同步减少候选、其他静态证明候选；跨核或 queue 重构同步不得进入集合。

首轮删除集合应优先覆盖同一职责的一组热路径冗余同步。例如同一 vector loop 中 `TQue` 已覆盖的 `MTE2_V` 与不承担跨核发布的 chunk 尾 `MTE3_MTE2` 可以组成一个 delete_set；禁止只选低频 function_entry fence 作为首轮主实验，除非同步清单证明不存在热路径候选。

### 7.3 单变量实验

定义：

```text
test(delete_set):
  从同一 baseline 还原源码；只删除 delete_set 中同步点；
  清理因此失去用途的 event ID 代码；build；
  检查 auto-sync log、Set/Wait、event ID、queue 生命周期；
  run accuracy；accuracy PASS 后 run performance。
```

每轮只允许“删除集合”变化，禁止夹带其他源码修改。

### 7.4 资源与构建门禁

删除 `SetFlag/WaitFlag/TQueSync` 后检查：Set/Wait 是否成对；`AllocEventID` 是否仍有用途，无用途时连同匹配 `ReleaseEventID` 删除；不得删除仍被其他同步使用的 event ID；`FetchEventID` 返回值是否仍被引用；wrapper 内是否有隐式配对或共享 ID；目标 kernel 与所有目标 SoC/核类型分支构建通过；无 event ID 未使用、未释放、重复释放、孤立 Set/Wait、queue 生命周期和 depth 变化；diff 只包含允许范围。

### 7.5 正确性门禁

至少执行：固定全量精度集；最大循环次数、长序列、大 batch、多 block 压力 case；首块、尾块、非对齐尾块、最小 shape；易触发 buffer 复用的多 chunk case；同一高风险 case 多次重复以检测非确定性 race。

任意 mismatch、hang、随机失败、NaN/Inf、p99/p99.9 异常均为 `FAIL`；禁止接受“仅一个大 case 失败”“mismatch 很低”“p50 正常但 p99 异常”“多跑几次大部分通过”。

### 7.6 性能门禁

相同环境、输入、构建模式、设备状态；至少 3 次 warm-up；baseline/candidate 各不少于 10 个有效样本；尽量交错运行；以中位数为主，记录均值、MAD 或波动指标。

```text
gain = (median_baseline - median_candidate) / median_baseline
noise = max(MAD_baseline / median_baseline, MAD_candidate / median_candidate)
keep only if gain > max(project_min_gain, 3 × noise)
```

项目已有更严格统计规范时以项目规范为准。若编译器补回同一同步，不得仅因源码更短保留。

---

## 8. 组合失败定位：三态 delta debugging

`test(X)` 必须从同一 baseline 出发，只删除集合 `X`。返回三态：`PASS`、`FAIL`、`FLAKY`。高风险 case 运行 N 次：0 次失败为 `PASS`；达到失败阈值 K 为 `FAIL`；介于两者之间为 `FLAKY`。`FLAKY` 不得当作 PASS；应扩大重复次数或按 FAIL 保守处理。

```text
function ddmin(failing_set):
  current = failing_set; n = 2
  while size(current) >= 2:
    subsets = partition(current, n); reduced = false
    for part in subsets:
      if test(part) in {FAIL, FLAKY}: current=part; n=max(2,n-1); reduced=true; break
    if reduced: continue
    for part in subsets:
      comp = current - part
      if comp != empty and test(comp) in {FAIL, FLAKY}: current=comp; n=max(2,n-1); reduced=true; break
    if reduced: continue
    if n == size(current): break
    n = min(size(current), n*2)
  return current
```

得到失败集合 `F` 后验证：`test(F)`、`test({Si}) for Si in F`、`test(F-{Si}) for Si in F`。结论：单点失败则该点 `KEEP`；单点均过但组合失败则记录组合依赖并禁止同时删除；失败不可重复则按非确定性 race 处理，不得保留。

---

## 9. 常见失败信号与优先排查

| 信号 | 优先排查 |
|---|---|
| 仅大 case / 多 chunk 失败 | 跨迭代 RAW/WAR/WAW、chunk 尾部 buffer/queue slot 复用、workspace/online state 提前读写、depth 不足 |
| 大面积 mismatch | 裸 MTE2→V、裸 V→MTE3、无替代同步的 V 流水依赖、wrapper 实际访问范围不一致 |
| 随机失败 / 偶现误差 | event ID 复用、Set/Wait 配对错误、DMA 完成前复用 Local Memory、auto-sync 条件在部分模板或条件编译路径不成立 |
| kernel hang | 删除 Set 或 Wait 一侧、`FetchEventID` 连续复用、`Alloc/Release` 生命周期错误、框架事件冲突、跨核/AIC-AIV 协议误改 |
| 性能无变化 | 编译器补回同一同步、同步点不在热路径、stall 被其他流水或访存瓶颈掩盖、收益小于设备波动 |

性能无变化不是继续扩大删除范围的理由。

---

## 10. 决策与实验模板

环境记录：

| 字段 | 值 |
|---|---|
| source revision / diff base | ... |
| CANN / compiler / SoC / core type | ... |
| auto-sync / auto-sync log | on/off/path |
| accuracy command / performance command | ... |

同步点分析表：

| ID | 位置 | 类型 | producer→consumer | 地址冲突 | 跨迭代 | queue/TQueSync 证据 | auto-sync 证据 | 状态 | 理由 |
|---|---|---|---|---|---|---|---|---|---|
| S1 | ... | MTE2_V | MTE2 write→V read | RAW | 否 | 无 | 无 | KEEP | 裸 TBuf 搬入 |
| S2 | ... | PIPE_V | V write→V read | RAW | 否 | - | log:line... | CANDIDATE | 编译器补回；仅源码清理候选 |
| S3 | ... | TQueSync | ... | ... | ... | valid | - | CANDIDATE/KEEP | ... |
| S4 | ... | CrossCore | ... | ... | ... | ... | ... | OUT_OF_SCOPE | 跨核协议 |

实验结果表：

| 变体 | 删除集合 | build | 静态检查 | auto-sync 证据 | 精度 | 性能中位数 | 波动 | 处理 |
|---|---|---|---|---|---|---|---|---|
| baseline | 无 | PASS | PASS | recorded | PASS | ... | ... | 基线 |
| A | S2 | PASS | PASS | PASS | PASS | ... | ... | 计算收益 |
| B | S2,S5 | PASS | PASS | PASS | FAIL/FLAKY | - | - | ddmin |

---

## 11. LLM 最终输出与保留规则

LLM 完成后必须输出：环境和 baseline 摘要；全部同步点清单及四态结论；每个删除点的 producer、consumer、地址冲突、替代 happens-before 证据；仅包含允许范围的源码 diff；build、auto-sync log、精度和性能命令及结果；delta debugging 结果和组合依赖记录；最终保留删除集合与未删除原因。

禁止输出未经验证的结论：如“理论上安全”“应该不会影响精度”“官方会自动处理”“性能更快所以同步多余”。

允许结论格式：

```text
保留删除 S2：删除后 V RAW 由 auto-sync log 中 PIPE_V 覆盖；地址与循环生命周期无其他冲突；build、全量/压力/重复精度 PASS；性能收益 X%，超过项目门限和 3×noise。
保留 S4：属于跨迭代 queue slot 复用保护；删除后无替代 happens-before；状态 KEEP。
```

最终只保留满足以下全部条件的同步删减：修改范围符合本策略；删除理由可由依赖图和实际地址范围解释；删除后存在可靠、可核查的替代 happens-before；event ID、`TQueSync` 和 queue 生命周期完整；所有目标构建通过；全量、边界、压力和重复精度通过；性能收益稳定且超过噪声；不存在未解释组合依赖。任一条件不满足：恢复同步。

---

## 12. 官方参考文档

使用时优先查阅项目实际 CANN 版本对应官方文档；以下链接用于说明本策略采用的官方语义：

1. PipeBarrier(ISASI): https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0271.html
2. SetFlag/WaitFlag(ISASI): https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0270.html
3. AllocEventID: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0114.html
4. ReleaseEventID: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0115.html
5. FetchEventID: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0116.html
6. 自动同步与 auto-sync log: https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/900beta1/opdevg/BishengCompiler/atlas_bisheng_10_0008.html
7. 毕昇编译器编译选项: https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/900beta1/opdevg/BishengCompiler/atlas_bisheng_10_0010.html
8. TQue: https://www.hiascend.com/document/detail/zh/canncommercial/900/API/ascendcopapi/atlasascendc_api_07_0137.html
9. TBuf: https://www.hiascend.com/document/detail/zh/canncommercial/80RC2/apiref/opdevgapi/atlasascendc_api_07_0155.html
10. TQueSync: 以项目 CANN 版本对应官方同步控制文档为准。

## 检索卡（短卡）

动作：识别 AscendC 核内冗余同步，并在证据约束下安全删减。
适用：存在可定位的同步原语或 wrapper，且基线可稳定构建并通过全量精度。
限制：不得改变数学公式、tiling、buffer/queue、跨核协议、输出格式及其他性能点。
范围：AscendC kernel 的核内同步。
检索词：PipeBarrier、SetFlag、WaitFlag、TQueSync、同步 wrapper。
机会：kernel 内存在可定位、可审查的同步点。
