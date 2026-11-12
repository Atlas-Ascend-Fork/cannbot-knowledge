---
type: Concept
title: LI 量化模式配置：GLM li_cache_quant_mode 与 V3.2 字段差异
description: LI 模式配置的静态契约：GLM li_cache_quant_mode、950 float8 条件、scale cache dtype 与 V3.2 kv_cache_quant_mode 的区别；不代表产品部署已验证。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-structure-cards.md
  role: supporting
created_at: '2026-11-10T03:39:02Z'
updated_at: '2026-11-10T03:54:53Z'
platforms:
- agnostic
aliases:
- li_cache_quant_mode
- past_key_scales_indexer
- GLM LI 950 float8
- LI 模式选择
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# LI 量化模式配置：GLM 与 V3.2 的字段和静态分支

## 契约范围

本文描述固定 Recipes 的 Python 配置赋值与缓存元数据，适用性不依赖运行该分支的物理 NPU。`platforms: agnostic` 仅对应这项配置契约；表中的950条件不证明目标设备、算子或完整模型已经通过部署验证。A3 的实际 LI 接线见 [LI 量化与 CP](../../guides/integration/lightning_indexer_quantization_scale_cache.md)。

GLM 的 `ForCausalLM.update_kv_quant_settings` 在存在 `quant_config` 时写入 `li_cache_quant_mode`，建模和 Indexer 再读取；不将它当作与权重产物无关的独立 YAML 开关。无 `quant_config` 时设置函数提前返回，读取端按未量化路径处理。

## 模式选择

| 模式路径 | Indexer 模式 | Q/K 量化入口 | scale 与读取分支 |
| --- | --- | --- | --- |
| glm_no_quant_config | unquant | none | npu_lightning_indexer |
| glm_a3_quant_config | int8 | npu_dynamic_quant | FP16 scale，npu_quant_lightning_indexer |
| glm_950_float_mm | float8 | npu_dynamic_block_quant | FP32 scale cache，npu_quant_lightning_indexer |
| v32_int8_cache | int8 | npu_dynamic_quant | query_dequant_scale / key_dequant_scale，INT8 LI 分支 |

有量化配置时 GLM 先将 LI 模式初始化为 `unquant`，随后按 `platform_version == "950" and "float" in mm_quant_mode` 选择 `float8`，其余选择 `int8`。950条件包含对 mm 模式串的判断，不能只凭设备名断言启用 FP8。

V3.2-Exp 的 Indexer 读取 `kv_cache_quant_mode`。不能把 GLM 的 `li_cache_quant_mode` 机械移植过去，也不能由普通 MLA KV 的 dtype 推导 GLM LI 模式。量化对象、模式字符串和实际调用要分别核对。

## 缓存与量化状态的配对

`indexer_key_cache` 与 `indexer_key_scale_cache` 保存 key 和相应量化 scale；旧材料中的 `past_key_scales_indexer` 是配套 scale 状态的历史名称。GLM `get_cache_info` 由 LI 模式选择 key dtype，int8 的 scale 元数据为 FP16，float8 的 scale 元数据为 FP32。它描述分配契约，不证明相关内核在任意产品均可调用。

模式更改必须与原始 checkpoint、key/scale 的编码、缓存声明及图缓存保持一致。只改变字符串不构成有效的量化转换；保留未量化分支作对照。CP 的全序恢复、prev/next scale 和持久槽位属于模型实现，按 [A3 接线指南](../../guides/integration/lightning_indexer_quantization_scale_cache.md) 与固定源码核对，不由本配置表承诺跨平台支持。


## Evidence

- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py)（primary）
- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（supporting）
- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-structure-cards.md)（supporting）
