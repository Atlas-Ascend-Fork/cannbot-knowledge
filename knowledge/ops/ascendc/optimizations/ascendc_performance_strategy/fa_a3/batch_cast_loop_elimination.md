---
type: Optimization
title: FP32→QType 写回用整块批量 Cast 替代逐行 Cast 循环
description: 将 FP32→QType 写回从逐行 Cast 改为整块批量 Cast。
tags:
- task.optimization
- topic.attention
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/04-batch-cast-loop-elimination.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：FP32→QType 写回用整块批量 Cast 替代逐行 Cast 循环

> **单一优化点：** 当 attention backward vec 阶段把 FP32 中间结果 Cast 到低精度 QType（FP16/BF16）并写回 GM 供 cube 下游消费时，naive 实现因「FP32 src 行距（`alignedCols`，8 元素/32B 对齐填充）与 QType dst 行距可能不同、且每行只有前 `actualCols` 个有效」而采用逐行 Cast 循环（每行一次 Cast 调用）。改为：在 **无 padding 条件**（`alignedCols == actualCols`）下用一次整块 Cast 处理 `numRows*alignedCols` 个元素，把 Cast 派发次数从 `numRows` 降到 1，消除逐行的标量地址/参数设置开销；非对齐尾块（行距不匹配）保留逐行 Cast 循环作 `else` 分支。

---

## 1. 已有模式与变更

### 已有模式（baseline）

attention backward vec 阶段常持有 FP32 中间结果（如 softmax 输出 / 梯度），需 Cast 到 QType 写回 GM workspace。由于 FP32 src 行距 `alignedCols`（向上对齐到 8 元素/32B）与 QType dst 行距 `qAlign`（对齐到 16 元素）**可能不同**，且每行仅前 `actualCols` 个元素有效，baseline 对每行发一次 Cast：

```text
// baseline：逐行 Cast 循环（numRows 次 Cast 派发）
for r in [0, numRows):
    srcRowOff = r * alignedCols        // FP32 行距
    dstRowOff = r * qAlign             // QType 行距
    Cast(dstUb[dstRowOff], srcUb[srcRowOff], roundMode, actualCols)
SyncVToMte3()                          // V(Cast 写) -> MTE3(DataCopy 读)
DataCopyPad(gmDst, dstUb, {numRows, actualCols*sizeof(QType), srcStride=0, dstGap, ...})
```

`numRows` 行产生 `numRows` 次 Cast 派发，每次伴随标量地址/参数计算（`srcRowOff`、`dstRowOff` 推导），推高 `aiv_scalar_time`；循环位于外层多次迭代（每个分块 / 每个 KV 段）时累积显著。

### 变更（v1.1）

- 【变更】在逐行 Cast 循环外包一层条件分支：`actualCols % 16 == 0`（等价于无 padding 且满足块 Cast 对齐粒度）时走**整块 Cast** 单次派发路径；否则保留原逐行循环作 `else` 尾块分支。
- 【变更】整块分支内 `Cast(dstUb, srcUb, roundMode, numRows*alignedCols)` 一次处理全部元素，dst 逻辑行距恰好 = `actualCols`，与下游 `DataCopyPad` 的 `srcStride=0` 连续读取自洽。
- 【变更】两条分支的 V→MTE3 反向同步（Cast 写 → DataCopy 读）**均保留**，不因整块化而删除；同一 UB buffer 上连续两次 Cast 间的 MTE3→V 同步亦在两分支中保留。
- 【不变】QType round mode 按方向区分（FP32→FP16 `CAST_ROUND`、FP32→BF16 `CAST_RINT`），两分支共用，本策略不改。
- 【不变】下游 `DataCopyPad` 参数（`srcStride=0`、`dstGap`、`rightPadding`）不改；写出元素总数不变，故 MTE3 写回字节数不变。

**expected_speedup_pct：8 ~ 15**（仅作用于该 Cast 循环节点；量化依据：Cast 指令派发次数 `numRows → 1`，对应 `aiv_scalar_time` 中该循环的标量地址/参数 setup 线性下降；实际整体收益随 `numRows` 与外层迭代数线性放大，shape 越大、外层迭代越多收益越高，非固定百分比，故不夸大）。

---

## 2. 参数变更表

| parameter | baseline | v1.1 | unit | remark | constraint |
|---|---|---|---|---|---|
| Cast 派发次数（单次外层迭代） | `numRows` | 1（整块分支）/ `numRows`（else 尾块分支） | 次 | 整块分支把循环折叠为单次 Cast | 整块分支仅当 `actualCols % 16 == 0` 命中 |
| 整块分支条件 | （无，恒逐行） | `actualCols % 16 == 0` | — | 同时保证「无 padding（`alignedCols==actualCols`）」与「块 Cast 元素数对齐」 | 见反模式：非对齐 shape 必须回落 else 分支，否则数据错位 |
| Cast count（整块分支） | `actualCols`（每行） | `numRows * alignedCols`（一次） | 元素 | dst 起点为 buffer 基址，无行偏移 | `numRows*alignedCols` 须为 Cast 对齐粒度（16 元素/32B）整数倍；`actualCols % 16 == 0` 已隐含保证 |
| dstUb 占用 | `numRows * qAlign` | `numRows * alignedCols`（整块分支） | 元素(QType) | 整块路径无行间 gap，占用通常 ≤ baseline | `numRows*alignedCols*sizeof(QType)` ≤ dstUb 容量（用 ascend-hardware 真实 UB 核算，禁硬编码） |
| Cast round mode | 方向区分 | 方向区分（不变） | 枚举 | FP32→FP16=`CAST_ROUND`，FP32→BF16=`CAST_RINT` | 禁止为整块化改动 round mode |
| V→MTE3 同步 | 循环后 1 处 | 整块分支 + else 分支各保留 1 处 | 处 | Cast(V 写)→DataCopy(MTE3 读) 反向同步 | 两分支都必须有，不得删除 |
| MTE3→V 同步（同 buffer 连续两次 Cast 间） | 逐行路径中保留 | 两分支均保留 | 处 | 前一次 DataCopy 写完 buffer 后第二次 Cast 才能覆写 | 同一 UB 上连续两次 Cast 共用 buffer 时必须有 |
| 下游 DataCopyPad srcStride | 0 | 0（不变） | block | 整块连续 dst 行距 = actualCols，与 srcStride=0 自洽 | 下游若用非零 srcStride 不可实施本策略 |

---

## 3. 结构变更模式

抽象结构（不含真实变量名 / 行号）：在「逐行 Cast + `srcStride=0` 写回」外包条件分支，无 padding 走单次整块 Cast，非对齐回落逐行尾块。两分支同步结构对称。

```text
roundMode = FP32->FP16 ? CAST_ROUND : CAST_RINT     // 方向区分，两分支共用，不改

if (actualCols % 16 == 0) {                          // 无 padding 且块 Cast 对齐：整块路径
    // src 行距 == actualCols（无 padding），布局已连续线性
    Cast(dstUb, srcUb, roundMode, numRows * alignedCols)   // 单次派发
}
else {                                               // 尾块：行距不匹配 / 非对齐，保留逐行
    for r in [0, numRows):
        Cast(dstUb[r * qAlign], srcUb[r * alignedCols], roundMode, actualCols)
}
// —— 两分支汇合：跨 pipe 同步全部保留 ——
SyncVToMte3()                                        // Cast(V 写) -> DataCopyPad(MTE3 读)，两分支都必须
DataCopyPad(gmDst, dstUb, {blockCount=numRows,
                           blockLen=actualCols*sizeof(QType),
                           srcStride=0, dstGap, rightPadding=...})

// 若同一 dstUb 上紧接着第二次 Cast（如先 P 后 dS 复用同 buffer）：
//   两次 Cast 之间须保留 MTE3->V 反向同步（前次 DataCopy 写完 -> 本次 Cast 覆写），
//   整块 / 逐行两分支均须保留，与 baseline 一致。
```

**整块分支为何与下游 `srcStride=0` 自洽**：无 padding 时 dstUb 是连续 `numRows*actualCols` 个 QType，逻辑行距恰好 = `actualCols`，`DataCopyPad` 的 `srcStride=0`（相邻 block 连续）逐行取 `actualCols` 个，完全匹配。else 分支 dstUb 有行间 gap，但 baseline 本就用 `srcStride=0` 连续读——仅当 `qAlign==actualCols`（即无 padding）时才自洽；而 else 分支只在非对齐时进入，此时下游读取的 rightPadding / dstGap 已由 baseline 正确处理，本策略不改动下游，故零风险。

---

## 4. 反模式

- **pattern**：不检查 `actualCols % 16 == 0`、无条件对全部行做整块 Cast。 **reason**：`actualCols` 非对齐时 `alignedCols > actualCols`，src 行尾有 padding，整块 Cast 会把 padding 连续写入 dst，下游按 `actualCols` 行距读取时把上一行 padding 当成下一行开头。 **metrics**：非对齐 shape 静默数据错位 / 精度 FAIL（aligned shape 仍通过，极具隐蔽性）。
- **pattern**：删除整块分支后的 V→MTE3 同步（误以为单次 Cast 无需等待）。 **reason**：Cast 是 V pipe 写 dstUb，DataCopy 是 MTE3 读 dstUb，缺失反向同步会读到未完成写入。 **metrics**：间歇性脏读 / 随机 mismatch。
- **pattern**：同一 UB buffer 上连续两次 Cast（先 P 后 dS）间删除 MTE3→V 同步。 **reason**：前一次 DataCopy（MTE3 写 GM 时可能复用/释放该 buffer）未完成即被第二次 Cast 覆写。 **metrics**：第二次 Cast 读到被破坏的源数据。
- **pattern**：为整块化把 round mode 改成统一值（如一律 `CAST_RINT`）。 **reason**：round mode 按精度方向区分，FP16 用 `CAST_ROUND`、BF16 用 `CAST_RINT`，混用引入精度偏差。 **metrics**：超出 atol/rtol 的精度下降。
- **pattern**：下游 DataCopy 用非零 `srcStride`（源按行距跳读）时仍套用整块连续 Cast。 **reason**：整块 Cast 产出连续布局，与非零 srcStride 的跳读语义不匹配。 **metrics**：行错位 / 精度 FAIL。
- **pattern**：src/dst layout 不同（NZ vs ND）时用整块 Cast 做 layout 转换。 **reason**：Cast 不做格式转换，NZ↔ND 须用专门转换 API。 **metrics**：数据完全错位 / 非法访存。
- **pattern**：整块写出量 `numRows*alignedCols*sizeof(QType)` 超出 dstUb 容量未核算。 **reason**：buffer 越界。 **metrics**：UB OOM / 写越界崩溃。

---

## 5. 硬件约束表

| resource | capacity | baseline_usage | v1.1_usage | constraint |
|---|---|---|---|---|
| dstUb（QType） | 芯片相关，由 ascend-hardware 获取（禁硬编码 KB） | `numRows*qAlign*sizeof(QType)`（逐行含 gap） | `numRows*alignedCols*sizeof(QType)`（整块分支，通常 ≤ baseline） | v1.1 占用须 ≤ dstUb 容量；按整块路径核算 |
| Cast 元素对齐粒度 | 16 元素 / 32B（FP32→FP16/BF16） | 每行 `actualCols` 须满足（逐行各自对齐） | 整块 `numRows*alignedCols` 须为 16 元素整数倍 | 整块分支条件 `actualCols % 16 == 0` 已保证 |
| V→MTE3 反向同步事件 | 硬件 flag 资源 | 1（循环后） | 1（每分支后各 1，二选一执行） | 两分支均须保留，禁删 |
| MTE3→V 反向同步事件（同 buffer 连续两次 Cast 间） | 硬件 flag 资源 | 逐行路径中保留 | 两分支均保留 | 同 UB 连续两次 Cast 共用 buffer 时必须有 |
| MTE3 写回带宽 | 芯片相关 | `numRows*actualCols*sizeof(QType)` | 不变（写出元素总数相同） | 本策略不改写回字节数，仅改 Cast 派发方式 |

---

## 6. 协同建议

- **本策略可独立执行**：仅需在目标逐行 Cast 循环外包条件分支，不依赖组内其他策略的状态，不与其他策略的写回地址/同步冲突。
- **synergistic_with（可选叠加，非必需）**：
  - `01-softmax-scalar-to-vector`：若被 Cast 的 FP32 中间量本身由 softmax 行统计量标量归约产生，先向量化归约再叠加本策略，可同时降 `aiv_scalar_time` 的两部分。
  - `02-softmax-stats-s2-cache`：缓存循环不变统计量减少 MTE2 后，本策略进一步削减同阶段的 Cast 派发，二者作用不同开销来源、互不干扰。
  - `03-aiv-subcore-s1-split`：子核按行切分后，各子核的逐行 Cast 循环仍可套用本策略（各子核的 `numRows` 变小，整块化收益按子核工作量等比缩放）。

---

## 7. 验证要点

**compile_check**：
- 整块分支与 else 分支均能编译；条件 `actualCols % 16 == 0` 在编译期/运行期可观测。
- `Cast(dstUb, srcUb, roundMode, numRows*alignedCols)` 的 count 满足 16 元素对齐粒度（编译期可断言）。
- V→MTE3、MTE3→V 同步在两分支均存在，无悬挂 `WaitFlag`/`SetFlag`。
- dstUb 占用 `numRows*alignedCols*sizeof(QType)` ≤ 分配容量（用 ascend-hardware 真实 UB 核算）。

**accuracy_check**：
- **必须覆盖 `actualCols % 8 != 0` 的 shape**：回落逐行 `else` 分支，验证行距转换、`rightPadding` 尾处理正确、无错位（应从 FAIL/可疑 → PASS）。
- **必须覆盖 `actualCols % 8 == 0` 但 `actualCols % 16 != 0` 的 shape**（如 actualCols=8/24/40）：仍走逐行 `else` 分支（因整块条件收紧到 `% 16`），须 PASS，确认未误入整块分支导致数据错位。
- **覆盖 `actualCols % 16 == 0` 的 aligned shape**（如 64/128）：走整块分支，结果须与 baseline 逐行实现逐位一致（无 padding 下数学等价）。
- FP16（`CAST_ROUND`）与 BF16（`CAST_RINT`）两种 QType 分别验证 round mode 正确。
- 同 UB buffer 连续两次 Cast 的 shape（若存在）验证两分支 MTE3→V 同步下无脏读。

**performance_check**：
- 该阶段 Cast 派发次数：aligned shape 下从 `numRows` → 1（外层迭代数不变）；非对齐 shape 下仍为 `numRows`（else 分支，无退化）。
- `aiv_scalar_time` 在 aligned shape 下下降，下降幅度随 `numRows` 与外层迭代数线性放大；`aiv_scalar_ratio` 改善方向正确。
- MTE3 写回字节数不变（仅 Cast 方式变化）；task duration 改善方向正确，收益为定性正向、非固定百分比。

## 检索卡（短卡）

动作：将 FP32→QType 写回从逐行 Cast 改为整块批量 Cast。
范围：attention backward vec 阶段的低精度 GM 写回
检索词：FP32、QType、FP16/BF16、批量 Cast、逐行 Cast
