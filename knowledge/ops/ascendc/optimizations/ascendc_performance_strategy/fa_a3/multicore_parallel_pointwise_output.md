---
type: Optimization
title: 收尾 Pointwise 阶段从"单核串行"改为"多核线性并行切分"
description: 去掉指定核门控，将收尾Pointwise由单核串行改为多核线性分段处理。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/02-multicore-parallel-pointwise-output.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：收尾 Pointwise 阶段从"单核串行"改为"多核线性并行切分"

> **单一优化点：** 当一个"对全量 workspace 做 读→(可选 scale)→Cast→写输出"的收尾阶段被钉死在**单个核**（仅一个核串行处理全量、其余核空转）时，把它改成**所有物理核线性切分全量、各核独立处理自己那段（Pointwise 无跨核数据依赖）**，把单核墙钟近似除以核数。本策略只改"收尾阶段的并行度"，不改 Cast 的数学语义、不改 workspace 布局、不改跨核同步。
>
> **算子/管线无关性：** 适用于 AscendC 任意"多核可用、收尾阶段逐元素 Pointwise（DataCopy→Muls→Cast→DataCopy）且元素间无依赖"的算子。不限于 attention 反传。前提：workspace 已是**单份共享**（各核读不同段不冲突）——若仍是 per-core 私有副本，须先做同族策略 01。

---

## 1. 原理

收尾 Cast 阶段虽是 Pointwise（无元素间依赖），却常因"写在同一输出张量"被误设计成单核串行（源于"怕跨核写冲突"或"沿用 reduce 单核归约的壳"）。但 Pointwise 各核处理不重叠段、写不同地址，天然无冲突。

本策略利用的硬件机制：

| 机制 | 利用方式 |
|---|---|
| 多核独立 HBM 带宽 | 每核有独立 HBM 带宽，N 核并行 Pointwise 近似 N× 吞吐 |
| 无跨元素依赖 | Pointwise（Cast/Muls）元素间独立，各核处理不同段无数据依赖、无需跨核通信 |
| 不重叠分段 | 各核段 `[i×perCore, (i+1)×perCore)` 互不重叠，写不同输出地址，无冲突 |

定性 pipe 归因（相对）：收尾阶段 `usedCoreNum` 利用率从 1/核数 提升到接近全核；`aiv_mte2`+`aiv_mte3` 不再集中在单核；收尾阶段墙钟近似 ÷核数（受聚合 HBM 带宽上限约束）。

---

## 2. 性能问题模式（基线写法）

收尾 Cast 阶段被钉死在单核：

```text
# 仅单个核执行，其余核 return
if myCoreIdx != designatedCore: return
for off in 0 .. totalElems step chunk:
    DataCopy(ub, wsGm[off], chunk)            # 单核读
    [Muls(ub, ub, scale)]                     # 单核算（某路乘 scale，另一路不乘）
    Cast(ub, ub, fp32 -> outputDtype)         # 单核 Cast
    DataCopy(outputGm[off], ub, chunk)        # 单核写
```

开销源：
- **单核带宽瓶颈**：全量 `totalElems` 的读+写都走单核 HBM 带宽，墙钟 ≈ `2×total×sizeof / 单核带宽`。核数中绝大多数核完全空转。

典型症状：profiling 显示收尾阶段 `usedCoreNum` 利用率极低（1/核数）、`aiv_mte2`+`aiv_mte3` 集中在单核、其余核 `aiv_time` 低。

---

## 3. 正确性红线

### 3.1 段不重叠 + 不越界
- 各核 `[start, start+perCore)` 互不重叠；`start+perCore` 可能超 `totalElems`，须 clamp `remain = totalElems - start`。
- `perCore` 向上取整对齐块大小 → 最后一个非空核的段会 < perCore（由 remain clamp），不越界。

### 3.2 段边界对齐
- `perCore`、`batch` 须按 dtype 块大小对齐（FP32 MTE2 / 输出 dtype MTE3 的 32B 对齐：FP32 8 元素、bf16 16 元素等）。
- 极端尾块（remain < 对齐块且 > 0）：`batch = 对齐块` 但不能越界读（workspace 末尾须有对齐余量，或 totalElems 本身是对齐块倍数）。

### 3.3 scale 一致性
- 若 Pointwise 含 `Muls(scale)`，所有核用同一 `scale`，分段不影响数值。

### 3.4 一维 flat 切分的 layout 等价（关键，易错）
- 若 workspace 多维 layout 与输出多维 layout 不同，**一维 flat 切分不一定等价**。当某中间维度 N≠1 时，workspace flat 顺序与输出 flat 顺序可能错位。
- 须验证两 layout flat 后元素一一对应；若不等价，按输出实际 stride 切分，而非一维 flat。

### 3.5 已知陷阱
- **陷阱 A 段边界未对齐**：`perCore` 不对齐 → MTE2/MTE3 报错或错值。修复：`perCore = align(ceil(total/cores))`，`batch = align(min(chunk, remain))`。
- **陷阱 B 遗漏尾核 clamp**：`start+perCore > totalElems` 未 clamp → 末核越界读/写。修复：`remain = min(perCore, total-start)`，`start >= total` 时 return。
- **陷阱 C flat 切分破坏 layout**：N≠1 时一维切分错位。修复：验证 flat 等价；不等价则按输出 stride 切分。
- **陷阱 D 误以为是 reduce 并行**：阶段实际含跨元素归约（sum/max），误用分段 → 各核只归约自己段，结果不全。修复：本策略只适用 Pointwise；含归约须用 reduce-then-broadcast 或同族策略 01 的 AtomicAdd 直累。

---

## 4. 泛化条件

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 阶段是 Pointwise | 读→(scale)→Cast→写，元素间无依赖、无跨元素归约 |
| workspace 单份共享 | 各核读不同段不冲突（若是 per-core 私有副本，先做策略 01；否则各核只读自己副本即天然并行，无需本策略） |
| 输出分段不重叠 | 各核写 `[start, start+perCore)` 互不重叠 |
| 段边界对齐 | perCore/batch 须按 dtype 块大小对齐 |
| 无跨核顺序依赖 | 输出顺序由地址决定（各核写固定地址），不依赖核执行顺序 |
| layout 等价 | 一维 flat 切分须与多维 layout 等价（或按实际 stride 切分） |

不适用：
- 阶段含跨元素归约（sum/max）——那需要 reduce，不是 Pointwise 并行。
- 输出段无法不重叠切分（如输出本身就是 per-core 分散）。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| **Kernel 收尾/Cast 函数** | 去掉 `if myCoreIdx != designatedCore: return` 的单核门控；改为按 `myCoreIdx` 计算本核段 `[start, start+perCore)`，只处理该段 |
| tiling / Host | **不改**（核数已有；perCore 在 kernel 内算） |
| 跨核同步 | **不改**（Pointwise 各核独立，无需新增） |

### 5.2 关键代码模式（通用前/后对比）

```text
# 前：仅单核
if totalElems == 0 or usedCoreNum == 0 or myCoreIdx != designatedCore: return
remain = totalElems; off = 0
while remain > 0: { DataCopy/Muls/Cast/DataCopy ... }

# 后：所有核线性切分
if totalElems == 0 or usedCoreNum == 0 or myCoreIdx >= usedCoreNum: return
ALIGN = 对齐块元素数
perCore = ceil(totalElems / usedCoreNum)
perCore = alignUp(perCore, ALIGN)                         # 段边界对齐
start = myCoreIdx * perCore
if start >= totalElems: return                            # 核数 > 段数时尾部核空
remain = min(perCore, totalElems - start)                 # 尾核 clamp
off = start
while remain > 0:
    batch = align(min(chunk, remain))                     # 极端尾块 batch = ALIGN
    DataCopy(ub, wsGm[off], batch); [Muls]; Cast; DataCopy(outputGm[off], ub, batch)
    off += batch; remain -= batch
```

### 5.3 layout 等价性论证
- 输出张量按一维 flat 切分（`off` 连续）。各核写 `[start, start+perCore)`，合起来覆盖 `[0, totalElems)`，无重叠无遗漏。
- workspace 多维 layout flat 后与输出 flat 元素一一对应时，一维切分等价。**若某中间维度 N≠1 须验证 flat 等价**，否则按输出实际 layout 切分。

---

## 6. LLM 前置问题

| 问题 | 必填内容 |
|---|---|
| 阶段性质 | 是否纯 Pointwise（无跨元素归约）？ |
| workspace 形态 | 是否单份共享？（per-core 副本先做策略 01） |
| 切分等价 | 输出一维 flat 切分是否与多维 layout 等价？ |
| 对齐 | perCore/batch 对齐块大小（dtype 决定）？totalElems 是否对齐块倍数？ |
| 核数 | usedCoreNum？核数 > 段数时尾核如何处理？ |
| 基线 | 修改前收尾阶段单核墙钟 / 整体基线 |

任一项无法回答，不实施。

---

## 7. 验收标准

```bash
bash <build_script> --soc=<soc> --op=<op>
source <set_env>
pytest <op>/test/test_<op>_*.py
```

精度：与基线一致（Pointwise，数值不变）。

性能（**用 profiling 归因**，相对）：
- 收尾阶段所有核均参与（profiling `aiv_time` 各核均非零，不再仅单核）。
- 收尾墙钟近似 ÷usedCoreNum（受聚合 HBM 带宽上限约束）。
- **判据**：收尾阶段 `usedCoreNum` 利用率提升到接近全核；若仍是单核 → 并行未生效，检查门控/核数。

边界：核数=1（退化单核，须不破坏）、核数 > 段数（尾核空）、totalElems 非对齐块倍数（极端尾块）、N≠1（验证 flat 等价或按 stride 切分）。

回退条件：收尾阶段 `usedCoreNum` 利用率未提升（仍是单核）→ 并行未生效；精度回归（多半是陷阱 C layout 错位或陷阱 A 对齐）；极端尾块越界崩溃（陷阱 B/对齐余量不足）。

与其它策略的关系：**requires 策略 01**（hard）——本策略前提是 workspace 单份共享。若仍是 per-core 私有副本，各核只读自己副本是天然并行，无需本策略；本策略专门解决"单份共享却被钉单核"的反模式。独立于搬运批量化策略（gather/scatter 侧）。

## 检索卡（短卡）

动作：去掉指定核门控，将收尾Pointwise由单核串行改为多核线性分段处理。
适用：阶段为无元素依赖、无跨元素归约的Pointwise，各核可写不重叠地址段。
限制：各核负责的[start,start+perCore)区间须互不重叠，且不得越界。
范围：Kernel收尾/Cast函数的输出阶段。
检索词：Pointwise、workspace、scale、Cast、myCoreIdx、designatedCore。
机会：仅一个核串行处理全量workspace，其余核直接返回。
