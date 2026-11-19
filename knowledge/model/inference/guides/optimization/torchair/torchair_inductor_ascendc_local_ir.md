---
type: Guide
title: Inductor AscendC本地IR：Load/Store、模板与Gather
description: 核对完整npu.py中的本地值复用、低精度转型、Cat/MM/BMM构图、间接索引拆解及视图变换实际边界。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py
  role: implementation
created_at: '2026-11-11T04:24:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# Inductor AscendC本地IR：Load/Store、模板与Gather

本卡绑定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的npu.py实际本地调用。完整文件静态读取，未运行、导入或构建上游，产品未知保持draft/空平台。这里描述调用AscIR的参数和控制流；AscIR/Autofuse数学实现及设备支持另核。

## 物理布局、读取与内部值

两版ASCBuffer保存经sizevars简化的size/stride/offset、dtype和device.type，再计算Loop hints；bind把这些实际值及hint写到IR私有layout属性，asc_size仅逐项包AscExpr。hint不是运行时验证。Reduction小对象保存dtype/src_dtype/type/value/src，getitem直接返回自身供Welford式访问，str返回src。

主线普通load先识别ASCIndexing自由符号并走indirect_load；其余rename后，只有index字符串为0且is_cpu_0d_scalar判定真才用ScalarData并广播。普通路径把索引转Loop后_load_contiguous(upcast_dtype=True)。DataLoader记录物理名、offset、dtype和MoveOp road；view相同仅比较offset字符串及每步kind/src/dst，不在_same_loader_view内额外比较name或dtype，同物理名分桶由调用方负责。

_load_contiguous先normalize读取Loop。若命中_local_stores，直接用上游值，必要时先升FP32再按view road重排，避免同图Data/Output自环；外部buffer先分离offset再生成load。FP16/BF16的普通计算读取在transpose/broadcast前升FP32；空road也会升精度。启用load-transpose且组未命中inline白名单时，提取到最后一个transpose为止的前缀作为独立DataLoader，余下road继续在主图；同物理输入的不同view各有slot，原始连续读取有独立raw槽，详见[生成/转置合同](torchair_inductor_ascendc_schedule_codegen_wrapper.md)。

主线store和store_reduction对低精度先FP32再目标dtype，cast用清零offset的副本，实际Store再按原Loop分离offset。_store_buffer总是记录(value, loop.copy)，非最终输出直接返回值，只对_outputs发Store+Output，避免不必要的workspace往返；这说明本地IR意图，非设备内存实测。两条store都pop cse.store_cache且不传默认值，依赖上游已有cache条目。_get_reduce_dims_and_loop按stride字符串0识别归约轴。

reduction只接受sum/max/min/any/prod/argmax/argmin/welford_reduce，Welford委托专门构造，其余ir.reduction再设置dtype。argmax/min注释提及A2/A3限制，但该方法本体没有SoC判断，不能由注释登记一个已经执行的硬件gate。真正能进入融合还受[调度条件](torchair_inductor_ascendc_fusion_decisions.md)约束。

## Cat、矩阵模板与布局

Cat逐路优先使用本地Store值，否则取真实layout，只有AttributeError/NotImplementedError才转入_concat_input_layout helper解析物理/逻辑layout；_load_concat_input把物理Loop变为连续目标，读取可先升FP32，FP16/BF16在concat前再降原dtype。_concat_input_layout在查不到buffer、秩不一致时回退；大小全等沿用物理layout；全静态且actual>=expected时用expected size、物理stride和fallback offset；其余不等轴置stride0并保持物理offset。该helper本体没有“物理维必须等于1”的独立检查，不把它当任意广播安全证明；融合的轴/布局约束另行成立。

_make_partial_loop在输入秩过多时逐次去掉静态size1维，找不到则失败，最终秩必须等于规范秩；concat轴保留真实输入长度，其余取规范尺寸，并保留真实stride与offset。不是任意reshape或非连续layout都能通过。

MatMul无bias要求2输入，有bias要求3输入；逻辑input_layouts优先，否则buffer.get_layout。以输出m/n加独立k轴构图，矩阵转置视图通过交换末两轴/尺寸/stride表达，_make_matmul_input_loop的offset固定0，相应raw load也是offset0。bias按其秩取末尾轴，并使用bias layout offset分离。生成ir.matmul或matmul_bias，has_relu硬编码False；_get_enable_hf32只有torch.npu.matmul.allow_hf32存在且真才传0x40，否则0。不能由这一位推导全部精度模式/性能。

BatchMatMul在输出最后两轴前保留batch轴，k取A最后维；另外判断跨batch转置和末两轴转置。跨batch转置经_load_contiguous且upcast_dtype=False，普通分支直接load，bias同样用末尾轴及其offset。两类模板都_store_buffer供后续epilogue消费；是否模板已被正确Lowering、offset已由外层view表达、batch广播是否允许，均不能仅从这几个构图调用推定。

## Gather拆解、轴选择和检查

indirect_load对rename后的表达式拆解，只捕获RuntimeError补充buffer/index上下文。拆解要求恰好一个ASCIndexing自由符号，分别提取规范轴与indirect系数/offset，indirect系数须等于某个真实物理stride，取首个匹配轴；找不到失败。依据direct系数零轴决定gather是否在loop内，in-loop替换被选轴stride，gather物理维用完整buffer size，其他零stride轴size1。

_find_loop_gather_axis先找direct系数为0的候选：没有时返回占位0，唯一时直接用；多个时排除已识别归约轴尝试唯一，再按contiguous_loop stride与indirect系数匹配，仍歧义取第一个。归约轴由当前body.reduce_vars通过_current_var_to_expr的自由符号推得；上下文缺失返回空集。注释把无候选场景解释为2D embedding轴压缩，但本helper没有另做weight rank2/gather_axis0断言，不能把注释前提扩大成独立校验。

_gather_load先按构造data Loop读物理buffer，再把非gather的size1轴broadcast至loop尺寸，发ir.gather_load(axis=loop_gather_axis, negative_index_support=True, need_check_bound=True, max=物理gather维长, loop=当前loop)。这些是下游请求的属性，不是本次已验证运行边界。低精度结果再升FP32。check_bounds收集expr中ASCIndexing的asc_tensor，把expr/size/lower/upper交ir.check_bounds，没有在本地执行索引检查。普通、间接和标量buffer helper均按graph已有输入复用，否则绑定各自Data/ScalarData。

## 标准stride与view road

主线_index_to_loop先剥离trivial FloorDiv，再算stride、offset，并将重建的offset+Σstride×axis从原index相减；简化余项非0即RuntimeError。零stride对应size1。_get_view_road在src==dst返回空；否则要求同秩且每个src维为1或等于dst。按非零hint stride降序排列物理视图，必要时生成transpose，其dst重建DenseLoop；随后逐维将1升为目标尺寸，各broadcast dst也重建连续stride。不能把任意非仿射、split或负stride当该road可表达。

发布load也在低精度计算前升FP32，但无主线内部Store直连逻辑；store直接ir.store再绑定output，归约只直接ir.reduction且无上述枚举/Welford专门分支。旧indirect_indexing把index_var字符串按点拆成op/output，构造npu_scalar并保存_Scalar，_get_npu_scalar按自由符号查表；不等同主线ASCIndexing/Gather整链。旧_index_to_loop没有主线重建余项拒绝；旧view road采用逆向插入transpose/broadcast并最终改首步src，没有主线同秩/尺寸前置检查。这些差异仅限两固定本地实现，不能将旧helper存在解释成当前gather支持集合。

[轴映射](torchair_inductor_ascendc_axis_mapping.md)与[生成/Wrapper](torchair_inductor_ascendc_schedule_codegen_wrapper.md)共同说明实际落点，外部Lowering、Loop变换与AscIR实现仍分别保留覆盖。

## 固定实现证据

- [固定源码 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（primary）：105–147, 224–252, 371–389, 1679–2576。
- [固定源码 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（implementation）：33–75, 377–529。
