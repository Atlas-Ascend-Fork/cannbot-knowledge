---
type: Guide
title: 原生NLLLoss执行：权重轴、标量统计与out准备
description: 区分普通及2D NLLLoss的缺省权重、前反向分配和out检查，保留标签、dtype与底层数学未核对边界。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLossKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLossBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLossBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLoss2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLoss2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLoss2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLoss2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T14:37:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生NLLLoss执行：权重轴、标量统计与out准备

## 固定入口与已有知识

核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的普通/2D NLLLoss OpAPI前反向与out重载。四对C++去注释、空白并拼接续行后token相同，其中普通前反向两文件还逐字节相同；不扩展成整个kernel或runtime一致。平台配套未知，保持draft、空平台，没有运行上游、自动求导或设备实验。

[原生损失约束](torch_npu_native_loss_constraints.md)已有标签、ignore_index和文档类型边界；[GE损失转换](torchair_ge_loss_lowering.md)已有Cast/归约构图；[词表并行融合损失](torch_npu_vocab_parallel_loss_contract.md)是独立路线。本卡补Eager OpAPI的实际准备，不能把交叉熵、公开F.nll_loss或自动微分全部调用视为已经进入这里。

## 缺省weight不是零成本None透传

| 所查入口 | weight缺失时的局部构造 |
| --- | --- |
| 普通nll_loss_forward及其out、nll_loss_backward及其out | `at::ones(self.size(-1), self.options())`，长度取最后一轴。 |
| nll_loss2d_forward及其out、nll_loss2d_backward及其out | `at::ones(self.size(1), self.options())`，长度取轴1。 |

普通前向无out路径在nocheck helper构造ones；直接out路径先构造后再调用helper，helper见已定义对象便不重复创建。每次缺weight会到相应构造分支，这几段没有保存一个跨调用共用的ones缓存。也不能把None直接当成向ACLNN传未定义Tensor。

轴的区别应按准确入口保留。普通(N,C)和一维(C)常规输入不能据此扩为任意高rank；2D分割路径需要单独处理通道轴。ones沿用self.options，不在本层强制FP32，也没有在这几段将给定weight统一转换为self的dtype或设备。实际类型支持及累加精度仍需底层合同。

## 前向输出和total_weight分别申请

普通前向默认output_size为空，即标量；仅当reduction==None且self.dim()!=1时改为`{self.size(0)}`。total_weight始终按空shape另申请标量。两份都以self为参照调用apply_tensor_without_format，不能从统计名字推断total_weight自动是FP32或INT64。

2D无out前向经过shape helper，显式要求self.dim()>=4；reduction==None时申请`(self.size(0),self.size(2),self.size(3))`，其他值为标量，total_weight仍标量。helper只取这四个维度，不据>=4就认证任意更高rank均合法。target和ignore_index虽传入该helper，在所读形状分支没有参与推导。

包装没有完整校验reduction枚举、标签上下界或所有target/weight形状；其他归约值落到标量准备分支，不是合法性保证。两路将ignore_index独立传交ACLNN，仍不能把任意负标签当忽略值或用有限loss代替标签检查。

## out重载的准备层并不相同

普通前向out调用两次check_tensor：输出expected shape按上文推导，total_weight为空shape；调用的参照参数分别也是传入output和total_weight本身。它不是简单绕过准备直接执行，但也不能据此声称自动按self进行类型提升；完整helper行为还需其消费者证据。

2D前向out没有调用上述shape helper和check_tensor，而是check_memory输入/输出列表后调用ACLNN。因而直接调用该out入口，不能从无out路径的>=4检查或输出推导推断本入口也执行了同样校验；check_memory名字也不认证任意输出shape/dtype合法。

普通反向out在所读函数内没有check_tensor或check_memory，准备缺失weight后就调用aclnnNLLLossBackward并返回同一grad_input引用。2D反向out则先检查self.dim()>1、准备weight，调用check_memory，再交aclnnNLLLoss2dBackward。两种无out反向都先按self申请grad_input，再调用各自out路径；没有在此按输出mask跳过某份梯度的分支。

## 精度、索引与路由的局部边界

这些OpAPI函数将self、target、grad_output及total_weight原样交对应ACLNN，没有在这几段仿照GE转换统一将target转INT32或按Meta提升所有浮点输入。不能把“未显式Cast”解释成底层始终保持64位索引、任意混合dtype受支持或没有内部临时量；同样不能从结果按self申请认证全部反向数值精度。

每个所查公开C++入口先做相应aclnnNLLLoss/NLLLoss2d或Backward的DO_COMPATIBILITY：缺执行/WorkspaceSize符号且ACLNN-only时报错，否则返回所给ACL表达式。宏不在已存在符号后的任意参数错误自动回退，也不证明每个设备/kernel可执行。无out再调用out时可能再经过该层；不能据函数嵌套重复计算成两次ACLNN kernel调用。

Schema分别声明四组普通/2D前反向及output/grad_input重载的ACL/OpAPI候选和`[v2.1,newest]`范围，out返回别名写明a!/b!。这是固定声明，本卡没有生成或加载注册，不证明某安装包dispatcher、自动求导或F.cross_entropy的分解最终选择哪一条。

## 模型优化与验收

先区分普通分类和空间2D入口，保存输入/target rank、C轴、weight是否缺失、reduction、ignore_index、total_weight来源及准确后端。核对无out和out的分配/检查次序及输出引用，再比较缺省ones、标量统计和梯度准备的成本。不要为省分配随意换权重轴、复用错误dtype的统计或绕过标签约束。

本卡只核对选定OpAPI包装；ACL回退实现、底层归约数学、空有效样本与真实自动求导消费者仍需另外核验，不提供运行复现、性能数字或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLossKernelNpuOpApi.cpp)（primary）：21–77。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLossKernelNpuOpApi.cpp)（implementation）：21–77。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLossBackwardKernelNpuOpApi.cpp)（implementation）：21–59。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLossBackwardKernelNpuOpApi.cpp)（implementation）：21–59。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLoss2dKernelNpuOpApi.cpp)（implementation）：21–82。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLoss2dKernelNpuOpApi.cpp)（implementation）：21–73。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLoss2dBackwardKernelNpuOpApi.cpp)（implementation）：21–74。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NLLLoss2dBackwardKernelNpuOpApi.cpp)（implementation）：21–59。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3835–3865。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3727–3757。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110。
