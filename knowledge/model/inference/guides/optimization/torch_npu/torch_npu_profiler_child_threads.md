---
type: Guide
title: Profiler 子线程采集：回调注册、设备与结束顺序
description: 说明主 Profiler 不自动感知用户线程，要求每线程配对注册与独立采集选项。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/child_thread_profile_data.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/child_thread_profile_data.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py
  role: implementation
created_at: '2026-11-09T02:54:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler 子线程采集：回调注册、设备与结束顺序

## 版本与范围

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的相应接口文档，限定 A2/A3。主线配套仍需核验，不回推为 26.0/PyTorch2.8 已支持所有选项。未运行采集或分析实验。

## 生命周期

主 Profiler 正常采集不代表能看到用户自行创建线程下发的框架 torch 算子。先启动主 profile，再在各子线程选择实际 NPU，调用 profile.enable_profiler_in_child_thread(...) 注册，业务结束后 disable_profiler_in_child_thread() 注销；主线程等待所有子线程结束后停止主 Profiler。

enable 参数 record_shapes、profile_memory、with_stack、with_modules、with_flops 默认均 False，可与主线程的开关不同。shape、stack、module、flops 依赖 CPU activity，其中 with_flops 暂不支持解析成性能数据，不能按开关名承诺输出 FLOPs 统计。

## 观测与限制

检查时间线里目标子线程的 aten 框架事件和线程/设备身份。缺少这些事件可能是未注册、注册范围不对或 CPU activity 未开，不要直接推断该子线程没有执行。

来源演示单进程多设备的 Profiler，不改变 TorchAir 每进程仅一张 NPU 的整体限制。采集回调只改变观测，不代替业务线程之间的执行同步、错误处理或 Tensor 生命周期管理。


## 使用后核验

先检查采集窗口、rank、线程、活动类型与配置是否生效，再核对实际产物和业务开销；缺少数据不等于该阶段耗时为零。关闭调试配置后再测正常性能。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)

## 完整样例与图的可消费范围

已查看两语言同像的子线程图：主线程455385与另外两条线程分开，子线程aten::linear/addmm是框架采集的示例。编号、层级和持续时间是历史数据，不作本机线程映射，也不与NPU kernel数量一一对应。

样例在主profile启动后注册各线程、业务后注销，主线程join再stop；model/input_data是占位，不能将一个未迁移到各设备的共享模型原样用于device0/1/2。普通路径展示的结束顺序没有独立给异常退出的自动注销保证，仍按真实生命周期核对；不因图中存在线程就认定回调已对所有新线程生效。

## Python参数顺序与注销等待

两固定实现的enable参数位置为record_shapes、profile_memory、with_stack、with_flops、with_modules，文档把最后两项顺序调换。使用关键字能避免错配，非bool参数逐项回False。

disable先同步当前NPU再注销C扩展回调，可能阻塞到该设备任务完成；它不是无等待的注册表操作，也不提供全部跨线程业务同步。独立子方法产品表比profile入口宽不能覆盖整体入口限制，详见[子线程API](../../../apis/torch_npu/profiler_child_thread_callbacks.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/child_thread_profile_data.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/child_thread_profile_data.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-disable_profiler_in_child_thread.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile-enable_profiler_in_child_thread.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)（implementation）
