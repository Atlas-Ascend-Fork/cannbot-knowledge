---
type: Guide
title: Inductor AscendC IndexExpr：算术展开、范围证明与整数精度
description: 完整核对索引表达式的标量/Arange/向量分流，保留Remainder范围证明、Pow缩窄和divmod回写的真实条件。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/index_expr_lowering.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py
  role: implementation
created_at: '2026-11-11T05:08:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC IndexExpr：算术展开、范围证明与整数精度

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c，完整读取index_expr_lowering.py及utils所列索引helper。它们生成ASCGraph前端节点；外部AscIR/Autofuse、Torch ValueRanges与生成AscendC主体不在本卡闭合。发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有该Lowering具体路径，其他表达式实现另计。保持draft/空平台，未运行或导入上游。

## 校验、标量和参与轴

lower_index_expr先sympify、可选kernel.rename_indexing，再要求存在contiguous_loop；这里只查非None，没有单独断言轴列表非空。参与轴按free_symbols名字匹配loop.axis，保留loop顺序。UnsupportedIndexExpr保存expr/dtype/reason，异常消息指明不支持形态，本模块没有自己的透明eager回退。

表达式校验允许Integer/Rational/Float/Symbol、递归Add/Mul及支持的类；Pow指数必须是非负sympy.Integer字面量。操作按类MRO名字匹配Abs、FloorDiv（包括CleanDiv等子类）、Pow、Min、Max，特殊处理ModularIndexing/Mod；这里沿用类名语义，未验证任意第三方同名类的数学实现。

_lower优先处理Pow；其他表达式若不含当前loop轴，或expand后轴已消去，先生成标量：数值非Symbol用ir.constant(str(expr),dtype)，其余用_index_expr_node。**无轴Mod/FloorDiv走这一标量分支，不会自动经过下方向量Remainder范围证明。** 有轴时按unary/binary/nary、特殊handler、单轴仿射、Add/Mul递归顺序处理，其他形态显式报错。

_Lowered的容器frozen，内部Tensor仍可改dtype；_set_dtype写_v.dtype。_align将每个操作数对齐完整active loop，_broadcast按目标轴逐次构造DenseLoop，未扩维先用size1，存在source y.dtype则复制到结果。最终只在full_axes非空且尚未对齐时再broadcast，不能仅据函数名声称任何上下文都生成非空rank。

## 单轴Arange与向量组合

_try_linear_decompose要求恰一个loop轴，Poly在该轴上取step，step非零、剩余base无参与轴才成功。base/step要作为Arange属性，还须没有支持表中的非线性节点且不含loop轴。简单base/step直接ir.arange；base复杂则Arange加递归base，step复杂则unit Arange乘递归系数，再加base。多轴Add/Mul按二元操作折叠，Min/Max按顺序折叠。

_create_arange先绑定单轴子Loop，再把metadata扩成完整轴集合、其他维size1/stride0，本地axes记录仍只包含该轴。前端绑定和数学表达式并存，不能把简化后的文本当成实际地址或运行时shape已经验证。

## Remainder有范围证明，Pow路径不同

范围环境先给每个loop轴[0,size-1]，构造失败返回None，再用可选shape_env.var_to_range update增强；这一步会按同名key覆盖，不是显式求区间交。_prove_int32对每项bound_sympy，只有上下界为数值且转int位于[-2³¹,2³¹-1]才通过，异常或未知返回False。

参与轴的int64 Remainder必须通过这项证明，再把两个操作数cast int32、做remainder、cast回int64；其他dtype直接下发相应IR。ModularIndexing先算FloorDiv(base,divisor)，divisor==1则用base，证明列表为base、divisor、modulus、quotient及quotient*modulus。Mod证明lhs、rhs、FloorDiv(lhs,rhs)及quotient*rhs。这里是源码实际选择的表达式集合，不是本次完成了所有整数溢出/除零/设备精度证明。

Pow的int64请求则主动在int32计算再cast回int64，代码注释明确接受缩窄溢出风险，**没有同样的范围证明门槛**。base与exponent先按active loop对齐再发cast/Pow，避免通常上下文中的标量metadata不匹配；active loop本身为空的任意调用没有在本helper独立保护。

float16/bfloat16/float32/float64请求先在int64域求表达式，只有此浮点请求分支会拒绝所有非Integer数值原子；整数dtype请求的普通validator仍允许Rational/Float，不能把该检查推广为全部入口统一整数原子验证。末端float16/bfloat16请求实际cast为float32，float32/float64用原请求类型，配合最终Store降精度，见[本地IR](torchair_inductor_ascendc_local_ir.md)。

## divmod重组与回写护栏

_strip_trivial_floordiv把FloorDiv(x,1)替成x，依据整数索引语义；不作为一般实数floor恒等式。_recombine_divmod_identity先expand顶层Add，将每项单个FloorDiv与step==1的ModularIndexing按(x,d)聚合系数。单项有多个同类原子、混含两类、或不匹配结构原样保留；仅c_fd==d*c_mi且positive(d)查询不是False才合并为c_mi*x。**未知正性也可过该条件，不是单独证明d>0。**

_recombine_body_index_exprs只处理LOAD/STORE/STORE_REDUCTION，不改memory_usage/MemoryDep。它要求新expr不同且新div/mod原子集合是旧集合的严格子集才写回；这是集合包含关系，不能仅按注释说“原子数量减少”便接受出现新原子的表达式。写前记录old/new日志，返回changed供外部依赖刷新。

宽catch会debug并返回False，但没有恢复此前已写入的exprs；若后续条目异常，不能把注释的“零行为变化”描述成该函数自身的事务回滚保证。_is_affine_index_expr先剥trivial div，再Poly，异常False；每个monomial最多一个非零轴指数且指数不大于1才通过，sizevar可处系数。实际调用处如何刷新依赖和对接索引域仍由[规范轴](torchair_inductor_ascendc_axis_mapping.md)及集成入口分别说明。

本卡保留数值缩窄、未知范围和回写时机，未把源码注释、表达式可打印或编译通过当成模型精度验证。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/index_expr_lowering.py)（primary）：1–510。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py)（implementation）：320–458。
