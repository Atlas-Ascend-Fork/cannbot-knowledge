---
type: Guide
title: 实验Triton线性化header：分块、odometer与mask边界
description: 核对贪心分块与unify开关、对齐、超大numel别名、odometer及实际mask转换和映射顺序。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/npu_header.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T09:51:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton线性化header：分块、odometer与mask边界

## 固定范围与真实调用

依据TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的完整_codegen_header_npu_for_tree局部方法及所列本地helper、codegen_range_tree调用者和配置声明；仅有界读取，不提升整个npu_header或triton大模块资格。发布固定快照的三个精确实验路径无Git条目，只说明来源关系。未导入或执行SymPy/Triton、IR、生成器、编译、设备及测试；产品和完整索引正确性未知。

codegen_range_tree在_npu_linearize为假时委托父类；线性化时仅对非loop、非reduction的tree调用自定义header，其他非loop reduction仍走iteration_ranges_codegen_header。它按self.range_trees的实际遍历顺序积累已处理free轴的_blocks名称，作为下一棵tree的outer_blocks；注释说按grid_dim排序，但这个方法内部没有额外sort。

header本体仅在tree.prefix精确等于'r'时提前委托默认header。其余路线保存或创建tree.pre_loop_code并向其中追加不变量，最后将新header放到原code之前；没有统一清空旧pre_loop或失败回滚，不能把重复调用视为自动重新生成全新无副作用对象。

## 轴优先序与贪心预算

free轴由tree.nodes中不在tree_node_mapping的项构成。reduce_xblock_by_input_stride默认True：inside_reduction且至少两个free轴时，从已有load文本提取地址；每轴在多次load出现时取最小stride rank，只有所有free轴都取得rank才采用该顺序。rank按符号次数与系数绝对值排序，另一个迭代轴出现在系数中则不接受；不能由“某次load最连续”推导所有load布局均连续或已获相同带宽。

地址提取沿用[clone与load rescue指南](torch_npu_experimental_triton_clone_fold_and_load_rescue.md)中的已有parser，不在本卡重复审数学规则。sympify/coeff的局部失败会跳过该项，并不是helper任意异常都整段回空字典。没有输入优先序时，现有pointwise_tile_contract可能提出顺序；其完整合同仍见同一指南。本体的xblock_priority_denom初始化为空且没有再填入，不能将保留的旧分支注释当作当前会建立运行时分母链的证据。

预算用truthy balanced_target固定值，否则用当前prefix的BLOCK constexpr；默认balanced_target=0。实际生成按输入rank（如已建立）或输出divisor hint排序的贪心链：第一轴取预算，后续剩余为max(前剩余//前tile,1)；有已知长度时tile取长度与剩余中的较小者，未知长度或batch_invariant时直接取剩余。没有在这个分支实现注释所说的按尺寸比例均匀分配。

每个tile是生成的constexpr表达式，combo成员另把_combo_num加入共享预算变量名前缀，避免相同tree.prefix直接共用这些局部名字。hint与排序是当前编译状态的选择，不是对完整动态尺寸范围重新证明最优分块或真实UB容量。

## unify开关不是整条flat路线的总开关

_is_unify_candidate会先读默认True的unify_block，并检查动态长度、divisor及长度hint等条件；scalar odometer轴还被排除。但是稍后贪心分配把所有自己的轴名并入_unify_names，**没有再次受unify_block控制**，静态轴也可经这一步进入。不能仅将配置改False便宣称所有统一分块都关闭。

scalar odometer轴固定real_block=1，不分配寄存器arange。其余free轴应走贪心/unify；没有落入两类的项在发射real_block时直接RuntimeError。arange选择及最终检查均保留flat路线，node_needs_inner_loop不请求寄存器内层循环；最终若有free轴请求内层循环则报错，而不是自动恢复旧T-loop生成器。

_clamp_to_length虽然作为局部函数定义，却没有在本方法后续被调用；不能只依据它的注释给所有tile额外补上一个运行长度clamp。长度约束应看实际贪心表达式、hint、后续对齐及mask。

## 对齐的单位与剩余pad分支

tile_align默认8，实际是**元素数**，只有FP32时8元素才对应32字节。对齐候选取原free轴顺序中首个静态divisor==1的合格轴，静态长度小于对齐量则跳过，动态长度不会因这个静态检查被排除。

inside_reduction且成功取得非OUTER/OUTER_TINY的ReductionHint时跳过这项对齐；features缺失或hint获取异常不会自动等同跳过。命中轴的arange宽度向上取整到对齐倍数，再把该constexpr作为real_block，所有权span与arange使用同名值。

对齐发生在预算链生成之后，本地没有因此重算所有后继剩余预算或实际UB分配；注释的“budget safe”不是本轮对任意tile、dtype、hint或配置范围的独立证明。pad_min_block_to_8默认True的旧分支另外跳过全部贪心轴和scalar轴；按当前正常构造，这些正是free轴的两类，不能照名字断言每个小轴都会被强行补到8。该分支保留的数字文本启发式也不是运行中实际测量tile。

## numel别名与2^31边界

_is_batch_invariant按调用时上游配置取Bool，异常返回False。_npu_emit_axis_numel对动态node.length直接返回，不在这里重新发射其定义；静态长度小于2^31且非batch_invariant时写constexpr，否则从tree.prefix的运行numel作别名，必要时除以其他free轴长度乘积。

_sibling_product排除映射轴及同名轴，sympify后要求**乘积**是至少1的整数，否则RuntimeError；这不是逐一检查每个其他轴都是静态正整数，也没有读取真实运行尺寸。别名正确性仍依赖tree.numel与free轴乘积的构造合同，运行参数是否已为正确i64由其他调用链负责，不能把注释中的保证当作本轮验证。

_blocks只有length/divisor都静态、length<2^31且非batch_invariant时写constexpr；其他情况写运行表达式ceil(numel/real_block)。这避免本地直接把超大轴长度烘焙进此constexpr，但不独自认证最终地址、总block乘积及所有设备比较都无溢出。

## odometer与每轴索引

odometer_opt默认True时，outer_blocks和先前非singleton轴的block数形成累计乘积，offset按pid//累计积%本轴blocks*real_block计算。静态长度精确为1的轴直接offset=0且不加入这条累计链；关闭时则依次连写除法，再取模乘real_block。单free轴还生成prefixoffset别名；caller跨tree积累仍按其自己的实际顺序。

scalar轴直接index=offset并以offset<numel为mask；没有tl.arange或独立tensor-dim槽。普通轴根据tree.is_loop、grid_dim及tensor_dim选择base/arange/标量表达式，再生成mask。局部loop或grid_dim=None分支与普通grid分支写出的别名并不完全相同，不能在未核外部定义时断言所有分支都独立生成相同的nameindex；当前所读正常caller已先排除loop树。

node_block_constexpr保存实际arange引用给后续使用；最终free mask是各free轴mask的与。这里的代码生成不执行物理迭代或验证输出存储边界，真实pad lanes、广播、slot和地址表达式仍需联动检查。

## mask比较以实际分支为准

模块赋值时将mask_cmp_fp32保存为npu_mask_cmp_fp32，默认False；以后仅改变config不代表这个已保存变量自动同步。_mask_cmp_lhs的实际顺序是：

1. index_dtype为tl.int64且numel为静态int/SymPy Integer、numel<2^31时，立即把左侧转tl.int32；
2. 其余情况，若保存的FP32开关为False，保留原表达式；
3. 否则把左侧转tl.float32。

所以动态轴或静态轴>=2^31在FP32开关打开时会走第3步；不能照docstring说它们无条件继续保持i64。第1步的提前返回确实不再落入FP32路线，但本地没有对剩余轴自动强制注释所建议的小尺寸范围。超过FP32精确整数范围时不能由开关名或注释推导比较无损；本轮没有复现注释中的timeout或任何硬件数值结果。

## 映射顺序不是循环依赖证明

_ordered_mapping_items尝试先发射不依赖remaining中其他名字的项，并忽略自依赖；一轮没有进展时直接按剩余字典顺序发射并返回，**没有报循环依赖错误**。这是一份有fallback的排序策略，不保证任意输入mapping都无环或所有引用均先定义。

_render_mapping_expr对_FlatMapExpr使用预渲染文本和全部free_symbols；普通表达式先rename_indexing/texpr，只有属于tree节点名的原free_symbols参与mask。映射结果仅在这些迭代名非空时额外生成mask；它不是对任意映射、除数、循环引用或新边界条件做独立合法性证明。

定位tile膨胀、尾块、溢出或动态shape问题时，保存实际tree顺序、scalar集合、priority/hints、constexpr预算与对齐、运行numel别名、offset/mask及最终映射代码，再验证代表性尺寸与数值。本次只补本地生成合同，不新增verified。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/npu_header.py)：1–198,281–318,560–1171行；完整局部方法/helper或所列调用/声明，不提升整个模块资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)：4101–4133行；完整局部方法/helper或所列调用/声明，不提升整个模块资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：120–120,123–123,126–126,129–129,353–353,376–376,379–379行；完整局部方法/helper或所列调用/声明，不提升整个模块资格。
