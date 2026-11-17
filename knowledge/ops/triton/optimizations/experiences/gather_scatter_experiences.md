---
type: Optimization
title: Gather/Scatter 优化经验聚合
description: 从 13 条 Gather/Scatter/MoE YAML 经验中蒸馏的核心优化模式：Binned Dispatch、原子冲突规避与负载均衡。
tags: [task.optimization, topic.compute.indexing, topic.implementation.atomic, topic.parallelism]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Indexing_Ops/gather.md
  role: primary
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# Gather/Scatter 优化经验聚合

从 13 条 Gather/Scatter/MoE YAML 经验中蒸馏。核心挑战：不规则内存访问无法直接向量化，需通过排序、binning 和原子操作优化。

## 共性模式

1. **Binned Dispatch**：按 expert ID 排序后连续写入，减少随机 scatter 开销
2. **寄存器局部聚合**：多核 scatter 时先寄存器聚合再单次 atomic write
3. **Slot 预计算**：host 侧预计算每个 token 的 slot，kernel 只做写入

## 经验汇总

| 经验 ID | 提升 | 核心优化 |
|---------|------|----------|
| [exp_gs_bin_003](#exp_gs_bin_003) | 35% | Binned expert dispatch (num_experts × capacity ≥ 1024) |
| [exp_gs_mem_002](#exp_gs_mem_002) | 30% | BLOCK_SIZE 元素向量化 scatter |
| [exp_gs_mem_005](#exp_gs_mem_005) | 30% | scatter 前索引排序改善局部性 |
| [exp_gs_bin_005](#exp_gs_bin_005) | 30% | work-stealing 均衡 expert 负载 |
| [exp_moe_binned_scatter_001](#exp_moe_binned_scatter_001) | 30% | Bin 分组 scatter |
| [exp_gs_mem_001](#exp_gs_mem_001) | 25% | 寄存器局部聚合 + 单次 atomic write |
| [exp_gather_001](#exp_gather_001) | 25% | 向量化 gather |
| [exp_scatter_001](#exp_scatter_001) | 25% | 向量化 scatter |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_gather_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Indexing Operations；Gather；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3；tensor_shape: nd；core_param: num_indices=>=32; x_size=>=64；level: advanced
- **优化点**：
  - **vectorized_indexing**：Replace the scalar loop `for i in range(SUB_BLOCK_SIZE)` with vectorized pointer arithmetic. Calculate the base addresses for all rows in the sub-block simultaneously using the `cur_indices` tensor to enable parallel memory access.
  - **batched_loading**：Utilize `tl.load` with advanced indexing (broadcasted pointer arithmetic) to fetch the entire `(SUB_BLOCK_SIZE, BLOCK_X)` block in a single operation. This eliminates the need for iterative `tl.insert_slice` calls and reduces instruction count.
  - **control_flow_optimization**：Remove the inner Python-level loop within the JIT kernel. This allows the compiler to generate efficient SIMT instructions and improves pipeline utilization by avoiding serial execution of row gathering.
  - **vectorized_row_load**：The kernel loads the entire feature vector (x_vals) for a specific row into local memory/registers in a single operation before performing the gather. This strategy transforms multiple potential scattered global memory reads into one contiguous read, significantly reducing global memory access latency and bandwidth usage.
  - **intrinsic_gather_utilization**：Leverages the tl.gather intrinsic, which maps directly to efficient hardware indexing instructions. This avoids the overhead of complex manual pointer arithmetic or loop-based masking typically required for irregular memory access patterns.
  - **stride_generalization**：The kernel is designed to handle arbitrary strides for input, index, and output tensors. This flexibility allows it to operate directly on non-contiguous tensor layouts (such as sliced or transposed views) without requiring a preliminary layout transformation (padding or transposition) kernel.
- **性能提升**：30%
- **边界与说明**：This approach assumes the feature dimension (x_size) is small enough to fit efficiently into the GPU's SRAM or register file. For extremely large feature vectors, this method may lead to high register pressure.
- **KKB 来源**：[gather_scatter/exp_gather_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/gather_scatter/exp_gather_001.yaml)

### exp_moe_binned_scatter_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Indexing Operations；Binned Scatter；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: NUM_COLUMNS=>=128; expert_capacity=>=1; BLOCK_SIZE=>=64；level: advanced
- **优化点**：
  - **register_buffering**：The kernel utilizes a register-level buffer (`tmp_buf`) sized `(SUB_BLOCK_SIZE, BLOCK_X)` to accumulate data. By gathering multiple elements from the source tensor `a` into this buffer before performing a global store to `b`, the number of high-latency global memory write operations is significantly reduced.
  - **vectorized_memory_access**：The inner loop iterates over the feature dimension (`NUM_COLUMNS`) with a step size of `BLOCK_X`. This allows the kernel to load and store data using wide vector instructions (e.g., 128-bit or 256-bit), maximizing memory bandwidth utilization on the NPU.
  - **dynamic_bin_handling**：The logic efficiently handles transitions between different expert bins within a single `SUB_BLOCK_SIZE` iteration. By checking `if bin_idx != base_bin_idx`, it flushes the current buffer and updates the target address dynamically, ensuring correct data placement without breaking the vectorized processing loop.
  - **address_calculation_optimization**：The source address calculation `idx_a = (indices // TOP_K) * NUM_COLUMNS` is hoisted outside the column loop, and the destination address `idx_b` is updated incrementally. This minimizes redundant arithmetic instructions within the critical inner loops.
- **性能提升**：30%
- **边界与说明**：This optimization is specifically designed for Mixture of Experts (MoE) routing layers where tokens must be scattered to specific expert bins. It assumes that `expert_capacity` is large enough to hold the tokens per bin.
- **KKB 来源**：[gather_scatter/exp_moe_binned_scatter_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/gather_scatter/exp_moe_binned_scatter_001.yaml)

### exp_scatter_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Indexing Operations；Scatter；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: INDICES_LENGTH=>=BLOCK_SIZE; NUM_COLUMNS=>=BLOCK_X; BLOCK_X=>=32；level: advanced
- **优化点**：
  - **vectorized_memory_access**：The kernel loads data from the source tensor `x` in a 2D block (SUB_BLOCK_SIZE x BLOCK_X) and stores to the destination `out` using vectorized stores of width BLOCK_X. This maximizes memory bus utilization compared to scalar operations.
  - **sub_block_tiling**：By processing indices in chunks of SUB_BLOCK_SIZE, the kernel balances register pressure. It keeps a tile of the source matrix in registers/scratchpad while performing the random write pattern characteristic of scatter operations.
  - **boundary_masking**：Efficient handling of tensor boundaries using `idx_mask` and `col_mask` for both loads and stores. This eliminates the need for padding or expensive conditional branching for partial blocks at the edges of the tensor.
  - **hybrid_precision_compute**：The scaling operation is performed in float32 (`val.to(tl.float32) * scale.to(tl.float32)`) to preserve numerical accuracy during accumulation/multiplication, before casting back to the output type, ensuring stability without sacrificing memory storage efficiency.
- **性能提升**：30%
- **边界与说明**：This kernel assumes that the scatter operation does not require atomic adds (i.e., indices are unique or race conditions are acceptable/ignored). The `SCALE` feature is conditionally compiled via the `SCALE` constexpr.
- **KKB 来源**：[gather_scatter/exp_scatter_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/gather_scatter/exp_scatter_001.yaml)

### exp_gs_mem_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：分散 scatter 原子竞争
- **核心优化**：寄存器局部聚合，单次 atomic write per program
- **性能提升**：25%
- **KKB 来源**：[ops/gather_scatter.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/gather_scatter.md)

### exp_gs_mem_002

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：小粒度 scatter 写入
- **核心优化**：以 BLOCK_SIZE 元素为单位向量化 load/store
- **性能提升**：30%
- **KKB 来源**：[ops/gather_scatter.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/gather_scatter.md)

### exp_gs_mem_004

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：不规则索引访问
- **核心优化**：用 block pointer 表达索引访问，减少地址计算
- **性能提升**：25%
- **KKB 来源**：[ops/gather_scatter.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/gather_scatter.md)

### exp_gs_mem_005

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：随机 scatter 访问模式
- **核心优化**：scatter 前对索引 argsort，使相邻 program 写入相邻地址
- **性能提升**：30%
- **KKB 来源**：[ops/gather_scatter.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/gather_scatter.md)

### exp_gs_bin_003

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：MoE top-k 路由
- **核心优化**：按 expert 分 bin 连续写入；num_experts × expert_capacity ≥ 1024 时收益显著
- **性能提升**：35%
- **KKB 来源**：[ops/gather_scatter.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/gather_scatter.md)

### exp_gs_bin_004

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：MoE token 排列
- **核心优化**：用 shuffle 完成 token 重排，减少随机写
- **性能提升**：25%
- **KKB 来源**：[ops/gather_scatter.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/gather_scatter.md)

### exp_gs_bin_005

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：Expert 负载不均
- **核心优化**：动态 work-stealing 在 expert 间均衡核负载
- **性能提升**：30%
- **KKB 来源**：[ops/gather_scatter.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/gather_scatter.md)
