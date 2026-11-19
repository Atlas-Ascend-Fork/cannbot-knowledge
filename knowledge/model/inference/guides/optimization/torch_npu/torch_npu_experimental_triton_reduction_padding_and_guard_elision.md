---
type: Guide
title: 实验 Triton 归约 padding：中性填充、SSA 事实与 where 删除
description: 保存逐 load 填充值选择、pad fact 的本地前提、mask 覆盖与累加器 guard 删除，以及 legacy 候选追加和未闭合数值边界。
tags:
- task.optimization
- topic.compilation
- topic.compute.reduction
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: implementation
created_at: '2026-11-11T08:49:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验 Triton 归约 padding：填充值与 where 删除

## 固定局部机制

依据 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的实验 codegen 中 pad-lane 抽象值、FX cone 小 solver 以及实际 load/reduction/filter 消费者，另核默认开关和 legacy 候选的相关段。整个 8617 行 codegen 与 3293 行 heuristics 不在本卡范围，不提升这两个文件的整文件资格；发布固定快照在这些精确实验路径缺失，只表示局部来源关系。

没有导入模块、运行 FX solver/解释器、生成代码、执行数学参考、调优或设备测试；本卡不把注释中的 sound、never raises、byte-identical 当作本次运行结论。它与[permute 加载重写](torch_npu_experimental_triton_permute_gather_rewrite.md)都挂在 load 附近，但前者推导 padding 值/移除累加器 mask，后者改变加载几何，不应混为一种证明。

## 三种事实与传播规则

内部事实只有常量 `("c", float_value)`、`fin` 和 `top`。CSE 变量初始 top；新 CSE 变量使用本地 NPUTritonCSEVariable 类，update_on_args 先调用上游，再从本地 CSE 的事实、非 bool 的 Python 数字提取参数事实。普通外部 CSE 是 top，dtype、字符串、符号等其他参数忽略；不是扫描最终代码字符串来猜中性值。

常量二元操作可直接计算常量；加减的无穷常量与 fin 有专门传播，乘法对 0×fin 和 1×任意事实有专门分支。exp 对常量计算，OverflowError 记正无穷；非具体常量的 fin 输入返回 top，未承诺 exp(finite) 仍有限。where 不求条件，只 join 两个分支：相等常量保留，均有限则 fin，否则 top。

to_dtype、to_dtype_bitcast、identity、broadcast、constant_to_device 都直接转发第一个参数事实；neg/abs 处理常量或有限标签。未列出的操作只要收集到的参数事实非空且全有限，就默认给 fin，否则 top。`_pad_transform` 调用的 Exception 在 CSE 更新中回退 top；之前的 `super().update_on_args` 和参数事实收集（包括 `float(a)`）在该 try 外，未统一捕获。

这些是**本地抽象规则**，没有在每次标 fin 时检查真实 Tensor 的 NaN、Inf、dtype 溢出、bitcast 后数值或所有未列出算子的定义域；尤其不能把 to_dtype_bitcast 的事实转发称作已证明数值恒等。后续删除条件依赖这些事实的适用性，top 保留 guard 并不意味着所有 fin 的产生都已经经过完整运行数值证明。

## load 种子与覆盖检查

只在非 persistent reduction 中、结果是本地 CSE 类且 index 是 SymPy 表达式时记录 load 的 pad fact。若地址不使用任何 reduction range-tree symbol，直接标 fin；这里没有读取数据检查有限性。若使用 reduction symbol，则检查结果 mask_vars 是否包含这些 root prefix 的全部 `<prefix>mask`；全部覆盖且 `_load_other` 可转成 float 时标该常量，否则 top。other 为 None 按默认 0.0 处理，转换异常也使常量不可用。

覆盖条件按地址真正触及的 reduction roots 建立，并非只要有一个 mask 就可确认 padding；但它不在此证明上游索引、所有语义 mask 和外部加载地址都正确。代码注释提到的其他 load neutralizer 也没有在本组继续展开。

## FX forward cone 如何选择填充值

选择只在默认开关 elide_reduction_where=True、inside_reduction、非 persistent 且 `_load_other is None` 时尝试，已有 semantic fill 不覆盖。当前解释器节点还须 target 为 load，且解析出的地址确实触及 LoopBody.reduce_vars；不能解析时放弃更换。

solver 沿 load 的 users 图继续遍历，按对象 id 去重，收集所有 target 字符串为 reduction 的节点。无 reduction、参数数量不足 5、reduction type 不在下表中都返回 None。候选按 0.0、负无穷、正无穷、1.0 的顺序测试；必须让每个所收集 reduction 的 value fact 都精确等于其 identity 常量，才返回该 fill。默认 0.0 已满足就不作实际更换。

| 类型 | solver 的 identity |
|---|---|
| sum、xor_sum、any | 0.0 |
| prod | 1.0 |
| max | 负无穷 |
| min | 正无穷 |

cone 求值用当前 load 的候选常量；其他 reduction-axis load 按默认 0.0、地址无法解析按 top、reduction-invariant load 按 fin。非 bool 数字常量保持常量；get_index/index_expr/load_seed/randn/rand 标 fin，普通操作只收集 args[1:] 中的节点或数字事实，再用同一个传播规则，kwargs 没有通用递归求值。

因此它是**逐 load、按其他 load 默认填 0 的局部分析**，没有在 solver 内联合优化全部 load 的填充值，也不读取已有其他 load 的运行结果。本地 solver 只按 reduction type 选 identity，没有在这层检查 dtype；最终 guard 删除另有 floating-point src_dtype 门槛。

docstring 还列出“逃逸到 store 就放弃”，实际收集/候选检查里没有独立的 store-escape 拒绝遍历：它收集 reductions 并求各 value fact，不能仅凭该文字声称已经验证任意额外 store 使用或全图别名/副作用隔离。solver 运行异常由 `_pick_reduction_load_fill` 的 try 捕获并保留默认；但之前的当前节点/地址解析检查在这个 try 外，不能把 never raises 扩成整个 helper 的异常保证。

## 临时替换 other，按事实删除 guard

选择非零 fill 后，load 暂存原 `_load_other`，写入新值并调用上游 load；在新值仍生效时给结果记录 pad fact，再在 finally 恢复加载状态。它不永久修改整个 kernel 的默认填充值。任何后续 permute 记录失败也仍受这一 finally 的恢复约束。

reduction 删除条件要求开关开启、inside_reduction、非 persistent、value 是本地 CSE，且其 pad fact 与 `_reduction_identity_pad` 精确相等。该 identity helper 只处理 floating-point src_dtype 和表中的六种 type；未知事实、整数源和其他类型走普通上游 reduction。不是“只要改了 other 就一定删 where”。

命中时只在调用上游 reduction 期间置 `_npu_elide_reduction_masks=True`，finally 清 False。filter_masks 先委托上游；该 flag 生效时移除每个 range tree 的 `<prefix>mask`，包括非 reduction tree 的 prefix。实际 semantic mask 的完整上游附加顺序未在本组展开，不能把本地 prefix 删除提升成对全部 mask 的通用合同。

返回结果还会再设 pad fact：floating-point 的 sum/xor_sum/prod/max/min 且结果本身是本地 CSE 时标 fin；any 不在这个结果播种列表，tuple 也不会逐元素播种。此处同样没有实际检测归约结果是否因输入 Inf/NaN 或溢出而非有限；它是下一轮传播使用的分类前提。

## legacy 候选与真实资源边界

所读 heuristics legacy 段在开关开启、rnumel 是 int 且 0<rnumel<=4096 时，把 rnumel 本身加入 r_list，并可追加按 `max(1,32//最小指针元素宽度)` 向上对齐且<=4096 的值。它用集合并集**追加**候选，保留先前较小 tile，不把 r_list 替换成仅一个大 tile。最小元素宽度的表与缺省规则见[归约候选指南](torch_npu_experimental_triton_reduction_formula_and_entry_gates.md)。

这只是相应 legacy 分支被到达后的候选补充；默认公式/permute marker/诊断 pin 等早退可能先返回，不能说每次归约都加入这些候选。也没有因 rnumel<=4096 就证明整个融合 kernel 必定适配 UB；原有小 tile 留存只是提供更多候选，资源失败的实际处理按[候选编译回退](torch_npu_experimental_triton_compile_tiers_and_resource_fallback.md)的局部合同核对。

排查时应同时保存原 semantic fill、load 地址/mask、各 CSE pad fact、solver 看到的所有 reduction 与其他 load、选择的 fill、最终 guard、实际候选和数值边界。内部标记命中或 where 消失都不替代真实输入上的数值、NaN/Inf、尾块及性能验证；本次没有新增 verified。

## Evidence

- [固定源码 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（primary）：198–200、1453–1823、2225–2479；仅列出有界源码，外部上游 reduction/mask/设备正确性另计。
- [固定源码 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：179–181；仅列出有界源码，外部上游 reduction/mask/设备正确性另计。
- [固定源码 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（implementation）：1634–1634、2839–2865；仅列出有界源码，外部上游 reduction/mask/设备正确性另计。
