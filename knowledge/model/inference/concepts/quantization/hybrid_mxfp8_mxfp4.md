---
type: Concept
title: Hybrid FP8-MXFP4 / Hybrid MXFP8-MXFP4 (DeepSeek-V4 Ascend 950PR/DT)
description: DeepSeek-V4 在 Ascend 950PR/DT 上采用 FP8 与 MXFP4 混合量化。原生 FP8-MXFP4 可直接加载 HuggingFace 权重；面向 Flash/Pro 的 MXFP8-MXFP4 将部分 Linear 改为 MXFP8，并以 MXFP4 W4A8 执行 MoE 路由专家，共享专家仍为 W8A8。MLA/Indexer 的 KV Cache 可用 Per-Group-64 FP8、E8M0 Scale 的 C8 伪量化，实现存 8 位、算 16 位并约减半 KV 占用；Compressor 与 LMHead 不量化。950DT 16 卡 DP+EP、8192 token、MTP3 条件下，MXFP8-MXFP4 为 9.84 ms/1625 TPS，原生方案为 11.06 ms/1447 TPS。该方案限定 950 平台，不等同于 HunyuanVideo DiT 的 mxfp8-a8w8。
tags:
- task.design
- topic.precision
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md
  role: primary
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- '950'
---

# Hybrid FP8-MXFP4 / Hybrid MXFP8-MXFP4

## Summary

DeepSeek-V4 在 Ascend 950PR/DT 代际平台上的浮点混合量化方案，引入 **MXFP4**（Micro-scaling FP4，OCP 微缩放格式，dtype `float4_e2m1fn_x2`）量化——本仓/本知识库首次使用该格式：

- **Hybrid FP8-MXFP4（原生）**：HuggingFace 发布的原始权重格式 —— 部分 Matmul 用 FP8 量化、MoE 模块用 MXFP4 量化；可在 950 平台**权重无损平滑迁移**直接推理。
- **Hybrid MXFP8-MXFP4（硬件亲和，推荐 Flash/Pro）**：用 **MXFP8** 替换原生 FP8 格式的 Linear 模块（部分 Matmul MXFP8 + MoE MXFP4），在 Prefill/Decode 高吞吐场景进一步提升 950 算力利用率。KV Cache 采用 **C8 伪量化（动态存 8 算 16，Per-Group-64 FP8，Scale 格式 E8M0）**，超长序列省 2× KV 显存。

二者均区别于 Atlas A3 Pod 的整数路径（见 [int8-int4-hybrid](int8_int4_hybrid.md)）：A3 走 Int8/W4A8 整数 + KV C16；950 走 FP8/MXFP8 浮点 + KV C8。MXFP8 在本仓另有 DiT 场景实现（[mxfp8-a8w8](mxfp8_a8w8.md)，HunyuanVideo Linear），与此处 V4 LLM 场景为不同模型用途。

## Mechanism

### Hybrid MXFP8-MXFP4 逐模块量化矩阵

源（`deepseek_v4_inference_guide.md` 量化策略 / Ascend 950PR/DT / Hybrid MXFP8-MXFP4）：

| 模块 | W 侧 | A 侧 | KV / Cache | 备注 |
| ---- | ---- | ---- | ---- | ---- |
| MLAProlog | `q_a_proj` / `q_b_proj` / `kv_proj` W8A8（MXFP8） | — | **KV Cache C8 伪量化** | 动态存 8 算 16 |
| IndexerProlog | `q_b_proj` W8A8 | `indexer_q` A8 | Indexer Cache **C8** | `indexer_weight` 不量化 |
| LightningIndexer | — | `batch_matmul` **FP8 计算** | — | A8C8，见 [lightning-indexer](../kernels/lightning_indexer.md) |
| Compressor | Linear 不量化 | — | — | 见 [compressor](../kernels/compressor.md) |
| MLAEpilog | `o_a_proj` / `o_b_proj` W8A8 | — | — | A3 Int8 档 `o_a_proj` 不量化，此处量化（差异） |
| MoE | 路由专家 Linear **W4A8（MXFP4）** | 共享专家 Linear W8A8 | — | — |
| LMHead | 不量化 | — | — | — |

源注：此处 W8A8 的 W 与 A 均指 **MXFP8** 量化；LI A8C8 = Indexer Q/Cache 动态 Per-Token-Head **FP8**（Scale 格式 FP32）；KV Cache C8 = 动态 Per-Group-64 **FP8**（Scale 格式 E8M0）。

### MXFP4 量化算法（代码核对）

MXFP4 路径实现于 `module/quantization/mxfp4.py`：

- MoE GMM 方法类 `W4A8MxFp4MoEGMMMethod`，及上/下投影分别 W4A4/W4A8 的子类 `UpGateW4A4DownW4A8MxFp4MoEGMMMethod`（继承前者）。
- MXFP4 权重 dtype 为 `torch_npu.float4_e2m1fn_x2`；激活量化经 `torch_npu.npu_dynamic_mx_quant(x, dst_type=torch.float8_e4m3fn)`（A8 用 FP8 E4M3）或 `dst_type=torch_npu.float4_e2m1fn_x2`（A4）。
- 权重转换 `convert_model.py` 从 `mx_quantize.py`（本仓 `models/deepseek-v4/utils/mx_quantize.py`）导入 `quantize_mx` / `pack_uint4` / `unpack_uint4` / `f4_unpacked_to_f32` / `f32_to_f4_unpacked` 完成 MXFP4 打包。
- 转换为 Hybrid MXFP8-MXFP4 权重：`--quant_type w4a8-mx`（源 README）。

> 代码核对：modeling 中 `quant_mode` 注释「2: mxfp8 for dst_dtype e5m2; 3: mxfp8 for dst_dtype e4m3; 4: fp8 for dst_dtype e5m2; 5: fp8 for dst_dtype e4m3」；950 平台当 `"float" in mm_quant_mode` 时 KV/LI Cache 置 `float8`，否则 LI Cache 置 `int8`（`update_kv_quant_settings`）。

## Applicable Scenarios

- **Ascend 950PR/DT，Flash/Pro**：Hybrid MXFP8-MXFP4 为推荐档，高吞吐 Prefill/Decode。
- **权重平滑迁移**：原生 Hybrid FP8-MXFP4 权重可直接在 950 推理，无需 convert（源 README：原生权重推理可跳过转换步骤）。
- 超长序列（128K~1M）：C8 KV 伪量化省 2× KV 显存。

## Constraints

- **仅 950PR/DT 代际**：FP8/MXFP8/MXFP4 浮点路径与 KV C8 为 950 平台特性；A3 Pod 走整数路径（[int8-int4-hybrid](int8_int4_hybrid.md)）。
- **MXFP4 算法依赖 `mx_quantize`**：打包/解包逻辑在本仓 `models/deepseek-v4/utils/mx_quantize.py`（`quantize_mx`）；底层 `npu_dynamic_mx_quant` / `float4_e2m1fn_x2` 由 torch_npu 提供。
- **MXFP8 区分 DiT 场景**：本页为 V4 LLM 的部分 Matmul MXFP8；[mxfp8-a8w8](mxfp8_a8w8.md) 是 HunyuanVideo DiT Linear 的 MXFP8 A8W8，用途不同。

## Known Results

950DT，16 卡，DP+EP（MTP 投机 + 强制 EPLB，源 Benchmark；同序列长度两种 DataType 并列为选型证据，平台前提 950DT）：

| 规格 | Global Batch Size | Chips | MTP | DataType | SeqLen | TPOT (ms) | Throughput (Tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Flash | 256 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 9.84 | 1625.31 |
| Flash | 1536 | 16 | 1 | Hybrid MXFP8-MXFP4 | 8192 | 20.33 | 4722.22 |
| Flash | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 1048576 | 8.22 | 121.70 |
| Flash | 256 | 16 | 3 | **Hybrid FP8-MXFP4** | 8192 | 11.06 | 1447.00 |
| Flash | 1536 | 16 | 1 | **Hybrid FP8-MXFP4** | 8192 | 24.28 | 3953.49 |
| Pro | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 17.64 | 56.7 |
| Pro | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 131072 | 19.46 | 51.38 |

同 8192 序列、MTP3、Global Batch Size 256：MXFP8-MXFP4（9.84ms / 1625 TPS）相比原生 FP8-MXFP4（11.06ms / 1447 TPS）TPOT 更低、吞吐更高 —— MXFP8 替换 FP8 在高吞吐场景的算力利用率收益。注意各行操作点不同：1625TPS@9.84ms 为 GBS256/MTP3、4722TPS@20.33ms 为 GBS1536/MTP1，吞吐随 batch 与 MTP 档不同不可直接横比。两组 DataType 对比数据带平台前提保留为选型证据。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md)「量化策略 / Ascend 950PR/DT / Hybrid MXFP8-MXFP4」（逐模块矩阵 L248-269）+「Benchmark / 950DT」（Flash/Pro 表 L341-370）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/quantization/mxfp4.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/module/quantization/mxfp4.py)（已代码核对：`W4A8MxFp4MoEGMMMethod` / `UpGateW4A4DownW4A8MxFp4MoEGMMMethod` / `float4_e2m1fn_x2` / `npu_dynamic_mx_quant`）、[`models/deepseek-v4/utils/mx_quantize.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/utils/mx_quantize.py)（`quantize_mx` L375）、[`models/deepseek-v4/models/modeling_deepseek.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modeling_deepseek.py)（`quant_mode` 注释 L494、`update_kv_quant_settings` 950 float8 分支 L1786-1796）、[`models/deepseek-v4/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/README.md)（`--quant_type w4a8-mx` L140）
- 溯源（@2c45117）：`5df82b1` support deepseek v4（MR!366，引入 MXFP4 量化路径）；`5ba7598` 950 combine quant

## Links

- [deepseek-v4](../models/deepseek_v4.md)
- [int8-int4-hybrid](int8_int4_hybrid.md)
- [mxfp8-a8w8](mxfp8_a8w8.md)
- [w4a8c8](w4a8c8.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [compressor](../kernels/compressor.md)
- [ascend-950](../platforms/ascend_950.md)（原生 FP8 / MXFP4 浮点算力的硬件平台来路）
- [sana-video](../models/sana_video.md)（MXFP4 `float4_e2m1fn_x2` 的另一用途：SANA DiT 的 `quant_type=a4w4`，`QuantLinear.forward_a4w4`，部分层回退 a8w8；与本页 DeepSeek-V4 MoE W4A8 MXFP4 为不同模型场景）

<!-- cannbot:related:start -->
## 相关

- [EPLB 专家重映射漏搬独立 scale 张量：per-expert 参数清单缺 scale 致权重/scale 失配、静默掉精度](../../runbooks/precision/eplb_remap_drops_independent_scale_tensor.md)（`related`）：专家权重采用**独立 scale 量化布局**：反量化时需要「量化权重张量」与其**独立存放的 scale 张量**成对使用，缺一不可。；｜ MoE ｜ 路由专家 Linear **W4A8（MXFP4）** ｜ 共享专家 Linear W8A8 ｜ — ｜ — ｜；前者规定 EPLB 搬运必须覆盖独立 scale，后者界定 DeepSeek-V4 950 上 MXFP4 路由专家这一具体适用量化域。
- [Int8 / Hybrid INT8-INT4 (DeepSeek-V4 Atlas A3 Pod)](int8_int4_hybrid.md)（`related`）：二者均区别于 Atlas A3 Pod 的整数路径（见 ［int8-int4-hybrid］(int8_int4_hybrid.md)）：A3 走 Int8/W4A8 整数 + KV C16；950 走 FP8/MXFP8 浮点 + KV C8。；DeepSeek-V4 在 ［atlas-a3］(../platforms/atlas_a3.md) Pod 平台上的两档整数量化方案，二者均以原生 Hybrid FP8-MXFP4 权重为转换起点：。两卡共同完成 DeepSeek-V4 从同一原生权重出发、按 950 与 A3 平台选择浮点或整数量化路线的部署决策。
- [W4A8C8 (MoE W4A8 + Attention W8A8C8)](w4a8c8.md)（`related`）：焦点卡写明“950PR/DT 的 Hybrid MXFP8-MXFP4 走 **MXFP4 浮点变体**的 W4A8”，候选卡写明“路由专家 Linear **W4A8（MXFP4）**”。焦点指出 950 的 W4A8 是 MXFP4 浮点变体，候选给出路由专家与共享专家的位宽分工，可防止误当整数 INT4。
<!-- cannbot:related:end -->
