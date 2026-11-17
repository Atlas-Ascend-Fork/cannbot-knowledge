---
type: Optimization
title: 杂项优化经验聚合
description: 从 40 条杂项融合 + 17 条 Conv + 12 条 Loss + 3 条 Embedding + 2 条 Elementwise
  + 6 条 solve_tril YAML 经验中蒸馏的核心模式。
tags: [task.optimization, topic.compute.composite, topic.compute.neighborhood.convolution, topic.compute.indexing, topic.compute.elementwise.arithmetic]
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
# 杂项优化经验聚合

从小类别 YAML 经验中蒸馏的共性模式。涵盖卷积、损失函数、嵌入查找、三角求解等。

## Causal Conv1D（17 条）

| 经验 ID | 提升 | 核心优化 |
|---------|------|----------|
| [exp_causal_conv1d_prefill_002](#exp_causal_conv1d_prefill_002) | — | 滑动窗口寄存器复用：col0-3 移位，每 token 仅 1 load |
| [exp_causal_conv1d_prefill_003](#exp_causal_conv1d_prefill_003) | 1.60x | 2D Grid + BTD 布局并行 |
| [exp_causal_conv1d_prefill_006](#exp_causal_conv1d_prefill_006) | — | Conv+Bias+SiLU 三合一融合 |
| [exp_causal_conv1d_update_002](#exp_causal_conv1d_update_002) | 3.1x | W=4 循环展开 + D 阈值控制 |

## Loss 函数（12 条）

| 经验 ID | 核心优化 |
|---------|----------|
| [exp_celoss_001](#exp_celoss_001) | Online log-softmax + NLL |
| [exp_celoss_bwd_001](#exp_celoss_bwd_001) | `softmax - one_hot(label)` 单步 grad |
| [exp_celoss_smooth_001](#exp_celoss_smooth_001) | Label-Smoothed CE: (1-ε)·one_hot + ε/V uniform |

## Embedding（3 条）

| 经验 ID | 核心优化 |
|---------|----------|
| [exp_embedding_001](#exp_embedding_001) | 2D tile (M×N) + 软件流水线 |
| [exp_embedding_backward_001](#exp_embedding_backward_001) | scatter-add 原子操作 + 索引排序 |

## solve_tril（6 条）

| 经验 ID | 提升 | 核心优化 |
|---------|------|----------|
| [exp_solve_tril_001](#exp_solve_tril_001) | 1.33-1.87x | 结构零元 mask 消除 |
| [exp_solve_tril_002](#exp_solve_tril_002) | — | 寄存器预加载 + extract_slice 替代 HBM load |
| [exp_solve_tril_003](#exp_solve_tril_003) | — | Constexpr 双路径循环展开 |
| [exp_solve_tril_004](#exp_solve_tril_004) | — | BT=16/32/64 三层分级调度 |

## 经验条目与迁移锚点（KKB）

以下条目从 KKB 结构化 YAML 或 wiki 页面蒸馏，按 `### <experience_id>` 建立稳定锚点；其他知识卡可直接链接到这些锚点。原始 YAML 与完整代码保留在 KKB 仓库，作为机器索引和代码来源。

### exp_causal_conv1d_prefill_002

- **经验类型**：Memory Access Optimization
- **适用条件**：Convolution Operations；Causal Conv1D Prefill (sliding window)；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: dim=>=512; seqlen=>=32; width=4；level: advanced
- **优化点**：
  - **sliding_window_register_reuse**：将卷积窗口 `[col0, col1, col2, col3]` 维护在 4 个命名寄存器中，每次迭代只 load 一个新 token（col3），其余 3 个值从前次迭代的寄存器移位获得（col0←col1←col2←col3）。相比 reference 实现每 token 需要 4 次 load，load 次数降低 75%。对于 seq_len=2048 的典型 Prefill 场景，每个 program 节省 3×2048=6144 次全局内存 load。这是整个 kernel 中最大的单项性能提升来源。
  - **register_shift_zero_cost**：寄存器移位 `col0 = col1; col1 = col2; col2 = col3` 在编译器层面通过寄存器重命名实现，零周期开销。不同于内存拷贝或显式 shuffle，移位不产生任何实际指令。
  - **initialization_from_state**：首次迭代从 conv_states 加载 3 个历史值到 col0/col1/col2，后续 seq_len-1 次迭代每步仅 1 次 load。窗口末尾的 3 个值恰好就是需要写回 conv_states 的最后 3 个 token，无需额外 load 即可完成状态更新——状态更新与卷积计算的 load 完全复用。
  - **explicit_register_naming**：使用 4 个显式命名的寄存器（col0/col1/col2/col3）而非数组或 loop，使编译器能够：(1) 精确追踪每个寄存器的生命周期；(2) 生成最优的寄存器分配方案；(3) 将 `col0*w0 + col1*w1 + col2*w2 + col3*w3` 识别为可并行的 4 路 FMA 归约。
  - **fma_friendly_expression**：单语句 4 路归约 `col0*w0 + col1*w1 + col2*w2 + col3*w3` 中 4 个乘法相互独立，编译器可发射 4 条并行向量乘法指令；加法树结构直接映射到硬件 FMA 单元（融合乘加），一条指令完成 mul+add。相比 `for w in range(4): acc += col[w]*weight[w]` 的循环累积方式，避免了跨迭代的 out_block 数据依赖。
  - **width_hardcoded_tradeoff**：寄存器复用方案硬编码 W=4（4 个命名寄存器 + 4 个权重标量），无法支持可变 width。这是性能（零数据编排开销）与灵活性（通用 W 支持）的取舍。实践中 Mamba/SSM 架构的 width=4 是最常见配置，此取舍合理。
- **性能提升**：消除 75% 的 token load，实测贡献 Prefill kernel 整体加速比中的最大份额（与 2D Grid + DIM_IS_MULTIPLE 组合达 1.60x 平均加速比，最高 1.84x）
- **边界与说明**：滑动窗口寄存器复用是 Prefill kernel 最核心的创新，利用了 W=4 的小卷积核特性。此模式可推广到任何固定小窗口的序列处理 kernel（如移动平均、指数平滑、small-kernel 1D conv），前提是窗口大小在编译期已知且足够小（≤8）。
- **KKB 来源**：[conv/exp_causal_conv1d_prefill_002.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/conv/exp_causal_conv1d_prefill_002.yaml)

### exp_causal_conv1d_prefill_003

- **经验类型**：Scheduling Optimization
- **适用条件**：Convolution Operations；Causal Conv1D Prefill (parallel strategy)；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: dim=>=512; batch=>=1；level: advanced
- **优化点**：
  - **two_dimensional_grid_strategy**：采用 2D Grid = `(batch, cdiv(dim, BLOCK_D))` 并行方案。比 1D grid（每条序列一个 program）的优势：(1) 沿 D 维度展开并行，D=4096 时切成 4 个 BLOCK_D=1024 tile，SM 占用率 4 倍提升；(2) 每个 program 的计算密度更合理（1024 维而非 4096 维），避免寄存器溢出；(3) 遗传搜索验证：2D grid 比 1D→2D 方案低 25%，比 1D strided 方案低 39%。
  - **btd_layout_rationale**：Prefill 采用 BTD `[B, T, D]` 布局而非 Update 的 BDT。原因是 Prefill 阶段 seq_len 大（512-4096），BTD 布局下同一 token 的所有 D 维度元素连续存储（stride=1），一次 load 可获取 1024 个连续元素（32 cache lines），硬件预取高效。BDT 布局对长序列的逐 token 处理反而需要跨步访问（行间距 = seq_len），load 效率低。
  - **d_tile_only_no_t_tiling**：仅对 D 维度做 tile 化（BLOCK_D=1024），不对 T 维度做 tile 化——一个 program 处理整条序列的所有 T 个 token。原因是滑动窗口寄存器复用依赖跨 token 的寄存器移位，若 T 维度被切分，tile 边界需要跨 tile 状态传递，寄存器复用的优势会被 tile 边界处理逻辑抵消。
  - **grid_search_validated**：遗传搜索在 2 轮内收敛到 2D Grid 为全局最优：Round 1→Round 2 性能提升 26%（加入 DIM_IS_MULTIPLE + 指针预计算），Round 2→Round 3 提升 <1%（已接近硬件极限）。最终配置为 Route 1（2D Grid）+ Round 2（scalar-reduction），1.60x 平均加速比（最高 1.84x）。
- **性能提升**：2D Grid vs 1D Grid: 25-39% 性能优势（搜索验证）; 整体 Prefill kernel: 1.60x 平均加速比
- **边界与说明**：2D Grid + BTD 布局是 Prefill 阶段的架构基础决策，与 Update kernel 的 1D Grid + BDT 布局 + T-tiling 形成互补——两者针对不同的 seq_len 范围（长 vs 短）做了相反的架构选择。选择依据见 tiling.md Layout-Driven Tile Size Selection 节。
- **KKB 来源**：[conv/exp_causal_conv1d_prefill_003.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/conv/exp_causal_conv1d_prefill_003.yaml)

### exp_causal_conv1d_prefill_004

- **经验类型**：Compute Optimization
- **适用条件**：Convolution Operations；Causal Conv1D Prefill / any sequence-loop kernel；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: seqlen=>=16；level: advanced
- **优化点**：
  - **pointer_base_precompute**：将循环外可计算的地址分量（batch start offset、D-tile offset）预先计算为基址指针，循环内仅做廉价的 `+ i * stride` 偏移加法。循环外的指针计算（`start * stride + d_offs * stride_dim`）只需执行一次，循环内每次迭代省去整数乘法和完整地址重组。
  - **loop_invariant_hoisting**：属于编译器优化的手动实现——将循环不变量（loop-invariant）显式提升到循环外。在 Triton kernel 中，编译器不一定能自动识别指针表达式中的不变量（尤其当涉及多维 stride 时），手动预计算确保优化必定生效。
  - **stride_simplification**：循环内的地址增量简化为单一 stride 乘法：`x_ptrs + i * stride_x_tokens`。当 stride_x_tokens 是编译期常量时，`i * stride` 可被强度削减为累加（`addr += stride`），进一步减少乘法指令。
  - **applicability_general**：适用于所有含 token/row 维度循环的 kernel（attention、normalization、elementwise over seq_len），只要循环体内需要按照固定 stride 访问不同位置的元素。
- **性能提升**：减少 10-20% 的标量地址计算指令（取决于循环体大小），在大 seq_len 场景收益更显著
- **边界与说明**：此优化在遗传搜索 Round 2 中被引入，与 DIM_IS_MULTIPLE 共同贡献了 26% 的 Round 1→Round 2 性能提升。是通用模式，不限于 conv1d。
- **KKB 来源**：[conv/exp_causal_conv1d_prefill_004.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/conv/exp_causal_conv1d_prefill_004.yaml)

### exp_causal_conv1d_prefill_005

- **经验类型**：Scheduling Optimization
- **适用条件**：Convolution Operations；Causal Conv1D Prefill (batching)；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: batch=>=1；level: intermediate
- **优化点**：
  - **pad_slot_early_exit**：在 kernel 入口处检查 `cache_idx == pad_slot_id`（-1），匹配时立即 return，不做任何计算。释放对应的 compute unit 给其他有用的 program，提升整体硬件利用率。
  - **continuous_batching_support**：通过 cache_indices 间接映射 batch_id → cache_slot，支持：(1) beam search 场景多条序列共享同一 cache slot；(2) 动态 batch 大小（pad_slot_id=-1 标记无效序列）；(3) 无需为 padding 序列分配额外物理资源。
  - **zero_cost_skip**：`tl.load(cache_indices_ptr + pid_batch)` + `if ... return` 的开销仅为 1 次 load + 1 次整数比较，远小于执行完整卷积循环的成本（~seq_len 次 load/store/FMA）。在 batch 中有 ≥10% 填充序列时收益显著。
  - **applicability_general**：适用于所有使用间接索引映射 batch 的 kernel（如 attention with KV-cache page table、embedding lookup with dynamic indices、MoE routing），只要能用单次 load + compare 判断是否需要跳过计算。
- **性能提升**：在有 padding 序列的 batch 中节省无效计算比例（如 25% padding→~25% 资源节省）；最小开销仅 1 load + 1 cmp
- **边界与说明**：pad_slot 机制不仅节省无效计算，更重要的是让 SM/SIMT 单元可被其他有用工作抢占——在 Ascend 的 grid-stride 调度下，提前退出的 program 对应的 tile 可被重新分配给其他 tasks。
- **KKB 来源**：[conv/exp_causal_conv1d_prefill_005.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/conv/exp_causal_conv1d_prefill_005.yaml)

### exp_causal_conv1d_prefill_006

- **经验类型**：Compute Optimization
- **适用条件**：Convolution Operations；Causal Conv1D Prefill (fusion)；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: dim=any; seqlen=any; width=4；level: intermediate
- **优化点**：
  - **conv_bias_silu_triple_fusion**：将卷积计算 + Bias 加法 + SiLU 激活融合在单个 kernel 的每条 token 循环内。所有中间结果保留在寄存器中（fp32 精度），只产生一次最终的 fp16/bf16 store。相比 3 个独立 kernel launch（conv → add_bias → silu），消除了 2 次 HBM 写 + 2 次 HBM 读。
  - **fp32_activation_numerical_stability**：SiLU 激活 `acc / (1 + tl.exp(-acc))` 在 fp32 累加器上计算，而非提前 downcast 到 fp16。SiLU 中的 exp 对大负值敏感（exp(-x) → inf when x < -88 in fp16），fp32 提供足够范围避免 overflow。
  - **constexpr_fusion_control**：通过 `HAS_BIAS: tl.constexpr` 和 `ACTIVATION: tl.constexpr` 编译期开关控制融合路径。不需要 bias/activation 的场景编译器完全消除对应代码路径，零额外开销。
  - **register_resident_bias**：bias 向量在卷积循环外一次性加载到寄存器，循环内每次迭代复用。对于 seq_len=2048 的场景，节省了 2047 次重复的 bias load。
- **性能提升**：消除 2 个额外 kernel launch（延迟降低约 30-40%）；Bias 寄存器驻留节省 2047 次 load
- **边界与说明**：此融合模式是 Prefill kernel 的标准融合配置，与 Update kernel 中的 Conv1D+State+SiLU 双缓冲融合互补。两者的共同原则：激活函数必须在 fp32 上计算以保证数值稳定性。
- **KKB 来源**：[conv/exp_causal_conv1d_prefill_006.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/conv/exp_causal_conv1d_prefill_006.yaml)

### exp_causal_conv1d_update_002

- **经验类型**：Compute Optimization
- **适用条件**：Convolution Operations；Causal Conv1D Update (Decode)；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: dim=>=1024; seqlen=>=1; width=4；level: advanced
- **优化点**：
  - **w_loop_unrolling_with_threshold**：当 W=4 且 D>=1024 时，将 `for owi in range(width)` 循环展开为 4 路独立计算表达式 `x_s0*w0 + x_s1*w1 + x_s2*w2 + x_s3*w3`，消除 3 次 tl.trans 和 8 次 extract_slice 的数据编排开销。实测 D=8192 时加速比 3.1x，D=2048 时 2.3x。D<1024 时回退到原始 for 循环路径，避免小 D 场景下独立 tl.load 的启动开销占比过大导致负收益（D=128 时仅 0.41x）。
  - **d_threshold_gating**：在 host 端通过编译期常量 `W_IS_4=(width==4 and dim>=1024)` 控制是否启用展开路径。D=1024 作为阈值有足够安全边际（正收益 case 均在阈值之上，负收益 case 均在阈值之下），改动仅一行，零风险。
  - **extract_slice_elimination**：展开后消除原始路径中每次 W 迭代的 2 次 extract_slice（x_b 切片 + w 切片），W=4 时共消除 8 次 extract_slice。extract_slice 在 Triton IR 层面创建新的 tensor view（修改 offset/stride/shape 描述符），虽不移动数据但编译器必须生成独立的地址计算逻辑，消除后可减少 scalar 单元压力。
  - **transpose_elimination**：展开后消除 3 次 tl.trans 调用（x_b 转置 [D_CHK, buf]→[buf, D_CHK]、w 转置 [D_CHK, W]→[W, D_CHK]、out 回转），直接将 x_b 保持 [D_CHK_SIZE, buffer_len] 布局进行切片乘加，减少数据路径的中间步骤。
  - **fma_friendly_expression**：展开后的单语句 4 路归约 `x_s0*w0 + x_s1*w1 + x_s2*w2 + x_s3*w3` 比 4 次独立的 `out += x * w` 更容易被编译器优化为并行 FMA 指令。4 个乘法相互独立可并行发射，加法树结构可直接映射到硬件 FMA 单元。
- **性能提升**：D≥2048: 2.3x-3.1x; D≤256: 0.41x-0.75x（需阈值控制）
- **边界与说明**：此经验为 W=4 场景下的实测优化，含完整的正/负收益分析和根因诊断。核心启示：循环展开的收益取决于 D 维度大小，需要阈值控制来保留正收益、消除负收益。方案 A（D≥1024 阈值）已可落为一行改动。
- **KKB 来源**：[conv/exp_causal_conv1d_update_002.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/conv/exp_causal_conv1d_update_002.yaml)

### exp_causal_conv1d_update_003

- **经验类型**：Memory Access Optimization
- **适用条件**：Convolution Operations；Causal Conv1D Update (Decode)；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: dim=any; width=4；level: advanced
- **优化点**：
  - **make_block_ptr_hardware_acceleration**：`tl.make_block_ptr` 在 Ascend NPU 上映射为硬件 block transfer 指令（类似 DMA），一条指令搬运整个 tile，包含自动边界检查和零填充（padding_option='zero'）。这是 Ascend 专为 tile 加载优化的硬件原语，效率远高于通用标量 load 指令。在 causal_conv1d_update 中用于加载权重 `[D_CHK_SIZE, W]` 和存储输出 `[1, D_CHK_SIZE, T_CHK_SIZE]`。
  - **scalar_load_degradation**：用 4 次独立 `tl.load(weight_ptr + d_offs * width + offset, mask=mask_w)` 替代 1 次 `tl.load(make_block_ptr(...))` 会导致显著性能倒退。每条独立 load 需要独立的标量地址计算，丧失 block transfer 的 DMA 级效率。这在 W_IS_4 展开优化的负收益 case 中是首要根因。
  - **block_ptr_boundary_check**：`make_block_ptr(..., boundary_check=(0, 1))` 由硬件处理边界检查，不产生软件 mask 运算开销。配合 `padding_option='zero'`，越界访问自动填零，消除 kernel 内的显式 mask 分支。
  - **hybrid_loading_strategy**：方案 B（进阶）：保留 make_block_ptr 加载权重 tile `[D_CHK_SIZE, W]`，然后展开 W 循环手动提取各列 `w0=tl.extract_slice(w, (0,0), (D_CHK,1))`，同时消除 x_b/w/out 的 3 次 transpose。这样既保留了 block transfer 的硬件加速，又获得了循环展开的数据编排消除收益。需实测验证大 D 时 w 的 4 次 extract_slice 开销是否可忽略。
  - **weight_prefetch_leverage**：make_block_ptr 提供硬件预取提示，允许 Ascend MTE2 在 Cube 计算期间异步预取下一 tile 的权重。独立 tl.load 无法提供等效的预取语义，导致 MTE2→Vector 流水线停顿增加。
- **性能提升**：block_ptr vs scalar load: 在 D≥2048 场景差异可达 2-3x（与循环展开组合效应）
- **边界与说明**：此经验阐明 Ascend 上 make_block_ptr 与标量 tl.load 的根本差异：前者是硬件 DMA 原语，后者是通用标量指令。在性能敏感的 tile 加载路径上，应优先使用 make_block_ptr。若需手动索引权重（如 W 循环展开），应采用混合方案（block_ptr 加载 + extract_slice 切片）而非退化到独立 tl.load。
- **KKB 来源**：[conv/exp_causal_conv1d_update_003.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/conv/exp_causal_conv1d_update_003.yaml)

### exp_celoss_bwd_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Cross Entropy Loss Backward；data_type: fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: C=>=128; D=>=128；level: advanced
- **优化点**：
  - **two_pass_algorithm**：The kernel separates the reduction phase (calculating max and sum of exponents) from the gradient accumulation phase. This avoids storing the large intermediate probability matrix (C x D) in global memory, significantly reducing memory bandwidth pressure and memory footprint, at the cost of re-reading the input tensor.
  - **numerical_stability**：Implements the 'max trick' (subtracting max value before exp) during the reduction loop to prevent floating-point overflow/underflow, which is critical for the stability of Softmax calculations in fp16/bf16.
  - **block_tiling_and_autotuning**：Utilizes `BLOCK_C` and `BLOCK_D` tiling to process data chunks that fit into the SRAM/Cache. The `@triton.autotune` decorator dynamically selects the optimal block sizes based on the specific C and D dimensions to maximize hardware utilization.
  - **vectorized_masking**：Efficiently handles boundary conditions and the `ignore_index` logic using vectorized mask operations (`tl.where`, `ignore_mask`) rather than scalar branching, maintaining high pipeline throughput.
  - **stable_log_sum_exp_reduction**：The first loop implements a numerically stable reduction algorithm for the Softmax denominator. It iteratively updates `tmp_max` and `tmp_sum` using the `max` and `exp` shifting technique (`tmp_sum * tl.exp(tmp_max - cur_max) + cur_exp`). This prevents floating-point overflow/underflow when computing exponents of large logits, which is critical for large vocabulary sizes (C).
  - **two_pass_gradient_computation**：The kernel employs a two-pass strategy over the class dimension `C`. The first pass aggregates global statistics (sum of exponentials and weighted target sum), and the second pass computes the per-element gradient. This trades off increased memory traffic (reloading inputs) for significantly reduced register/Shared Memory pressure, allowing the kernel to handle large batch sizes or hidden dimensions that would otherwise spill registers.
  - **fused_label_smoothing_and_weighting**：The logic for label smoothing (`tgt * (1 - label_smoothing) + label_smoothing / C`) and sample weighting (`w`) is fused directly into the kernel loops. This eliminates the need for pre-processing the target tensor or launching separate auxiliary kernels, reducing memory footprint and kernel launch overhead.
  - **vectorized_tiled_memory_access**：The kernel utilizes 2D block tiling (`BLOCK_C` x `BLOCK_D`) to load data. It uses `tl.load` with masks to efficiently handle non-divisible dimensions, ensuring high memory bandwidth utilization while correctly processing boundary elements without padding artifacts.
- **性能提升**：35%
- **边界与说明**：This implementation prioritizes numerical stability and memory capacity over minimizing global memory loads (due to the two-pass approach). It is best suited for scenarios where C (number of classes) is large, preventing the storage of the full [N, C, D] intermediate activation matrix in SRAM.
- **KKB 来源**：[loss/exp_celoss_bwd_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/loss/exp_celoss_bwd_001.yaml)

### exp_embedding_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Indexing Operations；Embedding Lookup；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: embedding_dim=>=64; n_elements=>=32；level: advanced
- **优化点**：
  - **2D_Tiling_Strategy**：The kernel tiles the output matrix into blocks of BLOCK_SIZE_M x BLOCK_SIZE_N. This allows for vectorized memory loads and stores along the embedding dimension (N), significantly improving memory bandwidth utilization compared to row-wise processing.
  - **Software_Pipelining**：Utilizes the num_stages parameter in tl.range to enable software pipelining. This overlaps memory access operations for subsequent blocks with the current block's execution, effectively hiding global memory latency.
  - **Memory_Coalescing**：The address calculation embedding_offsets = indices[:, None] * embedding_dim + offsets_n[None, :] ensures that consecutive threads access contiguous memory locations in the embedding table, maximizing the efficiency of memory transactions.
- **性能提升**：25%
- **边界与说明**：Best suited for scenarios with large embedding dimensions where memory bandwidth is the primary bottleneck.
- **KKB 来源**：[embedding/exp_embedding_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/embedding/exp_embedding_001.yaml)

### exp_embedding_backward_001

- **经验类型**：Scheduling Optimization
- **适用条件**：Indexing Operations；Scatter Add；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: n_elements=>=1024; embedding_dim=>=128；level: advanced
- **优化点**：
  - **2D_Block_Tiling**：The kernel tiles the gradient matrix into 2D blocks (BLOCK_SIZE_M x BLOCK_SIZE_N) rather than processing rows or columns individually. This improves memory access coalescing for loading `grad_output` and maximizes the utilization of memory bandwidth by processing larger contiguous chunks per transaction.
  - **Software_Pipelining**：Utilizes `tl.range` with the `num_stages` parameter to implement software pipelining. This allows the hardware to overlap memory loads (indices and gradients) for subsequent iterations with the atomic add operations of the current iteration, effectively hiding global memory latency.
  - **Batched_Atomic_Accumulation**：Performs atomic updates on blocks of data rather than individual scalar elements. By accumulating a block of gradients before writing back, the kernel reduces the total number of atomic instructions issued and alleviates pressure on the memory subsystem, though contention remains dependent on index duplication.
- **性能提升**：35%
- **边界与说明**：This optimization is highly effective for large batch sizes and embedding dimensions. Performance may be impacted by high rates of duplicate indices due to serialization of atomic operations.
- **KKB 来源**：[embedding/exp_embedding_backward_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/embedding/exp_embedding_backward_001.yaml)

### exp_grpo_loss_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；LogSumExp Reduction；data_type: fp32, fp16, bf16；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: V=>=4096; BL=>=1；level: base
- **优化点**：
  - **numerical_stability**：Implements the iterative LogSumExp (LSE) algorithm to compute log-probabilities. This prevents floating-point overflow/underflow that is common when computing softmax over large vocabulary sizes by separating the max and sum operations.
  - **memory_chunking**：Processes the vocabulary dimension V in fixed-size blocks defined by BLOCK_SIZE_V. This allows the kernel to handle vocabulary sizes that exceed the register file capacity or shared memory limits, ensuring flexibility across different model architectures.
  - **loop_fusion_analysis**：The current implementation performs three separate reduction loops for new_logits, ref_logits, and old_logits. A critical optimization point is to fuse these three loops into a single pass. By loading chunks of all three tensors simultaneously, memory bandwidth utilization can be tripled, and cache locality can be significantly improved.
  - **compile_time_branching**：Utilizes tl.constexpr for hyperparameters like HAS_DELTA. This ensures that conditional logic related to algorithm variants is resolved during compilation, eliminating runtime thread divergence within the warp.
- **性能提升**：30%
- **边界与说明**：The kernel is currently memory-bandwidth bound due to sequential passes over the logits. Fusing the reduction loops is the primary path to performance improvement on NPU hardware.
- **KKB 来源**：[misc/exp_grpo_loss_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/misc/exp_grpo_loss_001.yaml)

### exp_idx_copy_001

- **经验类型**：Memory Access Optimization
- **适用条件**：Indexing Operations；Index Copy；data_type: int32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: c_len=>0; BLOCK_SIZE_N=>=64；level: advanced
- **优化点**：
  - **block_pointer_utilization**：The kernel utilizes `tl.make_block_ptr` for both source and destination pointers. This abstraction allows the compiler to generate optimized memory access instructions, ensuring better vectorization and cache line utilization compared to manual pointer arithmetic.
  - **ragged_tensor_handling**：By employing `boundary_check=(0,)` during load and store operations, the kernel efficiently processes variable-length sequences (ragged tensors) without requiring padding to the maximum sequence length. This minimizes memory bandwidth consumption and avoids unnecessary computation on padding tokens.
  - **early_exit_condition**：The implementation includes early exit checks (if `c_len <= 0` and if `pid_n * BLOCK_SIZE_N >= c_len`). This ensures that thread blocks corresponding to empty sequences or out-of-bounds ranges terminate immediately, freeing up SM resources for active blocks.
  - **right_padding_offset**：The source pointer calculation `(n_len - c_len)` dynamically adjusts the base address to skip right-padding. This allows the kernel to read contiguous valid data directly, optimizing memory access patterns for right-padded inputs common in transformer architectures.
- **性能提升**：25%
- **边界与说明**：This kernel is specifically designed for scenarios involving variable-length sequences and cumulative counts, such as gathering top-k indices in attention mechanisms.
- **KKB 来源**：[embedding/exp_idx_copy_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/embedding/exp_idx_copy_001.yaml)

### exp_solve_tril_001

- **经验类型**：Compute Optimization
- **适用条件**：Linear Algebra Operations；Triangular Matrix Inverse / solve_tril / structured matrix element access；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；level: intermediate
- **优化点**：
  - **redundant_mask_elimination_by_matrix_property**：当矩阵具有已知结构零元（严格下三角、对角、上三角等）时，对已为零的元素再次施加的 `tl.where(mask, val, 0.)` 是冗余 ALU 指令。Triton 编译器可能无法在运行时变量 `i` 驱动的循环中优化掉这类掩码。直接删除冗余掩码，依赖矩阵结构本身保证零值位置正确。
  - **strictly_lower_triangular_case**：对于严格下三角矩阵 A（A[i,j]=0 for j≥i），循环体内 `b_a = tl.where(o_i < i, b_a, 0.)` 是恒等变换——`b_a` 从 A 加载后取反，j≥i 位置已经是 0。删除后精度不变、性能提升 1.33x-1.87x（BT=16, 14 次迭代节省 14 条 where 指令）。
  - **applicability_general**：适用于所有处理具备已知结构零元的矩阵 kernel：三角矩阵（tril/triu）、对角矩阵、带状矩阵、mask 矩阵。只要矩阵元素在特定位置的零值由数学保证而非运行时条件决定，对应的保护性 mask 即可删除。
  - **tl_where_cost**：`tl.where(condition, a, b)` 在 Ascend NPU 上需要：(1) condition 比较指令；(2) 逐元素 select 指令。对 16 元素向量每次迭代省 16 次 cmp + 16 次 select，14 次迭代累计 448 条 scalar 指令。
- **性能提升**：1.33x-1.87x（BT=16 kernel）；~1.40x（BT=64 kernel）；BT=32 无此冗余故无变化
- **边界与说明**：此为 V1 优化。从 fla 仓库原始代码中识别出的冗余模式——原始代码直接复用了 merge kernel 的代码模式，未针对 16×16 做差异化处理。BT=32 kernel 原本就没有此掩码。
- **KKB 来源**：[solve_tril/exp_solve_tril_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/solve_tril/exp_solve_tril_001.yaml)

### exp_solve_tril_002

- **经验类型**：Memory Access Optimization
- **适用条件**：Linear Algebra Operations；Triangular Matrix Inverse / solve_tril / preload register block extract；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: block_size=16；level: intermediate
- **优化点**：
  - **preload_extract_slice_eliminate_hbm_read**：当矩阵块已在循环外通过单次 `tl.load(block_ptr)` 加载到寄存器后，循环内不应再用 `tl.load(A + row_offset)` 逐行重新从 HBM 读取。虽然 Triton 不支持 `b_A[i, :]` 动态寄存器索引，但可以使用 `tl.extract_slice(neg_A, (i, 0), (1, 16), (1, 1))` + `tl.reshape` 从寄存器块提取行数据，完全消除循环体内的 HBM 访问。
  - **why_triton_cannot_dynamic_index**：`b_A[i, :]` 在 Triton 中会报错 `ValueError('unsupported tensor index: int32[]')`——i 是运行时 int32，Triton 的 block tensor 不支持运行时动态索引。`tl.extract_slice` 是 Triton 支持的寄存器块子集提取原语，offset 为运行时变量时生成动态偏移指令（开销低于 global load）。
  - **preload_pattern**：循环前预加载并取反：`neg_A = -b_A`（或保留原值）。循环内 `b_a = tl.extract_slice(neg_A, (i, 0), (1, BLOCK), (1, 1))` + `b_a = tl.reshape(b_a, (BLOCK,))`。BLOCK=16 时 reshape 零开销。
  - **multi_block_extension**：对于分块矩阵（如 32×32 有 2 个对角块、64×64 有 4 个对角块），每个对角块独立预加载并独立 extract_slice，块间无依赖。
  - **tradeoff_analysis**：小 grid（B=1, T=512）场景下 preload 的额外寄存器操作开销可能与省下的 global load 抵消（实测 1.01x）。大 grid 场景累计效益显著（1.37x）。选择始终使用 extract_slice 可统一代码路径。
- **性能提升**：1.01x-1.37x（BT=16, V4 vs V1）；1.25x-1.27x（BT=32, V4 vs V1，首次优化）；1.11x-1.13x（BT=64, V4 vs V1）
- **边界与说明**：此为 V4 优化的核心。与 V1（[exp_solve_tril_001](#exp_solve_tril_001)）组合后，ORIGINAL vs V4 累计加速比：BT=16 达 1.42x-2.54x，BT=32 达 1.26x-1.29x，BT=64 达 1.55x-1.57x。
- **KKB 来源**：[solve_tril/exp_solve_tril_002.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/solve_tril/exp_solve_tril_002.yaml)

### exp_solve_tril_003

- **经验类型**：Compute Optimization
- **适用条件**：Linear Algebra Operations；Triangular Matrix Inverse / solve_tril / constexpr loop unrolling dual path；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: block_size=16, 32, 64；level: intermediate
- **优化点**：
  - **constexpr_dual_path_full_vs_boundary**：当 kernel 处理固定大小 tile 时，绝大多数 chunk 是完整 tile（99%），仅最后一个可能是边界不完整 tile。用 `if T - chunk_offset >= BT` 分支：(1) 快速路径使用 `range(2, BT)` 其中 BT 是 `tl.constexpr`，编译器完全展开循环 + extract_slice offset 静态优化为零开销；(2) 慢速路径使用运行时 `range(2, min(16, remaining))`，仍从寄存器提取数据。两个路径统一数据来源（均 extract_slice），区别仅在于循环展开程度。
  - **constexpr_static_unroll_benefit**：`range(2, BT)` 当 BT 是 constexpr 时，Triton 编译器在编译期：(1) 完全展开循环体；(2) extract_slice 的 offset 参数 `(i, 0)` 中的 i 为编译期常量，生成静态偏移指令（零 ALU）；(3) 消除循环分支预测开销。
  - **boundary_path_still_register**：慢速（边界）路径虽然循环未展开，但同样使用 extract_slice 从预加载的寄存器块读取——消除 HBM 访问的收益对所有 chunk 均等。
  - **excluded_approaches**：被排除的方案：(a) 统一运行时循环（失去 constexpr 展开优化，性能回退到 V1 水平）；(b) 慢速路径保留 tl.load（不如 extract_slice 统一简洁，且边界块 HBM 读取无性能优势）。
  - **applicability**：适用于所有以固定 tile 处理数据、且 tile 大小是 constexpr 的 kernel。只要存在'完整 tile'和'边界不完整 tile'两种情况，即可用此双路径模式。
- **性能提升**：此模式保证快速路径（99% chunk）达到最优展开性能，避免统一运行时循环导致的性能退化
- **边界与说明**：此为 V4 最终方案的路径选择策略（V4 混合模式）。V3（统一运行时循环）被排除——虽然代码更简洁，但失去 constexpr 展开后性能回退到 V1 水平。
- **KKB 来源**：[solve_tril/exp_solve_tril_003.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/solve_tril/exp_solve_tril_003.yaml)

### exp_solve_tril_004

- **经验类型**：Scheduling Optimization
- **适用条件**：Linear Algebra Operations；Triangular Matrix Inverse / solve_tril / hierarchical kernel dispatch；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: block_size=16, 32, 64；level: architecture
- **优化点**：
  - **three_tier_hierarchical_dispatch**：根据 BT（块大小）选择不同 kernel：BT=16 直接用 `solve_tril_16x16_kernel`（基础递推）；BT=32 用 `merge_16x16_to_32x32_inverse_kernel`（4 块分治 + 1 次 merge）；BT=64 用 `merge_16x16_to_64x64_inverse_kernel`（16 块分治 + 多层 merge）。每个 kernel 内部保持 16×16 为基本计算单元（NPU 矩阵计算最优粒度）。
  - **block_recursive_inverse_formula**：分块求逆递推公式：`X[i,j] = -X[i,i] · Σ_{k=j}^{i-1} A[i,k] · X[k,j]`。与标量递推 `X[i,j] = -A[i,j] - Σ A[i,k]·X[k,j]` 在数学结构上完全一致——前者逐块，后者逐元素。统一性使得代码逻辑在不同层级可复用。
  - **divide_and_conquer_merge**：BT=32 将 32×32 矩阵分为 4 个 16×16 块，计算对角块逆后通过 `X₂₁ = -X₂₂ · A₂₁ · X₁₁` 合并。BT=64 分 16 个块，需要 3 层合并（紧邻→隔行→最远），共 7 次 16×16 tl.dot。
  - **grid_parallelism**：grid = (NT, B×H)，所有 chunk 内的所有 (batch, head) 对完全独立并行。NT = T/BT（定长）或 len(chunk_indices)（变长）。
  - **atomic_unit_16x16**：所有层级统一以 16×16 为原子计算单元（tl.dot / 逐行递推），匹配 NPU Cube 单元的最优粒度。
- **性能提升**：通过分治将 O(BT³) 求逆降为 O(BT²) 的递推 + O(BT) 个 16×16 矩阵乘法
- **边界与说明**：此架构是算子设计层面的决策，非后期优化。16×16 原子单元的选择由 NPU 矩阵乘法硬件决定。
- **KKB 来源**：[solve_tril/exp_solve_tril_004.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/solve_tril/exp_solve_tril_004.yaml)

### exp_solve_tril_005

- **经验类型**：API Usage / Compatibility
- **适用条件**：Linear Algebra Operations；Triangular Matrix Inverse / solve_tril / CANN compatibility；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3；tensor_shape: nd；level: basic
- **优化点**：
  - **cann_incompatible_parameter_removal**：CANN 不同版本支持的编译参数不同。以下参数在 CANN 8.5.0 上不支持或不兼容，应从 kernel launch 或 wrapper 中删除：`limit_auto_multi_buffer_of_local_buffer='no-limit'`（CANN 8.5.0 未实现）、`sync_solver=True`（CANN 8.5.0 不支持同步 solver）、`num_stages=2`（TMA 异步拷贝依赖，USE_TMA=False 时无效）。保留这些参数可能导致编译错误或警告。
  - **version_aware_parameter_audit**：从第三方仓库（如 fla）迁移 kernel 时，必须审计所有编译参数和 launch option 与目标 CANN 版本的兼容性。特别是 `tl.range(..., num_stages=N)` 中的 num_stages 依赖 USE_TMA 能力，而在 Ascend 上 TMA 通常不可用。
  - **tma_unavailable**：Ascend 910b 上 USE_TMA=False（CANN 8.5.0），TMA（Tensor Memory Access）异步拷贝不可用。依赖 TMA 的参数（num_stages、sync_solver 等）均为无效参数。
- **性能提升**：无性能影响（参数在 CANN 8.5.0 上本就不生效），消除编译警告/错误
- **边界与说明**：此经验适用于所有从外部仓库（fla、vllm、flash-attention 等）迁移到 Triton-Ascend 的 kernel。迁移时务必逐项审计 launch option 和编译参数。
- **KKB 来源**：[solve_tril/exp_solve_tril_005.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/solve_tril/exp_solve_tril_005.yaml)

### exp_celoss_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Cross Entropy Loss；data_type: fp16, bf16, fp32；hardware: 910b2, 910b3, 91093, 91095；tensor_shape: nd；core_param: C=>=128; D=>=1；level: advanced
- **优化点**：
  - **numerical_stability**：Implements the Online LogSumExp algorithm within the reduction loop. By iteratively tracking the maximum value (`tmp_max`) and scaling the exponential sum (`tmp_sum`), the kernel prevents floating-point overflow/underflow that typically occurs when computing `log(sum(exp(x)))` on large logits.
  - **vectorized_memory_access**：Utilizes 2D tiling strategy with `BLOCK_C` and `BLOCK_D` to load input logits. This maximizes global memory bandwidth utilization by reading contiguous chunks of data and aligning with the hardware's cache line size, reducing the number of memory transactions.
  - **compilation_optimization**：Applies `do_not_specialize=["ignore_index"]` in the JIT decorator. This prevents the compiler from generating a unique kernel version for every distinct `ignore_index` value, significantly reducing compilation time and binary size while maintaining runtime flexibility.
  - **conditional_masking**：Handles the `ignore_index` logic using vectorized boolean masks (`ignore_mask`) applied to the weights and outputs. This approach avoids expensive conditional branching (divergence) within the GPU/NPU threads during the calculation phase.
  - **online_logsumexp**：Implements a numerically stable LogSumExp algorithm by iteratively updating the maximum value (`tmp_max`) and the sum of exponentials (`tmp_sum`) in chunks. This prevents floating-point overflow or underflow during the reduction over the class dimension `C`, which is critical for training stability.
  - **operator_fusion**：Fuses the label smoothing operation (`tgt * (1.0 - label_smoothing) + label_smoothing / C`) and the weighting application directly into the loss calculation loop. This eliminates the need for separate kernel launches and intermediate global memory storage for the smoothed labels.
  - **memory_tiling**：Utilizes block-based processing with `BLOCK_C` and `BLOCK_D` to load sub-matrices of the input and target tensors. This optimizes data reuse in cache/SRAM and reduces the pressure on global memory bandwidth, especially beneficial when the class dimension `C` is large.
- **性能提升**：35%
- **边界与说明**：The kernel employs a two-pass strategy (one for LogSumExp, one for Loss calculation) to balance register pressure and memory bandwidth. This is highly efficient for scenarios where C is large, as it avoids keeping the entire C dimension in registers.
- **迁移归一**：目标仓库原引用为旧 ID（celoss_fwd），KKB 303 条 YAML 中无该 ID，按 online log-softmax + NLL 语义归一到本锚点。
- **KKB 来源**：[loss/exp_celoss_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/loss/exp_celoss_001.yaml)

### exp_celoss_smooth_001

- **经验类型**：Compute Optimization
- **适用条件**：Reduction Operations；Cross Entropy Loss with Label Smoothing；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: C=>=1024; D=>=1；level: advanced
- **优化点**：
  - **numerical_stability**：Implements the Log-Sum-Exp trick (calculating max, then exp(x-max), then log(sum) + max) to prevent overflow/underflow when computing softmax probabilities in low precision (fp16/bf16).
  - **two_pass_algorithm**：Separates the computation into two passes over the class dimension. The first pass calculates the log-partition function (normalization term), and the second pass computes the weighted loss. This avoids redundant expensive exponential and logarithmic calculations during the loss accumulation.
  - **vectorized_batch_processing**：Utilizes BLOCK_D to process multiple samples (or sequence tokens) in parallel within a single kernel thread. This maximizes memory bandwidth utilization and instruction throughput by amortizing the loop overhead over the batch dimension.
  - **efficient_smoothing_logic**：Uses vectorized `tl.where` operations to apply label smoothing factors based on target indices, avoiding scalar loops or complex gather operations for the smoothing distribution.
- **性能提升**：30%
- **边界与说明**：This kernel reads the input tensor twice (once for max/sum, once for loss). It is optimized for scenarios where C (number of classes) is large (e.g., vocabulary size in LLMs).
- **迁移归一**：目标仓库原引用为旧 ID（ls_celoss），按 Label-Smoothed CE 语义归一到本锚点。
- **KKB 来源**：[loss/exp_celoss_smooth_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/loss/exp_celoss_smooth_001.yaml)

### exp_fused_entropy_001

- **经验类型**：Compute Optimization
- **适用条件**：Matrix Operations；Matrix Multiplication fused with Softmax；data_type: fp16, bf16；hardware: 910b2, 910b3；tensor_shape: nd；core_param: num_tokens=>=32; hidden_size=>=128; vocab_size=>=256；level: advanced
- **优化点**：
  - **operator_fusion**：The kernel fuses the GEMM computation (hidden @ weight.T) with the Softmax reduction and Entropy calculation. By fusing these stages, the kernel avoids materializing the massive intermediate logits matrix (size num_tokens x vocab_size) to global memory, significantly reducing memory bandwidth pressure.
  - **online_softmax_algorithm**：Implements a numerically stable online softmax reduction within the main loop over the vocabulary dimension. It iteratively updates the global maximum (_max) and the sum of exponentials (_accu) using the coefficient exp(old_max - new_max), allowing for correct softmax calculation without storing all logits simultaneously.
  - **tensor_parallelism_support**：The kernel is designed to work with Tensor Parallelism by processing vocab_per_split. It computes partial maximums, accumulations, and entropy terms per split, which are typically reduced in a subsequent step, enabling efficient scaling of large vocabulary models.
  - **autotuning_strategy**：Utilizes @triton.autotune to select optimal block sizes (BLOCK_SIZE_M, BLOCK_SIZE_N, BLOCK_SIZE_K) and pipeline configurations (num_stages, num_warps) based on runtime input dimensions, ensuring high occupancy across different batch sizes and vocabulary lengths.
- **性能提升**：60%
- **边界与说明**：This kernel is specifically optimized for the final layer of Large Language Models (LLMs) where the vocabulary size is large. It is most effective when the vocabulary dimension is split across multiple devices (TP).
- **迁移归一**：目标仓库原引用为旧 ID（entropy_loss），按 Entropy Loss 语义归一到本锚点。
- **KKB 来源**：[loss/exp_fused_entropy_001.yaml](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/raw/experiences/loss/exp_fused_entropy_001.yaml)

### exp_elem_vec_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：大张量连续 load/store
- **核心优化**：BLOCK_SIZE=1024/2048，连续地址向量化 load/store
- **性能提升**：30%
- **KKB 来源**：[ops/elementwise.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/elementwise.md)

### exp_elem_vec_002

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：非连续内存输入
- **核心优化**：kernel 前调用 .contiguous() 保证连续布局
- **性能提升**：15%
- **KKB 来源**：[ops/elementwise.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/elementwise.md)

### exp_elem_vec_003

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：不同规模张量
- **核心优化**：autotune {256,512,1024,2048,4096} 选择块大小
- **性能提升**：20%
- **KKB 来源**：[ops/elementwise.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/elementwise.md)

### exp_elem_vec_005

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：指令级并行不足
- **核心优化**：单次 load+compute+store 拆为多个小 tile 循环
- **性能提升**：20%
- **KKB 来源**：[ops/elementwise.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/elementwise.md)

### exp_elem_vec_006

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：int64 比较算子
- **核心优化**：int64→fp32 转换，避免 CMP 退化为标量
- **性能提升**：25%
- **KKB 来源**：[ops/elementwise.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/elementwise.md)

### exp_elem_fusion_001

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：激活紧跟 matmul
- **核心优化**：激活函数内联进 matmul kernel，消除独立 elementwise kernel
- **性能提升**：35%
- **KKB 来源**：[ops/elementwise.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/elementwise.md)

### exp_elem_fusion_004

- **经验类型**：KKB wiki 经验（未落入 303 条结构化 YAML）
- **适用场景**：激活+量化组合
- **核心优化**：激活与量化在单 kernel 内融合完成
- **性能提升**：30%
- **KKB 来源**：[ops/elementwise.md](https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/ops/elementwise.md)
