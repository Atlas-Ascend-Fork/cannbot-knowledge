---
type: Optimization
title: RoPE 优化经验聚合
description: 从 10 条 RoPE YAML 经验中蒸馏的核心优化模式：cos/sin 复用、constexpr 多路特化与向量化旋转。
tags: [task.optimization, topic.compute.elementwise.arithmetic, topic.compute.composite, topic.programming_model.execution_unit.vector, topic.compilation]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Math_Ops/sin.md
  role: primary
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# RoPE 优化经验聚合

从 10 条 RoPE YAML 经验中蒸馏。RoPE 通过复数旋转实现位置编码，包含多种变体：标准、Partial（Llama-3）、Multi-RoPE（Qwen2-VL）、Neox 风格等。

## 共性模式

1. **cos/sin 复用**：预计算频率表，循环内复用
2. **constexpr 多路特化**：IS_NEOX_STYLE/IS_VARLEN/HAS_KV_LENS 编译期分支消除
3. **向量化旋转**：对相邻维度 pair 施加 2D 旋转矩阵 `[cos -sin; sin cos]`

## 经验汇总

| 经验 ID | 提升 | 核心优化 | 适用条件 |
|---------|------|----------|----------|
| [exp_rope_npu_001](#exp_rope_npu_001) | 35% | cos/sin 复用+software pipeline+前后向共用 | Ascend NPU, hd≥64 |
| [exp_rope_forward_001](#exp_rope_forward_001) | 25% | ALIGNED 路径+do_not_specialize | varlen 前向 |
| [exp_rope_backward_001](#exp_rope_backward_001) | 25% | grid-stride+IS_VARLEN+HAS_KV_LENS | varlen/KV cache 反向 |
| [exp_partial_rope_001](#exp_partial_rope_001) | 25% | 跳过 NOPE_DIM+向量化前/后半 | Llama-3, ROPE_DIM≥32 |
| [exp_qwen2vl_mrope_001](#exp_qwen2vl_mrope_001) | 25% | t/h/w 三维融合+head blocking | Qwen2-VL, hd≥128 |
| [exp_rope_llama4_npu_001](#exp_rope_llama4_npu_001) | 25% | UB tiling+FMA+interleaved | Llama-4 NPU |
| [exp_rope_siso_001](#exp_rope_siso_001) | 25% | 3D tiling+非交错向量化 | SISO 布局 |
| [exp_triton_rope_001](#exp_triton_rope_001) | 25% | IS_NEOX_STYLE constexpr 双路 | Neox/非Neox |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_partial_rope_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Partial Rotary Positional Embedding；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: total_seq_len=>=128; ROPE_DIM=>=32; BLOCK=>=128；level: advanced
- **优化点**：
  - **vectorized_memory_access**：The kernel utilizes `tl.arange(0, half_dim)` to load and store contiguous chunks of the head dimension (`x_l`, `x_h`, `o_l`, `o_h`) as vectors. This approach maximizes memory bandwidth utilization and enables the hardware to leverage SIMD (Single Instruction, Multiple Data) capabilities for data movement.
  - **partial_rope_efficiency**：The implementation explicitly calculates offsets starting from `NOPE_DIM` (Non-rotated dimensions). By skipping the non-rotated portion of the head dimension during the load/compute/store phases, the kernel optimizes for modern architectures (like Llama-3) that utilize partial RoPE, saving significant compute cycles compared to a full-dimension rotation.
  - **fused_arithmetic_pipeline**：The rotation calculations ($x \cos - y \sin$ and $y \cos + x \sin$) are performed immediately on the loaded vector registers before storing. This fusion keeps the data in the high-speed register file (or L1 cache) throughout the transformation, eliminating the latency overhead of writing intermediate results back to global memory.
  - **vectorized_load_splitting**：The COS and SIN embeddings are loaded in two separate vectorized operations for the lower (`_l`) and upper (`_h`) halves of the rotary dimension. This aligns memory access patterns with the complex number rotation logic (treating pairs as real/imaginary components), maximizing vector unit utilization and reducing instruction count.
  - **explicit_core_scheduling**：The kernel utilizes a grid-stride loop pattern `range(pid, NUM_BLOCKS, NUM_CORES)` to statically distribute work across the available AI cores. This explicit scheduling minimizes synchronization overhead and ensures optimal load balancing on NPU architectures like the 910 series.
  - **block_masking_efficiency**：Boundary conditions for sequence length are handled via `pos_mask` and `seq_mask` applied during the load of COS/SIN and implicitly passed to the compute function. This avoids branching within the inner loop and maintains high throughput for sequences not perfectly divisible by the block size.
- **性能提升**：25%
- **边界与说明**：The `NUM_CORES` parameter is critical for performance and should be tuned to match the physical core count of the specific NPU chip (e.g., 32 for 910B) to maximize parallelism.
- **KKB 来源**：[rope/exp_partial_rope_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_partial_rope_001.yaml)

### exp_qwen2vl_mrope_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Rotary Positional Embedding；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: hd=>=128; n_qh=>=1; n_kh=>=1；level: advanced
- **优化点**：
  - **fused_mrope_logic**：The kernel fuses the complex logic of Multi-RoPE (temporal, height, width) directly into the computation. Instead of preprocessing or splitting tensors, it calculates pointers for t, h, and w components and uses tl.where to dynamically select the correct cos/sin values based on the dimension index. This eliminates extra memory reads and kernel launch overheads associated with handling multi-modal positional encodings.
  - **head_blocking_reuse**：The implementation processes Query and Key heads in blocks (BLOCK_Q, BLOCK_K). This strategy allows the cos and sin vectors, which are constant for a given row across all heads, to be loaded once from global memory and reused for all heads within the block. This drastically reduces the memory bandwidth pressure for accessing the relatively small positional embedding tables.
  - **software_pipelining**：The outer loop utilizes the num_stages parameter to implement software pipelining. By prefetching the next row's data while computing the current row, the kernel effectively hides global memory latency, ensuring the compute units are consistently fed with data.
  - **vectorized_rotation**：The rotation operation is performed by splitting the head dimension into left and right halves (q_left, q_right). This aligns with the memory layout of interleaved RoPE tensors, enabling the use of wide vectorized load/store instructions which maximize memory bus utilization on NPU hardware.
- **性能提升**：25%
- **边界与说明**：This kernel is specifically optimized for Qwen2-VL's 3D positional encoding requirements. It assumes the input tensors are in a standard 2D layout (rows, head_dim) and handles boundary conditions for arbitrary sequence lengths and batch sizes.
- **KKB 来源**：[rope/exp_qwen2vl_mrope_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_qwen2vl_mrope_001.yaml)

### exp_rope_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；RoPE (Rotary Positional Embedding)；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: head_dim=>=64；level: advanced
- **优化点**：
  - **cos_sin_reuse**：The COS and SIN tensors are loaded once per sequence block outside the NUM_HEADS loop. Since positional embeddings are identical across all attention heads for a given position, this strategy significantly reduces global memory bandwidth consumption by avoiding redundant loads for each head iteration.
  - **persistent_scheduling**：The kernel utilizes a grid-stride loop pattern (range(pid, NUM_BLOCKS, NUM_CORES)). This acts as a persistent kernel, allowing a single program instance to process multiple sequence blocks. This improves load balancing across cores and reduces kernel launch overhead for variable sequence lengths.
  - **vectorized_access**：The COS and SIN values are loaded in contiguous chunks (split into low/high dimensions) corresponding to the BLOCK size. This maximizes memory coalescing and utilizes the memory bus width efficiently on the NPU.
  - **vectorized_complex_decomposition**：The complex number multiplication required for RoPE is decomposed into separate real (x1) and imaginary (x2) floating-point operations. This mapping allows the underlying hardware to utilize standard SIMD vector units efficiently, avoiding potential overhead or latency associated with native complex data type handling.
  - **compile_time_branch_pruning**：The 'inverse' flag is defined as a tl.constexpr. This forces the Triton compiler to generate specialized kernels for the forward and inverse (backward) passes during compilation. It completely eliminates runtime branch divergence within the thread blocks, ensuring all threads in a warp execute the same instruction stream.
  - **fused_arithmetic_expression**：The computation combines multiplication and addition/subtraction into single expressions (e.g., x1 * cos_tile - x2 * sin_tile). This fusion minimizes register pressure by avoiding the storage of intermediate products, allowing for higher instruction throughput and better utilization of the NPU's compute pipelines.
- **性能提升**：15%
- **边界与说明**：This kernel is a compute helper that assumes data (x1, x2, sin, cos) is already loaded into SRAM/Registers. Performance gains are realized when combined with an optimized memory loading strategy in the parent kernel.
- **KKB 来源**：[rope/exp_rope_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_rope_001.yaml)

### exp_rope_backward_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Activation Operations；RoPE Backward；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: bs=>=1; hd=>=64; rope_dim=>=32；level: advanced
- **优化点**：
  - **grid_stride_loop**：Implements a grid-stride loop (`for block_id in range(pid, total_blocks, grid_size)`) to allow a single program to process multiple blocks. This increases hardware utilization and load balancing, particularly when the total number of sequence blocks is large or not evenly divisible by the grid size.
  - **varlen_memory_optimization**：Specialized logic for `IS_VARLEN` loads chunk metadata (`chunk_indices_ptr`) to compute dynamic sequence offsets and masks. This avoids padding to the maximum sequence length, significantly reducing memory bandwidth consumption for ragged batches common in LLM inference.
  - **vectorized_load_strategy**：Uses compile-time branching (`ALIGNED`) to select the optimal memory access pattern. When aligned, it loads the full RoPE dimension in a single transaction for maximum throughput; otherwise, it splits loads into two halves to handle unaligned addresses or non-contiguous memory layouts safely without hardware penalties.
  - **kv_cache_aware_indexing**：Supports `HAS_KV_LENS` to correctly index `cos` and `sin` tables based on the actual KV cache length per batch. This ensures correctness for autoregressive decoding scenarios where the KV sequence length differs from the current input sequence length.
- **性能提升**：25%
- **边界与说明**：This kernel is highly optimized for variable-length sequence processing and KV-cache scenarios in Transformer models. Ensure `TOKEN_BLOCK_SIZE` is tuned based on the specific hardware's L1 cache size for optimal performance.
- **KKB 来源**：[rope/exp_rope_backward_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_rope_backward_001.yaml)

### exp_rope_forward_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Matrix Operations；RoPE (Rotary Positional Embedding)；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: seq_len=>=TOKEN_BLOCK_SIZE; head_dim=>=rope_dim；level: advanced
- **优化点**：
  - **dynamic_specialization**：Uses `do_not_specialize=["seq_len"]` to prevent kernel recompilation for varying sequence lengths, significantly reducing launch overhead in dynamic batching scenarios.
  - **memory_alignment_handling**：Implements an `ALIGNED` path that loads the full RoPE dimension in a single vectorized load, and a fallback path for unaligned dimensions, ensuring maximum memory bandwidth utilization regardless of tensor layout.
  - **grid_stride_scheduling**：Employs a grid-stride loop (`for block_id in range(pid, total_blocks, grid_size)`) to map a fixed number of thread blocks to a variable number of sequence blocks, maintaining high hardware occupancy.
  - **efficient_masking**：Combines sequence validity masks with head and dimension masks to perform safe loads/stores for variable-length sequences and KV caches without expensive branching.
- **性能提升**：25%
- **边界与说明**：Optimized for LLM inference with variable length sequences and KV cache support. Handles both contiguous and non-contiguous memory layouts for RoPE dimensions.
- **KKB 来源**：[rope/exp_rope_forward_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_rope_forward_001.yaml)

### exp_rope_llama4_npu_001

- **经验类型**：Hardware Adaptation Optimization
- **适用条件**：Matrix Operations；RoPE (Rotary Position Embedding)；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: hd=>=32, multiple of 2; n_qh=>=1; n_kh=>=1；level: advanced
- **优化点**：
  - **ub_tiling_strategy**：The kernel iterates over query and key heads in chunks defined by BLOCK_Q and BLOCK_K. This tiling strategy is designed to keep the active working set within the NPU's Unified Buffer (UB), minimizing high-latency data transfers between Global Memory (GM) and UB.
  - **fma_instruction_utilization**：The complex multiplication arithmetic is implemented using tl.math.fma (Fused Multiply-Add). This leverages the NPU's pipeline capabilities to compute the real and imaginary components (ac - bd, ad + bc) efficiently, reducing the total number of instructions compared to discrete multiplication and addition.
  - **interleaved_layout_optimization**：By using can_reorder=True in reshape operations and tl.interleave for the output, the kernel allows the compiler to handle the interleaved complex data layout (real, imag) optimally. This avoids costly explicit transposition or gather/scatter operations and aligns memory access patterns with the NPU's vectorization units.
- **性能提升**：25%
- **边界与说明**：This kernel is specifically tuned for the Ascend NPU memory hierarchy. It assumes an interleaved complex layout for the frequency inputs and outputs.
- **KKB 来源**：[rope/exp_rope_llama4_npu_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_rope_llama4_npu_001.yaml)

### exp_rope_npu_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Activation Operations；Element-wise Operation；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: hd=>=64; n_qh=>=1; n_kh=>=1; sl=>=1；level: advanced
- **优化点**：
  - **cos_sin_reuse**：The cos and sin values are loaded once per row (sequence position) outside the inner head iteration loops. These values are then reused for all query and key heads within that row, significantly reducing redundant global memory accesses and bandwidth pressure.
  - **software_pipelining**：The outer loop utilizes the `num_stages` parameter in `tl.range` to enable software pipelining. This overlaps the memory loading operations of subsequent rows with the arithmetic computation of the current row, effectively hiding memory latency.
  - **head_blocking**：The kernel processes query and key heads in fixed-size blocks (`BLOCK_Q` and `BLOCK_K`). This tiling strategy ensures that the intermediate data and pointer calculations fit within the NPU's Unified Buffer (UB) or registers, preventing overflow and maximizing on-chip memory utilization.
- **性能提升**：35%
- **边界与说明**：This implementation supports both forward and backward passes (controlled by `BACKWARD_PASS`). It also handles broadcasting of cos/sin when `cos_bs` is 1.
- **KKB 来源**：[rope/exp_rope_npu_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_rope_npu_001.yaml)

### exp_rope_siso_001

- **经验类型**：Compute Optimization
- **适用条件**：Matrix Operations；Rotary Positional Embedding；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: num_tokens=>=BLOCK_N; num_heads=>=BLOCK_H; head_dim=>=BLOCK_D；level: advanced
- **优化点**：
  - **vectorized_non_interleaved_path**：For non-interleaved data layouts, the kernel constructs dimension ranges using tl.arange to process the entire head dimension block in a single pass. This eliminates loop overhead and maximizes vector unit utilization compared to the scalar iteration used in the interleaved path.
  - **3d_tiling_strategy**：The kernel employs a 3D tiling strategy (BLOCK_N for tokens, BLOCK_H for heads, BLOCK_D for dimensions). This maps the computation efficiently to the hardware grid, ensuring data loaded into registers/SRAM is reused before eviction, optimizing memory bandwidth usage.
  - **layout_specific_optimization**：By using a compile-time constant (rotary_interleaved), the kernel generates specialized code paths. The interleaved path handles element-wise pairs via a loop, while the non-interleaved path leverages bulk vector operations, ensuring optimal performance for both common tensor formats without runtime divergence.
- **性能提升**：25%
- **边界与说明**：The performance relies heavily on the BLOCK_D size matching the hardware's vector width. The helper function rotary_embedding_rw_kernel is assumed to handle the actual load/store and arithmetic operations.
- **KKB 来源**：[rope/exp_rope_siso_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_rope_siso_001.yaml)

### exp_triton_rope_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Rotary Positional Embedding；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: num_tokens=>=1; head_dim=>=rope_dim; rope_dim=>=2；level: advanced
- **优化点**：
  - **vectorized_chunked_processing**：The kernel explicitly calculates offsets for the first and second halves of the head dimension (`first_half_q_offsets`, `second_half_q_offsets`) based on the `IS_NEOX_STYLE` flag. This enables loading contiguous blocks of memory for the rotation calculation, maximizing memory bandwidth utilization and allowing the compiler to generate efficient SIMD instructions for the `x1*cos - x2*sin` operations.
  - **padded_access_with_masking**：The kernel utilizes padding parameters (`pad_n_qh`, `pad_rope_dim`) to calculate static, aligned memory offsets for vectorized loads. It simultaneously applies runtime masks (`first_q_mask`, `cos_mask`) to handle cases where the actual dimensions are smaller than the padded block size. This strategy ensures memory access alignment for performance while maintaining correctness for arbitrary tensor shapes without expensive global memory re-padding.
  - **loop_tiling_over_tokens**：The kernel employs a grid-stride loop (`tl.range`) over the `num_tokens` dimension, allowing a single kernel launch to process the entire sequence. This significantly reduces kernel launch overhead compared to launching a separate kernel instance for each token or head, and improves data locality by keeping cos/sin values in registers/cache across head iterations.
- **性能提升**：25%
- **边界与说明**：Supports both Neox-style (chunked) and non-Neox-style (interleaved) RoPE, as well as partial RoPE application where rope_dim < head_dim. It also handles both pre-computed cos/sin tensors and position-indexed lookups.
- **KKB 来源**：[rope/exp_triton_rope_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/rope/exp_triton_rope_001.yaml)
