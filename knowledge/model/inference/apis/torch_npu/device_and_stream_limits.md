---
type: API
title: TorchNPU 设备与流限核：设置、查询和重置
description: 说明进程级一次设置、流级覆盖与恢复、私有格式限制，以及核数配置和实际执行的区别。
tags:
- task.optimization
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-set_device_limit.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-get_device_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-set_stream_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-get_stream_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-reset_stream_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npu_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-get_device_limit.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-get_device_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-get_stream_limit.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-get_stream_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-reset_stream_limit.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-reset_stream_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-set_device_limit.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-set_device_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-set_stream_limit.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-set_stream_limit.md
  role: constraint
created_at: '2026-11-09T04:38:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU 设备与流限核：设置、查询和重置

## 版本和产品

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的五个接口产品表，范围为 A2、A3、950；这不证明任意历史 TorchNPU 版本均有相同接口，也不证明两个仓库的主线配套兼容。

## 接口契约

|接口|参数、返回值与生命周期|
|--|--|
|`torch.npu.set_device_limit(device, cube_num=-1, vector_num=-1)`|device 是卡号；先 set_device，接口只支持调用一次，且仅对当前进程生效；返回 None。|
|`torch.npu.get_device_limit(device)`|返回字典，含 cube_core_num 和 vector_core_num，表示所查询设备的核资源限制。|
|`torch.npu.set_stream_limit(stream, cube_num=-1, vector_num=-1)`|stream 是 Stream 对象；先 set_device，再在算子执行前设置。同一流多次设置以后一次为准，返回 None。|
|`torch.npu.get_stream_limit(stream)`|返回相同键的字典；未设流限制时，取当前进程的设备限制，否则取硬件默认限制。|
|`torch.npu.reset_stream_limit(stream)`|重置该流限制，返回 None；随后通过 get_stream_limit 检查默认资源配置，不要假定总是恢复到物理最大核数。|

设置参数默认 -1 表示不设置该类核的限制；它不等同于 GE 主线配置中 0 的约定。来源未给出其他任意负值或超硬件数的通用行为，不用它们构造动态调度策略。

## 流控核必须同时满足的条件

set_stream_limit 要求 `torch_npu.npu.config.allow_internal_format=False`，只对 Ascend C 开发的算子提供控核支持。非 Ascend C 算子可能不受限制，micro batch 多流并行甚至可能卡住；不能把设置成功理解为所有任务受到硬性资源隔离。

不支持多个线程并发设置同一流的核数；设置后的流可以跨线程传递使用，两种行为应区分。该 API 主要服务 micro batch 多流并行，不能单独保证通信与计算无死锁。

## 核验和恢复

先查询实际资源配置，再在已采集的 Profiler kernel_details.csv 中检查对应算子的 BlockDim，结合算子所属 Cube/Vector 及 Mix 信息判断是否符合限制；不能用字典值代替执行证据。流级试验结束后 reset_stream_limit 并再次查询。本文未调用这些接口或运行真机实验。

- [GE 和捕获图控核的不同层次](../../guides/optimization/torchair/torchair_core_limits_and_determinism.md)

## 两固定Python实现的校验与一次调用边界

发布npu_config通过_get_device_index接受可解析设备，独立主线仅接受非bool的int；非法类型会在调用底层前拒绝。_call_once_class在执行真实函数前就将called=True，因此首次参数错误也可能消耗进程的一次调用机会，不能按“未设置成功”无限重试。同一装饰对象并非按每设备计数，完整流程应在调用前准备有效参数。

流setter/getter/resetter要求非None且是Stream，Python只在对应核数!= -1时转发，未在这几行完成所有核数域校验。代码存在不扩大文档的私有格式、Ascend C和无并发设置条件。

## 发布文档、语言收录和采集示例

发布五页与 main 实际收录的五份英文已核对；main对应中文文件未收录，不当作删除或解除限制。发布set_stream_limit文字要求先set_device_limit，main英文改先set_device；Python局部包装没有自动设置进程限核，不把两种前提合并成通用默认。

发布reset示例对另一条新建流重置，main改对current_stream，需重置真正曾设置的同一流。Profiler示例从kernel_details.csv的BlockDim检查对应算子核数不超过配置，仍要区分Cube/Vector/Mix；日志“解析成功”及字典值不等于所有算子限核均生效，SwiGLU样例也不扩其独立产品支持范围。main五页950只确认DT，不扩950PR；本卡此前950范围按此限定消费。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-set_device_limit.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-get_device_limit.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-set_stream_limit.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-get_stream_limit.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-reset_stream_limit.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npu_config.py)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-get_device_limit.md)（primary）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-get_device_limit.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-get_stream_limit.md)（primary）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-get_stream_limit.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-reset_stream_limit.md)（primary）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-reset_stream_limit.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-set_device_limit.md)（primary）

- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-set_device_limit.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-set_stream_limit.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-set_stream_limit.md)（constraint）
