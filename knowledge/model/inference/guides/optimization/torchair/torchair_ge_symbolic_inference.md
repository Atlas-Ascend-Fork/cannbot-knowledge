---
type: Guide
title: GE符号推导：表达式节点与自动形状规则
description: 区分有限AST构图和自动_inference_rule生成，记录容器版本差异、符号覆盖门槛、ref传播和警告后返回的边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/infer_symbol_calculate.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/infer_symbol_calculate.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/infer_symbol_shape.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/infer_symbol_shape.py
  role: implementation
created_at: '2026-11-10T10:35:14Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE符号推导：表达式节点与自动形状规则

## 固定版本与两类符号处理

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的infer_symbol_calculate.py和infer_symbol_shape.py。表达式解析器两版AST相同，自动规则层有容器重建和输出校验差异。本卡为静态实现合同，产品矩阵未知，保持draft与空平台；未导入上游、求值模型、生成运行图或做设备验证。

两层不可混为一个“支持全部动态shape”的能力：前者把字符串表达式变成GE节点，后者结合Meta和符号覆盖关系给自定义节点写入_inference_rule。

## ExpressionParser：有限AST到GE节点

infer_ge_output_by_symbol_calculate直接把meta_output转str交ExpressionParser.parse_expression，以ast.parse(mode='eval')解析后递归访问；不是Python eval。Name只能查symbol_map，缺符号报错；Add/Sub/Mult/Div/Pow映射相应GE算子，USub映射Neg、UAdd原样返回，Constant统一生成DT_INT64 Const。

operator_map没有FloorDiv、Mod、比较、布尔或位运算。表达式解析成功不证明所有常量值都适合INT64、GE算子dtype已统一、除法与整型形状语义已验证；不能把infer_symbol_shape中另一套转换支持直接转给本解析器。

Call只接受裸函数名，先递归位置参数，再按hasattr(ge,func_name)查同名构图API并调用；属性形式的函数名变空字符串，不会把torch.sin等注释示意自动实现成命名空间解析。源码没有转发node.keywords，也没有固定函数白名单；带关键字的表达式不能据Python原表达式推导语义被保留。

整个parse_expression把异常包装为ValueError；此前递归已创建的GE节点在本函数里没有回滚。它不是事务式校验器，未运行失败例子，也未执行任意表达式。

## 形状表达式转规则文本是另一套合同

sympy_to_ge_expr解析表达式、按name_replacements改名，再由PyToCppTransformer变换：幂变Pow，整除变Floor(Div(a,b))，取模变Mod，真除变Div；裸ceil/ceiling/CeilToInt变Ceil，floor/FloorToInt变Floor，IntTrueDiv变Div，属性形式按末属性名处理ceil/ceiling/floor。并没有在此完整识别函数命名空间或证明全部SymPy语法可表达。

优先使用ast.unparse，旧Python回退ASTUnparser；后者的运算符表包含位运算、移位和矩阵乘等文本，但“能打印一个符号”不等于GE规则解释器能执行它。两种表达式处理在接受域和输出形式上必须分开。

## SymTensor是推导描述，不是设备Tensor

SymTensor对torch.Tensor保存size和转换后的GE dtype；符号标量包装为sym_value列表，列表中取首个符号的dtype。普通常量列表未必有dtype，is_defined_sym_tensor要求sym_size与dtype均非None，且每维为int/SymInt；单纯值列表不等于完整输出Tensor规格。

free_symbols只从SymInt的node.expr收集，不直接把所有符号类型一视同仁。to只克隆描述并改ge_dtype，不生成GE Cast或搬运数据；复制构造用列表真值判断拷贝sym_size/sym_value，空列表会变None，不能忽略标量shape=[]的元数据边界。这是源码静态条件，未执行样例。

## 自动推导何时启动，容器版本差异在哪里

infer_and_gen_sym_shape若ops全都在ge模块有同名API就提前返回，空ops同样满足all；所谓builtin判定只是hasattr(ge,op.type)，不是底层kernel可用性查询。其余路线复制kwargs并去掉meta_outputs，建立符号上下文后重建Meta。

主线_reconstruct_meta递归GE Tensor、Mapping、tuple、list，tuple保留类型、Mapping转dict；发布版仅处理直接GE Tensor及含GE Tensor的一层list/tuple，不具备同一嵌套Mapping能力。

主线map_ge_tensor_with_meta对Mapping要求两路均Mapping、key集合与长度相同，再按GE键映射；对list/tuple要求Meta同属序列并等长。发布版没有Mapping分支，序列用zip而未做相同类型/长度检查。两版“返回容器”不能按同一保证验收。

ShapeEnv使用duck_shape=False；遇SymInt时以hint_int创建动态符号，Tensor Meta按符号shape调用torch.empty并保留dtype/device，再调用target重算Meta。此函数本身没有新建并进入FakeTensorMode上下文，实际Meta执行环境取决于调用方；hint和重建不等于真实输入范围已被验证。主线hint_int导入失败时回退optimization_hint，发布直接导入。

## 推导传播与ref命名只覆盖明确规则

节点间仅为TensorMove、Cast、Const定义辅助传播：TensorMove取输入描述，Cast改变描述dtype，Const只取得proto dtype而不从常量内容恢复完整shape/value。推导输出数量不匹配就跳过该传播。

get_output_sym_tensor优先取已有上下文；否则若output_desc.name与某input_desc.name同名，取对应输入描述作为ref关系；找不到返回未定义SymTensor并记录debug。描述符同名在这里是推导依据，不独立证明真实运行时别名或写回顺序正确。

## _inference_rule生成有完整性门槛

只处理非builtin节点，全部输出描述必须is_defined_sym_tensor。minimal_required_inputs按输入顺序贪心收集尚缺的输出自由符号，保留原位置并以None填未选项；它不是求全局最少输入集合的优化算法。仍有未覆盖符号时警告并跳过该节点。

已覆盖时将输入shape/value和输出shape转字符串表达式，必要时给符号值改名，dtype列表取输出描述，再通过attr.Str(...).merge_to写入op.attr['_inference_rule']。这些JSON字段是推导规则材料，不是实际输出shape已经在设备计算或数值结果已正确的证据；不同节点的局部描述也不能替代完整图合同。

infer_and_gen_sym_shape_silent捕获Exception并warnings.warn后返回，没有把异常重新抛出或撤销先前所有元数据/节点修改。调用没有报错不等于规则生成成功；应检查警告、每个目标节点的_inference_rule以及符号覆盖情况。

## 验证与关联

核对准确快照、表达式AST、symbol_map、常量dtype、调用方FakeTensor上下文、容器key/长度、ref名字、输出shape/dtype和规则文本；区分早退、未定义输出、符号缺失跳过、异常警告与成功写规则。实际动态范围、数值正确性及性能仍须匹配栈实验，本次未运行。

- [自动函数化视图重建](torchair_ge_auto_functionalized_views.md)
- [View物化与符号来源](torchair_ge_view_materialization.md)
- [FX Meta/NPU容器配对](torchair_fx_value_pack_metadata.md)
- [GE元数据占位与hint](torchair_ge_metadata_support_helpers.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/infer_symbol_calculate.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/infer_symbol_calculate.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/infer_symbol_shape.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/infer_symbol_shape.py)（implementation）
