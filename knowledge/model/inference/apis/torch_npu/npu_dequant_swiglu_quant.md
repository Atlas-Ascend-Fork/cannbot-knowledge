---
type: API
title: 反量化与 SwiGLU 再量化融合（torch_npu.npu_dequant_swiglu_quant）
description: torch_npu.npu_dequant_swiglu_quant：反量化与 SwiGLU 再量化融合。对张量`x`做dequant反量化+swiglu激活+quant量化操作，同时支持分组。 说明分组 count、激活方向、动态量化和未处理尾部，保留来源输入类型差异。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dequant_swiglu_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dequant_swiglu_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dequant_swiglu_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dequant_swiglu_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantSwigluQuantOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantSwigluQuantOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_swiglu_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_swiglu_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_dequant_swiglu_quant
---


# npu_dequant_swiglu_quant：反量化激活与 count 分组

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_dequant_swiglu_quant(x, *, weight_scale=None, activation_scale=None, bias=None, quant_scale=None, quant_offset=None, group_index=None, activate_left=False, quant_mode=0, dst_type=None, round_mode=None, activate_dim=None, swiglu_mode=0, clamp_limit=7.0, glu_alpha=1.702, glu_bias=1.0) -> (Tensor, Tensor)
```

融合权重/激活反量化、SwiGLU 和再量化，返回 INT8 的 out=(Tokens,H) 与 FP32 scale=(Tokens,)。标准模式 activate_left 默认 False，即激活后半；swiglu_mode=1 使用奇偶切分及 clamp/alpha/bias，相关三个属性仅在该模式生效。

## 参数与组合限制

- x 为二维 ND (Tokens,2H)、尾维为偶数。参数段确认 INT32/BF16；约束段另提 FP16，但未在参数段列出，因此本卡不把 FP16 当作已确认输入组合。
- INT32 输入必须提供 FP32 weight_scale=(G,2H)、activation_scale=(Tokens,1)；BF16 输入的 weight_scale/activation_scale/bias 均须 None。
- group_index 为一维 INT64、非负的每组 token 数，只有 count 语义；总和不得超过 Tokens。分组时仅支持 quant_mode=1，bias/quant_offset 必须 None，H≤10496 且 64 对齐。
- quant_scale 为 (G,H)，FP32/FP16/BF16。group_index 总和之后的 out/scale 尾部未清理，可能含垃圾值或 Inf/NaN，下游必须按有效 token 范围消费。
- group_index 的 count 不等于 npu_dynamic_quant 的累计边界；不要在融合前后直接复用同一列表。

## 验证与模型关联

按反量化、激活方向、平滑、动态量化逐步对比；重点覆盖空组、有效 token 少于预分配容量以及尾部被误消费的反例。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py#L166)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线新模式与完整版本差异

主线中英文新增950PR及DT，输入参数明确补FP16；浮点输入的weight_scale改为可选，activation_scale/bias仍须None。INT32的weight_scale在发布页是必需，主线中文改为建议，英文参数段仍写应提供、约束段又写建议，不把这些文字收敛成所有版本必需或可省略。静态quant_scale主线只允许FP32，不能沿用动态路径的FP16/BF16列表。

swiglu_mode=0按前后两半，activate_left默认False激活后半；1按偶/奇交错，偶支只做上界clamp、奇支双边clamp，再用glu_alpha和标量glu_bias；主线新增2，使用模式1算式但改为前后切分；3先标准Swish再clamp，只用clamp_limit而不用glu_alpha/glu_bias。输入Tensor bias与标量glu_bias不是同一个参数。发布只支持0/1，不回推新模式。

主线新增的公开参数dst_type/round_mode/activate_dim其实在固定发布schema及包装已经存在，发布公开原型却漏了三项并混入C风格float声明；上方接口按实际schema列示。950主线可选择FP8、HiFloat8、FP4；INT8/FP8舍入仅0=rint，HiFloat8仅1=round，其他2/3/4为floor/ceil/trunc，不能将别处的字符串舍入直接传进本参数。

group_index仍是INT64 count，非负、总和≤Tokens，剩余out/scale不清理；H≤10496且64对齐，不把超出有效token的槽用于归约。发布与主线英文都只确认分组动态量化；主线中文删除了同一处限制，其他段仍要求分组时bias/offset无效或为None。本卡保留文字差异，不据删句扩出可用的分组静态量化组合。公开仍二维，C++只检查rank>1不构成更高秩支持。

## 默认参数不保证选择新计算

两固定包装的pre950分支都固定INT8输出、rint、尾轴，用户传入的dst_type/round_mode/activate_dim不会下传；不能据主线总类型名单把FP8/FP4扩到A2/A3该分支。mode=0且缺V2才用旧入口，其他情况会调用V2，包装未给所有缺符号场景提供降级。

950分支在缺V2符号，或三个Optional参数dst_type、round_mode、activate_dim都未赋值时，都会选择旧入口；该入口连swiglu_mode/clamp/glu_alpha/glu_bias也不接收。只改swiglu_mode不能保证变种激活生效，公开mode=1示例省略三项也不是此行为已验证的证据。是否传入显式默认值与是否留None是不同条件。

V2实际先把activate_dim对应轴减半，再在FP4时把物理尾轴再减半，故尾轴激活的FP4输出是输入尾轴的1/4、UINT8承载两个量化值；量化后的逻辑H必须偶数。非尾轴激活只按公开静态且不分组条件使用，scale是激活后形状去尾轴，不套固定(Tokens,H)简写。

两个固定Meta及GE Converter总是按请求的类型/轴描述结果，不复现上述SoC/Optional选择；图Converter用GE DequantSwigluQuant并对FP4重打包，其名称不是ACLNN版本门槛。C++还无条件检查clamp为有限正数、glu_alpha/glu_bias有限，不从“仅某模式生效”推断其他模式可以传NaN。未执行算子或设备实验。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 反量化与 SwiGLU 再量化融合：torch_npu.npu_dequant_swiglu_quant

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

对张量`x`做dequant反量化+swiglu激活+quant量化操作，同时支持分组。

### 文档签名

```text
torch_npu.npu_dequant_swiglu_quant(x, *, weight_scale=None, activation_scale=None, bias=None, quant_scale=None, quant_offset=None, group_index=None, activate_left=False, quant_mode=0, swiglu_mode=0, clamp_limit=7.0, float glu_alpha=1.702, float glu_bias=1.0) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dequant_swiglu_quant.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dequant_swiglu_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dequant_swiglu_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dequant_swiglu_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantSwigluQuantOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantSwigluQuantOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_swiglu_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_swiglu_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
