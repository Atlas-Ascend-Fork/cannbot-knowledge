---
type: Guide
title: 原生GroupNorm桥接：统计对象、反向掩码与分派边界
description: 追踪GroupNorm到ATen BatchNorm反向的对象与槽位，区分前向统计、候选分派、掩码分配和无条件view的静态边界。
tags:
- task.optimization
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GroupNormKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GroupNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GroupNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GroupNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BatchNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BatchNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T14:02:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生GroupNorm桥接：统计对象、反向掩码与分派边界

## 固定范围与阅读入口

核对 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 和发布 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的原生 GroupNorm ACL前向、两路反向及其调用到的 BatchNorm反向包装。五对所选C++去注释/空白并拼接续行后token相同；此结论不扩展为整个runtime、生成物或kernel相同。平台及完整配套未知，保持draft、空平台。

[公开Norm限制](torch_npu_native_normalization_constraints.md)和[GE层组/RMS转换](../../inference/guides/optimization/torchair/torchair_ge_layer_group_rms_norm_lowering.md)已有对应内容。本卡补 Eager ACL→ATen桥接、实际统计对象传递和掩码处理；不把GE节点、公共Swish/SiLU接口或局部注册当作同一路执行。未导入、生成、编译或执行上游，未做训练、数值或设备实验。

## 前向准备与两个ACL算子不能混写

Schema的native_group_norm OpAPI生成描述申请y同input、mean/rstd为(N,group)且dtype取input，exec为aclnnGroupNorm。这是固定生成描述，不是本卡运行生成器、核对安装包生成物或验证kernel累加精度的结果。

ACL前向另先申请result，以及按X.options、ND、(N,group)准备mean/variance/rstd三份统计对象，再探测aclnnGroupNormSwish及其GetWorkspaceSize。兼容宏在ACLNN-only且缺符号时报错，其余缺符号情况返回旧GroupNorm表达式，不能从函数名或回退字样推定所有设备无条件可走旧实现。

符号检查通过后，局部SoC门控仍决定是否用旧表达式：条件是`Ascend910B1<=SoC<Ascend310B1`或`SoC>Ascend310B4`才走GroupNormSwish，其余走GroupNorm。它是枚举比较，不是已复核的产品支持矩阵。

- 旧路径用OpCommand GroupNorm，activate无独立属性，is_training=True；缺gamma/beta时按C和X.options构造1/0。算子输出接入variance，随后以`1/(variance+eps).sqrt()`构造rstd并重新绑定变量。
- Swish名称路径也构造缺失仿射，但设置activate_swish=False，直接以第三输出接rstd；不能当成公共npu_group_norm_swish默认激活等价物。

两条路径都以float属性传eps。前向返回三项不意味着包装只准备了三份Tensor，也不能把准备统计对象的dtype等同于所有中间计算精度；旧路径重绑定rstd还增加了算术调用。实际临时量、布局整理和收益需要测量。

## OpAPI反向按gamma对象和mask申请

OpAPI native_group_norm_backward先检查aclnnGroupNormBackward兼容性，借用Optional weight得到gamma，按mask申请：dx依据input，dgamma/dbeta依据gamma，均用apply_tensor_without_format。没有在此把所有仿射梯度强制为FP32；也没有缺weight时先填一份C元素ones的本地分支。不能从LayerNorm或BatchNorm的FP32输出规则推导这里相同。

mask为false的局部槽保持未定义，完整mask、N/C/HxW/group、mean/rstd和gamma传给ACLNN；包装没有在此完整验证这些尺寸相互一致或建立空输入特例。Optional存在和参数透传不认证任意缺weight与请求仿射梯度的组合均已核对。

## ACL反向如何进入ATen BatchNorm

ACL入口只显式拒绝group=0。输入rank不等于3时，input/grad_out先view为(N,C,HxW)；gamma定义时先按(1,C,1)乘到dy。随后把样本和组折到通道维，形成(1,N*group,N>0?-1:1)，mean变为(N*group)。它没有先统一contiguous，view合法性及N/C/HxW一致性仍需调用者满足。

传入rstd经以下明确算术重建对象：`variance_like=1/(rstd*rstd)-1e-5`，再view为(N*group)。以ones(N*group)为weight，running_mean/var为nullopt、train=True、eps=1e-5和原output_mask，调用`at::native_batch_norm_backward`，不是直接调用`acl_op::native_batch_norm_backward`。

这条ATen调用保留分派，所查Schema同时声明ACL和OpAPI候选；本卡没有生成/加载注册或运行包确认某环境一定选择哪一路。把GroupNorm已进入ACL包装当成其内部ATen调用也一定继续ACL，会漏掉统计约定和mask消费者的边界。

## 统计对象、槽名和底层数学合同分别记录

| 所查候选BatchNorm包装 | 可直接确认的传递 |
| --- | --- |
| ACL native_batch_norm_backward | train=True时继续使用save_mean/save_invstd传入对象；UpdateGrad和ReduceGrad的Input标签分别为batch_mean/batch_variance，epsilon也继续传入。 |
| OpAPI native_batch_norm_backward | 将save_mean_opt/save_invstd_opt和eps等原样交aclnnBatchNormBackward；本层没有把传入对象重新求倒数、开方或恢复另一统计量。 |

上表只核对Python/C++层对象和槽位，`batch_variance`标签、`save_invstd`变量名都不是本卡已展开的底层数学合同。不能仅凭名字断言统计量传错、不同后端数学等价或某训练路径必错；需要核对实际选中后端及底层算子定义，再做数值对照。

同样不能只见内部固定eps=1e-5就断言任意非默认前向eps被丢弃：传入rstd本身可能已编码前向eps，调用方又显式构造上述对象并向下游传eps。有效解释必须连同底层计算一起核验；本卡没有进行这种设备验证。

## mask控制了返回，不必然省掉准备和计算

所读ACL BatchNorm包装先申请三份梯度，两个仿射梯度显式FP32；batch_norm_backward_impl无条件调用training_update，mask[0]才控制输入梯度reduce/infer计算，最后对false槽赋未定义Tensor。OpAPI BatchNorm包装则按mask分配输出，再传完整mask给ACLNN；false槽同样保持未定义。OpAPI部分另见[BatchNorm OpAPI指南](torch_npu_native_batch_norm_opapi_execution.md)，ACL部分依据本卡所列实现；不能用最终None推定前面没有工作。

ACL GroupNorm拿到上述第0槽后，却没有先判断output_mask[0]或defined，就无条件view回输入形状。对mask[0]=False且确实到达所查候选BN消费者、按该返回合同拿到未定义槽的路线，调用方缺少本地保护；这是明确的静态通路边界，不是本卡已运行复现，也不意味着所有自动求导调用都会请求该mask或进入此入口。

GroupNorm的dgamma/dbeta还在该ATen调用之后另按自身mask构造：dgamma从原dy、input、mean/rstd广播后逐空间轴和batch求和，dbeta从原dy归约。它没有直接返回BN仿射梯度，所以不能用BN中间FP32申请认证最终GroupNorm仿射梯度的全部精度，亦不能把这些BN输出当作无代价的复用结果。

## 优化与验证入口

先记录准确原生入口、选中后端、前向统计来源、rstd对象及输出mask，再检查Optional gamma、view所需stride、N/C/HxW/group和零N。分别对照旧GroupNorm与activate_swish=False路线、ACL/OpAPI原生反向及ATen桥接，把同一统计对象如何被解释作为验收项目。

至少分别核对仅输入梯度、仅仿射梯度、全部梯度和缺weight组合的中间/最终dtype与未定义槽；不要通过随意改rstd为variance或强制某后端掩盖不明合同。数值与真实autograd通过后再比较前向额外统计、归约和格式准备成本。本卡未执行这些实验，不新增verified或性能数字。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GroupNormKernelNpu.cpp)（primary）：20–125。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GroupNormKernelNpu.cpp)（implementation）：20–125。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GroupNormBackwardKernelNpu.cpp)（implementation）：20–93。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GroupNormBackwardKernelNpu.cpp)（implementation）：20–93。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupNormBackwardKernelNpuOpApi.cpp)（implementation）：20–56。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupNormBackwardKernelNpuOpApi.cpp)（implementation）：20–56。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BatchNormBackwardKernelNpu.cpp)（implementation）：20–296。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BatchNormBackwardKernelNpu.cpp)（implementation）：20–267。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp)（implementation）：20–79。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp)（implementation）：20–50。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3743–3746,3756–3774。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3639–3641,3651–3669。
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119。
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–112。