---
type: Guide
title: vLLM Ascend compressed-tensors：逐层格式匹配与 scheme 分派
description: 从config_groups、ignore和packed映射推导实际Linear/MoE方案，按位宽、粒度、动态性和MX格式判据区分未匹配回退与不支持报错。
tags:
- task.implementation
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/compressed_tensors_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/configs/test_compressed_tensors_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/registry.py
  role: implementation
created_at: '2026-10-29T11:32:34Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T11:32:34Z'
---

# vLLM Ascend compressed-tensors：逐层格式匹配与 scheme 分派


## 范围与入口

固定ceac1a2b的AscendCompressedTensorsConfig；本文是格式解析/框架分派契约，不证明各scheme的完整硬件或kernel支持。来源没有整项接口的产品范围，保持draft、空平台。部署前先按[权重加载入口](../deployment/vllm_ascend_quantized_checkpoint_loading.md)识别格式，不能仅改quantization参数转换checkpoint。

## 匹配顺序和回退

from_config把config_groups.targets映射到weights、input_activations和组内format；组内format缺省才取全局format。只有activation格式或全局mixed-precision时才保留非空input_activations。相同target在后续group再次出现会覆盖已有条目，应在制备阶段检查重名。

get_scheme_dict先处理ignore（含fused mapping），再通过find_matched_target匹配完整层名、模式或module类型。缺匹配/无scheme/无weight_quant会使Linear/MoE选择浮点方法；已经识别出quant_type但registry缺对应layer_type则抛NotImplementedError。二者不能统一解释为“量化已生效”。

MoE按prefix+'.0.gate_proj'查方案；只有Linear目标且没有RoutedExperts目标时，为RoutedExperts补同一scheme。不能由Linear的一条注册推导每种MoE格式均有实现。apply_vllm_mapper同时映射target keys和ignore列表，验收要核对运行时prefix。

## 当前识别判据

| 分支 | 关键条件 |
| --- | --- |
| W8A8静态 | 权/激活8bit、权channel/激活tensor、均静态且对称，处于activation格式 |
| W8A8动态 | 权channel静态/激活token动态、均8bit且对称；两者type都为FLOAT时改选W8A8FP8_DYNAMIC |
| W4A8动态 | 权4bit channel静态、激活8bit token动态、对称，处于activation格式 |
| W4A16 | 无input_activations，权INT4、group、静态；不能先要求激活量化存在 |
| W8A8_MXFP8 / W4A4_MXFP4 | 分别mxfp8-quantized / mxfp4-pack-quantized；权/激活均FLOAT、对应8/4bit、group_size均严格32、权静态/激活动态、对称 |

MX分支还把group_size=32写入quant_description。上述是配置谓词，不是所有dtype组合的算子支持表；尤其普通8bit判据没有在所有分支显式限制type，不能把“命中字符串”当kernel保证。

本实现的MX判据是format与group参数，不能照搬[其他框架的历史门控诊断](../../runbooks/precision/compressed_tensors_scheme_gating_pitfalls.md)中的weight_block_size=[1,32]判据。也不能用模式名子串替代这些逐字段条件。

## 验收与失败处理

对每类关键层记录最终target、ignore、format、QuantizationArgs、scheme和权重/scale布局，分别覆盖无激活量化、混合格式、未命中和缺registry。源码测试包含静/动态W8A8、W4A8、W4A16、MXFP4/8及mixed-precision激活保留等断言；本次只读这些断言，未运行上游pytest或NPU。

未命中导致浮点展开时重新核对mapper/target；不支持格式应重新制备权重或接入真实scheme，不以伪造配置字段越过门控。数值与显存验收后再报告性能。
