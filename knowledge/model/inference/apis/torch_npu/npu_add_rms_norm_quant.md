---
type: API
title: npu_add_rms_norm_quant：静态双量化与 axis 限定
description: 说明每产品 dtype 组合、scale乘除方向与仅单算子调用，并保留非默认 axis 的 Meta 差异。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddRmsNormQuantKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormQuantKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:25:22Z'
updated_at: '2026-11-09T22:10:09Z'
platforms:
- a2
- a3
- '950'
---

# npu_add_rms_norm_quant：静态双量化与 axis 限定

## 版本和支持范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，按产品表和具体参数分支使用，不回推发布基线，不从单页类型名单推导任意混合组合。未执行上游代码、设备算子或图编译。

## 接口

```text
npu_add_rms_norm_quant(x1, x2, gamma, scales1, zero_points1,
    beta=None, scales2=None, zero_points2=None, *, axis=-1,
    epsilon=1e-6, div_mode=True, dst_type=None) -> (y1, y2, x)
```

先Add、RMSNorm与可选beta，再按静态scales/zero_points量化。div_mode=True为除scale再加zero point，scale不能为0；False为乘scale。x是相加残差、同x1 shape/dtype。第二量化分支的缺省槽不凭Meta分配了同shape就认定含有效结果。

x1为1..8维ND，可非连续，x2同shape/dtype；gamma匹配norm尾维，beta同gamma。两路scale及zero point的shape与gamma一致，第二路类型分别同第一路；所有维≤INT32_MAX。zero_points1文档称可选，但Schema是允许None却无省略默认值，调用位置仍需明确提供。

|产品|确认的dtype组合|
|--|--|
|A2/A3|x为FP16时scale为FP32、zero point为INT32；x为BF16时scale/zero point为BF16。输出INT8。|
|950|支持FP32全浮点组合；低精度x可配同dtype scale/zero point，或FP32 scale配INT32/FP32 zero point。输出还可选FP8或hifloat8。|

不能把参数列表的dtype做笛卡尔积，也不将本接口的静态scale当作动态返回scale。

## 模式与文档差异

仅单算子模式。axis只采用-1：文档称其他值不生效，但同提交Meta显式检查axis==-1并拒绝其他值，不能按“忽略”生成可用配置。默认epsilon=1e-6，dst_type=None按INT8。A2/A3对Inf/NaN的特殊说明不扩展为950所有低精度输出的统一行为。


## 验证

先核对计算顺序、分组语义、scale方向与真实存储形状，再比较量化/反量化数值；覆盖空组、尾块、非连续和打包解码的实际需要。分别测内存与稳态收益，本文只有静态证据。

## 完整产品矩阵与运行库选择

发布中文仅A2/A3及旧Atlas推理，主线中英文新增950PR及DT；950的FP32输入和新输出类型不回推发布。950完整组合按行核对：FP32的x/gamma/scale/zero point均FP32；FP16或BF16的x/gamma可配同dtype scale及同dtype zero point，或FP32 scale配INT32/FP32 zero point。两路scale各自同类型、两路zero point各自同类型，beta若存在同gamma。950组合表未单列beta，不据缺列扩大beta类型。

旧Atlas推理仅FP16输入、FP32 scale、INT32 zero point，且输入末轴及各参数至少32个元素；这里是元素数，不能混作旧RMSNormQuant的32 Bytes条件。输入不许Inf/NaN；A2/A3“输出Inf/NaN”文字未清楚区分INT8量化输出与残差x，不据此断言整数能承载这些值。所有维度仍不大于INT32_MAX，主线只支持单算子。

两固定C++均明确拒绝axis!=-1，公开“其他轴不生效”不能作为可接受的配置。两版总是分配完整y1/y2，无第二路参数时y2也不能仅凭形状认作有效结果；输出残差独立分配，未做输入原地写回。

发布包装只有pre950且存在aclnnAddRmsNormQuantV2时走V2；其他路径要求beta/scales2/zero_points2都无值、div_mode=True。主线改为pre950或提供beta时、并有V2符号才走V2；950无beta则直接用旧入口且不做上述第二路/乘法限制，其余降级分支仍拒绝这些参数。错误信息建议CANN8.3或以上是该分支提示，不当成所有产品及新dtype的完整最低版本保证。两固定版本不能只按函数名判断同一行为。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddRmsNormQuantKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormQuantKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
