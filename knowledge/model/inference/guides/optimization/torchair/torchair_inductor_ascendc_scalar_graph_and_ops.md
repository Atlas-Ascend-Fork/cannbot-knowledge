---
type: Guide
title: Inductor AscendC标量图与操作映射：属性、缓存和真实缺口
description: 完整对照两版ASCGraph、asc_ops与Overrides，区分图内标量、Host载体、文本CSE、操作转发和实际缺失实现。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/asc_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/asc_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_overrides.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_overrides.py
  role: implementation
created_at: '2026-11-11T05:37:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC标量图与操作映射：属性、缓存和真实缺口

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013，完整读取两版ASCGraph/asc_ops/Overrides；发布Overrides复用144个完整AST相同定义并逐项读完整原始diff。产品未知，draft/空平台，没有导入、构图、Lowering或设备运行。[dtype登记表](torchair_inductor_ascendc_lowering_dtype_registry.md)是另一层准入，不能用本卡函数名或登记存在替代实际后端支持。

## 属性追踪与ScalarData的两层类型

_Track读取不存在属性时创建路径节点，赋值时将全名写入root.attrs；不在这里校验任意属性名。_Op另存order、buffer_name、private_attrs和支持标记，get_attr未中返回None。生成代码将torch dtype改为ascir.dtypes表示、bf16改名，符号表达式按size-name映射替换再repr；只有Arange专用_SizeExprConstant强制序列化ascir.SizeExpr常量。它们是生成文本对象，不是AF实际算子定义。

| 输入dtype | Host标量载体 | AF ScalarData dtype |
| --- | --- | --- |
| float16/bfloat16/float32 | float32 | float32 |
| int8/int16/int32/int64 | int64 | 各自原位宽 |
| uint8 | int64 | uint8 |
| bool | _BOOL_DTYPE | _BOOL_DTYPE |

_BOOL_DTYPE在未知SoC或低于Soc.A5时为uint8，A5及以上为bool。Soc.A5按Ascend950系列（包含旧称Atlas A5）表述，这只是代码本地枚举门控，不认证产品矩阵。未列dtype由两个转换helper直接NotImplementedError，不能把所有无符号整数都套为已支持Host int64。

_Tensor把Scalar/ScalarData/IndexExpr认作标量，as_loop直接保留；向量才写axis/size/strides及私有hint size/stride/offset，非连续另记not_contiguous。主线这里没有像发布那样再向ASC Tensor写非零offset，实际访存offset由对应Load/Store链核对。ASCIndexing持有原asc_tensor且作为SymPy Symbol使用；它本身不执行取值或边界检查。

Welford helper明确构造mean、broadcast、差值平方和sum得到M2，两返回Tensor绑定共同loop更新；weight只是Unsupported占位，源码明确禁止参加真实计算，不将它写成通用数值稳定在线Welford或完整三输出实现。

## 图输入、匿名化与生成的可变状态

ASCGraph.add_op按类型生成局部名字、顺序和当前buffer_name；is_unsupported进入unsupported_ops，add_fallback_op还进入fallback_ops。reason只汇总这些集合，不是自动运行eager。get_tensor仅支持index0，找到op而index非0才抛错。Data/ScalarData在同一inputs顺序中另存input_op_names，标量记录原dtype；reorder_inputs按canonical签名重写ir_attr.index并重排名字/outer列表，ops本身不重排。

主线graph-level schedule_axes独立于axis_vars，生成时先声明全部size/axis，再在非空schedule_axes时设置sched.axis，随后逐op属性并infer_dtypes。size_vars在codegen时从set改成排序list，不能把这个对象当可无限追加的纯不可变打印器。_Op属性序列化没有自动检查所有外部AscIR类或数学helper是否存在。

FusedASCGraph主线只有一个图，subgraphs为兼容返回单元素列表；输入保序去重并排除图outputs，输出按调用者给的列表，size_vars排序。输入/输出/内部workspace匿名化后，外层Data或ScalarData必须与内图输入种类和index一致，再把AscBackend的输出接到外层Output。is_fused_mm识别MatMul/MatMulBias/BatchMatMul/BatchMatMulBias并选择CV Tiling类型。生成字符串最后调用AutofuserOptions(graph_type=1)、schedule、codegen，外部AF主体仍未闭合。

发布按多个subgraphs聚合读写和size_vars，每op直接写current_loop.axis，外层输入全Data；同buffer多个写者生成列表连接。它没有本文件主线ScalarData、重排、graph schedule、原名符号替换等本地定义；不从这点泛化发布其他实现没有同类能力。发布另有_Scalar(cse,max_value,check)保存对象，不能把它与主线ScalarData ABI混成同一个类型。

## asc_ops的文本缓存与完整直接映射

装饰器每次以原函数名、args、loop、kwargs的字符串组成graph.op_cache键，命中直接返回原对象；不是完整别名/环境/数学等价证明。Data/ScalarData/Output/Workspace跳过loop设置，其余用显式truthy loop或kernel.contiguous_loop；主线多输出先实体化list再统一as_loop，发布该通用分支仍构造generator。发布本文件实际暴露的函数没有同样完整多输出集合，不能把那段generic写法当已验证多输出能力。

以下99项只是将输入按表中槽位写入一个Op并返回y的完整直接映射（不含特殊属性/转换分支），dtype推导仍交外部AscIR。

| 本地形式 | Python名→AscIR名 |
| --- | --- |
| 一元：x→y | abs→Abs、sigmoid→Sigmoid、sqrt→Sqrt、log→Ln、rsqrt→Rsqrt、neg→Neg、exp→Exp、broadcast→Broadcast、transpose→Transpose、reciprocal→Reciprocal、exp2→Exp2、expm1→Expm1、floor→Floor、ceil→Ceil、round→Round、trunc→Trunc、sign→Sign、erf→Erf、erfc→Erfc、erfcx→Erfcx、erfinv→Erfinv、i0→I0、i0e→I0e、i1e→I1e、ndtri→Ndtri、log_ndtr→LogNdtr、airy_ai→AiryAi、bessel_j0→BesselJ0、bessel_j1→BesselJ1、bessel_y0→BesselY0、bessel_y1→BesselY1、modified_bessel_i0→ModifiedBesselI0、modified_bessel_i1→ModifiedBesselI1、modified_bessel_k0→ModifiedBesselK0、modified_bessel_k1→ModifiedBesselK1、scaled_modified_bessel_k0→ScaledModifiedBesselK0、scaled_modified_bessel_k1→ScaledModifiedBesselK1、spherical_bessel_j0→SphericalBesselJ0、digamma→Digamma、lgamma→Lgamma、log2→Log2、log10→Log10、log1p→Log1p、tanh→Tanh、sin→Sin、cos→Cos、sinh→Sinh、cosh→Cosh、tan→Tan、asin→Asin、asinh→Asinh、acos→Acos、acosh→Acosh、atan→Atan、atanh→Atanh、isnan→Isnan、isfinite→IsFinite、relu→Relu、gelu→Gelu、bitwise_not→BitwiseNot、logical_not→LogicalNot、nop→Nop |
| 二元：x1/x2→y | add→Add、sub→Sub、ge→Ge、gt→Gt、le→Le、lt→Lt、eq→Eq、ne→Ne、mul→Mul、maximum→Maximum、bitwise_and→BitwiseAnd、pow→Pow、minimum→Minimum、nextafter→NextAfter、igamma→Igamma、igammac→Igammac、zeta→Zeta、copysign→CopySign、hypot→Hypot、fmod→Fmod、mod→Mod、remainder→Remainder、floordiv→FloorDiv、truncdiv→TruncDiv、axpy→Axpy、bitwise_or→BitwiseOr、bitwise_xor→BitwiseXor、xor→Xor、logical_and→LogicalAnd、logical_or→LogicalOr、logical_xor→LogicalXor、bitwise_left_shift→LShift、bitwise_right_shift→RShift |
| 三元：x1/x2/x3→y | where→Where、fma→Fma、select→Select、clip_by_value→ClipByValue |

truediv只有x1恰为字符串'1'时转Reciprocal，div委托它，square用Mul(x,x)。atan2特意交换x1/x2。cast只写dst，src及use_compute_types没有在该helper驱动另一条计算；isinf/signbit显式bool，frexp显式mantissa=float32、exponent=int32，四个*_to_int的dst为keyword-only且缺省int32。leaky_relu写negative_slope=0.01缺省值，axpy没有在本wrapper额外设置alpha。

MM四类逐项写transpose/adj、has_relu、enable_hf32、offset_x和输出dtype，Bias作为额外输入；BMM使用adj_x1/adj_x2名称。注释将部分relu/offset标暂未实现，本wrapper赋属性不等于已证明后端执行这些组合。Concat的axis参与文本CSE但不直接写ir_attr，输出loop/shape由调用者提供。Data/ScalarData/Output舍弃原buffer名作为Op名、写index及dtype；Load/Store可记录offset，IndirectLoad保留axis/negative_index_support/need_check_bound/max；indirect_indexing本地仅返回输入，不自行做检查。

constant写Scalar字面文本，IndexExpr是无loop轴的符号占位；Arange把无自由符号的base/step包_SizeExprConstant。普通reduction按reduce_type.capitalize命名并记compute_type=reduce。多项式degree会剥Broadcast，仅Tensor Scalar可读作常量，否则TypeError；其他值最终int(...)，这里没有额外证明原值非负或本来就是整数。Chebyshev及shifted四族写整数attr.n，polygamma、Hermite H/He、Laguerre和Legendre则造int32 Scalar并显式Broadcast为n输入。

## Overrides暴露不等于已经实现

NPUOverrides多数方法只是转发同名ir操作。主线以下22个转发目标在asc_ops没有显式定义或别名：int_truediv、gammainc、gammaincc、i1、ndtr、and_、or_、to_dtype_bitcast、halide_clamp、device_assert_async、identity、inline_asm_elementwise、load_seed、rand、randint64、randn、masked、store_reduction、placeholder、scan、sort、bucketize。访问缺失模块名会进入__getattr__：正常抛NotImplementedError；debug_options含nothrow时才生成is_unsupported=True的占位并记录参数，图支持标记仍保留。unsupported(error_msg)则是另一个直接创建Unsupported类型节点的函数，不能与上述集合标记协议混同。发布没有同样的模块__getattr__，缺失显式目标不能被当作其本地实现。

还有静态签名边界：四个*_to_int转发按位置传dtype，而实际asc_ops只接受keyword-only dst；NPUOverrides的load/store/reduction通用转发参数也与本文件被装饰函数签名不同；output(*args)同样使用位置转发，而两版asc_ops.output只接受keyword-only的name/src/dtype/index。发布还独有NPUOverrides.check_bounds，直接转发ir.check_bounds，但所读发布asc_ops没有该显式定义，也没有模块__getattr__，不能把该门面当已实现边界检查。workspace wrapper向仅接收t的Op传name关键字，同样存在本地签名不一致。这些是从所存定义直接比较得到的静态结论，未触发运行；真实NPUKernel可有自己的load/store/reduction路径，不能据通用方法存在或签名问题推导所有模型必失败或全部已支持。partial_accumulate明确抛NotImplementedError，scan/sort/bucketize等转发也不因出现在类中成为AF能力矩阵。

主线to_dtype先在dst==src时直接返回（包括相同低精度），其余请求float16/bfloat16先改float32；src显式bool转非bool时造1/0、逐轴Broadcast再Select，其他走cast。constant同样把低精度改float32、bool值规范为1/0，再逐轴按前缀真实size/后缀1构造Broadcast链，无loop或无axis直接保留标量。发布仅把bf16改float32，没有这组bool/Broadcast分支；六比较在发布asc_ops里先把两输入Cast到float32，主线直接比较，数值影响需各自验证。

主线index_expr委托[完整索引Lowering](torchair_inductor_ascendc_index_expr_lowering.md)，indirect_indexing将本地identity结果包ASCIndexing并透传上下界开关；发布通用转发还把wrap_neg写成True，不能从参数名当可自由关闭。真实访存、边界、dtype白名单和融合结果继续按Lowering、中央IR及外部实现逐层核验。

## 本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/asc_graph.py)（primary）：1–521。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/asc_graph.py)（implementation）：1–340。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_ops.py)（implementation）：1–1335。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_ops.py)（implementation）：1–311。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_overrides.py)（implementation）：1–871。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/asc_overrides.py)（implementation）：1–821。
