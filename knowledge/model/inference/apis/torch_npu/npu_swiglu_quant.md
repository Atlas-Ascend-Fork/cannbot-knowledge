---
type: API
title: SwiGLU 后动态或静态分组量化（torch_npu.npu_swiglu_quant）
description: torch_npu.npu_swiglu_quant：SwiGLU 后动态或静态分组量化。在swiglu激活函数后添加quant操作，执行输入`x`的`SwiGluQuant`计算，支持`int8`或`int4`量化输出，支持MoE场景和非MoE场景（`group_index`为空），支持分组量化，支持动态/静态量化。 区分 cumsum/count、量化模式与分组 scale，说明尾轴限制和 INT4 输出选择。
tags:
- task.lookup
- topic.activation
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_swiglu_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_swiglu_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_swiglu_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_swiglu_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SwigluquantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluquantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T03:38:50Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_swiglu_quant
---


# npu_swiglu_quant：激活方向、分组与静动态量化

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口产品页及同提交 Schema，仅描述下列产品和参数路径，不回推到发布快照。文档支持、来源配套和设备验证分别核对。

## 接口

```text
npu_swiglu_quant(x, *, smooth_scales=None, offsets=None, group_index=None,
    activate_left=False, quant_mode=0, group_list_type=0, dst_type=None)
    -> (out, scale)
```

先将尾轴对半做SwiGLU，再按group选smooth scale，最后静态或动态量化。activate_left默认False激活右半；group_list_type=0是累计边界，1是各组token数；group_index=None是非MoE路径，不与其他接口固定count约定混用。

x为ND、FP16/BF16/FP32，可非连续，rank>1，尾轴为正偶数且≤8192。量化INT4时x尾轴为4的倍数。令N=x尾轴/2、G为分组数，smooth_scales为FP32、shape=(G,N)或(G,)；静态offset与它同shape/dtype，动态offset不生效，传None。

group_index为一维INT32、shape=(G,)，来源要求非递减且最大值不超过前置维度乘积。由于count模式与累计边界语义不同，不能自行取消文档限制或拿一组数直接切换模式；按准确版本核对并验证分组覆盖。

quant_mode=0默认静态、1动态；dst_type默认None即INT8，可选torch_npu.int4。out是量化结果；scale为FP32，shape是x去掉最后一维。接口页未在这里给静态scale输出有效性的额外约定，不把它推成动态校准scale。两固定C++明确INT4由INT8容器每元素承载两个值，物理尾维为原输入的1/4，和其他量化API的INT32打包不同。

- [反量化后SwiGLU是另一接口](npu_dequant_swiglu_quant.md)


## 核验

按同一计算顺序、激活模式和量化参数建立参考，检查输出数量、dtype、shape与别名；训练或其他模式须另有来源支持，不由本卡的通用核验步骤推定。再比较正常负载的稳态时间和内存。本次未执行算子、图编译或设备性能测试。

## 完整版本、INT4实际容器与Meta差异

发布中文确认A2/A3，主线中英文新增950DT，没有确认950PR；元数据的950家族仍只按这一产品形态使用。公开将[2,4,6]写作group_index的shape，这是示例的三个边界值，实际shape为(3,)；count例为[2,2,2]。计数模式不能仅检查每项最大值就代替完整覆盖范围，包装没有读取group_index内容来保证分组合法。

两个固定C++的ScalarType检查只接受INT8或quint4x2，None按INT8；主线公开改写为torch_npu.int4不等于局部包装已经证明任意自定义整数别名可用，应按准确绑定核对。两版物理输出总是INT8容器：普通INT8量化在SwiGLU后尾维为原来的1/2；INT4再将两个值打包进一个INT8，物理尾维为原来的1/4。它既不是其他动态量化的八值INT32，也不是FP4的UINT8逻辑类型。

两版Meta却始终按原尾维的1/2分配、dtype直接采用传入值，未复现INT4额外打包形状或N被4整除检查；不能由Meta证明图路径和Eager物理结果一致。静态scale/offset须同shape，动态offset不生效；源码分配FP32前缀scale不构成静态槽有效数值的额外保证。

固定两个GE Converter树中未找到注册本入口的转换器，本文不据相邻SwiGLU MX接口补出图模式，也不把局部搜索当全部后端运行时结论。公开只列rank>1、尾轴偶数且≤8192、INT4额外被4整除；不从通用验证模板推定支持训练、任意空Tensor或所有模型。

## 已有 OpPlugin 7.3.0 文档与版本边界

### SwiGLU 后动态或静态分组量化：torch_npu.npu_swiglu_quant

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

在swiglu激活函数后添加quant操作，执行输入`x`的`SwiGluQuant`计算，支持`int8`或`int4`量化输出，支持MoE场景和非MoE场景（`group_index`为空），支持分组量化，支持动态/静态量化。

### 文档签名

```text
torch_npu.npu_swiglu_quant(x, *, smooth_scales=None, offsets=None, group_index=None, activate_left=False, quant_mode=0, group_list_type=0, dst_type=None) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_swiglu_quant.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_swiglu_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_swiglu_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_swiglu_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SwigluquantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluquantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
