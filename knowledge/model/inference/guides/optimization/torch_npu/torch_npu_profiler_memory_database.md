---
type: Guide
title: Profiler 内存数据库：分配、释放与流内归还时间
description: 区分 MEMORY_RECORD 快照和 OP_MEMORY 生命周期，按组件、设备、流及字节数分析。
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
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/memory_record.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/memory_record.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/operator_memory.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/operator_memory.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/npu_module_mem.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/npu_module_mem.png
  role: constraint
created_at: '2026-11-09T03:21:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler 内存数据库：分配、释放与流内归还时间

## 版本与任务

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，限定已声明产品支持的 A2/A3 采集路径。两仓主线提交不自动构成兼容软件栈；不回推为 26.0/PyTorch2.8 的默认值或完整能力。


## 两张表回答不同问题

两表均由 profile_memory 控制。MEMORY_RECORD 记录组件的内存占用状态；component 是 STRING_IDS 的 ID，可解析为 GE、TorchNPU 或 TorchNPU+GE。字段还包括 timestamp、totalAllocated、totalReserved、totalActive、streamPtr 和 deviceId。组件总计与分项不是可直接相加的独立占用，streamPtr 也不能当作跨进程稳定身份。

OP_MEMORY 根据 MEMORY_RECORD 整理算子的内存使用；name 需经 STRING_IDS 解析，size 的单位 Byte。allocationTime、releaseTime、activeReleaseTime 分别表示申请、释放与实际归还内存池时间，单位 ns；duration 与 activeDuration 同为 ns，描述相应占用区间。不能把 Python 对象结束或 releaseTime 等同于设备侧立即可复用。

## 生命周期与总量联合查看

OP_MEMORY 的 allocationTotalAllocated/Reserved/Active 描述申请时的总量；releaseTotalAllocated/Reserved/Active 描述释放时的总量，单位均为 Byte。其中 Allocated/Reserved 覆盖 TorchNPU 和 GE，Active 描述当前流申请量；并不是三类互不重叠的内存。

streamPtr/deviceId 限定记录位置。分析一个分配时，先核对名字、设备、流及采集窗口，再比较申请、释放和实际归还；释放信息未完整捕获时保留缺失或版本定义的特殊值，不一律补零、也不直接判断为泄漏。

本页来源没有明确给 MEMORY_RECORD.timestamp 标注单位，而 OP_MEMORY 的时间列明确为 ns；不能因为列名类似就无条件相减。应按实际安装版本的表结构/解析实现核对时间基准后对齐。

## 一个只读关联示例

下面仅展示文档字段间的关联，不预设全部版本均有相同表；先检查实际 schema。

```sql
SELECT m.deviceId, m.streamPtr, s.value AS operator_name,
       m.size, m.allocationTime, m.releaseTime, m.activeReleaseTime,
       m.duration, m.activeDuration
FROM OP_MEMORY AS m
LEFT JOIN STRING_IDS AS s ON s.id = m.name
ORDER BY m.deviceId, m.allocationTime;
```

使用 LEFT JOIN 保留尚未解析到名称的记录；同名多行是多次分配的候选，不将名字当唯一主键。此示例未在真实数据库执行。

- [allocated、reserved 与设备整体占用](torch_npu_memory_counters.md)
- [可视化时间线的采集前提](torch_npu_profiler_memory_and_metadata.md)


## 结果核验

检查实际配置、采集窗口、rank/device 和导出模式，再检查文件及表是否存在；未采集或未关联不等于数值为零。关闭高成本观测后复测正常负载。本文没有运行采集、数据库查询或 NPU 性能实验。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)
- [数据库关联和时间单位](torch_npu_profiler_database_relations.md)

## CSV与DB单位以及历史组件名

两语言CSV图逐字节相同，均已查看。operator_memory的Size是KB、时间是us、总量是MB；OP_MEMORY的size和总量是Byte、时间列为ns，不从相似列名直接相减。MEMORY_RECORD.timestamp仍无单位明示，保留前文限制。

memory_record组件除TorchNPU/GE还可有APP进程总量、TASK_QUEUE_ENABLE=2时的WORKSPACE；它们不是互斥分项，不能与组合行机械求和。历史截图使用PTA/PTA+GE、Stream Ptr科学计数法，npu_module_mem图使用SLOG；不把这些字符串和展示格式固定为所有解析版本的枚举或精确指针值。

operator_memory图的Active Release/Duration为N/A表示该样例未展示相应值，不是已证明泄漏；缺失/负值解释委托外部msprof文档，其全部定义不在本卡来源内。Release Total Active的CSV文字强调跨流未释放复用，而DB表写当前流申请总量，保留所在产物层次，不凭描述合并两套统计协议。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/memory_record.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/memory_record.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/operator_memory.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/operator_memory.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/npu_module_mem.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/npu_module_mem.png)（constraint）
