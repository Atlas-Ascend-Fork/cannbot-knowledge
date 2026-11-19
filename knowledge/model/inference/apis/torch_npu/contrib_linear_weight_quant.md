---
type: API
title: LinearWeightQuant：反量化布局、分组与INT64特例
description: 保存权重量化包装的形状/转置、dtype耦合和仅图NZ限制，区分真实初始化与描述。
tags:
- task.lookup
- topic.compilation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearWeightQuant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearWeightQuant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearWeightQuant.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/linear_weight_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/linear_weight_quant.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# LinearWeightQuant：反量化布局、分组与INT64特例

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 构造与状态

`LinearWeightQuant(in_features,out_features,bias=True,device=None,dtype=None,antiquant_offset=False,quant_scale=False,quant_offset=False,antiquant_group_size=0,inner_precise=0)`包装npu_weight_quant_batchmatmul。产品A2训练/推理、A3训练及旧Atlas推理，不由A3训练扩大推理。旧Atlas仅perchannel，不支持group、输出quant_scale/offset。

两固定实现还接文档未列的weight_dtype=None；device用于empty分配，dtype未消费，参数均requires_grad=False且未填有效量化值。weight在forward末两维转置，二维antiquant_scale/offset也转置；不能把文档(N,K)/(N,groups)存储直接当底层最终布局。

## 输入与耦合条件

x为二维ND(M,K)，A2/A3可FP16/BF16，旧Atlas只FP16；weight二维(N,K)可ND/NZ且可非连续，A2/A3为INT8或INT32承载INT4，旧Atlas只INT8。K、N为[1,65535]，x非转置时M≤2^31−1，转置时M≤65535，均非空。

antiquant_scale/offset为ND，可一维1/N或二维(N,1)，pergroup为(N,ceil_div(K,group_size))，二者shape一致。scale FP16/BF16需与x一致，offset相同；旧Atlas只FP16。A2/A3特殊INT64 scale要求x为非转置FP16、weight为转置INT8/ND，仅perchannel，M在[1,96]且K/N64对齐；对应offset可INT32，不能移植到其他dtype/NZ/group组合。

quant_scale为FP32或预转INT64，quant_offset FP32，形状1/N或(1,N)，两者shape一致且offset不能独立存在。只在weight ND支持，antiquant_scale INT64时两者必须空。bias FP16或FP32同类形状，x BF16时bias FP32，x FP16时bias FP16。输出有quant_scale则INT8，否则与x同dtype。

## 分组、NZ和高性能模式

group_size默认0，非零范围[32,K−1]且32倍数。NZ weight仅图模式，不支持单算子调用；INT32/NZ perchannel需weight转置，pergroup需x转置、weight非转置、group=64/128、K按group对齐且N64对齐。

inner_precise默认0高精度，1可能损精度，只推荐INT32/NZ、pergroup且M≤16场景，不按名称推广。旧示例torch.randn(dtype=INT8)在主线修为randint；数值校准、打包与转换仍由调用方提供，不能把随机整数例当正确量化模型。

- [底层权重量化矩阵乘](npu_weight_quant_batchmatmul.md)
- [TorchAir选定权重转换](../torchair/use_internal_format_weight.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearWeightQuant.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearWeightQuant.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearWeightQuant.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/linear_weight_quant.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/linear_weight_quant.py)（implementation）
