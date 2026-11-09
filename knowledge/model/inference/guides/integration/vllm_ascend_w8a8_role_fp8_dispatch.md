---
type: Guide
title: vLLM Ascend W8A8分派：PDMix的KV角色与动态FP8的bias和输出
description: 新模型接入W8A8_MIX或W8A8FP8_DYNAMIC时，区分构造时KV consumer角色与batch phase，核对PreparedLinearInput、静态参数规格、E4M3/FP32
  scale、FP8 bias补加、ND融合kernel和MoE输出dtype，保留weight switch与EPLB门禁。
tags:
- task.implementation
- task.debugging
- topic.precision
- topic.model_adaptation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/w8a8_pdmix.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/w8a8fp8_dynamic.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w8a8/test_w8a8_pdmix.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w8a8/test_w8a8fp8_dynamic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/w8a8_dynamic.py
  role: constraint
created_at: '2026-11-03T01:22:02Z'
updated_at: '2026-11-03T01:22:02Z'
platforms: []
aliases:
- W8A8_MIX
- W8A8FP8_DYNAMIC
- AscendW8A8PDMixLinearMethod
- AscendW8A8FP8DynamicLinearMethod
- AscendW8A8FP8DynamicFusedMoEMethod
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend W8A8分派：PDMix的KV角色与动态FP8的bias和输出

## 先区分部署角色、数据类型与层类型

固定Ascend `ceac1a2b`。`W8A8_MIX`在所读文件注册Linear组合器，`W8A8FP8_DYNAMIC`分别注册Linear和MoE；同样含W8A8的名字不意味着相同激活dtype、checkpoint参数、融合kernel或输出。family init通过实际导入触发这些类的注册，不把单个decorator或__all__名字当作运行支持证明。

通用namespace、参数分片与scheme生命周期见[ModelSlim适配](vllm_ascend_modelslim_scheme_adaptation.md)，跨流输入见[PreparedLinearInput接入](vllm_ascend_prepared_linear_overlap.md)。本卡不扩展整项硬件范围，保持draft/空平台；静态/动态或FP8名称不构成任何模型精度、吞吐保证。

## PDMix按KV consumer角色分派

构造器创建静态和动态两个method，从当时的kv_transfer_config保存 `_is_kv_consumer`。权重、per-tensor与per-channel参数规格统一委托静态method；post-load也先走静态处理，再生成weight_scale_fp32缓存，并把角色写入 `layer.is_kv_consumer`。

prepare_input_for_overlap和apply都按layer上的该角色选择同一个method：consumer用静态，非consumer用动态。文件说明以Prefill/Decode概述，但这里没有按每个batch的has_prefill重新判断。P/D共部署、没有KV transfer配置时角色为False；不能仅因正在decode就宣称已经切到静态，也不能让consumer临时处理prefill时凭token数绕过其静态参数。

若实例或配置被复用于不同部署角色，必须核对重构/post-load和layer标记，不能假定修改外部config会自动刷新已构造scheme。prepare与apply角色应一致，否则缓存的量化输入与实际method可能不匹配。

| 接入检查 | 要保存的实际证据 |
| --- | --- |
| 参数创建 | 采用静态method返回的全部参数，不只保存dynamic所需weight/scale |
| post-load | 静态转换已完成、weight_scale_fp32已建立、layer.is_kv_consumer已写入 |
| overlap | PreparedLinearInput对应的真实quant dtype、scale和output_dtype，以及prepare时角色 |
| apply | 当前layer角色、实际静态/动态method、bias和TP参数 |

UT通过mock验证三种参数委托、两种apply分支和role写回；并未证明所有P/D拓扑、量化权重或运行时角色切换已经正确。

## FP8 Linear：E4M3与额外bias只处理一次

`AscendW8A8FP8DynamicLinearMethod` 继承动态Linear，但weight与激活dtype为float8_e4m3fn，per-channel weight_scale固定FP32，weight_offset采用params_dtype。Linear post-load沿父类转置并flatten参数；只有INT8激活类型才调用父类NZ转换，FP8不照搬该INT8分支。

父类支持普通tensor或PreparedLinearInput。后者直接消费其quantized、scale和output_dtype，缺scale会断言；普通tensor再动态量化。若pertoken_scale为二维，路径会squeeze相应维度，输出再unsqueeze恢复；不能为了匹配matmul临时永久改掉模型输入rank。

父类仅INT8时将bias传入npu_quant_matmul，FP8时传None；FP8子类在matmul后补加非None bias并cast回原输入dtype或PreparedLinearInput.output_dtype。这是当前封装处理FP8 bias问题的路线，不能在外层再加一次bias，也不能因父类有bias形参就认为FP8 kernel已经消费它。

`supports_weight_switch=False` 明确关闭此FP8 Linear的通用权重切换能力。父类INT8支持的gather specs、CP投影或reload行为不能只靠继承关系推给该子类。

## FP8 MoE：scale的dtype不是输出dtype

MoE分配w13 `[E,2I,H]`、w2 `[E,H,I]` 的E4M3权重，scale分别 `[E,2I,1]`、`[E,H,1]` 且为FP32；offset为params_dtype。子类QuantType为W8A8FP，父类post-load转置并整理这些参数，只对QuantType.W8A8执行原INT8 NZ转换，因此FP8权重保留ND路线。

父类还可能按真实EPLB配置建立每专家clone列表，并删除原stacked参数，或建立MegaMoe views；实际消费者通过_get_mlp_weights选择活动weights/scales。新模型不能只修改原layer.w13_weight而让计算仍读clone列表，或从普通列表存在推导任意EPLB/MC2/Mega组合都已支持。

FP8的GMM2明确设置 `output_dtype=self.in_dtype`，来源为模型dtype；若像INT8父分支那样从FP32 scale推导，可能将FP32 MoE输出传给后续要求同dtype的residual/norm。该输出合同与scale容器精度不同，二者必须分别验证。

## ND融合与非融合门禁

fusion启用、非dynamic_eplb且激活不是SWIGLUOAI_UNINTERLEAVE时，FP8子类使用支持FP8 ND权重的 `npu_grouped_matmul_swiglu_quant_v2`，而不是INT8 weight-NZ融合kernel。它先准备真实FP8 hidden_states/pertoken_scale，使用活动w1与scale，将group_list按helper转累计边界，设置quant_dtype为E4M3、dequant_dtype为FP32，随后dispose原MLP输入。

其余条件回到父类路径。此处对OAI等条件的分支不证明任意其他activation均可融合；完整选择还需满足实际MoE调度门禁。不能把fused入口输出精度参数与最终GMM2输出dtype混为一谈，也不能在dispose后继续让另一consumer使用原输入存储。

## 新模型与性能Agent验收

先记录真实scheme类/注册key、KV角色、Linear/MoE层类型及checkpoint dtype；再保存post-load的布局、scale/offset、活动expert view与PreparedLinearInput生命周期。分别对无bias/有bias、普通/overlap输入、INT8/FP8、融合/回退路径检查输出dtype和数值，确认bias只应用一次。

在正确性基线成立后，固定权重、校准、batch、序列与TP/EP测P/D两侧端到端指标，并分别记录量化、通信和调度成本。不能由“动态”“FP8”或“MIX”名字自动选择更快方案。两份专项UT以分配、mock调用及dispatch参数为主，本次未运行UT、真实kernel、NPU、精度或性能实验，未生成verified事件。
