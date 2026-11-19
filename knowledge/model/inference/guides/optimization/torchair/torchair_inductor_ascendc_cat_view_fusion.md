---
type: Guide
title: Inductor AscendC Cat与Gather：布局、归约与View准入
description: 保留Cat/View设计，并补完整Cat与Gather实际Lowering、FX/IR双层布局证明、多轴归约回退和共享分支物化。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/cat_fusion_summary.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/cat_fusion_summary_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/view_like_fusion_rules.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/view_like_fusion_rules_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/cat_lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/gather_lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/indirect_reduction.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/common.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC Cat与View融合：布局、静态轴和独占用户条件

## 固定来源与范围

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的Cat与View双语设计。整套融合没有独立完整产品矩阵，保留draft/空platforms；文中的Soc.A5指Ascend950系列（包含旧称Atlas A5），只用于明确的转置门控，不扩成全部算子/版本支持。未运行融合或性能实验。

## Cat从分解到Lowering

保留原生Inductor cat分解：过滤相应空1D输入、单输入转clone并处理dtype；同一对象重复输入可经unsqueeze/expand/flatten/clone处理。普通多输入形态的NotImplemented表示保留cat给后续Lowering，不等于立即判定Unsupported或关闭所有融合。

NPUConcatBuffer继承TemplateBuffer并记录输入、轴和layout，没有普通elementwise的inner_fn/body，不套用TritonTemplateBuffer的实现假设。输出固定layout在concat轴求和。非NPU调用保留原路径；设计最多64输入是编译成本启发式，不是任意更多输入都报错或截断。

concat轴及其后的维须静态，之前的轴可动态：dim=1时(s0,5)和(s0,11)可保持动态前轴；dim=0本身动态或之后维动态则不满足此路径。不能把dynamic=True整体解释成Cat不支持，也不能把单例推广所有stride和dtype。

## 融合前后约束

Prologue只接受相应纯elementwise；broadcast/slice通过layout吸收，与普通Prologue节点路径不同；reduction、matmul、gather不属于该纯elementwise前融合。Epilogue也限elementwise。含cat的节点不做此处水平融合，多cat组合不在本路径。

独占用户检查发生在调度节点和实际融合关系层：调度器可能复制Prologue到多个Kernel，也可能先把多个Epilogue水平合成单consumer，不能简化为“Python里任何多用户都不融合”。override返回True时走扩展决策，False还可继续原始判断，不把False一律当最终拒绝。

设计记录构造用例未触发_share_concat，只是来源测试/实现观察，不登记为所有输入均不可达。nocat/nocanfuse等调试开关分别控制路径；Lowered统计、算子名出现在文件名和真正减少Kernel数仍是不同证据。

## View、轴语义与转置门控

reshape/_unsafe_view、slice/select、unsqueeze/expand、transpose/permute主要表达布局或索引。slice需要保留真实stride/storage offset，广播需要可证明轴映射；非连续输入可能先通过独立重排形成规整buffer，不保证view永远零开销或所有elementwise链均合一。

reshape只允许静态、contiguous、strict split-axis子集；merge、跳轴重组、动态或非连续不由此放开。文档示例只列目标shape，输入shape未给出时不能仅凭reshape(2,12)这个字符串认定本次一定merge。

原设计中名为_kernel_has_reduction_or_concat_or_matmul的门控描述为转置inline白名单：低于Soc.A5直接切分；有reduction/concat/matmul/batch matmul切分；其他节点须为纯elementwise、允许的indirect indexing，或origin属于expand、permute、reshape、select、slice、squeeze、transpose、unsqueeze、view。950仍须满足dtype、布局及轴证明，不据架构名保证inline。

简单transpose→elementwise/broadcast/slice/gather及白名单view链有机会内联，复杂后继、复杂stride、多consumer会使条件更难成立；noloadtrans关闭默认独立切分不能替代正确性证明。设计提示不同代际dtype白名单不同，尤其int8/int16/uint类，未提供完整表时不补齐支持集合。

## 模型侧验证

先保持view关系简单、选择稳定子模块范围，再检查融合前后IR及output_code.py中是否仍有外部aten调用、Lowered/Fallback原因和生成转置调用；无外部view调用也不单独证明只有一个Kernel。保存真实shape/stride/dtype与关闭单项融合的对照，比较数值、Kernel数、内存和端到端时间。两篇外链PR仅作来源指针，其讨论内容未因此自动摄取。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/cat_fusion_summary.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/cat_fusion_summary_en.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/view_like_fusion_rules.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/view_like_fusion_rules_en.md)（constraint）

## 完整Lowering实现补充与设计边界

本次完整读取同一固定主线的cat_lowering.py、gather_lowering.py与indirect_reduction.py；固定发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这三个具体路径，这只说明所存目录差异。Soc.A5对应Ascend950系列（包含旧称Atlas A5）的代码门控，未知SoC分支也会注册相关路径，产品资格继续保持未知。前文保留的是设计描述，中央实际调度和转置helper见[融合决策](torchair_inductor_ascendc_fusion_decisions.md)、[生成/转置](torchair_inductor_ascendc_schedule_codegen_wrapper.md)，不把设计中的旧helper名当现实现符号。

## Cat的两条实际输出路径

Cat guard先登记F，再在since=A5登记F+八类整数+bool；集合和覆盖规则见[dtype白名单](torchair_inductor_ascendc_lowering_dtype_registry.md)。实际Lowering直接注册cat.default及存在时的cat.names overload，type_promotion_kind=None。模块先快照origin_lowerings；非NPU且非CPU调试时委托原default或fallback，超过max_cat_lowering_inputs也回原ATen。输入上限来自配置变量，源码注释的64只是该配置设计说明。

_npu_cat在过滤None及非空assert前就访问inputs[0].get_device，输入数检查也在过滤之前；它没有为任意空列表或首项None提供通用保护。过滤后保留顺序，逐项promote_types并to_dtype成同一dtype，负dim加rank，再仅检查首路concat轴及后面维度经简化后为int/sympy.Integer；普通rank/dim及其他输入shape合法性不能从这几行补成独立完整校验。

普通路径先保留各输入logical layout（get_layout仅NotImplementedError时构造连续FixedLayout），再realize全部输入，输出concat轴求和、连续FixedLayout，unwrap_storage后构造NPUConcatBuffer。模板保存input_layouts/axis，继承TemplateBuffer且make_kernel_render=None，不挂普通body。保留logical layout先于unwrap/realize，供后续维持view/slice语义。

另一条ConcatKernel/store路径要求至少一条可内联gather来源。FX层检查cat packet、已登记dtype、0<输入数<=上限、所有输入/输出meta为Tensor、int且合法的dim、首路concat轴及后维静态、各路目标slice Store布局；再沿args[0]最多穿10个已支持view查gather family。reshape/view还调用外部静态连续reshape准入，未因这次调用关闭其主体覆盖。

_node_dtypes_supported只检查all_input_nodes中meta.val直接为Tensor的项及单Tensor输出；元组/列表meta和非Tensor输入没有在该helper递归校验。view回溯只沿位置args[0]，不泛称可跨任意参数图。FX候选仍不足：IR阶段重新推导实际输出stride，包含comprehensive_padding及channels_last选择，再要求所有目标slice的最内非1轴stride可证明1，外层间隔可以保留，全singleton也可过。固定IR输入有任一路channels_last就选对应输出格式，只有全部IR输入没有storage/layout时才用FX channels_last/3d元数据。

最后至少一条对应IR输入的loader仍含MemoryDep.is_indirect才内联，检查期间临时允许FlexibleLayout索引，不为检查主动realize；异常回False。已成为稳定extern结果的gather不因此拆成多路copy；不满足任一条件便保持NPUConcatBuffer。这个Lowering/store分流与“Gather不能作Cat模板普通prologue”的调度规则处在不同层次。

## Gather数据连续化与结果共享

Gather、Embedding、IndexSelect packet及index.Tensor的guard为F+int32/int64，since=A5；wrapper实际定义在current_soc为None或>=A5时，较低已识别SoC保留原Lowering。这里的dtype登记不代替indices参数本身的原生合法性检查。gather/embedding委托保存的原handler，结果通常保持Pointwise延迟；回退handler创建时add_to_fallback_set=False。

_maybe_materialize_for_indirect只处理TensorBox。存在layout且stride非None时与FlexibleLayout.contiguous_strides逐项比较；无layout则对Pointwise get_reads追踪有效MemoryDep访问，非Pointwise、异常或任何不连续读会要求物化。实现没有对zip两侧长度或offset加同样独立检查。**layout.stride为None时保持不物化，无有效MemoryDep读时也返回不物化**，不能照注释写成任何未知都强制clone。

需要物化才调用原clone Lowering和realize；返回name非None才加入no_fuse_buffer_names，存在对应属性时设_force_realize=True，layout有as_fixed再转FixedLayout，避免后续loader重新内联非连续Pointwise。结果共享helper是另一路：下游有fanout且多个单轴归约时只realize结果并尝试_force_realize，不在这个helper另加no_fuse或固定layout。

index_select先做回退判定、data连续化与TensorBox assert，再_validate_dim。空index按替换该轴长度new_empty，仍可能已发生前面的data准备；非空Pointwise在idx[dim]处从一维index_loader读取值，经ops.indirect_indexing替代原索引，返回x_loader，最后考虑共享。index.Tensor去掉None后，bool/uint8索引、多于一个索引或回退判定真时先x.realize再extern；零个索引没有在该wrapper独立拒绝，其他参数与原handler验证仍需保留。

## 多轴归约回退是图内路径分析

indirect_reduction识别reduction tag；无tag的prims.sum/prod/amax/amin/var另列集合。normalized_shape类包含可取得的layer_norm/native_layer_norm/rms_norm/_fused_rms_norm，dim类包括softmax/log_softmax及所列安全/反向变体；group_norm/native_group_norm及若干norm反向按已知但轴数未知保守回退。未知普通算子不自动成为风险源，但继续看下游。

schema解析合并位置、关键字及默认参数，输入rank从self/inp/input的FX Tensor meta取。dim为None或空列表表示全轴：rank未知拒绝，rank>1多轴拒绝；原生int轴才静态规范化，bool不按int接收。单元素的符号轴列表仍按单轴计，具体合法性交原生；rank已知时检查范围并将负轴规范化，多个不同轴回退。normalized_shape只按非空tuple/list长度计轴，维度长度本身可动态。

_analyze_paths逆拓扑为每节点保留一个cause，所有可能Tensor路径继续传播，包括MM/view/clone及单轴归约；缺meta视为可能Tensor，显式非Tensor则止。只在已注册handler的_is_fallback_handler精确为True时停止，不以算子名猜融合边界。一条下游路径有已知多轴/未知轴归约，整个当前间接索引节点回ATen图内extern，不等于Dynamo graph break。

should_fallback_indirect要求当前FX Node与target同一对象，否则True；普通非CPU调试下若输出meta为CPU Tensor直接False。其余要求节点属于V.graph.module.graph，缓存按graph对象身份复用，不按图内容版本自动刷新；节点不在cache也保守True。此helper没有对任意已识别归约的坏schema统一catch并恢复。

should_materialize_indirect_for_reductions用visited遍历Tensor users，排output；识别某节点有多个users才记fanout，去重节点后累积可接受归约分支数：_single_axis_reduction_count以_reduction_reason为None时计1，var_mean计2；rank为0的all-axis也可返回None而未单独剔除，因此该计数不独立证明恰有一个有效归约轴。遇fallback边界停止向后，但当前节点的归约计数已在停止前完成；最终fanout且count>1才共享realize。它只检查当前节点/target，不另做前一helper同样的CPU或graph所属检查。

这些逐层证明决定内联、模板、共享物化或extern位置；实际Kernel、索引越界与数值验收继续由[中央IR](torchair_inductor_ascendc_local_ir.md)及外部原生实现分别核对，本次没有执行数据追踪、clone、lowering或设备调用。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/cat_lowering.py)（implementation）：1–296。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/gather_lowering.py)（implementation）：1–216。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/indirect_reduction.py)（implementation）：1–246。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/common.py)（implementation）：12–32, 155–220。
