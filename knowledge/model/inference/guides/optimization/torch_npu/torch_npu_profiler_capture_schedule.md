---
type: Guide
title: TorchNPU Profiler：采集活动、步数调度与离线解析
description: 说明 CPU/NPU 活动、schedule 与 step 配对、调试开销和解析方式，区分快照与性能采集。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-profiler.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/torch_npu-profiler-schedule.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/torch_npu-profiler-schedule.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md
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
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
created_at: '2026-11-09T02:15:26Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU Profiler：采集活动、步数调度与离线解析

## 版本与范围

依据固定 PyTorch 主线 ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf 的 Profiler 指南中“使用前准备”“采集和自动解析”“离线解析”及 profile/schedule 接口章节，并以固定 OpPlugin 主线的 profile 产品页确认 A2/A3 训练接口范围。本卡覆盖基础采集，动态采集、MSTX、子线程和数据库关键关联见专项指南；完整硬件指标矩阵与全部数据库字段仍需另核对，本次未运行采集。

## 活动与成本

torch_npu.profiler.profile 默认同时采 CPU/NPU：CPU 对应框架，NPU 对应 CANN/设备。profile_memory 在两种活动下采不同层内存；它不是 OOM 历史快照。record_shapes、with_stack、with_modules 默认关闭，后两项依赖 CPU 活动并增加开销。需要调用链或 shape 时再打开，不将高成本调试吞吐当作正常基准。

## 调度和产物

schedule(wait,active,warmup=0,repeat=0,skip_first=0,skip_first_wait=0) 与每轮 prof.step() 配对；wait 跳过、warmup 预热、active 记录，repeat=0 按总步数持续重复而不是不采集。skip_first_wait 只省略第一次 wait。训练总步数必须足以进入 active；分析集群或查看工具时可选 repeat=1，使一次窗口对应一份数据。手动 start/stop 需完整配对。

tensorboard_trace_handler 指定产物目录并可自动解析，analyse_flag=False 可关闭自动解析；async_mode 控制解析是否阻塞业务。省略 on_trace_ready 时保留原始数据，再使用 torch_npu.profiler.profiler.analyse(profiler_path=...,max_process_number=...,export_type=['text']) 离线解析。大数据量可降低解析进程数，不能把解析停顿算成模型算子耗时。

## 采集边界

Profiler 调用与业务须在同进程，各种采集方式不同时开启，性能采集不与 Data Dump 同时进行。多进程多 Device 可各设备分别采；多进程同设备需完整启停且采集串行。单进程多 Device 的 Profiler 支持另有 PyTorch 版本条件，不能用它推翻 TorchAir 每进程只用一张 NPU 的整体限制。输出目录、rank/worker 与采样窗口必须可对应。

## 验证

核对 schedule 实际覆盖步数、activities 与文件类型、采集/解析日志及同负载时间线；移除高成本采集后复测稳态。框架特定绝对步数、恢复训练和 rank 选择见[训练可观测性](../../../../training/concepts/techniques/training_debug_observability.md)，不要与原生 schedule 参数混用。

- [OOM 内存快照](torch_npu_oom_memory_snapshot.md)
- [图模式分层定界](torchair_accuracy_and_performance_triage.md)


## 专项采集与分析

- [动态采集、显式触发和恢复步数](torch_npu_dynamic_profiler.md)
- [子线程回调与启停](torch_npu_profiler_child_threads.md)
- [MSTX 范围与流、Domain 配对](torch_npu_mstx_ranges.md)
- [内存时间线和元数据](torch_npu_profiler_memory_and_metadata.md)
- [数据库关联和时间单位](torch_npu_profiler_database_relations.md)

## 指标选择与测量干扰

- [Level、AI Core 指标与主线默认值差异](torch_npu_profiler_metrics_selection.md)
- [GC 阈值与进程/系统级采样](torch_npu_profiler_gc_and_host_system.md)
- [内存数据库与实际归还](torch_npu_profiler_memory_database.md)
- [互连采样和通信统计的口径差异](torch_npu_profiler_interconnect_database.md)
- [启动、解析和共享存储落盘的测量开销](torch_npu_profiler_measurement_overhead.md)

## 原生Profiler支持页的名称与版本层级

同一PyTorch主线七版本原生torch.profiler页要求使用各条目给出的NPU形式：profile/schedule/tensorboard_trace_handler/ProfilerActivity/ProfilerAction/step映射到torch_npu.profiler，元数据和导出方法映射到torch_npu.profiler._KinetoProfile对应方法。profile、schedule、handler、Activity/Action与step中文仅列A2/A3，英文明确950DT不支持，本卡保持A2/A3范围。

2.7.1、2.9..2.12把_KinetoProfile作为独立条目，类及add_metadata/add_metadata_json/export_chrome_trace/export_stacks列三类产品；2.13/2.14改以profile.*列这些方法，中文仅A2/A3、英文明确950不支持，NPU形式仍指向_KinetoProfile。旧类或部分导出方法列950不能扩大新版profile采集入口；这组文档收录/产品差异不直接证明实际发行包何时增删能力。

英文七版本对events/key_averages另列三类均不支持，旧五版本在_KinetoProfile下、新两版本在profile下；ProfilerActivity.name及itt.is_available/mark/range_push/range_pop亦三类均不支持。不要将它们与[autograd.profiler报告工具](../../../../training/guides/torch_npu_native_autograd_profiler.md)的同名方法互换命名空间和产品表。

英文2.14对原生profile写use_cuda已移除、使用activities，以及with_modules弃用、动态图模块跟踪改with_stack=True；同提交中文原生页未给这段说明，本文主来源的TorchNPU接口指南又单列with_modules配置。保留来源/命名空间/版本边界，不将原生英文提示无条件覆盖TorchNPU专用指南或实际包签名。

## 全文复核后的版本、窗口和导出范围

两语言使用前准备都要求配套Toolkit/算子包、驱动与已迁移模型；单进程多Device专门列PyTorch2.1.0post14、2.5.1post2、2.6.0及之后，不把通用≥2.1替代该条件。快速入门的PyTorch2.9/Python3.12/AArch64/torchvision0.24.0只是示例组合，不替代主线2.14或26.0/PyTorch2.8配套。建议一次采集≤5分钟，并按已落盘data原始数据预留至少20倍内存/磁盘，这是来源资源建议，不是模型显存配额或产物大小保证。目录可写、无软链接及权限条件随实际部署核对，未执行安装或权限修改。

英文导航一句“no more than two”与中文及英文后文“各方式不可同时开启”不一致，按具体约束选择一种采集方式。现代原生torch.profiler示例及支持表的冲突独立放在[兼容入口草稿](torch_npu_native_profiler_compatibility.md)，不覆盖本卡A2/A3专用采集范围。

两语言schedule图分别查看：skip_first在循环前只执行一次，warmup/active和保存回调按repeat安排；中文额外标出首次wait可跳过，英文图未标。总步数公式skip_first+(wait+warmup+active)*repeat没有扣除skip_first_wait，是足量预算说明，不能据它否定示例9步：wait2/warmup1/active2/repeat2/skip_first1并跳过首次wait时共需9步。repeat=0按有限业务步数继续循环，不将示例9次换算当所有输入的精确份数。

_KinetoProfile没有profile的schedule/on_trace_ready、step及子线程注册入口，不能仅按继承/同名把全部控制参数互换。导出stacks需实际with_stack数据和版本支持的metric；文档stack.log与FlameGraph示例profiler.stacks文件名不一致，应使用真实产物，不把该命令链当作已跑通配方。

## 目录清单是按条件生成的产物

| 产物 | 指南列出的条件或用途 |
| --- | --- |
| trace_view.json、operator_details.csv | 整合框架/CANN/设备事件与算子明细，仍依赖实际采集活动 |
| task_time.csv | NPU活动且Level0/1/2 |
| api_statistic.csv、communication.json、communication_matrix.json | Level1/2，后两项还要实际存在通信 |
| data_preprocess.csv | Level2且存在AI CPU任务；无任务不生成 |
| kernel_details.csv | NPU活动；shape/指标等字段另受对应配置影响 |
| memory_record/operator_memory/npu_module_mem.csv | profile_memory所控制的各层内存产物 |
| l2_cache.csv、soc_pmu.csv | 对应l2_cache，后者还明确NPU活动；不与AiCMetrics.L2Cache混为同一参数 |
| nic/roce.csv、hccs/pcie.csv | 分别sys_io与sys_interconnection |
| analysis.db | 实际通信/迭代分析，Text与Db及CANN导出能力另核 |
| FRAMEWORK、PROF、logs、PLATFORM | 框架原始、CANN原始/解析、解析日志与NUMA相关数据，层次不同 |

输出目录中的hostname/pid/timestamp、单卡省略Rank_ID和*_op_arg/_op_args样例后缀不能硬编码为跨版本协议。handler路径优先于ASCEND_WORK_PATH，省略自动解析时保留原始数据后离线analyse；离线最大进程数1..CPU核数、缺省CPU一半，超出上限取CPU核数、非法值取缺省是本指南合同，不与编译进程数默认混用。

## 独立API页与两版实际默认行为

发布与主线实现都在schedule省略或非空不可调用时使用持续RECORD的默认函数，并关闭ProfilerStep标记；文档“默认不执行操作”不等于不采集。ProfilerAction页直接传枚举的示例会触发这个回退，有限窗口请传[Schedule对象](../../../apis/torch_npu/profiler_schedule.md)。主线skip_first_wait不在发布实现，不能把本文主线签名回推26.0。

省略handler时还须考虑export_only临时目录：没有ASCEND_WORK_PATH时，_KinetoProfile析构会删除该目录；原始数据不保证长期保留。需要离线分析可显式handler且analyse_flag=False，并核对真实路径、生命周期和[主线压缩规则](../../../apis/torch_npu/profiler_trace_handler.md)，不由“已归档”推断解析成功。

主线execution_trace_observer在外层profile.start/stop调用，不按每个schedule active窗口反复启停；[profile API](../../../apis/torch_npu/profiler_profile.md)保留此差异。专用OpPlugin主线profile页增加950DT，与本文原生支持页限制并不一致；本卡继续A2/A3，不静默择一扩平台。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-profiler.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/torch_npu-profiler-schedule.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/torch_npu-profiler-schedule.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-ProfilerAction.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-schedule.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-tensorboard_trace_handler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/scheduler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/scheduler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py)（implementation）
