---
type: Guide
title: TorchNPU输出准备的重叠检查、尺寸调整与格式回写
description: 沿CheckOut和check_tensor说明out检查次序、is_same读写识别、两版resize差异与Sigmoid反向的格式临时及copy_回写。
tags:
- task.implementation
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/NpuUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/NpuUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ResizeNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ResizeNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ResizeNpu.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ResizeNpu.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastHelper.cpp
  role: implementation
created_at: '2026-11-11T02:58:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU输出准备的重叠检查、尺寸调整与格式回写

## 固定版本和实际消费者

本卡静态核对PyTorch/TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b的输出准备helper，并以OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布dedc316708372c9a8bfde4527abd2a94b74840f5的ACL sigmoid_backward_out为调用入口。整卡产品矩阵未知，保持draft与空平台。两仓主线的引用只建立源码对应关系，软件配套仍按已登记基线核对。

[Iterator和OpCommand类型准备](torch_npu_tensor_iterator_type_inference_and_cast_consumers.md)已解释公共类型推断与显式Cast。本卡补输出校验、尺寸与格式的实际准备次序，未执行上游或设备。

## CheckOut读取哪个参照

CheckOut(inputs, output, dst)先从dst提取NPU格式、dtype和sizes，再交给显式format/dtype/shape重载。另一个重载从dst取格式和dtype，shape采用单独实参。参照对象是调用者选定的Tensor，不能从helper名字推定这里重新计算广播形状或算子输出类型。

核心重载依次执行以下步骤。

1. 把input与output交给CalcuOpUtil::CheckMemoryOverLaps。
2. 要求output满足is_npu，并精确匹配传入dtype。
3. 逐输入用output.is_same(local_input)识别is_read_write。
4. shape不匹配时要求is_read_write为False，再进入当前版本的尺寸调整分支。
5. 最后检查输出实际格式与请求format。格式不同也要求is_read_write为False，随后调用npu_format_cast_。

dtype不匹配在尺寸和格式调整前报错，该步骤没有代为转换dtype。设备检查针对output的NPU类型，实际部署仍需核对各输入输出的device ordinal及执行上下文。

## 重叠、对象身份与两版尺寸分支

CheckMemoryOverLaps跳过未定义的输出，对每个已定义输出调用ATen assert_no_internal_overlap，再对每对输出与输入调用assert_no_partial_overlap。它没有在该循环比较多个输出之间的每一对，也没有以本地Storage地址比较代替ATen断言。准确允许关系仍依赖配套ATen实现，未展开外部ATen源码或运行别名实验。

后面的读写识别只看is_same。共享Storage的不同view仍需要按前述重叠检查及真实布局验证，不能把这一个布尔值视作完整Storage别名分析。

| 固定实现 | shape不同且通过is_same限制后 |
| --- | --- |
| 发布版check_tensor_size和CheckOut | 直接调用dst.resize_或output.resize_。 |
| 主线check_tensor_size和CheckOut | 先调用at::native::resize_output_check，返回True才执行resize_。 |

主线将这一步委托给配套ATen检查，所读helper没有定义其全部告警、空输出和特殊Tensor语义。尺寸准备先于格式检查，若resize_已执行，后续格式分支的异常不能按本函数理解成此前准备自动回滚。

check_tensor的显式dtype重载也先检查重叠，再检查NPU类型与dtype，最后调用check_tensor_size。只有expect_size的重载没有独立dtype比较，expect_tensor重载则转发其dtype/sizes或单独expect_size。所读check_tensor系列没有CheckOut末尾的格式转换。选用时应保留准确重载和参照对象，而不把几种helper合并成一个固定合同。

## Sigmoid反向的格式临时与实际回写

sigmoid_backward_out以grad_output作CheckOut参照，因此初始grad_input的dtype、shape和目标格式来自这个参数。通过准备后，如果grad_input不满足check_match，会先format_contiguous，执行nocheck，再format_fresh_view；匹配时直接交给nocheck。后续公共类型与OpCommand转换条件沿用已链接的类型准备指南。

check_match依次检查连续性、Storage描述与Tensor元数据匹配，以及有padding格式下的storage offset匹配。format_contiguous按当前分支调用src.contiguous、metadata_convert_match_without_copy_optimize或针对padding偏移的empty加copy_。描述不匹配时，metadata_convert_match在numel与base_sizes乘积一致且源为内部格式的分支调用npu_format_cast及npu_reshape_out，其余分支显式empty加copy_。这些请求须与具体格式转换消费者一起评估，不能统一计成一次固定大小的复制。

format_fresh_view(x,y)在两版所读实现中直接执行x.copy_(y)。这条out路径可以包含格式准备、算子写入临时对象和copy_回写。返回grad_input引用仅记录接口的返回对象，峰值内存与搬运量仍取决于实际分支。

## 采用前核验

记录准确helper重载、参照Tensor、输入输出dtype/shape/stride/format及is_same关系，分别观察重叠失败、尺寸调整、格式准备和回写阶段。对比不同版本时保留resize_output_check这一差异。先核结果、梯度和别名，再测显存峰值及复制耗时。仅完成所列固定源码的定向审阅，没有新增verified或设备性能结果。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（primary），定向范围134–224、307–371、513–519。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation），定向范围140–225、306–366、509–515。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation），定向范围344–356。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation），定向范围299–312。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/NpuUtils.cpp)（implementation），定向范围26–67、123–150、183–217。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/NpuUtils.cpp)（implementation），定向范围25–71、126–154、187–222。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp)（implementation），定向范围19–57。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SigmoidBackwardKernelNpu.cpp)（implementation），定向范围19–68。

## CheckOut尺寸分支的resize_实际做什么

前述resize_落到NPU本地实现，不是通用ATen委托。`NPUNativeFunctions::resize_`先处理前置：非Fake/Meta的张量若处于内部格式，先经`npu_format_cast_`转base格式（按下一节真实分支，可能换存储）；命名张量在发布版单独分支，尺寸不同即报错。随后`resize_impl_npu_`在sizes/strides完全一致时直接返回、不触碰存储；否则更新sizes/strides，经`maybe_resize_storage_npu`仅在目标字节数（含storage_offset）大于当前存储nbytes时进入`storage_resize_npu`。因此缩小尺寸不重新申请、不搬数据；增长才换存储。

`storage_resize_npu`要求存储resizable且base格式；主线在换存储前会flush挂起的DVM lazy fusion（其Store节点持有即将失效的data_ptr），发布无此步。它随后`allocator->allocate(size)`新申请、`set_data_ptr`换指针、更新nbytes与存储描述，并把旧数据按min(旧,新)字节的异步D2D拷贝搬进新存储。主线最后在deterministicAlgorithms、deterministicFillUninitializedMemory与npuFillUninitializedMemory同时成立时对新增存储段做确定性填充，发布没有该分支。

因此CheckOut对增长的out执行的是"保留旧内容的新存储"，不是清零重建；对缩小的out是元数据收缩。旧数据搬运与算子执行同流异步，崩溃/并发语义不在此展开。

## CheckOut格式分支的npu_format_cast_实际做什么

[公开格式接口](../../../apis/torch_npu/npu_format_cast.md)已给入口级语义，这里补CheckOut调用链上的实际分支。`npu_format_cast_(self, format)`先比较存储描述的npu_format_：相同即原对象返回；源与目标都是base格式时`format_cast_as_base_format`只重写origin_format_/npu_format_两个描述字段，不移动数据、不换存储。

其余情况先问`MaybeUseAclnnNpuFormatCast`，该helper先处理AclnnOnly分支，主线其后才是非AclnnOnly分支，两分支的准入与回退条件不同。AclnnOnly分支没有非连续/view守卫，也不设回退：aclnn符号缺失直接报错，`aclnnNpuFormatCastCalculateSizeAndFormat`查询失败同样报错，不落回aclop。主线非AclnnOnly分支先过两道守卫，非base格式且非连续的源、view张量（sizes与base_sizes不一致）直接回退；随后在CANN≥9.1.0加910B/910C且两个aclnn符号齐全时尝试aclnn，其`aclnnNpuFormatCastCalculateSizeAndFormat`查询目标size/format，返回非零（CANN尚不支持该格式对）也回退。这里的回退对象是size/format查询失败，不是从实际`aclnnNpuFormatCast`设备拷贝执行中恢复的一般性兜底。走aclnn时新申请目标存储、`aclnnNpuFormatCast`设备拷贝、再`self.set_(dst.storage(), ...)`把self换绑到新存储；回退走aclop：`ApplyTensorWithFormat`按目标格式申请新Tensor，经Identity（或跨格式组转换）拷入，同样`self.set_`换绑存储。发布版只在AclnnOnly走aclnn（符号缺失即报错），其余一律走上述aclop路径。

所以CheckOut格式分支完成后，out仍是同一个Tensor句柄，但其底层Storage可能已被替换并做过一次设备拷贝；把它当作原地址原地覆盖或零成本元数据调整都与这两条真实分支不符。

## 实现层来源

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ResizeNpu.cpp)（implementation）：1–62。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ResizeNpu.cpp)（implementation）：1–84。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ResizeNpu.h)（implementation）：1–152。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ResizeNpu.h)（implementation）：1–166。
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp)（implementation）：1–469。
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp)（implementation）：24–80、200–263。
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastHelper.cpp)（implementation）：22–33。
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastHelper.cpp)（implementation）：24–35。
