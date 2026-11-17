---
type: Optimization
title: Attention 优化经验聚合
description: 从 47 条 Attention YAML 经验中蒸馏的核心优化模式：Flash Attention、GQA/MQA、Paged KV Cache、Split-K
  与稀疏注意力。
tags: [task.optimization, topic.attention, topic.compute.normalization, topic.data_movement.memory_access, topic.compute.composite]
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
platforms: [a2]
---
# Attention 优化经验聚合

从 47 条 Attention YAML 经验中蒸馏的核心优化模式。

## 共性模式

所有 Attention 优化共享：
1. **Online Softmax**：维护 running max/sum，单 pass 完成 softmax，O(S) 内存
2. **分块 QK^T**：按 BLOCK_M × BLOCK_N tile 计算注意力分数
3. **fp32 精度**：softmax 中间计算全部升 fp32

## 高质量经验汇总

| 经验 ID | 提升 | 核心优化 | 适用条件 |
|---------|------|----------|----------|
| [exp_fused_attention_002](#exp_fused_attention_002) | 50% | Flash Attention: 分块+Online Softmax, O(S) 内存 | seq≥1024, fp16/bf16 |
| [exp_flashattn_gqa_001](#exp_flashattn_gqa_001) | 40% | SIMD index select 多头复用 KV | GQA/MQA |
| [exp_flashattn_splitk_gqa_001](#exp_flashattn_splitk_gqa_001) | 40% | Split-K + 分页 KV | GQA, 大 seq |
| [exp_attn_ascend_dual_pipeline_001](#exp_attn_ascend_dual_pipeline_001) | 45% | 双流水线软件流水 | seq≥2048 |
| [exp_paged_attn_flash_001](#exp_paged_attn_flash_001) | 35% | Block Pointer 分页注意力 | 推理, 分页 KV |
| [exp_sparse_attn_topk_001](#exp_sparse_attn_topk_001) | 30% | top-k 稀疏 mask | 稀疏注意力 prefill |
| [exp_sdpa_flash_001](#exp_sdpa_flash_001) | 35% | SDPA + Cube hints | PyTorch SDPA 对齐 |
| [exp_attn_fp8_ub_slice_001](#exp_attn_fp8_ub_slice_001) | 35% | UB 溢出分片处理 | fp8 输入 |
| fusion-search 3_FusionAttention | 59% | 29 基因编码存档：G023 反向倾斜 + G017 GQA 摊销 + 连续 kernel 结构重构 → 1.5933x；18 基因证伪全表（split-KV/num_stages/batched-rescale 均判否） | npu_fusion_attention 复刻，910b2，61 case（详见 operator playbook §2.5） |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_attn_ascend_dual_pipeline_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Matrix Operations；Attention Forward；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: N_CTX=>=128; HEAD_DIM=>=64; BLOCK_M=>=64；level: extreme
- **优化点**：
  - **dual_task_pipelining**：The kernel implements a dual-task scheduling strategy where a single program ID (pid) processes two independent sequence blocks (block_idx_0 and block_idx_1) in a loop. This effectively doubles the workload per core launch, overlapping memory access latency of one task with the computation of the other.
  - **cube_vector_asynchronous_execution**：The code explicitly separates the compute graph into `dl.async_task(scope=dl.async_task.cube)` for matrix multiplications (QK^T and Softmax*V) and `dl.async_task(scope=dl.async_task.vector)` for element-wise operations (Softmax, masking). This allows the NPU's Cube and Vector units to operate in parallel rather than sequentially.
  - **hardware_synchronization_mechanism**：Utilizes `dl.wait_cross_flag` and `dl.set_cross_flag` to implement a fine-grained producer-consumer synchronization model between the Cube and Vector units. This ensures that the Vector unit starts processing a tile immediately after the Cube unit writes it to the workspace, minimizing pipeline stalls.
  - **multi_level_workspace_buffering**：Leverages multiple workspace buffers (WS1, WS2, WS3, WS4) to store intermediate results (S matrix and partial O) in high-bandwidth memory (L1/L0). This avoids spilling intermediate data to global memory (HBM), significantly reducing memory bandwidth pressure.
- **性能提升**：55%
- **边界与说明**：This optimization relies on the specific DL (Device Link) API extensions for Ascend hardware. It is highly effective for long sequence lengths (N_CTX) where the overhead of kernel launch is amortized over the large compute volume.
- **KKB 来源**：[attention/exp_attn_ascend_dual_pipeline_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_attn_ascend_dual_pipeline_001.yaml)

### exp_attn_fp8_ub_slice_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Attention Operations；FlashAttention Forward；data_type: fp16, bf16, fp8；hardware: 910b2, 910b3；tensor_shape: nd；core_param: HEAD_DIM=>=256; BLOCK_M=>=128; BLOCK_N=>=128；level: extreme
- **优化点**：
  - **fp8_value_casting**：The softmax weights p are cast to float8e5 before the PV dot product if fp8_v is enabled. This reduces the data volume for the PV accumulation and leverages FP8 compute acceleration.
  - **ub_overflow_slicing**：For large head dimensions (HEAD_DIM >= 256), the accumulator is explicitly sliced into 4 segments (BLOCK_M // 4) during the update phase. This prevents Unified Buffer (UB) overflow on the NPU by ensuring intermediate results fit within on-chip memory limits.
  - **online_softmax**：Implements the online softmax algorithm within the loop, updating m_i (max) and l_i (sum) incrementally. This avoids storing the full attention matrix, significantly reducing global memory access.
- **性能提升**：30%
- **边界与说明**：The slicing logic is specifically required for HEAD_DIM >= 256 to avoid hardware resource limits. For smaller heads, the standard accumulator path is more efficient.
- **KKB 来源**：[attention/exp_attn_fp8_ub_slice_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_attn_fp8_ub_slice_001.yaml)

### exp_flashattn_gqa_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Attention Operations；FlashAttention (GQA/MQA)；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: BLOCK_DMODEL=>=64; BLOCK_N=>=32; kv_group_num=>=1；level: extreme
- **优化点**：
  - **simd_index_select**：Utilizes libdevice.index_select_simd to load K and V tensors. This enables parallel index selection from Global Memory to Unified Buffer (UB) with zero-copy semantics, optimizing for the irregular memory access patterns of ragged/paged attention.
  - **online_softmax**：Implements the online softmax algorithm (iterative max and sum updates) to avoid materializing the full attention matrix in SRAM/UB, significantly reducing memory bandwidth consumption.
  - **kv_split_parallelism**：Splits the KV sequence dimension across multiple program IDs (split_kv_id), allowing for parallel processing of long sequences and better utilization of compute units.
- **性能提升**：45%
- **边界与说明**：Optimized for Ascend NPU (910B series) using libdevice intrinsics. Supports variable sequence lengths via indptr/indices.
- **迁移归一**：目标仓库原引用为旧拼写（flash_attention_gqa），已按 KKB 规范 ID 归一到本锚点。
- **KKB 来源**：[attention/exp_flashattn_gqa_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_flashattn_gqa_001.yaml)

### exp_flashattn_splitk_gqa_001

- **经验类型**：Compute Optimization
- **适用条件**：Attention Operations；Split-K Grouped Attention；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: head_size=>=64; kv_len=>=1024; num_heads_q=>=1；level: advanced
- **优化点**：
  - **split_k_parallelism**：The sequence dimension (K) is partitioned into SPLIT_K chunks, allowing multiple thread blocks to compute partial attention scores in parallel. This reduces the per-block memory footprint and increases occupancy for long sequences.
  - **online_softmax**：Implements the iterative online softmax algorithm (updating m_i and l_i) within the main loop. This avoids materializing the full N x M attention matrix in global memory, significantly reducing memory bandwidth consumption.
  - **paged_kv_cache**：Utilizes Block_offsets to load K and V tiles, supporting non-contiguous memory layouts. This is crucial for inference frameworks (like vLLM) that use paged attention to manage variable-length sequences and KV cache efficiently.
  - **gqa_head_tiling**：The BLOCK_H parameter enables processing multiple query heads simultaneously against a single KV head. This optimization increases data reuse and arithmetic intensity for Grouped Query Attention (GQA) and Multi-Query Attention (MQA) workloads.
  - **logit_softcapping**：Directly integrates the tanh-based logit softcapping logic (qk = tanh(qk/cap) * cap) into the kernel loop, eliminating the need for a separate post-processing pass for models requiring this feature (e.g., Gemma).
  - **head_dim_vectorization**：Handles head dimensions that are not multiples of the tile size using BLOCK_DMODEL1, ensuring vectorized memory loads and efficient compute utilization for various head sizes (e.g., 128).
- **性能提升**：35%
- **边界与说明**：This kernel represents the first stage of a split-K attention implementation. A second reduction kernel is required to aggregate the partial outputs (Acc_out, m_i, l_i) produced by each split_k_id.
- **KKB 来源**：[attention/exp_flashattn_splitk_gqa_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_flashattn_splitk_gqa_001.yaml)

### exp_fused_attention_002

- **经验类型**：内存优化+数值稳定优化
- **适用条件**：MIX；fused-attention；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: seq_len=>=1024; d_k=>=64; num_heads=>=8；level: extreme
- **优化点**：
  - **分块计算**：将大序列长度矩阵按BLOCK_SIZE分块处理，避免存储完整的注意力分数矩阵，降低内存占用
  - **在线Softmax**：增量式计算Softmax，维护全局最大值(m_i)和全局exp和(l_i)，无需存储完整scores矩阵
  - **数值稳定**：分块内先减去块内最大值再计算exp，避免指数运算溢出，提升数值稳定性
  - **内存复用**：累加器(acc)分块更新，减少重复加载V张量的开销
- **性能提升**：50%
- **边界与说明**：适用于大序列长度（seq_len≥1024）的Attention计算，分块计算减少内存占用（从O(S²)降至O(S)），在线Softmax提升数值稳定性，910b2/910b3硬件上性能提升显著
- **KKB 来源**：[attention/exp_fused_attention_002.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_fused_attention_002.yaml)

### exp_paged_attn_flash_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Matrix Operations；Paged Attention；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: BLOCK_M=>=64; BLOCK_N=>=64; head_size=>=64；level: advanced
- **优化点**：
  - **Paged Memory Access Strategy**：Utilizes `Block_offsets` to calculate physical addresses for K and V tensors dynamically. This allows the kernel to handle non-contiguous KV cache blocks (pages) efficiently, which is critical for managing variable-length sequences and memory fragmentation in LLM inference.
  - **FlashAttention-style Online Softmax**：Implements the online softmax algorithm by maintaining running statistics `m_i` (maximum logit) and `l_i` (sum of exponentials) in registers/SRAM. The output accumulator `acc` is updated incrementally within the KV loop, avoiding the materialization of the large $N \times N$ attention matrix in HBM and significantly reducing memory bandwidth pressure.
  - **Head Dimension Tiling**：Supports arbitrary head dimensions by splitting the load and compute into `BLOCK_DMODEL` and `BLOCK_DMODEL1` (remainder). This ensures the kernel can handle model configurations where the head size is not a multiple of the standard tile size (e.g., 128) without performance degradation or code duplication.
  - **Vectorized Masking and Softcapping**：Integrates causal masking, sliding window attention (`window_size`), and logit softcapping (`tanh`) directly into the compute loop using vectorized operations like `tl.where`. This approach minimizes control flow divergence and ensures that masking logic does not introduce significant overhead.
- **性能提升**：35%
- **边界与说明**：Supports Grouped Query Attention (GQA) through the `kv_group_num` parameter and handles variable sequence lengths via `Q_seqlens` and `KV_seqlens`.
- **KKB 来源**：[attention/exp_paged_attn_flash_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_paged_attn_flash_001.yaml)

### exp_sdpa_flash_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Attention Operations；Matrix Multiplication；data_type: bf16, fp16, fp8；hardware: 910b2, 910b3；tensor_shape: nd；core_param: HEAD_DIM=<=128; BLOCK_M=>=64; BLOCK_N=>=64；level: advanced
- **优化点**：
  - **tiling_strategy**：Implements a block-wise tiling approach (BLOCK_R for Q rows, BLOCK_C for K/V columns) to load Key and Value tiles into SRAM once and reuse them across multiple Query row blocks. This significantly reduces HBM (High Bandwidth Memory) access frequency compared to a naive implementation.
  - **online_softmax**：Utilizes the online softmax algorithm (iteratively updating max value `m` and sum of exp `l`) to compute attention probabilities and output incrementally. This avoids materializing the large N x N attention matrix in global memory, drastically lowering memory footprint and bandwidth consumption.
  - **autotuning_config**：Employs `@triton.autotune` with a comprehensive search space over block sizes (e.g., 128x128, 64x128) and multibuffer settings. This allows the kernel to dynamically select the optimal configuration that maximizes Tensor Core utilization and minimizes latency for specific sequence lengths (S) and head dimensions (H).
  - **software_pipelining**：Leverages the `multibuffer` configuration option to overlap memory load operations (for K and V tiles) with compute operations (matrix multiplications). This effectively hides memory latency, keeping the compute units busy.
  - **mixed_precision_computation**：Performs matrix multiplications (`tl.dot`) in `bf16` (LOW_TYPE) to maximize hardware throughput, while maintaining softmax statistics and accumulation in `fp32` (HIGH_TYPE) to preserve numerical stability during the exponential and reduction operations.
  - **online_softmax**：Implements the online softmax algorithm (FlashAttention style) by tracking running maximums (m_i) and normalization factors (l_i) incrementally. This avoids materializing the large N x N attention matrix in high-bandwidth memory (HBM), drastically reducing memory traffic.
  - **kernel_fusion**：Fuses the QK^T matrix multiplication, Softmax activation, and PV^T matrix multiplication into a single kernel loop. This eliminates the need to write intermediate attention scores (S) and softmax output (P) back to global memory.
  - **block_tiling**：Processes data in tiles defined by BLOCK_M, BLOCK_N, and BLOCK_D. This maximizes data reuse in the on-chip memory (SRAM/Cache) by keeping blocks of Q, K, and V resident while performing multiple compute operations.
  - **efficient_boundary_handling**：Utilizes tl.load with boundary_check and padding_option="zero". This efficiently handles sequence lengths that are not perfectly divisible by the block size without introducing expensive branching logic or complex index calculations inside the kernel loop.
  - **mixed_precision_accumulation**：Casts the softmax probabilities (p) to the data type of the Value tensor (k_T.dtype) before the final dot product. This allows the use of lower precision formats (like FP8) for the accumulation phase when fp8_v is enabled, reducing memory bandwidth while maintaining FP32 stability for the softmax statistics.
- **性能提升**：200%
- **边界与说明**：This function represents the inner loop of a FlashAttention-style kernel. It assumes that the input pointers (K_T_block_ptr, V_block_ptr) are advanced correctly by an outer loop. The fp8_v flag enables low-precision computation for the Value projection.
- **KKB 来源**：[attention/exp_sdpa_flash_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_sdpa_flash_001.yaml)

### exp_sparse_attn_topk_001

- **经验类型**：Compute Optimization
- **适用条件**：Attention Operations；Sparse Attention (TopK)；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: HEAD_DIM=>=64; TOPK=>=1; BLOCK_SIZE_D=>=64；level: advanced
- **优化点**：
  - **sparse_iteration_strategy**：The kernel iterates only over the `real_topk` blocks identified by the `t_ptr` index tensor, rather than the full sequence length. This drastically reduces the number of expensive GEMM operations (QK and PV) from $O(N^2)$ to $O(N \cdot \text{TopK})$.
  - **block_pointer_utilization**：Utilizes `tl.make_block_ptr` for Q, K, V, and O tensors. This abstracts complex stride calculations, enables efficient 2D block memory access, and handles boundary conditions (padding) automatically via hardware-friendly instructions.
  - **online_softmax**：Implements the online softmax algorithm within the sparse loop by maintaining running maximums (`m_i`) and log-sum-exp (`lse_i`). This ensures numerical stability without materializing the large attention score matrix, saving significant memory bandwidth.
  - **efficient_causal_masking**：Applies the causal mask directly on the QK scores using `tl.where((pid_q_j >= c + off_k)...)` inside the compute loop. This vectorized approach avoids loading a separate large mask tensor.
- **性能提升**：40%
- **边界与说明**：Supports variable sequence lengths and Grouped Query Attention (GQA) via NUM_SHARE_Q_HEADS. Best suited for long-context scenarios where sparsity is high.
- **KKB 来源**：[attention/exp_sparse_attn_topk_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/attention/exp_sparse_attn_topk_001.yaml)
