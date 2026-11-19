---
type: API
title: npu_gelu_quant：静动态量化与 FP8 舍入模式
description: 说明 950 的 GELU 后量化、动态 scale 形状和 hifloat8 不能沿用默认 rint。
tags:
- task.lookup
- topic.activation
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gelu_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gelu_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GeluQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T06:17:11Z'
updated_at: '2026-11-09T22:23:06Z'
platforms:
- '950'
---

# npu_gelu_quant：静动态量化与 FP8 舍入模式

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口产品页及同提交 Schema，仅描述下列产品和参数路径，不回推到发布快照。文档支持、来源配套和设备验证分别核对。

## 接口与输入

```text
npu_gelu_quant(self, *, input_scale=None, input_offset=None,
    approximate='none', quant_mode='dynamic', dst_type=None,
    round_mode='rint') -> (y, out_scale)
```

self为ND、FP16/BF16/FP32，可非连续、不支持空；动态量化rank2..8，静态rank1..8。GELU可选none/tanh，默认none。静态计算激活*input_scale+input_offset，input_scale必填；动态先可选平滑，再按每行绝对最大值产生out_scale并量化，默认dynamic。

input_scale为一维、长度1或尾轴D，与self同dtype或更高精度；offset同scale的shape/dtype，动态且scale=None时offset也必须None。不要把静态输入scale与动态返回scale互换。

## 输出与舍入

dst_type默认None即INT8；可选float8_e4m3fn、float8_e5m2、hifloat8。各自动态maxValue为127、448、57344、32768。INT8/E4M3FN/E5M2仅支持rint；hifloat8必须显式round或hybrid，默认rint不合法。

y形状同self；hifloat8以UINT8容器承载，不是普通UINT8量化。动态out_scale为FP32、shape去掉末维；静态没有有效尺度，文档称空Tensor而Meta返回None、C++未显式分配，不能要求统一的可读Tensor对象。只选择产品页列明的950推理范围；文档列单算子与图模式调用。


## 核验

按同一计算顺序、激活模式和量化参数建立参考，检查输出数量、dtype、shape与别名；本接口只按公开推理范围核对，不据模板增加训练支持。再比较正常负载的稳态时间和内存。本次未执行算子、图编译或设备性能测试。

## 完整双语与默认None的Meta冲突

主线中英文仅950PR及DT的推理、单算子及图模式。GELU的none是erf形式，tanh使用含0.044715*x³的近似；激活在静态乘scale加offset或动态平滑、逐行量化之前，不能把输入scale提到GELU之前合并。动态目标最大值按INT8/E4M3FN/E5M2/HiFloat8分别为127/448/57344/32768，不把所有FP8写成448。

两固定包装在dst_type=None时按INT8；两个固定TorchAir Converter也如此，但两个Meta却在dst_type为None时直接抛错，尽管函数自身默认写1、schema默认却是None。不能用公开默认图示例证明此组合已经成图；显式dst_type=1可使这一项与Meta契约一致，仍需核对其他形状、类型和运行库条件。

静态out_scale还有对象差异：文档称空Tensor，两个Meta直接返回None；两个C++静态分支没有显式分配out_scale，而将未定义Tensor槽传入底层并返回。本文不把这些统一写成可调用numel()的已验证空Tensor，也不消费其数值。动态才明确分配FP32前缀尺度。

两个Converter校验静态必填scale、动态无scale时不可单独offset、动态至少二维，以及目标类型×舍入表；HiFloat8必须round或hybrid，默认rint无效。包装/Meta未复现全部检查不解除公开限制，字段存在也不证明全部非连续、极值或符号形状已经验证。固定发布已有声明、Meta、包装和Converter却没有同名公开页，不据代码补出发布产品支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gelu_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gelu_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GeluQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
