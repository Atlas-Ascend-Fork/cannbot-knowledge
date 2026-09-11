---
type: Concept
title: TorchTitan 5D 并行与 DTensor Sharding 优化（DeepSeek-V3.2）
description: DeepSeek-V3.2 TorchTitan 预训练以 DTensor 组织 5D 并行，组合 FSDP2、TP、PP、EP 与自定义 CP；通过调整 MoE 的 TP 通信顺序及 DTensor 算子 sharding 策略，减少不必要的通信与张量重排。
tags:
- task.design
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# TorchTitan 5D 并行与 DTensor Sharding 优化（DeepSeek-V3.2）

## Summary

[DeepSeek-V3.2 TorchTitan 预训练](../../guides/recipes/deepseek_v32_pretrain.md)以 **DTensor** 组织 5D 并行，组合 **FSDP2、TP、PP、EP 与自定义 CP**。MoE 的 TP 通信顺序与 DTensor 算子 sharding 策略共同决定分片张量间的数据搬运；调整这两类策略可减少不必要的通信与张量重排。

## DTensor 一等公民 + 5D 乐高并行

> TorchTitan 最根本的优势在于深度应用 DTensor，将张量并行抽象为一等公民语义，实现并行策略的乐高式组合。
> - **统一抽象**：DTensor 通过 Placement（Shard/Replicate/Partial）将参数切分与模型定义解耦，开发者仅需配置子模块的 ParallelStyle 声明切分方式，无需显式编写通信逻辑。
> - **多维组合**：基于携带完整设备网格的 DTensor，TorchTitan 可以极低侵入成本实现 5D 并行（FSDP2+TP+PP+EP+CP）组合。

切分由 Placement 三态描述：`Shard(dim)`（沿某维切到各 rank）、`Replicate()`（各 rank 全量副本）、`Partial()`（各 rank 持部分和、待 AllReduce/ReduceScatter 归约）。一旦选定的 sharding 与张量当前 Placement 不符，DTensor 会自动插入 Slice / 通信完成状态转换——这正是后两节优化的发力点。

本 recipe 的实际并行度由 `deepseek_v32_671b_61layers_32k_128die.toml` 的 `[parallelism]` 段给出：

```toml
[parallelism]
data_parallel_replicate_degree = 1
data_parallel_shard_degree = -1          # FSDP 分片度自动填满剩余卡数
tensor_parallel_degree = 4               # TP4
pipeline_parallel_degree = 1             # PP1
pipeline_parallel_schedule = "Interleaved1F1B"
expert_parallel_degree = 64              # EP64
expert_tensor_parallel_degree = 1        # 路由专家不再做 TP（TP extend EP）
context_parallel_degree = 8              # CP8
enable_custom_context_parallel = true    # DSA 专用自定义 CP
# torchtitan_npu/models/deepseek_v32/train_configs/deepseek_v32_671b_61layers_32k_128die.toml
```

即该 128 die 配置取 **TP4 × EP64 × CP8 × PP1**，FSDP 分片度自动填满；而源文档「最小化切分策略」节在权衡 MoE 极端负载不均后，整体推荐以 **PP2TP4EP64** 为基础的切分（见第 4 节）——两者是不同切分点，并列保留。

`parallelize_deepseekv32` 的**装配顺序**固定（`infra/parallelize.py`），各维度按从内到外叠加：

1. **TP**（`apply_non_moe_tp`）— 非 MoE 部分（embedding/norm/output、Attention、dense FFN）的张量+序列并行；详见 [tensor-parallel](../../../inference/concepts/parallelism/tensor_parallel.md)
2. **CP**（`apply_cp_to_attention_module`）— 仅当 `cp_enabled`；`npu_dsa` 激活时把 `attn_type` 由 `sdpa` 覆写为 `dsa` 走自定义 CP，详见 [custom-cp-dsa](custom_cp_dsa.md) 与 [context-parallel](../../../inference/concepts/parallelism/context_parallel.md)（CP 基础原理）
3. **MoE-EP-TP**（`apply_moe_ep_tp`）— 专家分支的 EP + 共享专家 TP（第 2 节）；EP 详见 [expert-parallel](../../../inference/concepts/parallelism/expert_parallel.md)
4. **AC**（`apply_ac`）— 激活重计算（toml `mode = "full"`）
5. **compile**（`apply_compile`）— 逐 TransformerBlock `torch.compile`（inner_attention 已是融合算子故跳过）
6. **FSDP2**（`apply_fsdp`，**最外层**）— 对剩余复制维做全分片；详见 [fsdp](fsdp.md)

**PP** 在 DeepSeek-V3.2 配置中取 `Interleaved1F1B` 调度（toml 当前 PP1）。上游优化文档计划接入 **DualPipeV**（脱胎自 DeepSeek DualPipe、借鉴 Interleaved1F1B 的高效 MoE PP 调度，一卡同时承载一前向 batch + 一反向 batch 以互相掩盖 EP 通信），但 torch 原生 dW 约束权重 W 不能在 DP 域保持切分，故当前**无法与 ZeRO3/FSDP 同时使能**，待适配。

## MoE 的 TP 策略优化原理

大 EP 场景下，**路由专家不做 TP 切分（TP extend EP）**，只有共享专家走 TP。TorchTitan 原生的 MoE TP 策略两个分支都有不合理处：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/EP_optimize_before.png" width="55%"></p>
<p align="center"><sub>图：MoE 原生 TP 策略——路由专家分支冗余 topk/通信、共享专家维持不安全的 Partial（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·MoE的TP策略优化）</sub></p>

> - 路由专家分支接收在 TP 域 AllGather 之后的激活 tensor，一个 TP 域内每个 rank 对相同的 tensor 做了 topk 选择，产生了计算和内存的冗余；同时 Reorder 重排布模块又做了 Sequence Parallel，相当于前面 TP 域 AllGather 对路由专家分支来说是冗余操作。
> - 共享专家分支与传统的 TP 不同，其输出没有立刻做 ReduceScatter 通信，而是维持 Partial 这种不安全的状态，并且占据内存较多。

根因是 **TP 域的 AllGather / ReduceScatter 位置安排不合理**。优化把这两个通信**移动到共享专家分支**，路由专家分支不再需要 TP 域通信：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/EP_optimize_after.png" width="55%"></p>
<p align="center"><sub>图：优化后——AllGather/ReduceScatter 收敛到共享专家分支，路由专家支路无冗余计算/通信，共享专家退化为普通 TP（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·MoE的TP策略优化）</sub></p>

代码层（`apply_moe_ep_tp`）即把共享专家声明为标准 TP——输入 `Shard(0)→Replicate` 做 AllGather、`w2` 输出 `Shard(0)` 做 ReduceScatter，而 `moe.experts` 单独用 `ExpertParallel()` 沿 EP mesh 切分（`etp` 不开，故 TP extend EP）：

```python
"moe.shared_experts": PrepareModuleInput(
    input_layouts=(Shard(0),), desired_input_layouts=(Replicate(),)),   # AllGather
"moe.shared_experts.w1": ColwiseParallel(),
"moe.shared_experts.w2": RowwiseParallel(output_layouts=Shard(0)),      # ReduceScatter
"moe.shared_experts.w3": ColwiseParallel(),
# experts 分支：experts_plan = ExpertParallel(); 沿 ep_mesh 切，无 TP 冗余
# torchtitan_npu/models/deepseek_v32/infra/parallelize.py · apply_moe_ep_tp
```

## DTensor Sharding 策略优化

> 当使用 DTensor 进行计算，算子下发时需要对算子的输入（包含权重）、输出生成 sharding 策略。对于一个 DTensor，若选定的 sharding 策略与当前状态不符，就会触发 DTensor 的状态转变，会引入 Slice 或通信等额外的操作，会对性能甚至内存产生非常不利的影响。

### Matmul Sharding（正向，以 q_lora 为例）

q_lora 矩阵乘在 TP 域内**不做任何切分**，直接算 matmul 即可。但默认 sharding 生成却把简单的 Replicate 矩阵乘转成「权重做 TP 行切」的形式，凭空引入额外操作：

> - **输入 X**：从 Replicate 变为 Shard(2)，需要 Slice 操作。
> - **权重 W**：从 Replicate 变为 Shard(0)，需要 Slice 操作。
> - **输出 Y**：由于 TP 策略中指定 q_lora 模块不做并行，因此最终该 matmul 输出需要调整为 Replicate 状态，从 Partial 到 Replicate 则需要 AllReduce 通信。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/ecf4872c-c7e9-4932-9705-1c785afd053c.png" width="55%"></p>
<p align="center"><sub>图：q_lora Matmul——左侧默认 sharding 引入 Slice/AllReduce，右侧合理的 Replicate 策略直接计算（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·Matmul Sharding策略优化）</sub></p>

修法：**复用 pytorch 已写好的 matmul sharding 策略生成函数**得到合理的 Replicate 策略，输入/权重/输出全程不变状态，无 Slice、无 AllReduce。代码层对应 `attention.pre_attention.wq_a` 等被声明为 `NoParallel(use_local_output=False)`，让 q_lora 子模块保持非并行而不被默认推断改写。

### Matmul Backward Sharding（反向，以末尾 output 矩阵乘为例）

output 正向是权重 TP 列切；反向时默认策略同样引入冗余：

> - **输入 X**：从 Replicate 变为 Shard(2)，需要 Slice 操作。
> - **梯度 dY**：从 Shard(2) 变为 Replicate，需要 AllGather 通信，且占据更多内存。
> - **权重 W**：从 Shard(1) 变为 Shard(0)，需要 AllToAll 通信。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/89247407-6507-4ae4-aa9b-dfee0fe484ab.png" width="55%"></p>
<p align="center"><sub>图：Matmul Backward——左侧默认引入 Slice/AllGather/AllToAll，右侧 _mm_like_strategy 融合后输入不再调整切分状态、无多余操作（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·Matmul Backward Sharding策略优化）</sub></p>

torch 没有 matmul 反向的策略生成函数，但 matmul 反向本质是 dX、dW 两个矩阵乘。修法：

> 我们设计对两个矩阵乘分别调用 `_mm_like_strategy` 生成策略然后融合得到最终的 matmul 反向 sharding 策略。……由于通常计算中不会再调整权重的切分状态，我们从众多策略中分别选择不调整 W 切分状态的策略（dX 计算）和 dW 与 W 切分状态一致的策略（dW 计算），将两条策略融合后即可得到上图右侧的理想策略。可以看到，理想的策略实际上就是对算子的输入 tensor 不再做切分状态的调整，这样也就没有了额外操作的引入。

## 切分策略对比与选择

核心约束：64 卡 A3 上部署 671B。TorchTitan 当前用 FP32 存权重，权重+梯度即占 **5368GB**，超过 32 卡 A3 总内存 4096GB，故 **64 卡是部署的最小规模**，策略主线是「极限压缩单卡内存」。文档对比了多种切分策略：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/fe933026-03be-4731-b45a-2fb7acb6a2ae.png" width="55%"></p>
<p align="center"><sub>图：多种切分策略对比，在考虑 MoE 极端负载不均后选择以 PP2TP4EP64 为基础的切分（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·最小化切分策略）</sub></p>

以 PP2TP4DP16 为例，单卡非 MoE 权重+梯度约 `(671B − 654B)/PP2/TP4 × 8Byte ≈ 18GB`（`qkv_a`/`indexer` 等不参与 TP 切分，实际更高）；DP16 开启 FSDP 后这部分在 DP 域间完全均分、几乎清零。最终**在考虑 MoE 极端负载不均衡的可能后选择了 PP2TP4EP64 为基础的切分**——零冗余权重的二次分片机制详见 [fsdp](fsdp.md)。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v32_pre_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（「为什么选择 TorchTitan」DTensor 一等公民 / 5D 乐高 / 「分布式并行策略」MoE TP 优化 + DTensor 计算 Sharding 策略优化（Matmul / Matmul Backward）/ 「内存优化」最小化切分策略）
- [`torchtitan_npu/models/deepseek_v32/infra/parallelize.py`](https://gitcode.com/cann/torchtitan-npu/blob/87221a1beaa55314a1cdb73460346ba3cec0b475/torchtitan_npu/models/deepseek_v32/infra/parallelize.py) — `parallelize_deepseekv32` 装配顺序（TP→CP→MoE-EP-TP→AC→compile→FSDP）、`apply_moe_ep_tp` 共享专家 TP + experts `ExpertParallel`、`apply_non_moe_tp` 中 q_lora `NoParallel`、CP `attn_type` sdpa→dsa 覆写
- [`torchtitan_npu/models/deepseek_v32/train_configs/deepseek_v32_671b_61layers_32k_128die.toml`](https://gitcode.com/cann/torchtitan-npu/blob/87221a1beaa55314a1cdb73460346ba3cec0b475/torchtitan_npu/models/deepseek_v32/train_configs/deepseek_v32_671b_61layers_32k_128die.toml) — `[parallelism]` 真实并行度（TP4 / EP64 / CP8 / PP1，`pipeline_parallel_schedule="Interleaved1F1B"`，`expert_tensor_parallel_degree=1`，`enable_custom_context_parallel=true`）

## Links

- [torchtitan](../frameworks/torchtitan.md)（5D 并行的承载框架，DTensor / ModelConverter / torch.compile）
- [fsdp](fsdp.md)（5D 装配最外层 FSDP2：零冗余权重二次分片、A3 超节点预取掩盖）
- [custom-cp-dsa](custom_cp_dsa.md)（5D 中的 CP 维：DSA 专用自定义 CP，对 KV 序列维 AllGather）
- [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)（本并行原理的承载实践，148 TPS/卡）
- [tensor-parallel](../../../inference/concepts/parallelism/tensor_parallel.md)（跨域：TP 基础原理，本页非 MoE TP / 共享专家 TP 与之对照）
- [expert-parallel](../../../inference/concepts/parallelism/expert_parallel.md)（跨域：MoE 专家并行，本页路由专家 TP extend EP 走纯 EP）
- [context-parallel](../../../inference/concepts/parallelism/context_parallel.md)（跨域：CP 基础原理，本页 CP8 维度的通用机制）
- [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（跨域：64 卡最小规模与 A3 高带宽支撑通算掩盖的硬件平台）
- [autofuse-train](../techniques/autofuse_train.md)（V4 入图：compile 在并行装配 AC 之后/FSDP 之前）
- [hif8](../quantization/hif8.md)（训练低精度量化 HiF8/MXFP8(see also)）
- [model-custom-converter](../frameworks/model_custom_converter.md)（声明式 converter 的 ParallelizePlanUpdater 改写并行 plan（ExpertParallel→GMMExpertParallel））
- [tensor-parallel-2d](tensor_parallel_2d.md)（同域：另一条 TP/CP 并行主线，MindSpeed 把单 `tp` 域分解为 `tp_x×tp_y` 子域，其 tp-y∪cp 联合域与本页 CP 长序列切分对照）
- [dualpipev](dualpipev.md)（Megatron 栈侧的 V 形流水，对照 torchtitan Interleaved1F1B PP）
- [pipeline-parallel-advanced](pipeline_parallel_advanced.md)（Megatron 栈侧的高级 PP 能力集：VPP / Ripipe / 多参数 / 变长序列）