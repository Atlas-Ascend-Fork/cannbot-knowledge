---
type: Guide
title: GE引用复制与副作用：消除条件和排序边界
description: 核对硬编码ref映射、TensorMove/Assign删除门槛、输出输入索引疑点及限定副作用和Cmo的图内顺序。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/graph_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-10T10:53:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE引用复制与副作用：消除条件和排序边界

## 固定版本与范围

全文核对TorchAir发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013与主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的graph_pass.py。本卡限定引用复制删除和图内排序，不将控制边、源码注释或节点变少当作真实存储/多流/跨rank正确性证明。产品范围未知，保持draft与空平台，未执行上游或设备实验。

## ref对应关系是硬编码名单

_get_output_to_input_ref_idx为Scatter、QuantUpdateScatter、ScatterNdUpdate、FfnWorkerScheduler、AttentionWorkerScheduler配置输出0到输入0；ScatterList逐项同索引；ScatterPaKvCache为0→1、1→4；MlaPrologV3为2→9、3→10；KvRmsNormRopeCache为0→5、1→6；GatherSelectionKvCache前4项同索引；RecurrentGatedDeltaRule为1→4；QkvRmsNormRopeCache为0→6、1→7、2→8。发布另有FusedCausalConv1d的1→2，主线没有同一映射项。

名单不表示其他节点完全不原地，只表示此pass没有用同一硬编码关系处理。来源构图原型、Schema和运行时真实ref仍需配套核对。

## TensorMove/Assign消除需要完整消费者条件

_find_ref_ops_and_io_ops记录Data、TensorMove、Assign、NetOutput与ref输出。Data消费者计数忽略Cmo，ref输出消费者另行统计，NetOutput成员也单独记录；它依赖图中有可用NetOutput。

optimize_reference_op_redundant_copy只有在Assign目标为Data、源为名单ref输出、该ref输入为TensorMove、TensorMove源是同一Data且Data计数恰为2时尝试删除。ref输出是网络输出或引用计数为1时仅删TensorMove、保留Assign；否则删两者。返回ref_data_idx会收集Assign目标Data索引，包括后来没有成功消除的项，不能把返回列表等同成功优化清单。

静态疑点须保留：ref_op_info保存的是output_id及ref_input_name，真正改写却用ref_op.input[output_id]，没有保留并使用原硬编码的input_id。对于输出/输入索引不相同的映射，不能依据注释宣称一定改写正确输入；本次未运行反例，也不声称已复现错误。

## 副作用排序只覆盖明确类型

explicit_order_for_side_effect_nodes把PrintV2、AttentionToFFN、FFNToAttention按原图次序串控制边，并将末节点连向NetOutput防止裁剪；不是所有Hcom、自定义回调或原地算子都在这份集合中。

特别是没有上述副作用节点时函数直接返回，后面的graph_output_ref_input处理也不执行，不能概括成无论何种输入mutation都会增加顺序边。有副作用节点时才按输出到输入索引映射定位写入节点，并根据副作用节点读取输入的关系，按原图先后补边；PrintV2可递归查看StringFormat输入。

这些规则不等同任意数据依赖、别名和多流分析，也不在这里证明无环、没有遗漏其他副作用类型或真实设备已完成同步。

## Cmo单独保序

explicit_order_for_cmo独立按原图次序串Cmo并把最后一个接到NetOutput，没有在此给Cmo与所有RefOp之间加同一顺序边。注释称二者可并行是设计前提，不能作为本次实验结果；它和引用优化中“不计Cmo消费者”一起要求匹配的系统语义。

## 验证

核对精确ref映射、输入/输出索引、Data与ref计数、NetOutput和剩余Assign；对副作用类型、原图次序、图输出ref映射及Cmo分别检查。实际后续mutation、共享Storage、多次调用、跨流顺序和性能须在匹配栈验证，本次只做静态全文与版本差异审阅。

- [自动函数化的base复制与ViewCopy](torchair_ge_auto_functionalized_views.md)
- [GE输入与固定权重重写](torchair_ge_input_rewrites.md)
- [FX层Noop/Cat/重新原地化](graph_noop_cat_and_reinplace_passes.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/graph_pass.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
