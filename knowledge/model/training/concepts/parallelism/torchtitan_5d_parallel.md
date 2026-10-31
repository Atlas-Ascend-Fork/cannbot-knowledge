---
type: Concept
title: TorchTitan 5D 并行与 DTensor Sharding 优化（DeepSeek-V3.2）
description: 当前 V3.2 ShardingConfig 的 MLA/Indexer 参数与输入布局、TP/CP 转换边界；以最新 Recipes 的 MoE 与 Matmul 案例说明冗余通信，并撤下已移除的 TOML 与旧策略注册接口。
tags:
- task.design
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/sharding.py
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/parallelize.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/config_registry.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- a3
---

# TorchTitan 多维并行与 DSA Sharding（DeepSeek-V3.2）

## Summary

以 DTensor/SPMD 布局组合 FSDP、TP、PP、EP、CP，减少分片转换引入的冗余通信。各维的支持与顺序由具体模型、backend 和配置决定；不存在把五个开关同时打开即可正确运行任意模型的保证。

## 当前模型与配置入口

V3.2 位于 `models/deepseek_v3_2`，parallelizer 直接复用社区 DeepSeek V3；本仓用 `set_deepseek_v3_2_sharding_config` 在公共 decoder/MTP 规则上叠加 DSA。当前不再使用旧 infra/parallelize.py、32K TOML、enable_custom_context_parallel 或 npu_dsa converter。

Python ParallelismConfig 的 replicate/shard、TP、PP、EP、CP 度需要满足模型与集群约束。当前本地 registry 只提供小型 debugmodel，不等于来源671B生产配置；MTP/CP组合另见 [MTP](../modules/deepseek_v32_mtp_train.md)，模型融合算子用显式 override。

## DSA 的声明式布局

当前 ShardingConfig 明确声明 state/input source/input destination/output：

- MLA w_uk、w_uv 以及 Indexer wq_b 的 weight 沿 TP 行维 Shard(0)。
- Indexer wk、weights_proj、k_norm 的 weight/bias 与 RoPE cache 在 TP 复制。
- inner attention 的主 Q/RoPE 与 Indexer Q 在 head 维切分；MQA 的单 KV head 在 TP 复制，目标 key 在 CP 聚合。
- Indexer 的部分 TP 输入使用 spmd.I，Attention.forward 补 R→I，避免 spmd_types 同时重分布 TP/CP 的限制；不要把 I 与 Replicate/Partial 简单互换。
- MTP 独立 layers 同样应用这些 attention 规则。Indexer aux loss 的 instance_acc 与输入使用自己的布局，归一化见 [SLIG](../kernels/slig.md)。

FSDP 在 dense/expert 剩余复制域做二次分片，EP process group 与 dense/FSDP 分离；当前 decoder helper、reshard与预取见 [FSDP2](fsdp.md)。

## MoE TP 的来源优化案例


大 EP 场景下，**路由专家不做 TP 切分（TP extend EP）**，只有共享专家走 TP。TorchTitan 原生的 MoE TP 策略两个分支都有不合理处：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/EP_optimize_before.png" width="55%"></p>
<p align="center"><sub>图：MoE 原生 TP 策略——路由专家分支冗余 topk/通信、共享专家维持不安全的 Partial（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·MoE的TP策略优化）</sub></p>

> - 路由专家分支接收在 TP 域 AllGather 之后的激活 tensor，一个 TP 域内每个 rank 对相同的 tensor 做了 topk 选择，产生了计算和内存的冗余；同时 Reorder 重排布模块又做了 Sequence Parallel，相当于前面 TP 域 AllGather 对路由专家分支来说是冗余操作。
> - 共享专家分支与传统的 TP 不同，其输出没有立刻做 ReduceScatter 通信，而是维持 Partial 这种不安全的状态，并且占据内存较多。

根因是 **TP 域的 AllGather / ReduceScatter 位置安排不合理**。优化把这两个通信**移动到共享专家分支**，路由专家分支不再需要 TP 域通信：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/EP_optimize_after.png" width="55%"></p>
<p align="center"><sub>图：优化后——AllGather/ReduceScatter 收敛到共享专家分支，路由专家支路无冗余计算/通信，共享专家退化为普通 TP（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·MoE的TP策略优化）</sub></p>


上述是最新 Recipes 文档保留的策略复盘。当前模型通过公共 sharding/dispatcher Config 表达布局，不再照抄旧 apply_moe_ep_tp 的模块树或 ParallelStyle 示例。

## DTensor 算子策略的来源复盘


> 当使用 DTensor 进行计算，算子下发时需要对算子的输入（包含权重）、输出生成 sharding 策略。对于一个 DTensor，若选定的 sharding 策略与当前状态不符，就会触发 DTensor 的状态转变，会引入 Slice 或通信等额外的操作，会对性能甚至内存产生非常不利的影响。

### Matmul Sharding（正向，以 q_lora 为例）

q_lora 矩阵乘在 TP 域内**不做任何切分**，直接算 matmul 即可。但默认 sharding 生成却把简单的 Replicate 矩阵乘转成「权重做 TP 行切」的形式，凭空引入额外操作：

> - **输入 X**：从 Replicate 变为 Shard(2)，需要 Slice 操作。
> - **权重 W**：从 Replicate 变为 Shard(0)，需要 Slice 操作。
> - **输出 Y**：由于 TP 策略中指定 q_lora 模块不做并行，因此最终该 matmul 输出需要调整为 Replicate 状态，从 Partial 到 Replicate 则需要 AllReduce 通信。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/ecf4872c-c7e9-4932-9705-1c785afd053c.png" width="55%"></p>
<p align="center"><sub>图：q_lora Matmul——左侧默认 sharding 引入 Slice/AllReduce，右侧合理的 Replicate 策略直接计算（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·Matmul Sharding策略优化）</sub></p>

修法：**复用 pytorch 已写好的 matmul sharding 策略生成函数**得到合理的 Replicate 策略，输入/权重/输出全程不变状态，无 Slice、无 AllReduce。这是来源优化案例中算子策略与模块意图不一致的问题。当前不再有旧 custom_shardings.py 接口；不能把此复盘当成该历史补丁仍自动安装，应结合当前配置和编译图核验。

### Matmul Backward Sharding（反向，以末尾 output 矩阵乘为例）

output 正向是权重 TP 列切；反向时默认策略同样引入冗余：

> - **输入 X**：从 Replicate 变为 Shard(2)，需要 Slice 操作。
> - **梯度 dY**：从 Shard(2) 变为 Replicate，需要 AllGather 通信，且占据更多内存。
> - **权重 W**：从 Shard(1) 变为 Shard(0)，需要 AllToAll 通信。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/89247407-6507-4ae4-aa9b-dfee0fe484ab.png" width="55%"></p>
<p align="center"><sub>图：Matmul Backward——左侧默认引入 Slice/AllGather/AllToAll，右侧 _mm_like_strategy 融合后输入不再调整切分状态、无多余操作（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·Matmul Backward Sharding策略优化）</sub></p>

torch 没有 matmul 反向的策略生成函数，但 matmul 反向本质是 dX、dW 两个矩阵乘。修法：

> 我们设计对两个矩阵乘分别调用 `_mm_like_strategy` 生成策略然后融合得到最终的 matmul 反向 sharding 策略。……由于通常计算中不会再调整权重的切分状态，我们从众多策略中分别选择不调整 W 切分状态的策略（dX 计算）和 dW 与 W 切分状态一致的策略（dW 计算），将两条策略融合后即可得到上图右侧的理想策略。可以看到，理想的策略实际上就是对算子的输入 tensor 不再做切分状态的调整，这样也就没有了额外操作的引入。


## 内存与切分案例

来源671B的FP32权重+梯度约5368GB，64卡A3是该设置的最小化部署案例；PP2TP4EP64是考虑专家负载不均后的选型。以非专家约17B估算，PP2TP4下权重/梯度约18GB/卡，再沿DP16分片摊薄。不能把该案例的卡数、旧TOML或148TPS/卡推广到当前所有精度/序列/模型配置。

核验实际前反向图中的 AllGather、ReduceScatter、AllToAll 和 Slice，固定权重/数据/精度/并行后分别评估内存与耗时；形状或布局正确不等于数值、收敛与通信重叠已经验证。本次未运行NPU训练。

## Evidence

- [sharding.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/sharding.py)（primary）
- [parallelize.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/parallelize.py)（implementation）
- [config_registry.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/config_registry.py)（implementation）
- [deepseek-v32_pre_train_optimization.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（supporting）

## Links

- [FSDP2](fsdp.md)
- [训练 CP](custom_cp_dsa.md)
- [V3.2 训练](../../guides/recipes/deepseek_v32_pretrain.md)
- [当前配置替换](../frameworks/model_custom_converter.md)
