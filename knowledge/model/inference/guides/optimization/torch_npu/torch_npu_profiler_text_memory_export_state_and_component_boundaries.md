---
type: Guide
title: Profiler文本内存导出：共享状态、组件对象与版本边界
description: 补齐MemoryPrepare/View全链中的列表共享、祖先名前缀差异、非GE对象写CSV边界及空数据/部分输出，复用已有配组和总量算法。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_common_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_common_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py
  role: implementation
created_at: '2026-11-11T06:28:11Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler文本内存导出：共享状态、组件对象与版本边界

本卡完整核对固定PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的MemoryPrepareParser/MemoryViewParser，共4个本地文件1049行。主线Prepare390行、发布337行，所有raw差异和完整定义逐项对照，发布变动方法另读全文；View两版161行原字节完全相同。这里补导出状态、版本命名及组件对象边界；[指针配组与OP归属](torch_npu_profiler_op_memory_pairing_and_attribution.md)、[PTA/GE总量曲线](torch_npu_profiler_pta_ge_memory_merge.md)已有的算法和单位按原卡保留复用。平台未知，保持draft、空平台，没有导入上游、解析采集或写CSV。

## Prepare的返回数据和缓存是同一对象状态

run从依赖取Torch树/算子及enqueue/dequeue，generate_view依次加载ProfilerConfig、按需重建无CANN路径的框架树、初始化队列索引，再处理内存。异常返回FAIL和空字典；正常返回SUCCESS及pta_record_list、memory_data的原成员引用，不是深复制快照。_incomplete_num>0在成功路径告警，数值含义仍是既有配组卡所述缺失槽位，不是唯一泄漏数。

_enqueue_record_dict以corr_id建字典，同id后写覆盖，没有在这个键再加pid/tid；dequeue另按(pid,tid)累积列表，保存pid/tid集合。Torch游标按(tid,is_enqueue)保存，dequeue游标按(pid,tid)，record→name缓存连空名字也会保存。正文所述排序和单次处理约定很重要：本地没有在每次run统一清空pta列表、计数、dequeue列表、游标与名称缓存，不能将复用同一解析对象视为无状态重建。

配组仍只对NPU且内部allocator记录关联到同pid Torch算子；pta_record_list可以保留没有形成OP生命周期行的原记录。Text/Db结果按setdefault写入，Text且默认Db支持时还可在首pid后return。缺行、缓存空名称或一次成功返回不证明所有pid/设备/窗口完整。

## enqueue祖先名前缀存在真实版本差异

两版_get_op_name_of_record本体可相同，但它调用的_get_aten_op_name_by_enqueue_record消费不同模块常量：主线只接受`aten::`、`npu::`、`atb::`前缀；发布接受更宽的`aten`或`npu`前缀，没有同一个atb分支。不能用外层方法AST相同证明整条名称归因完全相同。

匹配不到dequeue时另走内存线程的时间/父链查找，不用上述同一祖先前缀筛选；已经匹配dequeue但缺enqueue则返回空名，不会因此再自动回退普通线程搜索。两条游标扫描均依赖时间顺序，缺失范围不能通过补一个相近算子名字修复。

Text的时间为ns经convert_ns2us_str转换并附尾制表符，size/总量与Db的Byte/ns不同；主线把双记录分支的FREE/BLOCK_FREE判据提成局部bool，发布直接重复条件，完整Text/Db槽位仍分别按已有配组卡解释。这些格式差异和真实前缀差异要分开记录。

## View取原列表，按活动决定CANN输入

MemoryViewParser从MEMORY_PREPARE拿Text生命周期列表和pta_record_list原引用；operator_memory.csv的15列生命周期表与memory_record.csv的7列组件快照不是同一张表。NPU activity不在传入活动列表时，APP、GE快照和GE算子文件三条CANN读取路线都给空set；PTA依赖仍按已有数据继续处理。

同类文件集合只取next(iter(file_set))的一份，未合并所有分片、rank或设备文件。APP行先进入size_record_list并把设备字段补`NPU:`前缀；GE快照分组件，GE算子row另extend到memory_data。这个extend会改变来自Prepare的同一Text列表，不能把两个阶段的输出当作彼此隔离、可任意重复调用的快照。

run取CANN设备列表，恰一项时保存该索引，否则保存-1。合并时把这个值写进MemoryUseBean.device_index；所读Bean getter在覆盖值为-1时回落原始索引，所以这里不是把所有多设备记录统一显示成NPU:-1。该成员赋值仍是真实对象修改，单设备覆盖也不提供跨rank/跨进程身份认证。

## 组合曲线、顺序与重复调用

普通PTA/GE记录输出原组件行及PTA+GE行，workspace只输出自身；同时间先PTA，组合沿用同设备对侧最近值，具体统计语义见组件合并卡。APP行在合并前加入、component_list最后拼接，整个CSV不是统一全局时间排序。GE Active getter=0而原GE.row的Active/stream为None，不能从组合列推定实测GE active为零。

size_record_list、ge_record_list、component_list等只在构造时初始化，generate前未统一清理。重复使用同一实例可再次extend和重处理旧行；_add_device_type_for_npu也会遍历已经存在的APP行，没有先检查是否已带NPU前缀。MAX_FIND_LAYERS=100在本文件没有被后续搜索消费，不能据这个常量名推导所有归因都有100层安全上限。

## 非GE组件对象的CSV边界

_get_data_from_file(...,bean_list=True)返回FileManager构造的GeMemoryRecordBean实例列表。split_component_ge把component恰为GE的对象放进ge_record_list；其他对象直接append到component_list，**没有在该分支取它们的row属性**。后续把size_record_list+component_list交create_csv_file，而writer直接调用csv.writer.writerows。

所读GeMemoryRecordBean及其CommonBean基类没有__iter__或__getitem__，row只是一个属性。因此若这条输入确含非GE对象，按这些未修改类定义，写出可因对象不可迭代而失败，由run返回FAIL；源码没有在这里统一转成七列CSV行。实际CANN是否产出这种组件组合仍待输入证据，本次没有构造或运行复现，也不把这一静态边界宣称为所有正常采集必然失败。

## 文件存在、空数据和部分输出各自核对

FileManager.read_csv_file缺文件/非正大小返回空列表；发布另对超过MAX_CSV_SIZE的文件告警并返回空，主线该函数没有同一个局部大小分支，不推导主线其他安全层无约束。读非空文件时逐DictReader行构造Bean，解析错误包装RuntimeError。它不是自动恢复损坏字段或补齐缺失采集。

generate_view按添加CANN→组合组件→operator_memory.csv→memory_record.csv顺序调用。create_csv_file对空data直接返回，已有旧文件不会在这里自动删除；有数据才写header和rows。后一个输出或更早解析失败不会回滚前面已经改动的列表或写好的CSV。因此SUCCESS、FAIL、存在旧CSV、只存在其中一张、空字段或未知释放均需分别看日志/窗口/版本，不以文件存在独立证明所有指标有效。外部CANN导出、allocator事件生产与完整路径安全策略继续按各自证据核验，未做数值、内存或性能实验。

## Evidence

- [ac0e156 _memory_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py)：范围 1–161。
- [ac0e156 _memory_prepare_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py)：范围 1–390。
- [ac0e156 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 29–45, 62–77。
- [ac0e156 _ge_memory_record_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py)：范围 9–47。
- [ac0e156 _common_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_common_bean.py)：范围 19–21。
- [ac0e156 _memory_use_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py)：范围 104–107, 109–111。
- [f3ecfe4 _memory_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py)：范围 1–161。
- [f3ecfe4 _memory_prepare_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_prepare_parser.py)：范围 1–337。
- [f3ecfe4 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 33–53, 74–89。
- [f3ecfe4 _ge_memory_record_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py)：范围 9–47。
- [f3ecfe4 _common_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_common_bean.py)：范围 19–21。
- [f3ecfe4 _memory_use_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py)：范围 104–107, 109–111。
