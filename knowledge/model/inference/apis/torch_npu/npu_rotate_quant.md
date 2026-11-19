---
type: API
title: npu_rotate_quant：旋转量化的产品矩阵与物理打包
description: 区分A2/A3整数量化与950 MX类型、图模式和块旋转，明确默认INT8不能直接用于950。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rotate_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RotateQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rotate_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/rotate_quant.py
  role: implementation
created_at: '2026-11-09T06:53:58Z'
updated_at: '2026-11-09T22:23:06Z'
platforms:
- a2
- a3
- '950'
---

# npu_rotate_quant：旋转量化的产品矩阵与物理打包

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品分支与同提交包装/Meta，未运行上游算子或设备实验。新参数和产品支持不回推发布基线。

## 接口

```text
npu_rotate_quant(x, rotation, *, alpha=None, dst_dtype=None,
    axis=-1, round_mode='rint', scale_alg=0,
    dst_type_max=0.0, transpose_y=False) -> (y, scale)
```

融合旋转与量化，x/rotation同为FP16或BF16、ND，可非连续；x末轴须被旋转块K整除。transpose_y只False。axis包装虽检查一般范围，产品页只支持末轴，不能用包装的宽检查推定任意轴受支持。

|分支|A2/A3|950|
|--|--|--|
|x形状|二维，末维128..16000且8整除|rank1..7，FP4末维为偶数|
|rotation|二维(K,K)，K=16..1024|二维(K,K)或(block_num,K,K)，K=32/64/128，block_num=x末维/K|
|目标类型|INT8或INT4/quint4x2|MX FP8 E4M3FN/E5M2或FP4 E2M1|
|alpha|仅None|有效范围(0,1)，None/范围外不处理|
|scale_alg|仅0|FP8为0/1，FP4为0/2|
|图模式|产品页确认支持|产品页明确不支持|

文档总参数段写rotation二维，但950专节明确允许三维，应按目标产品专节使用。Schema省略dst_dtype或显式None均在包装落为INT8；950产品专节不支持此目标类型，**950必须显式选择相应MX类型**，不能直接套默认调用。

## 数据容器与尺度

INT8输出同x形状，scale为FP32(x.size(0),)。INT4八值打包为INT32、末轴/8；FP4两值打包为UINT8、末轴/2。两者物理布局不同，不能按“都是4位”互换容器或尺度。

MX尺度逻辑E8M0，按每32值分组，末尾追加配对维2，量化轴维度改成ceil(ceil(N/32)/2)，其余轴沿用x；普通整数scale是per-token FP32，不是该MX格式。

FP8仅rint；FP4可rint/round/floor。950算法2的dst_type_max按专节为[6,12]，其他场景仅0；不把统一默认0推定为该特定算法已确认的有效幅度设置。

## 验证

先检查目标分支、旋转权重排列和尺度粒度，再对照旋转后独立量化；覆盖块边界、打包/解包与尾尺度pad。融合性能收益需在相同数学结果与实际产品上测量。

## 公开图范围与转换器实际默认值

中英文均明确950PR及DT不支持图模式，只有A2/A3确认图模式；主线存在Converter不推翻产品限制。rotation总参数写二维，950专节允许(block_num,K,K)，应按专节；alpha本身是一维Tensor，不能把其(0,1)值范围误写为可直接传Python float。

固定主线Converter位于custom/rotate_quant.py，直接默认dst_dtype=0，与公开及C++的None→INT8不同；它未归一化None，调用图路径应明确指定A2/A3允许的目标类型并核对映射。直接默认0不能成为UINT8公开输出支持，声明样例也不是运行验证。

图转换器仅对quint4x2做逻辑INT4到物理INT32的八值打包；不能据有GE RotateQuant就把950的FP4容器或图支持补上。Meta对MX尺度使用逻辑E8M0类型表示，C++按对应容器分配；布局、类型注册和具体后端分别核对，不将Meta推导作为设备结果。

transpose_y=True在包装和Meta都明确拒绝；axis虽做一般范围检查，公开只给末轴及其等价正索引，不扩大成任意量化轴。950算法2的[6,12]幅度条件与默认0不能相互替代，其他参数组合、块旋转K及输入长度仍按上文产品矩阵。固定发布没有该声明或包装，缺文件不作为全部安装版本的结论。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rotate_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RotateQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rotate_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/rotate_quant.py)（implementation）
