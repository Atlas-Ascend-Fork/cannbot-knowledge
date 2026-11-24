---
type: Optimization
title: 跨核累加 workspace 从"每核私有副本 ×核数放大 + 单核串行归约"改为"单份共享 + 跨核 AtomicAdd 直累"
description: 将跨核累加workspace由每物理核一份私有副本改为单份，并以GM AtomicAdd累加。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/01-single-shared-workspace-atomic-reduce.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：跨核累加 workspace 从"每核私有副本 ×核数放大 + 单核串行归约"改为"单份共享 + 跨核 AtomicAdd 直累"

> **单一优化点：** 当一个多核算子中某个"各核并行产生、需跨核求和后再 Cast 输出"的累加 workspace，被实现成**每个物理核一份全量私有副本（总容量 ×核数放大），各核只写自己的副本，再由单个核按核号定序串行归约所有副本**时，把它改成**全局单份共享 workspace + 各核在写出阶段直接用跨核 GM AtomicAdd 累加到同一份**。消除 ×核数的内存放大、消除单核串行归约（及其全核空转）、消除为规避累加顺序非确定而引入的私有副本机制。本策略只改"累加 workspace 的布局与写/归约方式"，不改任何计算语义。
>
> **算子/管线无关性：** 适用于 AscendC 任意"AIC+AIV 多核、某输出需跨核累加再 Cast"的算子（attention 反传梯度、稀疏梯度、任意 reduce-scatter 风格的梯度累加）。不限于任何具体算子。

---

## 1. 原理

该写法的核心病灶是**用"私有副本 + 软件定序归约"去规避跨核同址累加的非确定顺序**。但只要输出 dtype 容忍 FP32 ULP 级抖动（fp16/bf16 输出），跨核 GM AtomicAdd 的硬件串行就足以保证正确，私有副本完全没有必要。

本策略利用的硬件机制：

| 机制 | 利用方式 |
|---|---|
| GM AtomicAdd（FP32） | `SetAtomicAdd<float>()` 后 `DataCopy(UB→GM)` 即硬件原子累加；跨核同址累加由硬件串行保证正确，无需软件定序 |
| 单份共享 workspace | 累加目标只有一份（×1），内存放大、启动清零量、归约读量全部降为单份 |
| 跨核同步 barrier | 沿用既有"写出阶段 → 收尾读"的跨核 barrier（如 `PipeBarrier<PIPE_MTE3> + SyncAll`），保证所有 AtomicAdd 在收尾前对全核可见 |
| FP32 累加宽容度 | AtomicAdd 跨核累加顺序非确定，但 FP32 ULP 抖动（~1e-7 相对）远低于 fp16/bf16 的 atol，精度不回归 |

定性 pipe 归因（相对、无绝对数字）：收尾/归约阶段的 `aiv_mte2`（读各副本）+ `aiv_vec`（串行 Add）占比大幅下降且不再集中在单核；`usedCoreNum` 利用率回升；workspace GM 占用与 InitOutput 清零量同比下降到 1/核数。

---

## 2. 性能问题模式（基线写法）

低效基线用**私有副本 + 单核串行归约**规避跨核同址 AtomicAdd 的非确定累加顺序：

```text
# Host（tiling）：workspace 按物理核数放大
reduceWorkspaceLen = totalElems * sizeof(float) * coreCount        # ×核数 放大
for core in 0 .. coreCount: alloc privateSlice[core]                # 核数份独立全量

# Kernel - 写出/产生阶段（每核只写自己副本）：
dstOff = privateSliceBase(myCoreIdx) + tokenStart * rowElems        # 偏移含本核副本基址
ordinary_store reduceWorkspace[myCoreIdx][tokenStart]              # 普通写（非跨核 AtomicAdd）

# Kernel - 收尾/输出阶段（仅单个核串行归约所有副本）：
if myCoreIdx != designatedCore: return
for off in 0 .. totalElems step chunk:
    acc = reduceWorkspace[slice0 + off]                             # 副本0 初始化 acc
    for slice in 1 .. coreCount:                                    # 串行读其余副本累加
        acc += reduceWorkspace[slice * sliceElems + off]
    output[off] = Cast(acc)                                         # 单核 Cast 输出
```

三个开销源（每个都随核数线性恶化）：

- **workspace 内存放大 ×coreCount**：GM 分配 `total × coreCount`。副本仅用于容纳私有副本，GM 占用异常大。
- **InitOutput 全清零 ×coreCount**：为保证 acc 初值正确，启动须把所有副本清零；清零量 = `total × coreCount`，墙钟可观。
- **收尾单核串行归约**：仅单个核干活，读 `total × coreCount`，其余核空转；墙钟 = 单核带宽限制下的全量读 + 累加 + Cast。

典型症状：profiling 显示收尾/输出归约阶段 `aiv_mte2`（读副本）+ `aiv_vec`（Add）占比高且集中在单核，`usedCoreNum` 利用率低；workspace GM 占用与核数成正比。

---

## 3. 正确性红线

### 3.1 AtomicAdd 语义与 dtype
- 写出前 `SetAtomicAdd<float>()`，写完 `SetAtomicNone()`。AtomicAdd 仅对 `DataCopy(UB→GM)` 类 store 生效，须确认写路径经过该机制。
- 目标 dtype 必须是 **FP32**（硬件 AtomicAdd 原生支持 FP32；bf16/fp16 通常不支持）。若各核部分结果是低精度，须先在 FP32 workspace 累加、收尾再 Cast。

### 3.2 跨核可见性（最易翻车）
- 必须保证"最后一个写出 AtomicAdd"先于"任一收尾读"完成。沿用既有"写出 → 收尾"跨核 barrier；若流水无此同步，**必须新增**，否则收尾读到未完成累加 → 错值。
- AtomicAdd 的"硬件串行"只保证**同一地址**多次累加的正确性，**不**保证跨核时序——跨核时序靠 barrier。

### 3.3 防双累加的切分必须保留
- 若原有"某维度对半切分 block"是为避免双 subBlock/双路对同一 block 重复累加（如 2× 防护），**该切分逻辑必须原样保留**——只改写目标从私有副本改共享 workspace，切分不变。否则同一 block 被两路各 AtomicAdd 一次 → 结果 ×2。

### 3.4 tiling 字段兼容
- 若 tiling 里某个"副本长度"字段被 kernel 当作容量上限读取，单份化后**不要直接删字段**（kernel 会读旧值/越界）；保留该字段（令其 == 全量长度）或同步改所有读取点。

### 3.5 精度边界
- 输出 FP32 且下游要求 bit-exact：**不适用**（AtomicAdd 顺序非确定破坏 bit-exact）。
- 输出 fp16/bf16（atol ~1e-3 量级）：适用，ULP 抖动不可见。

### 3.6 已知陷阱
- **陷阱 A 输出 FP32 + bit-exact 误用**：FP32 bit-exact 用例出现间歇性 mismatch，而 fp16/bf16 用例正常。修复：确认输出 atol 容忍 ULP；FP32 bit-exact 场景保留私有副本串行归约。
- **陷阱 B 漏跨核可见性 barrier**：以为 AtomicAdd 硬件串行就够，未保证写出→收尾跨核 ordering → 间歇性错值/NaN（竞态，难复现）。修复：确认并保留写出→收尾的跨核 barrier。
- **陷阱 C 顺手删防双累加切分**：改单份时顺手删了切分逻辑 → 对应维度结果系统性 ×2。修复：保留 per-路 blkStart/blkEnd 切分，只改写目标偏移。
- **陷阱 D 副本长度字段被删**：kernel 读到旧值/越界。修复：保留字段或同步改读取点。
- **陷阱 E AtomicAdd dtype 不匹配**：`SetAtomicAdd<float>` 但 workspace 实际存低精度 → AtomicAdd 不生效。修复：workspace 一律 FP32，收尾 Cast。

---

## 4. 泛化条件

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 累加语义 | 输出是"各核部分结果求和"（reduce-sum），而非"各核各写不重叠区域"（纯 scatter 无累加） |
| 当前形态 | workspace 是 per-core 私有副本 ×核数放大 + 单核串行归约（即 §2 模式） |
| 输出 dtype 容忍 ULP | 输出 fp16/bf16，或 FP32 但不要求 bit-exact |
| AtomicAdd 支持 | 硬件/驱动支持 FP32 GM AtomicAdd；低精度部分结果可经 FP32 中转 |
| 跨核可见性同步 | 既有流水已有（或可加）"写出 → 收尾读"的跨核 barrier |

不适用或需先满足前提：

- 输出 FP32 且要求 bit-exact（AtomicAdd 顺序非确定）。
- 该 workspace 是其它归约（max/min/prod）——AtomicAdd 只覆盖加法。
- 硬件不支持目标 dtype AtomicAdd 且无法用 FP32 中转。
- 既有流水无法保证跨核"写→读"可见性（需先加 barrier，属同步重构）。
- 该算子内已有其他路径采用同模式且精度通过（如某条输出路径早已是"单份 + 跨核 AtomicAdd"）——则本路径对齐它即可，可行性更高。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| **Host tiling** | workspace 容量计算从 `×coreCount` 改为 `×1`（单份）。保留"副本长度"字段命名兼容（== 全量长度）或同步改读取点 |
| **Kernel 写出阶段** | 累加目标偏移去掉 `privateSliceBase = coreIdx × sliceElems`，改为直接 `base + tokenStart × rowElems`；`SetAtomicAdd<float>()` 后 `DataCopy` 即跨核原子累加 |
| **Kernel 收尾阶段** | 删除"读 N 副本串行累加"循环；单份 workspace 已被 AtomicAdd 累加好，直接 Cast 输出（并行化见同族策略 02） |
| 跨核同步 | **不改**（沿用既有写出→收尾 barrier） |
| 写出 per-block 计算 | **不改**（oob idx→0、partial clamp、防双累加切分等不变） |

### 5.2 关键代码模式（通用前/后对比）

**Host（tiling）**：
```text
# 前：×coreCount 放大
reduceWorkspaceLen = alignUp(totalElems * fp32SizeBytes, GM_ALIGN) * coreCount

# 后：单份
reduceWorkspaceLen = alignUp(totalElems * fp32SizeBytes, GM_ALIGN)
```

**Kernel 写出阶段**：
```text
SetAtomicAdd<float>()
# 前：偏移含本核副本基址
#   dstOff = privateSliceBase(coreIdx) + base + tokenStart * rowElems
# 后：直接累加到共享 workspace
dstOff = base + tokenStart * rowElems
DataCopy(reduceWorkspaceGm[dstOff], ubData)        # 硬件 AtomicAdd 累加
SetAtomicNone()
```

**Kernel 收尾阶段**：删除归约循环，单份 Cast：
```text
# 前：单核 for(off) { acc=ws[slice0+off]; for slice in 1..N: acc+=ws[slice+off]; out[off]=Cast(acc) }
# 后：单份已累加好，直接 Cast
for off in 0 .. totalElems step chunk:
    DataCopy(ub, reduceWorkspaceGm[off], chunk)
    Cast(ub, ub, fp32 -> outputDtype)
    DataCopy(outputGm[off], ub, chunk)
```

### 5.3 数据与缓存布局
- workspace 从 `total × coreCount` 降为 `total × 1`；InitOutput 清零量同比下降。
- 不新增片上 buffer；写出复用既有 UB，收尾复用既有 cast buffer。
- workspace 元素须 16/32B 对齐（FP32 MTE2 / 输出 dtype MTE3 要求）；行宽应已按 dtype 对齐到块大小。

### 5.4 正确性论证（须在实施时写明）
1. 各核部分结果经 AtomicAdd 求和到同一份，数学上等价于私有副本串行求和（只是顺序非确定）。
2. FP32 ULP 抖动 < atol：AtomicAdd 顺序差异在 FP32 ULP（~1e-7 相对），Cast 到 fp16/bf16 后不可见。
3. 若该算子内已有其他路径采用"单份 + 跨核 AtomicAdd"且精度通过，本路径对齐该实现，一致可信。
4. 写出与收尾之间有既有 barrier，保证写对读可见。

---

## 6. LLM 前置问题

| 问题 | 必填内容 |
|---|---|
| 累加语义 | 该 workspace 是否"各核部分求和"？输出 dtype + atol 是否容忍 FP32 ULP？ |
| 当前形态 | 是否 per-core 私有副本 ×核数 + 单核串行归约？核数？workspace 总放大倍数？ |
| AtomicAdd 支持 | 硬件是否支持 FP32 GM AtomicAdd？workspace 是否 FP32？ |
| 跨核可见性 | 写出→收尾之间是否有既有跨核 barrier？没有则如何补？ |
| 防双累加切分 | 是否有避免双路重复累加的切分逻辑？改单份后是否保留？ |
| 字段兼容 | tiling 的副本长度等字段是否被 kernel 读取？单份后如何兼容？ |
| 基线 | 修改前 build/精度/perf 基线值 |

任一项无法回答，不实施。

---

## 7. 验收标准

```bash
bash <build_script> --soc=<soc> --op=<op>
source <set_env>
pytest <op>/test/test_<op>_*.py        # 精度 + 性能
```

精度：与基线一致（fp16/bf16 用例全部通过；AtomicAdd ULP 抖动不可见）。FP32 bit-exact 用例若存在则按红线 §3.5 判定（不适用本策略）。

性能/资源（**用 profiling 归因**，相对、无绝对数字）：
- **workspace GM 占用**从 `×核数` 降为 `×1`（从 tiling 日志 / workspace 分配字节数核对）。
- **InitOutput 清零量**同比下降。
- 收尾阶段不再有"单核读 N 副本累加"循环（归约循环消失）。
- 收尾阶段 `aiv_mte2`/`aiv_vec` 占比下降、`usedCoreNum` 利用率回升。
- **判据**：workspace 降到 ×1 + 收尾归约循环消失 + 收尾单核 pipe 占比下降。若 workspace 未降到 ×1，说明副本放大未真正消除。

边界 shape：单核场景（coreCount=1，私有副本本就 ×1，本策略无变化但须不破坏）、不同核数、不同行宽（影响对齐）。

回退条件：精度出现非 ULP 级回归（系统性偏差 → 多半是陷阱 C 双倍或陷阱 B 竞态）；FP32 bit-exact 用例间歇 mismatch（陷阱 A）；workspace 内存未下降到 ×1。

与其它策略的关系：本策略把 workspace 改单份后，收尾从"单核归约 N 副本"变成"单份 Cast"；同族策略 02 进一步把单核 Cast 并行化为多核（02 依赖本策略的"单份共享"前提）。本策略与搬运批量化策略（gather/scatter 侧）正交——批量化优化"怎么搬"，本策略优化"搬到哪、怎么累加"，可叠加。

## 检索卡（短卡）

动作：将跨核累加workspace由每物理核一份私有副本改为单份，并以GM AtomicAdd累加。
适用：各核部分结果需跨核求和，且输出为容忍FP32 ULP级抖动的fp16/bf16。
限制：写出前启用SetAtomicAdd<float>()，写完恢复SetAtomicNone()。
范围：多核算子中跨核求和后Cast输出的累加workspace。
检索词：跨核GM AtomicAdd、私有副本、软件定序归约、reduce-sum、workspace。
机会：存在“私有副本+软件定序归约”以规避跨核同址累加顺序。
