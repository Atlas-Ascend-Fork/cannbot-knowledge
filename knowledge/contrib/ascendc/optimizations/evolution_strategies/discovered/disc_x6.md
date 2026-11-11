---
type: Optimization
title: "X6: Merge Partial + Reduce Kernel for Split-KV FlashDecode"
description: "Split-KV FlashDecode 的 partial+reduce 两阶段在 reduce 计算量小、launch 头开销占比高时，可把最后一次归约内联到 partial kernel，由指定 block 完成状态合并并写回，从而合并为一次 launch。"
tags:
  - task.optimization
  - topic.attention
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T15:50:00Z"
platforms:
  - a2
---
# Strategy X6: Merge Partial + Reduce Kernel for Split-KV FlashDecode

## 核心思路

在 Split-KV FlashDecode 实现中，算子通常拆分为两个独立的 kernel launch：

1. **partial kernel**：每个 (task, split) 单元独立扫描其 token 子区间，
   产出 online-softmax 的中间状态 `(m, l, acc[D])` 并写入 workspace；
2. **reduce kernel**：读取所有 split 的中间状态，执行 online-softmax 合并，
   得到最终输出。

当 batch/head 数较小、seq 较短或 `splitKv` 不大时，reduce kernel 的**实际计算量很小**，但其独立 launch 带来固定的头开销以及 workspace 二次读取的延迟。此时可将 reduce 阶段的最后一次归约内联到
partial kernel 内部，由指定的 block（如每个 task 的最后一个完成单元，或一个
独立的合并 block）在 partial 计算完成后直接完成状态合并并写回输出，从而将
两次 kernel launch 合并为一次。

## 适用场景

- **算子类型**：Split-KV FlashDecode、TurboQuant decode、任何采用
  "partial + reduce" 两阶段结构的 attention/softmax 类算子。
- **瓶颈类型**：
  - profiling 显示 reduce kernel 的 `Task Duration` 中头开销占比高；
  - 或 reduce kernel 整体耗时与 partial kernel 计算耗时相当；
  - 或 workspace 写入/读取成为次要瓶颈。
- **推荐触发条件**：
  - `numTasks * splitKv` 较小，导致 reduce kernel 核利用率低；
  - 单条 seq 长度不长，reduce 阶段的计算量远小于 launch 开销；
  - 已确认 partial kernel 结束后所有 split 结果按 `(task, split)` 连续存放。

## 前提条件

1. workspace 布局已知且连续：每个 task 的 `splitKv` 个 slot 依次存放
   `[m, l, pad x6, acc[D]]`，总大小为 `numTasks * splitKv * (D + 8)` floats。
2. partial kernel 的 block 分配逻辑允许某个 block 在自身任务完成后，
   继续读取同一 task 的其他 split 结果（通常通过 `GetBlockIdx()` 与 task/split
   映射实现）。
3. 输出 buffer 与 workspace 无地址重叠，或可通过 barrier 保证写顺序。
4. 需验证精度：online-softmax 的合并公式（rescale + weighted acc）与独立
   reduce kernel 逐比特一致。

## 实现要点

### 方案 A：指定合并 block（推荐）

保持 partial kernel 的 block dim 不变，额外分配 `numTasks` 个 block
（或复用因 splitKv 较小而空闲的 block）作为 reduce worker：

```cpp
// Host 侧
uint32_t partialDim = std::min(totalUnits, aivCoreNum);
uint32_t reduceDim  = numTasks;  // 每个 task 一个合并 block
uint32_t blockDim   = partialDim + reduceDim;

// Device 侧：blockIdx < partialDim 走 partial 路径
//            blockIdx >= partialDim 且 < partialDim + reduceDim 走 reduce 路径
```

优点：不修改 partial 循环体，仅在 kernel 末尾增加一个分支；
缺点：总 block 数可能超过核数，导致部分 block 排队。

### 方案 B：最后一个 split 单元兼任 reduce

在 partial kernel 中，每个 task 的最后一个 split 单元在完成自身 partial
计算后，不立即退出，而是读取同一 task 的其他 split 结果并完成 reduce。
该 block 已拥有该 task 的最新 online-softmax 状态，可直接作为归约起点。

```cpp
int64_t unit = (int64_t)GetBlockIdx();
int64_t task = unit / splitKv;
int64_t split = unit % splitKv;
bool isLastSplit = (split == splitKv - 1);

ComputePartial(task, split, workspace);

if (isLastSplit) {
    // 等待同 task 的其他 split 写入完成
    // 可通过 HardEvent 或 GM 写入顺序保证
    MergeSplitsAndStore(task, workspace, output);
}
```

优点：不增加额外 block；
缺点：需要显式同步（如 `PipeBarrier<PIPE_ALL>` + GM 可见性保证），
且最后一个 split 的运行时间变长，可能拖累整体 wall-clock。

### 同步建议

- 若采用方案 A，reduce block 与 partial block 之间天然不存在写后读冲突
  （partial 先全部完成，reduce 后启动），但因为在同一个 kernel launch 内，
  需要确保 partial 的 workspace 写入对 reduce block 可见。可在 reduce 分支
  开始前插入 `PipeBarrier<PIPE_ALL>` 或 `SyncAll()`。
- 若采用方案 B，建议通过 `SetFlag/WaitFlag<HardEvent::MTE2_V>` 或
  `PipeBarrier<PIPE_ALL>` 确保同一 task 的其他 split 的 workspace 写入已完成。

## 常见陷阱

⚠️ **同步错误**：partial 写 workspace 与 reduce 读 workspace 的顺序必须严格保证，
否则会出现精度错误（旧的 m/l/acc 被用于归约）。

⚠️ **精度回归**：online-softmax 合并的 rescale 顺序、空 split 处理（`m=-inf, l=0`）
必须与独立 reduce kernel 完全一致。

⚠️ **核利用率下降**：方案 A 增加 block 数可能导致排队；方案 B 使最后一个 split
block 成为瓶颈。需根据实际 shape 选择。

⚠️ **UB 压力**：reduce 分支需要额外分配读取 workspace 的 buffer，需确认
UB 容量（尤其是 MSE 路径已占用较大 UB 时）。

⚠️ **不适用于大 splitKv**：当 `splitKv` 较大时，reduce 阶段的计算量
足以掩盖 launch 开销，合并收益有限，且可能因同步复杂度导致劣化。

## 代码搜索关键词

```bash
grep -n "tq_decode_partial\|tq_decode_reduce\|EXEC_KERNEL_CMD\|splitKv" \
    op_kernel/*.cpp op_host/*.cpp

grep -n "workspace\|wsGm_\|splitKv_" op_kernel/*.cpp

grep -n "GetBlockIdx\|usedCoreNum\|tasksPerCore\|blockDim" \
    op_kernel/*.cpp op_host/*.cpp
```

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。

## 补充判据（跨算子复核）

- **combine 段可以做二维并行**：kernel1 变快后，combine 的逐 split 串行加权求和会成为独立可回收段；按 `split_groups` 把每组的 `splits/ng` 个 partial 并行归并，再做一级小归并，多 split case 可再 +2.5%。
- **单遍 online softmax 归并**：把 combine 的两遍 safe-softmax 合成单遍流式归并，并对 `part_m/part_l/part_o` 的 GM 读做双缓冲，可把 per-split 成本从约 0.70us 降到约 0.4us；单遍实现复杂，先在 kernel2 单独改、kernel1 逐 byte 保留时验证。
