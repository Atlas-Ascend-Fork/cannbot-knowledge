---
type: Guide
title: GE View延迟物化：连续推导、符号与Scope
description: 解释两版GE view辅助层的白名单、FakeTensor模拟、Reshape/Transpose物化、符号来源和连续判断静态边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/continguous.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/continguous.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/continguous_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/continguous_utils.py
  role: implementation
created_at: '2026-11-10T10:27:56Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE View延迟物化：连续推导、符号与Scope

## 固定版本与用途

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的continguous.py、continguous_utils.py，保留源码中的continguous拼写。本卡限定GE view优化的辅助层，不等于全部非连续布局均可转换；产品范围未知，保持draft与空平台，未运行上游或设备实验。

## 白名单只延迟物化指定view

view_white_list仅列aten.permute.default、aten.view.default、aten.transpose.int、aten.t.default、aten.reshape.default，输入位置均为0。ViewFakeTensor保存当前Meta、源shape及字符串符号到图边的映射；set_mapsym要求dict后合并，不产生设备计算结果。

guard_view_input只在config.experimental_config.enable_view_optimize打开时处理；目标可视为view且无scope或仅有superkernel scope时，更新Meta并跳过该目标的普通Converter。其他计算目标或带多流等scope时，先optimize_view物化参数，再进原Converter；关开关时原样进入原函数。白名单、可跳过条件和后端可执行是不同层。

is_view_case首次按symsize推得参考连续stride，与Meta stride不同时才用as_strided及offset=0重建Meta，否则保留原Meta；view/reshape另外从形状Tensor.meta与对应图输入建立mapsym，要求每个符号输出维度都能在映射中找到，否则返回False。并不是遇到任意动态表达式都会直接建节点。

## Meta模拟不搬运数据

_get_npu_outputs_of_view_ops先从view_faketensor.meta或GE Tensor.meta取参数，在FakeTensor模式下调用目标，再浅拷贝原GE Tensor并更新view元数据；GE输出本身不在此执行实际view kernel。主线在detect_fake_mode返回None时新建FakeTensorMode(allow_non_fake_inputs=True)，发布版没有同一回退。

仅接受FakeTensor或tuple/list输出；容器分支复制输入Tensor若干次并共用同一fake描述符，set_ge_outputs递归配Meta，要求两边list/tuple等长并跳过Meta为None的项。这里并不提供Mapping处理，也不能由单输出白名单推导任意多输出结构都正确。

set_meta_tensor_info通过Meta的as_strided创建连续stride参考，不能据此认为真实存储已变连续或storage_offset被实际重置。

## 从延迟视图恢复Reshape与Transpose

optimize_view会解开ValuePack.npu，无view标记则原样返回，list/tuple递归后归一为list；没有通用Mapping递归。源shape与Meta shape/stride完全相同时直接返回，随后以(源GE Tensor,Meta Tensor)查缓存，物化后保存缓存并恢复原GE Meta。

静态目标形状用INT64 Const加Reshape；动态目标逐维取常量、view_operator_map已有节点或get_sym_node_from_graph。后者优先按mapsym逆序找图中节点，否则仅在符号位于源shape时从Shape(INT32)加Gather取维，找不到则AssertionError。Pack全输入host时写_inputs_all_sym，force_op_unknown_shape只是属性标记，不独立证明完整动态范围已支持。

非连续推导剔除stride为0或shape为1的轴，以stride/shape的hint排序并计算perm，按需要执行源Reshape、Transpose及目标Reshape；无需transpose时仍可Reshape。它不是任意as_strided、空布局或重叠存储的通用实现。gen_contiguous_storagesize为空shape返回1，gen_contiguous_stride为空shape返回[]，均只接受list/tuple。

## 连续判断的实参与空列表边界需保留

源码is_contiguous声明参数顺序为(stride,shape)，但optimize_view调用为is_contiguous(meta_shape,meta_stride)；两版都有这一表达式。函数本身在长度<=1时直接True，其他情况检查末stride和相邻乘积，并使用hint_int。这是静态发现的参数顺序疑点，不能照注释宣称它等价于torch.Tensor.is_contiguous；本次没有执行反例或声称已复现错误。

_build_valid_stride过滤后直接访问simple_stride[0]，没有单独空列表保护；是否可达取决于前面的返回与调用域。主线hint_int导入失败时使用optimization_hint，发布版直接导入hint_int；hint与真实动态范围验证分开。

## Scope、元数据与性能验收

只有superkernel scope时，optimize_view_args_and_kwargs记录新建GE节点并应用scope属性；其他scope按前述路径及时物化以保持所属范围。设置scope标签或减少view节点不能独立证明切流顺序、存储别名和性能收益。

应用时核对精确目标/overload、源shape/stride/offset、符号mapsym、scope、是否触发Transpose以及缓存复用；在匹配栈对输出值与存储语义做验证，再测端到端收益。本次只完成两版静态合同审阅。

- [GE View配置与编译调优](ge_compile_optimization_controls.md)
- [FX元数据容器与ValuePack](torchair_fx_value_pack_metadata.md)
- [自动函数化与写回](torchair_ge_auto_functionalized_views.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/continguous.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/continguous.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/continguous_utils.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/continguous_utils.py)（implementation）
