---
type: Guide
title: 索引累加执行：初值复制、连续克隆与out差异
description: 核对index_add与scatter_add在OpAPI中的初值准备、原地与out边界及版本检查差异，避免遗漏复制和连续化开销。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexAddKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexAddKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterAddKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterAddKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T14:59:11Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 索引累加执行：初值复制、连续克隆与out差异

## 固定准确入口

本卡核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`中index_add、index_add_out及scatter_add、scatter_add_的OpAPI包装。重点是保留self初值的准备与写回，不把所有索引/归约、index_add_或其他out重载纳入已核对范围。平台及安装配套未知，保持draft、空平台，未执行上游或设备实验。

[公开索引/归约约束](torch_npu_native_tensor_index_reduce_scope.md)已有方法级类型与重复索引提示；[GE索引与Scatter](../../inference/guides/optimization/torchair/torchair_ge_index_scatter_lowering.md)已有TensorMove、Cast和广播构图。本卡补Eager准备，不用其中某一路的转换规则认证另一路。

## index_add先保留self初值

无out入口先申请与self shape/options对应的无格式result，然后以`EXEC_NPU_CMD(aclnnIndexAdd,result.copy_(self),dim,index,source,alpha,result.copy_(self))`调用。这里两个宏实参都包含copy_表达式，不能把代码概括为“只申请空输出，直接累加”。

本卡只确认这些有副作用表达式的位置，没有展开执行宏各分支及所有辅助模板，不能据两个文本位置直接报固定两次Device复制、固定字节量或测得额外耗时。宏分支和参数求值应作为性能定位入口，不能为了消除复制就删掉累加所需的初值。空index或alpha=0在所读包装中没有独立免准备分支，不由更新量为零就推导本层无申请/复制请求。

index_add_out先调用check_tensor，传入期望shape为self.sizes、dtype参数为result.scalar_type；随后仅在`!result.is_same(self)`时调用result.copy_(self)，再把result同时放入ACLNN输入和输出位置，返回该result引用。不能将is_same判定擅自换成shape相同，也不能仅凭out名声称没有初值搬运、任意别名或任意dtype组合都安全。

## 主线新增形状检查，不能回填到发布

主线两个普通整数dim入口在准备输出前比较self/source的sizes：双方非零维时，以self.dim经maybe_wrap_dim处理dim，分别删去该轴，再要求剩余sizes完全相同；否则比较未删轴的sizes。用于检查的wrapped_dim并未替换传给ACLNN的原dim。

发布对应函数没有这段检查，不能以主线报错分支保证发布同样拒绝输入。该局部检查也不是任意rank、index长度/范围、dtype、设备及重复索引规则的完整验证。两版所读调用都没有仿照GE转换显式把index转INT32或把alpha转self.dtype；未见本地Cast不等于底层保持索引位宽或支持任意混合输入。

## scatter_add的函数式和原地准备不同

两版scatter_add无out都显式请求`self.clone(at::MemoryFormat::Contiguous)`，对克隆、index与src调用CheckMemory后，将克隆同时作为aclnnScatterAdd输入/输出并返回。申请和保留self值的复制请求与连续布局准备不可从本体算子开销中省略；实际空Tensor、分配峰值、格式转换及物理复制代价没有实测依据。

scatter_add_则对self、index、src调用CheckMemory，直接将self作为输入/输出并返回同一引用，所读函数没有再clone或先统一contiguous。不能为了提速把函数式路径机械改成原地：它改变输入写回与后续消费者条件，也不能用缺少本地连续化推定任何stride都受支持。CheckMemory的调用存在不认证所有shape/dtype/别名已合法。

主线index_add及scatter_add的Dimname重载置于`!VERSION_BETWEEN(V2R13,VERSION_NEWEST)`条件，发布所读C++无此保护；它们把Dimname转位置后进入整数dim入口。该源码条件不等于任意安装包注册结果或整个未来版本支持承诺。

## 路由与模型优化验收

上述入口先用相应DO_COMPATIBILITY检查执行和GetWorkspaceSize符号；缺任一且ACLNN-only时报错，否则返回给定ACL表达式。此卡没有展开ACL回退主体，不把回退前后的分配/转换当成相同，也不将符号存在认证为目标设备、重复索引精度或确定性支持。

记录准确函数式/原地/out入口、self/source/index大小、dim、alpha、stride及实际后端；分别核初值复制、连续clone、输出引用与索引累加本体。先验证数值、别名和梯度，再比较调用及内存成本；本卡没有运行宏展开、模型、NPU、数值或性能实验，不提供固定复制次数、性能数字或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexAddKernelNpuOpApi.cpp)（primary）：20–90。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexAddKernelNpuOpApi.cpp)（implementation）：20–63。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterAddKernelNpuOpApi.cpp)（implementation）：20–45。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterAddKernelNpuOpApi.cpp)（implementation）：20–59。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110。
