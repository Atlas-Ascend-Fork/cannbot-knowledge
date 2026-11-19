---
type: Guide
title: Inductor AscendC轴映射：规范轴、细化与访存顺序
description: 完整核对主线规范轴生成、静态拆分、广播映射与Store顺序证明，对照发布逐节点转置评分的不同实现。
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


# Inductor AscendC轴映射：规范轴、细化与访存顺序

范围为TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的完整npu.py本地定义，本文聚焦索引证明。两版分别读取，没有运行上游或声称配套/产品支持；保持draft/空平台。模板构造边界见[本地IR](torchair_inductor_ascendc_local_ir.md)，是否实际融合由[调度决策](torchair_inductor_ascendc_fusion_decisions.md)继续约束。

## 规范逻辑轴不等于遍历顺序

主线_AlignedNodeAxes保存节点的axis_indexings、size、var_to_expr和concat-prologue标志。规范轴优先取Cat/MatMul/BatchMatMul的输出形状；普通组从LoopBody.var_ranges与归约输出消费关系收集有序尺寸，再求共同细化。空轴使用a0=1。逻辑轴用于表达索引，后续schedule_axes可以换序，不能将换序解释成tensor逻辑维度已经置换。

相同符号尺寸组可直接沿用；只有一组原样返回；动态组尝试从轴数最多的候选开始，要求所有其他组能对齐。否则按静态元素数取最大规模组的累积边界，同一边界的重复次数保留最大值，排序后逐项整除求细轴，并重新要求全部完整组可连续映射。_static_int_or_none接受bool、int、sympy整数及无自由符号且is_integer的表达式；正数限制仅由调用_require_static_positive_integer的路径施加。不能把一个size hint当静态正整数证明。

常用比较有两种：_expr_equal用图sizevars.simplify差值后检查整数0或is_zero=True，_same_size直接用sympy.simplify差值==0。flatten按行主序多项式拼轴。一般广播映射搜索有序非空轴子集，可以跳过规范轴；严格contiguous映射要求连续分组并消耗全部目标轴。满秩普通对齐允许节点维为1或与规范维相等；validate=True的满秩检查更严格，逐位置必须相等。

## 两类细化及失败边界

affinity细化只对LOAD/STORE/STORE_REDUCTION索引含FloorDiv/ModularIndexing的组试验，模板跳过；以plan_local_stores=False对齐，再替换索引、按轴值域化简并检查仿射性。请求仅取base恰为规范轴、静态k>1的拆分，冲突用LCM，轴长必须静态且可整除；最多两轮拆分，再做一次验证。失败、动态、不可整除或未收敛返回原轴。代码注释举ModularIndexing(v,1,k)，实际请求提取只读其args[2]，没有在该helper另检查args[1]==1；不能把示例写成独立验证条件，最终仍依赖完整仿射复查。

节点轴细化只处理含“Cannot map node axes”的映射失败，尝试把合并的pointwise轴改为节点中更细的连续轴，归约部分不这样扩展，并按最长连续组优先。其注释称最终会重新检查，但函数修改后直接返回，没有自己的最终完整align复查；后续validate_axis_mapping仍会重建、对齐并做Store顺序可行性验证。两个层次不能合并成该helper独立保证。

## Cat前驱与本地Store偏好

Cat逻辑输入形状来自input_layouts；前驱节点按输出名匹配对应输入。非直接前驱且元素数不同的pointwise节点，优先选同秩同numel的某个Cat输入形状，否则保持规范形状。Cat prologue要求group为二元结构、rnumel=1、无归约、元素数一致、输入秩及连续分组可证明；特殊索引构造会再次核对，而不是仅凭“elementwise”放行。

Cat相关的numel/细化校验通过_merged_pointwise_sizes_for_node取得普通节点merge_loops后的pointwise尺寸，模板在该helper取自身ranges；普通_align_node_to_canonical仍按body.var_ranges原顺序对齐，并非先把所有节点merge_loops。节点按生产顺序对齐，本地Store Loops为后来读取提供轴分组偏好；偏好Loop按轴字符串身份重映射。搜索评分优先跳过零stride轴，减少把零stride轴用于实体访问及跳过非零stride轴，偏向后部对齐，再减少flatten。计划Store时将索引代入规范表达式；affinity试验关闭这一步，以免在化简前把非线性Store当标准stride解释。

## 访存评分与真正拒绝条件

_adjust_canonical_axes_by_access在逻辑对齐之后收集外部输入Load和最终输出Store；内部产生的Load以及非最终输出写入不参与同样的外部访存评分。模板通常保持逻辑顺序，Store验证路径仍会约束连续性。_adjust_canonical_axes枚举排列，只保留满足归一化Store后缀连续stride的候选；可行性模式找到一个即返回，普通模式最小化(access逆序罚分+100×Store转置罚分, Store转置罚分)，平分保留先遇到者，0分提前结束。这是代码启发式，不能推导实际带宽或最优性能。

validate_axis_mapping重建规范轴、验证各节点并要求存在Store可行顺序，异常由调度器缓存为拒绝原因。只因numel相同、可表示为某个reshape或单个读索引连续，都不足以绕过该整链。

发布实现不同：逐节点new_subgraph，空轴用z0=1；_get_minimal_transpose_order枚举该节点LoopBody轴排列，用stride_hints判断非零stride是否降序，逆序且最后hint为1罚1，否则罚100，首个0分提前结束。它没有主线规范轴统一、共同细化和Store可行性这套本地定义。发布这里的差异不代表其他路径或版本没有相关优化；两版不能混用同一轴证明结论。

View设计与实际npu.py消费者的范围分别见[Cat/View设计](torchair_inductor_ascendc_cat_view_fusion.md)、[生成与转置](torchair_inductor_ascendc_schedule_codegen_wrapper.md)。本卡不把外部简化器、Loop类或Lowering实现因被调用而登记完整。

## 固定实现证据

- [固定源码 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（primary）：151–157, 365–369, 391–1342。
- [固定源码 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（implementation）：130–175, 550–558。
