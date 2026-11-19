---
type: Guide
title: TorchNPU DTensor重分布、逐点策略与版本注册
description: 说明位置与关键字参数重分布、非参与rank结果、逐点注册及旧版mesh展开补丁。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_common.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_pointwise_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_view_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_common.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_pointwise_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_dtensor_patch.py
  role: implementation
created_at: '2026-11-11T06:29:26Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU DTensor重分布、逐点策略与版本注册

## 实现与外部依赖边界

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。本组覆盖包初始化、_common、_pointwise_ops，以及主线_view_ops和发布_dtensor_patch的本地逻辑。未导入运行上游；矩阵、attention、math、MoE与experimental的包导入仅作为注册依赖，不由本文认定它们的全部策略完成审阅。

## 位置参数与关键字参数分开重分布

get_redistributed_local_args仅在needs_redistribute成立时调用DTensor dispatcher的redistribute_local_args，再按args_tree_spec恢复位置参数树，否则直接取local_args。主线向dispatcher额外传use_val_from_redistribute_schema，发布快照不传；不要跨版本照抄内部调用签名。

get_redistributed_local_kwargs根据传入的kwargs_spec_infer_func推导目标，而非假设位置参数的redistribute_schema已经包含所选策略的关键字参数布局。它遍历推导结果中的键，取原始kwargs schema和local值；目标为DTensorSpec且placements不同才调用redistribute_local_tensor，否则保留该值。返回新字典，函数自身不把未由推导器列出的键自动补回，也不修改op_info.local_kwargs。

当目标为list/tuple且schema_info.needs_pytree成立时，按zip逐元素处理并返回list；源码没有等长检查或任意深层容器递归。该局部判断只比较placements，不是对mesh、dtype、shape和kwargs正确性的完整校验。转换是否触发实际通信取决于外部重分布实现与布局。

## 不参与mesh的rank返回什么

get_empty_local_results在output_spec为None时返回None。存在DTensorSpec时要求tensor_meta：零维shape生成具有该dtype的零标量Tensor，其余shape生成空Tensor，而非全局shape的零Tensor；未显式指定NPU设备。有Sequence输出时逐项构建list，None项会进入不支持返回类型的检查，缺少tensor_meta则报RuntimeError。它并不执行算子来为非参与rank计算真实结果，不能当作普通有效输出参与误差比较。

## dtype cast与普通逐点策略分别注册

两版将npu_dtype_cast、_npu_dtype_cast及各自backward四个default入口交给逐点策略。发布快照直接导入pointwise_strategy，回调传linearity=0，注册携带static_kwargkey=["out"]。

主线先尝试导入pointwise_strategy，ImportError时使用_single_dim注册器。旧接口存在时四个cast仍传linearity=0，普通组直接用pointwise_strategy；新分支对cast传_ALL_PARTIAL_BINARY_PRESERVING_RULES，普通组不传这组规则。普通组完整列isclose、isfinite、fast_gelu、npu_fast_gelu、npu_layer_norm_eval和npu_fast_gelu_backward。这里记录的是注册选择，不把linearity参数或规则名等同于已做数学线性、溢出与数值误差验证；外部策略算法没有在本组核对。

主线_view_ops另把npu_transpose.default映射到torch.permute的策略映射器。本地六行没有实现新的任意view/transpose布局证明，也不定义实际张量转置是否产生拷贝。

## 发布快照补丁的kwargs与多维mesh展开

发布包先导入_dtensor_patch，再导入pointwise/matrix/attention/math/MoE/sharded模块。补丁为旧OpSchema提供kwargs_strategy属性：needs_pytree成立时取tree_leaves，否则遍历kwargs_schema.values，只保留OpStrategy。

expand_to_full_mesh_op_strategy把单mesh维策略在mesh.ndim上做笛卡尔积，按列组装DTensorSpec或None；从input_index处分出输入，并串接位置参数和关键字参数策略。输入spec数与输入策略数不等时报AssertionError；inplace_op只接纳与第一个输入当前策略的首个output_spec placement一致的候选。之后依次检查每个输入是否可分片、可选op过滤回调，计算逐输入重分布成本，再创建OpSpec。input_index>1时输出为tuple，否则要求第一个输出spec非None；第一个输入不存在等畸形调用没有额外的完整参数防御。

成本由外部generate_redistribute_costs生成，不是本地测量结果；候选过滤也不证明组合性能最优。TupleStrategy的pytree注册把childs作为子节点，重复注册引发ValueError时忽略。

## 版本判断保持源码原义

发布_apply_dtensor_patch直接判断torch.__version__ < "2.10"及torch.__version__ < "2.9"；前一条件成立时按需补kwargs_strategy并覆盖全局expand函数，后一条件成立时注册TupleStrategy。本地没有把torch.__version__强制转成str；比较语义由所加载版本对象的比较实现决定，不能仅因右侧为字符串字面量就认定按词典序排序。补丁在模块末尾导入即调用，没有本地回滚机制。

主线包不再从此初始化文件导入_dtensor_patch，另外增加_view_ops及experimental导入。缺少同一路径只说明注册组织发生变化，不证明主线没有其他兼容实现。集成时固定Torch/TorchNPU版本，检查实际策略选择、kwargs布局、Partial归约和通信；避免混用两版私有补丁。能力清单仍见[原生张量并行约束](torch_npu_native_tensor_parallel_constraints.md)，MoE具体布局见[隐藏维策略](torch_npu_dtensor_moe_hidden_sharding.md)。
