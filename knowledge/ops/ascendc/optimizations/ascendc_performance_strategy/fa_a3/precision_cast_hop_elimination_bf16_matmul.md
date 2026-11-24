---
type: Optimization
title: 消除 vec→cube 冗余 FP32 Cast 中转，matmul 改 bf16 直入（精度换取的搬运/算力节省）
description: 删除 vector 侧 bf16→FP32 workspace 中转，改由 cube 以 bf16 HMMA 累加到 FP32。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/03-precision-cast-hop-elimination-bf16-matmul.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：消除 vec→cube 冗余 FP32 Cast 中转，matmul 改 bf16 直入（精度换取的搬运/算力节省）

> **单一优化点：** 当一个 matmul 的输入在 vector 侧被 `Cast(bf16→FP32)` 落地到 GM workspace、cube 再从 GM 读 FP32 做 FP32 路径 matmul 时，**删掉这条 vector 侧 FP32 Cast 中转**，cube 直接从 GM 读原始 bf16 输入做 bf16 HMMA。省掉 vector 一次"读 bf16 + Cast + 写 FP32"的搬运/计算（≈2× 该张量流量 + V 计算开销）+ cube 的 FP32 装载开销（4B vs 2B，流量翻倍）。代价：bf16 HMMA 精度低于 FP32（丢低 16 位），极端大数值/scale 用例可能超 atol。**本策略是"精度换性能"取舍，非精度中性。**
>
> **算子/管线无关性：** 适用于 AscendC 任意"vector 预处理 Cast 到 FP32 落地 → cube FP32 matmul"且硬件支持 bf16 HMMA 的算子。不限于 attention。前提：算子精度红线允许该 matmul 用 bf16（输出 atol 容忍 bf16 HMMA 误差）。

---

## 1. 原理

该写法的病灶是**为"高精度 matmul"在 vector 侧多挂一条精度转换中转 hop**，而 cube 硬件原生就支持 bf16 HMMA（bf16 L0A/L0B → FP32 L0C），这条中转 hop 是冗余的流量与计算。

本策略利用的硬件机制：

| 机制 | 利用方式 |
|---|---|
| bf16 HMMA（硬件原生） | Cube 的 Mmad 原生支持 bf16 L0A/L0B → FP32 L0C（HMMA），无需 FP32 输入即可做 matmul |
| 去中转 | vector 不再 Cast 落地，cube 直接读原始 bf16 GM，少一条 vector 搬运+计算 hop |
| 流量减半 | cube 读 bf16（2B）而非 FP32（4B），L1/L0 装载流量 ÷2 |

定性 pipe 归因（相对）：vector 侧该输入张量的 `aiv_mte2`（读 bf16）+ `aiv_vec`（Cast）+ `aiv_mte3`（写 FP32 落地）消失；cube 侧 `aic_mte2` 读 bf16（流量 ÷2）。整体墙钟在该 Cast 中转是瓶颈时下降。

### 1.1 精度代价（必须显式评估）

bf16 HMMA 相比 FP32 path 丢低 16 位精度。影响程度取决于输入数值范围：
- **正常 scale（P 值小）**：bf16 表示精度足够，结果在 atol 内（PASS）。
- **大 scale / fp16 大数值输入**：数值大，bf16 误差累积超 atol（FAIL）。

**判据**：若算子精度红线允许该 matmul 用 bf16（绝大多数用例 PASS，仅极端边界 FAIL 且可接受），则适用；否则不适用。注意：若该算子存在一个"高性能版/参考实现"本就是 bf16 HMMA（无精度补偿），那是精度可接受的强证据——但其"无 FAIL"可能源于测试集差异（不含大 scale 用例），非精度魔法。

---

## 2. 性能问题模式（基线写法）

为"高精度 matmul"，vector 把 bf16 输入 Cast 成 FP32 落地，cube 做 FP32 path：

```text
# vector 侧（预处理后）：
DataCopy(ub, gm[bf16Input])                  # MTE2 读 bf16
Cast(fp32Ub, ub, bf16 -> fp32)               # V 转 FP32
DataCopy(gm[fp32Workspace], fp32Ub)          # MTE3 写 FP32（落地，供 cube 读）

# cube 侧：
LoadNdGmToNzL1(l1, gm[fp32Workspace])        # 读 FP32（FP32 装载，4B/元素）
... FP32 path Mmad ...
```

开销源：
- **vector 多一次完整搬运+计算**：读 bf16（2B）→ Cast → 写 FP32（4B），等于额外 2× 该张量流量（读 bf16 + 写 FP32）+ V Cast 计算。
- **cube FP32 装载**：FP32 元素 4B vs bf16 2B，L1/L0 装载流量翻倍。
- **GM workspace 占用**：FP32 中转 workspace 额外占环形槽。

典型症状：profiling 显示该 matmul 的输入张量在 vector 侧有额外 `aiv_mte2`（读 bf16）+ `aiv_vec`（Cast）+ `aiv_mte3`（写 FP32），cube 侧 `aic_mte2` 读 FP32。

核心改动：
```text
# vector 侧：删除 Cast 落地（预处理后不再 Cast 到 FP32）
# cube 侧：直接读 bf16 做 bf16 HMMA
LoadNdGmToNzL1(l1, gm[bf16Input])            # 读 bf16（原读 FP32 中转）
... bf16 Mmad (HMMA) ...
```

---

## 3. 正确性红线

### 3.1 精度边界
- bf16 HMMA 误差在正常 scale 用例 < atol（PASS）；大 scale/fp16 可能超阈（FAIL）。
- **必须跑全量精度**，确认 FAIL 仅限于可接受的边界用例（如大 scale），无其它新 FAIL。
- 边界用例的 max_abs 会变化（从 PASS 阈值内变 FAIL）——这是本策略的本质，**不算"精度回归"**（前提是用户接受该边界用例 FAIL）。

### 3.2 flag 同步保留（关键）
- vector→cube 的跨核 flag（如 `CrossCoreSetFlag<...>`）**必须保留**：cube matmul 仍依赖 vector 预处理完成（输入在 GM 就绪）。删 Cast 不等于删数据依赖。

### 3.3 复用已有 bf16 matmul 内核须匹配语义
- 关键：cube 侧通常已有 bf16 matmul 内核（本算子另一处 matmul 本就是 bf16）。改 bf16 即**复用同款 bf16 内核**，无需新写。
- 判别：核对复用的 bf16 内核的 M/N/K 切分、左右矩阵来源（转置与否）、L0C 结构与该 matmul 语义一致，否则维度错。

### 3.4 HF32 模式状态
- 原 FP32 path 若用 `SetHF32Mode(DISABLE)`，改 bf16 后须确认 HF32 模式状态不影响后续 matmul（保持一致）。

### 3.5 已知陷阱
- **误删跨核 flag**：删 vector Cast 时顺手删了 vector→cube flag → cube 读到未完成预处理的输入 → 间歇性错值/NaN（竞态）。修复：Cast 删，flag 保留。
- **精度边界用例 FAIL 当回归**：把 bf16 导致的边界用例 FAIL 当成"精度回归"回退。诊断：本策略本质降精度，边界 FAIL 预期；判据是"是否有边界之外的新 FAIL"。修复：明确精度红线（哪些 FAIL 可接受），只回退边界之外的新 FAIL。
- **FP32 path 与 bf16 path 内核不等价**：复用的 bf16 内核与原 FP32 matmul 的 M/N/K 切分、L0C 结构不一致 → 维度错。修复：核对 bf16 内核参数与该 matmul 语义一致。
- **HF32 模式残留**：改 bf16 后 HF32 状态影响后续 matmul。修复：保持 HF32 状态一致。

---

## 4. 泛化条件

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| matmul 输入有 FP32 Cast 中转 | vector 把 bf16 Cast 到 FP32 落地、cube 读 FP32（§2 模式） |
| 硬件支持 bf16 HMMA | Cube Mmad 支持 bf16 L0A/L0B |
| 精度红线允许 | 该 matmul 用 bf16 后，绝大多数用例在 atol 内；仅极端边界 FAIL 且用户接受 |
| 已有 bf16 内核可复用（优先） | 算子另一处 matmul 已是 bf16 HMMA → 直接对齐复用 |

优先适用：
- matmul 输入张量大（Cast 中转的 2× 流量 + V 开销可观）。
- 该 matmul 是 vector 侧搬运瓶颈的一部分。
- 高性能版/参考实现已是 bf16 HMMA（证明精度可接受）。

不适用：
- 精度红线严格（所有用例须 PASS，含大 scale/fp32），且 bf16 HMMA 误差超阈。
- matmul 输入本就需 FP32 精度（如累加链中对精度敏感的关键 matmul）。
- 硬件不支持 bf16 HMMA。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| **vector 侧（预处理）** | 删除 `Cast(bf16Input → fp32Workspace)` 调用（各输入张量一处） |
| **cube 侧（matmul）** | 从 FP32 path（`SetHF32Mode(DISABLE)` + FP32 装载 + FP32 Mmad）改为 bf16 path（直接 `LoadNdGmToNzL1` 读 bf16 原始 GM + bf16 Mmad），优先复用算子已有的 bf16 内核 |
| tiling / Host | **不改**（FP32 中转 workspace 分配可保留不读写，或后续清理） |
| 跨核同步 | **不改**（vector→cube 的 flag 仍需保留，因 cube 仍依赖 vector 预处理完成） |

### 5.2 关键代码模式（通用前/后对比）

**vector 侧（删除）**：
```text
# 前：预处理后 Cast 到 FP32 落地
Cast(fp32WorkspaceA, bf16InputA)            # 输入A → FP32   ← 删
Cast(fp32WorkspaceB, bf16InputB)            # 输入B → FP32   ← 删
CrossCoreSetFlag<...>(flag)                  # flag 保留

# 后：不再 Cast，cube 直接读 bf16 原始 GM
CrossCoreSetFlag<...>(flag)                  # 仅保留 flag
```

**cube 侧（改 path）**：
```text
# 前：FP32 path
SetHF32Mode(HF32Mode::DISABLE)
Fp32Matmul(... reads fp32WorkspaceA/B ...)   # 读 FP32 中转

# 后：bf16 path（复用已有 bf16 内核）
const kTiles = kDim / BLOCK_N
LoadToLeftL1(bf16InputA, kDim)               # 读 bf16（原读 FP32 中转）
Bf16MatmulInner(isLeftMatmul=true, ...)       # 读 bf16，bf16 Mmad
```

### 5.3 死代码清理（可选收尾）
- FP32 中转 workspace 在删 Cast 后全程不读写，但仍占 GM 环形槽。可顺手清理（省 GM），但**非本策略必需**（保留不影响正确性，只浪费 GM）。

---

## 6. LLM 前置问题

| 问题 | 必填内容 |
|---|---|
| 中转模式 | 哪个 matmul、vector 侧哪处 Cast 落地、cube 哪处读 FP32？ |
| 硬件 | 是否支持 bf16 HMMA？ |
| bf16 内核 | 算子是否已有 bf16 matmul 内核可复用？参数是否匹配该 matmul 的 M/N/K 与转置语义？ |
| 精度红线 | 哪些用例 FAIL 可接受（scale/dtype 边界）？全量精度预期几 PASS/FAIL？ |
| flag | vector→cube 跨核 flag 是否保留？ |
| 基线 | 修改前 build/精度/perf 基线 |

任一项无法回答，不实施。

---

## 7. 验收标准

```bash
bash <build_script> --soc=<soc> --op=<op>
bash <build_script> --soc=<soc> --op=<op> --wheel
source <set_env>
pytest <op>/test/test_<op>_*.py
```

精度：除明确接受的边界用例外全 PASS；边界用例（如大 scale）FAIL 且 max_abs 变化符合预期（bf16 误差量级）。不得出现边界之外的新 FAIL。

性能（**用 profiling 归因**，相对）：
- vector 侧该输入张量的 `aiv_mte2`（读 bf16）+ `aiv_vec`（Cast）+ `aiv_mte3`（写 FP32）消失。
- cube 侧 `aic_mte2` 读 bf16（流量 ÷2）。
- **判据**：vector 侧 Cast 三件套消失 + cube 装载流量减半；若 vector 侧 `aiv_mte2`/`aiv_mte3` 未降，说明该 Cast 中转非瓶颈。

边界 shape：不同 scale（小 scale PASS / 大 scale FAIL）、不同 dtype（bf16/fp16）、不同 K 维（影响装载流量）。

回退条件：边界用例之外出现新 FAIL（bf16 误差超预期）；正常 scale 用例 FAIL（说明 bf16 内核复用错误，或精度确实不够）；性能未提升（Cast 中转非瓶颈）。

与其它策略的关系：独立于 workspace/cast/搬运策略（01/02/04/05）。与同类"为速度降精度"取舍族（如降另一处 matmul 的 P/dS 精度）可叠加，但叠加后精度边界用例 FAIL 范围可能扩大，须重测。与"删无计算的中转 DataCopy hop"类策略机制相关但精度维度不同（本策略删的是有计算的精度转换中转）。

## 检索卡（短卡）

动作：删除 vector 侧 bf16→FP32 workspace 中转，改由 cube 以 bf16 HMMA 累加到 FP32。
适用：vector 将 bf16 转成 FP32 落盘，cube 再读取 FP32 时适用。
范围：vector 预处理到 cube matmul 的输入通路。
检索词：bf16 HMMA、FP32 Cast、GM workspace、L0A/L0B、FP32 L0C。
机会：matmul 前存在 vector Cast 落盘与 cube FP32 路径组成的额外中转 hop。
代价：大 scale 或 fp16 情况可能超过误差阈值。
