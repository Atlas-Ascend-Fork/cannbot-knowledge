---
type: Guide
title: Inductor AscendC Lowering白名单：dtype登记与诊断统计
description: 完整归并250条ATen/Prims输入输出dtype登记，说明覆盖顺序、未知SoC、LowerSummary和NPU allfallback实际行为。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/common.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/aten_lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/npu_lowering.py
  role: implementation
created_at: '2026-11-11T05:08:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC Lowering白名单：dtype登记与诊断统计

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c，完整读取lowering/common.py、aten_lowering.py及npu_lowering.py。本卡仅描述本地dtype登记和诊断分支，保持draft/空平台，没有导入上游或执行Lowering。Soc.A5在此指代码对Ascend950系列（包含旧称Atlas A5）的枚举门控；源码集合、PR讨论和未列分支都不补成产品支持矩阵。固定发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有本包这些具体路径，其他路径/版本能力另核。

## 表的语义与覆盖顺序

_LoweringGuard把OpOverload映射为(输入dtype tuple,输出dtype tuple)。support的输出为None时沿用输入；packet展开当时ops.overloads()，直接overload包成一项，多个相同key按后一次赋值覆盖。只有current_soc与since均为真且current_soc<since才跳过登记；未知SoC并不会自动拒绝since条目。整个框架怎样调用guard、跨模块导入顺序、所配Torch的全部overload集合不在本模块重新定义。

下面完整蒸馏aten_lowering.py的250次support为50组相同成员集合，保留准确操作表达式和源码行号。相同操作或显式overload出现多次时按原行号决定顺序，**不是把基础和A5项求并集**。packet项也不能视为已枚举每个实际overload。此文件只登记metadata，未替这些操作重新实现Lowering、dtype cast或设备Kernel；真正融合仍见[中央调度](torchair_inductor_ascendc_fusion_decisions.md)。

集合缩写：F={float16,float32,bfloat16}；I={int8,int16,int32,int64,uint8,uint16,uint32,uint64}；S为四种有符号整数；B={uint8,bool}；T=F+I+bool；P=F+S+uint8+bool；LI=F+S+bool；LO=F+int16+int32+int64+bool。加号表示成员并集，表内只比较成员，不依赖tuple顺序。exclude的本地全集只有这12种T，不能把“排除某dtype”理解成还包括float64、float8或complex。

|源码门控|输入集合|输出集合|登记表达式（括号为起始行）|
|---|---|---|---|
|无since限制|F+{int16,int32}|F+{int16,int32}|aten.add(L28)、aten.add_(L32)、aten.sub(L36)、aten.sub_(L40)、aten.mul(L44)、aten.mul_(L53)、aten.square(L113)、aten.maximum(L121)、aten.minimum(L125)、aten.neg(L258)、aten.clamp_min(L266)、aten.clamp_max(L270)|
|since=A5|F+I|F+I|aten.add(L29)、aten.add_(L33)、aten.sub(L37)、aten.sub_(L41)、aten.maximum(L122)、aten.minimum(L126)、aten.clamp_min(L267)、aten.clamp_max(L271)、aten.empty(L334)|
|since=A5|P+{uint32,uint64}|P+{uint32,uint64}|aten.mul(L45)、aten.mul_(L54)|
|无since限制|F+{int32}|F+{int32}|aten.div(L62)、aten.div_(L71)、aten.true_divide(L80)、aten.pow(L84)、aten.remainder(L95)、aten.floor_divide(L98)、aten.abs(L107)、aten.relu(L244)、aten.sgn(L249)、aten.sign(L253)、aten.empty(L333)、aten.empty_like(L352)、aten.lift_fresh_copy(L365)|
|since=A5|P|F+{int16,int32,int64,int8,uint8}|aten.div(L63)、aten.div_(L72)、aten.floor_divide(L99)、aten.floor_divide_(L686)|
|since=A5|P|F|aten.true_divide(L81)、aten.exp(L130)、aten.expm1(L133)、aten.rsqrt(L137)、aten.sqrt(L141)、aten.log(L155)、aten.log10(L158)、aten.log1p(L161)、aten.cos(L179)、aten.sin(L182)、aten.tanh(L186)、aten.tan(L189)、aten.cosh(L192)、aten.sinh(L195)、aten.acos(L198)、aten.acosh(L201)、aten.asin(L204)、aten.asinh(L207)、aten.atan(L210)、aten.atanh(L213)、aten.lgamma(L219)、aten.erfc(L222)、aten.erf(L263)、aten.special_erf(L275)、aten.special_ndtr(L278)、aten.exp2(L461)、aten.log2(L464)、aten.atan2(L467)、aten.erfinv(L470)、aten.digamma(L473)、aten.i0(L476)、aten.special_erfcx(L479)、aten.special_ndtri(L482)、aten.special_log_ndtr(L485)、aten.special_i0e(L490)、aten.special_i1e(L493)、aten.special_airy_ai(L496)、aten.special_bessel_j0(L501)、aten.special_bessel_j1(L506)、aten.special_bessel_y0(L511)、aten.special_bessel_y1(L516)、aten.special_modified_bessel_i0(L521)、aten.special_modified_bessel_i1(L526)、aten.special_modified_bessel_k0(L531)、aten.special_modified_bessel_k1(L536)、aten.special_scaled_modified_bessel_k0(L541)、aten.special_scaled_modified_bessel_k1(L546)、aten.special_spherical_bessel_j0(L551)、aten.special_zeta(L556)、aten.polygamma(L583)、aten.special_chebyshev_polynomial_t(L592)、aten.special_chebyshev_polynomial_u(L597)、aten.special_chebyshev_polynomial_v(L602)、aten.special_chebyshev_polynomial_w(L607)、aten.special_shifted_chebyshev_polynomial_t(L612)、aten.special_shifted_chebyshev_polynomial_u(L620)、aten.special_shifted_chebyshev_polynomial_v(L628)、aten.special_shifted_chebyshev_polynomial_w(L636)、aten.special_hermite_polynomial_h(L644)、aten.special_hermite_polynomial_he(L649)、aten.special_laguerre_polynomial_l(L654)、aten.special_legendre_polynomial_p(L659)、aten.true_divide_(L683)|
|since=A5|F+{int16,int32,int8,uint16,uint32,uint8}|F+{int16,int32,int8,uint16,uint32,uint8}|aten.pow(L85)|
|since=A5|F+{int16,int8,uint8}|F+{int16,int8,uint8}|aten.fmod(L92)|
|since=A5|F+{int16,int32,int64,int8,uint8}|F+{int16,int32,int64,int8,uint8}|aten.abs(L108)、aten.ceil(L164)、aten.floor(L169)、aten.round(L174)、aten.full(L341)、aten.scalar_tensor(L347)、aten.fill_(L357)、aten.trunc(L664)、aten.amax(L718)、aten.amin(L724)|
|since=A5|F+{int16,int32,int64,int8,uint32,uint64,uint8}|F+{int16,int32,int64,int8,uint32,uint64,uint8}|aten.square(L114)|
|无since限制|F|F|aten.exp(L129)、aten.rsqrt(L136)、aten.sqrt(L140)、aten.reciprocal(L144)、aten.tanh(L185)、aten.sigmoid(L238)、aten.silu(L241)、aten.erf(L262)、aten.special_erf(L274)、aten.new_empty(L315)、aten.arange(L319)、aten.copy(L330)、aten._to_copy(L362)、aten.sum(L702)、aten.mean(L706)、aten.max(L709)、aten.min(L713)、aten.amax(L717)、aten.amin(L723)、aten.var_mean(L729)、aten.squeeze(L742)、aten.reshape(L746)、aten._unsafe_view(L750)、aten.permute(L753)、aten.t(L771)、aten.alias(L792)、aten.sym_size(L796)、aten.detach(L802)|
|since=A5|P+{uint64}|F+{int64,uint64}|aten.reciprocal(L146)|
|无since限制|{float16,float32}|{float16,float32}|aten.log(L154)|
|since=A5|F|F|aten.copysign(L216)、prims.fma(L227)、aten.hypot(L559)、aten.special_gammainc(L562)、aten.special_gammaincc(L565)、aten.igamma(L568)、aten.igammac(L571)|
|无since限制|F+{bool,int32,uint8}|F+{bool,int32,uint8}|prims.convert_element_type(L232)|
|since=A5|F+{bool,int32,int64}|F+{bool,int32,int64}|prims.convert_element_type(L233)|
|since=A5|F+{int32,int64,uint8}|F+{int32,int64,uint8}|aten.relu(L245)、aten.sgn(L250)、aten.sign(L254)|
|since=A5|F+{int16,int32,int64,int8}|F+{int16,int32,int64,int8}|aten.neg(L259)|
|无since限制|F+{int32}|B|aten.ge(L286)、aten.le(L290)、aten.eq(L302)、aten.ne(L306)|
|since=A5|T|B|aten.ge(L287)、aten.le(L291)、aten.gt(L295)、aten.lt(L299)、aten.eq(L303)、aten.ne(L307)|
|无since限制|{float16,float32,int32}|{uint8}|aten.gt(L294)、aten.lt(L298)|
|无since限制|F|B|aten.isnan(L310)|
|since=A5|T|T|aten.new_empty(L316)、aten.copy_(L327)、aten.empty.memory_format(L337)、aten.empty_like(L353)、aten.unsqueeze(L739)、aten.squeeze(L743)、aten.clone(L756)、aten.select(L760)、aten.slice(L764)、aten.split(L768)、aten.alias(L793)、aten.sym_size.int(L799)、aten.detach(L803)|
|since=A5|{int32,int64}|{int32,int64}|aten.arange(L320)、prims.iota(L323)|
|无since限制|P+{uint16,uint32}|P+{uint16,uint32}|aten.copy_(L326)、aten.unsqueeze(L738)、aten.select(L759)、aten.slice(L763)、aten.split(L767)|
|无since限制|F+{int32,uint8}|F+{int32,uint8}|aten.full(L340)、aten.scalar_tensor(L346)、aten.fill_(L356)|
|since=A5|F+{int32,int64}|F+{int32,int64}|aten.lift_fresh_copy(L366)、aten.reshape(L747)、aten.tril(L806)、aten.triu(L809)|
|无since限制|{int16,int32,uint16,uint8}|{int16,int32,uint16,uint8}|aten.bitwise_and(L371)、aten.bitwise_and_(L375)、aten.__and__(L394)、aten.__iand__(L401)|
|since=A5|I+bool|I+bool|aten.bitwise_and(L372)、aten.bitwise_and_(L376)、aten.bitwise_or(L379)、aten.bitwise_or_(L382)、aten.bitwise_xor(L385)、aten.bitwise_xor_(L388)、aten.bitwise_not(L391)、aten.__and__(L395)、aten.__or__(L398)、aten.__iand__(L402)、aten.__ixor__(L405)、aten.__xor__(L669)、aten.__ior__(L672)|
|无since限制|{bool}|{bool}|aten.logical_and(L408)、aten.logical_and_(L414)、aten.logical_not(L418)、aten.logical_not_(L424)、aten.logical_or(L428)、aten.logical_or_(L434)|
|since=A5|T|{bool}|aten.logical_and(L409)、aten.logical_not(L419)、aten.logical_or(L429)、aten.isinf(L589)|
|since=A5|T|LO|aten.logical_and_(L415)、aten.logical_not_(L425)、aten.logical_or_(L435)|
|无since限制|F+{bool,int16,int32,uint8}|F+{int16,int32}|aten.where(L440)|
|since=A5|T|F+I|aten.where(L454)|
|since=A5|{float32}|{float32}|aten.nextafter(L574)|
|since=A5|F|F+{int32}|aten.frexp(L577)、prims.frexp(L580)|
|since=A5|F+{int32}|{bool}|aten.signbit(L586)|
|since=A5|LI|{bool}|aten.logical_xor(L675)|
|since=A5|LI|LO|aten.logical_xor_(L678)|
|since=A5|S|S|aten.bitwise_left_shift(L694)、aten.bitwise_right_shift(L697)|
|since=A5|F+{int32}|F+{int32}|aten.sum(L703)|
|since=A5|F+{int16,int32,int8,uint8}|F+{int16,int32,int8,uint8}|aten.max(L710)、aten.min(L714)|
|无since限制|F+{bool,uint8}|F+{bool,uint8}|aten.sum.dim_IntList(L732)|
|since=A5|F+{bool,int32,uint8}|F+{bool,int32,uint8}|aten.sum.dim_IntList(L733)|
|无since限制|F+{int16,int32,uint16,uint32}|F+{int16,int32,uint16,uint32}|aten.transpose(L774)|
|since=A5|F+{bool,int16,int32,uint16,uint32}|F+{bool,int16,int32,uint16,uint32}|aten.transpose(L775)|
|无since限制|F+{bool,int16,int32,int8,uint16,uint32,uint64,uint8}|F+{bool,int16,int32,int8,uint16,uint32,uint64,uint8}|aten.expand(L780)|
|since=A5|I+bool+{float16,float32}|I+bool+{float16,float32}|aten.expand(L781)|
|无since限制|F+{int16,int32,int8,uint8}|F+{int16,int32,int8,uint8}|aten.repeat(L784)|
|since=A5|P|P|aten.repeat(L785)|

这组覆盖存在有意的非单调变化：A5 arange将原F改为int32/int64；convert_element_type移除原uint8、加入int64；expand从exclude(int64)改为exclude(bfloat16)。sum.dim_IntList、empty.memory_format、sym_size.int等后续显式overload会覆盖packet已登记的对应key。比较/逻辑操作的输入输出集合分别检查，例如基础gt/lt输出仅uint8，而A5输出B；inplace逻辑输出LO与其输入不同。不能凭算子名称或“新代际”推断所有dtype都更宽。

float_dtypes为F，byte_dtypes为B，int_dtypes仅int32，all_int_dtypes为I。common里的gather family集合为index/embedding/gather/index_select，view集合为reshape/view/permute/transpose/unsqueeze/squeeze/slice/expand/select；它们只供具体检查使用，完整准入继续见[Cat与Gather](torchair_inductor_ascendc_cat_view_fusion.md)、[MM模板](torchair_inductor_ascendc_matmul_lowering_contract.md)。

## LowerSummary统计实际调用形态

LowerSummary构造时只有TORCH_COMPILE_DEBUG精确为1才使能，并在原decompositions清空前快照key集合。_node_key把FX target、位置/关键字参数及输出meta.val拼成文本；Tensor包含dtype/shape/stride/device，其他值str。lowered/fallback按这个key累加进程字典，fallback另附原因、当前lowerings是否有此OpOverload及原decomposition集合是否包含它。这是诊断计数，不是Kernel数量、数值通过或性能收益。

begin_graph用threading.local记AOT图名、depth及本图两个计数字典，嵌套时depth加一；end_graph减一到0后先删除线程状态再_log，避免日志handler失败把状态带入下一图。没有本地depth负值校验或进程字典锁。save仅在使能且有记录时输出Process汇总，模块用atexit登记调用；本次只读了这些路径，没有执行注册或退出日志。

## 两个NPU cast及allfallback

npu._npu_dtype_cast与npu.npu_dtype_cast用type_promotion_kind=None登记to_dtype(x,dtype,copy=True)，guard输入/输出为F。debug_options包含allfallback时，对这两个packet显式make_fallback(warn=False)，再包装各overload，弥补图级hook只处理aten/prim/prims的本地范围。

包装器仅在V.get_current_node是实际FX Node且target与对应overload同一对象时记录forced原因，随后始终调用原handler；functools.wraps保留属性，再显式设置_is_fallback_handler及_npu_ext_fallback_wrapped。重复登记遇到已包装标记True则跳过，避免叠多层。它不将任意NPU命名空间算子全部重新注册，也没有在这里启动CPU或设备计算。

这些实际注册、可变统计和门控与模型精度/性能验收分别保留，外部Torch Lowering表、AscIR映射和CANN实现未因被导入而取得完整资格。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/common.py)（primary）：1–220。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/aten_lowering.py)（implementation）：1–809。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/npu_lowering.py)（implementation）：1–90。
