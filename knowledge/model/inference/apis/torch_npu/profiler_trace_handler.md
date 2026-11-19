---
type: API
title: Profiler导出回调：Text/Db、异步解析与压缩保留条件
description: 区分handler返回函数、原始数据生命周期，以及主线gzip参数和错误路径。
tags:
- task.lookup
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ExportType.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ExportType.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-ExportType.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_npu_profiler.py
  role: implementation
created_at: '2026-11-09T20:03:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler导出回调：Text/Db、异步解析与压缩保留条件

## 固定版本和支持范围

文档分别来自OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文；实现分别核对TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。发布组合ascend_26_0_pt28有独立配套证据，两个仓库主线提交不自动配套，不能用新参数回推发布版。

本卡平台限定A2/A3。部分OpPlugin主线接口页列950DT，但同一固定PyTorch主线原生Profiler支持页对相关入口另有明确不支持说明，且不同方法产品表并不相同；版本与命名空间冲突见[采集指南](../../guides/optimization/torch_npu/torch_npu_profiler_capture_schedule.md)，不以类级表扩展全部方法。旧Atlas条目不自动映射新型号。这里只做静态来源审阅，未导入上游、运行设备采集、解析或性能实验。


## ExportType和回调对象

ExportType.Text='text'、Db='db'，用于_ExperimentalConfig.export_type。文档Text含JSON/CSV时间线和summary及汇总DB，Db仅数据库，实际DB依赖配套Toolkit能力；不能把Text当绝不生成DB。Db仅列on_trace_ready与离线解析导出。

tensorboard_trace_handler(dir_name=None,worker_name=None,analyse_flag=True,async_mode=False)返回handler_fn给profile.on_trace_ready；文档返回“无”不是Python包装返回值。默认worker身份按hostname/PID构造，目录名再带时间戳及_ascend_pt；显式worker名实现仍追加PID。路径无软链接等约束按安装包核对。

显式dir_name优先ASCEND_WORK_PATH；后者未指定时，已配置handler默认当前目录。未配置handler采用另一条export_only路径，无环境保留目录时析构可删原始数据；需要离线分析应显式配置handler并analyse_flag=False，或明确核对ASCEND_WORK_PATH产生的profiling_data路径与实际生命周期。

## 解析和主线压缩

analyse_flag=True请求自动解析，False只保留原始采集待离线处理；async_mode=True让解析异步，不代表采集或业务同步已被取消。布尔类型非法按对应默认回退。

主线实现和中文页增加use_gzip=False，英文仍只有四参数，发布实现也无gzip；主线实现另有use_python_export=False形参但函数体未消费，不承诺效果。gzip创建同名.tar.gz，临时包成功替换后删除原始采集目录；失败会清理临时包并告警，需看实际产物。

async_mode且analyse_flag同时True时等待返回的全部futures完成，只在无取消/异常时压缩；无futures不压缩，解析任务失败保留原始数据。其余分支直接压缩，包括关闭自动解析的原始数据，不能把“已压缩”推为“已成功解析”。同步路径也没有逐future异常检查后才压缩的同等分支。

这些是静态代码分支，不是已验证归档恢复。不要假定无handler原始数据一直存在或压缩包里必然具有全部分析结果。handler细节页未列950，类别总表或profile范围不能代替方法确认。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ExportType.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ExportType.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-ExportType.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_npu_profiler.py)（implementation）
