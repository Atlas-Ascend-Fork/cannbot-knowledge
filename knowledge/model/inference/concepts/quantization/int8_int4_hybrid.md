---
type: Concept
title: Int8 / Hybrid INT8-INT4 (DeepSeek-V4 Atlas A3 Pod)
description: DeepSeek-V4 在 Atlas A3 Pod 平台的两档整数量化方案，均以原生 Hybrid FP8-MXFP4 权重为转换起点。Int8（W8A8C16，推荐 Flash）：仅对参数量多的部分 Linear（MLA q_b_proj/o_b_proj、Indexer q_b_proj）做静态 Per-Channel W8 + 动态 Per-Token A8，**KV Cache 维持 C16（BF16 存算）而非 C8**，LI 经 A8C8（Indexer Q/Cache 动态 Per-Token-Head Int8）降时延，LightningIndexer batch_matmul Int8 计算，Compressor Linear/IndexerProlog indexer_weight 不量化，LMHead 不量化。Hybrid INT8-INT4（推荐 Pro 1.6T）：在上策略基础上仅 MoE 路由专家 Linear 改 W4A8（静态 Per-Channel Int4 + 动态 Per-Token Int8）、共享专家保持 W8A8，缓解 MoE 访存墙。权重转换 convert_model.py --quant_type w8a8-int / w4a8-int(--quant_param_path)；argparse choices=['w8a8-int','w4a8-int','bfloat16','w4a8-mx']，docstring/assert 另列 w8a8-mx 但 choices 未含（doc≠runnable flag）。KV C16 ≠ V3.2-Exp 的 C8 属代际选型差异不互相覆盖。Known Results：A3 Pod 64卡 DP+EP W8A8C16 Flash 8192 序列 TPOT 27.82/29.17ms、吞吐 4025/4388 TPS（MTP1）。
tags:
- task.design
- topic.precision
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md
  role: primary
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a3
---

# Int8 / Hybrid INT8-INT4

## Summary

DeepSeek-V4 在 [atlas-a3](../platforms/atlas_a3.md) Pod 平台上的两档整数量化方案，二者均以原生 Hybrid FP8-MXFP4 权重为转换起点：

- **Int8（W8A8C16，推荐 Flash）**：仅对参数量较多的部分 Linear（MLA `q_b_proj`/`o_b_proj`、Indexer `q_b_proj`）做静态 Per-Channel W8 + 动态 Per-Token A8 量化；**KV Cache 维持 C16（BF16 存算）而非 C8**；LI 通过 A8C8 降低计算时延，同步优化 TTFT/TPOT。
- **Hybrid INT8-INT4（推荐 Pro）**：在 Int8 策略基础上，对 MoE 路由专家的 Linear 改用 [w4a8c8](w4a8c8.md) 概念中的 **W4A8**（静态 Per-Channel Int4 权重 + 动态 Per-Token Int8 激活），共享专家保持 W8A8，显著降低 Pro（1.6T 参数）MoE 的存储与访存开销。

"C16" 指 KV Cache 不做 Int8 压缩、以 BF16 存与算；这是与 DeepSeek-V3.2-Exp 的 [w8a8c8](w8a8c8.md)（C8 = 动态 Per-Token-Head-Tile-128 Int8）的关键差异，属模型代际选型不同，不互相覆盖。

> ⚠️ 矛盾标记：同源谱系两模型的 KV Cache 代际差异 —— V4 A3 Pod 走 C16（BF16 存算），V3.2-Exp 走 C8（动态 Per-Token-Head-Tile-128 Int8）。二者为代际选型不同，并存保留、不互相覆盖（口径与 model 页一致）。

## Mechanism

### Int8（W8A8C16）逐模块量化矩阵

源（`deepseek_v4_inference_guide.md` 量化策略 / Atlas-A3 Pod / Int8）：

| 模块 | W 侧 | A 侧 | KV / Cache | 备注 |
| ---- | ---- | ---- | ---- | ---- |
| MLAProlog | 仅 `q_b_proj` W8A8 | — | **KV Cache C16（BF16 存算）** | 其它 Linear 不量化 |
| IndexerProlog | 仅 `q_b_proj` W8A8 | `indexer_q` A8 | Indexer Cache **C8** | `indexer_weight` 不量化 |
| LightningIndexer | — | `batch_matmul` **Int8 计算** | — | A8C8 降时延，见 [lightning-indexer](../kernels/lightning_indexer.md) |
| Compressor | Linear 不量化 | — | — | 见 [compressor](../kernels/compressor.md) |
| MLAEpilog | `o_b_proj` W8A8 | — | — | `o_a_proj` 不量化 |
| MoE | 路由 + 共享专家 Linear **W8A8** | — | — | — |
| LMHead | 不量化 | — | — | — |

源注：W8A8 = W 静态 Per-Channel Int8 + A 动态 Per-Token Int8；LI 的 A8C8 = Indexer Q 动态 Per-Token-Head Int8 + Indexer Cache 动态 Per-Token-Head Int8。

设计理由（源文档）："出于性能考虑，只对参数量较多的部分 Linear 模块进行量化……KV Cache 暂时维持 BF16 存算。"

### Hybrid INT8-INT4 差异

仅替换 MoE 路由专家（其余同 Int8 矩阵）：

| 模块 | Int8（W8A8C16） | **Hybrid INT8-INT4 差异** |
| ---- | ---- | ---- |
| MoE 路由专家 | W8A8 | **W4A8**（W4 = 静态 Per-Channel Int4，A8 = 动态 Per-Token Int8） |
| MoE 共享专家 | W8A8 | W8A8（不变） |

源文档："由于 DeepSeekV4-Pro 模型的参数量较大，MoE 部分使用 W8A8 推理会面临较大的内存和访存瓶颈……主要对 MoE 部分采用 INT4 量化。"

## Weight Conversion

原始权重为 Hybrid FP8-MXFP4（HuggingFace 发布），经 `models/deepseek-v4/utils/convert_model.py` 转换：

- Int8：`--quant_type w8a8-int`
- Hybrid INT8-INT4：`--quant_type w4a8-int --quant_param_path <量化参数文件夹>`（`quant_param_path` 仅 Pro 的 Hybrid INT8-INT4 需要，源 README）

> 代码核对：`convert_model.py` argparse `choices=["w8a8-int", "w4a8-int", "bfloat16", "w4a8-mx"]`（L442）；其 assert 列表（L290）与 docstring（L274）另列了 `w8a8-mx`，但 argparse choices 未含——`w8a8-mx` 仅出现在文档/断言而非可用命令行参数（doc≠runnable flag，待验证）。

## Applicable Scenarios

- **Atlas A3 Pod，Flash 规格**：Int8（W8A8C16）为推荐档；64 卡 DP+EP，8192 序列 Decode 单卡吞吐可达 4388 TPS@30ms（见 Known Results）。
- **Atlas A3 Pod，Pro 规格**：Hybrid INT8-INT4 为推荐档，缓解 1.6T MoE 的访存墙。
- KV C16 适合对 KV 精度敏感、HBM 容量充裕、或不接受 C8 伪量化误差的部署。

## Constraints

- **KV Cache 不量化（C16/BF16）**：相比 950 平台 MXFP8-MXFP4 路径的 C8 伪量化（超长序列省 2× KV），A3 Int8 档不享受该 KV 显存收益；这是平台/方案差异。
- **仅部分 Linear 量化**：MLA/Indexer 其余 Linear、Compressor Linear 均保持原精度。
- **W4A8 校准依赖 quant_param**：Hybrid INT8-INT4 的 Int4 路径需外部量化参数文件夹（见 [w4a8c8](w4a8c8.md) 的 Clamp 学习；V4 W4A8 是否复用 V3.2 同一 Clamp 算法，源未明示，gap）。

## Known Results

Atlas-A3 Pod，64 卡，DP+EP，**W8A8C16**（DeepSeek-V4 Flash，LI Cache Int8 / KV Cache BF16；MTP1，强制 EPLB，源 Benchmark）：

| Global Batch Size | Chips | MTP | DataType | SeqLen | TPOT (ms) | Throughput (Tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 7168 | 64 | 1 | W8A8C16 | 8192 | 27.82 | 4025 |
| 8192 | 64 | 1 | W8A8C16 | 8192 | 29.17 | 4388 |

源未给 Hybrid INT8-INT4（Pro）的独立 Benchmark 数据（gap）。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md)「量化策略 / Atlas-A3 Pod」（Int8 逐模块矩阵 L225-237、Hybrid INT8-INT4 L239-245）+「Benchmark / Atlas-A3 Pod」（W8A8C16 表 L378-385）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/utils/convert_model.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/utils/convert_model.py)（已代码核对：`quant_type` 分支 `w8a8-int`/`w4a8-int`/`w4a8-mx`/`bfloat16`，L289-306、L441-443）、[`models/deepseek-v4/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/README.md)（`--quant_type` 命令与 `quant_param_path` 说明 L117-140）
- 溯源（diff `2f82d10..2c45117`）：`989758d` add w4a8-int for deepseekv4-pro（MR!464）；`9b367c9` / `d4acdde` w4a8int4；`5df82b1` support deepseek v4（MR!366）

## Links

- [deepseek-v4](../models/deepseek_v4.md)
- [w4a8c8](w4a8c8.md)
- [w8a8c8](w8a8c8.md)
- [hybrid-mxfp8-mxfp4](hybrid_mxfp8_mxfp4.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [compressor](../kernels/compressor.md)

<!-- cannbot:related:start -->
## 相关

- [Hybrid FP8-MXFP4 / Hybrid MXFP8-MXFP4 (DeepSeek-V4 Ascend 950PR/DT)](hybrid_mxfp8_mxfp4.md)（`related`）：二者均区别于 Atlas A3 Pod 的整数路径（见 ［int8-int4-hybrid］(int8_int4_hybrid.md)）：A3 走 Int8/W4A8 整数 + KV C16；950 走 FP8/MXFP8 浮点 + KV C8。；DeepSeek-V4 在 ［atlas-a3］(../platforms/atlas_a3.md) Pod 平台上的两档整数量化方案，二者均以原生 Hybrid FP8-MXFP4 权重为转换起点：。两卡共同完成 DeepSeek-V4 从同一原生权重出发、按 950 与 A3 平台选择浮点或整数量化路线的部署决策。
- [W4A8C8 (MoE W4A8 + Attention W8A8C8)](w4a8c8.md)（`related`）：焦点卡写明“A3 Pod 的 Hybrid INT8-INT4 走整数 W4A8 且 **KV 为 C16（非 C8）**”，候选卡写明“仅替换 MoE 路由专家（其余同 Int8 矩阵）”。焦点明确 V3.2 W4A8C8 与 V4 A3 整数 W4A8 的 KV 差异，候选给出 V4 只替换路由专家的具体矩阵。
- [量化权重格式 / dtype 组合的可用性受 SoC 平台与 CANN 算子包版本双重约束（非量化配置 bug）](../../runbooks/precision/quant_format_dtype_platform_cann_version_gating.md)（`related`）：“A3：DeepSeek-V4-Flash → INT8 W8A8（`--quant_type w8a8-int`）；DeepSeek-V4-Pro → Hybrid INT8-INT4（`--quant_type w4a8-int`）。”给出型号到参数的分流；“**Hybrid INT8-INT4（推荐 Pro）**”解释 Pro 分支为何采用 W4A8 路由专家与 W8A8 共享专家。
<!-- cannbot:related:end -->
