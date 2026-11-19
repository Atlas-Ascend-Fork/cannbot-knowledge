---
type: API
title: TorchNPU C++ NPUEvent：记录、等待、查询与计时
description: 区分流依赖和CPU同步，保存延迟创建、recordOnce、毫秒计时与TaskQueue等待成本。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUEvent.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUEvent.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)struct-c10_npu-NPUEvent.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: implementation
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU C++ NPUEvent：记录、等待、查询与计时

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 生命周期与设备

定义于`torch_npu/csrc/core/npu/NPUEvent.h`。文档列默认构造、flags构造、析构和移动构造；发布配对头禁止复制、允许移动。事件通常首次record才创建并取得该流的设备，后续record流须匹配设备；从IPC句柄构造等路径另有条件，不据通常延迟创建规则覆盖所有构造入口。

`device()`返回optional Device，未创建可为空；`isCreated()`查询是否已创建，`device_index()`和`event()`取得编号/底层事件，转`aclrtEvent`等价取得事件表示。未创建时的空值/默认编号不是有效已记录事件。

## 记录与等待成员

|成员|语义|
|--|--|
|`record()`、`record(const NPUStream&)`|在当前流/指定流记录事件。|
|`recordOnce(const NPUStream&)`|仅首次记录；不等于每轮迭代自动更新事件位置。|
|`query() const`|查询记录点相关工作完成状态；不能解释成所有流及未来工作均完成。|
|`block(const NPUStream&)`|使指定流等待事件，核心是设备流依赖，不等同调用synchronize等待设备完成。|
|`synchronize() const`|CPU等待事件完成，不自动成为整个设备全局屏障。|
|`elapsed_time(const NPUEvent&) const`|返回两事件间隔，float，单位毫秒；不是以秒计，也不是所有流模型关键路径。|

发布中文elapsed_time说明误写成事件block，主线改为查询耗时；不能据旧行把它当建立依赖的接口。

## 发布实现的Host等待与计时成本

配对NPUEvent.cpp120–225行中，block在多TaskQueue或IPC事件条件下会在Host等待record出队，然后向目标流排入wait；捕获中的路径还会排空流队列。因此“建立流依赖”不能进一步夸成Host侧永不等待。外部事件在相应功能存在时限制一次record不能关联多次wait。

elapsed_time要求两个事件已创建，先排空Host队列并分别同步两个事件，再调用ACL取毫秒值；它不是无等待的纯查询。synchronize在TaskQueue开启时先等record记录状态，再同步事件。默认flags在该发布实现根据运行库能力选ACL_EVENT_SYNC或ACL_EVENT_DEFAULT，不硬编码某个值适配全部版本/计时需求。

业务计时应明确记录位置、依赖、预热和测量区间，验证事件能力及任务实际完成；仅静态核对，未创建事件或测时。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUEvent.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUEvent.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)struct-c10_npu-NPUEvent.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.h)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp)（implementation）
