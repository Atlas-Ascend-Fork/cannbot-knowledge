---
type: Guide
title: GESoftmax转换：前反向精度与安全边界
description: 核对四组GE Softmax前反向、条件注册的safe入口和混合梯度判断，不以接口名字或声明样例认证运行支持。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax_backward_data.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax_backward_data.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax_backward_data.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax_backward_data.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T07:07:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GESoftmax转换：前反向精度与安全边界

## 版本与使用前提

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的完整Converter合同。主线逐个审阅全部非空源码，发布版通过完整AST对比、所有AST变化及注释变化核对；不把AST相同当字节相同。平台矩阵未知，保持draft与空平台；未执行上游、GE编译、smoke或NPU数值/性能实验。

declare_supported只是声明与测试输入候选，不是已运行结果。Meta、显式Cast、GE节点的推导和设备kernel各自约束仍须核对，不能由Python分支存在推导所有dtype、广播、空输入及动态形状都支持。[类型转换辅助函数](torchair_ge_arithmetic_lowering.md)按调用方指定dtype转换，不自行选择完整PyTorch公共类型；本文保留各准确overload的不同调用顺序。

## 前向：half_to_float不是两类Softmax的同一条分支

torch.ops.aten._softmax.default在half_to_float=True时要求输入dtype恰为FP16，否则RuntimeError；通过后将self、axes=[dim]及原half_to_float交SoftmaxV2，没有另按Meta Cast输入。不能把错误文本里的half_to_tensor拼写当新的参数或兼容条件。

torch.ops.aten._log_softmax.default则先按meta_outputs.dtype处理输入，再LogSoftmaxV2(axes=[dim])，half_to_float参数没有参与本函数的显式检查或GE属性传递。两版这四份Softmax相关文件AST相同；不能把另一个FXRT后端对_log_softmax的half_to_float限制套在此GE Converter上，也不能用GE路径反证FXRT支持。

## _safe_softmax的条件注册与安全语义边界

模块先尝试读取torch.ops.aten._safe_softmax.default，遇ImportError/AttributeError设None；只有属性存在时才定义并注册嵌套Converter。文件存在或源码含装饰器，不代表所有PyTorch版本实际注册成功。

该Converter以dtype的真值选择显式dtype或meta_outputs.dtype，先处理输入，再调用普通SoftmaxV2(half_to_float=False)；本层没有额外构造全负无穷行的mask、零填充或其他专用安全处理。**函数名带safe不独立证明所有特殊输入安全语义已保持**，需要结合对应GE版本和真实输入检查。声明列表含FP16/BF16/FP32/FP64 dtype候选，也不是这些产品组合已运行通过。

## 反向：按判断条件读精度，不照抄报错文字

两个反向入口都先把input_dtype映射成GE类型。当grad_output.dtype与它不同时，仅允许grad_output=FP32且input_dtype=FP16，其他组合拒绝；相同类型则不走这条不同类型检查。_softmax_backward_data的异常消息把input/grad精度方向写反，判断条件才是这里记录的静态合同，不能由消息推导“FP16 grad+FP32输入”获准。

torch.ops.aten._softmax_backward_data.default调用SoftmaxGrad(output,grad_output,axes=[dim])；torch.ops.aten._log_softmax_backward_data.default调用LogSoftmaxGrad(grad_output,output,axis=[dim])。二者操作数次序及axes/axis属性名字都不同，不可机械复用调用模板。不同类型拒绝时前者用RuntimeError，后者用NotImplementedError。

input_dtype只用于上述比较，没有作为独立输出dtype参数传给最终GE调用，也没有在返回前显式Cast到Meta/input_dtype；不能只根据“允许FP32 grad+FP16输入”推导最终梯度dtype已经验证。前向half_to_float通过也不自动认证配套反向的全部类型、输出别名或捕获安全性。

## 精度与优化验收

分别保存准确前向/反向FX节点、输入与梯度dtype、Meta输出和half_to_float；检查Cast是在Softmax之前还是其他位置，以及实际GE梯度输出。覆盖极大/极小值、全负无穷行、空输入、不同dim、FP16输入与FP32梯度；检查数值后再量吞吐。单个SoftmaxV2节点或名字中的safe不作为精度、融合、训练及产品支持的认证。本次没有执行这些实验。

四个out重载在这两版均直接拒绝，详细标识见下表。一般归约和索引的精度区别见[GE归约与排序](torchair_ge_reduction_lowering.md)，后端选择与函数化见[自定义算子入图合同](../../integration/torchair/custom_operator_graph_contract.md)。

## 全部准确注册重载与拒绝边界

下表仅描述实际选中此内置Converter后的构图或直接拒绝。主线†表示getattr(...,None)兼容声明，目标不存在时不建立有效Converter；发布快照这些named overload使用直接属性访问。不把兼容声明变化当成计算实现新增，也不否定高层函数可经decomposition或其他后端执行。

| 来源主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| _softmax | `torch.ops.aten._softmax.default`、`torch.ops.aten._safe_softmax.default`（仅目标属性存在时注册） | RuntimeError：`torch.ops.aten._softmax.out` |
| _softmax_backward_data | `torch.ops.aten._softmax_backward_data.default` | RuntimeError：`torch.ops.aten._softmax_backward_data.out` |
| _log_softmax | `torch.ops.aten._log_softmax.default` | RuntimeError：`torch.ops.aten._log_softmax.out` |
| _log_softmax_backward_data | `torch.ops.aten._log_softmax_backward_data.default` | RuntimeError：`torch.ops.aten._log_softmax_backward_data.out` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax_backward_data.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_softmax_backward_data.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax_backward_data.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_log_softmax_backward_data.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
