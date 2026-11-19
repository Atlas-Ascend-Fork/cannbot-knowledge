---
type: Guide
title: 原生FX与符号形状：FP32条目和方法级产品范围
description: 区分Graph/Node/Tracer的类型表、950DT例外、实验性ShapeEnv及SymInt前提，不替代TorchAir Pass合同。
tags:
- task.implementation
- topic.compilation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-fx.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-fx-experimental.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-fx-experimental.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
created_at: '2026-11-09T12:39:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生FX与符号形状：FP32条目和方法级产品范围

## 固定来源与适用范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文支持页，逐项保留类、方法、函数与文档版本差异；不回推26.0/PyTorch2.8发布组合，也不从TorchNPU与TorchAir各自主线推定两者配套。产品按A2/A3训练系列与950DT条目区分，不扩展950PR。清单未收录不等于已证实不支持；未列出的参数与组合不自行补齐。本次仅静态审阅，未执行上游、导出、编译或设备实验。

## FX对象与局部FP32表

symbolic_trace、wrap、GraphModule与Node主条目及下表方法标注input仅FP32，列三类产品。对象/图工具的笼统input字段按条目保留，不推出“所有FX节点、参数和模型只能FP32”；同样不能仅因为工具管理的是图元数据就忽略支持页的限制。

| 所属对象 | 标注FP32的方法 |
| --- | --- |
| GraphModule | __init__、add_submodule、delete_all_unused_submodules、delete_submodule、to_folder |
| Graph | lint、node_copy、nodes、on_generate_code、print_tabular、python_code |
| Node | append、format_node、is_impure、replace_input_with、update_arg、update_kwarg |
| Tracer | call_module、create_args_for_root、create_proxy、iter、keys、proxy、to_bool |
| Interpreter | call_function/call_method/call_module、fetch_args_kwargs_from_env、fetch_attr、get_attr、map_nodes_to_values、output、placeholder、run_node |
| Transformer | call_function/call_module、get_attr、placeholder |

Graph、Tracer、Proxy、Interpreter、Transformer及其余已列子方法只有产品表时，不补造另一份dtype表。Graph的节点创建、插入/删除/复制、输入输出与代码生成；Node的args/kwargs、链表邻接、替换使用、stack_trace；Tracer的create_arg/create_node/getattr/is_leaf_module/path_of_module/trace；GraphModule的code/graph/recompile/print_readable；Interpreter的run/boxed_run和Transformer.transform都不独自证明变换后算子与副作用等价。

Graph.find_nodes/output_node、Node.insert_arg、node.map_arg/map_aggregate、passes.regional_inductor.regional_inductor中文仅列A2/A3，英文明确950DT不支持。node.map_arg/map_aggregate与regional_inductor只在2.12..2.14中英文页收录；replace_pattern列三类产品，node.has_side_effect也只在2.12..2.14中文页收录且列三类产品。匹配/改图工具支持不表示任意替换或regional Inductor后端已支持全部产品。

## 实验性符号形状的产品层级

fx.experimental导言强调接口属实验性质、可能随时变化。symbolic_shapes.ShapeEnv及其大部分列出方法、ShapeEnvSettings、DimDynamic、EqualityConstraint、Stateless/Stateful/SubclassSymbolicContext、DimConstraints的方法，以及StrictMinMaxConstraint.render、PropagateUnbackedSymInts的方法，中文主要只列A2/A3，英文明确950DT不支持；不能由普通FX类的950表扩展这些项。

ShapeEnv列出格式/冻结guard、axiom/implication、创建symbolic sizes/strides/storage_offset与SymBool/Float/Int节点、反序列化、evaluate、size_hint/suppress_guards、replace/simplify/create_symbol/bound_sympy/check_equal/cleanup。produce_guards_expression另列input仅FP32。add_backed_var_to_val在2.11..2.14收录，旧2.7.1/2.9/2.10则列set_unbacked_var_to_val，范围仍按所列A2/A3处理，不据名字差异生成可互换实现。

bind_symbols子方法在中英文均另列三类产品，而ShapeEnv父条目的950限制仍保留；单个子方法支持不证明父对象完整生命周期可在950使用。英文还对produce_guards_verbose明确三类产品均不支持，中文未列，不能用produce_guards_expression替代其合同。

## 辅助函数、SymInt与代理Tensor

is_concrete_int/bool/float、has_free_symbols、guard_size_oblivious、sym_eq、canonicalize_bool_expr、statically_known_true、lru_cache、check_consistent、compute_unbacked_bindings、is_accessor_node、is_symbolic，以及DivideByKey/ConvertIntKey/CallMethodKey.get采用上述中文A2/A3、英文950不支持的范围。is_symbolic只在2.11..2.14页收录；hint_int/has_free_unbacked_symbols只在2.7.1、2.11/2.12中英文页收录，另列三类产品；不因这些例外推广整个symbolic_shapes。

constrain_range/constrain_unify需通过torch.compile获取SymInt，同样不扩950；普通Python int、常量Tensor与编译产生的SymInt不因值相同就具有同一合同。proxy_tensor的make_fx/handle_sym_dispatch/get_proxy_mode/maybe_enable_thunkify/maybe_disable_thunkify也只有上述A2/A3范围，英文明确950不支持；代理模式可进入不证明任意真实算子/动态形状可执行。

## 验收与相关层次

保存改图前后结构、输入类型/shape、别名和副作用，核对guard、重编译、实际消费者及前后向结果，再比较性能。普通FX支持清单与[TorchAir pre/post Pass顺序和缓存身份](../torchair/torchair_fx_pass_and_fusion_controls.md)分别消费，不将框架工具或lint通过当作后端已支持目标变换。

## 私有FX入口和公开化版本说明

private_apis中英文对torch.fx.proxy.ParameterProxy、passes.split_module.split_module及passes.regional_inductor.regional_inductor均列A2/A3支持、950暂不支持，没有独立完整参数表。regional_inductor限PyTorch2.10.0及之后，并说明从2.12.0改为公开接口；它与前述版本支持页仅在2.12至2.14收录该入口的事实相容，不由收录版本直接推断实现首次出现。

ParameterProxy与普通Proxy、split_module与split_module名称相近的其他后端Pass不互相补合同。接口可调用、图lint通过或区域编译工具存在，不替代改图语义和实际后端验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-fx.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-fx.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-fx.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-fx.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-fx.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-fx.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-fx.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-fx.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-fx.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-fx.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-fx.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-fx.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-fx.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-fx.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-fx-experimental.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-fx-experimental.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-fx-experimental.md)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-fx-experimental.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-fx-experimental.md)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-fx-experimental.md)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-fx-experimental.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-fx-experimental.md)（constraint）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-fx-experimental.md)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-fx-experimental.md)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-fx-experimental.md)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-fx-experimental.md)（primary）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-fx-experimental.md)（constraint）
- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-fx-experimental.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）
