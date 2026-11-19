---
type: Guide
title: Profiler内存数据流：schema匹配、可变输入与版本边界
description: 解释内存分析如何用已采参数匹配运行环境schema、聚合可变性并建立Tensor版本，区分未知、释放和真实分配。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: implementation
created_at: '2026-11-11T05:35:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler内存数据流：schema匹配、可变输入与版本边界

本卡完整阅读固定主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的本地内存时间线模块，并与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`逐行及完整AST对照。两版1099行去行尾空白后相同；唯一严格AST差异是分类说明docstring的一处尾空格，技术含义相同。这里解释SchemaMatcher、DataFlowEdge/Node/Graph；外部`torch._C`已注册schema的内容取决于实际分析环境，未执行其查询或任何采集解析。平台未知，保持draft、空平台。

## schema从分析环境补取，不是已采到的执行签名

SchemaMatcher把TorchOp输入转成签名：Tensor元数据变成TensorKey，一层Tensor列表逐项变成key，其余值保留。TensorKey须同时有tensor_id、allocation_id、ptr并包含设备；缺任意身份字段返回None。这会影响匹配结果；不能因原事件名字像Tensor算子就假定元数据齐全。身份的生产另见[指针和分配周期](torch_npu_profiler_tensor_storage_identity.md)。

`lookup_schemas`只查询带`::`的名字，调用运行环境的`torch._C._jit_get_schemas_for_operator`；缺命名空间或该调用抛RuntimeError返回None。它没有绑定采集时那一套外部Torch/扩展schema；本地代码也未将所有异常统一转换为“无匹配”。随后先要求观测输入数恰等于schema.arguments数，再逐项匹配，未补齐缺省参数或按关键字重排。

| 目标schema类型 | 当前匹配条件 |
| --- | --- |
| Optional | 观测值恰是字符串`"None"`，或递归匹配元素类型；不把所有Python None都当成Optional Tensor匹配成功 |
| Any | 无条件通过 |
| Tensor | 必须是有效TensorKey |
| Tensor列表子类型 | 必须是list，所有元素为TensorKey；空list的all检查通过，不递归证明任意嵌套列表 |
| 其他类型 | 只排除TensorKey和list；未精确核验int/float/bool/string之间的标量区别 |

所以这是按记录形状近似匹配的分析规则，不是重新执行算子、唯一重载证明或运行时别名证明。名字相同而元数据不全，可能无匹配；多个标量重载也可能同时匹配。

## 可变性有两层合并，未知不总是统一“写入”

匹配到多个schema时，`inputs_are_mutable`对每个参数的alias_info.is_write取OR；无任何匹配则每个输入返回None。DataFlowNode再遍历整个所选事件子树，把同一TensorKey在直接输入或一层列表输入中得到的标志收成集合。

边的`mutated`恰在集合包含True，或集合仅为`{None}`时为True；`{False, None}`不满足这两项，结果为False。不能泛化成“只要有一次未知就当成写入”，更不能将静态is_write推断当作采集已证明发生了原地变更。

## 边按输入、释放、分配的顺序构造

DataFlowEdge默认input_version=None、mutated=False。`is_allocation`只检查input_version是否None，`is_deletion`只检查mutated是否None；这两个标签是边状态，可以同时成立。

1. 先处理Tensor输入：有效key从图中lookup当前版本，未见key默认版本0，按上述集合推断mutated。
2. 再处理alloc_size<0的释放：即使先前不在输入表，也补输入边；设mutated=None、记当前版本。
3. 最后处理alloc_size>0的分配：设input_version=None，保留前一步的mutated状态。因此同一节点子树中创建又删除的key可同时是allocation/deletion。零大小事件不属于这两步的正/负分配分支。

无效key最终被滤掉，剩余边按TensorKey排序。输入视图只含非allocation边，把mutated转成bool，所以删除边作为输入呈False；输出是未删除的新分配（version0），或被判定变更的输入（旧version+1）。同时创建/删除的中间量只出现在intermediates，不作为正常输出；它们供[临时量分类](../../../../training/guides/torch_npu_profiler_memory_category_inference.md)使用。

DataFlowNode构造后，仅对mutated且非allocation的边递增图的active_version。图没有在所读删除分支清除版本表；版本与TensorKey/分配周期一起解释，不能按版本数字直接计数底层申请。版本迁移如何扣旧类别、加新类别见[事件字节累计](torch_npu_profiler_memory_timeline_event_accounting.md)。

## 数据流叶子不是事件树的所有末端

DataFlowGraph先做部分DFS：TorchOp处于BACKWARD_FUNCTION，或其SchemaMatcher有匹配，就把它当作本图叶子；Allocation也单独入图。这些节点不继续向下选择图顶点，但DataFlowNode仍完整遍历其子树以收集输入和分配。未匹配schema的普通包装事件可继续下探，避免把整个Python上下文一概当成一个算子，也不保证最终选中最底层kernel。

叶子先按start_time_ns排序，再依次构造节点和版本，完成后flow_nodes再按start_time排序；同时间没有额外拓扑、stream或设备完成次序判据。start_time取所选事件开始时间，不是显存申请时间或NPU耗时。

validate仅检查输出(TensorKey,version)是否被多个节点创建；发现重复集合中含NPU key便警告并return，不抛统一完整性错误、不修复或回滚图，CPU重复不触发这条警告。图建立成功不足以证明采集完整或分类准确；缺失身份、schema和分配记录仍需分别核查。

本卡覆盖本地匹配和数据流定义。EventTree的事件恢复、外部Torch schema/type实现、真实操作是否写入、所有设备/进程因果关系仍依赖各自证据；未做分类精度、内存或性能实验。

## Evidence

- [ac0e156 _memory_timeline_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)：直接证据范围 75–142, 281–544；main complete 1099-line raw text read; release all raw line deltas checked, rstrip-lines exact; strict AST differs only one CategoryElement docstring trailing space; local technical meaning preserved。
- [f3ecfe4 _memory_timeline_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)：直接证据范围 75–142, 281–544；main complete 1099-line raw text read; release all raw line deltas checked, rstrip-lines exact; strict AST differs only one CategoryElement docstring trailing space; local technical meaning preserved。
