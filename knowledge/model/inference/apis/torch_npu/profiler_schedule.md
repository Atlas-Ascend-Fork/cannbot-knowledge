---
type: API
title: Profiler schedule与Action：步数、保存状态和参数回退
description: 说明Schedule可调用对象、四种Action、首次wait省略及非法参数的实际处理。
tags:
- task.lookup
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_action_controller.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_action_controller.py
  role: implementation
created_at: '2026-11-09T20:03:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler schedule与Action：步数、保存状态和参数回退

## 固定版本和支持范围

文档分别来自OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文；实现分别核对TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。发布组合ascend_26_0_pt28有独立配套证据，两个仓库主线提交不自动配套，不能用新参数回推发布版。

本卡平台限定A2/A3。部分OpPlugin主线接口页列950DT，但同一固定PyTorch主线原生Profiler支持页对相关入口另有明确不支持说明，且不同方法产品表并不相同；版本与命名空间冲突见[采集指南](../../guides/optimization/torch_npu/torch_npu_profiler_capture_schedule.md)，不以类级表扩展全部方法。旧Atlas条目不自动映射新型号。这里只做静态来源审阅，未导入上游、运行设备采集、解析或性能实验。


## 返回对象和逐步动作

torch_npu.profiler.schedule是导出的Schedule类别名，构造(wait,active,warmup=0,repeat=0,skip_first=0)；主线增加skip_first_wait=0，发布实现没有。构造得到可调用对象，schedule(step)返回ProfilerAction：NONE=0、WARMUP=1、RECORD=2、RECORD_AND_SAVE=3；文档返回“无”不能当作None合同。不要将ProfilerAction.RECORD本身传给profile.schedule。

skip_first只在整个过程前跳过，wait/warmup/active逐周期执行；repeat=0持续到业务结束，不是零次。main的非零整数skip_first_wait把第一次wait省略，后续周期wait保留。每次业务后prof.step()，构造从step0选动作；活动最后一步返回RECORD_AND_SAVE，随后转换负责停止、finalize和回调，枚举名不代表赋值瞬间已经保存。

## 检查和不完整窗口

两版wait/warmup非法或负值回0，active非法或≤0回1，repeat/skip_first非法或负值回0；main的skip_first_wait非int回0，负整数仍是非零开关。warmup=0仅告警采样可能失真，不自动补1。负step抛ValueError；这些是该包装的实际处理，不替调用者容忍错误配置。

WARMUP→NONE、RECORD→NONE/WARMUP均告警不正确调度，不能据切换成功保证保存回调已执行。WARMUP结束退出会finalize并删除空目录；在RECORD退出会停止并回调但可能不完整，RECORD_AND_SAVE退出也提示周期可能未完整。

文档建议warmup1，动态shape可先跳10步，集群查看repeat1便于一份窗口；均为具体采样建议，不保证所有模型10步已稳定。多份数据按时间戳分组后分析。主线英文示例skip_first与skip_first_wait间漏逗号，不复制为可运行代码。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/scheduler.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/scheduler.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/__init__.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/__init__.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_action_controller.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_action_controller.py)（implementation）
