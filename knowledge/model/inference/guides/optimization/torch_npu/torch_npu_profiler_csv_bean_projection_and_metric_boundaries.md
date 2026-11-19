---
type: Guide
title: Profiler指标CSV投影：字段顺序、共享表头与版本边界
description: 说明各类Profiler统计Bean和IntegrateParser怎样透传CSV，区分字段投影、单位标签与尚未计算的性能指标。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ai_cpu_bean.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_api_statistic_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_common_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_hccs_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_l2_cache_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_nic_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_statistic_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_pcie_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_roce_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_soc_pmu_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_step_trace_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_task_time_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ai_cpu_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_api_statistic_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_common_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_hccs_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_l2_cache_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_nic_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_statistic_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_pcie_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_roce_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_step_trace_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_csv_headers.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_csv_headers.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_integrate_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_integrate_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_kernel_view_parser.py
  role: implementation
created_at: '2026-11-11T04:30:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler指标CSV投影：字段顺序、共享表头与版本边界

## 固定版本与知识边界

本卡完整审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`及发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的统计/通信CSV Bean、CsvHeaders和IntegrateParser。大多数成对Bean完整AST相同；两版表头常量与整合入口的实际差异单独列出。平台未知，保持draft；没有运行CANN分析、文件解析或设备实验。

CommonBean只保存传入字典的原引用。静态HEADERS声明、文件名和Python类名不是运行时schema，也不是PMU/带宽/利用率计算或硬件支持证明。

## 保留字典顺序的Bean

下列类的row为`list(_data.values())`，headers为`list(_data.keys())`，沿当前字典插入顺序输出；它们不按静态HEADERS重排、不校验必选列、不改数值类型、不换算时间或计算平均值。继承构造只传给CommonBean。

|Bean|可以从本地实现确认的范围|
|---|---|
|ApiStatisticBean|原始API统计字段透传，无本地调用次数或耗时聚合。|
|OpStatisticBean|声明Op Type/Core Type/Count/Total、Min、Avg、Max Time(us)/Ratio(%)静态表头，但row/headers仍取输入字典，未据Count重新计算均值或比例。|
|AiCpuBean|静态表头混合Timestamp、Compute_time(ms)、Memcpy_time(us)、Task_time/Dispatch_time/Total_time(ms)、Stream ID、Task ID；实现不把这些字段统一为同一单位。|
|HccsBean、NicBean、PcieBean、RoCEBean|互连数据原样投影，不计算带宽、吞吐、传输字节或通信暴露时间，缺列不自动补齐。|
|L2CacheBean|静态StreamId/TaskId/HitRate/VictimRate/OpName列表不参与实际排序和命中率计算。|
|SocPmuBean、TaskTimeBean|主线此目录新增的同形投影类；在固定发布树的相同路径没有这两个模块。不能据此断言发布栈完全不支持对应采集。|

输入字典后续被改写会改变新取出的row/header；已返回的列表只是该次keys/values列表，不构成完整数据快照契约。Stream/Task字段在此仅随行保留，未与框架corr_id、HostToDevice flow或step建立关联，解释关联应看[数据库trace与通信归因](torch_npu_profiler_database_trace_and_communication_attribution.md)。

## OpSummary与StepTrace有额外状态

OpSummaryBean的`headers=[]`是共享类属性：非空时row按此列表投影，缺字段填空字符串；为空时按本字典keys顺序。all_headers始终返回原字典key列表。它没有每实例独立表头或自动列版本检测，外部修改类表头会影响其他实例。ts原样返回Task Start Time(us)，缺省是字符串`"0"`，并未转成ns；不能与EventBean的ns时间戳直接比较。

CsvHeaders定义八个op_summary基础字段到kernel基础字段的对应顺序：Device_id→Device_id、Op Name→Name、OP Type→Type、Task Type→Accelerator Core、Task Start Time(us)→Start Time(us)、Task Duration(us)→Duration(us)、Task Wait Time(us)→Wait Time(us)、Block Num→Block Num。主线另外定义Mix Block Num、输入/输出Shapes/Data Types/Formats七项additional headers，发布版该常量不存在。已读KernelView辅助方法只将这八项名称投影，保留全部模式返回原表头，否则基础字段加输入中存在的additional字段；这里不升级该消费者的整文件覆盖。

StepTraceBean只保存字典，并把Iteration ID用int转换，缺省-1，非法字符串会抛转换异常。它没有解析开始/结束、建立step区间或把一次迭代变成训练wall time。step构建和重叠处理继续看[step范围与统计](torch_npu_profiler_step_interval_aggregation.md)。

## IntegrateParser拼接不等于统一schema

两版映射NIC→nic.csv、RoCE→roce.csv、PCIe→pcie.csv、HCCS→hccs.csv、AiCPU→data_preprocess.csv、L2→l2_cache.csv、API统计→api_statistic.csv、OP统计→op_statistic.csv、NPU模块内存→npu_module_mem.csv。主线再加入TASK_TIME→task_time.csv与SOC_PMU→soc_pmu.csv。generate_view从ProfilerConfig的parser/bean配置迭代，外部配置是否启用某类、原始CANN文件是否存在另计。

run先初始化logger，再在try内加载ProfilerConfig并调用generate_view；这两步异常时记录错误并返回FAIL/None，正常返回SUCCESS/None。logger初始化本身位于try外，不受这一返回分支保护。主线使用logger.exception保留异常栈，发布使用logger.error。返回成功不证明所有类型都有数据或输出文件。

generate_csv遍历CANN文件集合，逐文件读取Bean、拼接各自row；本方法不排序文件集合，也不按字段名重新对齐每一行。第一份非空数据的第一个Bean.headers确定整份输出header，后续来源即使表头顺序或schema不同也不重排。文件名映射缺项时默认`none`，最后交FileManager.create_csv_file；不由此保证空输入一定生成文件。两版generate_csv完整AST相同。

FileManager读取CSV前先做目录可读性检查；缺少常规文件或文件为零字节时返回空列表。csv.DictReader在try块中构造Bean，读取或构造异常包装为RuntimeError；许多Bean的row/property转换稍后才执行，错误不一定发生在读取try块。**发布版另有超过MAX_CSV_SIZE就warn并返回空列表的分支，主线所审方法移除了该尺寸检查**。这也可能造成同样原始数据在两版得到不同的空结果，不应解释为指标真实为零。

## 使用时先检查字段再解释指标

先保留版本、输入文件集合与实际列顺序，确认每行对齐到同一header，检查是否触发尺寸拒绝、构造异常或空数据分支。随后按源列的us/ms、KB/MB等单位解释数值；相关Bean没有替分析者完成这一层。命中率、PMU指标、通信重叠和端到端时长仍需独立定义、采集配置与真实时间窗口；本卡只覆盖本地投影和整合行为，不宣称底层CANN指标实现、完整解析链或产品能力已全量入库。

## Evidence

本文所依据的完整模块与有界辅助来源如下；未列完整范围的依赖保持独立待审，固定提交不等于设备验证。

- [ac0e156 _ai_cpu_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ai_cpu_bean.py)：1–19。
- [ac0e156 _api_statistic_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_api_statistic_bean.py)：1–32。
- [ac0e156 _common_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_common_bean.py)：1–21。
- [ac0e156 _hccs_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_hccs_bean.py)：1–17。
- [ac0e156 _l2_cache_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_l2_cache_bean.py)：1–18。
- [ac0e156 _nic_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_nic_bean.py)：1–17。
- [ac0e156 _op_statistic_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_statistic_bean.py)：1–34。
- [ac0e156 _op_summary_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py)：1–28。
- [ac0e156 _pcie_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_pcie_bean.py)：1–17。
- [ac0e156 _roce_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_roce_bean.py)：1–17。
- [ac0e156 _soc_pmu_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_soc_pmu_bean.py)：1–16。
- [ac0e156 _step_trace_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_step_trace_bean.py)：1–7。
- [ac0e156 _task_time_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_task_time_bean.py)：1–16。
- [f3ecfe4 _ai_cpu_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ai_cpu_bean.py)：1–19。
- [f3ecfe4 _api_statistic_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_api_statistic_bean.py)：1–32。
- [f3ecfe4 _common_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_common_bean.py)：1–21。
- [f3ecfe4 _hccs_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_hccs_bean.py)：1–17。
- [f3ecfe4 _l2_cache_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_l2_cache_bean.py)：1–18。
- [f3ecfe4 _nic_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_nic_bean.py)：1–17。
- [f3ecfe4 _op_statistic_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_statistic_bean.py)：1–34。
- [f3ecfe4 _op_summary_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py)：1–28。
- [f3ecfe4 _pcie_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_pcie_bean.py)：1–17。
- [f3ecfe4 _roce_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_roce_bean.py)：1–17。
- [f3ecfe4 _step_trace_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_step_trace_bean.py)：1–7。
- [ac0e156 _csv_headers.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_csv_headers.py)：1–9。
- [f3ecfe4 _csv_headers.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_csv_headers.py)：1–7。
- [ac0e156 _integrate_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_integrate_parser.py)：1–76。
- [f3ecfe4 _integrate_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_integrate_parser.py)：1–62。
- [ac0e156 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：29–45。
- [f3ecfe4 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：33–53。
- [ac0e156 _kernel_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_kernel_view_parser.py)：21–40。
