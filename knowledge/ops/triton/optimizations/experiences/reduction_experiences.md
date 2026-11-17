---
type: Optimization
title: 归约优化经验聚合
description: 从 4 条 Reduction YAML 经验中蒸馏的核心优化模式：Split-K 并行归约、fp32 累加器与数值稳定性。
tags: [task.optimization, topic.compute.reduction, topic.precision, topic.implementation.atomic, topic.parallelism]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Reduction_Ops/sum.md
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Reduction_Ops/reduce.md
  role: supporting
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# 归约优化经验聚合

从 4 条 Reduction YAML 经验中蒸馏。归约优化的核心：fp32 累加防止溢出、Split-K 大维度并行、联合归约单遍完成。

## 共性模式

1. **fp32 累加器**：归约 sum/mean/var 必须 fp32，最终 cast 回目标 dtype
2. **单遍联合归约**：argmax+max、log-softmax+CE 在单 pass 完成
3. **Split-K**：K≥4096 时按核划分，atomic_add 合并部分和

## 经验汇总

| 经验 ID | 提升 | 核心优化 | 适用条件 |
|---------|------|----------|----------|
| [exp_reduce_split_001](#exp_reduce_split_001) | 35% | K 维按核划分 + atomic_add 归约 | K≥4096 |
| [exp_backward_sum_001](#exp_backward_sum_001) | 25% | 反向 sum 优化 | 反向传播 sum 归约 |
| [exp_sum_scale_001](#exp_sum_scale_001) | 20% | sum + scale 融合 | sum 后缩放 |
| [exp_reduction_fp32_001](#exp_reduction_fp32_001) | 30% | fp32 累加器 | fp16/bf16 输入 |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_backward_sum_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Element-wise Multiplication + Sum Reduction；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: HEAD_DIM=>=64; o_len=>=128；level: advanced
- **优化点**：
  - **vectorization_alignment**：Align BLOCK_SIZE_D to the hardware's vector width (e.g., 128 for fp16/bf16 on Ascend 910 series) to ensure the Vector Unit processes data efficiently without remainder handling, maximizing throughput for the element-wise multiplication.
  - **memory_coalescing**：Ensure the stride for the HEAD_DIM (stride_od, stride_dod) is 1 (contiguous). This allows the memory controller to issue contiguous load instructions, significantly reducing memory access latency compared to strided loads.
  - **block_size_tuning**：Increase BLOCK_SIZE_O to improve data reuse and hide memory latency. By processing more sequence elements per program ID, the kernel can better saturate the compute units while keeping the intermediate accumulation in registers or high-speed cache (L0C/UB).
- **性能提升**：25%
- **边界与说明**：This kernel computes the gradient for the scale parameter in normalization layers (e.g., RMSNorm backward). The current implementation is functionally correct but requires tuning of block sizes and alignment to achieve peak performance on Ascend hardware.
- **KKB 来源**：[reduction/exp_backward_sum_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/reduction/exp_backward_sum_001.yaml)

### exp_reduce_split_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Split-K Reduction；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: head_size_v=>=64; SPLIT_K=>=1；level: advanced
- **优化点**：
  - **vectorized_memory_access**：The kernel loads the partial accumulation matrix `acc_k` of shape [SPLIT_K, BLOCK_DV] and the statistics vectors `m_k`, `l_k` using vectorized loads. This coalesces memory accesses and significantly improves bandwidth utilization compared to scalar or loop-based loading.
  - **numerically_stable_aggregation**：Implements the online softmax reduction logic by first computing the global maximum `m_max` across all splits and then scaling the partial accumulations by `fast_expf(m_k - m_max)`. This prevents overflow/underflow that can occur when summing exponentials directly.
  - **efficient_tensor_reduction**：Utilizes `tl.sum` with axis=0 to aggregate the scaled partial results along the split-K dimension. This maps efficiently to the hardware's reduction units, minimizing instruction overhead for the summation step.
  - **stride_aware_addressing**：Calculates memory offsets using explicit stride parameters (`stride_ak`, `stride_abs`, etc.), allowing the kernel to support various data layouts (e.g., contiguous or strided heads) without requiring pre-transposition, thus saving memory bandwidth.
- **性能提升**：20%
- **边界与说明**：This kernel is the second stage of a Split-K FlashAttention implementation. It assumes the first stage has produced partial accumulations and statistics.
- **KKB 来源**：[reduction/exp_reduce_split_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/reduction/exp_reduce_split_001.yaml)

### exp_sum_scale_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Reduction Operations；Sum and Scale；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3；tensor_shape: nd；core_param: N=>=1024；level: advanced
- **优化点**：
  - **block_size_tuning**：Increase BLOCK_N from 128 to 1024 or 2048. This aligns better with the memory burst length and cache line size of the Ascend 910B series, significantly reducing the number of memory transactions and loop control overhead.
  - **vectorized_access**：Ensure that the tl.load operations for both input and weight pointers utilize the maximum vector width (e.g., 128 bytes) supported by the hardware. This maximizes memory bandwidth utilization, which is critical as the kernel loads two data streams simultaneously when scalebyw is enabled.
  - **loop_unrolling**：Apply loop unrolling to the main accumulation loop to minimize branch prediction penalties and instruction dispatch overhead, allowing the hardware pipeline to process data more efficiently.
- **性能提升**：30%
- **边界与说明**：The current implementation processes the entire array within a single program block (grid size 1). For large-scale arrays (N > 10000), it is highly recommended to refactor the kernel into a multi-block parallel reduction pattern to fully utilize the NPU cores.
- **KKB 来源**：[reduction/exp_sum_scale_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/reduction/exp_sum_scale_001.yaml)

### exp_reduction_fp32_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：fp16/bf16 累加溢出
- **核心优化**：归约累加使用 fp32，避免 fp16 溢出并保持精度
- **性能提升**：30%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)

### exp_reduction_logsumexp_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：logsumexp 数值不稳定
- **核心优化**：先减全局 max 再 exp，避免上溢/下溢
- **性能提升**：35%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)

### exp_reduction_cross_entropy_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：cross-entropy 计算
- **核心优化**：单 kernel 融合 log-softmax 与 CE，避免中间张量
- **性能提升**：30%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)

### exp_reduction_argmax_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：argmax 两遍扫描
- **核心优化**：一次遍历同时维护 max 与 argmax 索引
- **性能提升**：25%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)

### exp_splitk_reduction_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：大 K 并行（K≥4096）
- **核心优化**：K 维按核划分，部分和 atomic_add 归约
- **性能提升**：35%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)

### exp_splitk_two_pass_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：大 K 且 atomic 竞争严重
- **核心优化**：Phase1 写部分和，Phase2 全局规约
- **性能提升**：40%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)

### exp_cumsum_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：累加和/前缀扫描
- **核心优化**：使用 scan primitive 实现 cumsum
- **性能提升**：25%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)

### exp_histogram_reduction_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：直方图 atomic 竞争
- **核心优化**：原子 binning 前先在寄存器局部聚合，最后单次写回
- **性能提升**：25%
- **KKB 来源**：[ops/reduction.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/reduction.md)
