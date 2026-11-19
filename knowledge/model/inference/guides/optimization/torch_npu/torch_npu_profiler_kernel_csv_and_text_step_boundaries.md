---
type: Guide
title: Profiler文本CSV：Kernel列选择、字符串归步与迭代输出边界
description: 核对两版Kernel CSV表头选择、字符串时间归步及Text step格式/哨兵/输出门控，避免把成功状态视作完整指标。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_kernel_view_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_kernel_view_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py
  role: implementation
created_at: '2026-11-11T05:56:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler文本CSV：Kernel列选择、字符串归步与迭代输出边界

完整核对固定PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的KernelViewParser、TraceStepTimeParser。主线Kernel95行、发布88行分别全文读；Text step两版188行原字节完全相同。OpSummaryBean与文件/时间helper仅审所列范围；不新增它们整文件资格。整卡draft/空平台，未导入或执行解析器。

## kernel_details.csv来自OP_SUMMARY，不是框架算子表

KernelViewParser加载ProfilerConfig、初始化step_range，再逐OP_SUMMARY文件读OpSummaryBean；按文件给出记录，未在本函数按name聚合、跨文件去重或证明文件集合顺序。框架operator_details的Host Self与关联Kernel求和见[算子耗时](torch_npu_profiler_operator_time_attribution.md)，不能用同一行名等同两张CSV。

每个非空文件以第一行all_headers设置共享类变量OpSummaryBean.headers。all-headers模式保原列；默认模式发布只用OP_SUMMARY_SHOW_HEADERS，主线另保留实际文件中存在的OP_SUMMARY_ADDITIONAL_HEADERS。显示列按登记表一一改成Kernel基础列名，其余列原样保留。最后一个非空文件决定最终output_headers，没有为各文件不同schema另做统一列对齐；类变量也未在结束时自动重置。

OpSummaryBean.row按该共享headers从原字典取值，缺字段填空字符串；headers为空才遍历原字典keys。all_headers返回原字典键列表。空输入最终调用create_csv_file时data为空便不写文件，已有旧产物未由此清理。

## 归步实际比较的是字符串

有框架树但关系kernel字典空时只记错误并返回初始化，不设置step_range；随后仍可生成无Step Id列的Kernel CSV。存在step_range时，框架ns端点经convert_ns2us_str转成us字符串；OpSummaryBean.ts直接返回原Task Start Time字段，默认也是字符串`"0"`。代码使用两端闭区间直接比较，没有在这一层float数值化。

因此默认CSV字符串输入走字典序，只有时间表示满足相应可排序约定时才等价于数值排序；不把可变长度十进制时间的字符串比较描述成已完成准确数值归步。输入字段意外为数值时还可能触发类型比较错误，由run报FAIL。

有step_range就给每行加Step Id，按首个匹配赋值，无匹配仍保留行且Step Id=None；没有step_range则完全不加该列。它不同于Text step聚合的半开区间及不匹配行处理，也不同于按整个Kernel结束时间包含或裁剪持续时间。两版run异常日志写法不同，基本数据分支相同。

## Text step的完整字段、类型与哨兵

Text聚合的全部输入/公式/归步/接收及Db区别见[迭代聚合](torch_npu_profiler_step_interval_aggregation.md)。本卡补该模块完整输出合同：default_time每次新建compute/comunNotOverlp/Overlp/comun/free/stage/bubble/comunNotOverlpRec/prepare九字段字典，step_time_dict返回相应defaultdict；_StepInfoIndex七槽是id/start/end/e2e_start/e2e_end/fwk_start/first_task。

process_labels只有args.labels以NPU开头才建pid→device映射，恰是NPU时device=-1，否则用空格分隔的第二项int转换；没有通用标签schema修复。计时先取pid_device_map[data['pid']]，缺pid映射可在数值检查前KeyError。is_float_num只捕获ValueError；None等造成TypeError时不是“打印Ts or dur format error后跳过”，而是向run传播失败。float可接受NaN/Infinity，本地未另做有限性检查。

每个device深复制step列表，初始e2e与first_task为-1；无step_range则一行None标签和-1哨兵。四类汇总事件至少出现一项才允许继续产CSV，仅hcom_receive不够。计时按开始点归半开step并累加完整dur，不切割跨边界事件；不匹配归None，有明确step_range时输出跳过None行。无明确step时None会匹配默认槽并更新所见跨度。

Preparing仅按首次Computing/Communication起点计算，不是第一次Free或receive；无首任务时-1哨兵没有统一归零保护，可产生没有真实开销含义的数值。Overlapped和Stage按既定差式直接计算，未统一钳成非负，只有ExcludeReceive使用max(...,0)。最终有step时按(device,int(step))排序，非法非数字step标签可使run失败；无step则只按device排序。

run读取树/relation、Torch算子和CANN timeline，初始化日志并捕获Exception；缺分析事件或空输出时可SUCCESS却不写CSV，文件helper也会跳过空data。数值的0、负数、缺行、None标签和解析失败各有不同意义，先检查标签、窗口、输入和实际产物，不能将它们一概解释成等待/计算成本已为零。

## Evidence

- [ac0e156 _kernel_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_kernel_view_parser.py)：范围 1–95。
- [ac0e156 _op_summary_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py)：范围 1–28。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：范围 35–36, 258–265, 268–279。
- [ac0e156 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 62–77。
- [ac0e156 _trace_step_time_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py)：范围 1–188。
- [f3ecfe4 _op_summary_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_summary_bean.py)：范围 1–28。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：范围 38–39, 253–260, 263–274。
- [f3ecfe4 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 74–89。
- [f3ecfe4 _kernel_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_kernel_view_parser.py)：范围 1–88。
- [f3ecfe4 _trace_step_time_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_trace_step_time_parser.py)：范围 1–188。
