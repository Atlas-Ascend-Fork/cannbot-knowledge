---
type: Optimization
title: 跨任务不变操作数 L1 生命周期缓存（signature 命中 + gating）
description: 将不变操作数的逐任务加载改为仅在归约组开始时载入L1，并跨连续任务缓存。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/10-invariant-operand-l1-lifetime-cache.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：跨任务不变操作数 L1 生命周期缓存（signature 命中 + gating）

> **单一优化点：** 当连续任务属于同一归约组，且某个输入操作数在这些任务之间不变时，只在归约组开始时加载一次该操作数到 L1，在归约组最后一个任务使用完成后释放，避免任务化流水后重复搬运同一操作数。命中/重载判定用**任务签名（signature/task-key）比较**：连续命中同一签名则跳过 GM→L1 重载，签名变化强制重载。
>
> **原 03-cross-tile-operand-reuse-via-taskkey-cache 已并入：** 两个提取稿实为同一策略的两个半份——本策略（原 10）提供 signature 构造规则、sentinel 域证明、释放同步协议与 `not_applicable` 证据门禁；并入内容补充**内层迭代数阈值 gating**（小迭代数场景跳过装载会扰动 MTE2/MTE1 流水节拍、净劣化，必须 gate）与"命中时 `LoadData` 与其 `SetWaitFlag` 对整块跳过"的写法。
>
> **与"循环重排复用"/"装载外提"两类策略的区别：** 本策略是**跨 Cube 调用（跨 ring 迭代/跨任务）**的 L1 持久化复用——内层迭代由顶层调度/ring 驱动，非单个 MM 函数内的循环；复用靠签名命中而非循环重排或装载外提。三者层级不同：装载外提是单 MM 函数内 N 循环外提；循环重排是单 MM 函数内 M/N 层序重排；本策略是跨 ring 迭代/跨任务的缓存命中。

本策略适用于各类 attention-like kernel（含 GQA/MQA 与稀疏/反向变体）。典型对象包括 forward 中同一 query row block 的 Q tile，backward 中同一 dO/O/state tile，或多头潜空间类变体中同一 latent query tile，以及任意"内层迭代共享某 Cube 操作数"的流水（attention 的 `Q` 跨 KV-tile、卷积的 weight 跨 tile 等）。它服务于"连续任务流水"后的不变输入复用，但也可以独立用于任何连续 reduce-tile 任务流。

本策略只改"不变操作数的装载命中判断 + 跳过 + 生命周期管理"。不改变 L1 布局、L0A/L0B/L0C 结构、TQue 双缓冲、ring 流水、跨核同步、循环层序、M/N/K 维切分。

---

## 1. 性能问题模式

任务化前，一个外层 block 可能只加载一次不变操作数：

```text
load Q once
for kv_tile in K/V tiles:
  compute with same Q
release Q
```

任务化后，外层 block 被拆成多个 reduce tasks。如果每个 task 都重新加载不变操作数，会产生重复搬运：

```text
task(qBlock A, kv 0): load Q(A)
task(qBlock A, kv 1): load Q(A) again
task(qBlock B, kv 0): load Q(B)
task(qBlock B, kv 1): load Q(B) again
```

优化后：

```text
first task of group A: load Q(A)
next tasks of group A: reuse Q(A)
last task of group A: release Q(A)
```

收益来源是恢复任务化前的不变操作数搬运次数，同时保留连续流水带来的跨任务重叠。

---

## 2. 适用条件

必须同时满足：

| 条件 | 要求 |
|---|---|
| 归约组连续 | 同一归约组的 reduce-axis tasks 在同一 core 内连续生成 |
| 操作数不变 | 被缓存操作数的地址、shape、format、dtype 在该归约组内不随 reduce tile 改变 |
| 只被本核消费 | 缓存只在同一 core、同一 kernel、同一执行上下文中消费 |
| 生命周期边界明确 | 有可靠的 first/last reduce tile 标志或等价 group boundary |
| L1 容量足够 | 缓存操作数不会挤占必要的 K/V/P/dO 等流式 L1 buffer |
| 同步可证明 | 重新加载、复用和释放都有明确 happens-before |

优先适用：

- 连续任务流水把一个 query/row block 拆成多个 reduce tasks。
- 不变操作数较大，重复 GM->L1 成本可见。
- profiling 显示任务化后某类输入搬运量翻倍或明显上升。

不适用：

- 同一归约组 tasks 被跨 core 切分，且没有跨核缓存/归约协议。
- 操作数受 block-sparse、动态 mask、ragged sequence 影响而随 reduce tile 改变。
- 操作数只被一个 task 使用。
- 需要为缓存牺牲关键 double buffer，导致主流水回退。
- 同 task 的迭代在调度顺序中**不连续**（被其它 task 隔开）——此时签名命中不会发生，策略 no-op（无害但无收益）。
- 内层迭代数小且装载与计算重叠良好——须由 gating 关闭（见 §2.1）。

### 2.1 场景 gating（内层迭代数阈值，必须）

跳过装载同时跳过了伴生的 `SetWaitFlag<MTE1_MTE2>`/`<MTE2_MTE1>`，改变 MTE2/MTE1 的交错节拍：

- **内层迭代多（带宽主导）：** 装载是瓶颈，跳过省带宽，净收益。
- **内层迭代少（计算主导）：** 装载本与 Cube 计算良好重叠，跳过后 MTE2 空窗打乱重叠，**净劣化**（小迭代数场景实测出现过数个百分点的劣化）。

故按内层迭代数阈值 gate：

```text
innerCount = CeilDiv(内层轴总长, tile 长)         # 内层迭代数（attention 场景为 KV 轴 / s2 tile 数）
enableReuse = innerCount >= THRESH
reuse = cacheLoaded and (signature == cacheSignature) and enableReuse
```

阈值选取：在"内层迭代多（带宽主导）"与"少（计算主导）"的分界处。无 profiling 时取使大小两端都不劣化的值。验收时大/小迭代数两类场景都必须无劣化（§8）。

### `not_applicable` 证据门禁

host kernel launch: host 发起的一次 kernel 执行；它不等于 kernel 内部为计算流水构造的
internal reduce task。一次 launch 可以让每个 core 在核内循环执行多个逻辑 task，因此不得用
launch 次数、launch block 数或单个 host owner 直接推导 reduce group 只有一个 task。

若以 single-task 或“不存在跨 task 复用”为由判定本策略不适用，负面证明必须同时覆盖：

| 证据槽 | 必须证明的内容 |
|---|---|
| `host launch ownership` | host 如何划分 core/block 及其 task range，reduce group 是否保持同核 |
| `kernel task ownership` | kernel 如何构造、归属并依次执行内部逻辑 task，而不是只证明 host 发起了一次 launch |
| `reduce-task count` | 相关 shape 或声明支持域中，每个 group 的实际内部 task 数及其边界计算 |
| `per-task load` | 不变操作数的 load 位于每个内部 task、每个 group 还是整个 kernel，并给出实际加载次数 |

四项证据缺少任一项时，结论必须保持 `unknown`，不得判定整个策略 `not_applicable`。某个 shape 的
`reduce-task count == 1` 只说明该 shape 应回退；若支持域内存在多 task group，仍须继续评估策略。
若基线在每个内部 task 重复加载同一身份的操作数，这属于正面适用性证据，而不是跳过理由。

---

## 3. Group Signature

必须用纯函数构造缓存签名，不能依赖隐式当前状态。

示例：

```cpp
uint64_t MakeInvariantSignature(const AttentionTask &task) {
    return Pack(task.batch, task.qHead, task.kvHead, task.qRowStart, task.qRows);
}
```

规则：

- 签名必须包含决定 GM 地址和有效 shape 的全部维度。
- 签名的无效值必须落在有效签名域之外；若 `0` 表示未加载，则每个有效任务的签名必须证明非零，例如对每个 packed 维度使用 `+1` 编码，或改用 `UINT64_MAX` / `INVALID_SIGNATURE` 并证明有效签名不会取到该值。
- 必须显式检查首个合法任务（例如 `batch=0, head=0, qBlock=0`）不会生成无效签名；否则首个 group 会被误判为已缓存，跳过 GM->L1 load。
- GQA/MQA 必须同时考虑 qHead 和 kvHead 映射。
- 存在 latent/head group 的算子必须包含其中会影响地址的维度。
- FAGrad/SFAGrad 必须包含梯度累加目标或状态目标。
- tail 形状不同的任务不能共享同一签名。
- **key 位编码形式**（等价于 `Pack`）：`key = (bz << off1) | (head << off2) | seqPos`，各字段位宽按取值范围分配；task 变 → key 变 → 强制重载。签名比较须在 gating 开启时进行（§2.1）。

禁止：

- 不要只用 `qRowStart` 判断是否复用。
- 不要用 `seq % slot` 作为复用签名。
- 不要跨 batch/head/group 复用缓存。
- 不要把 `cacheSignature == 0` 当作未加载，除非 `MakeInvariantSignature(...)` 的实现和注释都证明所有有效签名非零。

---

## 4. 生命周期模板

状态：

```cpp
bool cacheLoaded = false;
uint64_t cacheSignature = INVALID_SIGNATURE;
LocalTensor<T> invariantL1;
```

准备：

```cpp
void PrepareInvariantOperand(const AttentionTask &task) {
    uint64_t sig = MakeInvariantSignature(task);
    if (cacheLoaded && cacheSignature == sig && innerCount >= THRESH) {
        return;                                   // 命中：跳过 LoadData 及其伴生 SetWaitFlag 对（整块跳过）
    }

    if (cacheLoaded) {
        ReleaseInvariantOperand();
    }

    WaitCacheFreeIfNeeded();
    invariantL1 = AllocOrGetL1Cache();
    LoadInvariantOperand(invariantL1, task);      // 未命中/首次/task 变：装载 + 更新签名
    WaitLoadReadyIfNeeded();

    cacheSignature = sig;
    cacheLoaded = true;
}
```

释放：

```cpp
void ReleaseInvariantOperandIfLast(const AttentionTask &task) {
    if (!task.isLastReduceTile) {
        return;
    }
    WaitAllConsumersDoneIfNeeded();
    FreeOrMarkL1CacheReusable(invariantL1);
    cacheLoaded = false;
    cacheSignature = INVALID_SIGNATURE;
}
```

调用位置：

```cpp
if (current.valid) {
    PrepareInvariantOperand(current);
    ComputeStageUsingInvariant(current);
    ReleaseInvariantOperandIfLast(current);
}
```

若实际消费者只在 `MatA` 阶段，释放点应在该归约组最后一个 `MatA` 发射并确认不再读取后；不要等到无关的后续 `VecD` 才释放。

---

## 5. 同步要求

必须建立三类顺序：

| 关系 | 要求 |
|---|---|
| load -> compute | MTE2/L1 load 完成后，MTE1/M 才能读取 |
| compute -> release | 最后一个消费者完成读取后，L1 cache 才能被覆盖或释放 |
| release -> next load | 新 group 覆盖同一 cache 前，旧 group 消费必须完成 |

可使用：

- 完整 TQue 生命周期表达 L1 tensor 的生产消费。
- TBuf + HardEvent 表达裸缓存的 ready/free。
- 项目已有封装，但必须展开确认真实 HardEvent 和 event id 生命周期。

禁止：

- 不要用普通 bool 替代跨流水 ready/free 同步。
- 不要把 `SetWaitFlag` 当作长期 slot 生命周期事件。
- 不要手写固定 event id，除非项目已有证明该 id 未冲突。
- 不要把 release 拆成“上一组 `isLastReduceTile` 只 `SetFlag<MTE1_MTE2>`、下一组 `needReload` 才 `WaitFlag<MTE1_MTE2>`”，除非已证明所有 Set 在 kernel 退出前必定被消费；单组、末组、tail 组没有下一次 reload，容易留下 orphaned Set 并导致 AIC pipe 无法 drain。
- 不要把“runtime 会清理最后一个 pending flag”作为正确性依据。最后一个消费者完成后必须有显式 drain，或使用完整 TQue 生命周期。
- 不要在 AIC/AIV 都可能访问该缓存时省略跨阶段协议。
- **命中分支不得残留半截同步**：跳过 `LoadData` 时必须连同其伴生 `SetWaitFlag` 对**整块跳过**（无 MTE2 写可等，留下 `SetWaitFlag<MTE2_MTE1>` 会造成 MTE2/MTE1 同步错位、流水扰动或偶发数值错）。命中时 L1 内容来自该组首次装载，其完成性已由首次装载的同步保证，SRAM 内容持久，无需再同步。
- **单缓冲隔离契约**：被复用缓冲须满足"仅本装载(MTE2)写、仅本 L0(MTE1)读"，连续同组迭代间同阶段其它 GM→L1 装载不得覆盖该缓冲；实施前逐阶段证明，不满足则不可套用。

推荐的裸 `TBuf + HardEvent` 释放写法：

```cpp
void ReleaseInvariantOperandIfLast(const AttentionTask &task) {
    if (!task.isLastReduceTile) {
        return;
    }
    int32_t ev = FetchEventID(HardEvent::MTE1_MTE2);
    SetFlag<HardEvent::MTE1_MTE2>(ev);
    WaitFlag<HardEvent::MTE1_MTE2>(ev);
    cacheLoaded = false;
    cacheSignature = INVALID_SIGNATURE;
}
```

若为了性能把 release 推迟到下一次覆盖前，必须在设计和 handoff 中列出 one-group / last-group / tail-group 的 Set/Wait 配对证明；证明缺失时不得采用延迟 Wait。

---

## 6. 与连续任务流水的关系

本策略常作为连续任务流水后的配套修复：

```text
连续任务流水：把 block 拆成多个 reduce tasks
本策略：避免每个 reduce task 重新加载同一不变操作数
```

实施顺序建议：

1. 先实现显式任务描述符和连续任务流水。
2. 验证正确性和性能。
3. 再单独实施不变操作数缓存。
4. 单独验证搬运量是否恢复到任务化前水平。

不要在同一提交里同时改变任务调度和缓存生命周期，否则精度问题很难归因。

---

## 7. 验收标准

正确性：

- 同一归约组所有 reduce tasks 读取同一缓存操作数。
- 不同 batch/head/qBlock/tail 不误复用。
- 全量精度通过，无随机 hang。
- signature sentinel 检查通过：首个合法 group 不等于 `INVALID_SIGNATURE`，所有有效签名不与未加载值冲突。
- sync balance 检查通过：`MTE1_MTE2` release/free 事件在单组、末组、tail 组中没有 orphaned Set，固定 event id 如被使用必须有完整配对证明。

性能：

- 不变操作数 GM->L1 搬运次数从 `reduce_tile_count` 降到 `1`，或降到理论必要值。
- AIC/AIV 搬运指令数不因任务化而增加。
- Task Duration 不回退；若回退，检查 L1 容量压力和 release 点。
- **大/小内层迭代数两类场景都必须无劣化**：大迭代数（`innerCount ≥ THRESH`）整体耗时与 `aic_mte2` 下降；小迭代数（`innerCount < THRESH`）gating 关闭、整体持平——小迭代数 case 劣化是硬失败，说明 gating 阈值或落点有误（§2.1）。

性能结论必须写清基线、gating 阈值与两类场景：

```text
本策略收益相对"每 reduce task 重装不变操作数"基线；判据是大迭代数 case 整体耗时 + aic_mte2 下降。
小迭代数 case 由 gating 关闭，不劣化是硬指标。后续策略须相对"本策略后"评估。
```

建议记录：

```text
invariant_operand_loads_per_group
expected_loads_per_group
GM->L1 bytes for invariant operand
L1 cache bytes
Task Duration
```

## 检索卡（短卡）

动作：将不变操作数的逐任务加载改为仅在归约组开始时载入L1，并跨连续任务缓存。
适用：同组reduce-axis任务在同一core连续生成，且输入操作数在任务间不变。
限制：L1缓存生命周期至少覆盖归约组最后一个任务使用完成。
范围：同一core内连续归约组任务的不变输入操作数。
检索词：归约组、reduce-axis tasks、同一core、不变操作数、L1生命周期缓存。
机会：外层block拆为多个连续reduce tasks，且它们复用同一不变操作数。
