---
type: Concept
title: SLIG（SparseLightningIndexerGradKLLoss，DSA 训练反向算子）
description: SparseLightningIndexerGradKLLoss（SLIG）是 DeepSeek-V3.2 训练独有的 DSA 反向融合算子：在 Sparse Training Stage 计算每个 token Top-k 位置的 lightning-indexer 反向梯度，并融合 KL Loss 的计算。反向梯度依赖 sparse-flash-attention 正向 softmax 的聚合归一化结果（softmax_max / softmax_sum）与 Lightning Indexer 自身的输出分布。推理侧只有 LI/SFA 正向算子，SLIG 是训练侧新增件，也是「业界率先攻克 DSA 反向」的核心。device 侧 kernel 对应 torch_npu.npu_sparse_lightning_indexer_grad_kl_loss，在 torchtitan 里通过 npu_dsa converter 注入。
tags:
- task.implementation
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a3
---

# SLIG（SparseLightningIndexerGradKLLoss，DSA 训练反向算子）

## Summary

`SparseLightningIndexerGradKLLoss`（SLIG）是 DeepSeek-V3.2 **训练独有**的 DSA 反向融合算子：在 Sparse Training Stage 计算每个 token Top-k 位置的 [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md) 反向梯度，并**融合 KL Loss 的计算**。反向梯度依赖 [sparse-flash-attention](../../../inference/concepts/kernels/sparse_flash_attention.md) 正向 softmax 的聚合归一化结果（`softmax_max` / `softmax_sum`）与 Lightning Indexer 自身的输出分布。推理侧只有 LI/SFA 正向算子，SLIG 是训练侧新增件，也是「业界率先攻克 DSA 反向」的核心。device 侧 kernel 对应 `torch_npu.npu_sparse_lightning_indexer_grad_kl_loss`，在 [torchtitan](../frameworks/torchtitan.md) 里通过 `npu_dsa` converter 注入。绑定它的 autograd `LILossTrain.forward` 只做 `ctx.save_for_backward` 并返回 dummy 零标量，真正的算子下发、三路梯度 + loss 计算、loss tracker 记录全部推迟到 `backward`——以避免 activation checkpointing 重算正向时重复下发算子。

## 计算逻辑

训练阶段需把 Lightning Indexer 的输出与 Sparse Flash Attention 的 softmax 结果对齐算 loss。记 $g$ 为 GQA group size、$d$ 为头维度、$S_k$ 为上下文长度：

1. **LI 正向 Top-k value**：$I_{t,:} = W_{t,:}\,@\,\mathrm{ReLU}(\tilde{q}_{t,:}\,@\,\tilde{K}_{topk,:}^\top)$（$\tilde{q}_{t,:}$ 为第 $t$ token 的 $g$ 个 query 头合轴结果，$\tilde{K}_{topk,:}$ 按 Top-k 索引取行）
2. **SFA 正向 Top-k value**：$p_{t,:} = \mathrm{Softmax}(q_{t,:}\,@\,K_{topk,:}^\top/\sqrt{d})$
3. **KL Loss**：$Loss = \sum_t D_{KL}(p_{t,:}\,\|\,\mathrm{Softmax}(I_{t,:}))$，$D_{KL}(a\|b)=\sum_i a_i\log(a_i/b_i)$；$p$ 为 target distribution（对所有 head 求和后沿上下文方向 L1 正则）
4. **梯度**：$dI_{t,:} = \mathrm{Softmax}(I_{t,:}) - p_{t,:}$
5. **链式法则**（$S=\tilde{q}@\tilde{K}^\top$，$dS$ 由 $dI$ 反传 ReLU）：
   $$dW_{t,:} = dI_{t,:}\,@\,(\mathrm{ReLU}(S_{t,:}))^\top,\quad d\tilde{q}_{t,:} = dS_{t,:}\,@\,\tilde{K}_{topk,:},\quad d\tilde{K}_{topk,:} = (dS_{t,:})^\top\,@\,\tilde{q}_{:t,:}$$
   $d\tilde{K}$ 为 Top-k 索引对应行的累加。

为平衡显存与算力，算子保留部分重要正向结果做**部分重计算**。

## op 调用与 autograd 绑定（torchtitan-npu）

device 侧反向 kernel 通过自定义 `torch.autograd.Function`（`LILossTrain`）接入，但**算子下发不在 forward**：`LILossTrain.forward` 只把正向张量 `ctx.save_for_backward`（query/key/query_indexer/key_indexer/weights/sparse_indices/softmax_max/softmax_sum/query_rope/key_rope）、把标量配置存进 `ctx`，然后**无条件返回 dummy 零标量** `torch.zeros(1, dtype=torch.float32, device=query.device)[0]`。真正的算子调用 `torch_npu.npu_sparse_lightning_indexer_grad_kl_loss`、三路梯度 + loss、`grad_output[0]` 缩放、loss tracker 记录，全部在 `backward`。如此设计是为了**真实计算推迟到 backward**——activation checkpointing 重算正向时不会重复下发算子。

```python
def forward(ctx, query, key, query_indexer, key_indexer, weights,
            sparse_indices, softmax_max, softmax_sum, layer_number=None,
            num_layers=0, scale_value=1, query_rope=None, key_rope=None,
            actual_seq_qlen=None, actual_seq_klen=None, layout="BSND",
            sparse_mode=3, pre_tokens=65536, next_tokens=65536):
    ctx.save_for_backward(query, key, query_indexer, key_indexer, weights,
                          sparse_indices, softmax_max, softmax_sum,
                          query_rope, key_rope)
    ctx.layer_number = layer_number; ctx.num_layers = num_layers
    ctx.scale_value = scale_value; ctx.layout = layout
    ctx.sparse_mode = sparse_mode; ctx.pre_tokens = pre_tokens
    ctx.next_tokens = next_tokens
    ctx.actual_seq_qlen = actual_seq_qlen; ctx.actual_seq_klen = actual_seq_klen
    return torch.zeros(1, dtype=torch.float32, device=query.device)[0]  # dummy
# torchtitan_npu/converters/kernels/dsa.py — LILossTrain.forward
```

关键签名要点（同源文件）：
- 必选输入 `query/key (B,S,N,D 或 T,N,D)`、`query_indexer/key_indexer`、`weights`、`sparse_indices`（已排序的 KV/key-index token 索引）、`softmax_max`、`softmax_sum`；可选 `query_rope/key_rope`（MLA 架构 RoPE）、`actual_seq_qlen/klen`（TND layout 下必填）。
- 默认 `layout="BSND"`、`sparse_mode=3`、`pre_tokens=next_tokens=65536`。
- **forward 无条件返回 dummy 零标量**：真实 KL/梯度计算延后到 `backward`，activation checkpointing 重算正向时不重复下发算子；dummy 零仅占位以保证计算图形状稳定。

外层 `SparseLightningIndexerKLLoss(nn.Module)` 封装这个 Function，对 loss 做 `loss / (bsz * sq)` 归一化；`@register_npu_converter("npu_dsa")` 的 `DSAKernel` 把 `dsa_forward` 替换进 `DSV32_SDPA.forward`，并逐 layer 把 `inner_attention.compute_dsa_indexer_loss` 设为该 Module（TP 开启时改由 `deepseek_v32_parallelize.py` patch）。正向链路里 SLIG 的输入由 SFA 提供：

```python
output, softmax_max, softmax_sum, *_ = torch_npu.npu_sparse_flash_attention(
    q_nope, k_nope, v, sparse_indices=topk_indices.to(torch.int32), ...,
    attention_mode=2,            # 2: MLA-absorb（dsa_forward 只支持矩阵吸收模式）
    return_softmax_lse=True)     # 训练必须 True，才有 softmax_max/sum 喂 SLIG
# torchtitan_npu/converters/kernels/dsa.py — dsa_forward
```

> `npu_dsa` converter 经 toml `converters = ["npu_dsa", ...]` 开关启用，「只支持矩阵吸收模式，LI Loss 默认开启」（`NpuDSAConverter.convert` 的 logger）。

### 梯度反传与正向链路顺序

`dsa_forward` 的算子下发顺序固定为 **LI → SFA → loss**：先 `torch_npu.npu_lightning_indexer(..., return_value=False)` 产 `topk_indices`（`return_value=False` 是为绕开 torch.compile/DTensor meta path 在 `return_value=True` 下的失败），再 `npu_sparse_flash_attention` 产 `output/softmax_max/softmax_sum`，最后 `compute_dsa_indexer_loss(...)` 触发 SLIG（即调用 `SparseLightningIndexerKLLoss.forward`→`LILossTrain.apply`）。`dsa_forward` 返回 `(loss, output)` 两路——output 进主网络前传，loss 为 dummy 零标量经 `loss / (bsz * sq)` 缩放后的零（占位，保证计算图形状），真实 indexer KL 数值在 `backward` 才算出。

融合路径下 loss 标量不驱动训练：indexer 三个可训练张量的梯度由 `LILossTrain.backward` 直接注入，真实 KL 数值经 `DSAIndexerLossLoggingHelper.save_loss_to_tracker` 进 indexer-loss tracker（仅作 metric）。算子下发、三路梯度、loss、缩放、tracker 记录都集中在 `backward`：

```python
def backward(ctx, *grad_output):
    (query, key, query_indexer, key_indexer, weights, sparse_indices,
     softmax_max, softmax_sum, query_rope, key_rope) = ctx.saved_tensors
    (d_query_index, d_key_index, d_weights, loss) = \
        torch_npu.npu_sparse_lightning_indexer_grad_kl_loss(
            query, key, query_indexer, key_indexer, weights, sparse_indices,
            softmax_max, softmax_sum, scale_value=ctx.scale_value,
            query_rope=query_rope, key_rope=key_rope,
            actual_seq_qlen=ctx.actual_seq_qlen, actual_seq_klen=ctx.actual_seq_klen,
            layout=ctx.layout, sparse_mode=ctx.sparse_mode,
            pre_tokens=ctx.pre_tokens, next_tokens=ctx.next_tokens)
    if grad_output[0] != 1.0:        # loss 缩放系数透传到三路梯度
        d_query_index = d_query_index * grad_output[0]
        d_key_index = d_key_index * grad_output[0]
        d_weights = d_weights * grad_output[0]
    bsz, sq = query.shape[0], query.shape[1]
    DSAIndexerLossLoggingHelper.save_loss_to_tracker(loss[0] / (bsz * sq),
                                                     ctx.layer_number, ctx.num_layers)
    return (None, None, d_query_index, d_key_index, d_weights, *([None] * 14))
# torchtitan_npu/converters/kernels/dsa.py — LILossTrain.backward
```

返回元组的位置严格对齐 `forward` 的 19 个入参：仅 `query_indexer`（位 3）、`key_indexer`（位 4）、`weights`（位 5）有梯度，`query/key` 与其余 16 个配置项均为 `None`（即 `*([None] * 14)`）——SLIG 只为 Lightning Indexer 的三个可训练张量供梯度，SFA 主路梯度由 [sfag](sfag.md) 单独承担。对比非融合路径 `model.py` 的 `DSAIndexerLossAutoScaler.apply(output, loss)` 才是 loss 标量驱动训练。

## Tiling 设计

- **核间**：对 B 和 S 轴分核切分。
- **核内**：基本块 $(128,128)$；L1 空间划分——$Q$ 矩阵 $128{\times}576{\times}2B=144\,\mathrm{KB}$ 常驻、$Q_{index}$ 启 Double Buffer 32 KB 常驻、$Gather$ 矩阵 DB 64 KB（每次搬 $(128,128)$）、$reluGrad$ 矩阵 288 KB（每次搬 $(64,2048)$）；L0A/L0B/L0C 启 DB（$2{\times}32/32/64$ KB）。$C_1$ 阶段含 $MatmulP$/$MatmulSy$，$C_2$ 阶段含 $MatmulDk$/$MatmulDq$，各自的 L0A/L0B 搬入块尺寸不同（如 $MatmulDk$ 为 $(128,64)/(64,128)$）。

## Pipeline 与离散访存优化

计算分五阶段：预处理 Gather（$V_0$）→ Matmul + ReLU（$C_1$）→ $V_1$ 多向量计算 → $C_2$ Matmul → 后处理 ScatterAdd（$V_2$）。相较 LI/SFA 正向，本算子流程更繁琐、数据依赖更复杂，朴素排布下 Cube/Vector 间气泡多，**提前 Preload 一次 $V_0$** 实现流水互相掩盖。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/b3eb5905-9d3c-4391-b6b8-21d6d098cd0d.jpg" width="62%"></p>
<p align="center"><sub>图：SLIG 五阶段流水，Preload V0 掩盖 Cube/Vector 气泡（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SLIG Pipeline 设计）</sub></p>

$V_0$ Gather 与 $V_2$ ScatterAdd 需离散访存。非 Sparse 场景的 Attention 算子访存连续，单次搬运耗时长于指令下发耗时，可连续多次访存达到较高带宽；而 Sparse Attention 的离散访存单次耗时大幅下降，甚至**小于指令下发耗时**，于是退化为严重的指令下发阻塞（如下图，搬运被一连串指令下发卡住），这正是后续成对聚合优化要解决的问题。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/b97ed3e2-ca09-46f6-9f5d-2887c8bad304.png" width="50%"></p>
<p align="center"><sub>图：Sparse 离散访存单次量小 < 指令下发耗时，导致指令下发阻塞（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·离散访存优化）</sub></p>

两项优化：

- 利用 A3 **Cube:Vector = 1:2** 的核数比，用 Vector 核发射访存指令，下发效率翻倍。
- 离散数据点**两两聚合**，用 `srcGap` 参数成对访存提升带宽。
- **合轴**：不同 QueryToken 对应不同 KeyToken，故 N 轴放内层循环，B、S 轴作切分轴。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/31a06a5c-c7aa-4767-8cc3-76afb6628db0.png" width="52%"></p>
<p align="center"><sub>图：离散数据点两两聚合、srcGap 成对访存提升带宽（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SLIG 离散访存优化）</sub></p>

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v32_pre_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（『DSA 融合算子 / SparseLightningIndexerGradKLLoss』节：KL Loss 与梯度公式、Tiling、五阶段 Pipeline、离散访存成对聚合、合轴）
- [`torchtitan_npu/converters/kernels/dsa.py`](https://gitcode.com/cann/torchtitan-npu/blob/87221a1beaa55314a1cdb73460346ba3cec0b475/torchtitan_npu/converters/kernels/dsa.py)（autograd 绑定 `LILossTrain` + op 调用 `torch_npu.npu_sparse_lightning_indexer_grad_kl_loss`、`SparseLightningIndexerKLLoss` Module、`npu_dsa` converter 注册、`dsa_forward` 正向产 `softmax_max/sum`）

## Links

- [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)（所属预训练实践；148 TPS/卡 A3 64 卡）
- [sfag](sfag.md)（同批 DSA 反向算子，SFA 反向 `SparseFlashAttentionScoreGrad`）
- [sasg](sasg.md)（V4 同构：SAS 统一算子的训练反向，与本算子在 V4 续训练中分工，SASG 算主路 Attention 梯度、SLIG 算 Indexer 反向+KL Loss）
- [custom-cp-dsa](../parallelism/custom_cp_dsa.md)（CP 场景下对 KV/key-index AllGather 后与本算子配合）
- [torchtitan](../frameworks/torchtitan.md)（`npu_dsa` converter 经 ModelConverter 机制注入，不改上游模型）
- [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)（跨域：LI 正向算子，SLIG 是其训练反向）
- [sparse-flash-attention](../../../inference/concepts/kernels/sparse_flash_attention.md)（跨域：SFA 正向算子，产 `softmax_max/sum` 喂 SLIG）
- [ascendc](../../../inference/concepts/frameworks/ascendc.md)（跨域：Ascend C 算子编程框架，本 kernel 的实现底座）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v32_pre_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（DSA 融合算子 / SLIG）
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（V4 续训同样使用 SLIG(DSA 反向)）
- [autofuse-train](../techniques/autofuse_train.md)（手写定制算子 vs AutoFuse 自动融合并列路线）
- [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md)（DSA/融合算子 converter 家族总览）
- [smla](smla.md)（V4 SMLA 与 DSA SLIG 同族稀疏注意力训练融合算子）
