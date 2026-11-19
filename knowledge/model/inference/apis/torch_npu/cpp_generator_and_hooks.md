---
type: API
title: TorchNPU C++随机数API：生成器、状态与Hooks
description: 保存默认生成器引用差异、seed与offset状态、graphsafe迁移及Hooks接口的独立签名。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-createNPUGenerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-createNPUGenerator.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-detail-createNPUGenerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-getDefaultNPUGenerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-getDefaultNPUGenerator.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-detail-getDefaultNPUGenerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）class-at_npu-NPUGeneratorImpl.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）class-at_npu-NPUGeneratorImpl.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)class-at_npu-NPUGeneratorImpl.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksArgs.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksArgs.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)struct-c10_npu-NPUHooksArgs.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksInterface.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksInterface.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)struct-c10_npu-NPUHooksInterface.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/NPUGeneratorImpl.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/NPUGeneratorImpl.cpp
  role: implementation
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU C++随机数API：生成器、状态与Hooks

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 创建与取得默认对象

`at_npu::detail::createNPUGenerator(c10::DeviceIndex=-1)`按值返回`at::Generator`；`getDefaultNPUGenerator(c10::DeviceIndex=-1)`取得指定设备的默认生成器，-1选择当前设备。接口页把后者写成`at::Generator&`，发布中文目录写常量引用，主线英文目录又简写Generator；发布配对头文件194–195行和cpp35–84行均为`const at::Generator&`，以实际编译版本声明确认const资格。

发布实现对每设备默认对象call_once初始化并seed；create则新建NPUGeneratorImpl、设置默认seed和offset=0。文档“创建默认生成器”的措辞不能把create等同于取回全局默认对象，也不意味着新建对象自动安装为默认对象。英文参数表的required措辞与原型默认-1分开保留。

## NPUGeneratorImpl成员与状态

定义于`torch_npu/csrc/aten/NPUGeneratorImpl.h`，设备索引构造默认-1。以下是接口族的职责，不是跨设备/跨版本随机序列相等保证。

|成员|契约与区别|
|--|--|
|`clone() const`|返回`std::shared_ptr<NPUGeneratorImpl>`。|
|`set_current_seed(uint64_t)`、`current_seed() const`|设置/读取当前seed；`seed()`生成新的seed，和单纯查询不同。|
|`set_offset(uint64_t)`、`get_offset() const`|设置/读取offset；与seed组成不同状态。|
|`set_state(const c10::TensorImpl&)`、`get_state() const`|以TensorImpl传入状态/返回`c10::intrusive_ptr<c10::TensorImpl>`；文档要求状态检查，不把任意Tensor当有效状态。中文get_state标题的重复类型词不是合法双返回类型。|
|`set_philox_offset_per_thread`、`philox_offset_per_thread`|管理每线程Philox offset。|
|`philox_npu_state(uint64_t increment)`|获取用于随机算子的PhiloxNpuState；increment是状态消耗的一部分。|
|`philox_engine_inputs(uint64_t increment)`|返回seed/offset二元组；发布头注明用于逐步迁移旧调用点，不能与philox_npu_state返回对象互换。|
|`device_type()`|静态获取设备类型，不表示某设备的运行验证。|

## 图模式接口变更

文档按PyTorch2.5.1及以上移除生成器类的`capture_prologue`/`capture_epilogue`，新增`graphsafe_set_state`、`graphsafe_get_state`、`register_graph`、`unregister_graph`。发布头对应声明为`graphsafe_set_state(const c10::intrusive_ptr<GeneratorImpl>&)`和返回`c10::intrusive_ptr<c10::GeneratorImpl>`的get；中文文档缺失模板类型处不直接生成可编译配方。

发布头的内部`NPUGeneratorState`仍有capture/replay辅助成员，不代表旧的生成器公共成员重新存在。保存seed不足以替代seed、offset和图注册状态的完整管理；更不能据与CUDA/curand用途类比推定逐位相同的随机序列、可复制任意graph状态或随意重置训练中的随机状态。

## Hooks接口独立消费

`c10_npu::NPUHooksArgs`仅有参数类描述与`NPUHooksInterface.h`位置，文档未列字段，不据类名补造字段。`NPUHooksInterface::getDefaultGenerator(c10::DeviceIndex device_index)`返回`const at::Generator&`，本接口原型没有默认实参；其CUDA对照中的`=-1`不能移植成NPU函数默认值。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-createNPUGenerator.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-createNPUGenerator.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-detail-createNPUGenerator.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-getDefaultNPUGenerator.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）at_npu-detail-getDefaultNPUGenerator.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)at_npu-detail-getDefaultNPUGenerator.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）class-at_npu-NPUGeneratorImpl.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）class-at_npu-NPUGeneratorImpl.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)class-at_npu-NPUGeneratorImpl.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksArgs.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksArgs.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)struct-c10_npu-NPUHooksArgs.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksInterface.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）struct-c10_npu-NPUHooksInterface.md)（primary）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)struct-c10_npu-NPUHooksInterface.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/NPUGeneratorImpl.h)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/NPUGeneratorImpl.cpp)（implementation）
