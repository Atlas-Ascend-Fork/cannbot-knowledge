---
type: Guide
title: GE批量更新转换：foreach标量、列表与整数别名
description: 归并31组foreach实现的首元素类型选择、ScalarList差异、取整整数拆分及输出复用，限定准确重载与版本。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_abs.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_abs.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_acos.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_acos.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcdiv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcdiv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_asin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_asin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_atan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_atan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cos.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cos.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cosh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cosh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_div.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_div.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erf.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erf.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erfc.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erfc.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_exp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_exp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_expm1.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_expm1.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_lerp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_lerp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log10.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log10.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log1p.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log1p.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_maximum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_maximum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_minimum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_minimum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_pow.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_pow.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_round_off_number.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_round_off_number.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sigmoid.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sigmoid.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sinh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sinh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sub.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sub.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T07:23:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE批量更新转换：foreach标量、列表与整数别名

## 版本与证据强度

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013中31组foreach Converter。逐项审阅主线全部非空源码，两版31组AST均相同，注释差异也已核对；这不表示字节相同或与任意TorchNPU版本配套。

这里只维护构图层优化合同，没有覆盖整卡的产品矩阵，保持draft和空平台。未执行上游、smoke、GE编译、NPU数值或性能实验；declare_supported中的shape、dtype、标量只表示声明/候选测试，不是已通过记录，也不构成完整混合类型或空列表支持表。

## 批量更新不能照搬普通逐点算子规则

这些入口直接构造Foreach系列GE节点，没有在Converter里逐个调用普通add/mul等Python循环；但单个GE节点不等于一个设备kernel、保证融合或吞吐必然提升。需要按真实优化器路径确认准确Scalar、List、ScalarList、Tensor和输出重载，不能从数学名称推导相同类型提升或原地语义。

多数函数不使用meta_outputs逐项修正输入/输出dtype，也未在此层完整检查列表长度、对应shape、同设备、同dtype及标量数量。原码只处理局部参数时，不能把缺少检查解释为任意混合列表合法；同样不能凭声明列出的混合dtype样例当作已实测。

## Scalar与List系数以首元素选择类型

| 入口 | 此层转换规则 |
| --- | --- |
| _foreach_add.Scalar、_foreach_sub.Scalar、_foreach_mul.Scalar、_foreach_div.Scalar | self非空时，以self[0].dtype处理scalar；首元素为BF16则改为FP32。空self不经过这个转换，随后仍调用对应Foreach节点，不据此认证空列表可运行。 |
| _foreach_add.List、_foreach_sub.List | 两个Tensor列表原样传递；alpha也只按首个self选择类型，BF16特例为FP32。没有逐项把self/other按各自Meta输出类型提升。 |
| _foreach_addcdiv.Scalar、_foreach_addcmul.Scalar | value按首个self转换，BF16时FP32，再连同三组Tensor列表传给ForeachAddcdivScalar/ForeachAddcmulScalar。 |
| _foreach_maximum.Scalar、_foreach_minimum.Scalar、_foreach_pow.Scalar | scalar或exponent沿用上述首元素/BF16规则，不能据首个Tensor就证明列表中其余类型也满足同一IR合同。 |

这与普通[逐点算术Converter](../../inference/guides/optimization/torchair/torchair_ge_arithmetic_lowering.md)按Meta输出dtype处理所有操作数不同。文档[ATen能力表](../../inference/guides/optimization/torchair/torchair_aten_constraint_review.md)对若干foreach标量另列FP32/INT64限制，源码此处的局部Cast和declare_supported候选不能独立取消文档限制；先确认实际前端overload和GE输入描述，再按目标组合验收。

## ScalarList、Tensor及底数/指数方向

add/sub/mul/maximum/minimum的ScalarList仅在scalars非空且第一个元素是Python int时，将整个scalars通过dtype_promote转INT64 Const；否则原样交Foreach...ScalarList。它们没有逐元素根据每个Tensor dtype构造独立系数；只看首个scalar也不构成完整异构列表校验。

div.ScalarList、pow.ScalarList以及addcdiv/addcmul.ScalarList则直接传scalars，不共享前一个INT64分支。addcdiv/addcmul.Tensor把一个GE Tensor scalars交ForeachAddcdivList/ForeachAddcmulList，与ScalarList的IR名字不同；不能将Tensor形参按Python List索引/len规则任意替换。

pow.ScalarAndTensor的方向是一个标量底数与一组指数Tensor：仅底数为Python float时，先构造FP32 Cast并Fill成[1] Tensor；其他类型原样传ForeachPowScalarAndTensor。它不是把_scalar指数和Tensor底数交换，也不按指数列表首元素dtype自动选择底数精度。

div.List、mul.List、maximum.List、minimum.List、pow.List分别原样传两个Tensor列表；lerp.Scalar与lerp.List分别调用ForeachLerpScalar和ForeachLerpList，当前函数没有为weight补公共dtype。foreach lerp.List有实际构图分支，不能把普通lerp.Tensor的拒绝边界套在它上面。foreach_norm.Scalar将scalar直接交ForeachNorm，其默认2，不在本层认证所有范数阶数或精度规则。

## 取整函数的整数拆分、顺序与别名

辅助函数把INT8/UINT8/INT16/INT32/UINT32/INT64/UINT64 Tensor记为整数项，保留原列表索引；其他dtype留在另一组，这个“非整数”组并不自动等于完整合法浮点集合，BOOL也未在整数白名单中。

| 准确default入口 | roundMode及列表处理 |
| --- | --- |
| _foreach_floor | INT8类型的模式值2；只向ForeachRoundOffNumber传非整数项，随后按原位置插回原整数Tensor；全为整数时直接返回原self列表。 |
| _foreach_round | 模式4；采用与floor相同的整数拆分及原对象插回，全整数时同样直接返回self。 |
| _foreach_frac | 模式7；无论非整数组是否为空都先调用ForeachRoundOffNumber，再按原位置插入整数项的ZerosLike。不能由floor/round的空非整数保护推定这里也有同一保护。 |
| _foreach_ceil、_foreach_trunc | 分别模式3和5；直接把全部self传ForeachRoundOffNumber，不执行上述整数拆分逻辑。 |

这些模式在源码中通过Fill和INT8 Cast构造，不是Python读取Tensor运行数值。floor/round的整数输出复用了输入Tensor对象，全整数时还复用列表；这与“数值不变但返回独立对象”不是同一个别名合同。需结合外围函数化、后续mutation及输出存储单独核对，不能只比较数值后认定优化完全等价。

## 批量一元算子的直接映射

abs、acos、asin、atan、cos、cosh、erf、erfc、exp、expm1、log、log10、log1p、log2、sigmoid、sin、sinh、tan、tanh的所列default入口直接调用对应Foreach GE节点，部分使用x=self关键字，其余位置参数。它们没有复制普通逐点数学Converter的全部Meta Cast或定义域处理；精确标识见下表。

_foreach_abs的Schema说明字符串写成普通aten::abs与别名标记，实际装饰器绑定的是torch.ops.aten._foreach_abs.default。分析优化器是否走原地路径应以准确注册对象和实际图为准，不能仅凭这条说明把它认定为foreach_abs_原地更新。

## 优化器使用与验收

分别记录Tensor列表每项的dtype/shape、scalar或ScalarList的真实Python/GE类型、列表长度、alpha/value及是否走输出重载。覆盖BF16首元素与混合顺序、整型ScalarList、空列表、pow操作数方向、floor/round输出复用及frac全整数路径。先核对数值、输出结构和别名，再比较foreach与逐点方案在目标版本的GE图、设备启动和稳态耗时；本次没有执行这些实验。

通用开发与decomposition边界见[Converter开发](../../inference/guides/optimization/torchair/torchair_converter_implementation.md)，激活前反向的保存值及参数限制见[GE逐点数学与激活](../../inference/guides/optimization/torchair/torchair_ge_activation_lowering.md)。

## 准确overload与直接拒绝清单

有构图分支只表示以下固定内置Converter有计算调用，不独立证明完整输入域、原地别名或设备运行支持。未列入本卡的其他foreach壳见[纯占位合同](../../inference/guides/optimization/torchair/torchair_ge_unimplemented_overloads.md)，不从文件清单扩展全部优化器或所有重载。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| _foreach_abs | `torch.ops.aten._foreach_abs.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_acos | `torch.ops.aten._foreach_acos.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_add | `torch.ops.aten._foreach_add.Scalar`、`torch.ops.aten._foreach_add.List`、`torch.ops.aten._foreach_add.ScalarList` | RuntimeError：`torch.ops.aten._foreach_add.Scalar_out`、`torch.ops.aten._foreach_add.List_out`、`torch.ops.aten._foreach_add.ScalarList_out` |
| _foreach_addcdiv | `torch.ops.aten._foreach_addcdiv.Scalar`、`torch.ops.aten._foreach_addcdiv.ScalarList`、`torch.ops.aten._foreach_addcdiv.Tensor` | RuntimeError：`torch.ops.aten._foreach_addcdiv.Scalar_out`、`torch.ops.aten._foreach_addcdiv.ScalarList_out`、`torch.ops.aten._foreach_addcdiv.Tensor_out` |
| _foreach_addcmul | `torch.ops.aten._foreach_addcmul.Scalar`、`torch.ops.aten._foreach_addcmul.ScalarList`、`torch.ops.aten._foreach_addcmul.Tensor` | RuntimeError：`torch.ops.aten._foreach_addcmul.Scalar_out`、`torch.ops.aten._foreach_addcmul.ScalarList_out`、`torch.ops.aten._foreach_addcmul.Tensor_out` |
| _foreach_asin | `torch.ops.aten._foreach_asin.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_atan | `torch.ops.aten._foreach_atan.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_cos | `torch.ops.aten._foreach_cos.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_cosh | `torch.ops.aten._foreach_cosh.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_div | `torch.ops.aten._foreach_div.Scalar`、`torch.ops.aten._foreach_div.List`、`torch.ops.aten._foreach_div.ScalarList` | RuntimeError：`torch.ops.aten._foreach_div.Scalar_out`、`torch.ops.aten._foreach_div.List_out`、`torch.ops.aten._foreach_div.ScalarList_out` |
| _foreach_erf | `torch.ops.aten._foreach_erf.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_erfc | `torch.ops.aten._foreach_erfc.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_exp | `torch.ops.aten._foreach_exp.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_expm1 | `torch.ops.aten._foreach_expm1.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_lerp | `torch.ops.aten._foreach_lerp.Scalar`、`torch.ops.aten._foreach_lerp.List` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_log | `torch.ops.aten._foreach_log.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_log10 | `torch.ops.aten._foreach_log10.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_log1p | `torch.ops.aten._foreach_log1p.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_log2 | `torch.ops.aten._foreach_log2.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_maximum | `torch.ops.aten._foreach_maximum.Scalar`、`torch.ops.aten._foreach_maximum.ScalarList`、`torch.ops.aten._foreach_maximum.List` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_minimum | `torch.ops.aten._foreach_minimum.Scalar`、`torch.ops.aten._foreach_minimum.ScalarList`、`torch.ops.aten._foreach_minimum.List` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_mul | `torch.ops.aten._foreach_mul.Scalar`、`torch.ops.aten._foreach_mul.List`、`torch.ops.aten._foreach_mul.ScalarList` | RuntimeError：`torch.ops.aten._foreach_mul.Scalar_out`、`torch.ops.aten._foreach_mul.List_out`、`torch.ops.aten._foreach_mul.ScalarList_out` |
| _foreach_norm | `torch.ops.aten._foreach_norm.Scalar` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_pow | `torch.ops.aten._foreach_pow.List`、`torch.ops.aten._foreach_pow.Scalar`、`torch.ops.aten._foreach_pow.ScalarList`、`torch.ops.aten._foreach_pow.ScalarAndTensor` | RuntimeError：`torch.ops.aten._foreach_pow.List_out`、`torch.ops.aten._foreach_pow.Scalar_out`、`torch.ops.aten._foreach_pow.ScalarList_out` |
| _foreach_round_off_number | `torch.ops.aten._foreach_floor.default`、`torch.ops.aten._foreach_frac.default`、`torch.ops.aten._foreach_ceil.default`、`torch.ops.aten._foreach_round.default`、`torch.ops.aten._foreach_trunc.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_sigmoid | `torch.ops.aten._foreach_sigmoid.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_sin | `torch.ops.aten._foreach_sin.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_sinh | `torch.ops.aten._foreach_sinh.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_sub | `torch.ops.aten._foreach_sub.Scalar`、`torch.ops.aten._foreach_sub.List`、`torch.ops.aten._foreach_sub.ScalarList` | RuntimeError：`torch.ops.aten._foreach_sub.Scalar_out`、`torch.ops.aten._foreach_sub.List_out`、`torch.ops.aten._foreach_sub.ScalarList_out` |
| _foreach_tan | `torch.ops.aten._foreach_tan.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |
| _foreach_tanh | `torch.ops.aten._foreach_tanh.default` | 本文件无无条件拒绝壳；不表示全部overload均支持 |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_abs.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_abs.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_acos.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_acos.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_add.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_add.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcdiv.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcdiv.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcmul.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_addcmul.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_asin.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_asin.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_atan.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_atan.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cos.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cos.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cosh.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_cosh.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_div.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_div.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erf.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erf.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erfc.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_erfc.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_exp.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_exp.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_expm1.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_expm1.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_lerp.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_lerp.py)（implementation）
- [固定来源 31](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log.py)（implementation）
- [固定来源 32](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log.py)（implementation）
- [固定来源 33](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log10.py)（implementation）
- [固定来源 34](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log10.py)（implementation）
- [固定来源 35](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log1p.py)（implementation）
- [固定来源 36](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log1p.py)（implementation）
- [固定来源 37](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log2.py)（implementation）
- [固定来源 38](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_log2.py)（implementation）
- [固定来源 39](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_maximum.py)（implementation）
- [固定来源 40](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_maximum.py)（implementation）
- [固定来源 41](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_minimum.py)（implementation）
- [固定来源 42](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_minimum.py)（implementation）
- [固定来源 43](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_mul.py)（implementation）
- [固定来源 44](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_mul.py)（implementation）
- [固定来源 45](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_norm.py)（implementation）
- [固定来源 46](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_norm.py)（implementation）
- [固定来源 47](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_pow.py)（implementation）
- [固定来源 48](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_pow.py)（implementation）
- [固定来源 49](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_round_off_number.py)（implementation）
- [固定来源 50](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_round_off_number.py)（implementation）
- [固定来源 51](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sigmoid.py)（implementation）
- [固定来源 52](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sigmoid.py)（implementation）
- [固定来源 53](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sin.py)（implementation）
- [固定来源 54](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sin.py)（implementation）
- [固定来源 55](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sinh.py)（implementation）
- [固定来源 56](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sinh.py)（implementation）
- [固定来源 57](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sub.py)（implementation）
- [固定来源 58](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_sub.py)（implementation）
- [固定来源 59](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tan.py)（implementation）
- [固定来源 60](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tan.py)（implementation）
- [固定来源 61](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tanh.py)（implementation）
- [固定来源 62](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_foreach_tanh.py)（implementation）
- [固定来源 63](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 64](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 65](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 66](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
