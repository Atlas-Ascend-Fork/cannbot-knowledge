---
type: Optimization
title: MatMul/GEMM 优化经验聚合
description: 从 38 条 MatMul YAML 经验中蒸馏的核心优化模式：L0 Tiling、对角 Core Mapping、NZ Layout、融合变体与硬件特定优化。
tags: [task.optimization, topic.compute.composite, topic.programming_model.execution_unit.cube, topic.tiling, topic.memory]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Linear_Algebra_Ops/dot.md
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/third_party/ascend/tutorials/03-matrix-multiplication.py
  role: example
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences
  role: evidence
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/tree/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages
  role: evidence
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-03T02:20:00Z'
platforms: [a2, a3]
---
# MatMul/GEMM 优化经验聚合

从 38 条 MatMul YAML 经验中蒸馏的核心优化模式。按提升幅度降序排列。

## 共性模式

所有 MatMul 优化共享三条基石：
1. **L0 级 Tiling**：BLOCK_M/N∈{128,256}, BLOCK_K=256，对齐 Cube L0 访存粒度
2. **fp32 累加**：中间结果在 L0C 寄存器中以 fp32 累积，最终 cast 回目标 dtype
3. **Autotune**：GROUP_SIZE∈{8,16,32}，num_stages=2，num_warps=4

## 高质量经验汇总

| 经验 ID | 提升 | 核心优化 | 适用条件 |
|---------|------|----------|----------|
| [exp_matmul_001](#exp_matmul_001) | 40% | L0 128³ Tiling + L0C 寄存器复用 | M,N≥256, K≥1024, fp16/bf16 |
| [exp_matmul_002](#exp_matmul_002) | 35% | Cube fixpipe 量化 + 4×K 展开 | M,N≥128, K≥128, fp16, NZ |
| [exp_matmul_005](#exp_matmul_005) | 32% | M=256,K=256,N=128 双转置专项 | trans_a & trans_b |
| [exp_matmul_diag_tiling_001](#exp_matmul_diag_tiling_001) | 25% | 对角 Tiling 消除 bank conflict | M,N≥512 |
| [exp_matmul_mem_001](#exp_matmul_mem_001) | 30% | L0C 寄存器复用，避免重复加载 | 所有 matmul |
| [exp_matmul_sched_003](#exp_matmul_sched_003) | 25-35% | Persistent Kernel grid-stride | n_rows >> num_cores |
| [exp_matmul_sched_004](#exp_matmul_sched_004) | 30% | dl.async_task Cube/Vector 并行 | 含后处理激活 |
| [exp_grouped_matmul_001](#exp_grouped_matmul_001) | 30% | 分组矩阵乘 work-stealing | MoE grouped GEMM |
| [exp_matmul_hw_001](#exp_matmul_hw_001) | 30% | grouped_launch_diagonal | 硬件级对角映射 |
| [exp_matmul_hw_004](#exp_matmul_hw_004) | 35% | Cube/Vector 分离调度 | 异构并行 |

## 融合变体

| 融合 | 提升 | 说明 |
|------|------|------|
| GEMM + GELU/SiLU | 30% | L0C 寄存器上直接施加激活 |
| GEMM + Bias | 15% | fixpipe 后处理 |
| GEMM + RoPE | 25% | 投影后直接旋转 |
| GEMM + RMSNorm | 30% | 归一化融合 |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_gemma_rmsnorm_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Reduction Operations；RMSNorm + Element-wise Add；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: dim=>=1024; batch=>=32；level: advanced
- **优化点**：
  - **operator_fusion**：Fuses the residual addition (hidden_state + residual) and RMSNorm operations into a single kernel. This eliminates the need to write and read back the intermediate addition result from global memory, significantly reducing memory bandwidth pressure.
  - **weight_hoisting**：The weight tensor is loaded inside the row processing loop. An optimization is to move the weight loading statement outside the `for row_start` loop. Since weights are constant across the batch, this ensures the data is loaded once and kept in registers or cache, minimizing redundant global memory accesses.
  - **vectorized_reduction**：Utilizes `tl.sum` on the squared values to compute variance efficiently. This maps well to the vector units of the target hardware, allowing for parallel reduction of the `dim` axis.
  - **precision_control**：Performs the reduction (variance calculation) in `float32` to maintain numerical stability, while keeping the loads and stores in the lower precision `fp16`/`bf16` to optimize memory throughput.
- **性能提升**：35%
- **边界与说明**：This kernel implements the specific Gemma variant of RMSNorm where the weight is effectively added by 1.0 (w + 1.0) during scaling. It is optimized for scenarios where the hidden dimension is large enough to saturate the memory bus.
- **KKB 来源**：[matmul/exp_gemma_rmsnorm_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/matmul/exp_gemma_rmsnorm_001.yaml)

### exp_grouped_matmul_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Matrix Operations；Grouped Matrix Multiplication；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: M=>=32; N=>=32; K=>=32；level: advanced
- **优化点**：
  - **dynamic_load_balancing**：The kernel implements a dynamic scheduling strategy within the main loop (`for cur_block in range(cur_block, cur_count, total_cores)`). This allows a single kernel launch to handle multiple matrix multiplications with varying M dimensions (groups), efficiently distributing work across all available cores to prevent idle time caused by uneven group sizes.
  - **hardware_specific_hints**：Utilizes `tl.compile_hint(..., "dot_pad_only_k")` to explicitly instruct the compiler to pad operands only along the K dimension for the dot product instruction. This is critical for Ascend NPU hardware (910B series) to ensure the matrix unit (Cube) operates efficiently without unnecessary memory overhead or instruction constraints violations.
  - **pointer_arithmetic_optimization**：Optimizes memory access patterns for the 'bNmajor' layout by calculating base pointers (`a_ptrs_base`, `b_ptrs_base`) using offsets that incorporate the group index (`group_idx`). This ensures that while iterating through the K dimension, the memory accesses remain coalesced and aligned with the hardware's expectation for grouped operations.
  - **dynamic_load_balancing**：Implements a core rotation mechanism using modulo arithmetic on `last_count` to distribute blocks of different groups across cores. This mitigates the "tail effect" in grouped GEMMs where cores might idle waiting for the last group to finish.
  - **compile_hint_optimization**：Utilizes `tl.compile_hint(..., "dot_pad_only_k")` to instruct the compiler backend (likely CANN for Ascend) to optimize padding specifically for the K-dimension in dot product instructions, reducing instruction overhead.
  - **on_chip_transpose**：Performs `tl.trans(a)` immediately after loading to align the data layout for the `tl.dot` operation, ensuring efficient vectorization without requiring pre-transposed global memory layouts.
- **性能提升**：25%
- **边界与说明**：Specifically designed for K-grouped matrix multiplication where the K dimension varies per group. The dynamic scheduling is critical for performance when group sizes vary significantly.
- **KKB 来源**：[matmul/exp_grouped_matmul_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/matmul/exp_grouped_matmul_001.yaml)

### exp_matmul_001

- **经验类型**：访存优化
- **适用条件**：AIC；矩阵乘法；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: m=>=256; n=>=256; k=>=1024；level: extreme
- **优化点**：
  - **分块策略**：L0级Tile采用128x128x128块划分，适配910b2/910b3 Cube L0层访存粒度
  - **数据排布**：输入张量nd保持不变，减少重排开销
  - **寄存器复用**：中间结果存入L0C，提升数据复用
- **性能提升**：40%
- **边界与说明**：适用于m/n/k≥256的大尺寸矩阵，小尺寸矩阵建议使用128分块
- **KKB 来源**：[matmul/exp_matmul_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/matmul/exp_matmul_001.yaml)

### exp_matmul_002

- **经验类型**：计算优化
- **适用条件**：AIC；矩阵乘法；data_type: fp16；hardware: 910b2, 910b3；tensor_shape: nz；core_param: m=>=128; n=>=128; k=>=128；level: extreme
- **优化点**：
  - **量化融合**：将fp16计算与Cube fixpipe随路量化融合，提升计算效率
  - **循环展开**：展开K维循环，减少分支判断开销
  - **内存预取**：使用triton.preload做数据预取，隐藏访存延迟
- **性能提升**：35%
- **边界与说明**：仅适配Triton框架，
- **KKB 来源**：[matmul/exp_matmul_002.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/matmul/exp_matmul_002.yaml)

### exp_matmul_005

- **经验类型**：切分优化
- **适用条件**：AIC；矩阵乘法；data_type: float, float16, bfloat16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: m=>=256; n=>=128; k=>=256；level: high
- **优化点**：
  - **分块策略**：按M0=256、K0=256、N0=128划分分块行宽，适配Ascend后端512B整数倍要求
  - **带宽优化**：双转置场景下优先保证M0/K0对齐512B，平衡N0的访存效率
  - **数据排布**：转置后矩阵指针计算适配分块规则，减少内存重排开销
- **性能提升**：32%
- **边界与说明**：适用于A、B矩阵均转置的matmul场景，M0=256、K0=256满足512B整数倍，N0=128适配转置后的数据排布
- **KKB 来源**：[matmul/exp_matmul_005.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/matmul/exp_matmul_005.yaml)

### exp_matmul_diag_tiling_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Matrix Operations；Matrix Multiplication；data_type: bf16, fp16, fp32；hardware: 910b2, 910b3；tensor_shape: nd；core_param: m=>=512; n=>=512; k=>=256；level: advanced
- **优化点**：
  - **diagonal_tiling_strategy**：Replaces the traditional row-major (horizontal) core splitting with an 8x8 diagonal tiling strategy. The kernel calculates task indices (`task_m_idx`, `task_n_idx`) such that program IDs are mapped to blocks along the diagonal of the MxN grid, rather than filling rows sequentially.
  - **bank_conflict_mitigation**：In horizontal splitting, multiple cores simultaneously access the same row of the left matrix (mat_a), causing severe bank conflicts. Diagonal tiling distributes these accesses across different memory banks, significantly improving memory access bandwidth and efficiency.
  - **l2_cache_locality_optimization**：Horizontal splitting requires loading the entire right matrix (mat_b) for each row of the output, often exceeding L2 cache capacity and causing thrashing. Diagonal tiling reuses active blocks of mat_b across adjacent diagonal steps, greatly increasing L2 cache hit rates and reducing global memory access latency.
  - **adaptive_thresholding**：Introduces a `BLOCK_TRESHHOLD` parameter (tuned between 4-8) to conditionally enable diagonal tiling. This ensures the optimization is only applied when the matrix dimensions are large enough to justify the scheduling overhead, falling back to standard tiling for smaller shapes.
  - **diagonal_tiling_strategy**：将传统行主序（水平）分核替换为 8×8 对角线分块策略。Kernel 通过计算 `task_m_idx`、`task_n_idx`，将 program ID 映射到 MxN 网格的对角线方向， 而非逐行顺序填充。具体实现中，利用当前块在局部 BLOCK_TRESHHOLD×BLOCK_TRESHHOLD 子格内的相对位置（`localRelativeBlock`），结合最小公倍数（lcm）求解 N 轴坐标， 确保同一时刻各核心访问的任务块在 M、N 方向均匀分布。
  - **bank_conflict_mitigation**：水平分核时，同一时刻大量核心并发访问左矩阵（mat_a）的同一行数据，引发严重 Bank 冲突，硬件访问效率显著下降。对角线分块将各核心的访问分散至不同内存 Bank， 从根本上消除冲突热点，大幅提升内存访问带宽与效率。
  - **l2_cache_locality_optimization**：水平分核完成一整行 mat_c 的计算后，已将右矩阵（mat_b）全部数据消费完毕； 当 mat_b 较大时将超出 L2 Cache 容量，导致频繁换入换出（Cache Thrashing）， 后续每行均产生大量 Cache Miss。对角线分块使相邻对角步骤间可复用 mat_b 的活跃 数据块，显著提升 L2 Cache 命中率，降低全局内存访问延迟。
  - **adaptive_thresholding**：引入可调参数 `BLOCK_TRESHHOLD`（通过 autotune 在 4～8 范围内搜索最优值）， 仅当 M、N 方向的块数均不低于该阈值时（即 `NUM_BLOCKS_M >= BLOCK_TRESHHOLD and NUM_BLOCKS_N >= BLOCK_TRESHHOLD`）才启用对角线分块；否则回退至传统顺序 分核，避免小矩阵场景下调度开销得不偿失。
  - **block_size_tuning**：autotune 搜索空间覆盖两组基础分块配置： （1）BLOCK_M=128, BLOCK_N=256, BLOCK_K=256； （2）BLOCK_M=256, BLOCK_N=128, BLOCK_K=256。 两组配置均与 NPU 芯片亲和的 512B 对齐场景匹配，结合 `BLOCK_TRESHHOLD` 共同 构成 10 个候选 Config，以 [M, N, K] 为 key 进行离线调优。
  - **instruction_level_hint**：对 `mat_a_block` 与 `mat_b_block` 均调用 `tl.compile_hint(tensor, "dot_pad_only_k")`， 指示编译器仅在 K 轴方向进行 Pad 补齐，避免不必要的 M/N 轴 Pad，降低无效计算量， 提升指令执行效率。
  - **core_parallel_launch**：以硬件实际 AI Core 数（`num_aicore`，通过 `driver.active.utils.get_device_properties` 动态获取）作为 grid size 启动 Kernel，每个 Core 通过步长为 `num_cores` 的循环 处理多个任务块，实现负载均衡与全核心利用。
  - **autotune_config**：{'search_space': {'BLOCK_M': [128, 256], 'BLOCK_N': [256, 128], 'BLOCK_K': [256], 'BLOCK_TRESHHOLD': [4, 5, 6, 7, 8]}, 'total_configs': 10, 'tune_key': ['M', 'N', 'K']}
- **性能提升**：25%
- **边界与说明**：本优化专为昇腾 910B 大规模矩阵场景设计，核心目标是缓解内存带宽压力与 L2 Cache 容量 瓶颈。对角线分核在 M、N 方向均超过 BLOCK_TRESHHOLD 个基本块时生效，右矩阵大小超过 L2 Cache 容量时优化效果尤为显著。输出结果以 bfloat16 写回（`mat_c_block.to(tl.bfloat16)`）， 中间累加保持 float32 精度以保证数值稳定性。
- **KKB 来源**：[matmul/exp_matmul_diag_tiling_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/matmul/exp_matmul_diag_tiling_001.yaml)

### exp_matmul_mem_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：Matmul 重复加载
- **核心优化**：中间结果常驻 L0C，K 轴迭代完成后一次写回
- **性能提升**：30%
- **KKB 来源**：[ops/matmul.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/matmul.md)

### exp_matmul_sched_003

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：Matmul launch 开销
- **核心优化**：grid_stride_loop 固定核数，减少 launch 开销
- **性能提升**：25–35%
- **KKB 来源**：[ops/matmul.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/matmul.md)

### exp_matmul_sched_004

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：Cube/Vector 串行
- **核心优化**：dl.async_task 让 Cube 与 Vector 单元并行流水
- **性能提升**：30%
- **KKB 来源**：[ops/matmul.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/matmul.md)

### exp_matmul_sched_006

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：MoE grouped GEMM
- **核心优化**：动态 work-stealing 均衡专家负载
- **性能提升**：25%
- **KKB 来源**：[ops/matmul.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/matmul.md)

### exp_matmul_hw_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：Matmul 对角遍历
- **核心优化**：grouped_launch_diagonal 生成对角 PID，消除 bank conflict
- **性能提升**：30%
- **KKB 来源**：[ops/matmul.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/matmul.md)

### exp_matmul_hw_004

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：异构并行
- **核心优化**：Cube 与 Vector 单元独立调度，重叠计算与搬移
- **性能提升**：35%
- **KKB 来源**：[ops/matmul.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/matmul.md)
