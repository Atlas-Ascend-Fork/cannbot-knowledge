---
type: Guide
title: Profiler迭代聚合：Text累加、Db区间并集与缺失边界
description: 补齐双版本完整DB聚合入口、区间对象与保存分支，保留归步、重叠/空闲/接收统计、对象共享及缺失数据边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_trace_step_time_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_trace_step_time_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_time_range_calculator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_time_range_calculator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-10T12:57:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler迭代聚合：Text累加、Db区间并集与缺失边界

## 固定消费者与两种输入

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的step_trace_time文本/数据库聚合及区间helper，对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。两版Text parser和RangeCaculator完整AST相同；Db parser的所查AST差异仅SQL字符串内空白，归一该空白后AST相同。比较用于识别版本差异，不代表完整Profiler已审或输出已验证。整卡平台未知，保持draft、空平台，没有执行上游、SQL、采集解析或设备实验。

Text导出配置安装TraceStepTimeParser，消费框架树/relation及CANN timeline；它以FwkCANNRelationParser返回的step范围关联事件。DbParser则在存在CANN路径且Level不是None时纳入分析表parser，其中TraceStepTimeDbParser消费StepInfoDbParser结果与已导出的数据库。不能把“文件存在”当作这些数据已经完整，或把下面任一格式算法默认为所有Profiler视图。

| 维度 | Text step_trace_time.csv | Db StepTraceTime |
| --- | --- | --- |
| 主要输入 | CANN timeline中命名为Computing、Communication、Free、Communication(Not Overlapped)的汇总事件，以及hcom_receive前缀事件 | COMPUTE_TASK_INFO关联TASK得到计算任务区间；COMMUNICATION_OP关联TASK定位通信所属device |
| 时间处理 | 直接累加这些输入事件dur，本层不重新合并全部Kernel区间 | 分别合并计算与通信的重叠/相接区间，再计算纯通信和内部空隙 |
| 单位 | timeline的ts/dur按us处理；框架step ns先转us | 原表startNs/endNs以ns处理，落StepTraceTime前转us |
| device身份 | 由process_labels中的NPU标签映射pid；标签仅NPU时为-1 | 来自TASK.deviceId；通信connectionId只纳入关联到唯一device的情况 |

它们与[operator_details的关联Kernel时长求和](torch_npu_profiler_operator_time_attribution.md)是不同层次。Db Computing区间并集不等于把operator Device Self/Total逐行相加，Text的汇总名称也不代表本层重新验证了CANN如何生成这些区间。

## 按起点归step，跨界任务不裁剪

两条路径都以事件/任务开始时间满足step.start<=start<step.end作为纳入条件，随后保留完整dur或end-start，没有在这些函数按step终点切割跨界任务。跨界长任务可将终点延伸到step范围之外；不能只凭step标签就把所有字段看作严格裁剪在相同窗口内。

Text遇到有step_range但没有命中任何step的事件时，会先积到None，再在输出时跳过这类行；没有step_range则按device输出Step=None的聚合。若timeline没有四类规定的分析汇总事件，Text即使见到其他Kernel或receive事件，也不从这些事件自动推导整套CSV。

Db输入另有缺失边界：需要STRING_IDS才能继续收集任务；计算和通信各按表存在情况收集。通信device关联SQL按connectionId分组，只有COUNT(DISTINCT deviceId)=1才纳入，缺失或多设备关联不等于该通信零耗时。[数据库身份与单位](torch_npu_profiler_database_relations.md)仍需共同核对。

## Db合并和Free只覆盖内部空隙

merge_continuous_intervals按起点排序，start<=当前end就合并，并原地扩大当前TimeRange.end_ts；相接区间也合并。Computing、Communication分别对这些合并后区间求长度和，因此它们不是各任务耗时的简单和。

compute_pipeline_overlap从两类合并区间的最早起点开始扫描，产出未被计算覆盖的纯通信片段，以及相邻已观测区间之间的Free。它没有凭step起止额外补前后空白；准备期、末任务之后到框架step结束的等待或未采到的任务，不能由Free这一个字段完整代表。

公共派生式为：

```text
Overlapped = Communication - Communication(Not Overlapped)
ExcludeReceive = max(Communication(Not Overlapped) - Bubble, 0)
Stage = 已观测事件/任务的最早起点到最晚终点跨度 - Bubble
```

Text的跨度还随其纳入的汇总/receive事件更新；Db使用计算和通信区间端点。Stage、Bubble、Free、Preparing并非独立可任意相加的串行时间。两个输入层不同，即使使用上述相同派生式也不承诺数值一致；更多Overlapped也不自动意味着训练step更快。

## Bubble和准备时间的实现边界

Text把hcom_receive前缀事件的dur直接累加为Bubble，本层没有做receive区间去重或与未重叠通信求交。Db先筛出同前缀TimeRange放进bubble_data，最后也对其长度求和；它不是在这里另计算完整通信接收关键路径。

Db还存在对象共享边界：bubble_data与origin_communication_data可持有同一TimeRange；通信合并会原地扩大所选对象的end_ts。因此Bubble应按这条实际对象链核对，不能先假定合并后每个receive对象仍保持原始单条长度，或简单拿原始receive求和推断所有输入的最终输出。本次只记录静态关系，未运行数据复现。

Preparing用于首个设备任务相对框架step起点的差。Text明确step时用首次Computing/Communication起点减框架起点；Step=None时尝试减首个框架算子。Db同样依赖首任务与框架数据，但所选_get_first_device_task_ts从0初始化：若没有compute而只有非负时间的communication，比较条件不会用其起点替换0，get_prepare_time据此返回0。这是该局部分支的静态推论，不是“通信无准备开销”的测量。

## 空step范围不能按一行零值解释

Db generate_view在step_range为空时先建立一行默认零值，但这行没有deviceId键，后面重排时无条件读取step['deviceId']。若确实进入这条路径，会在该读取处触发KeyError，由run捕获并报告解析失败；不能把前面的默认字典视为已经成功写入一行全零StepTraceTime。

本卡没有证明上游在任意环境都会送来空step_range，也没有执行解析器复现。遇到表缺失、Preparing为0、Bubble异常或Text/Db差异时，先检查真实parser日志、step依赖、采集窗口、输入表/flow、device关联与原始区间，再决定是缺数据、统计口径还是执行瓶颈。不要为未采集/未关联的阶段补造零成本；本卡没有新增verified或性能数字。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py)（primary）：定向范围18–188。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py)（implementation）：定向范围18–188。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_trace_step_time_db_parser.py)（implementation）：定向范围47–221。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_trace_step_time_db_parser.py)（implementation）：定向范围47–221。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_time_range_calculator.py)（implementation）：定向范围38–101。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_time_range_calculator.py)（implementation）：定向范围38–101。
- [固定实现来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py)（implementation）：定向范围62–105。
- [固定实现来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py)（implementation）：定向范围78–94。
- [固定实现来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py)（implementation）：定向范围47–49。
- [固定实现来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py)（implementation）：定向范围20–65。
- [固定实现来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（implementation）：定向范围258–265。

## 完整Db聚合模块与区间对象补充

本次完整核对两版TraceStepTimeDbParser的1–221行及RangeCaculator的1–101行。区间helper完整AST一致；Db模块唯一AST差异是已逐处阅读的SQL多行字符串中SELECT后尾空格，去掉这些明确空格后完整AST相同，没有删除docstring或改写条件来扩大等价范围。其他Text/关系文件仍保持原卡选段边界。

TimeRange为可变dataclass，start_ts/end_ts默认-1；CommunicationTimeRange仅继承并调用父构造，用类身份区分通信。generate_time_range按传入class_range新建对象再直接赋端点，没有校验start<=end或窗口。merge会原地排序输入列表并修改被保留对象；overlap helper对组合列表排序扫描，严格正间隙才产Free，边界相接不另造空隙。空输入返回空结果对，末尾通信剩余会追加；这些对象/别名行为与前文Bubble共享边界一起使用。

Db构造器把compute_task_info与communication_op_info设为defaultdict(list)，step与Torch记录初始为空。OpIndex固定为name/start/end/device四槽；run从DB_PRE_PARSER取Torch算子、从STEP_INFO_DB_PARSER取step，再初始化任务、聚合、写表。异常统一记录并返回FAIL/None；没有异常则SUCCESS/None。

任务初始化连接失败会告警并提前返回，缺STRING_IDS会记错误并返回，不抛异常；缺各任务表只跳过对应类别。上述返回未自动令run失败。save_step_trace_db_data连接AnalysisDb失败也只是告警返回，成功连接才建StepTraceTime并插入。因此SUCCESS不充分证明已产出该表，实际仍需同时检查日志、表、device行及输入任务数量。

get_e2e_time以-1初始化最早/最晚端点，空任务列表返回0；get_prepare_time将假值首任务时间直接视为0准备，None step仅有Torch记录时才从首框架起点减。generate_view按所有计算/通信device键的并集排序，逐device逐step生成行，默认字段和派生字段的实际单位沿前文；不为从未出现的设备补全表。空step缺deviceId的失败路径及仅通信时首时间初始化边界继续保留，不能把缺行解释成空闲成本为零。

所读文件没有证明上游SQL输入覆盖全部task、时钟一致、对象没有被其他消费者共享或所有输出已实际写入。整张卡仍是draft/空平台，未新增verified，未执行SQL/解析/设备实验。

## 完整数据库链与补充证据

- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_trace_step_time_db_parser.py)（implementation）：1–221。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_trace_step_time_db_parser.py)（implementation）：1–221。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_time_range_calculator.py)（implementation）：1–101。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_time_range_calculator.py)（implementation）：1–101。
