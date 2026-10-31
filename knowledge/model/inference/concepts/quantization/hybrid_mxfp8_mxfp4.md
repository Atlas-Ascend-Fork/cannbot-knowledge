---
type: Concept
title: DeepSeek-V4 950 混合量化：HiF8、MXFP8 与 MXFP4
description: 更新 950 的 HiF8 混合矩阵、FP8/HiF8 KV 记录格式和 A4W4 的转换、路由及加载校验。
tags:
- task.design
- topic.precision
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/utils/convert_model.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/utils/convert_config.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/common_modules.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/indexer.py
  role: implementation
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T15:17:34Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      - decode
---

# DeepSeek-V4 950 混合量化

## 格式与模块边界

950 路径支持原生 FP8-MXFP4、MXFP8-MXFP4，以及新增的 HiF8-MXFP8-MXFP4；选择由转换后的 quant_config 和实际模块决定，不能只按文件夹名判断。

| 模块 | MXFP8-MXFP4 | HiF8-MXFP8-MXFP4 |
| --- | --- | --- |
| MLA Q/KV 投影、输出投影 | MXFP8 W8A8 | HiF8 W8A8 |
| Indexer Q 投影 | MXFP8 W8A8 | HiF8 W8A8 |
| Indexer weights_proj | 不量化 | HiF8 W8A8 |
| Compressor wkv / wgate | 不量化 | HiF8 W8A8 |
| 路由专家 | MXFP4 W4、MXFP8 A8 | MXFP4 W4、MXFP8 A8 |
| 共享专家 | MXFP8 W8A8 | MXFP8 W8A8 |
| LMHead | 不量化 | 不量化 |

HiF8 Linear 使用静态 Per-Channel 权重量化、Per-Tensor 激活与 FP32 scale。该路径的 Indexer 不做 Hadamard 旋转，Q 由 Partial RoPE 后量化为 HiF8，LI 使用 quant_mode=4 与单位 descale；不能照搬 Int8/FP8 的旋转和 scale 布局。

## KV Cache 与当前算子接口

`update_kv_quant_settings` 在 950 的 HiF8 mm 模式下将 KV/LI cache 设为 hifloat8，其他浮点 mm 模式设为 float8。两类格式不同：

- float8 KV 是混合打包记录：NoPE 为 FP8，RoPE 为 BF16，另有每 64 个 NoPE 元素的 BF16 scale；最后按 32 字节对齐，以 uint8 保存，调用 mixed_quant_sparse_flash_mla 时转 FLOAT8 view。记录维度为 align_up(nope_dim + 2×rope_dim + 2×nope_dim/64, 32)，不是所有通道都减半。指南的 C8/约 2× 为总体策略口径，实际容量按记录和状态缓存计算。
- hifloat8 KV 以 head_dim 个字节保存，Query/KV 经量化后走 quant_sparse_flash_mla，显式传 q/ori_kv/cmp_kv descale。LI cache 由 indexer_quant_cache 写回，HiF8 slot_mapping 要转连续 INT32；Q/Key scale 的当前接口与 FP8 Per-Token-Head scale 不相同。

当前 FP8 LI 使用动态 Per-Token-Head FP8 与 FP32 scale。整数路径见[A3 量化](int8_int4_hybrid.md)，不可把 950 的格式套到 A3。

## 转换与新增 A4W4

原生混合权重推理仍需按 README 转换 config.json，先备份；转换脚本会覆盖它。当前 convert_model.py 的可执行选项包括 `w4a8-mx`、`w4a4-mx`、`w4a8-mx-hif`。`w4a4-mx` 对两次路由专家 Matmul 的激活均采用 MXFP4，config 中 moe_activation_bits=4；默认 A8 为 8。模型在加载前拒绝非 950 的 A4W4，并校验选择 W4A4MxFp4MoEGMMMethod。

A4W4 Decode dispatch 提前量化激活以降低 EP 通信，quant_mode=4、y_dtype=float4_e2m1fn_x2，re-routing 需同一 tokens_dtype；不能只把 GMM 权重 dtype 改为 FP4。低时延 TP 与 EP 的路由流程不同，配置边界见[部署流程](../../guides/models/deepseek_v4_deployment.md)。

## 验证

固定权重、配置、后端和输入，检查转换结果、每个模块量化方法、scale/打包记录、接受率及输出精度，再比较时延与容量。来源性能见[950 观测](../../optimizations/benchmark_observations/deepseek_v4_950_source_benchmark.md)；本次未执行模型或复测。DiT MXFP8 是[另一条实现](mxfp8_a8w8.md)。
