---
type: Guide
title: 实验Triton循环合并与addmm融合安装边界
description: 解释Max结构折叠的循环合并比较副本、返回索引合同与addmm pattern禁用的真实作用范围。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/fx_passes.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/overrides.py
  role: implementation
created_at: '2026-11-11T09:35:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton循环合并与addmm融合安装边界

## 固定实现与配置含义

本文限定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的两个完整局部安装器、Max折叠helper、相关imports、默认配置和overrides调用段。发布固定快照的这些精确实验路径无Git条目，只说明来源关系，不推导发布没有其他同类实现。没有导入SymPy/上游Torch、执行patch、改图、编译或测设备；产品与运行正确性未知。

fold_max1_in_loop_merge=True允许安装循环合并替换；disable_addmm_fusion=True则允许修改pattern以**关闭**那类融合，两个True的作用方向不同。apply_npu_overrides先执行addmm限制，再safe_stride_order、循环合并安装、整数往返/source pin安装，最后codegen patches；之前的任一步异常都可能阻止后续调用，这里没有总事务或恢复协议。

## Max折叠是结构性替换

_npu_fold_max1先要求sympy.Basic；内部只按类名等于Max、is_Function为真、两个args且其中一个等于1来匹配，移除1后返回剩余参数。它不是只匹配某一个导入类的精确身份，也没有为被移除Max中的表达式建立非负性证明。replace内部异常返回原expr；这层catch不覆盖安装器和循环合并函数的所有后续操作。

注释用非空Tensor、每维至少1解释Max(1,e)可折叠的动机；本地helper没有检查实际Tensor、所有尺寸正性或新建运行guard。不能从默认开关或符号替换通过推导零尺寸、未知符号范围及任意同名函数都已证明等价。

## 比较用副本与返回值分开

替换函数先self.simplify每个size；每个sympy.Expr公式用stride_vars求stride，非Expr公式以全零stride表示。它显式核对sizes长度和**第一行**stride长度，不是逐行全面校验；index_formulas为空时访问strides[0]本身就可能异常。没有总except把异常转换成原实现回退。

size等于1的轴先标None。fsizes、fstrides、fformulas再用Max折叠形成比较副本。每个待合并(a,b)必须在所有公式上同时满足：

- simplify(fstride[a]*fsize[a])等于simplify(fstride[b])；
- 公式代入`a=m1*fsize[a], b=m2`与代入`a=0, b=m1+m2`后的simplify结果相等。

这是实际的局部符号比较，不是本轮执行了求解或验证所有输入。遍历按倒序尝试所有不同轴对，不只相邻轴；命中后将原sizes[a]乘sizes[b]、把b标None，更新fsizes[a/b]，重复直到无合并。原始stride及公式列表并没有每次重算，不能自行补成另一个合并算法。

返回的尺寸来自self.simplify后的原sizes及其乘积；折叠副本用于判断，不直接作为返回尺寸。reindex按仍存活轴从输入迭代器取值，被删轴填sympy.S.Zero；发现多余输入显式报RuntimeError，缺少输入则next自身也可报错。prune先要求原轴数长度相等，再筛出存活项。这里没有另外实现任意合并轴索引的div/mod逆映射；三个返回项如何由上游使用仍服从外部接口合同。

因此“比较副本不直接返回”不能升级为任意空维、动态范围、索引公式或reduction全都已获独立正确性证明。应核对原sizes、公式、最终合并决定、reindex/prune调用及实际生成索引。

## 安装替换作用于进程类对象

开关关闭时安装器直接返回；打开后导入SizeVarAllocator和sympy_subs，sympy_index_symbol第一次导入失败会尝试另一模块。随后检查类属性_npu_fold_max1_installed：已有真值便返回，否则直接将_simplify_loops_impl替换成这份函数，再置标志。

这里没有保存原函数、包一层仅特定图才调用的wrapper或提供卸载。之后把配置设False不会自动恢复原方法；标志也不认证当前方法仍是这份实现。它是当前进程的类方法修改，不是仅给当前一个kernel增加候选。外部import、标志设置和先前patch之间没有统一失败回滚。

## addmm规则只修改一组已登记pattern

_disable_addmm_fusion_pass在开关为真时导入post_grad，遍历pass_patterns[2].patterns中各entry；handler的__name__精确等于addmm就将entry.extra_check替换为总返回False的lambda，并记录数量。它按名字筛选，并未核handler所在模块、函数对象身份或匹配图的完整内容。

这不是禁止所有addmm调用、删除矩阵乘算子、关闭所有FX融合或关闭shape-padding pass。注释解释为什么仅改模块同名函数不足以影响既有entry；本卡只确认本地实际修改对象，未执行外部pattern_matcher来证明完整调度效果。

没有匹配项时数量可为0，函数仍正常结束；关闭开关后没有恢复旧extra_check。该安装器也没有一次性标志或总except，重复调用会再次扫描；缺少预期第三个pass或其他外部结构变化并不保证自动跳过。日志数量只表示修改条目数，不等于真实模型发生融合、性能改善或数值已验证。

使用这组规则时，记录有效开关、安装前后类方法/pattern对象、真实尺寸与公式、命中规则和最终图，再做模型结果及性能比较。本次摄取不增加verified。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/fx_passes.py)：15–25,490–646行；完整局部方法和所列imports/调用/默认声明，非整模块资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：139–139,156–156行；完整局部方法和所列imports/调用/默认声明，非整模块资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/overrides.py)：25–29,87–104行；完整局部方法和所列imports/调用/默认声明，非整模块资格。
