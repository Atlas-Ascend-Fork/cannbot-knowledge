---
type: Guide
title: Profiler 数据库：框架关联、通信分析与时间单位
description: 说明 STRING_IDS、PYTORCH_API、CONNECTION_IDS 和 analysis.db 的关键职责与缺失数据边界。
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
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/step_trace_time.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/step_trace_time.png
  role: constraint
created_at: '2026-11-09T02:54:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler 数据库：框架关联、通信分析与时间单位

## 版本与范围

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的相应接口文档，限定 A2/A3。主线配套仍需核验，不回推为 26.0/PyTorch2.8 已支持所有选项。未运行采集或分析实验。

## 文件与前置条件

ASCEND_PROFILER_OUTPUT 内 ascend_pytorch_profiler_{Rank_ID}.db 汇总框架和 CANN 数据；analysis.db 用于通信/迭代分析，是否生成相应表和文件取决于活动、Level、模型实际任务和解析结果。不存在相应任务时可能没有文件，缺失不是零耗时。

Text 导出包括 JSON/CSV 和汇总 DB，Db 模式只导出汇总数据库；底层 PROF 目录中的 msprof 数据不是同一层产物。跨版本不要预设所有表必存在。

## 框架关联

STRING_IDS 用 id→value 解析字符串；PYTORCH_API 的 name/inputDtypes/inputShapes 等整数是字符串 ID，不是文本。CPU activity 控制框架 API 与 CONNECTION_IDS，with_stack 控制 PYTORCH_CALLCHAINS，profile_memory 控制 MEMORY_RECORD。

PYTORCH_API 的 startNs/endNs 单位 ns；globalTid 高 32 位是 pid、低 32 位是 tid。connectionId 关联 CONNECTION_IDS，可表达 task_queue、前反向、torch-CANN-task 关系；不能只按相同名称或相近时间将 Host API 和 Device Kernel 一一配对。callchainId/connectionId 可以为空，必须保留未关联状态。

## 通信和迭代

analysis.db 中 CommAnalyzerTime、Bandwidth、Matrix 分别描述通信时间分解、带宽与 rank 对。group_name、step、算子名和 src/dst rank 等共同定位操作；等待长不等于链路带宽低，需要与所有 rank 到达时间和传输数据对照。

CommAnalyzerTime 的 start_timestamp 为 us，耗时字段为 ms；Bandwidth 的数据量 MB、传输时间 ms、带宽 GB/s；StepTraceTime 的 computing/communication/overlapped 等为 us。统一单位后再比较，不将各层耗时直接相加；重叠时间不是可额外累加的串行耗时。

本卡只覆盖这些关联与单位，不冒充完整数据库所有字段或所有硬件 PMU 矩阵。


## 使用后核验

先检查采集窗口、rank、线程、活动类型与配置是否生效，再核对实际产物和业务开销；缺少数据不等于该阶段耗时为零。关闭调试配置后再测正常性能。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)

## 调用链、Rank 和 Step 的补充关联

PYTORCH_CALLCHAINS 中的 stack 仍是 STRING_IDS 的字符串 ID；同一调用链按 stackDepth 还原，不能把一行整数当作完整堆栈。RANK_DEVICE_MAP 在导出汇总 DB 时默认生成：rankId=-1 表示未设置 rank，deviceId=-1 表示未采到设备，两个含义不能合并成合法设备或正常 rank。

STEP_TIME 由 schedule 控制，id 是 Step ID，startNs/endNs 为 ns。先按实际采集窗口和 rank/device 对齐，再关联业务 step；不能因缺行就为未采步补出零耗时。

## 按问题选择专项表

- [MEMORY_RECORD 与 OP_MEMORY 的生命周期和单位](torch_npu_profiler_memory_database.md)
- [GC_RECORD、阈值与 Host 系统采样](torch_npu_profiler_gc_and_host_system.md)
- [NIC/RoCE、HCCS、PCIe 的速率和累计计数](torch_npu_profiler_interconnect_database.md)
- [Level、PMU 与导出能力](torch_npu_profiler_metrics_selection.md)

本组卡蒸馏指南明确列出的框架、内存、GC 和互连表；仍不等于所有版本、所有 CANN 表或完整芯片 PMU 字段已覆盖。

## 迭代分解的全部字段与聚合边界

两语言明确StepTraceTime/step_trace_time的computing、communication、overlapped、communication_not_overlapped、free、stage、bubble、communication_not_overlapped_and_exclude_receive、preparing均为us。stage排除receive，bubble为receive时间，preparing从框架step起点到首个设备任务；它们不是三个可额外累加的独立区间。

CommAnalyzerTime还分别给wait_time、synchronization_time和idle_time；文档idle=elapse-transit-wait，没有另减synchronization，不能把该字段再重复扣减。Bandwidth/Matrix还区分数据包大小、次数、传输类型LOCAL/SDMA/RDMA与Collective/P2P。total_duration没有独立单位说明，不用相近字段的ms单位自行补齐。

step图两语言同像，已查看：####是表格显示未展开的数值，不据它填零或判数据损坏；历史NPU1/2/3、科学计数法与样例耗时不是本机结果。Free文字简述为总时间扣计算/通信，但计算通信可重叠，不据三列直接相减推导真实Host空洞；按实际分析器定义、窗口与交集核对，更多overlap也不必然意味着端到端更快。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/step_trace_time.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/step_trace_time.png)（constraint）
