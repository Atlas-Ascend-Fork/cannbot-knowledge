---
type: Guide
title: GE回调Schema：别名匹配、REG_OP与值依赖
description: 核对主线自定义回调的类型分类、out/inplace别名、可选输入、标量Const、动态数量及普通Converter与执行层的分工。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py
  role: primary
created_at: '2026-11-10T11:04:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE回调Schema：别名匹配、REG_OP与值依赖

## 固定快照与证据范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的custom_op_codegen_common.py、custom_op_codegen_cpp.py和custom_op_codegen_python.py，包含嵌入的生成代码模板。发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这三个同路径，仅记录路径事实，不否定其他发布入口。本文为静态实现合同，产品矩阵未知，保持draft与空平台；未导入上游、调用生成器、编译/加载动态库、读取设备地址或执行回调。

## 候选与Python/C++路由

is_custom_op要求OpOverload和_schema，且namespace不在aten、prim、prims、quantized、_quantized集合；不等于所有其他namespace都已可运行。determine_callback_path先查询PrivateUse1 kernel，缺失则跳过；_defined_in_python缺省True，该标记为假值走cpp，真值走python。它没有根据完整性能测量自动选路，也没有在本函数独立证明Meta与所有Schema类型可用。

## Schema类型分类与可选输入

extract_schema_info按字符串分类：Tensor、Tensor[]/List[Tensor]、int/float/bool/str及相应列表、Scalar/number、Scalar列表和若干enum；Dict及未知类型拒绝，任意嵌套列表或Optional内部组合不能由外层名称推定被支持。Layout、Device、MemoryFormat与ScalarType都归enum，但具体回调恢复方式仍需分别核对。

有默认值也会使参数标记为GE可选输入，不仅是Optional[T]；scalar_list特例不据默认值变成可选。保存is_out、is_kwarg_only、别名组、输入kind及默认值，描述字段存在不等于每条后续调用都按同一方式使用。

_INPUT_KIND对Optional Tensor列表及Scalar列表没有独立OPT编号，字符串列表则有此处新增编号并注明delegate没有同类。_compute_input_kind未知组合默认0，不能把编号视作跨任意delegate版本的稳定兼容证明。

## 别名匹配只接受明确out或写入关系

返回值按alias_info.before_set与输入组匹配；Tensor[]返回带别名直接拒绝，找不到对应输入也拒绝。匹配out参数则记录返回索引，单个out对应多个返回拒绝；匹配写入输入则标inplace return并采用输入名；只读view式返回别名明确不支持。每个out参数必须有对应返回。

这些是Schema层的匹配，不恢复普通共享Storage、stride和offset。多输入共用别名组时映射按遍历建立并取首个匹配，不能把它概括为完整任意别名关系求解器。find_inplace_arg_index另按首个写入非out且组相交的输入查找。

## REG_OP与标量值依赖

make_ge_op_name把namespace::op变namespace__op并追加非default overload。build_reg_op_proto跳过out参数，Tensor为必选/可选输入，Tensor[]为动态输入，标量也成为GE输入而不是普通属性；返回Tensor[]声明动态输出，其他返回声明Tensor输出。TensorType::ALL()只是原型类型表达，不独立证明所有dtype和返回类别有可用kernel或回写方式。

有动态输入时增加必选N属性，再写op_name、overload、input_kinds、num_outputs和is_inplace元数据。generate_reg_op保留inputs→N→outputs→其余attrs顺序，为标量输入增加InputsDataDependency；num_outputs是逻辑返回描述数，不等于Tensor[]展开后的物理输出总数。

## 普通Converter的取参、默认值与动态数量

build_common_converter逐个非out参数从args或kwargs取值；Tensor和列表直接传GE输入，列表把len写到同一N属性，多个列表不是各自独立N字段。标量None仅对可选项保留空输入，否则报错；未给标量可用Schema默认值。

_scalar_to_ge_input将int/enum及torch.dtype值归INT64，float为FP32，bool为BOOL，Scalar按Python整型或浮点分支；列表对应INT64/FP32/BOOL，混合Scalar列表不是逐项保留原精度。字符串手动建Const，字符串列表以零字节拼接；不能从构图接受推断任意包含零字节/空字符串边界都可被所有回调无损恢复。

动态输出数有合适meta_outputs列表时取len；多个逻辑返回按对应Meta项取数，否则默认1。缺Meta的默认值不是实际返回列表长度证明。函数没有在此按is_kwarg_only构造完整独立参数绑定器，也没有统一额外kwargs或全部位置参数校验。

register_callback_converter重新抽Schema、造同名GE节点Converter并注册；Converter只生成图节点，Python/C++实际Execute在其他层。应分别验收Schema、REG_OP、Meta数量、回调绑定和执行结果，本次均未运行。

- [预扫描与编译加载次序](torchair_ge_custom_prescan_compilation.md)
- [Python回调合同](torchair_ge_python_callback_codegen.md)
- [C++回调合同](torchair_ge_cpp_callback_codegen.md)
- [Triton HOP路由](torchair_ge_triton_hop_contracts.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py)（primary）
