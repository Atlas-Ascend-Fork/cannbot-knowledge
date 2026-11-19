---
type: Guide
title: TorchNPU原生量化Tensor的表示、存储与版本派发
description: 说明原生per-tensor/per-channel的版本分支、整数承载、PrivateUse1回调、元数据与反量化成本。
tags:
- task.optimization
- topic.compute.quantization
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IntReprQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizeTensorKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IntReprQuantKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IntReprQuantKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T07:37:41Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# TorchNPU原生量化Tensor的表示、存储与版本派发

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 与固定发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的原生per-tensor/per-channel量化、反量化和整数表示入口。主线四个OpAPI与四个ACL文件的全部本地定义均已静态读；发布六个同名文件以完整phase2 token、全部注释及有序预处理指令等价复用，不把格式差异当语义变更。未执行量化、ATen、NPU或模型精度实验。

这里的 `quantize_per_tensor/channel` 与自定义 [npu_quantize](../apis/torch_npu/npu_quantize.md) 是不同接口。不要把自定义乘法scale、INT4打包或FP8能力直接移到本卡所述原生量化入口，也不能仅凭传入QInt8枚举推断不同版本都返回相同量化元数据和物理Tensor类型。

## Schema与实际编译分支

两版Schema均为quantize_per_tensor与quantize_per_channel登记acl_op/op_api all_version；本地CPP的版本分支还决定实际实现。q_scale、q_per_channel_scales、q_zero_point、q_per_channel_zero_points、q_per_channel_axis与qscheme均只登记acl_op v2.2，虽然其CPP宏范围更宽，也不能据此提升已登记版本范围。

dequantize.self和int_repr在两版都有acl_op `[v2.2,newest]`；主线另增加同范围op_api登记及对应两个CPP。发布精确OpAPI路径在Git树中不存在，但有既有ACL实现，不能将路径缺失误写成发布版不支持反量化或整数表示。_empty_affine_quantized在两版登记acl_op `[v2.2,newest]`。

| 本地分支 | 构造入口行为 |
| --- | --- |
| V2R1 per-tensor | double scale先转float，分配单元素FP32 scale与INT32 zero_point；按输入格式分配同shape普通INT8/UINT8/INT32结果，再调用量化命令。结果本地没有附加ATen量化器的代码。 |
| V2R1 per-channel | 轴经make_warp_dim处理；scales/zero_points均1维、同长度且等于self对应轴，再分配普通整数结果并量化。 |
| V2R2及以后 per-tensor | 入口委托at::native::quantize_per_tensor；OpAPI文件为ATen的量化/反量化stub登记PrivateUse1回调，实际构造量化元数据的外部ATen实现不在本卡展开范围。 |
| V2R2 per-channel | 入口先将zero_points转CPU、Long并contiguous，再委托at::native::quantize_per_channel；OpAPI回调将CPU zero_points转PrivateUse1、Int、contiguous。 |
| V2R3及以后 per-channel | 入口直接委托ATen，回调只做zero_points.to(Int).contiguous()而不在这行显式指定设备；不能把它读成已证明整条路径没有CPU元数据或拷贝。 |

ACL与OpAPI的外层ATen委托原则一致，PrivateUse1 stub的注册定义位于所审OpAPI文件。不能把ACL函数存在理解成每次调用都同时执行ACL与ACLNN两条路线，真实派发取决于构建与调用环境。

## ACLNN与ACL的参数形态不同

OpAPI的 `_quantize_per_tensor_impl_out` 与 `_quantize_per_channel_impl_out` 以QInt8→Char、QUInt8→Byte、QInt32→Int选择普通输出dtype；代码缺省也是Int，未在这里为任意其他枚举补完整合法性检查。它们调用 `aclnnQuantize`，per-tensor的axis固定1，per-channel透传归一化后的轴。

ACL实现用OpCommand的 `Quantize`，dtype属性为字符串torch.qint8/quint8/qint32，缺省torch.qint8；这种缺省不能扩展为任意dtype都受支持。per-channel先将scale与zero_point reshape成“指定轴为原长、其他轴为1”的广播形状，再下传；OpAPI直接传入向量。per-tensor同样固定axis1。两条路线的参数包装差异不表示舍入、饱和或产品能力已经等价实测。

V2R1 per-channel的ACL分配使用apply_tensor，OpAPI使用apply_tensor_without_format；per-tensor及较新per-tensor stub按输入格式分配scale、zero_point及整数结果。格式分配策略不同，不能据接口名称推断全部路径保持任意私有格式。

## 新版PrivateUse1回调的存储与数值步骤

per-tensor量化回调按目标qtensor的量化dtype选择普通整数输出，构造FP32的单元素scale（double压为float）与INT32的单元素zero_point，调用 `_quantize_per_tensor_impl_out`，再执行 `NPUNativeFunctions::set_(qtensor,result)`。per-channel回调执行一维、等长和轴长度检查，生成同shape整数result、转换zero_point为INT32连续Tensor，量化后同样set_到qtensor。不能把这些set_调用直接当作已证明对外零拷贝、任意别名关系或所有量化器元数据行为不变，set_及ATen量化器本体未在本卡重审。

反量化回调先按QInt8/QUInt8/其他选择Char/Byte/Int，创建同shape且suggest_memory_format的普通整数Tensor，通过set_接入qtensor，再调用 `_npu_dtype_cast(...,Float)`。per-tensor接着计算 `(rtensor-zero_point)*scale`；per-channel用同一轴的广播reshape计算 `(rtensor-zero_points_reshape)*scales_reshape`。这里先显式转FP32，但后续Tensor运算的类型提升仍取决于scale等参数，不能简单承诺所有组合的最终dtype恒为FP32。

V2R2 per-channel的量化和反量化都会把CPU zero_point拷到PrivateUse1的Int；V2R3及以后对zero_point执行Int转换和contiguous，反量化时也按轴reshape。scales在这些回调没有被自动转换到某一固定dtype或设备，输入、device与合法性还依赖ATen及下层算子。单元素参数Tensor创建、连续化、dtype转换和可能的Host/设备元数据往返均要计入真实优化测量。

## int_repr、反量化入口与元数据访问

主线OpAPI int_repr分配普通整数tmp，QInt8→Char、QUInt8→Byte、其余缺省Int；tmp保留self.suggest_memory_format，经set_(tmp,self)后返回 `_npu_dtype_cast(tmp,output_dtype)`。两版ACL int_repr同样处理，但还先分配一个result再将其赋为dtype_cast返回值；不能据同dtype就保证没有分配或返回值与原Tensor别名。它不是按scale做反量化。

主线OpAPI dequantize直接委托 `at::native::dequantize_quantized`；两版ACL同样如此，具体选择per-tensor还是per-channel回调由外部ATen量化协议决定，本卡没有根据函数名推断CPU执行。

| ACL元数据入口 | 本地动作 |
| --- | --- |
| q_scale、q_zero_point | 委托ATen对应量化标量读取。 |
| q_per_channel_scales、q_per_channel_axis | 委托ATen读取，不在此补变换。 |
| q_per_channel_zero_points | 先从ATen取得Tensor，再显式to(PrivateUse1)。 |
| qscheme | 委托qscheme_quant。 |
| _empty_affine_quantized | 将size、dtype、layout、device、pin_memory、scale、zero_point、memory_format原样委托empty_affine_quantized；没有在本地填充数值。 |

这组读取入口的Schema版本与实际tensor元数据都要核对；不能把没有本地数值校验当作可随意混用qscheme、scale方向或zero_point表示。所审包装没有认证任意QInt dtype、非法scale/zero_point、空输入、NaN或非连续私有格式组合。

## 优化与验收边界

优先区分普通整数承载与带量化器协议的Tensor，再核对axis、scale方向、zero_point设备/类型、实际派发及格式。需要导出原始整数时用int_repr语义，恢复浮点值时用相应反量化协议；与自定义量化API混用应显式对齐表示和元数据。

本卡没有数值、性能、图捕获、梯度或量化模型运行结果。已读固定包装与注册只能说明本地调用链，ATen量化器、set_、dtype_cast和底层Quantize Kernel的执行支持仍按各自证据验收，不把完整文件映射提升成全仓知识完成。

## Evidence

- [QuantizePerChannelKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp)（primary）：1–352；完整本地文件。
- [QuantizePerTensorKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp)（implementation）：1–161；完整本地文件。
- [IntReprQuantKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IntReprQuantKernelNpuOpApi.cpp)（implementation）：1–45；完整本地文件。
- [QuantizeTensorKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizeTensorKernelNpuOpApi.cpp)（implementation）：1–28；完整本地文件。
- [QuantizePerChannelKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp)（implementation）：1–363；完整本地文件。
- [QuantizePerTensorKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp)（implementation）：1–189；完整本地文件。
- [QuantizePerChannelKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp)（implementation）：1–219；完整本地文件。
- [QuantizePerTensorKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp)（implementation）：1–112；完整本地文件。
- [IntReprQuantKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IntReprQuantKernelNpu.cpp)（implementation）：1–49；完整本地文件。
- [QuantizeTensorKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp)（implementation）：1–73；完整本地文件。
- [QuantizePerChannelKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp)（implementation）：1–232；完整本地文件。
- [QuantizePerTensorKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp)（implementation）：1–130；完整本地文件。
- [IntReprQuantKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IntReprQuantKernelNpu.cpp)（implementation）：1–49；完整本地文件。
- [QuantizeTensorKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp)（implementation）：1–73；完整本地文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4048–4055、7707–7734；仅所列Schema条目。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3936–3943、7469–7494；仅所列Schema条目。
