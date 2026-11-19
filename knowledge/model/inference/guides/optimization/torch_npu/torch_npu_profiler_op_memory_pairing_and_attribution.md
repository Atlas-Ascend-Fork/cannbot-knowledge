---
type: Guide
title: Profiler内存生命周期：指针配对、缺失释放与算子归属
description: 追踪内存事件到operator_memory和OP_MEMORY的配组及队列归因，区分未知释放、统计槽位、设备/进程边界和单位。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py
  role: implementation
created_at: '2026-11-10T13:11:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler内存生命周期：指针配对、缺失释放与算子归属

## 固定生产链与覆盖范围

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的MemoryPrepareParser与文本/数据库消费者，对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的选定配组和输出函数。两版_add_pta_memory_data、_get_valid_record_entry、_get_op_name_of_record的AST一致；输出函数有局部布尔临时变量/等价条件写法差异，所审缺失字段与单位分支保持上述分别核对的合同，不宣称整个解析器相同。整卡平台未知，保持draft、空平台；没有执行上游、采集或数据库解析。

MemoryPrepareParser接收Torch树、队列与算子数据，返回pta_record_list和按Text/Db分开的memory_data。MemoryViewParser把Text内存生命周期与CANN数据用于operator_memory.csv；MemoryDbParser把Db条目的名字转成STRING_ID后写OP_MEMORY，并可合入GE条目。本卡只讲框架分配记录的准备与归因，不把GE整套生命周期或分类memory timeline当作同一算法；字段文档继续见[内存数据库](torch_npu_profiler_memory_database.md)。

## 先按进程和ptr配组，不是按算子名配对

准备层按time_ns排序，只把NPU记录加入pta_record_list，内部分配器记录才进一步进入算子生命周期配组。它先按pid分桶，再按ptr分桶；这里没有把device/stream另作为该分桶键。存在多设备、指针地址复用或多进程数据时，不能只用ptr或算子名跨范围合并结果。

_get_valid_record_entry从MALLOC起建组，初始FREE/BLOCK_FREE会跳过；每组最多3条且data_type不能重复。遇到相同类型或容量已达3时结束当前组，再从新位置寻找MALLOC。固定类型为MALLOC=0、FREE=1、BLOCK_FREE=2；该方法分割重复使用地址的候选生命周期，不是验证所有异常事件序列都语义完整，也不会为采集开始前的分配凭空补MALLOC。

没有同pid的Torch算子时，该pid内存不进入这些OP_MEMORY准备条目，即使原始NPU记录仍可存在。单靠表中缺行不能判断该分配没有发生。

## 1/2/3条记录产生不同释放字段

| 组内记录 | 准备层输出 |
| --- | --- |
| 只有MALLOC | 申请时间/大小及申请总量存在，释放时间、active释放、持续时间和释放总量为None |
| MALLOC加一个释放事件 | 第二条为FREE时填release/duration；为BLOCK_FREE时填activeRelease/activeDuration；另一套时间保留None |
| 三类齐全 | 按FREE与BLOCK_FREE类型分别选择两套结束时间，持续时间各减MALLOC时间；释放总量取FREE记录 |

这不是把BLOCK_FREE时间固定成Python对象死亡或设备完成时刻。这里消费的是已记录事件类型，底层allocator/stream语义仍需结合[内存统计](torch_npu_memory_counters.md)及实际采集核对。

CACHING类型的单条组给_incomplete_num加2，双条组加1；它计的是这个格式化过程的缺失槽位增量，不是唯一泄漏分配数。Text与Db格式函数都可以增加同一计数，不能把警告数字直接当作互异泄漏次数。采集窗口截断、未配对事件和真实长期存活要另外区分；缺失时间不应改填0。

## 队列归因和普通线程归因不同

有匹配dequeue时，先按(pid,tid)寻找覆盖分配时间的dequeue区间，再通过corr_id找enqueue，最后沿enqueue线程的Torch树找受支持前缀aten::/npu::/atb::的祖先名称。匹配失败可留下空名字与警告，并不创建一个虚构算子。

没有匹配dequeue时，按内存记录tid找开始时间不晚于申请的最近Torch节点，必要时沿父节点回溯到结束时间覆盖申请的区间。这是时间/树关联，不是Tensor所有权或全部Host调用栈证明；命名给分配源头也不表示该算子独占整段生命周期。

这些扫描保存前进索引，依赖准备层已按时间处理的顺序；外部不能任意重排记录后仍假定同样结果。当前输出只在首次需要时建立按tid索引，排除empty_tensor/malloc_workspace辅助节点；它没有重新证明任意多pid/多线程合并都完整。

## 单位与输出容器的边界

文本Size用原字节数/1024，总量用/1024^2，时间由ns转us；Db保留字节与ns。单一CANN设备目录可覆盖输出device标记，否则用记录自身device；不能以展示字符串当作跨进程稳定身份，或把文本KB/MB与数据库Byte直接比较。

每个pid的准备结果用memory_data.setdefault(Text/Db,...)设置，而非持续append；Text且支持默认Db的分支还可在首个处理pid后return。因此本函数返回容器不能直接认证任意多pid原始文件已经完整聚合。本次没有构造多pid采集复现，也不据此断言常规单pid路径必有丢失。

诊断时联合检查原始ptr/pid/device/stream、三个事件类型、申请与两种释放、空名称及缺失槽位，再看真正长期存活和[OOM快照](torch_npu_oom_memory_snapshot.md)。OP_MEMORY没有覆盖的指针、未知归属或None释放，不等于零成本或已证泄漏；本卡没有新增verified。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py)（primary）：定向范围33–161, 163–390。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py)（implementation）：定向范围106–163, 229–239, 241–331。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py)（implementation）：定向范围57–99, 133–149。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py)（implementation）：定向范围20–27, 75–97。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py)（implementation）：定向范围81–96, 178–184, 249–253。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（implementation）：定向范围85–100。
- [固定实现来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py)（implementation）：定向范围60–68。
