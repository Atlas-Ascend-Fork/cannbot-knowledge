---
type: Concept
title: LongCat-Flash-Lite
description: LongCat-Flash-Lite 是 LongCat-Flash 的减配验证模型（顶层类 LongcatFlashNgramForCausalLM），保留 MoE + MLA + N-gram Embedding 核心结构、缩小到 14 层 / 256 routed+128 zero expert / top-12 规模，归档 EP 与 TP 两份终态部署报告。优化覆盖 MLA 压缩缓存 + Paged Attention（PA_NZ，省 55% KV）、MLA Prolog 融合（npu_mla_prolog_v3，decode）、算子融合、GE 图模式 decode 整图编译、MoE EP/MC2（dispatch_v2/combine_v2）与 Prefill double-routing；目标 Atlas A2/A3、BF16。config 变体：8ep / 8ep_b8 / 8tp / 8tp_4k1k（长输入）。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: primary
created_at: '2026-04-16T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
- a3
---

# LongCat-Flash-Lite

## Summary

LongCat-Flash-Lite 是 [longcat-flash](longcat_flash.md) 的**减配验证模型**：保留 **MoE + MLA + N-gram Embedding** 核心结构，但层数、expert 数与若干配置缩小到适合**单节点 8 卡（A2 / A3）冷启动优化**的规模（顶层类 `LongcatFlashNgramForCausalLM`，`model_type="longcat_flash_ngram"`）。归档两份终态部署报告：**EP 部署**（`optimization_report_ep.md`）与 **TP 部署**（`optimization_report_tp.md`），两路均为 `world_size=8`。优化覆盖 MLA 压缩缓存 + Paged Attention、MLA Prolog 融合（decode）、算子融合、GE 图模式整图编译、MoE EP/MC2 与 double-routing，目标平台 **Atlas A2 / A3**，BF16。

与满配 [longcat-flash](longcat_flash.md) 不同：Lite 是减配验证模型，**不含** Flash 的 AFD / KVP / 多流控核 / 权重预取 / SuperKernel 等满配独有优化（详见 [longcat-flash](longcat_flash.md)）。以下为 Lite 在终态报告中实测落地的优化。

## Architecture And Serving Traits

减配结构（终态报告 §1.1；层/expert 数取 `LongcatFlashNgramConfig` 默认值）：

- **14 个 decoder layer**（`LongcatFlashNgramConfig` 默认 `num_layers=14`；满配 `LongcatFlashConfig` 默认 61 层）；每层 `LongcatFlashDecoderLayer` 为 **dual sub-layer + shortcut MoE** 结构：2 个 `LongcatFlashMLA` attention block + 2 个 `LongcatFlashMLP`（Dense）+ 1 个共享 `LongcatFlashMoE`（其输出作为 shortcut 加到 sub-layer 1）。
- **MLA**（`LongcatFlashMLA`）：`q_lora_rank=1536`、`kv_lora_rank=512`、`qk_nope_head_dim=128`、`qk_rope_head_dim=64`、`v_head_dim=128`、32 heads。
- **MoE**（`LongcatFlashMoE`）：**256 routed expert + 128 zero/identity expert**（`zero_expert_num`，identity 副本每卡持有、不参与 EP 切分，计算 `MoE(x)=x`）、top-12 路由（`LongcatFlashTopkRouter`）。
- **两个独立 FFN 中间维**（`LongcatFlashNgramConfig` 子类同时携带，非字段歧义）：MoE expert FFN 中间维 `expert_ffn_hidden_size=1024`（EP 报告 §1.1 记 `expert_intermediate=1024`），Dense MLP 中间维 `ffn_hidden_size=6144`（TP 报告 §1.1 文字记 Dense MLP `3072→6144→3072`）——分属 MoE expert 与 Dense MLP 两个子模块，互不冲突。
- **N-gram Embedding**（`NgramEmbedding`）：12 个 sub-embedder 子表 + `post_proj`，是显存大头（~31 B），必须 TP 切分；`ngram_context` 用 `register_buffer` 持久化以便整图编译。主 `embed_tokens` / `lm_head` 在钉定版代码中按基础 vocab `vocab_size=131072` 构造（`embed_tokens = VocabParallelEmbedding(self.vocab_size, ...)`、`lm_head = ColumnParallelLinear(output_size=config.vocab_size, ...)`，`self.vocab_size = config.vocab_size = 131072`，与 TP 报告 §1.1 一致）；EP 报告 §1.1 记 `VocabParallelEmbedding(155136 → 3072)` / `lm_head(3072 → 155136)` 的 `155136` 仅见于 EP 报告 L17/L23，代码与 config 均无此值，属未解释的 doc-vs-code 文档差异。注意 `ngram_vocab_size_ratio=78` 与 155136 无关：它对应 ngram 子表 vocab `self.m = ngram_vocab_size_ratio * vocab_size`（=78×131072≈10.2M，EP 报告另行单列为 `ngram_embedders[12] (~10.2M→256)`），既非主表 vocab、与 155136 亦无算术或结构关系。

### 部署变体（config/*.yaml，world_size=8）

| 配置 | 路径 | 拓扑 | 场景 |
|---|---|---|---|
| `..._rank_8_8ep.yaml` | EP（[expert-parallel](../parallelism/expert_parallel.md)） | attn_tp=4 + attn_dp=2、dense_tp=1(DP)、moe_ep=8、`ngram_embed_tp_size=8`、lmhead_tp=8 | 1K input / 128 output，batch=2 |
| `..._rank_8_8ep_b8.yaml` | 同 EP 拓扑 | 同上，`batch_size=8`（4/DP 组） | 吞吐扩展性 |
| `..._rank_8_8tp.yaml` | TP（[tensor-parallel](../parallelism/tensor_parallel.md)） | 全模块 TP=8（MLA/Dense/MoE/Embedding/LM Head） | 单 batch 低时延 |
| `..._rank_8_8tp_4k1k.yaml` | 同 TP=8 | `input_max_len=4096`、`max_new_tokens=1024` | 长输入 |

两路 `exe_mode: "ge_graph"`、BF16、`enable_mla_prolog: true`（默认）。

## Known Optimizations

终态报告所列优化（默认 Atlas A2/A3、自研 `executor/`、`models/modeling_longcat_flash_lite.py`）。

### MLA 压缩缓存 + Paged Attention

每 token 仅缓存 latent KV（`kv_lora_rank=512` + `qk_rope_head_dim=64` = 576 维），较 vanilla MHA 全展开 1280 维**省 55%**；`cache_mode="PA_NZ"`、`block_size=128`（[kv-cache-manager](../frameworks/kv_cache_manager.md) Paged）。`npu_kv_rmsnorm_rope_cache` 在写 cache 同时完成 KV layernorm + RoPE。Prefill 非 absorb（展开 K/V，FA `NTD_TND` 布局 + `sparse_mode=3`）；Decode absorb（key=value=cache_nope，FA `BSND_NBSD` + `sparse_mode=0`），见 [mla](../modules/mla.md) 机制。

### MLA Prolog 融合（decode）

`npu_mla_prolog_v3` 一次完成 Q-/KV-LoRA 投影 + RMSNorm + RoPE + cache 写入，替代 6–7 个 small op（[mla-prolog](../kernels/mla_prolog.md)）。启用条件 `exe_mode="ge_graph"` 且 `q_lora_rank > 0`，`enable_mla_prolog: false` 可关。Decode 提速 TP 路径 −6%（A3 5.86→5.49 ms）、EP 路径 −3.1%（8.36→8.10 ms）。

> 适用范围约束（源标注）：fused kernel BF16 累加顺序异于拆解 op，从第 ~8（TP）/ ~4–5（EP）decode token 起出现 token-level 选词差异，语义保持等价；严格逐字对齐场景关闭 `enable_mla_prolog`。

### MoE EP / MC2 与 double-routing

MoE EP：256 routed expert EP 切分（EP=8 下每卡 32 个）；128 zero/identity expert 经 `copy_expert_num` **每卡持有、不参与 EP 切分**（计算 `MoE(x)=x`）。**Decode** 走 MC2 一体化融合算子 `npu_moe_distribute_dispatch_v2` / `combine_v2`（开关 `custom_params.enable_moe_mc2_dispatch`，缺省由 `exe_mode=="ge_graph"` 推断，`moe_tp_size==1` 时生效），dispatch 时暴露上述 128 个 zero expert；**Prefill** 走 `_dispatch_double_routing` 两轮 AllToAll（`dispatch_v2` 单层 token 数受 BS 上限约 512 约束，无法直接用于 prefill）。机制与平台约束详见 [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md) 与 [double-routing](../techniques/double_routing.md)。

> 平台约束：A2 上 `npu_moe_distribute_dispatch_v2` 受 `experts_per_rank ≤ 24` 限制（EP=8 下 Lite 为 32/rank 不满足）；A2 部署需 `custom_params.enable_moe_mc2_dispatch: false` 走 double-routing，或 `exe_mode: eager`（丢图 + MLA prolog）。A3 无该限制。

### 算子融合 + GE 图模式

融合算子：`npu_rms_norm` / `npu_add_rms_norm`（残差融合）/ `npu_swiglu`（Dense MLP `MergedColumnParallelLinear` 合并 gate/up）/ `npu_moe_gating_top_k`（router）/ `FusedMoEGMM`（`npu_grouped_matmul`+`npu_swiglu`，expert 计算）。**Decode 整图编译**（`fullgraph=True`，`_can_compile_fullgraph=True`），Prefill 保持 eager（[npu-graph-mode](../techniques/npu_graph_mode.md) ge_graph 后端）。GE 适配：NgramEmbedding 整体入图（`_shift_right_ignore_eos` Python 静态展开 prefix-max，GE 不支持 cummax）、LM head 用 `dist.all_gather_into_tensor`、MoE identity expert 用乘法掩码（GE 不支持布尔索引赋值）、prolog/absorb 权重 `mark_static_address`。

### 跨硬件 / 长输入（TP 报告 §7）

- **A2 vs A3 同代码**（前提 TP=8、BF16、batch=1、input_len=1024 / output_len=128，TP 报告 §7.1）：A3 Decode 较 A2 快 −18%~−35%、吞吐 +21%（如 NgramEmbedding 入图 ge_graph Decode A2 7.14 ms vs A3 5.86 ms）。
- **长输入（A3，TP=8、BF16、batch=1，input_max_len=4096 / max_new_tokens=1024，TP 报告 §7.2；对照 §7.1 短输入 baseline input_len=1024 / output_len=128）**：单步 Decode 仅增 ~9%（5.49→6.00 ms，PA 分块只读活跃 block），Prefill 近似线性（~62→216.5 ms，input ×4 对应 ×3.5），吞吐维持 165+ tok/s。

> 性能数值带平台 + 配置前提（A2/A3、EP/TP、batch、input/output 长度）；详见两报告 §8 累计演进表。

## Gaps（报告 §9 未覆盖 + doc≠code）

- **Prefill 图化**：MoE prefill 仍走 `_dispatch_double_routing` eager，受 `dispatch_v2` BS 上限约束无法图化；prefill 独立 graph 编译未做。
- **权重量化**：W8A8 / W4A16 路径未接入（Lite 当前仅 BF16，frontmatter 未挂量化 tag）。
- **批处理 / 通信重叠**：`batch_size>1` 路径、TP AllReduce 与 GEMM overlap、多流 dispatch overlap 未覆盖。
- **冷启动**：首次图编译 ~80 s，可 `enable_cache_compile` 缓存编译产物。
- ⚠️ **doc≠code（Prefill TP+SP / RS+AG）**：`optimization_report_ep.md` §4.3 描述 Prefill 把 attention 输出 `AllReduce(O)` 拆成 `ReduceScatter(O) + 下一层 AllGather`（`is_sp` 守卫，`attn_tp>1` 且 `attn_dp>1`，ep8 b=8 prefill −27%）。但 `modeling_longcat_flash_lite.py`@2c45117 **无 `is_sp` / `reduce_scatter` 符号**，attention 输出端三处均为 `dist.all_reduce(attn_output, attn_tp_group)`（L430/544/659），`progress_ep.md:82` 亦记 ngram「没有 SP 串接」。该 RS+AG SP 优化为报告描述，HEAD 模型代码未见落地。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat_flash_lite/agentic/optimization_report_ep.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md)（EP 部署：§1 结构 / §2 基线 / §3 并行切分 / §4.1 MLA 压缩缓存+PA / §4.2 MLA Prolog / §4.3 Prefill TP+SP（doc≠code，见 Gaps）/ §5 融合 / §6 图模式 / §7 吞吐扩展 / §8 演进 / §9 未覆盖）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat_flash_lite/agentic/optimization_report_tp.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_tp.md)（TP 部署：§2.1 精度基线 / §4 MLA+PA / MLA Prolog（A3 decode）/ §5 融合 / §6 图模式 / §7.1 A2 vs A3 / §7.2 长输入 4K·1K / §8 演进）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat_flash_lite/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/README.md)（A2/A3、CANN 9.0.0、Agent Skills 工作流）；[`models/longcat_flash_lite/config/`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/config)（`8ep` / `8ep_b8` / `8tp` / `8tp_4k1k` 四份部署 YAML）；[`models/longcat_flash_lite/models/modeling_longcat_flash_lite.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（`LongcatFlashMLA`/`LongcatFlashMoE`/`LongcatFlashDecoderLayer`/`NgramEmbedding`/`LongcatFlashNgramForCausalLM`、`enable_moe_mc2_dispatch` L1630、`copy_expert_num` L914/929、PA `cache_mode="PA_NZ"` L370/496）；[`models/longcat_flash_lite/models/configuration_longcat_flash_lite.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/configuration_longcat_flash_lite.py)（`LongcatFlashNgramConfig` `num_layers=14` / `n_routed_experts=256` / `q_lora_rank=1536` / `kv_lora_rank=512`）
- 原始模型：Meituan `meituan-longcat/LongCat-Flash-Lite`（HF）
- 引入提交：`feat: add longcat-flash-lite model optimized by agent skills`（39595c0，MR!348，refactor-longcatflashlite→master）

## Links

- [longcat-flash](longcat_flash.md)（满配模型；Lite 为其减配验证版）
- [mla](../modules/mla.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [kv-cache-manager](../frameworks/kv_cache_manager.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [double-routing](../techniques/double_routing.md)
- [npu-graph-mode](../techniques/npu_graph_mode.md)
- [atlas-a3](../platforms/atlas_a3.md)
