---
type: Optimization
title: 激活函数优化经验聚合
description: 从 14 条激活函数 YAML 经验中蒸馏的核心优化模式：SiLU/GELU/SwiGLU 向量化与激活+量化融合。
tags: [task.optimization, topic.compute.elementwise.activation, topic.programming_model.execution_unit.vector, topic.compute.composite, topic.compute.quantization]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Math_Ops/sigmoid.md
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Math_Ops/exp.md
  role: supporting
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# 激活函数优化经验聚合

从 14 条激活函数 YAML 经验中蒸馏。激活函数天然适合向量化——逐元素独立，无跨元素依赖。

## 共性模式

1. **向量化**：BLOCK_SIZE ∈ {256,512,1024,2048,4096}，大张量优先 1024/2048
2. **融合优先**：紧跟 matmul 时内联进 GEMM kernel，消除中间 HBM 读写
3. **fp32 精度**：SwiGLU 等含 sigmoid 的激活在 fp32 中计算以保证精度

## 高质量经验汇总

| 经验 ID | 提升 | 核心优化 | 适用条件 |
|---------|------|----------|----------|
| [exp_silu_fwd_001](#exp_silu_fwd_001) | 25% | SiLU 前向向量化 | SiLU 激活 |
| [exp_gelu_fwd_001](#exp_gelu_fwd_001) | 25% | GELU 前向向量化 | GELU 激活 |
| [exp_swiglu_fwd_001](#exp_swiglu_fwd_001) | 30% | SwiGLU 门控激活前向 | SwiGLU |
| [exp_swiglu_quant_001](#exp_swiglu_quant_001) | 35% | SwiGLU + 量化单核融合 | 量化推理 |
| [exp_fused_gating_001](#exp_fused_gating_001) | 30% | gating + 激活融合 | 门控激活融合 |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_fused_gating_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Element-wise Fused Operations；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: NUM_HEADS=>=BLK_HEADS; NUM_BATCHES=>=BLK_BATCHES; seq_len=>0；level: advanced
- **优化点**：
  - **operator_fusion**：Fuses the computation of the gating parameter 'g' (involving Softplus, Exp, and multiplication) and 'beta_output' (Sigmoid) into a single kernel. This significantly reduces global memory bandwidth pressure by reading inputs 'a', 'b', 'A_log', and 'dt_bias' only once and writing outputs 'g' and 'beta_output' in a single pass.
  - **numerical_stability**：Implements a numerically stable Softplus approximation using `tl.where`. It switches to a linear approximation (x) when `beta * x` exceeds a defined threshold, preventing overflow in the `tl.exp` operation which is a common issue with standard Softplus implementations on lower precision hardware.
  - **block_tiling_strategy**：Utilizes nested loops (`ROW_ITER`, `COL_ITER`) over fixed block sizes (`BLK_BATCHES`, `BLK_HEADS`). This strategy allows the kernel to handle tensor dimensions larger than the hardware's maximum block size constraints or optimal tiling limits, ensuring high occupancy and reducing kernel launch overhead for large batch/head dimensions.
  - **precision_upcasting**：Explicitly casts intermediate computations (addition, exponential, logarithm, and sigmoid) to `tl.float32`. This preserves numerical accuracy during the accumulation of non-linear operations which are sensitive to the reduced dynamic range and precision of fp16/bf16, before casting the final result back to the original dtype.
- **性能提升**：25%
- **边界与说明**：This kernel is optimized for Gated Linear Unit (GLU) or GDN variants. Ensure that the threshold parameter is tuned appropriately for the specific data distribution to maximize the effectiveness of the Softplus approximation.
- **KKB 来源**：[activation/exp_fused_gating_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/activation/exp_fused_gating_001.yaml)

### exp_gelu_fwd_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Activation Operations；Element-wise；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: n_rows=>=1; n_cols=>=1；level: advanced
- **优化点**：
  - **grid_stride_loop**：The kernel utilizes a grid-stride loop pattern (`for row_task_id in range(pid, num_row_tasks, grid_size)`) to process the row dimension. This allows a fixed number of thread blocks to process an arbitrarily large number of rows, maximizing hardware occupancy and reducing kernel launch overhead compared to a 1:1 block-to-row mapping.
  - **autotuning_block_m**：The `@triton.autotune` decorator is configured to test `BLOCK_SIZE_M` values from 1 to 32. This dynamic tuning is critical for element-wise operations on 2D tensors, as the optimal tile size for the row dimension often varies based on the specific shape of `n_rows` and `n_cols` (e.g., handling very small batch sizes or sequence lengths efficiently).
  - **precision_preservation**：The computation explicitly casts the input chunk to `float32` (`x_f32 = x_chunk.to(tl.float32)`) before applying the GELU approximation. This ensures numerical stability for the `tanh` and exponential operations, preventing overflow or underflow that can occur when computing GELU directly in `fp16` or `bf16`.
  - **vectorized_memory_access**：The inner loop iterates over columns using `BLOCK_SIZE_N` chunks with masked loads/stores. This ensures memory accesses are coalesced and vectorized, optimizing global memory bandwidth usage while correctly handling tensor boundaries where dimensions are not multiples of the block size.
- **性能提升**：15%
- **边界与说明**：This implementation uses the tanh approximation for GELU. The grid-stride scheduling makes it particularly robust for tensors with a large number of rows (e.g., large batch sizes) where the grid size might otherwise be insufficient to cover the dimension.
- **KKB 来源**：[activation/exp_gelu_fwd_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/activation/exp_gelu_fwd_001.yaml)

### exp_silu_fwd_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Activation Operations；Element-wise；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: n_rows=>=1; n_cols=>=1；level: advanced
- **优化点**：
  - **grid_stride_loop**：The kernel implements a grid-stride loop strategy over the row dimension (for row_task_id in range(pid, num_row_task, grid_size)). This allows a fixed number of thread blocks to process an arbitrarily large number of rows by iterating over multiple chunks, significantly improving hardware utilization and load balancing for tall matrices.
  - **dynamic_block_tuning**：The @triton.autotune decorator is configured to test BLOCK_SIZE_M values from 1 to 32. This runtime tuning is essential to identify the optimal tile size that maximizes instruction-level parallelism without exceeding register file limits, adapting to the specific cache hierarchy of the target hardware.
  - **precision_preservation**：The computation explicitly casts input data to float32 (x_f32 = x_chunk.to(tl.float32)) before applying the SiLU activation. This prevents potential precision loss or overflow issues inherent in the exponential calculation of the sigmoid function when using low-precision data types like fp16 or bf16.
  - **memory_coalescing**：The inner loop processes columns in blocks of BLOCK_SIZE_N, and pointer arithmetic is arranged to load contiguous memory segments. This ensures memory accesses are coalesced, maximizing memory bandwidth throughput.
- **性能提升**：25%
- **边界与说明**：The grid-stride loop is particularly beneficial when the grid size is limited or when the input matrix has a large number of rows. The float32 casting adds a small conversion overhead but is critical for model accuracy.
- **KKB 来源**：[activation/exp_silu_fwd_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/activation/exp_silu_fwd_001.yaml)

### exp_swiglu_fwd_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Activation Operations；Element-wise Operations；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: n_rows=>=1; n_cols=>=128；level: advanced
- **优化点**：
  - **mixed_precision_computation**：The kernel explicitly casts the input tensor 'a' to float32 before applying the silu (sigmoid linear unit) function. This ensures numerical stability for the sigmoid component, which is prone to overflow/underflow in fp16/bf16, while maintaining performance by casting back to the original dtype for the final multiplication.
  - **vectorized_memory_access**：By utilizing a compile-time constant BLOCK_SIZE and tl.arange, the kernel loads and stores data in vectorized chunks. This maximizes memory bandwidth utilization and reduces the number of memory instructions issued compared to scalar operations.
  - **operator_fusion**：The kernel fuses the silu activation and the element-wise multiplication (gate mechanism) into a single kernel launch. This eliminates the need to write intermediate results to global memory, significantly reducing memory bandwidth pressure and latency.
  - **grid_stride_scheduling**：The kernel implements a grid-stride loop over the row dimension (`for row_task_id in range(pid, num_row_tasks, grid_size)`). This allows a fixed number of thread blocks to process an arbitrary number of rows efficiently, ensuring high utilization even when the total number of row blocks exceeds the grid size.
  - **autotuning_block_m**：The `BLOCK_SIZE_M` is autotuned across a range of values (1 to 32). This is critical for adapting to varying row dimensions (e.g., different batch sizes or sequence lengths in LLMs), optimizing the trade-off between instruction-level parallelism and GPU occupancy.
  - **mixed_precision_computation**：The input tensor `a` is cast to `float32` before the `silu` activation and then cast back to the original dtype. This ensures numerical stability for the sigmoid calculation, which is prone to underflow in fp16/bf16, without sacrificing the memory bandwidth benefits of lower precision storage.
  - **vectorized_memory_access**：The inner loop processes columns in chunks of `BLOCK_SIZE_N`, ensuring that memory loads and stores are coalesced. This maximizes memory bandwidth utilization by accessing contiguous memory locations.
- **性能提升**：15%
- **边界与说明**：This kernel is specifically optimized for the SwiGLU activation function found in modern LLMs. The float32 intermediate calculation is essential for maintaining accuracy during the activation phase.
- **KKB 来源**：[activation/exp_swiglu_fwd_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/activation/exp_swiglu_fwd_001.yaml)

### exp_swiglu_quant_001

- **经验类型**：Compute Optimization
- **适用条件**：Activation Operations；Element-wise and Row-wise Reduction；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: TOTAL_COLS=>=128; total_rows=>=32；level: advanced
- **优化点**：
  - **operator_fusion**：Fuses the SwiGLU activation function (x1 * sigmoid(x1) * x2) with the per-row dynamic quantization process. This eliminates the need to write intermediate activation results to global memory (HBM), significantly reducing memory bandwidth consumption and latency.
  - **vectorized_memory_access**：Utilizes wide vector loads to fetch the entire input row (`TOTAL_COLS`) in a single transaction for the activation phase, and processes the quantization phase in `COL_BLOCK_SIZE` chunks. This maximizes memory bus utilization and improves data reuse within registers.
  - **dynamic_workload_distribution**：Dynamically calculates the total number of rows (`total_rows`) based on the `group_list_ptr` (supporting both cumulative sum and list formats) and partitions the work evenly across `NUM_CORES`. This ensures load balancing even in scenarios with variable batch sizes, such as Mixture of Experts (MoE) routing.
  - **hardware_accelerated_casting**：Leverages Triton's `cast` primitive with `overflow_mode="saturate"` to perform the clamping and type conversion (float to int8) efficiently using dedicated hardware instructions, avoiding slower software-based min/max clamping logic.
- **性能提升**：35%
- **边界与说明**：This kernel is optimized for scenarios requiring immediate quantization after activation, such as in MoE layers or quantized inference paths. The `GROUP_LIST_TYPE` parameter provides flexibility for different input metadata formats.
- **KKB 来源**：[activation/exp_swiglu_quant_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/activation/exp_swiglu_quant_001.yaml)
