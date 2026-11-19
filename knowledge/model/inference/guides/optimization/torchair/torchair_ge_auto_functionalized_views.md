---
type: Guide
title: GE自动函数化：视图重建、base复制与写回
description: 区分两版自动函数化的布局相等、AsStrided与ViewCopy路线、ref输出查找、返回结构及主线内部mock边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_functionalized_v2.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_functionalized_v2.py
  role: implementation
created_at: '2026-11-10T10:27:56Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE自动函数化：视图重建、base复制与写回

## 固定快照与范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的auto_functionalized_v2.py。本卡解释自动函数化的GE视图重建、base复制与写回；主线新增内部mock路线单独记录，产品范围未知，保持draft与空平台，未导入上游或运行设备用例。

## 先复制base，再重建mutable参数

conveter_auto_functionalize_v2从kwargs弹出_all_bases与symbol_input_map，取args[0]为_mutable_op，通过Torch私有get_mutable_args/read_view_information_from_args获得视图信息。每个base先TensorMove并set_meta，再据ViewInfo重建mutable关键字参数，而不是直接把原base交给原地算子。

函数运行时会给AsStridedViewInfo、SliceViewInfo、AliasViewInfo和NotView类赋regenerate_ge_view/view_copy方法；赋值位于共享类对象，没有在本函数结束时恢复旧方法。它依赖相应Torch私有类型，不能由函数名或文件存在推断任意Torch版本均兼容。

mutable参数None时写None，list时逐项保留None或重建视图，普通单视图才显式传symbol_input_map；list分支调用没有传同一映射。不能据“支持list”忽略符号映射和后续写回的不同路径。

## 视图相同与AsStrided重建

_tensors_layout_equal同时比较size、stride、storage_offset，不能仅按shape相同跳过。Slice/AsStrided/Alias先在detect_fake_mode(None)上下文计算Meta；此文件没有编译入口中FakeTensorMode为None时的新建回退。

Meta布局完全一致时标记_layout_equal并直接返回复制后的base；否则Slice将输出size/stride和offset经符号计算辅助层转图值后建AsStrided并set_meta。AsStrided路线使用既有size/stride/offset并set_meta；Alias路线也建AsStrided，但这个分支没有相同的显式set_meta调用。这里只记录不同调用，不将其写成已复现执行错误。

_sym_list_to_ge_tensor全是Python int时直接返回原列表；否则逐项委托infer_ge_output_by_symbol_calculate，再Pack、set_meta，全部host时标记_inputs_all_sym并force_op_unknown_shape。符号计算的支持域需另查对应实现；本卡不由委托函数名宣称任意表达式可运行。

## 普通Converter与主线内部mock不能混用

普通路线通过get_or_auto_gen_converter取得_mutable_op的Converter，仅用重建后的kwargs调用，再对本次新建节点调用infer_and_gen_sym_shape_silent。发布版只有这一普通路线。

主线另有_conveter_auto_functionalize_v2_internal_mock关键字：_extract_schema_info按Schema顺序取参数名，靠类型字符串是否含Tensor识别张量，返回值无名时取output_i；mock路线仅收集GE Tensor或全Tensor列表，其他值记None，并用ge_op构造模拟节点。非Tensor属性未被同样编码，字符串类型识别也不是完整Schema验证；这个内部模拟节点不证明真实IR、Converter或kernel已交付。

两条路线都对新增节点做静默符号形状推导；实际推导结果与回退机制不能从silent命名直接断言成功。

## 写回由最后节点控制，返回结构有精确条件

算子转换后取graph.op[-1]为control_node，以ControlTensor作为后续写回依赖；它假设本次转换产生可用的末节点，不能泛化为完整多节点别名推导。

_view_copy在_layout_equal时转_not_view_copy；否则对目标base和重建的_as_strided做ViewCopy，源连续stride由size计算，源offset为0，目标保留视图stride/offset。若size是GE Tensor，按其symsize[0]推源秩并构建Pack，需有可用秩。

_not_view_copy按末节点输入边找base，再以input_desc.name寻找同名output_desc，找到则返回该ref输出；找不到会警告并用带控制依赖的Identity保留base。它有利于后续pass消除TensorMove，但本文件没有直接证明复制节点已被删除或性能已改善。

最终写回循环遍历args_view_info.values()并直接调用view_info.view_copy，没有在这里逐项展开list或跳过None；虽然前面重建分支处理过list/None，不能据此宣称这两类输入在完整函数均有对称覆盖。这是静态边界，未运行反例。返回值若out为tuple则展开原输出再追加更新base，否则将out作为单项后追加；list输出并不按tuple规则展开。

## 验证与相邻主题

核对Torch私有ViewInfo版本、base_index、shape/stride/offset、symbol_input_map、Converter末节点的ref命名和控制依赖，再分别验证普通视图、布局相同、None/list和多输出路线；mock节点不能充当真机结果。需要实际精度、别名和性能结论时另做匹配栈实验，本次未执行。

- [Schema、Meta与函数化交付](../../integration/torchair/custom_operator_graph_contract.md)
- [View延迟物化](torchair_ge_view_materialization.md)
- [Converter注册生命周期](torchair_ge_registration_prims_lowering.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_functionalized_v2.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_functionalized_v2.py)（implementation）
