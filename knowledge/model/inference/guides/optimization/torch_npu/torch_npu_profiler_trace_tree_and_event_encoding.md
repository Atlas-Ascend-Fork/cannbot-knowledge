---
type: Guide
title: Profiler trace编码与算子树：时间单位、flow身份和关联边界
description: 解释trace事件的微秒字段、三类flow身份、进程编码与算子树构造，避免把显示连线当作完整依赖或设备同步。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_trace_event_manager.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_trace_event_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py
  role: implementation
created_at: '2026-11-11T05:35:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler trace编码与算子树：时间单位、flow身份和关联边界

本卡完整阅读固定主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的TraceEventManager和TreeBuilder。TraceEventManager两版80行原字节相同；TreeBuilder主线67行、发布66行，enqueue关联条件不同。时间转换函数与TorchOpNode仅核下面列出的直接消费者范围，其他模块不据此升级。没有执行上游、解析采集或生成trace；平台未知，保持draft、空平台。

## X事件的ts是字符串微秒，dur是浮点微秒

`create_x_event`直接取event.name/pid/tid/args，构造ph=X、调用方cat。ts经convert_ns2us_str由整数ns拆成含三位小数的us字符串；dur经convert_ns2us_float除1000成float。args是原对象引用，没有深复制或结构校验。

转换helper先计算abs(ns)并处理正负无穷，再对通过前置计算的有限非int输入抛RuntimeError；不支持abs的对象（如字符串）可能更早抛TypeError，不能把所有非法输入统一描述成经过了类型检查。str版本按字符长度切分，没有通用负数符号处理，例如负的小ns不应被当成它可靠支持的时间格式。这里的格式也不同于[内存raw的整数ns与汇总整数us](torch_npu_profiler_memory_timeline_event_accounting.md)。不能对所有JSON字段统一再除1000或假定ts/dur同一种数值类型。

## 三类flow使用不同身份

| 生成器 | flow id及端点 |
| --- | --- |
| create_torch_to_npu_flow | id=end_event.ts原始值；start/end分别用各自pid/tid/ts，ph=s/f、bp=e、cat=async_npu；不是队列corr_id或完整设备task身份 |
| create_task_queue_flow | id=event.corr_id，name=enqueue_to_dequeue、cat=async_task_queue；ph由调用方传入，函数不证明一对端点齐全 |
| create_fwd_flow | id为输入映射的fwd_id；仅start/end都truthy才创建；start/end tid相同就跳过，没有再比较pid；cat/name均fwdbwd |

每条flow端点的显示ts仍转成us字符串，但id保持其来源字段，不能用显示时间字符串代替原id。生成器不做全局唯一化、跨rank去重或因果验证；缺少配对和同tid过滤后的未显示连线都不能直接推出模型没有前反向依赖。输入构造顺序与框架采集门控见[框架trace输入链](torch_npu_profiler_framework_trace_input_and_join_boundaries.md)。

`create_m_event`先生成Python进程名、CPU标签、FWK排序0三条元事件，再为tid_dict每项生成线程名/排序。普通线程sort_index=tid；标成dequeue的线程都用max(tid_dict.keys())+1，同组可能相同，不是各得唯一末尾序号。空字典只产生进程元事件。GC元事件则用Python GC名、CPU标签、GC排序1及调用方tid。

`get_pid_format`返回`(pid<<10) | (sort_index<<5) | device_id`；没有字段掩码、位宽或负值校验。它是本地显示编号拼装，不能当作任意大整数输入无碰撞的通用进程标识方案。

## TreeBuilder按时间栈建树，返回节点列表

build_tree把event_list与enqueue_list合并后仅按ts稳定排序，先创建合成root；返回实际为`[root, ...TorchOpNode]`列表，尽管签名标注TorchOpNode。列表预分配len(原event_list)+1，依赖队列列表不额外带TorchOp事件的调用约定。时间相同且来自两个输入列表时，原event_list项先于enqueue项。

遇到event.ts严格大于当前非root节点end_time才回到父节点；等于end仍不在这里弹栈。TorchOp直接作为当前节点的子节点并成为last_node，未按pid/tid分开栈，也未独立核验其整个结束区间被父区间包含。因此这里是所采列表上的时间嵌套结构，不是跨线程或设备依赖的证明。

处理非TorchOp（通常enqueue）时，主线要求last_node有event且tid与enqueue相同，才update_corr_id；发布版无这两个条件。调用顺序还会影响最初enqueue是否到达合成root。TorchOpNode.update_corr_id把self id追加当前节点，再沿有parent的节点追加total；最高root的total不在该while中追加。列表允许重复，没有set去重。

## 按ACL时间下探不补全缺失的ID关系

update_tree_node_info令corr_id=acl_ts，经match_child_node逐层下探，匹配路径各节点追加total，最深匹配者追加self；match_self_torch_op沿同样路径返回最深节点，无初始匹配返回None。两函数没有在本地重新检查pid/tid/stream或证明ACL与该算子的真实因果，ACL原时间还在这里作为合成关联id使用。

TorchOpNode.match_child_node按子列表开始时间二分，最终只要求所选child.end_time>ts。特别是只有第一个候选时，没有额外要求ts>=它的start_time，故早于首child开始但小于其end的时间也可能返回首child；恰等于end则不匹配。TreeBuilder建树的`event.ts>end`与查询的`end>ts`是不同边界，不能统一写成任意端点闭区间。

诊断显示归属时，应保留原ns、各类flow id、线程和窗口，先核输入配对，再区分self与total的传播。host耗时与NPU kernel耗时的解释复用[算子耗时归属](torch_npu_profiler_operator_time_attribution.md)；本卡未重建所有上游输入或验证时间嵌套在任何trace都正确。

## Evidence

- [ac0e156 _trace_event_manager.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_trace_event_manager.py)：直接证据范围 1–80；complete main raw text; byte-exact trace pair reused; both complete TreeBuilder texts independently read, full delta inspected。
- [ac0e156 _tree_builder.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py)：直接证据范围 1–67；complete main raw text; byte-exact trace pair reused; both complete TreeBuilder texts independently read, full delta inspected。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：直接证据范围 35–36, 258–279；bounded exact time conversion constants and complete ns-to-us functions only。
- [ac0e156 _torch_op_node.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)：直接证据范围 9–18, 37–42, 73–100；bounded complete child lookup and correlation propagation, constructor/event/end-time consumers; no new whole-file claim。
- [f3ecfe4 _trace_event_manager.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_trace_event_manager.py)：直接证据范围 1–80；complete main raw text; byte-exact trace pair reused; both complete TreeBuilder texts independently read, full delta inspected。
- [f3ecfe4 _tree_builder.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py)：直接证据范围 1–66；complete main raw text; byte-exact trace pair reused; both complete TreeBuilder texts independently read, full delta inspected。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：直接证据范围 38–39, 253–274；bounded exact time conversion constants and complete ns-to-us functions only。
- [f3ecfe4 _torch_op_node.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)：直接证据范围 9–18, 37–42, 73–100；bounded complete child lookup and correlation propagation, constructor/event/end-time consumers; no new whole-file claim。
