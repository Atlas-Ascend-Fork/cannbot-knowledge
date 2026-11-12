---
type: Guide
title: Lightning Indexer 量化接入：GLM/V3.2 的 LI cache、scale 与 CP 重排
description: GLM li_cache_quant_mode 与 V3.2 kv_cache_quant_mode 的独立 LI 量化闭环：Hadamard、indexer_key_scale_cache、CP
  gather/restore 和 prev/next scale 对齐。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-structure-cards.md
  role: supporting
created_at: '2026-11-10T01:14:54Z'
updated_at: '2026-11-10T03:40:06Z'
platforms:
- a3
aliases:
- LI cache 量化
- li_cache_quant_mode
- past_key_scales_indexer
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# Lightning Indexer 量化接入：GLM/V3.2 模式、scale cache 与 CP 重排

## 适用范围与配置来源

本文解释固定 Recipes 的 GLM-5 / V3.2-Exp 在 Atlas A3 的实际 LI 量化接线。配置字段赋值、950条件分支和 scale cache dtype 的规范定义见 [LI 模式配置契约](../../concepts/quantization/li_cache_quantization_mode_contract.md)。该契约描述静态代码，不等同于950部署已验证。

GLM 使用 `li_cache_quant_mode`，V3.2-Exp 读取 `kv_cache_quant_mode`。LI cache 与普通 MLA KVCache 是不同闭环，不能由权重模式或 KV dtype 单独判断 LI 已量化。A3 接线重点核对 unquant/int8 的实际调用与缓存；其他产品和 FP8 必须按目标环境另验。

## Q/K 与 scale 同步流动

按模型的 RoPE 定义先旋转，再做 Hadamard 和量化；Hadamard 的数值目的与融合权重 scale FP32 契约见[低比特精度规则](../../optimizations/rules/precision_lightning_indexer_low_bit_quant.md)。INT8 与 FP8 的量化入口、scale dtype 需分别核对，不将普通权重 weight_scale 与每 token 的 query/key dequant scale 混用。

当前接口用 `indexer_key_cache` 和 `indexer_key_scale_cache` 保存 key 与对应 scale；旧参考名 `past_key_scales_indexer` 指向同一类配套状态，不是可忽略的附加日志。缓存读写要保持 token/slot 的一一对应，常驻缓存与 CP 计算临时缓存不能串用。固定实现当前都通过 npu_scatter_nd_update_ 写入相关槽位，旧“Prefill scatter、Decode indexed”描述应以实际调用为准。

## CP Prefill 的 scale 与布局

CP 开启时，key_dequant_scale 先在 cp_group 上 all_gather_into_tensor，再按 cp_metadata.restore_indices 恢复全局 token 顺序；不能只 gather key 而漏掉 scale。Query scale 按 local_prev_token_num / local_next_token_num 切成 prev/next 两段，与两次 LI 的 q、weights、有效长度保持一致。

scale 有两套存储职责：persistent_slot_mapping / persistent_valid_indices 写本 rank 持久缓存，global_slot_mapping 配合临时 compute_key_scales 供本轮全局计算。对应 key cache 也必须采用同一顺序和块表。不能把“两个 tensor shape 相同”当作 token/scale 已对齐。

GLM 量化 LI 调用传 key_dequant_scale、query_dequant_scale、key_quant_mode=0、query_quant_mode=0；INT8 时 weights 转 float16，float8 分支保留原 weights 类型。这里的 mode=0 是此算子反量化编码，不等同于 FIA sparse_mode 或其他量化算子的 mode。

## 验证与回退

分别覆盖无量化/INT8、Prefill/Decode、CP开关和不等长请求。检查实际 LI 内核、Q/K dtype、scale cache 的槽位及 prev/next 顺序，以浮点参考的 TopK/下游 attention 和任务输出验收。FP8、950和融合路径需按其目标环境另验；本文没有执行 NPU 测试。

模式、缓存和编译图应一起回退到原基线，不能只关 LI 内核却保留量化缓存，也不能靠更改 targets/ignore 来掩盖不匹配。


## Evidence

- [models/glm_5/models/indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py)
- [models/glm_5/models/modeling_glm.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py)
- [models/deepseek_v3_2_exp/models/indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)
- [models/glm_5/README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/README.md)
- [models/deepseek_v3_2_exp/README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/README.md)
- [.agents/skills/model-infer-quantization/references/quantization-structure-cards.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-structure-cards.md)
