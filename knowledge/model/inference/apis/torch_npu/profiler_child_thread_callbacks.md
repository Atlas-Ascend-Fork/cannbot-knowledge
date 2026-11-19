---
type: API
title: Profiler子线程接口：注册配置与同步注销
description: 保存五个开关、CPU活动条件和当前设备同步，区分线程观测与业务同步。
tags:
- task.lookup
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py
  role: implementation
created_at: '2026-11-09T20:03:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler子线程接口：注册配置与同步注销

## 固定版本和支持范围

文档分别来自OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文；实现分别核对TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。发布组合ascend_26_0_pt28有独立配套证据，两个仓库主线提交不自动配套，不能用新参数回推发布版。

本卡平台限定A2/A3。部分OpPlugin主线接口页列950DT，但同一固定PyTorch主线原生Profiler支持页对相关入口另有明确不支持说明，且不同方法产品表并不相同；版本与命名空间冲突见[采集指南](../../guides/optimization/torch_npu/torch_npu_profiler_capture_schedule.md)，不以类级表扩展全部方法。旧Atlas条目不自动映射新型号。这里只做静态来源审阅，未导入上游、运行设备采集、解析或性能实验。


## 参数与调用顺序

profile.enable_profiler_in_child_thread接收record_shapes/profile_memory/with_stack/with_modules/with_flops，默认均False。文档顺序modules在flops前，两个实际Python实现顺序是with_flops再with_modules；使用关键字避免位置交换。非法非bool逐项告警回False。

先启动主profile，在各业务子线程选择真实NPU并注册，业务结束后同线程disable_profiler_in_child_thread()，主线程join后stop。注册采用户线程下发的框架torch算子，主线程配置不自动替代子线程配置；shape/stack/modules/flops还依赖CPU活动。文档with_flops暂不支持解析的限制不能因开关True就省略。

## 注销及支持边界

两实现disable先torch_npu.npu.synchronize()再调用C扩展注销；这可能等待当前设备工作，不能称为纯粹无等待的回调删除，也不代替业务的跨线程/流同步。异常时须看日志和实际注册状态，样例普通路径没有自动finally注销保证。

两版产品页均比profile入口宽，另列A2/A3推理及旧Atlas推理；主线加950DT。单一子方法的表不能覆盖整套采集入口限制，TorchAir进程/设备约束也不由这份多设备示例取消。更完整生命周期与图例见[子线程指南](../../guides/optimization/torch_npu/torch_npu_profiler_child_threads.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)（implementation）
