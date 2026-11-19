---
type: Guide
title: TorchNPU Profiler的配置装载、时钟校准与保留状态
description: 区分计数转换、时钟来源、配置残留和Bean候选的双版本差异。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiler_config.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-11T07:06:23Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler的配置装载、时钟校准与保留状态

## 固定来源和装载顺序

固定PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`，完整核对ProfilerConfig双版定义。时间转换的Bean端合同沿用[框架二进制字段](torch_npu_profiler_framework_bean_wire_formats.md)，本卡补齐配置来源、失败及状态；没有读取真实采集文件、执行解析或验证外部时钟。

ProfilerConfig经Singleton装饰。初始Level0、AiMetricsNone、Text导出、data_simplification=True；L2/msprof_tx/op_attr/sys_io/sys_interconnection和syscnt均False，rank=-1、activities=[]、localtime_diff/time_offset/start_cnt=0、freq=100.0。data_simplification/export_type/activities/msprof_tx/rank等property直接返回当前值，列表没有复制；export_type setter也直接赋引用。

load_info若_is_load真就返回；否则先读info JSON，依次load_activities、rank、experimental、timediff、syscnt，全部完成才_is_load=True。主线另有reset_is_load，仅清这个布尔，不重建对象或清全部字段；发布无这个本地方法。中途异常不回滚前面写入，重试也可能从部分修改的对象开始。配置所属路径/调用流程见[解析计划](torch_npu_profiler_analysis_pool_parser_plan_and_done_marker.md)。

_get_json_data缺路径或JSONDecodeError返回{}并警告，但FileManager读取异常、合法JSON的错误类型等不统一转空字典。activities直接取嵌套JSON对象引用；CPU/NPU活动声明存在而对应FWK/CANN路径没有时，打印错误并remove该活动，没有自动补齐数据。remove一次不能当作完整去重/类型规范化。rank每次缺项回-1；多数experimental缺项却沿用当前字段值，可能保留此前Level/指标/flag，不是重新采用构造默认。

## 原始计数到本地时间分两步

TorchOpBean起止路径明确先get_timestamp_from_syscnt，再get_local_time，结果保存在_start_ns/_end_ns。启用计数转换时公式为`int((syscnt-start_cnt)*(time_fmt/freq))+time_offset`，time_fmt默认1000；其后为`int(monotonic_time+localtime_diff)`。先截断计数差的缩放结果、再加offset，与对整个表达式一次取整不可任意互换。freq的实际单位必须匹配采集上下文，函数没有统一验证来源单位，不能只凭字段名给未知输入补校准。

主线按not syscnt_enable决定是否原样返回，发布按syscnt_enable==False；正常布尔配置一致，None/空字符串等错误类型不能笼统视为完全相同。转换仅显式拒绝abs(freq)<1e-15，不检查正频率、计数单调、所有参数类型/有限值；负频率或错误类型不是本地已验收的正常配置。

load_syscnt_info从start_info读syscnt_enable。找到info_path时读CPU[0].Frequency，is_number(str(value))成立才float；只有没info_path才从start_info.freq回退。找到但JSON坏、Frequency不合法，不会自动走else回退，可能保留旧freq；只捕JSONDecodeError，CPU缺失/空列表/错误嵌套类型等可传播。

找到host start log就用ConfigParser取Host.clock_monotonic_raw与cntvct，检查字符串后int；没有log才取start_info.start_monotonic/start_cnt并沿用缺省旧值。is_number接受有限长度十进制/指数形式和符号，非str打印错误返回False；但它不保证后续int(string)能接受，例如'1e3'或'1.2'通过正则后仍可能转换失败。找到log却字段无效也不自动切回start_info。

## 本地时钟差的零值与回退

NPU活动存在时先取CANNFileParser.get_localtime_diff：缺CANN/start info返回0，否则literal_eval文件，将collectionTimeBegin经convert_us2ns后减int(clockMonotonicRaw)，异常记日志并保留0。convert_us2ns是字符串拼接式微秒转纳秒，最多保留三位小数，不是通用浮点/指数解析器。

ProfilerConfig随后仅在localtime_diff为假且end_info非空时，取int(collectionTimeEnd)-int(MonotonicTimeEnd)。**真实差值0也会触发回退**；若本轮没有NPU活动且对象留有非零旧差值，它也不会被这段自动清零。不能把所有采集时间直接当同一epoch，也不能把回退0等同外部时钟已经同步。本文未打开数据库或实测设备校准。

## Bean候选、Level与导出规范化

两版Level_none基表为空；Level0基表为NpuModuleMemory，Level1再含OpStatistic/APIStatistic，Level2再含AiCpu。主线在Level0/1/2均额外加入TaskTimeBean，发布没有。L2标志追加L2Cache；主线还追加SocPmuBean。sys_io追加NIC/RoCE，sys_interconnection追加PCIE/HCCS；这些追加在基表之外，所以Level_none不意味着get_parser_bean一定返回空。

get_parser_bean直接将LEVEL_PARSER_CONFIG.get(level)与附加列表相加，未知level没有本地空表回退；get_prune_config未知level返回None。剪枝表只有Level0列CANN、AscendCL、Runtime、GE、Node、Model、Hccl、acl_to_npu、Communication@，其余已列Level为空；它只是返回规则，不证明此方法已经删除所有这些事件。is_all_kernel_headers仅判断是否不等Level0，不能视为完整Level白名单。

从profiler_info取export_type先用当前导出值作缺省。假值回Text；str转单元素list，list经set去重，去重异常或其它类型回Text；只接受text/db成员，否则整体回Text。列表顺序不保留，也不表示外部CANN具备所选能力；公开analyse参数、_ExperimentalConfig构造和这里的文件配置归一化不能混为同一入口。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiler_config.py)（1–320行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（1–9行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)（270–290行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py)（125–131行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（142–153,282–294行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiler_config.py)（1–249行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（1–10行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)（195–210行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py)（125–131行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)（141–152,277–289行；有界辅助）
