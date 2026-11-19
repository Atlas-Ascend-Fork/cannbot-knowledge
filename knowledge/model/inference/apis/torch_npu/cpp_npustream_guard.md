---
type: API
title: TorchNPU NPUStreamGuard：作用域、查询与reset_stream
description: 区分Guard保存的上下文与线程当前状态，保存跨设备reset及文档/实现边界。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-NPUStreamGuard.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-NPUStreamGuard.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-NPUStreamGuard.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_device.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_stream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_device.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_stream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-reset_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-reset_stream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-reset_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUGuard.h
  role: implementation
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU NPUStreamGuard：作用域、查询与reset_stream

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 构造与恢复

定义于`torch_npu/csrc/core/npu/NPUGuard.h`。`explicit NPUStreamGuard(c10::Stream stream)`设置输入流所属设备，并将该设备的当前流设为输入流；析构恢复原上下文。它管理设备/流选择，不提交通信依赖、不等待任务结束，也不拥有Tensor的全部异步资源寿命。

发布配对头140–225行禁用默认构造、复制和移动。文档对非NPU流称行为未定义，头注释却称报错；保留来源差异，调用者须传NPU流，不依赖未经执行确认的具体异常行为。

## 查询与重置

|成员|文档合同|
|--|--|
|`current_device() const`|返回Guard最近设置的设备。|
|`current_stream() const`|返回Guard最近设置的NPUStream。|
|`original_device() const`|文档称构造时原设备；配对头注释涉及最近reset_stream时设备，不据简写承诺多次reset后含义固定。|
|`original_stream() const`|文档称构造时设置的流；配对头实际委托InlineStreamGuard保存的original_stream，不将其武断等同构造实参或任意设备当前流。|
|`reset_stream(c10::Stream stream)`|先恢复旧流/设备，再采用新流及其设备；不是清空流、取消任务或设备同步。|

current_*表达Guard保存的状态；若外部另改线程上下文，不能保证它始终等于即时线程状态。original_*的精确跨设备保存细节依赖配对InlineStreamGuard实现，该外部实现不在本卡来源范围，不扩充为完整算法。

头文件明确reset_stream不保存此前在不同设备设置的全部流；需要同时管理多设备多流时不能把单个Guard反复reset当作所有上下文均已保留。这里仅消费该限制，不提供未审阅的NPUMultiStreamGuard完整配方。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-NPUStreamGuard.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-NPUStreamGuard.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-NPUStreamGuard.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_device.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_device.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_device.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_stream.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_stream.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-current_stream.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_device.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_device.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_device.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_stream.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_stream.md)（primary）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-original_stream.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-reset_stream.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard-reset_stream.md)（primary）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard-reset_stream.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard.md)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-NPUStreamGuard.md)（primary）
- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-NPUStreamGuard.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUGuard.h)（implementation）
