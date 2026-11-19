---
type: Guide
title: Profiler trace与折叠栈：flow筛选、追加协议和耗时单位
description: 核对trace裁剪和待补尾JSON追加协议、flow缺失及CPU/NPU折叠栈的Self微秒统计与产物边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_trace_view_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_stack_view_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_stack_view_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_trace_view_parser.py
  role: implementation
created_at: '2026-11-11T05:56:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler trace与折叠栈：flow筛选、追加协议和耗时单位

固定PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。两版TraceViewParser105行、StackViewParser89行原字节相同，完整本地文本及调用分支已核；文件helper、常量仅按Evidence范围读取。draft/空平台，没有生成/解析trace、导出栈或运行设备。

## Trace路径与裁剪不认证全部事件已保留

TraceViewParser构造时按输出路径当时是否已为目录决定：目录用trace_view.json，否则直接用给定路径。其TRACE_VIEW和所读Constant.TRACE_VIEW均为trace_view.json，所以本快照的_temp_trace_file_path与最终路径相同，不是自动创建另一个独立临时文件。

run加载ProfilerConfig，取树（去合成root）、Torch及enqueue/dequeue依赖，再生成视图；没有CANN路径时直接用FwkFileParser生成框架trace，有CANN时追加经_prune_trace_by_level筛选的CANN事件。剪枝按name.startswith(prune_key)，或args.name精确等于prune_key；无配置/空输入原样返回，不做时间窗裁剪、任务唯一性验证或完整性修复。

CANN分支仅有Torch节点时补框架→设备flow，使用的是未裁剪的原CANN列表；所以显示被裁剪不等于用于关联的数据也已删掉，亦不保证所有flow端点都保留在最终事件集。成员_trace_data在这个分支用extend，没有每次generate前统一清空；重复调用同对象不应默认是幂等重新导出。框架入口顺序和身份见[输入链](torch_npu_profiler_framework_trace_input_and_join_boundaries.md)。

## flow有两条互斥关联路线

CANNFileParser.combine_acl_to_npu先把原flow转ACL时间→Kernel。OP_MARK文件不存在时，逐ACL时间调用TreeBuilder.match_self_torch_op，命中才给该节点和每个Kernel生成torch_to_npu flow；存在队列标记时则以dequeue合并到corr_id桶，再逐节点corr_id_self展开。

“有标记文件”不证明队列成功配对；缺映射不会自动走另一条最近邻回退，重复corr_id/Kernel也没有在本循环去重。flow id、微秒字符串和树端点规则见[trace编码与算子树](torch_npu_profiler_trace_tree_and_event_encoding.md)，显示连线不作为完整跨线程/stream因果的证明。

## append是待补尾数组协议，不是通用JSON合并

目标路径已存在就调用append_trace_json_by_path，不存在才create_json_file_by_path。create_prepare_trace_json_by_path的本地协议先写json.dumps(list)去掉最后一个`]`；append则以追加模式写逗号加新list JSON去掉第一个`[`，保留新列表尾括号。它没有解析/验证旧文件、删除旧尾括号、检查重复事件或提供本地原子替换。

静态上，这个协议依赖已有文件确为非空待补尾数组且追加列表非空：已闭合JSON再append可能形成串接内容；追加空list会写`,]`，可能形成尾逗号。文件存在或run返回SUCCESS不能独立证明JSON有效。这里记录的是所读字符串/写入顺序推论，没有实际创建文件或解析复现。

无旧文件且数据为空，create_json_file_by_path直接返回，不生成空数组文件；append本身没有同样的空data返回。路径权限/写入或其他错误可向run传播FAIL，先前已写内容没有通用回滚。不要把这一路径当成任意已有trace的安全追加工具。

## 折叠栈按Self微秒，且会截断

StackViewParser从依赖拿Torch树、Torch事件和dequeue；无CANN路径时重建框架树，去root后无节点直接返回。输出先realpath，后缀不为.log时告警并改成.log，扩展名大小写无统一归一。

metric恰为self_cpu_time_total时取Host Self ns经convert_ns2us_float成us；其他metric走关联Kernel Self dur求和，**但只有metric恰为self_npu_time_total才在初始化中加载Kernel映射及必要的无队列时间补归属。** 因而未知metric不能被理解成可靠的NPU别名；新构造对象的映射为空，可没有有效栈行。

无call_stack或float(total_dur)<=0直接跳过；保留的栈按`;`拆分、每帧strip、逆序再用`;`拼接，写`stack + 空格 + int(total_dur)`。不是CPU样本次数、Total包含时间、设备wall time或纳秒；正的小于1us值会截成0但仍可写行，转换前没有按相同栈聚合去重。重复关联可重复计时，多流重叠未在这里做区间并集。

无有效行时create_text_file_by_path收到空字符串便直接不写，所以SUCCESS/None或没有.log不能证明采集无调用开销。Host与Device耗时关系复用[算子耗时合同](torch_npu_profiler_operator_time_attribution.md)。以上仅覆盖本地视图与所列文件helper，实际flow生产、时钟、文件安全策略和设备性能仍按各自来源验证。

## Evidence

- [ac0e156 _trace_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_trace_view_parser.py)：范围 1–105。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：范围 167–167, 168–168, 218–218, 258–265。
- [ac0e156 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 86–99, 115–127, 143–154, 156–169。
- [ac0e156 __init__.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/__init__.py)：范围 1–1。
- [ac0e156 _stack_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_stack_view_parser.py)：范围 1–89。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：范围 166–166, 167–167, 217–217, 253–260。
- [f3ecfe4 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 98–111, 127–139, 155–166, 168–181。
- [f3ecfe4 __init__.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/__init__.py)：范围 1–1。
- [f3ecfe4 _stack_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_stack_view_parser.py)：范围 1–89。
- [f3ecfe4 _trace_view_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_trace_view_parser.py)：范围 1–105。
