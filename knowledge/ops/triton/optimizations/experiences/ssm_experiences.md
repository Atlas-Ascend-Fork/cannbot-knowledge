---
type: Optimization
title: SSM/KDA 优化经验聚合
description: 从 12 条 SSM YAML 经验中蒸馏的核心优化模式：Chunkwise 分解、State 寄存器复用与反向标量消除（i64→i32,
  block_ptr→手动指针）。
tags: [task.optimization, topic.compute.composite, topic.programming_model, topic.programming_model.execution_unit.scalar, topic.data_movement]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/index.md
  role: supporting
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# SSM/KDA 优化经验聚合

从 12 条 SSM YAML 经验中蒸馏。SSM 以线性递推更新隐状态，核心挑战：递推依赖（时间步间有数据依赖）、Chunkwise 分解（块内并行 GEMM + 块间串行状态转移）。

## 共性模式

1. **Chunkwise 分解**：block 内并行 GEMM + block 间串行状态传递
2. **State 寄存器复用**：隐状态 `h` 全程驻留寄存器
3. **反向标量消除**：KDA 反向 kernel 中 i64→i32、i32→fp32、cdiv/min 消除、block_ptr→手动指针

## Chunkwise 前向经验

| 经验 ID | 核心技术 |
|---------|----------|
| [exp_chunk_fwd_001](#exp_chunk_fwd_001) | block_ptr tiling + gating masking |
| [exp_chunk_gated_delta_001](#exp_chunk_gated_delta_001) | sigmoid gating + 状态更新 |
| [exp_fused_delta_rule_npu_001](#exp_fused_delta_rule_npu_001) | sigmoid+softplus+delta rule 三合一 NPU 路径 |

## KDA 反向优化（最大收益）

| 经验 ID | 提升 | 核心优化 |
|---------|------|----------|
| [exp_kda_bwd_wy_scalar_opt_001](#exp_kda_bwd_wy_scalar_opt_001) | 3.33x | i64→i32、i32→fp32 比较、cdiv/min/compile_hint 消除 |
| [exp_kda_bwd_intra_scalar_opt_001](#exp_kda_bwd_intra_scalar_opt_001) | 50% | block_ptr→手动指针、fp32 mask、min→tl.where |
| [exp_kda_bwd_scalar_loop_to_dot_001](#exp_kda_bwd_scalar_loop_to_dot_001) | 40% | 对角块标量循环 → tl.dot |
| [exp_kda_bwd_intra_memory_opt_001](#exp_kda_bwd_intra_memory_opt_001) | 35% | 转置 load 合并化、冗余 load 消除 |
| [exp_kda_bwd_wy_structure_opt_001](#exp_kda_bwd_wy_structure_opt_001) | 30% | Phase split、barrier 外提、LICM |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_chunk_cumsum_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Cumulative Sum；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: BLOCK_T=>=64; CHUNK_SIZE=64; H=>=1；level: advanced
- **优化点**：
  - **chunked_scan_strategy**：The kernel reshapes the loaded block into (N_CHUNKS, CHUNK_SIZE, H) and performs cumsum along the CHUNK_SIZE dimension. This breaks the long serial dependency chain of a full-sequence cumsum into smaller, independent chunks, significantly improving instruction-level parallelism and reducing register pressure.
  - **block_ptr_utilization**：Uses tl.make_block_ptr for memory loading and storing. This abstracts complex pointer arithmetic and enables the compiler to generate optimized vectorized memory instructions (e.g., 128-bit loads) suitable for the target hardware, ensuring high memory bandwidth utilization.
  - **layout_transposition**：Dynamically handles HEAD_FIRST (H, T) and non-HEAD_FIRST (T, H) layouts by transposing the data so that the cumsum operation always traverses contiguous memory segments, minimizing memory access latency and bank conflicts.
- **性能提升**：25%
- **边界与说明**：BLOCK_T must be a multiple of CHUNK_SIZE. The kernel supports variable length sequences via cu_seqlens, avoiding padding overhead.
- **KKB 来源**：[ssm/exp_chunk_cumsum_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_chunk_cumsum_001.yaml)

### exp_chunk_fwd_001

- **经验类型**：Compute Optimization
- **适用条件**：Matrix Operations；Chunkwise Linear Attention；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: T=>=128; K=>=64; V=>=64; BT=>=16；level: advanced
- **优化点**：
  - **block_ptr_tiling**：Utilizes `tl.make_block_ptr` to efficiently load 2D blocks of Q, K, V, and H tensors. This optimizes memory coalescing and leverages hardware load/store units to maximize bandwidth utilization.
  - **fused_gating_masking**：Integrates the exponential gating logic (`exp(g)`) and causal masking (`m_A`) directly within the main computation loop. This fusion reduces memory traffic by avoiding the storage and reloading of intermediate attention matrices.
  - **mixed_precision_accumulation**：Performs matrix multiplications (`tl.dot`) and accumulates results in `float32` (`b_o`, `b_A`) before casting to the output dtype. This ensures numerical stability during the recurrent state updates and attention score accumulation.
  - **layout_optimization**：Handles the implicit data layout requirements for Tensor Core (MMA) operations. The code structure ensures that data loaded into registers is aligned for `tl.dot` operations, minimizing the overhead associated with layout conversions (e.g., row-major to column-major).
- **性能提升**：35%
- **边界与说明**：This kernel is designed for chunkwise linear attention or state-space models (like RWKV/Mamba). It supports variable-length sequences via `cu_seqlens` and includes logic for recurrent state updates (`h`).
- **KKB 来源**：[ssm/exp_chunk_fwd_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_chunk_fwd_001.yaml)

### exp_chunk_gated_delta_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Matrix Operations；Chunked Matrix Multiplication；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: k=>=128; v=>=128; bt=>=64；level: extreme
- **优化点**：
  - **chunked_recurrence_strategy**：The kernel implements a chunked processing strategy for the gated delta rule recurrence. By processing the sequence in blocks of size BT, it reduces the memory pressure and allows for efficient checkpointing of the hidden state h to global memory, which is crucial for long sequences.
  - **state_matrix_tiling**：The hidden state matrix h (K x V) is explicitly split into two tiles of size 128x64 (b_h1_bv1 and b_h1_bv2). This tiling strategy is designed to fit the working set into the limited high-speed memory (SRAM/Registers) of the AI Core, maximizing data reuse during the iterative update process.
  - **block_ptr_memory_access**：Utilizes tl.make_block_ptr for loading keys (k) and storing outputs (h, v_new). This abstracts complex stride calculations and enables the compiler to generate efficient vectorized memory instructions, optimizing global memory bandwidth usage.
  - **mixed_precision_accumulation**：The accumulation of the hidden state (b_h1_bv1, b_h1_bv2) is performed in FP32 to ensure numerical stability during the recurrence, while the heavy computation (tl.dot) is cast to the input data type (fp16/bf16) to leverage the high-throughput matrix units (Cube units).
  - **heuristic_compilation**：The use of @triton.heuristics allows the kernel to dynamically handle optional features like gating (g), initial states (h0), and variable length sequences (cu_seqlens) without requiring multiple kernel compilations, improving deployment flexibility.
- **性能提升**：35%
- **边界与说明**：This kernel is highly optimized for scenarios where K and V dimensions align with the 128x64 tiling strategy. It supports variable-length sequences natively via cu_seqlens.
- **KKB 来源**：[ssm/exp_chunk_gated_delta_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_chunk_gated_delta_001.yaml)

### exp_chunk_kkt_001

- **经验类型**：Compute Optimization
- **适用条件**：Matrix Operations；Matrix Multiplication；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: BT=>=64; BK=>=32; K=>=64；level: advanced
- **优化点**：
  - **block_ptr_abstraction**：Utilizes tl.make_block_ptr for all tensor loads (k, beta, g_cumsum) and stores (A). This abstracts complex pointer arithmetic, enables automatic vectorization of memory operations, and efficiently handles 2D block traversals.
  - **tiled_accumulation**：Implements a tiled reduction loop over the K dimension using block size BK. The intermediate result b_A is accumulated in registers/SRAM (float32) across iterations, significantly reducing global memory access pressure compared to a naive implementation.
  - **vectorized_masking**：Applies the causal mask and boundary checks using vectorized operations (tl.where and boundary_check flags in load/store). This avoids expensive scalar branching inside the kernel loop, improving pipeline efficiency.
  - **fused_operations**：Fuses the matrix multiplication (K @ K.T), gating (safe_exp), scaling (beta), and masking into a single kernel. This minimizes memory write-read overhead for intermediate results.
- **性能提升**：35%
- **边界与说明**：This kernel is specifically designed for chunked attention mechanisms requiring the K*K^T computation. It supports variable sequence lengths via cu_seqlens and optional gating via g_cumsum.
- **KKB 来源**：[ssm/exp_chunk_kkt_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_chunk_kkt_001.yaml)

### exp_fused_delta_rule_npu_001

- **经验类型**：Compute Optimization
- **适用条件**：Matrix Operations；Recurrent Delta Rule Update；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: K=>=64; V=>=64; T=>=1；level: advanced
- **优化点**：
  - **deep_kernel_fusion**：Fuses multiple stages including Softplus, Sigmoid, Exponential gating, Matrix-Vector multiplication (outer product), and Reductions into a single kernel. This eliminates global memory access for intermediate activations (like the gated state or intermediate projections), significantly reducing memory bandwidth pressure.
  - **register_level_state_persistence**：The recurrent hidden state 'h' (shape [BK, BV]) is maintained entirely in registers across the time dimension loop 'for i in range(T)'. This avoids the high latency of writing and reading the state back to global memory (HBM) at every timestep, which is the primary bottleneck for recurrent architectures.
  - **numerically_stable_softplus**：Implements a numerically stable Softplus activation using a threshold check ('softplus_threshold'). For inputs where 'beta_x > threshold', it defaults to the identity function 'x' to prevent overflow in 'tl.exp', ensuring robustness on NPU hardware which may have different floating point behavior than GPUs.
  - **mixed_precision_accumulation**：Explicitly promotes loaded vectors ('b_q', 'b_k', 'b_v', 'b_a', etc.) to 'tl.float32' before performing arithmetic operations. This preserves precision during the recurrent accumulation of the hidden state 'h', preventing gradient degradation or instability during long sequence inference or training.
  - **efficient_masking_and_vectorization**：Utilizes pointer arithmetic and 'tl.load' with masks to handle variable sequence lengths ('IS_VARLEN') and boundary conditions. This allows the kernel to process batches with different lengths efficiently without dynamic branching or padding overhead.
- **性能提升**：35%
- **边界与说明**：This kernel is specifically optimized for NPU architectures (like Ascend 910B) where memory bandwidth is a limiting factor. The block sizes BK and BV should be tuned based on the specific NPU's SRAM size and register file capacity to avoid spilling.
- **KKB 来源**：[ssm/exp_fused_delta_rule_npu_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_fused_delta_rule_npu_001.yaml)

### exp_kda_bwd_intra_memory_opt_001

- **经验类型**：内存访问优化
- **适用条件**：SSM；chunk_kda_bwd_intra；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: K=>=64; T=>=128；level: advanced
- **优化点**：
  - **瓶颈**：AIV MTE2=37.9%，主要由转置load非合并访存和冗余load导致
  - **优化1-转置load合并化**：Phase 2中dAqk/dAkk转置加载从stride=(1, H*BT)改为行优先加载+tl.trans寄存器转置
  - **优化2-消除冗余load**：Phase 1.5加载的b_q在Phase 2.5复用；Phase 1加载的b_b在Phase 2.5复用；b_g在Phase 1.5复用
  - **优化3-手动指针load替代block_ptr**：虽然主要目标是消除scalar，但也减少block_ptr结构体创建开销
  - **注意**：寄存器复用需考虑tl.debug_barrier()是否导致spill，需实测验证
  - **预期效果**：AIV MTE2从37.9%降至<25%
- **性能提升**：35%
- **边界与说明**：此经验与exp_perf_015通用转置load合并化技术对应，但提供了KDA intra kernel的具体上下文和mask计算示例。
- **KKB 来源**：[ssm/exp_kda_bwd_intra_memory_opt_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_kda_bwd_intra_memory_opt_001.yaml)

### exp_kda_bwd_intra_scalar_opt_001

- **经验类型**：标量消除
- **适用条件**：SSM；chunk_kda_bwd_intra；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: K=>=64; T=>=128；level: advanced
- **优化点**：
  - **瓶颈**：chunk_kda_bwd_kernel_intra实测AIV scalar_ratio=41.4%，AIC scalar_ratio=31.4%，AIC MAC=2.1%，AIV MTE2=37.9%
  - **标量根因**：28+处block_ptr load/store都带boundary_check；10+处i32 LT/GT/LE/GE mask比较；8处min()运行时分支；非SAFE_GATE路径的逐行标量循环
  - **核心优化1**：4处store和24+处load从block_ptr改为手动指针+向量化mask，消除boundary_check标量开销
  - **核心优化2**：所有mask比较（m_k, m_dA, m_i_diag_qk, m_j_diag_qk等）改为fp32比较
  - **核心优化3**：min()全部改为tl.where
  - **核心优化4**：tl.cdiv(T_local - i_t*BT, BC)改为基于rows_in_chunk的条件计算
  - **推荐顺序**：Phase1 block_ptr store→fp32比较→min→tl.cdiv；Phase2处理MTE2
  - **预期效果**：AIV scalar从41.4%降至<20%，AIC scalar从31.4%降至<15%
- **性能提升**：50%
- **边界与说明**：intra kernel与wy_dqkg_fused的差异：intra已经正确使用i32（无i64问题），但标量占比仍极高，说明block_ptr boundary_check和i32比较是主要根因。优化时需特别注意转置dAqk/dAkk加载的mask布局。
- **KKB 来源**：[ssm/exp_kda_bwd_intra_scalar_opt_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_kda_bwd_intra_scalar_opt_001.yaml)

### exp_kda_bwd_scalar_loop_to_dot_001

- **经验类型**：计算优化
- **适用条件**：SSM；chunk_kda_bwd_intra；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: BC=16; K=>=64；level: advanced
- **优化点**：
  - **问题根因**：当SAFE_GATE=False时，对角块计算使用for j in range(BC)逐行标量循环，每次4个load+标量×向量broadcast乘法，不能利用Cube加速
  - **核心方案**：将逐行循环改为矩阵操作，一次性加载整个BC×BC对角块，用2次tl.dot替代16次标量循环
  - **精度注意**：SAFE_GATE使用min(BC//2, ...)作为归一化点保证数值稳定性，非SAFE_GATE原用第0行。改为矩阵操作需保持数值一致性
  - **典型收益**：16次标量循环→2次tl.dot，AIC MAC ratio从2.1%显著提升，AIV scalar大幅下降
  - **适用条件**：对角块计算且存在逐行标量循环的SSM/Attention反向kernel
- **性能提升**：40%
- **边界与说明**：此优化将标量×向量broadcast改为矩阵乘，是提升Cube利用率的关键。但需注意gate归一化点的数值稳定性，建议与SAFE_GATE路径对比精度。
- **KKB 来源**：[ssm/exp_kda_bwd_scalar_loop_to_dot_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_kda_bwd_scalar_loop_to_dot_001.yaml)

### exp_kda_bwd_wy_scalar_opt_001

- **经验类型**：标量消除
- **适用条件**：SSM；chunk_kda_bwd_wy_dqkg_fused；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: K=>=64; V=>=64; T=>=128；level: advanced
- **优化点**：
  - **背景**：chunk_kda_bwd_kernel_wy_dqkg_fused_opt_v2在Ascend上Task Duration从~169k μs经7轮优化降至~50.7k μs（3.33x）
  - **核心优化1**：消除i64地址计算。将所有涉及i_tg/bos/eos的偏移保持i32，避免int64算术标量降级
  - **核心优化2**：i32整数比较转fp32。所有mask生成（m_t, m_k, BT_mask, BK_mask, m_A等）使用fp32比较
  - **核心优化3**：tl.cdiv(K,BK)和tl.cdiv(V,BV)改为编译期常量NK/NV，避免运行时除法取余
  - **核心优化4**：min(T, expr)改为tl.where向量化条件选择
  - **核心优化5**：移除b_h/b_dh/b_dv等冗余compile_hint，释放编译器优化空间
  - **核心优化6**：使用other=0.0替代load后的冗余tl.where清零
  - **推荐顺序**：先消除i64（收益最大）→ i32转fp32 → tl.cdiv/min优化 → 移除hint → autotune
- **性能提升**：233%
- **边界与说明**：此bundle针对wy_dqkg_fused反向kernel。关键原则是保留tl.dot架构（不逐元素展开），定向消除导致标量降级的i64/i32操作。逐元素展开虽能降低scalar ratio，但会丧失Cube加速，性能严重回退。
- **KKB 来源**：[ssm/exp_kda_bwd_wy_scalar_opt_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_kda_bwd_wy_scalar_opt_001.yaml)

### exp_kda_bwd_wy_structure_opt_001

- **经验类型**：计算优化
- **适用条件**：SSM；chunk_kda_bwd_wy_dqkg_fused；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: K=>=64; V=>=64；level: advanced
- **优化点**：
  - **优化1-Phase split**：将i_k==0分支（计算dA/dv2/db）外提为独立的V-only循环，消除内循环的条件分支
  - **优化2-barrier外提**：将tl.debug_barrier()从i_v循环内移到循环后，barrier次数从NV×NK降为NK
  - **优化3-循环不变量外提**：预计算BT_arange[:, None]*V等循环不变地址分量，循环内仅做简单偏移
  - **优化4-stride预计算**：预计算H*K和H*V，避免循环内重复乘法
  - **优化5-K%BK==0快速路径**：当K能被BK整除时，BK_mask全True，跳过mask生成
  - **注意**：Phase split需确保dv2写入完成后Phase 2才能读取dv，barrier位置需正确
  - **典型收益**：Phase split和barrier外提各贡献显著延迟下降，与其他标量消除优化叠加达到3.33x加速
- **性能提升**：30%
- **边界与说明**：此bundle聚焦kernel结构层面的优化，与标量消除优化正交互。实施时建议先完成标量消除，再做结构优化，便于独立验证每步效果。
- **KKB 来源**：[ssm/exp_kda_bwd_wy_structure_opt_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/ssm/exp_kda_bwd_wy_structure_opt_001.yaml)
