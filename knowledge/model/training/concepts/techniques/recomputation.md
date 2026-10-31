---
type: Concept
title: 重计算（Recomputation：选择性/全量 + 激活函数/Norm 细粒度 + 按 PP rank 层数）
description: MindSpeed 重计算（activation checkpointing）技术页，覆盖算力换显存的分层启用策略。Megatron 底座给两个正交粒度：granularity（full 整层 / selective 仅注意力核）与 method（uniform 均匀分块 / block 前若干层），由 --recompute-num-layers 控层数；MindSpeed 重写 transformer_block_checkpointed_forward 承载 block 方式。三个细粒度增补：激活函数重计算（--recompute-activation-function，用 CheckpointWithoutOutput 把 gelu/swiglu 的 (b,s,4h) 输出 discard_output 释放物理存储、留逻辑视图，反向用 register_hook 在 4h→h 反向前 recompute 重算，附 llama2-7B 内存收益表）；Norm 重计算（--recompute-norm，复用同一 checkpoint 机制重算 RMSNorm/LayerNorm 输出，仅 mcore 分支，TP+SP 下激活已切分收益弱）；按 PP rank 计层（--enable-recompute-layers-per-pp-rank 把 --recompute-num-layers 语义从每 VPP rank 改为每 PP rank）。统一层选择 should_recompute 按 recompute_priority 优先级排序：前 recompute_num_layers 层做全量、其后做激活函数/Norm 细粒度，名额不交叠。关键术语：CheckpointWithoutOutput、discard_output、register_hook、RNG 回拨、should_recompute、recompute_priority、reduce_recompute_for_last_chunk、ripipe（recompute-in-bubble/advance）。
tags:
- task.optimization
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/README.md
  role: primary
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/recomputation.md
  role: supporting
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-10-29T15:24:42Z'
platforms:
- agnostic
---

# 重计算（Recomputation：选择性/全量 + 激活函数/Norm 细粒度 + 按 PP rank 层数）

## Summary

重计算（activation checkpointing / rematerialization）用算力换显存：前向只保留少量关键张量，把中间激活在反向需要时按保存的输入重新算一遍，从而压低激活显存峰值。Megatron 提供两个正交粒度——granularity（`full` 整层 / legacy 分支若开 `--use-flash-attn` 则不支持 selective；`selective` 只重算注意力核）与 method（`uniform` 均匀分块 / `block` 前若干层），由 `--recompute-num-layers` 控层数。MindSpeed 在此之上补三件事：**激活函数重计算**（`--recompute-activation-function`，丢弃 gelu/swiglu 那块 `(b,s,4h)` 输出，反向用 `register_hook` 在 `4h→h` 反向前重算）、**Norm 重计算**（`--recompute-norm`，复用同一套 `CheckpointWithoutOutput` 机制重算 RMSNorm/LayerNorm 输出，仅 mcore 分支）、以及**按 PP rank 计层**（`--enable-recompute-layers-per-pp-rank` 把 `--recompute-num-layers` 的语义从「每 VPP chunk」改成「每 PP rank」）。统一的层选择由 `should_recompute` 按优先级排序：前 `recompute_num_layers` 层做全量、其后若干层做激活函数/Norm 细粒度，二者不重叠。流水内的重计算调度（气泡内/提前重算）由 ripipe 承载，见 [pipeline-parallel-advanced](../parallelism/pipeline_parallel_advanced.md)。

## 为什么要重计算：激活显存与算力的取舍

Transformer 训练的显存大头之一是前向激活——它要一直存到反向用完。序列越长、micro-batch 越大，激活越占地方，且在 1F1B 流水里靠前 stage 还要缓存多份在途激活，stage-0 峰值最高。重计算的思路是：前向丢弃可重算的激活、只留它的输入（checkpoint 的 saved_tensors），反向需要时再算一遍。代价是这部分前向多算一次——整层全量重计算会增加一遍相应前向的计算成本，实际比例取决于模型与配置，而只重算「计算量小但产物大」的部分则几乎不掉性能。因此重计算不是开/关的二元选择，而是按「单位显存收益 / 单位算力代价」从高到低分层启用。

## 全量 vs 选择性：粒度与分块方式

Megatron 的重计算由三个参数描述，是 MindSpeed 细粒度特性的承载底座：

- **`--recompute-granularity`**：`full` 把整个 transformer 层作为重计算单元（checkpoint 该层输入、反向重算整层），显存收益最大、算力代价也最大；`selective` 只重算注意力核（softmax/dropout 这类显存重、算力轻的算子），收益小但近乎零性能损失。
- **`--recompute-method`**：`uniform` 把每个 PP rank 的层均匀分块、对每块的输入 checkpoint；`block` 只对每 rank（或每 chunk）的**前 `--recompute-num-layers` 层**做重计算、其余层正常跑——后段不重算的层换取性能。
- **`--recompute-num-layers N`**：`block` 方式下每单位重计算的层数。

MindSpeed 对 `block` 方式重写了 `TransformerBlock._checkpointed_forward`（`RecomputeMethodFeature` 在 `recompute_method == 'block'` 且未开 `swap_attention` 时 patch `transformer_block_checkpointed_forward`）。其内对每层判定是否落在重计算名额内：

```python
# block 分支：第 layer_idx 层是否重计算
return (layer_idx * vpp_size + vpp_rank) < self.config.recompute_num_layers
# mindspeed/core/memory/common.py · transformer_block_checkpointed_forward
```

`reduce_recompute_for_last_chunk=True`（ripipe-advance 置位）时额外排除「最后一层且为 PP 末 stage」的重计算——模型最后一层的重计算对反向关键路径无收益，去掉可提速。

## 激活函数重计算：丢输出而非丢输入

传统重计算的局限：一次计算过程只能省下它的**输入**，输出激活仍须保留。以 MLP 为例，`gelu`/`swiglu` 在 `linear_fc1` 后产出一块 shape 为 `(batch, seq, 4·hidden)` 的中间激活，体积大但算力极小；可后续 `linear_fc2`（`4h→h`）的反向需要这块激活，且它在时序上**早于** gelu 自身的重算流程，于是前向不得不把它留着——激活函数的输出省不下来。

激活函数重计算另起一套框架，把重算时机灵活插到反向计算之前的任意位置。`MLP.forward` 被换成 `core_activation_recompute_forward_impl`：用 `CheckpointWithoutOutput.checkpoint` 包住 `activation_function`，`linear_fc2` 取用其输出后立刻 `discard_output()` 释放那块 `(b,s,4h)` 物理存储、只留逻辑视图；再给 `linear_fc2` 输出挂 `register_hook`，反向回传到 `4h→h` 之前触发 `recompute` 把激活重新算回：

```python
self.activation_checkpoint_manager = CheckpointWithoutOutput(get_cuda_rng_tracker)
intermediate_parallel = self.activation_checkpoint_manager.checkpoint(
    activation_function, False, intermediate_parallel, bias_parallel, per_token_scale)
output, output_bias = self.linear_fc2(intermediate_parallel)
self.activation_checkpoint_manager.discard_output()       # 丢弃激活函数输出的物理存储
if output.requires_grad:
    output.register_hook(self.activation_checkpoint_manager.recompute)  # 反向前重算
# mindspeed/core/memory/recompute/activation/activation_recompute_forward.py
```

`CheckpointWithoutOutput` 是这套机制的核心：`forward` 在 `torch.no_grad()` 下跑函数并 `save_for_backward` 输入；`discard_output` 对每个输出 `untyped_storage().resize_(0)` 释放显存而保留 tensor 元信息；`recompute` 先把 RNG 状态回拨到前向时刻（保证 dropout 等随机算子结果一致），`torch.enable_grad()` 重跑函数，再把结果 `resize_` 回原大小并 `copy_` 进原存储，使后续反向无感知地拿到激活。

开关：`--recompute-activation-function` 开启，`--recompute-activation-function-num-layers N` 指定层数（不超过 `--num-layers`）。可与全量重计算同开，但此时**仅支持 `--recompute-method block`**，且同一层不会既全量又激活函数重计算；未开 PP 时两类层数之和应等于总层数。暂不兼容自适应重计算。

llama2-7B 实测内存收益随配置变化（激活函数算力小，性能仅略降）：

| 配置 | 设备 | 内存收益 |
|---|---|---|
| seq=12288, mbs=2, TP4 DP2 | 单机 8 卡 | 8.05 GB |
| seq=8096, mbs=2, TP4 DP2 | 单机 8 卡 | 5.31 GB |
| seq=16384, mbs=2, TP4 DP2 | 单机 8 卡 | 12.49 GB |
| seq=12288, mbs=1, TP4 DP2 | 单机 8 卡 | 4.04 GB |
| seq=12288, mbs=2, TP8 DP1 | 单机 8 卡 | 4.02 GB |

这套 `CheckpointWithoutOutput` 也对外可用，自定义模块按 `checkpoint → 用完 → discard_output → output.register_hook(recompute)` 四步即可对任意函数做「丢输出式」重计算（用 `register_hook` 需张量带梯度）。

## Norm 重计算：复用同一机制重算 LayerNorm/RMSNorm

Norm 重计算沿用激活函数重计算的 `CheckpointWithoutOutput`，把 RMSNorm/LayerNorm 的输出激活也省下来。`TransformerLayer.forward` 被换成 `norm_recompute_forward_impl`：对 `input_layernorm`（`norm_ckpt1`）与 `pre_mlp_layernorm`（`norm_ckpt2`）各建一个 checkpoint manager，norm 输出被下游 attention/MLP 取用后 `discard_output`，并给 attention/MLP 输出挂 `register_hook` 在反向前重算 norm：

```python
self.norm_ckpt1 = CheckpointWithoutOutput(get_cuda_rng_tracker)
input_layernorm_output = self.norm_ckpt1.checkpoint(self.input_layernorm, False, hidden_states)
# ... self.self_attention(...) 用完 ...
self.norm_ckpt1.discard_output()
attention_output_with_bias[0].register_hook(self.norm_ckpt1.recompute)
# mindspeed/core/memory/recompute/norm/norm_recompute_forward.py
```

开关：`--recompute-norm` + `--recompute-norm-num-layers N`。约束：**仅 mcore 分支**（需 `--use-mcore-models`），不支持 legacy；可与激活函数重计算、全量重计算同开，同开时同样仅支持 `--recompute-method block`、同一层不重复两类重计算。

收益取舍要点：Norm 计算很快，重算几乎不掉性能；但**开了 TP+SP 时这块 norm 激活已在 TP 域内被切分**，单卡省得有限、收益不明显——更适合未用 TP/SP 的模型。transformer_engine 实现下若 norm 已融进 `linear_qkv`/`linear_fc1`（`input_layernorm` 为 `IdentityOp`），走 `enable_recompute_norm_checkpoint` 把重算能力挂到对应列并行 linear 上。

## 自动层选择：full → activation → norm 的优先级

激活函数与 Norm 重计算复用同一套层选择函数 `should_recompute`，它按层在 chunk 内的位置算优先级，决定每层落到哪类重计算：

```python
recompute_priority = ((layer_number - 1) % layer_per_chunk) * vpp_size + vpp_rank
full_recompute_layers = config.recompute_num_layers
if full_recompute_layers:
    if recompute_priority < full_recompute_layers:
        return False                       # 该层做全量重计算（不走细粒度）
    elif num_recompute is None:
        return True
    elif recompute_priority < full_recompute_layers + num_recompute:
        return True                        # 该层做激活函数/Norm 细粒度重计算
    return False
# mindspeed/core/memory/recompute/recompute_common.py · should_recompute
```

由此前 `recompute_num_layers` 层优先做全量重计算（细粒度判定返回 `False`，让位给全量），紧随其后的 `num_recompute` 层做激活函数/Norm 细粒度——执行优先级即「先全量层、后细粒度层」，两类名额互不交叠。`should_recompute_activation` / `should_recompute_norm` 在转交 `should_recompute` 之前先看 ripipe：开了 `recompute_in_bubble`/`recompute_in_advance` 时，是否重算改由 `PipelineCheckpointManager.chunk_do_recompute` 决定（见下）。

## 按 PP rank 配置重计算层数

`layer_per_chunk` 与优先级里的 `vpp_size`/`vpp_rank` 取值受 `--enable-recompute-layers-per-pp-rank` 控制。默认（不开）下 `--recompute-num-layers` 的语义是**每个 VPP rank 重计算的层数**；开启后 `vpp_size`/`vpp_rank` 不再被压成 `1`/`0`，`--recompute-num-layers` 改为表示**每个 PP rank 重计算的层数**：

```python
if vpp_rank is None or not getattr(config, 'enable_recompute_layers_per_pp_rank', False):
    vpp_rank = 0
if vpp_size is None or not getattr(config, 'enable_recompute_layers_per_pp_rank', False):
    vpp_size = 1
# mindspeed/core/memory/recompute/recompute_common.py · should_recompute
```

`layer_per_chunk` 的取法：开 VPP 取 `num_layers_per_virtual_pipeline_stage`，否则开 PP 取 `num_layers // pp_size`，再否则取 `num_layers`。VPP 下重计算层会按优先级在各 model chunk 间均摊——例如 8 层 / PP2 / VPP2，`recompute_num_layers=2` 时 stage0 重算层 0,4、stage1 重算层 2,6；`=3` 时 stage0 重算 0,1,4。这让重计算名额能均衡落到 1F1B 的每个 chunk，而非堆在单个 chunk 上。

## 与 ripipe 流水内重计算调度的关系

上述特性决定「哪些层、哪类粒度」做重计算，**何时**做仍默认绑定在反向计算上——重计算要等下一 stage 回梯度才触发，徒增气泡。ripipe（重计算流水独立调度）把重计算从反向里解耦、交由调度器主动触发：`--recompute-in-bubble` 在 VPP 气泡时间里主动插重计算，以极小性能代价换内存峰值下降（把需保留激活的前向块数压到 `PP×VPP`）；`--recompute-in-advance` 把已开启的重计算提前到反向前执行、并去掉模型最后一层的多余重计算以提速。开了这两者时，`should_recompute_activation`/`should_recompute_norm` 即转由 `PipelineCheckpointManager` 接管 chunk 级的开/关。机制本体与互斥关系见 [pipeline-parallel-advanced](../parallelism/pipeline_parallel_advanced.md) 的 Ripipe 小节。

显存换计算之外的另一条路是「显存换搬运」——把激活换出到 Host 而非重算，见 [swap-attention](swap_attention.md)；二者常按层混用，对算力敏感层走 swap、对带宽敏感层走重计算。

## 组合与约束速览

| 特性 | 开关 | 省什么 | 关键约束 |
|---|---|---|---|
| 全量重计算 | `--recompute-granularity full --recompute-method {uniform,block} --recompute-num-layers N` | 整层激活 | 增加相应前向计算成本，比例需实测 |
| 选择性重计算 | `--recompute-granularity selective` | 注意力核激活 | legacy + use-flash-attn 不支持；收益需按配置验证 |
| 激活函数重计算 | `--recompute-activation-function [--recompute-activation-function-num-layers N]` | gelu/swiglu 的 `(b,s,4h)` 输出 | 与全量同开仅支持 `block`；不兼容自适应重计算 |
| Norm 重计算 | `--recompute-norm [--recompute-norm-num-layers N]` | LayerNorm/RMSNorm 输出 | 仅 mcore；TP+SP 下收益弱；与全量同开仅支持 `block` |
| 按 PP rank 计层 | `--enable-recompute-layers-per-pp-rank` | —（改 `--recompute-num-layers` 语义） | 每 PP rank 计层 vs 每 VPP rank 计层 |
| 流水内调度 | `--recompute-in-bubble` / `--recompute-in-advance` | 气泡换内存 / 提前重算压气泡 | 见 ripipe，需 VPP；两者互斥 |

## Evidence

- [README.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/README.md)（primary）
- [recomputation.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/recomputation.md)（supporting）

## Links

- [pipeline-parallel-advanced](../parallelism/pipeline_parallel_advanced.md)（ripipe 把重计算从反向解耦、气泡内/提前重算；本页定「哪些层哪类粒度」，ripipe 定「何时触发」）
- [swap-attention](swap_attention.md)（互补显存路线：激活换出 Host 而非重算，常与重计算按层混用）
- [mindspeed](../frameworks/mindspeed.md)（重计算各特性以 `MindSpeedFeature` + `MindSpeedPatchesManager` patch megatron 接入的承载框架）
- [auto-settings](auto_settings.md)（自动搜索把重计算粒度/层数纳入联合优化）
