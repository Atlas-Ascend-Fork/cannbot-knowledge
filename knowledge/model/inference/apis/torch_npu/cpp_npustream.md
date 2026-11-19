---
type: API
title: TorchNPU C++流API：取得、包装与Host队列刷新
description: 保存NPUStream成员与current/default/pool区别，明确stream(need_empty)的Host flush语义。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-getCurrentNPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-getCurrentNPUStream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-getCurrentNPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-getDefaultNPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-getDefaultNPUStream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-getDefaultNPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-getNPUStreamFromPool.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-getNPUStreamFromPool.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-getNPUStreamFromPool.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-setCurrentNPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-setCurrentNPUStream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-setCurrentNPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）class-c10_npu-NPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）class-c10_npu-NPUStream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)class-c10_npu-NPUStream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-stream_synchronize.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-stream_synchronize.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-stream_synchronize.md
  role: constraint
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU C++流API：取得、包装与Host队列刷新

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 获取与设置入口

|接口|含义|
|--|--|
|`c10_npu::getCurrentNPUStream(c10::DeviceIndex=-1)`|取得指定设备当前流，-1选择当前设备。|
|`c10_npu::getDefaultNPUStream(c10::DeviceIndex=-1)`|取得指定设备默认流；当前流不一定是默认流。|
|`c10_npu::getNPUStreamFromPool(c10::DeviceIndex=-1)`|从预分配池轮转取得流，不是每次无限创建一条独占物理流。|
|`c10_npu::setCurrentNPUStream(NPUStream stream)`|设置当前流，返回void；没有作用域结束自动恢复保证。|
|`c10_npu::stream_synchronize(aclrtStream stream)`|同步给定底层流，返回void；头文件NPUFunctions.h，不等于整个设备所有流同步。|

流类及取得/设置入口位于`torch_npu/csrc/core/npu/NPUStream.h`。文档列CUDA用途对照不授予CUDA版的额外参数，例如不把对照的isHighPriority强加到NPU池函数签名。

## NPUStream成员合同

|成员|用途与边界|
|--|--|
|`NPUStream(c10::Stream)`、Unchecked构造|前者检查NPU设备类型；Unchecked版本跳过检查，不能据名称把其他设备流变成NPU流。|
|析构、`operator==`、`operator!=`|包装对象生命周期及底层流身份比较，不是任务完成证明。|
|转换为`aclrtStream`、`c10::Stream`|取得底层/通用表示；底层转换可能涉及Host队列刷新，避免在队列回调里形成递归等待。|
|`device_type()`、`device_index()`、`device()`、`id()`|流所属设备与标识；不同层次的类型/id不互代。|
|`query()`|查询已提交工作的完成状态，返回bool；不是未来提交工作的保证。|
|`synchronize()`|等待该流工作完成，有CPU等待代价。|
|`stream()`、`unwrap()`|取得底层ACL流/通用Stream表示。|
|`pack3()`、静态`unpack3(stream_id, device_index, device_type)`|包装/恢复三项流身份元数据；不是Tensor序列化、跨进程句柄传送或任意版本ABI保证。|
|`setDataPreprocessStream(bool)`、`isDataPreprocessStream()`|设置/查询预处理流标识，不证明数据依赖已经满足。|
|`stream(bool need_empty)`|主线明确true先等待关联TaskQueue排空再返回底层流，false不要求这次Host flush。|

发布中文对need_empty=false有“不是返回空流”的易混措辞，主线中英文明确其队列刷新含义。这里的empty是Host TaskQueue排空，不是返回nullptr，也不是设备计算已经全部完成；flush后再直接向设备发任务仍要保证时序。

## 模型优化边界

切换流不自动建立数据依赖和Tensor资源所有权；用[Guard](cpp_npustream_guard.md)管理上下文、用[Event](cpp_npuevent.md)建立必要依赖。TaskQueue回调、流转换及资源寿命见[框架接入指南](../../guides/optimization/torch_npu/torch_npu_custom_op_taskqueue_adaptation.md)。不要为“更异步”移除业务所需同步，也不要把Host提交时间当设备耗时。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-getCurrentNPUStream.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-getCurrentNPUStream.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-getCurrentNPUStream.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-getDefaultNPUStream.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-getDefaultNPUStream.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-getDefaultNPUStream.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-getNPUStreamFromPool.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-getNPUStreamFromPool.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-getNPUStreamFromPool.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10_npu-setCurrentNPUStream.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10_npu-setCurrentNPUStream.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10_npu-setCurrentNPUStream.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）class-c10_npu-NPUStream.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）class-c10_npu-NPUStream.md)（primary）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)class-c10_npu-NPUStream.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10_npu-stream_synchronize.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10_npu-stream_synchronize.md)（primary）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10_npu-stream_synchronize.md)（constraint）
