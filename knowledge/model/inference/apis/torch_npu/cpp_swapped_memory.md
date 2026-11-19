---
type: API
title: TorchNPU C++ Host存储Tensor：empty_with_swapped_memory
description: 保存NPU设备身份与Host实际存储的特殊合同、六类允许算子、图模式排除及打印版本门槛。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/at_npu-native-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/at_npu-native-empty_with_swapped_memory.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/at_npu-native-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.h
  role: implementation
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU C++ Host存储Tensor：empty_with_swapped_memory

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 声明与返回对象

定义于`torch_npu/csrc/core/npu/NPUFormat.h`，命名空间`at_npu::native`：

```cpp
at::Tensor empty_with_swapped_memory(c10::IntArrayRef size,
    c10::optional<at::ScalarType> dtype_opt,
    c10::optional<c10::Device> device_opt);
```

返回device身份为NPU、实际内存在Host侧的特殊Tensor。size是形状；dtype_opt传nullopt采用全局默认dtype，device_opt传nullopt采用当前默认设备。optional类型不等于文档原型给了C++默认参数，调用时不能无依据省略实参。

## 可用算子和图模式

产品表仅A2/A3训练系列，明确暂不支持图模式。该特殊Tensor当前仅支持`aten::fill_`、`aten::zero_`、`aten::mul_`、`npu_apply_adam_w`、`npu_hans_encode`和`npu_hans_decode`六类算子。不能据NPU设备名让任意普通NPU算子消费它，也不把它视为普通CPU Tensor、通用统一内存或自动fallback机制。

## 打印与数值初始化

**同时**满足CANN>=8.5.0及Ascend HDK>=26.0.rc1时支持直接打印。任一版本较低，直接打印会警告，文档要求先经mul_转普通Tensor再查看；主线样例“必须转换”注释不能覆盖较新组合的直接打印许可。

样例申请empty后做mul_(1)再打印，没有先填充有意义数据，不能据该输出声称分配结果已经初始化、计算正确或某算法无精度损失。先按允许操作建立有效初值、核对实际存储与消费者，再验证优化器/压缩等模型使用路径及Host内存节省和带宽成本；本文没有执行这些操作。

## Python入口及共同Allocator的消费成本

[Python特殊Tensor API](empty_with_swapped_memory.md)独立文档在main增加950DT，不能补给本C++页。两固定Host交换Allocator已核对：Host注册、页对齐与deleter设备同步/注销/释放是实际生命周期，不将Host存储理解为无同步开销；Python主线的deterministic空分配初始化也不自动成为全部版本或C++调用的普通数值初始化承诺。

## 交换Allocator头的声明与实现分开核对

固定PyTorch两版NPUSwappedMemoryAllocator.h均只在c10_npu::NPUSwappedMemoryAllocator命名空间声明get()和TORCH_NPU_API emptyCache()。get()的声明返回类型为c10::Allocator*；emptyCache()声明返回void、无参数。头文件没有另给分配、页对齐、注册、回收或缓存清理算法；这些实际生命周期仍按本卡已有CPP实现来源和特殊Tensor调用方核对，不能仅由声明名推导调用完成时机或硬件支持。

这个Allocator接口与at_npu::native::memory_swap裸指针复制不是同一个操作；后者的四方向编码、参数检查及队列寿命另见[异步Copy入口](../../guides/optimization/torch_npu/torch_npu_native_async_copy_event_and_callback_ownership.md)。不把两个名字中的swap当作通用自动迁移/普通CPU Tensor兼容承诺，也不扩大本卡文档限定的A2/A3训练及版本范围。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/at_npu-native-empty_with_swapped_memory.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/at_npu-native-empty_with_swapped_memory.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/at_npu-native-empty_with_swapped_memory.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md)（primary）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.cpp)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）

- [完整原生入口声明/定义](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.h)（implementation）：全文1–13。

- [完整原生入口声明/定义](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUSwappedMemoryAllocator.h)（implementation）：全文1–13。
