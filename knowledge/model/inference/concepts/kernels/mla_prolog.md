---
type: Concept
title: npu_mla_prolog (v2 / v3)
description: '`npu_mla_prolog` 是 DeepSeek-V3/R1/Kimi-K2 的 MLA 前置融合算子，在单个 kernel 中完成 Q、KV 两级投影、RMSNorm、RoPE，并按 cache_index 写入 Paged NZ KV Cache，以减少 Decode 下发和 kernel gap。R1 Decode 使用 v3 接口，支持权重、KV Cache 和 Query 量化模式，并与 FIA v2 配合。DeepSeek-V4 虽改为 MQA/Shared-KV，仍以 PyPTO 版本完成 Q/KV 前置投影，加入 interleaved Partial RoPE、动态 shape 静态展开、buffer 合图、split-K 和 MPMD 流水。独立的 AscendC RoPE+Quant 算子尚未证实接入生产路径，v2/v3 的完整语义差异也仍待确认。'
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a3
- '950'
---

# npu_mla_prolog (v2 / v3)

## Summary

DeepSeek-V3 / R1 / Kimi-K2 **MLA 前置计算的端到端融合算子**：在一个 kernel 内完成 Q 两级投影（q_a_proj → RMSNorm → q_b_proj）、KV 两级投影（kv_a_proj_with_mqa → RMSNorm → kv_b_proj 的 K 分量）、RoPE 施加、以及按 `cache_index` 将 K/V 写入 Paged NZ KVCache。替代原生的多个 Linear + RMSNorm + rotary 子图，显著降低 Decode 阶段的 host 下发和 kernel 间 gap。

在 DeepSeek-R1 Decode 路径由 `enable_mla_prolog: True` 使能（YAML 级别），对应 `DeepseekV3Attention.forward_page_attention_mla_prolog` 分支（`models/deepseek_r1/models/modeling_deepseek.py:L1186`）。R1 使用 **v3** 版本（`torch.ops.npu.npu_mla_prolog_v3`）。DeepSeek-V4 attention 主体改为 MQA/Shared-KV，但仍调用 MLAProlog 做 Q/KV 前置投影，并把其适配为 PyPTO 算子（inplace interleaved RoPE / Unrollist 分档 / 合图，见 [DeepSeek-V4 适配](#deepseek-v4-适配pypto)）。

## Role In Pipeline

```mermaid
flowchart LR
 H[hidden_states<br/>BF16 or INT8+pertoken_scale] --> P[npu_mla_prolog_v3]
 subgraph P[npu_mla_prolog_v3 内部]
 direction TB
 A[q_a_proj + q_a_layernorm + q_b_proj]
 B[kv_a_proj_with_mqa + kv_a_layernorm]
 C[RoPE on q_pe / k_pe]
 D[K/V write to Paged NZ cache<br/>cache_index]
 end
 P --> Q[q_nope, q_pe, dequant_scale_q_nope]
 Q --> FA[npu_fused_infer_attention_score_v2]
 P --> KR[nope_cache, rope_cache<br/>已就绪, PA_NZ 布局]
 KR --> FA
```

- 输入：`hidden_states`（BF16 或 INT8 + `pertoken_scale`）、三个权重 + 三组 scale（量化场景）、`rope_cos` / `rope_sin`、`cache_index`、现有 `kv_cache` / `kr_cache`。
- 输出：`q_nope`、`q_pe`、`dequant_scale_q_nope`（供下游 FA 做 Q-side dequant）。
- 副作用：按 `cache_index` 原地更新 `kv_cache`（NoPE 部分）与 `kr_cache`（RoPE 部分）。

## Key Parameters

关键 launch 签名（源 `models/deepseek_r1/models/modeling_deepseek.py:L1216`）：

```python
q_nope, q_pe, dequant_scale_q_nope, _, _ = torch.ops.npu.npu_mla_prolog_v3(
 token_x=hidden_states_int8 if enable_mm_quant_a8w8 else hidden_states,
 weight_dq=self.q_a_proj.weight,
 weight_uq_qr=self.q_b_proj.weight,
 weight_uk=self.kv_b_proj_w_k,
 weight_dkv_kr=self.kv_a_proj_with_mqa.weight,
 rmsnorm_gamma_cq=self.q_a_layernorm.weight,
 rmsnorm_gamma_ckv=self.kv_a_layernorm.weight,
 rope_sin=sin.squeeze(1), rope_cos=cos.squeeze(1),
 cache_index=cache_index,
 kv_cache=nope_cache, kr_cache=rope_cache,
 dequant_scale_x=pertoken_scale if enable_mm_quant_a8w8 else None,
 dequant_scale_w_dq=self.q_a_proj.weight_scale.view(1, -1) if enable_mm_quant_a8w8 else None,
 dequant_scale_w_uq_qr=self.q_b_proj.weight_scale.view(1, -1) if enable_mm_quant_a8w8 else None,
 dequant_scale_w_dkv_kr=self.kv_a_proj_with_mqa.weight_scale.view(1, -1) if enable_mm_quant_a8w8 else None,
 quant_scale_ckv=self.ckv_scale_reci if self.kv_cache_quant_mode == "int8" else None,
 quant_scale_ckr=None,
 smooth_scales_cq=None,
 rmsnorm_epsilon_cq=self.q_a_layernorm.variance_epsilon,
 rmsnorm_epsilon_ckv=self.kv_a_layernorm.variance_epsilon,
 cache_mode="PA_NZ",
 weight_quant_mode=2 if enable_mm_quant_a8w8 else 0,
 kv_cache_quant_mode=1 if self.kv_cache_quant_mode == "int8" else 0,
 query_quant_mode=1 if enable_mm_quant_a8w8 and self.kv_cache_quant_mode == "int8" else 0,
)
```

### 量化模式枚举（来自代码注释）

- **`weight_quant_mode`**：
 - 0：non-quant；
 - 1：`weight_uq_qr` int8-quant；
 - 2：`weight_dq`、`weight_uq_qr`、`weight_dkv_kr` int8-quant（即完整 W8 量化）；
 - 3：上述三项 mxfp8-quant。
- **`kv_cache_quant_mode`**：
 - 0：non-quant；
 - 1：per-tensor quant（C8 走此模式）；
 - 2：per-channel quant；
 - 3：per-tile quant。
- **`query_quant_mode`**：
 - 0：non-quant；
 - 1：per-token-head quant（仅在 W8 + C8 组合下启用）。

### cache_mode

`"PA_NZ"` — Paged Attention + NZ 亲和布局。配合 `enable_pa: True` 与 `pa_block_size: 128`，支持 `block_table` 的分页 KVCache 管理。

## Performance Signals

- **Decode TPOT**：是 W8A8C8 + MTP1 decode 42~45 ms TPOT 的核心组成。
- **Host 下发**：eager 下多算子分别下发、MLA 前置阶段 host 占用高；`mla_prolog` 单 kernel 替代后 host 压力显著下降。
- **量化耦合**：Q-side dynamic quant 与 weight dequant 被内嵌，不再需要独立的 `npu_dynamic_quant` 调用。

## Optimization Notes

- **必须与 `npu_fused_infer_attention_score_v2` 配合**：`dequant_scale_q_nope` 要透传给 FA 作为 `dequant_scale_query`，否则 C8 量化场景下 Q-side 解量化错位。
- **KV NZ view 调整**：算子输出 `nope_cache` 是 flat 视图，之后按 `factor = 2 if kv_cache_quant_mode==int8 else 1` 的 INT8 打包 factor 重新 view 到 `[block_num, 1, kv_lora_rank/(16·factor), block_size, 16·factor]` 才能喂给 FA。
- **MTP 分支**：`if q_len > 1: sparse_mode = 3` 让下游 FA 用 MTP 因果 mask；否则 `sparse_mode = 0` 且 `attention_mask = None`。
- v2 与 v3 的差异：R1 实际使用 v3，文档提及的 `npu_mla_prolog_v2` 为早期入口，**语义差异 source 未明示，待验证**。

## DeepSeek-V4 适配（PyPTO）

DeepSeek-V4 的 attention 主体由 MLA 改为 MQA/Shared-KV，但仍调用 MLAProlog 做 Q/KV 前置投影。V4 把 MLAProlog 适配为 **PyPTO 算子**（上文 R1/Kimi 走的 `torch.ops.npu.npu_mla_prolog_v3` 端到端 AscendC 融合算子内容保留有效，对应 V3/R1/Kimi 谱系）。

### inplace interleaved RoPE

PyPTO 版 MLAProlog 的计算过程：

- **Query**：两次采样 + RmsNorm（第二次 RmsNorm 对应代码 `q_b_norm`，其 weight 恒为 1；代码符号对应、weight 恒 1 未逐权重核验），最后对 `-1` 轴的后 `rope_dim` 维度做 inplace interleaved RoPE：$c^Q = RmsNorm(x@wq\_a)$；$q = RmsNorm(c^Q@wq\_b)$；$q[\cdots,-rope\_dim:] = ROPE(q[\cdots,-rope\_dim:])$。
- **KV**：一次采样 + RmsNorm，再对后 `rope_dim` 维度做 inplace interleaved RoPE：$k = RmsNorm(x@wkv)$；$k[\cdots,-rope\_dim:] = ROPE(k[\cdots,-rope\_dim:])$。

代码侧 RoPE 由 `torch.ops.custom.inplace_partial_rotary_mul(..., rotary_mode="interleave", partial_slice=self.partial_slice)` 完成（`models/deepseek-v4/models/modeling_deepseek.py` 的 `mla_prolog_prefill`/`mla_prolog_decode` 路径，`partial_slice = [head_dim - rope_head_dim, head_dim]`）；PyPTO 整图路径走 `mla_prolog_pypto`（非量化）/ `mla_prolog_quant_pypto`（量化，多带 `wq_b_scale`）入口（`ops.pypto_python.impl.*`，由 `mla_prolog` 在 `enable_pypto` 时分派）。

> 仓内另发布了独立 AscendC 算子，注册符号为 `partial_rotary_mul_quant`（`torch.ops.custom.partial_rotary_mul_quant`，Python wrapper `npu_partial_rotary_mul_quant`；融合 RoPE + 量化）。该算子新增于 commit `8ced1a7`——注意其 commit 消息标题虽写作 "inplace_partial_rotary_mul_quant"，但**实际注册符号为 `partial_rotary_mul_quant`（无 `inplace_` 前缀）**，源码目录亦为 `src/partial_rotary_mul_quant/`。**V4 模型代码中 MLAProlog 各路径调用的是 `inplace_partial_rotary_mul`（无 `_quant`），未见调用 `partial_rotary_mul_quant`**，故此处不声称该融合 RoPE+Quant 算子已接入 MLAProlog 生产路径（**源/代码未明示其在 MLAProlog 的使用，待验证**）。

### Unrollist 动态转静态 + 合图

- **Unrollist 分档**：Prefill / Decode 下 token 数 `t` 差异巨大，单套 Tile 切分难兼顾。对动态 `t` 多分档、Tile 切分用静态 tTile：`unroll_list = [128, 64, 32, 16, 1]`，经 `pypto.loop_unroll(..., unroll_list=unroll_list)` 把动态循环展开为静态图，在不同场景均达较优性能。
- **合图优化**：设 `pass_options={"cube_nbuffer_mode":1, "vec_nbuffer_mode":2, "vec_nbuffer_setting":{-1:2}}` 把相同结构子图合并，避免子图数过大与重复搬运，增大核内流水调度空间。
- **MatMul 优化**：按参与 matmul 的 tensor shape 设 tile_shape 把任务均衡分到各 aic 核；K 轴过大时 `enable_split_k`，大 shape 下 `enable_multi_data_load` 开大包搬运提升带宽。
- **MPMD 流水并行**：Decode 下 `x@wq_a` 与 `x@wkv` 都用不满全部核，可并行执行；Query / KV 后续 RmsNorm 亦可并行。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-r1/deepseek_r1_decode_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md) "MLA 低秩压缩优化 → 使能融合算子"章节；[官方文档 torch_npu.npu_mla_prolog_v2](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_mla_prolog_v2.md)；`models/deepseek_r1/models/modeling_deepseek.py:L1186-L1304`。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_pypto_operator_guide.md) `## MlaProlog`（inplace interleaved RoPE 公式、Unrollist 分档、合图/MatMul/MPMD 优化）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/models/modeling_deepseek.py#L801`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modeling_deepseek.py#L801)（代码核对：`mla_prolog_pypto`/`mla_prolog_quant_pypto` 入口、`inplace_partial_rotary_mul` `rotary_mode="interleave"` + `partial_slice`、`mla_prolog` 按 `enable_pypto` 分派 prefill/decode/pypto 三路）。AscendC 融合 RoPE+Quant 算子（注册符号 `partial_rotary_mul_quant` / `torch.ops.custom` / Python `npu_partial_rotary_mul_quant`，源码 `ops/ascendc/.../src/partial_rotary_mul_quant/`）见 commit `8ced1a7`（commit 标题作 "inplace_partial_rotary_mul_quant" 但注册符号无 `inplace_` 前缀；diff 2f82d10..2c45117，未见接入 MLAProlog 生产路径）。

## Links

- [deepseek-r1](../models/deepseek_r1.md)
- [deepseek-v4](../models/deepseek_v4.md)（V4 attention 主体为 MQA/Shared-KV，但仍调用 MLAProlog 做 Q/KV 前置投影）
- [mla](../modules/mla.md)
- [fused-infer-attention-score](fused_infer_attention_score.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [ascendc](../frameworks/ascendc.md)
- [pypto](../frameworks/pypto.md)（V4 MLAProlog 走 PyPTO 算子实现）
- [sparse-attn-sharedkv](sparse_attn_sharedkv.md)（V4 SAS 的 Q 输入由 MLAProlog 前置投影产出）
- [longcat-flash-lite](../models/longcat_flash_lite.md)（LongCat-Flash 减配验证模型，Decode 用 `npu_mla_prolog_v3` 融合 Q-/KV-LoRA + RMSNorm + RoPE + cache 写入，`enable_mla_prolog` 可关）
- [tilelang-rope](../../../training/concepts/kernels/tilelang_rope.md)（跨域·训练：RoPE 的 TileLang 训练实现（含反向））
