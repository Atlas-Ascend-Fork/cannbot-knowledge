---
type: Optimization
title: Softmax 优化经验聚合
description: 从 7 条 Softmax YAML 经验中蒸馏的核心优化模式：Online Softmax 单趟算法、数值稳定化与前反向融合。
tags: [task.optimization, topic.compute.normalization, topic.precision]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Math_Ops/softmax.md
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/third_party/ascend/tutorials/06-fused-attention.py
  role: example
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# Softmax 优化经验聚合

从 7 条 Softmax YAML 经验中蒸馏。核心：Online Softmax 将两趟降为单趟，数值稳定化防止 exp 溢出。

## 共性模式

1. **Online Softmax**：维护 running max/sum，单 pass 完成
2. **升 fp32**：exp 前升精度 → 减 max → exp → sum
3. **反向利用导数性质**：`p * (dy - dot(p, dy))`

## 经验汇总

| 经验 ID | 提升 | 核心优化 | 适用条件 |
|---------|------|----------|----------|
| [exp_softmax_online_001](#exp_softmax_online_001) | 50% | 运行 m/l 迭代更新（Attention 内融合） | Flash Attention |
| [exp_softmax_inner_002](#exp_softmax_inner_002) | 30% | Online max+sum 单趟 | inner dim softmax |
| [exp_log_softmax_001](#exp_log_softmax_001) | 30% | max+sum → log-sum-exp 单核 | LogSoftmax 前向 |
| [exp_softmax_non_inner_001](#exp_softmax_non_inner_001) | 25% | 外层维度归约，转置处理 | 非 inner dim |
| [exp_softmax_backward_001](#exp_softmax_backward_001) | 25% | `p * (dy - dot(p, dy))` | inner dim 反向 |
| [exp_log_softmax_backward_001](#exp_log_softmax_backward_001) | 25% | `dy - softmax(x) * sum(dy)` | LogSoftmax 反向 |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_log_softmax_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；LogSoftmax；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: M=>=1; N=>=1; K=>=1；level: advanced
- **优化点**：
  - **two_pass_algorithm**：The kernel implements a two-pass strategy to handle the reduction over dimension N. The first pass iterates over N in tiles to compute the running maximum (m) and the sum of exponentials (z). The second pass iterates again to apply the log_softmax formula using the reduced values. This decouples the reduction phase from the element-wise computation phase, allowing the kernel to handle sequences (N) much larger than the SRAM/Cache capacity.
  - **numerical_stability**：It employs the "max trick" (Online Softmax algorithm) to prevent numerical overflow/underflow. By tracking the running maximum `m` and adjusting the exponential calculation as `tl.exp(inp - m_new)`, it ensures that values passed to the exponential function remain within a stable range, even before the final global maximum is known.
  - **tiled_memory_access**：The loop over the reduction dimension N is blocked by `BLOCK_N`. This ensures that memory loads from global memory are coalesced and occur in large, contiguous chunks, significantly improving memory bandwidth utilization compared to a scalar or strided access pattern.
  - **autotuning_configuration**：The kernel utilizes `@triton.autotune` with `runtime.get_tuned_config`. This allows the system to select the optimal `BLOCK_M` and `BLOCK_N` tile sizes at runtime based on the specific shapes of M and N, ensuring the kernel is performant across a wide range of input dimensions without manual tuning.
- **性能提升**：30%
- **边界与说明**：This implementation is optimized for scenarios where the reduction dimension N is large. The use of `pid_k` allows the kernel to batch process across the K dimension, effectively treating the input as a batch of matrices.
- **KKB 来源**：[softmax/exp_log_softmax_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/softmax/exp_log_softmax_001.yaml)

### exp_log_softmax_backward_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Reduction and Element-wise；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: M=>=128; N=>=128; K=>=1；level: advanced
- **优化点**：
  - **two_pass_algorithm**：The kernel separates the computation into two distinct passes a reduction pass to calculate the sum of gradients (scale) and a computation pass to derive the input gradients. This decouples the global reduction dependency from the element-wise calculation.
  - **block_tiling**：Utilizes 2D tiling with BLOCK_M and BLOCK_N to process data in chunks. This allows for vectorized memory loads and stores, significantly improving memory bandwidth utilization compared to element-wise processing.
  - **high_precision_accumulation**：The reduction variable 'scale' is explicitly initialized and computed using tl.float32. This ensures numerical stability during the summation of gradients, preventing overflow or underflow which is critical for softmax derivative calculations.
  - **mask_loading**：Implements boundary checks using masks during memory loads and stores. This ensures the kernel operates correctly even when the matrix dimensions (M, N) are not perfectly divisible by the block sizes.
- **性能提升**：25%
- **边界与说明**：The current implementation loads 'out_grad' twice (once for reduction, once for calculation). While this improves readability and reduces register pressure, it increases memory traffic. For memory-bound scenarios, consider caching 'out_grad' in software-managed cache (SRAM) if available or fusing the loops if register file permits.
- **KKB 来源**：[softmax/exp_log_softmax_backward_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/softmax/exp_log_softmax_backward_001.yaml)

### exp_softmax_backward_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Activation Operations；Softmax Backward；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: M=>=1; N=>=128；level: advanced
- **优化点**：
  - **two_pass_reduction_strategy**：The kernel decouples the computation into two distinct loops a reduction phase to compute the scale (sum of output * gradient) and an update phase to calculate the input gradient. This approach avoids the need to store intermediate results for the entire row in registers or scratchpad, which is critical for handling large N dimensions that exceed register capacity.
  - **explicit_cache_eviction_policy**：In the reduction loop, the `eviction_policy="evict_last"` argument is used for the `out` tensor. This explicitly instructs the memory subsystem to retain the loaded `out` data in the cache (L1/L2), as it will be accessed again in the subsequent update loop. This optimization significantly reduces global memory bandwidth pressure by maximizing data reuse across the two passes.
  - **adaptive_tiling_and_heuristics**：The kernel utilizes `triton.autotune` and runtime heuristics to dynamically select the optimal `TILE_M` and `TILE_N` based on the input shapes M and N. This ensures that the memory access patterns are fully coalesced and that the GPU occupancy is maximized for varying batch sizes and sequence lengths.
- **性能提升**：30%
- **边界与说明**：The `ONE_TILE_PER_CTA` path provides a fast-path for smaller N dimensions where the data fits in a single tile, bypassing the overhead of the two-pass loop structure.
- **KKB 来源**：[softmax/exp_softmax_backward_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/softmax/exp_softmax_backward_001.yaml)

### exp_softmax_inner_002

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Softmax Reduction；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3；tensor_shape: nd；core_param: M=>=1; N=>=TILE_N；level: advanced
- **优化点**：
  - **vectorized_accumulation_strategy**：The kernel employs a vectorized reduction strategy where intermediate max (m) and sum (z) values are maintained as vectors of size TILE_N instead of scalars within the reduction loop. This avoids expensive horizontal reduction operations (e.g., tl.max) inside the hot loop, replacing them with efficient element-wise operations (tl.maximum). The final reduction to a scalar is performed only once after the loop completes.
  - **online_softmax_algorithm**：Implements the numerically stable online softmax algorithm adapted for the vectorized strategy. It updates the running max and sum using the formula z = z * exp(m_old - m_new) + exp(x - m_new), ensuring stability against overflow/underflow for large input values.
  - **cache_eviction_policy**：Utilizes eviction_policy="evict_first" in the second pass (write-back). This optimizes L1 cache behavior by treating input data loads as transient, preventing them from polluting the cache and evicting the accumulator values or other critical data during the final normalization phase.
  - **loop_specialization_and_tiling**：The kernel tiles the reduction dimension N into blocks of TILE_N. It specializes the loop logic for the main body and the boundary (remainder) tiles. This removes redundant mask checks from the main loop body, significantly improving instruction throughput and reducing branch mispredictions.
- **性能提升**：30%
- **边界与说明**：This optimization is particularly effective for large N dimensions where the cost of horizontal reductions in the loop would be prohibitive. The vectorized approach leverages the full width of the vector units.
- **KKB 来源**：[softmax/exp_softmax_inner_002.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/softmax/exp_softmax_inner_002.yaml)

### exp_softmax_non_inner_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Softmax；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: N=>=128; K=>=64；level: advanced
- **优化点**：
  - **online_softmax_algorithm**：Implements the numerically stable online softmax algorithm within the reduction loop. It updates the running maximum (m) and sum (z) using the formulas m_new = max(m, inp) and z = z * exp(m - m_new) + exp(inp - m_new), allowing the reduction to be performed in chunks without storing the entire input tensor in registers.
  - **two_pass_strategy**：For reduction dimensions (N) larger than the tile size (TILE_N), the kernel employs a two-pass approach. The first pass iterates over N to compute the global max and sum, and the second pass iterates again to compute the final exponential and division values. This trades off memory bandwidth for reduced register pressure.
  - **heuristic_dispatch**：Utilizes the ONE_TILE_PER_CTA heuristic to dynamically select the kernel strategy at runtime. If N fits within TILE_N, it uses a faster single-pass load-compute-store path; otherwise, it falls back to the two-pass strategy for larger dimensions.
  - **vectorized_memory_access**：Loads data in tiles of (TILE_N, TILE_K), processing multiple elements of the K dimension simultaneously to maximize memory bandwidth utilization and ensure coalesced access patterns.
- **性能提升**：30%
- **边界与说明**：This kernel is optimized for softmax over the N dimension of a 3D tensor (M, N, K). The libentry decorator suggests integration with specific runtime environments.
- **KKB 来源**：[softmax/exp_softmax_non_inner_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/softmax/exp_softmax_non_inner_001.yaml)

### exp_softmax_online_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Softmax Reduction；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: BLOCK_M=>=64; BLOCK_N=>=64；level: advanced
- **优化点**：
  - **online_softmax_algorithm**：The kernel implements the online softmax algorithm by iteratively updating the running maximum (m_i) and the running sum of exponentials (l_i). This allows the softmax operation to be fused into the main attention loop without materializing the full $N \times N$ attention matrix in global memory, significantly reducing memory bandwidth pressure.
  - **numerical_stability**：The calculation `qk - m_ij[:, None]` subtracts the row-wise maximum before the exponential operation. This prevents floating-point overflow or underflow during the `tl.math.exp` calculation, which is critical for the stability of attention mechanisms in deep learning models.
  - **mixed_precision_storage**：The computation is performed in higher precision (implied float32 for accumulation), but the final result `p_cast` is cast to `Q.type.element_ty` (e.g., fp16/bf16) before storing to `WS2`. This optimizes shared memory usage and store throughput while maintaining sufficient numerical precision for the gradients.
  - **vectorized_reduction**：The use of `tl.max(qk, 1)` and `tl.sum(p, 1)` leverages hardware vector units to perform the reduction operations efficiently across the block dimension, minimizing the number of instruction cycles required for the reduction step.
- **性能提升**：35%
- **边界与说明**：This function is designed to be called within a loop (e.g., over K or N heads) in a FlashAttention-style kernel. It relies on `WS1` and `WS2` being pointers to fast shared memory (SRAM).
- **KKB 来源**：[softmax/exp_softmax_online_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/softmax/exp_softmax_online_001.yaml)
