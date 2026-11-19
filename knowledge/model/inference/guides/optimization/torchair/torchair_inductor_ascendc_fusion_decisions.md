---
type: Guide
title: Inductor AscendC融合决策：CV、Cat与间接索引门控
description: 完整审阅中央调度器的布局/依赖/广播约束、Triton否决旁路及版本差异，区分局部放行与最终融合。
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


# Inductor AscendC融合决策：CV、Cat与间接索引门控

本卡只陈述TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013所读npu.py的完整本地调度实现；不把主线代码推广到发布、硬件或所有模型。未运行上游，保持draft/空平台。设计层先见[Cat/View](torchair_inductor_ascendc_cat_view_fusion.md)，数学与索引落点见[规范轴](torchair_inductor_ascendc_axis_mapping.md)、[本地IR](torchair_inductor_ascendc_local_ir.md)。

## 入口、状态与共同证明

主线按disable_cat_fuse选择真实NPUConcatBuffer导入或空占位类，enable_matmul_fuse选择MM/BMM导入或两个空占位类；不能仅因源码出现类型名认定模板已启用。NPUScheduling持TritonScheduling作参考判断，另存kernel、轴映射和转置相关cache。模板查找遍历get_nodes，_find_matmul_info同时保留实际模板子节点，避免把已融合epilogue依赖当模板原输入。

输出名、read名与依赖名是不同集合：data reads保留MemoryDep，也兼容非Dep但有name的对象；普通read_names不做此筛选，dependency_names额外加入met/unmet依赖。vertical先要求生产输出被消费读取；MM另要求真实data依赖。_axis_mapping_fusion_decision以候选子节点名字元组为key，在计时区间调用轻量_NPUAxisMappingValidator（args/nodes/outputs/local_stores），异常缓存为拒绝及原因，成功缓存为可映射，不在此执行设备。

_Triton判断异常视False。形状split预检把静态非1轴做multiset包含比较，动态无法int化返回True作为未拒绝；读取ranges异常/空也不在这一项拒绝，仍须后续轴证明。普通vertical相连Store要连续，dep.is_contiguous先短路；否则offset须0且实际stride等于按size构造的连续stride，异常拒绝。read/write信息缺失时_vertical_outputs_are_contiguous返回True，不能写成所有缺信息都fail-closed。

## MatMul/BatchMatMul只向后CV融合

任何向MM/BMM原输入生产结果的prologue都拒绝，水平融合只要一方含MM/BMM便拒绝。相关候选通过专门包装器查snodes，计时/检查异常返回False；普通候选没有这一层统一catch。CV候选优先级返回1，其余0，源码意图是在VV后处理，并不证明每个外部调度器按何种顺序完成。

MM producer且consumer读取其输出时，_matmul_epilogue_fusion_status返回(是否epilogue,是否允许,原因)，内部异常保守返回(是,否,异常)。实际检查依次覆盖：

- consumer读写信息及data依赖；epilogue独有额外输入须有可解析Layout，NoneLayout通过mutation_real_name追真实storage，缺映射/循环拒绝。物理layout先按逆序检查compact+广播；MemoryDep访问层在var_names和dep.size同时为空时跳过，仅单方缺失或长度不一致时拒绝，两者均存在且长度一致才做访问stride证明。两层实际检查时均跳过size1或stride0轴，其余stride必须等于累计stride。捕获列出的布局/访问异常并拒绝；本检查没有单独的storage_offset为0条件。
- 额外共享的computed MM输入、consumer origin与非graph-input模板输入producer的origin身份交集均拒绝，避免把输入生产链当作普通后融合。真正允许CV时，模板输入与epilogue读名交集加入never_reuse_buffers，防止输出复用这些仍被Cube读取的输入。
- Cat、归约、带loop轴的INDEX_EXPR拒绝。轴相关检查使用body.var_ranges名与index表达式自由符号名交集，纯sizevar不因此拒绝。只含load/store/output、cast/bitcast、constant、index_expr或identity的链没有vector compute而拒绝，不能将仅cast的模板当有效CV tiling。
- MM输出broadcast拒绝：先查访问中非1轴stride0且MM同位置维不等，再处理依赖丢掉singleton轴后的consumer缺失非1轴。若依赖元素总数等于整个MM输出，还比较consumer numel：等量或可证明更小不由flatten检查拒绝，未知或更大保守拒绝，避免flatten隐藏新增广播轴。
- epilogue额外输入的stride0广播，在同秩时要求对应consumer维等于MM维；变秩时只有能连续合并MM非1轴的consumer形状可放行，否则相关广播轴拒绝。MM有1维或动态维不能证明>=2时，再沿data依赖追踪全部派生consumer，要求去1后的consumer轴只是连续合并，而非拆分/重排。
- origin禁用表为slice、split、gather、clone。提取只识别aten.或aten::前缀（可去torch.ops.），然后用子串包含匹配，不能把表写成只匹配四个精确全名；既看consumer输出origin，也看排除producer输出/MM输入后的额外输入origin。origin文本沿输出alias递归，visited防环，仅对alias查询NotImplementedError回空；origin身份比对保留节点name或id及target。
- transpose-like访问按去掉size1/stride0后的相邻stride顺序判断，静态无法证明递减也保守视可能转置。MM原输入的末两轴转置有局部例外，但同一逻辑转置同时用于prologue输入与epilogue时仍拒绝，其他transpose-like reads拒绝。
- BMM额外检查所有非producer输出读依赖：输出最后两轴以外的非1轴为batch轴。缺失/不一致访问轴、不能连续映射到MM轴前缀、未消费的batch轴或batch组stride0都拒绝；异常同样拒绝。仅m/n广播不被这个batch门控单独禁止，仍需前面全部条件。

通过CV专门检查仍须consumer无indirect且整体轴映射成功，才由vertical返回True。不能用triton_result或单个表项代替这些累计检查。

## Cat的前后与兄弟输入

Cat prologue/epilogue用真实concat input/output名确认数据关系。前驱独占检查遍历全部producer子节点输出，允许producer内部users及Cat本身；只有直接Cat输入作为图输出时可例外，不允许其他外部输出链混入。Epilogue只允许Cat输出被当前consumer组或没有get_nodes的图输出使用。这里按是否有get_nodes判断图输出例外，不是对任意对象执行类型认证。

普通vertical最多一侧含一个Cat，另一侧必须_pure_elementwise；直接前后关系还要独占用户与连续写入，最后用轴映射。_is_pure_elementwise本体只排除reduction、MM/BMM、Cat、indirect，没有另查所有算子opcode或transpose属性；其名字/注释不是完整数学白名单。

scheduler_can_fuse_override还提前排除disable、自身、任一MM、反向ancestor、不同device、no_fuse buffer、alias/mutation、reduction及超过一个indirect子节点，再考虑_maybe_concat_fuse。该helper的前后分支另外要求正向ancestor、原scheduler允许vertical依赖、纯elementwise/独占/连续写入和轴映射。兄弟输入水平分支只要两组输出喂同一Cat、各组无Cat、无互相ancestor，再做轴映射；这里不是含Cat模板本身的水平融合。override的False与整个外部调度流程最终拒绝仍须区分。

## 普通VV、归约与Gather

vertical间接索引数量按“含indirect_vars的子节点数”计，合计>1拒绝。indirect producer后继限elementwise/reduce，indirect consumer前驱限pure_elementwise；若有indirect，任何归约在原IR或scheduler ranges有超过一条归约轴都拒绝。单轴归约仍继续所有轴/Triton检查，不是无条件强融。

horizontal允许多个indirect子节点，但每个仅一个indirect变量，并且整个组无归约、MM或Cat。多个时须精确相同签名：支持gather/index_select、embedding以及只一个非None索引的aten.index.Tensor，取FX meta.val中的index shape、规范化dim和body.var_ranges值；缺数据/meta、非int dim或多个匹配origin时签名None而拒绝。这与vertical“最多一个子节点”的规则不同；不是全部gather可水平融合。

普通horizontal先排MM，检查间接兼容，排含Cat模板；同Cat兄弟输入可按轴映射单独放行，其余要求轴映射与Triton都成功。普通vertical中Cat或合格CV走自身路径；其余在轴映射成功而Triton否决时，只有enable_load_transpose且恰好一侧归约才可能旁路，且循环空间必须结构兼容：pw与red的iteration或完整iteration×reduction相等。red+red不触发此旁路；不能以“后端能处理transpose”放宽任意广播归约。

融合日志组合NPU/Triton结果和原因，显示original_aten只用于诊断标签；记录编译阶段时长不等于Kernel加速。group_fn仍委托Triton；后端声明REDUCE_TO_SINGLE_ELEMENT与INPLACE_BUFFERS两项特征，不能从特征声明推导每种原地别名组合已经正确。

## 分区和发布差异

scheduler_should_partition_override识别CPU0D读（CPU设备、非None/MultiOutput layout且size=[]）直接返回True；其他只在npu_as_gpu_context作用域内调用原生orig_fn并原样返回，保留原Torch其余规则。外部context恢复/并发语义没有因被调用而完成覆盖。

固定发布npu.py的can_fuse_vertical与horizontal都直接False，codegen_template直接NotImplemented；group_fn与两项特征声明仍存在。这是本模块两个固定实现的差异，不推导整个发布框架或其他后端没有融合。实际模板分流/无epilogue原生回退、代码cache与Wrapper见[生成合同](torchair_inductor_ascendc_schedule_codegen_wrapper.md)。

## 固定实现证据

- [固定源码 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（primary）：73–94, 2579–2584, 2895–4871。
- [固定源码 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（implementation）：561–582。
