---
type: Guide
title: 独立npugraph_ex的DLRM特定图改写与语义前提
description: 完整记录DLRM模型特定的embedding、三角矩阵和预测层改写，明确未发现所查包的直接调用及参数保留边界。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/_pattern_pass_dlrm.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/_pattern_pass_dlrm.py
  role: implementation
created_at: '2026-11-11T06:02:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex的DLRM特定图改写与语义前提

本卡完整静态审阅TorchAir固定主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的npugraph_ex/npugraph_ex/patterns/_pattern_pass_dlrm.py。两版控制结构逐项对照，含所有注释和日志差异；产品未知，draft/空平台，没有执行改写或数值实验。

在按函数字面名搜索两版npugraph_ex与python/torchair根时，只找到相应定义，没有找到这些范围内的额外直接调用；不据此排除动态调用、外部用户或别的源码树。文件存在不证明默认编译链已启用，也不作为直接启用的优化配方。

## 三段入口及公共替换辅助

_optimize_dlrm_pattern依次调用embedding、triangular、predict三段，再gm.recompile并返回原gm；example_inputs/config未在此控制匹配，没有入口graph.lint或整体数值校验。后两段各次只处理找到的一个匹配，不是自动迭代到固定点。

_replace_arg递归list/tuple并保容器类型，没有遍历dict。predict虽然尝试把user.kwargs交给它，也不能因此声称所有关键字引用已替换。_safe_remove_nodes按逆拓扑只删候选中无user的节点，删除异常仅debug记录，有user就保留；不是完整DCE，也没有失败后的事务回滚。

## embedding、slice与sum的全图收集

第一段从整个图收集dim1 slice、embedding、sum(dim=[1])，保留最后一个dim1 cat且其输入都在已收集sum中；要求每类至少2个。它没有进一步把全部收集节点证明为一个连通子图、一一对应同一权重、连续等宽slice、起点0或相同dtype/参数。

slice按start排序，以前两个start差作为group_size，从第一个slice追溯基础输入并取第一个embedding的weight；split_sizes先全为group_size，仅末slice end为最大整数且有Meta时调整尾部大小。再对split输出逐个embedding、在dim2合并、一次sum(dim1)，重定向所选cat用户的位置args。

新embedding只传weight/indices，没有统一转交原padding、sparse等额外参数；sum也没有统一传递原keepdim/dtype选项。全图收集和这些省略是实际源码边界，不能把该形状特定重排写成任意embedding/sum链等价优化。无用旧节点只按上述安全删除helper尝试清理。

## triangular改写固定生成tril(-1)

它找where.self，condition为triu(ones_like(X))转bool，true为zeros_like(X)、false为相同X；识别NPU cast与aten._to_copy两种形式。匹配后直接生成tril(X,-1)，没有在该分支独立检查或转交原triu diagonal及所有其他选项。字典dtype直接索引等操作也没有统一异常恢复。

只重定向user.args并尝试删除无用候选，不能从注释“ones_like+triu+where”推出任意diagonal或全部关键字参数均被保留；本次没有测量这种静态缺口是否会在实际模型命中。

## predict层的切片与线性分解

目标按_name识别addmm或linear，两者都要求至少3个位置实参；两实参linear即使接口允许省bias也会在本地跳过。输入必须是含两路Tensor的cat并至少有两个args，但没有在这里检查cat dim等于1。addmm还要求第三输入来自aten.t，取其原weight。

embedding_size从第一路dense Meta的shape[1]取得；备用分支仍依赖这些字段，不构成独立的一般推形能力。weight沿dim1切成前后两块；addmm分支分别t后mm，linear分支直接matmul各切片，再相加并按非None bias另加。没有在这里统一检查/转交addmm alpha、beta或所有原kwargs，也不能将linear权重布局按名字视为已经证明。

这些步骤只描述所存实现的局部图变换及其假设，不认证所有Cat/Linear/Addmm语义、数值、梯度、别名或性能。需要实际接入证据、改写前后图和准确参数域后才能评估；本卡无新增verified。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/_pattern_pass_dlrm.py)（primary）：1–433。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/_pattern_pass_dlrm.py)（implementation）：1–413。
