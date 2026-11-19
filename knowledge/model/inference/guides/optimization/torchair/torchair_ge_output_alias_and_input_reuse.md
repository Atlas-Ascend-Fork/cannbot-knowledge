---
type: Guide
title: GE输出别名、符号结果与输入存储复用
description: 解释FX返回值如何从GE输出、输入视图和符号表达式重建，以及Assign输出绑定、CPU复用限制与非连续输入写回。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
created_at: '2026-11-10T11:19:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE输出别名、符号结果与输入存储复用

## 固定版本与范围

定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的parse_output、ViewOfInput、SymOutput、Assign映射、运行和复用选项，相关语义一致。本卡仅有静态证据，未运行Tensor别名、原地更新或性能实验；产品矩阵未知，保持draft与空平台。

## FX返回值数量不同于GE图输出数量

parse_output先按FX位置保存返回项。非ge.Tensor项保留原值；符号meta转为SymOutput；与某个FX Tensor输入meta经torch._C._is_alias_of判定别名的输出转为ViewOfInput。以上后两类不加入常规GE输出列表。

其余ge.Tensor按tensor边名称去重，只把首次出现的边加入_outputs，并记录每个FX位置到GE输出位置的映射。重复返回同一边不会因此产生两个独立GE输出缓冲。运行结束先计算SymOutput/ViewOfInput，再填回GE输出，最终返回FX顺序的tuple；不能直接以NetOutput个数推断用户返回对象数量或独立存储数。

## 输入视图和符号结果在返回时重建

ViewOfInput保存FX输入索引与输出meta的shape、stride、storage_offset表达式。普通路径从本次真实FX输入执行as_strided，表达式值由符号输入映射计算；实数/复数互视图分别调用view_as_real或view_as_complex。此处没有clone，不应把这类返回值当成与输入隔离的快照。

SymOutput同样从输入符号映射求表达式值，而不是要求GE再返回一个设备Tensor。该机制只重建已登记的符号表达式和别名，不表示支持任意依赖设备Tensor内容的动态输出大小，也不表示对所有运行期分支重新做别名分析。

## Assign可转换为输出写回输入

_mapping_assign_op_to_graph_output先收集Data输入。Assign目标是这些Data时，把对应NetOutput输入改为Assign的value边；若该值还没成为输出，就补入一个输出和dtype，建立GE输出索引到GE输入索引的映射，然后删除相应Assign。目标不是这些Data时保留Assign，并把其控制边附到NetOutput，不能把两种情况都理解为删除了写操作。

__call__为映射输出构造assigned_outputs，将相应位置直接设为本次GE inputs里的Tensor，其余位置为None，再传给graph.run。这里的输入是处理后的GE inputs，和ViewOfInput使用的原FX args要分别跟踪。对于记录为非连续输入处理且属于_ref_data_idx的项，运行后还会把处理后的GE Tensor copy_回原FX输入；输出重建发生在这步之后。

## 内存复用选项与CPU限制

_normalize_ge_option把未映射到输入的常规输出位置写入ge.exec.outputReuseMemIndexes；存在输入输出映射且检查通过时，另外设置ge.exec.outputReuseInputMemIndexes，条目顺序为input_idx,output_idx，并用竖线分隔。

检查函数查看_input_placements：任何被复用输入的placement为HOST，或其索引超出已知placement列表，都会跳过整项outputReuseInputMemIndexes设置。它没有在函数体中独立检查输出描述或所有设备能力；不能仅因该检查返回False便断言任意输入输出布局组合都可复用。此选项被跳过也不等于上层assigned_outputs绑定或其他复用选项被全部关闭。

评估显存与原地语义时，分别验证输入别名、重复输出、Assign更新、非连续输入写回、CPU/未知placement及跨次调用保存结果。需要独立保存结果时由调用方按实际别名/生命周期需求处理；本卡未证明所有GE输出会在下次调用覆盖，也未测量复用收益。

- [引用复制与副作用排序](torchair_ge_reference_copy_and_ordering.md)
- [GE动态shape范围](torchair_ge_dynamic_shapes_and_fa_tiling.md)
- [首次调用运行时序](torchair_ge_runtime_binding_and_first_call.md)
- [捕获后端的内存池与clone](npugraph_ex_memory_pool_and_clone.md)：后端实现分别核对。

## Evidence

- [主线输出与复用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（primary）：159–235、760–812、1214–1254、1281–1294、1596–1653、1954–1991。
- [发布输出与复用](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：68–141、581–634、__call__与parse_output对应函数、1564–1602；完整定向范围见入库清单。
