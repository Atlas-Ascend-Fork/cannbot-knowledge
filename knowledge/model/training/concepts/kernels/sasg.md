---
type: Concept
title: SASG（SparseAttnSharedkvGrad，DeepSeek-V4 SAS 训练反向算子）
description: SparseAttnSharedkvGrad（SASG）是 sparse-attn-sharedkv（SAS，DeepSeek-V4 统一 Attention 融合算子）的训练反向融合算子。它在 cann-recipes-train 的 DeepSeek-V4-Flash TorchTitan-NPU 续训练实践中，与 slig（Lightning Indexer 反向 + KL Loss）一道补齐 V4 稀疏注意力的反向链路——推理侧 cann-recipes-infer 只有 SAS / lightning-indexer 正向算子，SASG 是训练侧新增件。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a3
---

# SASG（SparseAttnSharedkvGrad，DeepSeek-V4 SAS 训练反向算子）

## Summary

`SparseAttnSharedkvGrad`（**SASG**）是 [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)（SAS，DeepSeek-V4 统一 Attention 融合算子）的**训练反向**融合算子。它在 cann-recipes-train 的 DeepSeek-V4-Flash TorchTitan-NPU 续训练实践中，与 [slig](slig.md)（Lightning Indexer 反向 + KL Loss）一道补齐 V4 稀疏注意力的反向链路——推理侧 cann-recipes-infer 只有 SAS / [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md) 正向算子，SASG 是训练侧新增件。

它与 V3.2 DSA 的反向算子 [sfag](sfag.md)（SparseFlashAttentionGrad）同属一脉、角色对应，但针对的是 V4 的 **SAS 统一算子**：SAS 以单一接口按 `cmp_ratio` 覆盖**滑窗（SWA）/ 压缩（CFA）/ 稀疏压缩（SCFA）**三种 Multi-Query Shared-KV Attention，SASG 因此要为这套组合场景计算 `query / ori_kv / cmp_kv / sinks` 四路梯度。device 侧 op 为 `npu_sparse_attn_sharedkv_grad`，在 TorchTitan-NPU 里由 `deepseek_v4_sfa` converter（`DeepSeekV4SFAKernel`）通过自定义 `torch.autograd.Function` 注入到 `SparseAttention.forward`。

## SAS 正向回顾（反向的依据）

SASG 的输入大量来自 SAS 正向保存的中间量，先回顾 SAS 正向计算（详见跨域页 [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)）。SAS 完成的核心是 Multi-Query Shared-KV（$\tilde{K}=\tilde{V}$）带 Attention Sink 的 Attention：

$$S = Q @ \tilde{K}^\top,\qquad m = \max\bigl(\mathrm{sinks},\ \max(S)\bigr),\qquad \mathrm{Attention} = \frac{e^{S-m} @ \tilde{V}}{\sum e^{S-m} + e^{\mathrm{sinks}-m}}$$

其中 $\tilde{K}/\tilde{V}$ 是由 `ori_kv`（原始 KV，滑窗选取）、`cmp_kv`（Compressor 压缩后 KV）与 `cmp_ratio`（压缩比 1/4/128）共同控制的实际参与计算 KV。SAS 实现分 **V0/C1/V1/C2/V2** 五阶段（V 为 Vector、C 为 Cube）：

$$V_0:\ \mathrm{Gather}(\mathrm{cmpkv},\ \mathrm{topkIndices}[i]);\quad C_1:\ \mathrm{qk}=Q@K^\top;\quad V_1:\ P=\mathrm{onlineSoftmax}(\mathrm{qk},\mathrm{sinks});\quad C_2:\ O'=P@V;\quad V_2:\ O=\mathrm{rescale}(O')$$

正向流水通过 **Preload 一轮 V0+C1** 错开阶段依赖，实现除头尾外的 CV 流水并行：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/SAS-pipeline.png" width="58%"></p>
<p align="center"><sub>图：SAS 正向五阶段（V0/C1/V1/C2/V2）流水，Preload 一轮 V0+C1 实现 CV 并行（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·SparseAttnSharedkv）</sub></p>

反向要复用的正向产物即 `result`（attention 输出 $O$）与 `softmax_lse`（log-sum-exp，对应正向归一化分母），故正向调用必须开启 `returnSoftmaxLse=True`。

## SASG 反向计算流程

SASG 把 SAS 正向五阶段反传，主流程同样可分 **5 个阶段，依次为 Gather、Cube12、Process、Cube345、Scatter**：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/SASG-graph.png" width="62%"></p>
<p align="center"><sub>图：SASG 算子计算流程（Gather → Cube12 → Process → Cube345 → Scatter，逐路梯度 dQ/dKV/dSinks 反传）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·SparseAttnSharedkvGrad）</sub></p>

- **Gather**：按 `cmp_sparse_indices`（C4A 稀疏路径的 Top-k 索引）从压缩 KV 中离散提取本步需要的有效 K/V（对应正向 V0），是稀疏路径的离散访存入口。
- **Cube12 / Cube345**：两段 Cube 矩阵乘，承担 $dQ$、$d\tilde{K}/d\tilde{V}$ 反向链路中的若干 GEMM（反传 SAS 正向的 C1/C2）。源文档对 SASG 只给五阶段名、未列逐阶段公式；按标准 attention 反向推断，这两段大致覆盖 $Q@\tilde{K}^\top$、$P^\top@dO$、$dP@\tilde{V}$ 一类矩阵乘。
- **Process**：Vector 段，依据正向保存的 `softmax_lse` 重建在线 softmax 概率，并算 softmax 的雅可比反传（$dS$）、累计 sink 对分母的贡献得到 `sinks_grad`。
- **Scatter**：把离散位置上算出的 $d\tilde{K}/d\tilde{V}$ **ScatterAdd** 回 `ori_kv_grad` / `cmp_kv_grad` 的对应行（对应 Gather 的逆操作），因为 Shared-KV 下同一 KV 行可能被多个 query token 选中而需累加。

与 [slig](slig.md) / [sfag](sfag.md) 同源：稀疏 Top-k 选择带来 Gather / ScatterAdd 的**离散访存**，单次搬运量小，是该类反向算子共同的访存瓶颈来源。

## Pipeline 流水排布

> SASG 算子主流程可分为 5 个阶段，依次为 Gather、Cube12、Process、Cube345、Scatter，如图中所示。算子流水排布实现如下，通过 Preload 一次 Gather+Cube12 达成 CV 流水并行的效果。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/SASG-pipeline.png" width="60%"></p>
<p align="center"><sub>图：SASG 流水排布——Preload 一次 Gather+Cube12，使 Cube 与 Vector 阶段错开依赖、达成 CV 流水并行（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·SparseAttnSharedkvGrad）</sub></p>

排布思路与 SAS 正向（Preload V0+C1）、SLIG（V0 两次 Preload + PingPong）一致：**提前预取首段 Gather+Cube12**，让 Cube 段的算力与 Vector 段的访存/标量计算互相掩盖，消除朴素串行排布下 Cube/Vector 间的气泡。该批 V4 融合算子（LI / SAS / SASG / SLIG）的共同设计原则是从「负载均衡分核计算、内存与计算均衡」维度协同优化，充分释放芯片稀疏算力（源文档 Highlights）。

## op 调用与 autograd 绑定（torchtitan-npu）

SASG 不是独立暴露给用户的 op，而是 SAS 自定义 `torch.autograd.Function` 的 `backward`。正向 `SparseAttnSharedKV.forward` 先调 AICPU Scheduler 算子 `npu_sparse_attn_sharedkv_metadata` 产分核 metadata，再调 `npu_sparse_attn_sharedkv(..., True)` 产 `result/softmax_lse` 并 `save_for_backward`；反向直接调 `npu_sparse_attn_sharedkv_grad` 一次返回四路梯度：

```python
@staticmethod
def backward(ctx, grad_output):
    (query, ori_kv, cmp_kv, result, softmax_lse,
     ori_sparse_indices, cmp_sparse_indices, sinks) = ctx.saved_tensors
    query_grad, ori_kv_grad, cmp_kv_grad, sinks_grad = (
        _sas_op.npu_sparse_attn_sharedkv_grad(
            query, ori_kv, cmp_kv, grad_output, result, softmax_lse,
            ori_sparse_indices, cmp_sparse_indices,
            None, None, None,          # cuSeqlensQ / cuSeqlensOriKv / cuSeqlensCmpKv（非 TND）
            sinks,
            ctx.softmax_scale, ctx.cmp_ratio,
            ctx.ori_mask_mode, ctx.cmp_mask_mode,
            ctx.ori_win_left, ctx.ori_win_right, ctx.layout_q))
    return (query_grad, ori_kv_grad, cmp_kv_grad,
            None, None, None, None, None, sinks_grad, *([None] * 15))
# torchtitan_npu/converters/kernels/deepseek_v4_sfa.py — SparseAttnSharedKV.backward
```

关键点（同源文件 `deepseek_v4_sfa.py`）：
- **反向入参** `grad_output`（上游 $dO$）、`result`（正向 $O$）、`softmax_lse`（正向归一化分母）三者均来自正向 `ctx.save_for_backward(query, ori_kv, cmp_kv, result, softmax_lse, ori_sparse_indices, cmp_sparse_indices, sinks)`——SAS 把反向所需的全部正向中间量随 ctx 透传，反向无需重算正向 attention。
- **四路梯度** `query_grad / ori_kv_grad / cmp_kv_grad / sinks_grad` 严格对齐 `forward` 的 24 个入参位置：`query`（位 1）、`ori_kv`（位 2）、`cmp_kv`（位 3）、`sinks`（位 9）有梯度，其余 20 个（含 `cmp_ratio` / `ori_win_left` / `layout_q` 等配置项与索引）全为 `None`。
- 反向 `cuSeqlens*` 传 `None`，与正向 wrapper 注明的「not support TND」对齐；`ctx.softmax_scale / cmp_ratio / ori_mask_mode / cmp_mask_mode / ori_win_left / ori_win_right / layout_q` 这些标量配置随 ctx 透传给反向 op。

正向 wrapper `npu_sparse_attn_shared_kv` 把 PyTorch 张量整形为 SAS 期望的 `BSND` layout，并据 `cmp_ratio` 决定是否启用稀疏 Top-k：仅 `cmp_ratio==4`（C4A）走稀疏，此时 `topk = cmp_sparse_indices.size(-1)` 且 `cmp_sparse_indices` 被 `unsqueeze(2)` 整形；否则 `topk=0` 且 `cmp_sparse_indices` 同步被置 `None`——稀疏/非稀疏由这对双重门控对称切换，最终 `.apply(...)` 进 autograd 图：

```python
def npu_sparse_attn_shared_kv(query, ori_kv, cmp_kv, cmp_sparse_indices, sinks,
                              softmax_scale, cmp_ratio,
                              ori_mask_mode=4, cmp_mask_mode=3,
                              ori_win_left=127, ori_win_right=0):
    cu_seq_lens_q = cu_seq_lens_ori_kv = cu_seq_lens_cmp_kv = None  # not support TND
    ori_sparse_indices = None                       # ori kv use band mode
    batch_size, max_seq_len_q, num_heads_q, head_dim = query.size()
    num_heads_kv = 1                                 # Multi-Query：共享单头 KV
    max_seq_len_kv = ori_kv.size(1)                  # 整形前从 ori_kv 取 KV 序列长度
    topk = 0 if cmp_ratio != 4 else cmp_sparse_indices.size(-1)  # 仅 cmp_ratio==4(C4A) 走稀疏
    layout_q = layout_kv = "BSND"
    query = query.contiguous()                       # [S,B,N,D] -> [B,S,N,D]
    ori_kv = ori_kv.unsqueeze(2).contiguous()        # [S,B,D]   -> [B,S,1,D]
    cmp_kv = cmp_kv if cmp_kv is None else cmp_kv.unsqueeze(2).contiguous()
    cmp_sparse_indices = None if cmp_ratio != 4 else cmp_sparse_indices.unsqueeze(2).contiguous()  # 非稀疏路径同步置 None
    output = SparseAttnSharedKV.apply(query, ori_kv, cmp_kv, cu_seq_lens_q,
        cu_seq_lens_ori_kv, cu_seq_lens_cmp_kv, ori_sparse_indices, cmp_sparse_indices,
        sinks, softmax_scale, cmp_ratio, ori_mask_mode, cmp_mask_mode,
        ori_win_left, ori_win_right, num_heads_q, num_heads_kv, head_dim,
        batch_size, max_seq_len_q, max_seq_len_kv, topk, layout_q, layout_kv)
    return output.contiguous()
# torchtitan_npu/converters/kernels/deepseek_v4_sfa.py — npu_sparse_attn_shared_kv
```

默认 `ori_mask_mode=4`（滑窗）、`cmp_mask_mode=3`（causal）、`ori_win_left=127`/`ori_win_right=0`（对应 sliding_window=128）、`num_heads_kv=1`（Multi-Query Shared-KV）——这些与 cann-recipes-infer 侧 `prepare_fa_kwargs` 的常量一致，训练正反向沿用同一套 SAS 语义。

### Converter 注入（不改上游模型）

`@register_npu_converter("deepseek_v4_sfa")` 的 `DeepSeekV4SFAKernel` 用 `replace_methods` 把三个 NPU adapter 注入 DeepSeek-V4 模型的对应 `forward`，并惰性编译三个 Ascend C op：

```python
@register_npu_converter("deepseek_v4_sfa")
class DeepSeekV4SFAKernel(BaseConverter):
    MODEL_PACKAGE = "torchtitan_npu.models.deepseek_v4"
    SUPPORTED_MODELS = {"deepseek_v4"}

    @classmethod
    def apply(cls, model, model_name, **kwargs):
        pkg = cls.MODEL_PACKAGE
        total = 0
        total += replace_methods("SparseAttention", "forward", sdpa_to_sfa_adapter, package=pkg)  # → SAS/SASG
        total += replace_methods("LiCompute",       "forward", sdpa_to_li_adapter,  package=pkg)  # → LightningIndexer
        total += replace_methods("LiLoss",          "forward", li_loss_adapter,     package=pkg)  # → SLIG
        if total != 0:
            global _li_op, _kl_op, _sas_op
            _li_op  = build_op("lightning_indexer", ["lightning_indexer/binding.cpp"])
            _kl_op  = build_op("sparse_lightning_indexer_grad_kl_loss",
                               ["sparse_lightning_indexer_grad_kl_loss/binding.cpp"])
            _sas_op = build_op("sparse_attn_sharedkv", ["sparse_attn_sharedkv/binding.cpp"])
        return total
# torchtitan_npu/converters/kernels/deepseek_v4_sfa.py — DeepSeekV4SFAKernel
```

SAS 的 forward/backward op 都来自惰性编译的 `_sas_op = build_op("sparse_attn_sharedkv", ...)`，即 SASG 与 SAS 共用同一 Ascend C 算子二进制（`sparse_attn_sharedkv/binding.cpp`），正反向分别绑定其 `npu_sparse_attn_sharedkv` / `npu_sparse_attn_sharedkv_grad` 入口。`sdpa_to_sfa_adapter` 把 `SparseAttention.forward` 替换为对 `npu_sparse_attn_shared_kv` 的调用，从而让稀疏注意力的反向自动落到 `SparseAttnSharedKV.backward`。

## 与 LightningIndexer / SLIG 的配合

V4 续训练里 SASG 不是孤立工作，而是和同批注入的 LI 正向、SLIG 反向构成稀疏注意力训练算子组：

- **LightningIndexer（LI）正向** 由 `sdpa_to_li_adapter` 注入，调 `_li_op.npu_lightning_indexer(..., return_values=True)` 产 `compress_topk_idxs / index_score`，其中 `compress_topk_idxs` 即 SAS / SASG 的 `cmp_sparse_indices`（C4A 稀疏路径选块依据）。LI 反向梯度与 KL Loss 由 [slig](slig.md) 承担——SASG 只为 SAS 主路（`query/ori_kv/cmp_kv/sinks`）供梯度，不碰 Indexer 的可训练张量，二者分工恰如 V3.2 的 SFAG↔SLIG。
- **Indexer 的 TP 约束**：V4 沿用 V3.2 的 DSA 结构，Indexer 在算前向结果和 Loss 时都对 **head 维度做累加（ReduceSum）**，该语义决定无法直接沿 head 维做 TP 切分——强行切分需额外引入 AllGather 才能保证 ReduceSum 正确。这也是 V4 续训练实践放弃 TP、采用**纯 FSDP + 大 EP** 极简切分的原因之一：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/Indexer-TP.png" width="55%"></p>
<p align="center"><sub>图：Indexer 在前向与 Loss 计算中对 head 维度做累加，无法直接沿 head 维 TP 切分（否则需补 AllGather）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·易用性优势 / Indexer-TP）</sub></p>

正向算子下发顺序为 **LI → SAS → LI-Loss**：LI 产 `cmp_sparse_indices` 喂 SAS（C4A 路径），SAS 正向产 `result/softmax_lse` 留待 SASG 反向，LI-Loss 触发 SLIG。整套属 DeepSeek-V4-Flash 续训练实践，承载页见 [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（A3 64 卡 BF16 4K 序列 + MTP1，吞吐 1100 tokens/p/s；定制融合算子贡献约 90% 提升）。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（『高性能融合算子优化』节：SparseAttnSharedkv 五阶段 + 正向 Pipeline、SparseAttnSharedkvGrad 计算流程图 + 5 阶段 Gather/Cube12/Process/Cube345/Scatter + Preload Gather+Cube12 流水；『易用性优势』Indexer-TP 约束）
- [`torchtitan_npu/converters/kernels/deepseek_v4_sfa.py`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/converters/kernels/deepseek_v4_sfa.py)（V4 SAS/SASG op 绑定：`SparseAttnSharedKV.forward/backward` 调 `_sas_op.npu_sparse_attn_sharedkv` / `npu_sparse_attn_sharedkv_grad`、`npu_sparse_attn_shared_kv` wrapper（BSND 整形、`cmp_ratio==4` 走稀疏 topk、`num_heads_kv=1`）、`DeepSeekV4SFAKernel` converter 注册 + `replace_methods` 注入 + `build_op("sparse_attn_sharedkv", ...)`）

## Links

- [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)（跨域：SAS 正向算子，SASG 是其训练反向，共用 `sparse_attn_sharedkv` Ascend C 二进制）
- [ascendc](../../../inference/concepts/frameworks/ascendc.md)（跨域：Ascend C 算子编程框架，本 kernel 的实现底座）
- [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)（跨域：LI 正向算子，产 `cmp_sparse_indices` 喂 SAS/SASG C4A 稀疏路径）
- [slig](slig.md)（同批：LI 反向 + KL Loss，与 SASG 分工承接 V4 稀疏注意力训练反向）
- [sfag](sfag.md)（同源对应：V3.2 DSA 的 SFA 反向算子，SASG 之于 SAS 等价于 SFAG 之于 SFA）
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（承载实践：DeepSeek-V4-Flash A3 64 卡 BF16 续训练，1100 tokens/p/s）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（高性能融合算子优化 / SparseAttnSharedkvGrad）