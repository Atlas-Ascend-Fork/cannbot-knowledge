---
type: Guide
title: Profiler 测量开销：启动步、解析步与共享存储落盘
description: 区分业务性能、观测初始化和落盘/解析成本，大集群先检查共享存储竞争与回调阻塞。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/operator_details.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/operator_details.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/common.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/train.py
  role: implementation
created_at: '2026-11-09T03:21:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler 测量开销：启动步、解析步与共享存储落盘

## 版本与任务

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，限定已声明产品支持的 A2/A3 采集路径。两仓主线提交不自动构成兼容软件栈；不回推为 26.0/PyTorch2.8 的默认值或完整能力。


## 采集窗口边缘不代表稳态

Profiler 进入 warmup/active 前有初始化开销；采集结束后的自动解析也会扩大 step 耗时。需要参考业务 step 时，来源建议排除启动和解析对应步，检查中间有效窗口。不能看到首尾 step 变慢就判定模型计算劣化。

正常性能对照仍须使用关闭高成本观测的同输入负载，并分别记录采集、解析、输出与业务时间。简单把所有慢 step 删掉可能掩盖真实业务问题，应先确认它们与采集生命周期对应。

## 大集群共享存储可能成为瓶颈

on_trace_ready 的 tensorboard_trace_handler 若直接写共享存储，多 rank 同时大量落盘可引起响应延迟。来源建议先写本地目录，再搬移到共享存储；应保留 rank/worker 和窗口身份，避免路径冲突或结果串写。

这会改变写入位置，不自动取消 I/O。来源自定义回调在回调内执行解析和 shutil.move，跨文件系统搬移仍可能复制并阻塞；不能把它描述成无开销或异步上传。需要确认数据完整转移、目标写入成功与失败记录后，再处理本地副本。

## 示例的私有接口不固化为公共契约

来源示例直接使用 _profiler_path_creator.ProfPathCreator 和 prof_inst.prof_if.analyse()，含占位训练函数与随机临时目录。它是思路示例，不是可跨版本复制的公共回调实现；本卡不提供已经运行验证的搬移脚本。

若选择关闭自动解析、改离线解析，或使用实际版本支持的异步解析，需要分别检查原始数据保留、解析完成和资源占用。异步解析也不消除磁盘竞争或 Host CPU 成本。

data_simplification 默认 True，在导出后精简冗余文件；来源说明保留 profiler_*.json、ASCEND_PROFILER_OUTPUT、PROF 目录的原始数据、FRAMEWORK 和 logs。查找文件前应核对精简开关、导出模式及实际版本，不把精简删除与采集失败混为一谈。

- [GC、Host CPU 与磁盘采样](torch_npu_profiler_gc_and_host_system.md)
- [采集等级与额外指标成本](torch_npu_profiler_metrics_selection.md)


## 结果核验

检查实际配置、采集窗口、rank/device 和导出模式，再检查文件及表是否存在；未采集或未关联不等于数值为零。关闭高成本观测后复测正常负载。本文没有运行采集、数据库查询或 NPU 性能实验。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)
- [数据库关联和时间单位](torch_npu_profiler_database_relations.md)

## 压缩删除和原生示例的额外成本

中文长指南的handler表新增use_gzip：默认False，True时在指定目录生成同名.tar.gz，解析完成后压缩并删除原采集目录，只保留压缩包；英文表未列该字段，不据缺项否认能力，也不将此行为推广到未核对版本。异步解析、压缩与跨文件系统搬移分别有资源成本，处理原数据前先确认完成和目标结果。

快速入门样例是旧ImageNet训练脚本加transfer_to_npu，包含loss.item、打印、DataLoader与每epoch的采集上下文；原生TinyModel示例还每step同步。它们都不是无干扰基准，也不因注释保留CUDA/NCCL就证明未适配调用自动可用。DDP注释称自动拆分batch不能代替实际采样/每rank数据划分。

已查看operator_details图，Host/Device Self/Total、AI Core子集是嵌套统计，不直接求和；零Self而Total非零也不独立说明未执行。历史Py3.7路径和微秒值只展示字段。性能结论继续使用关闭采集的同负载对照，不把删除所有慢步视作修复。

## 基准辅助函数里的计时与同步顺序

同提交LLM TimingCallback先记录step_time，再profiler.step与设备同步；SimpleV1SparseDrive也在loss.item之前取时间差，不能仅凭打印的ms/s认定它覆盖设备完成。TorchBench的同步计时循环则另取30%..80%的中段，Profiler窗口和汇总Computing列平均不必是同批样本。

工具还可能在外层Profiler前额外运行一次训练迭代以避嵌套编译采集，这会影响状态。具体窗口、摘要丢步、空列表及旧目录选择见[TorchBench测量草稿](torch_npu_torchbench_measurement.md)和[LLM基准入口草稿](../../../../training/guides/torch_npu_llm_benchmark_inputs_and_switches.md)；它们完整产品合同未确认，不据本卡A2/A3采集范围宣称每个模型基准已支持或已复测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/operator_details.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/operator_details.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/utils.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/common.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/train.py)（implementation）
