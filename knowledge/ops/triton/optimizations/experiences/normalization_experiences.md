---
type: Optimization
title: 归一化优化经验聚合
description: 从 33 条 Normalization YAML 经验中蒸馏的核心优化模式：RMSNorm/LayerNorm/GroupNorm 的融合、列分块与
  Persistent Kernel 策略。
tags: [task.optimization, topic.compute.normalization, topic.compute.composite, topic.data_movement.memory_access, topic.precision]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Reduction_Ops/reduce.md
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/third_party/ascend/tutorials/05-layer-norm.py
  role: example
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# 归一化优化经验聚合

从 33 条 Normalization YAML 经验中蒸馏。归一化是 Transformer 中除 Attention/GEMM 外的第三大计算类别。

## 共性模式

1. **Column Blocking**：hidden_dim 超 UB 时分列处理，两次 pass（mean_sq → normalize）
2. **融合优先**：Skip Add / RoPE / QKV Split 与 Norm 在单 kernel 完成
3. **Persistent Kernel**：grid-stride loop，rows 远大于核数时固定 grid
4. **fp32 精度**：mean_sq 用 fp32 累加，`tl.rsqrt` 优于 `1/tl.sqrt`

## 高质量经验汇总

| 经验 ID | 提升 | 核心优化 | 适用条件 |
|---------|------|----------|----------|
| [exp_fused_rms_norm_001](#exp_fused_rms_norm_001) | 35% | 原地 residual 更新同时计算方差 | Skip Add + RMSNorm |
| [exp_fused_add_layernorm_001](#exp_fused_add_layernorm_001) | 30% | Skip + LN 融合单核 | Skip + LayerNorm |
| [exp_fused_norm_rope_001](#exp_fused_norm_rope_001) | 35% | Norm + RoPE 融合 | RMSNorm 后接 RoPE |
| [exp_fused_qkv_rmsnorm_rope_001](#exp_fused_qkv_rmsnorm_rope_001) | 40% | QKV+Norm+RoPE 三合一 | Attention QKV 投影 |
| [exp_gemma_rmsnorm_001](matmul_experiences.md#exp_gemma_rmsnorm_001) | 35% | (1+weight) 融合归一化乘法 | Gemma 风格 |
| [exp_fused_split_qk_norm_001](#exp_fused_split_qk_norm_001) | 35% | Q/K RMSNorm 单核融合 | Q/K 分别 Norm |
| [exp_groupnorm_001](#exp_groupnorm_001) | 25% | 分组归一化向量化 | GroupNorm |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_fused_add_layernorm_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Activation Operations；Fused Add + LayerNorm；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: n_rows=>=1; n_cols=>=1；level: advanced
- **优化点**：
  - **operator_fusion**：Fuses the element-wise addition (X + R), Layer Normalization (mean/variance calculation), and the affine transformation (scaling and shifting) into a single kernel launch. This significantly reduces the overhead of writing and reading intermediate tensors to and from global memory (HBM).
  - **precision_management**：Utilizes single-precision floating-point (float32) for the accumulation of mean and variance statistics to ensure numerical stability and prevent overflow/underflow, while performing the final arithmetic and storage in the input data type (e.g., fp16/bf16) to maximize throughput.
  - **loop_tiling_strategy**：Implements a 2D tiling strategy using `BLOCK_SIZE_M` for rows and `BLOCK_SIZE_N` for columns. This allows the kernel to process data in chunks that fit efficiently into the GPU/NPU's SRAM, reducing global memory access frequency and improving data reuse.
  - **heuristic_block_sizing**：Uses `@triton.heuristics` to dynamically configure `BLOCK_SIZE_M` based on the input tensor dimensions. This ensures that the number of launched programs is optimal for the specific hardware, maximizing occupancy and resource utilization.
  - **intermediate_streaming**：The kernel explicitly stores the intermediate sum (S) to global memory in the first pass and reloads it in the second pass. This design choice trades off some memory bandwidth for reduced register pressure, allowing the kernel to handle larger hidden dimensions (n_cols) that exceed register capacity.
- **性能提升**：30%
- **边界与说明**：This kernel is optimized for scenarios where the intermediate result S is required to be materialized in global memory or when the hidden dimension is too large for register tiling. For smaller dimensions where S fits in registers, a register-tiling approach would be more performant.
- **KKB 来源**：[normalization/exp_fused_add_layernorm_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_fused_add_layernorm_001.yaml)

### exp_fused_norm_rope_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Activation Operations；Fused RMSNorm and Partial RoPE；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: seq_len=>=1; num_heads=>=1; head_dim=>=64；level: advanced
- **优化点**：
  - **operator_fusion**：Fuses the RMSNorm and Rotary Positional Embedding (RoPE) operations into a single kernel. This eliminates the need to write intermediate normalized results to global memory (HBM) and read them back for RoPE, significantly reducing memory bandwidth consumption and latency.
  - **partial_rope_optimization**：Explicitly handles partial RoPE by separating the head dimension into ROPE (rotated) and NOPE (non-rotated) sub-spaces. The kernel only applies the computationally expensive rotation logic (cos/sin multiplication) to the ROPE dimensions, while the NOPE dimensions are simply normalized and scaled, optimizing arithmetic intensity for modern architectures like Llama-3.
  - **precision_management**：Utilizes single-precision floating-point (fp32) for the variance calculation (sum of squares and reciprocal square root) to maintain numerical stability during the reduction, while performing the rest of the vector operations in the input precision (e.g., fp16/bf16) to maximize throughput.
  - **grid_stride_scheduling**：Implements a grid-stride loop over the sequence length dimension. This allows the kernel to efficiently process sequence lengths of arbitrary size without requiring a 1:1 mapping between grid blocks and sequence tokens, ensuring high utilization of the compute units (NUM_CORES).
- **性能提升**：25%
- **边界与说明**：This kernel is specifically designed for models utilizing partial rotary position embeddings (e.g., Llama-3). It assumes the input layout is [seq_len, num_heads, head_dim].
- **KKB 来源**：[normalization/exp_fused_norm_rope_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_fused_norm_rope_001.yaml)

### exp_fused_qkv_rmsnorm_rope_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Fused QKV Split + RMSNorm + RoPE；data_type: bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: HEAD_DIM=>=64; batch_size=>=1；level: advanced
- **优化点**：
  - **operator_fusion**：Aggressively fuses Split, RMSNorm, Affine (Linear), and RoPE operations into a single kernel. This minimizes global memory access by keeping intermediate data in high-speed SRAM/Registers throughout the computation pipeline.
  - **precision_control**：Performs the variance calculation and reciprocal square root in FP32 (float32) to ensure numerical stability during normalization, while storing weights and activations in BF16 to optimize memory bandwidth and storage.
  - **rope_implementation**：Implements RoPE using `tl.extract_slice` and `tl.insert_slice` to handle the rotation of the first and second halves of the head dimension. This avoids complex indexing arithmetic within the inner loop.
  - **redundant_load_optimization**：The kernel currently loads `pos_idx`, `cos`, and `sin` inside both the Q and K processing loops. Since Q and K share the same position ID for a given token, these values should be loaded once per row iteration and reused to reduce global memory read pressure.
  - **vectorized_memory_access**：Utilizes block-level loading (`Q_BLOCK_SIZE`, `KV_BLOCK_SIZE`) to coalesce memory accesses, ensuring that consecutive memory transactions are handled efficiently by the memory controller.
- **性能提升**：25%
- **边界与说明**：The kernel processes Q, K, and V sequentially. While this improves data locality for the input tensor, the redundant loading of RoPE embeddings (`cos`/`sin`) for Q and K is a specific optimization target. Ensure `BLOCK_SIZE` is aligned with the hardware's cache line size (e.g., 128 bytes) for best results.
- **KKB 来源**：[normalization/exp_fused_qkv_rmsnorm_rope_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_fused_qkv_rmsnorm_rope_001.yaml)

### exp_fused_rms_norm_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Reduction Operations；Element-wise + Reduction；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093；tensor_shape: nd；core_param: N=>=1024；level: advanced
- **优化点**：
  - **kernel_fusion**：Fuses the residual addition (X+R), variance calculation (sum of squares), reciprocal root mean square computation, and final scaling/weight multiplication into a single kernel. This significantly reduces global memory access overhead by keeping intermediate data in high-speed memory (SRAM/Registers) and avoiding multiple kernel launch latencies.
  - **residual_inplace_update**：Optimizes the data path for Transformer architectures by writing back the intermediate sum (X+R) to the residual pointer R and the normalized output to X. This eliminates the need for a separate add kernel or extra memory allocation for the residual connection, effectively halving the memory traffic required for the residual path.
  - **precision_management**：Utilizes float32 precision specifically for the variance accumulation (_var_base) to maintain numerical stability during the reduction of squared values, while performing the final arithmetic and storage in the lower precision input type (e.g., fp16/bf16) to maximize memory bandwidth utilization.
- **性能提升**：35%
- **边界与说明**：This kernel is optimized for scenarios where the hidden dimension N is large enough to amortize the cost of the two-pass loading (once for reduction, once for output). It is particularly effective in Pre-Norm or Post-Norm Transformer blocks.
- **KKB 来源**：[normalization/exp_fused_rms_norm_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_fused_rms_norm_001.yaml)

### exp_fused_split_qk_norm_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Reduction Operations；RMSNorm + Split + Copy；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: q_lora_rank=>=1; kv_lora_rank=>=1; qk_rope_dim=>=1；level: advanced
- **优化点**：
  - **kernel_fusion**：Fuses tensor splitting, two RMSNorm operations (for Q and K-nope), and a direct copy operation (for K-pe) into a single kernel. This reduces global memory reads of the input `fused_ptr` from multiple passes to a single pass, significantly lowering memory bandwidth pressure.
  - **memory_access_pattern**：Implements a strictly sequential access pattern for the input tensor `fused_ptr`. By loading the Q segment, followed immediately by the K-nope segment, and then the K-pe segment, the kernel maximizes DRAM burst utilization and cache hit rates.
  - **numerical_precision**：Explicitly casts input data to `tl.float32` before computing the variance (`q_var`, `k_var`). This prevents precision loss and potential overflow during the accumulation of squared values, which is critical when inputs are `fp16` or `bf16`.
  - **compile_time_branching**：Utilizes `tl.constexpr` for `Q_HAS_BIAS` and `K_HAS_BIAS`. This allows the Triton compiler to generate specialized code paths where bias addition logic is either inlined or completely omitted, avoiding runtime thread divergence.
- **性能提升**：35%
- **边界与说明**：This kernel is highly effective for LoRA ranks (e.g., 8-128) commonly found in LLM inference. Ensure that the sum of `q_lora_rank`, `kv_lora_rank`, and `qk_rope_dim` does not exceed the maximum vector load width supported by the hardware's Tensor Core or Cube unit for optimal performance.
- **KKB 来源**：[normalization/exp_fused_split_qk_norm_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_fused_split_qk_norm_001.yaml)

### exp_groupnorm_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Normalization Operations；Group Normalization；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: group_size=>=1; HW=>=32；level: advanced
- **优化点**：
  - **dynamic_vectorization_tuning**：The kernel employs an extensive autotuning configuration for `BLOCK_SUB_HW_SIZE`, sweeping values from 32 to 16384. This allows the runtime to select the optimal vectorization width for the HW dimension, balancing instruction overhead against memory bandwidth saturation and cache capacity for specific tensor shapes.
  - **coalesced_memory_access_pattern**：The memory access logic is structured to iterate over the HW dimension (`hw_offsets`) as the inner-most stride. By calculating `base_offset` using `channel_offset * HW + hw_offsets`, the kernel ensures that loads and stores are contiguous in global memory, maximizing memory bus utilization.
  - **high_precision_accumulation**：To ensure numerical stability during reduction, the kernel casts input data to `tl.float32` before accumulating `X_sum` and `X_var_sum`. This prevents precision loss or overflow that can occur when summing a large number of elements in lower precision formats (fp16/bf16).
  - **three_pass_algorithm**：The computation is split into three distinct passes (Mean calculation, Variance calculation, and Normalization). While this increases global memory read traffic (loading X three times), it significantly reduces register pressure and simplifies the control flow compared to a single-pass fused approach, enhancing stability for autotuning.
- **性能提升**：25%
- **边界与说明**：This implementation is optimized for stability and ease of tuning via the three-pass method. It is best suited for scenarios where HW dimensions are large enough to amortize the memory access overhead.
- **KKB 来源**：[normalization/exp_groupnorm_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_groupnorm_001.yaml)

### exp_rmsnorm_npu_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Reduction Operations；Fused Add RMSNorm；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: n_cols=>=256; n_rows=>=1；level: advanced
- **优化点**：
  - **grid_stride_scheduling**：Implements a grid-stride loop using `tl.range(pid, n_rows, num_progs, num_stages=NUM_STAGES)`. This allows the kernel to process an arbitrary number of rows (`n_rows`) efficiently regardless of the physical NPU core count, ensuring high utilization by mapping multiple rows to a single program instance.
  - **column_blocking_ub_management**：Processes wide rows in chunks defined by `BLOCK_SIZE` rather than loading the entire row at once. This tiling strategy is critical for preventing Unified Buffer (UB) overflow on NPUs when `n_cols` is large, a common failure point in naive implementations.
  - **two_pass_reduction_algorithm**：Decouples the computation into two distinct phases. The first pass computes the residual `S = X + R` and accumulates the `sum_square` for the RMS statistic. The second pass reloads `S` and applies the normalization and weights. This separation is necessary to calculate the global mean square statistic before applying the normalization.
  - **explicit_cache_policy**：Utilizes specific cache modifiers to optimize data movement. `eviction_policy="evict_first"` is used for inputs `X` and `R` to stream data without polluting the cache, while `cache_modifier=".cg"` is used when storing the intermediate `S` to ensure it remains in the cache for the subsequent load in the second pass, significantly reducing memory latency.
- **性能提升**：35%
- **边界与说明**：This kernel is specifically optimized for scenarios where the hidden dimension (n_cols) is large, exceeding the capacity of the NPU's Unified Buffer if loaded in a single block. It also supports specific casting modes for Llama and Gemma architectures.
- **KKB 来源**：[normalization/exp_rmsnorm_npu_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_rmsnorm_npu_001.yaml)

### exp_skip_layernorm_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Reduction Operations；Skip Layer Normalization；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: N=>=1024；level: advanced
- **优化点**：
  - **precision_control**：Accumulators for the sum (sum_x) and sum of squares (sum_sq) are explicitly computed in float32. This prevents overflow and ensures numerical stability during the variance calculation, which is critical when inputs are fp16 or bf16.
  - **kernel_fusion**：The residual connection (X + R) and the affine transformation (W * x_hat + B) are fused directly into the LayerNorm kernel. This eliminates the need for separate kernel launches and intermediate global memory storage, significantly reducing memory bandwidth pressure.
  - **two_pass_algorithm**：The kernel utilizes a two-pass strategy the first pass iterates over the data in blocks to compute mean and variance (reduction), and the second pass applies the normalization and affine transform. This approach decouples the reduction phase from the element-wise phase, allowing the kernel to handle hidden dimensions (N) larger than the register file capacity by processing data in BLOCK_SIZE chunks.
- **性能提升**：30%
- **边界与说明**：The two-pass approach trades off some memory bandwidth (reloading X and R in the second pass) for flexibility in handling large N dimensions. Ensure BLOCK_SIZE is tuned to the L1 cache size for optimal performance.
- **KKB 来源**：[normalization/exp_skip_layernorm_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/normalization/exp_skip_layernorm_001.yaml)
