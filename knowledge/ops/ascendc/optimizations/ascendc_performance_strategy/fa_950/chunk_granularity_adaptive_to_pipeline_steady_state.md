---
type: Optimization
title: 分块粒度按"每核任务数是否留有流水稳态余量"自适应
description: 在减少块数的同时，以 totalWork 和每核任务数约束 chunk 粒度，避免无脑增大。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/04-chunk-granularity-adaptive-to-pipeline-steady-state.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：分块粒度按"每核任务数是否留有流水稳态余量"自适应

> **单一优化点：** 当一个归约轴被切成固定大小的 chunk、而每个 chunk 都要付一份**与 chunk 内数据量无关的固定开销**（元数据读取、跨核 flag 往返、批同步、online 合并等）时，把"固定的 chunk 大小"改为**按每核任务数自适应**：并行度充裕时用**更大的 chunk**（更少的块 ⇒ 更少的固定开销），并行度紧张时**保持原有块数**（保证每核任务数不跌破软流水稳态所需）。
>
> **判据（本策略的核心）：** `totalWork = outerWork × chunk数`，`每核任务数 = totalWork / coreNum`。合并后必须满足 `每核任务数 ≥ RING_SLOTS + 1`（流水深度 + 1 的余量），否则软流水进不了稳态，跨核 flag 往返全裸露在关键路径上，损失远大于省下的固定开销。
>
> **已验证锚点：** A5(Ascend950DT) SparseFlashAttention，`topK ∈ (512,1024]` 的 chunk 大小由恒定 256 改为 256/512 二选一。同一改动在两个用例上**方向相反**：
> - `prefill_bnsd_b2_s1024`（`outerWork=16384`，充裕）：`12481 → 11259µs`，**−9.8%** ✅
> - `decode_bnsd_dk576_b32`（`outerWork=32`，紧张）：`43.2 → 54.0µs`，**+25%** ❌
>
> 按判据二选一后：前者拿到 −10.2%，后者走回 256 分支、逐字节不变。
>
> **反向边界（重要）：** 继续把 chunk 合并到"单块"（1024）会因 **workspace 工作集跨出缓存容量**而产生 **30% 双峰分布**，见 §6。合并不是越多越好。

本策略只改"归约轴的分块粒度选择规则"。不改变每块内部的计算、不改变 online 合并的数学、不改 kernel 逻辑（纯 host tiling 侧）。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

把长归约轴（KV 序列、topK、reduce 维）切成 chunk 逐块处理时，每块的成本是：

```text
cost(chunk) = 数据相关成本(∝ chunk 大小)  +  固定开销(与 chunk 大小无关)
```

固定开销的典型来源：

| 来源 | 说明 |
|---|---|
| 元数据读取 | 每块都要读一次索引/长度/掩码等控制数据 |
| 跨核同步 | 每块一轮 `CrossCoreSetFlag/WaitFlag` 往返 |
| 批同步 | 每块内的 WAR/RAW 事件 |
| online 合并 | flash-attention 类算法每多一块就多一次跨块 rescale + 合并 |
| 操作数重载 | 每块可能重载一次不变操作数（如 Q） |

块数 = `ceil(轴长 / chunk大小)`。**块数减半 ⇒ 固定开销减半。**

### 1.2 但为什么不能无脑加大 chunk

减小块数会同时减小 `totalWork`：

```text
totalWork = outerWork × 块数        // outerWork = 天然并行维度的乘积，如 B×N×S
每核任务数 = totalWork / coreNum
```

软流水（ring pipeline，深度 `RING_SLOTS`）需要**每核任务数 > 流水深度**才能进入稳态。若每核任务数跌到 ≤ `RING_SLOTS`，流水永远处于填充/排空阶段，跨核 flag 的往返延迟**全部裸露**在关键路径上。

实例：`RING_SLOTS=3`，decode 场景 `outerWork=32`、32 核：

| chunk | 块数 | totalWork | 每核任务数 | 结果 |
|---|---|---|---|---|
| 256 | 4 | 128 | **4**（> 3，有余量） | 43.2µs ✅ |
| 512 | 2 | 64 | **2**（< 3，进不了稳态） | 54.0µs ❌ +25% |

### 1.3 本策略的判据

```cpp
const uint64_t needTasks  = coreNum * (RING_SLOTS + 1);      // 稳态 + 1 的余量
const uint64_t tasksIfBig = outerWork * ceilDiv(axisLen, BIG_CHUNK);
return (tasksIfBig >= needTasks) ? BIG_CHUNK : SMALL_CHUNK;
```

即：**只有当"用大 chunk 之后每核任务数仍留有稳态余量"时，才用大 chunk。**

`+1` 的余量是经验值：恰好等于 `RING_SLOTS` 时流水刚好填满但无冗余，任何抖动都会打断稳态。

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 分块存在 | 某归约轴被切成多块顺序处理 |
| 固定开销可辨识 | 每块存在与块内数据量无关的开销（§1.1 列表） |
| 并行度可算 | `outerWork`、`coreNum`、`RING_SLOTS` 在 host tiling 阶段已知 |
| 软流水 | kernel 使用固定深度的 ring 流水 |
| 合并安全 | 块数变化不破坏数值语义（online 合并的数学与块数无关） |
| 容量安全 | 大 chunk 对应的 workspace/片上 buffer 仍在容量与**缓存**限内（§6） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- 同一算子在不同 shape 下并行度差异极大（decode `outerWork` 小 / prefill `outerWork` 大）。
- 固定开销占比可估算且不小。

不适用：

- 块数由精度约束硬性限制（如 online 合并次数上限，见 §5.2）。
- 块大小同时决定片上 buffer 尺寸，且已接近容量上限。
- 归约轴很短（只有 1~2 块），无合并空间。

---

## 3. 实施步骤

### 3.1 识别固定开销

逐项列出每块要做的、与块内数据量无关的工作，估算其占比。若占比 <5%，本策略收益有限。

### 3.2 把并行度信息传入分块函数

分块选择函数原本可能只依赖轴长：

```cpp
// 改前
inline uint32_t SelectChunkSize(uint32_t axisLen);

// 改后：加入并行度参数
inline uint32_t SelectChunkSize(uint32_t axisLen, uint64_t outerWork, uint32_t coreNum);
```

调用点传入 `outerWork = B × N × S`（**天然并行维度的乘积，不含被分块的轴**）与实际 `coreNum`。

### 3.3 实现判据

```cpp
inline uint32_t SelectChunkSize(uint32_t axisLen, uint64_t outerWork, uint32_t coreNum)
{
    if (axisLen <= SMALL_CHUNK) {
        return alignUp(axisLen, FRACTAL_ALIGN);   // 单块，无需选择
    }
    if (axisLen <= BIG_CHUNK * 2) {
        const uint64_t needTasks  = (uint64_t)coreNum * (RING_SLOTS + 1);
        const uint64_t tasksIfBig = outerWork * ceilDiv(axisLen, BIG_CHUNK);
        return (tasksIfBig >= needTasks) ? BIG_CHUNK : SMALL_CHUNK;
    }
    return BIG_CHUNK;   // 更长的轴：块数本就多，直接用大块
}
```

### 3.4 同步核对 workspace 与片上容量

chunk 变大 ⇒ 相关 workspace 单槽尺寸同比放大。必须：

1. 重算 workspace 总量；
2. **检查是否跨出缓存容量**（§6 是本策略最容易翻车的地方）；
3. 检查依赖 chunk 大小的片上 buffer（如 softmax 工作区行数）是否仍在限内。

---

## 4. 正确性红线

### 4.1 数值语义与块数无关

- online 合并（flash-attention 类）必须满足"任意分块方式结果一致"。
- 若合并实现依赖"块数固定"，本策略不适用。

### 4.2 分核单位

- 若同一归约链的多个块必须由同一核连续处理（跨块状态传递），分核必须以**块组**为单位，不能从中间切开。
- chunk 大小变化会改变块组大小，须同步核对分核逻辑。

### 4.3 对齐约束

- 新 chunk 大小必须满足原有的所有对齐约束（fractal 对齐、下游 `dstStride` 约束等）。

### 4.4 精度：合并次数减少是安全方向

- 每多一次跨块 online 合并就多一次舍入累积。**减少块数是精度上的有利方向**。
- 反之，若为并行度而**增加**块数，须检查精度红线（见 §5.2）。

---

## 5. 已知陷阱

### AP-001：只看固定开销，不看并行度

问题：直接把 chunk 调大，未检查每核任务数。
症状：并行度紧张的 shape **大幅劣化**（实测 +25%）。
修复：§1.3 判据，二选一而非一刀切。

### AP-002：`outerWork` 算错

问题：把被分块的轴也算进 `outerWork`（重复计入）。
症状：判据永远为真，退化成一刀切。
修复：`outerWork` 只含**天然并行维度**，不含被分块的轴。

### AP-003：忽略 workspace 跨缓存（本策略最大的坑）

问题：只检查"容量是否放得下"，未检查"工作集是否还在缓存内"。
症状：**双峰分布**——同一二进制多次运行结果在两个值之间跳（实测 30% 摆幅）。
修复：§6。

### AP-004：为并行度反向增加块数

问题：并行度不足时，试图**增加**块数来填满流水。
症状：全面劣化——每多一块就多一份固定开销 + 一次 online 合并，计算量线性放大，代价远超填满流水的收益。
澄清：填满流水应靠**不增加计算量**的方式（如归约轴分核后二次归约），而非细分。

### AP-005：违反精度红线

问题：块数增加导致 online 合并次数超限。
症状：fp16 下舍入累积超容差（实测某场景切 7 块时 `max_abs 5.74e-3` 越过 `5e-3` 容差）。
修复：设置块数上限常量并注释红线来源。

---

## 6. 反向边界：合并到"单块"会翻车

**自然的下一步想法**：既然合并有收益，并行度充裕时干脆合并到单块（连最后一次 online 合并也省掉）。

**实测证伪。** 单次测量看似 −4.7%，但同一二进制重复测 3 次：

| run | 对照用例（不受影响） | 受影响用例 |
|---|---|---|
| 1 | 1358.3 | 10764 |
| 2 | 1359.3 | **13410** |
| 3 | 1357.9 | **13953** |

对照例摆幅 0.1%，受影响用例摆幅 **30%，呈双峰**。均值实际**劣于**二选一方案。

**根因**：chunk 翻倍使中转 workspace 单核占用翻倍（实例：单核 768KB，整体约 30MB，而原方案约 15MB）。该 workspace 是"写→读"的往返中转区，工作集一旦跨出缓存容量，命中与否随分配位置横跳，形成双峰。

**教训**：

1. 抬高分块粒度必须**连带核查 workspace 是否还在缓存内**——它同时是分块粒度和中转区尺寸，只算"容量放得下"是不够的。
2. **单次采样不足以支撑结论**。本例单测 −4.7% 是分布左端的运气采样。必须重复 ≥3 次看分布。

---

## 7. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 固定开销 | 逐项列出每块的固定开销及估算占比 |
| 并行度 | `outerWork` 表达式（不含被分块轴）、`coreNum`、`RING_SLOTS` |
| 每核任务数 | 各候选 chunk 下的 `totalWork/coreNum` 值 |
| 判据 | 余量取多少（推荐 `RING_SLOTS+1`）及理由 |
| workspace | 各候选 chunk 下的 workspace 总量；**是否仍在缓存内** |
| 片上容量 | 依赖 chunk 的片上 buffer 尺寸是否仍在限内 |
| 数值语义 | online 合并是否与块数无关 |
| 分核单位 | 块组是否会被核边界切断 |
| 精度红线 | 是否存在合并次数上限 |
| 对照例 | 是否有不受本改动影响的用例可作对照 |
| 基线 | 修改前基线值，**重复 ≥3 次** |

任一项无法回答，不实施本策略。

---

## 8. 禁止事项与回退条件

禁止：

- 不看并行度就一刀切调大 chunk（AP-001）。
- `outerWork` 把被分块轴计入（AP-002）。
- 只查容量不查缓存（AP-003 / §6）。
- 为填满流水而**增加**块数（AP-004）。
- 用单次采样下结论（§6）。
- 改变 online 合并的数学。

回退或缩小策略的条件：

- 任一 shape 劣化 → 检查其每核任务数是否跌破余量。
- 出现双峰/大摆幅 → workspace 跨缓存（§6），退回小 chunk。
- 精度失败 → 检查合并次数红线（AP-005）。

---

## 9. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op> --wheel 2>&1 | grep -cE "error:"
source <set_env> && pytest <op>/test/test_<op>.py -q
# 性能：每个 shape 重复 ≥3 次，取样间隔足够长
```

精度：与基线一致（块数减少是精度有利方向）。

性能：

- 并行度**充裕**的 shape：下降（实测 −10%）；
- 并行度**紧张**的 shape：走回原分支，**逐字节不变**（应完全无变化）；
- **必须留一个不受本改动影响的对照例**（如轴长本就单块的 shape），其数值应在两次构建间保持一致——以此证明收益来自改动而非构建波动。

边界：并行度处于判据两侧的 shape 各测；`axisLen` 恰在分界点的 shape 各测。

性能结论须写清：

```text
本策略是"二选一"而非"一刀切"：同一改动在并行度充裕/紧张的 shape 上方向相反。
判据是每核任务数是否仍 ≥ RING_SLOTS+1。
合并不是越多越好——合并到单块会因 workspace 跨缓存产生双峰（见 §6）。
所有结论必须基于重复 ≥3 次的分布，而非单次采样。
```

## 检索卡（短卡）

动作：在减少块数的同时，以 totalWork 和每核任务数约束 chunk 粒度，避免无脑增大。
适用：归约轴被切成多块顺序处理。
限制：数值语义须与块数无关；online合并必须保证任意分块方式结果一致。
范围：KV 序列、topK 或 reduce 长归约轴的分块
检索词：chunk、归约轴、固定开销、totalWork、每核任务数、coreNum
机会：每个 chunk 存在与块内数据量无关的固定开销。
代价：增大 chunk 虽减少块数，也会降低 totalWork。
