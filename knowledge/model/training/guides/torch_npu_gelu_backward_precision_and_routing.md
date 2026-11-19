---
type: Guide
title: 原生GELU反向：类型准备、近似校验与版本路由
description: 追踪GELU反向的广播和result_type输出准备、近似字符串校验顺序，以及ACLNN-only与兼容标志的两版差异。
tags:
- task.optimization
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GeluBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuNewParams.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T14:44:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生GELU反向：类型准备、近似校验与版本路由

## 固定准确入口

本卡针对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的OpAPI `gelu_backward(grad_output,self,approximate)`。[公开激活约束](torch_npu_native_activation_precision.md)已有GELU产品、近似及前向out路由，[GE激活](../../inference/guides/optimization/torchair/torchair_ge_activation_lowering.md)已有另一层转换。本卡补原生反向消费者，不把npu_gelu、FastGelu或GE GeluGrad当作同一实现。

平台与完整配套未知，保持draft、空平台。两版所选反向的完整token差异是主线增加IsAclnnOnly判断，字符串helper的所选合同相同；未运行上游、编译、生成、自动求导或设备实验。

## 结果类型提升不是输入都已转换

入口先以static变量保存CheckCompatibleImpl结果，再用broadcast_ops_npu_output_size(grad_output,self)取得候选输出shape，用at::native::result_type取得候选dtype；随后依据grad_output.options().dtype(output_dtype)申请无格式grad_input。

这是显式准备顺序，不能照输入self dtype一概估算输出大小，也不能从存在广播/type-promotion helper就认证任意混合dtype或广播均被底层支持。后续ACLNN调用仍传原始grad_output和self，这几段没有先将两者都转成result_type，也没有在返回前统一转回self dtype。kernel累加精度、内部转换和实际显存峰值仍需下层证据。

## approximate在旧分支之前也会校验

申请grad_input之后，无论即将选旧还是V2，都会调用npu_gelu_approximate_str。该helper只接受精确小写none/tanh，其余TORCH_CHECK报参数错误，返回所读字符串。再从该局部string取得c_str并const_cast成char指针；V2调用传此指针。

旧aclnnGeluBackward调用不接approximate，却不能据此说非法字符串被静默忽略：本地校验早已发生。另一方面，合法字符串通过也不证明旧算子按该值切换近似算法。分配在字符串检查之前，亦不能把参数报错路径当成前面完全没有输出准备。本卡没有执行异常或异步指针寿命实验。

## 两版选择条件不能混写

| 固定版本 | 旧aclnnGeluBackward条件 | 其他情况 |
| --- | --- | --- |
| 发布 | `!gelu_sc` | 调aclnnGeluBackwardV2，传approximate_ptr。 |
| 主线 | `!IsAclnnOnly() && !gelu_sc` | 调aclnnGeluBackwardV2，传approximate_ptr。 |

gelu_sc是本函数static缓存，不能靠运行中修改相关配置就假设重新求值。主线即使兼容标志关闭，只要所选IsAclnnOnly返回真也转V2；这是源码路由，不是产品支持矩阵或V2存在/执行成功保证。

只有旧分支内部使用DO_COMPATIBILITY检查旧执行及GetWorkspaceSize符号：缺符号且ACLNN-only时报错，否则返回acl_op::gelu_backward表达式。发布版旧条件没有先排除ACLNN-only，因此可能到该宏拒绝；不能把主线条件反填到发布。V2分支没有在这几段执行同一个旧符号兼容宏，不能推导V2任意缺失/参数错误都自动回退。

兼容宏发生在输出申请及字符串校验之后；若它返回ACL表达式，前面的候选输出已经准备，不能将调用点当成零成本后端选择。没有展开ACL回退主体，不认证其布局、dtype或近似算法与V2等价。

## Schema与验收边界

两版Schema都为准确gelu_backward声明ACL及OpAPI候选、`[v2.1,newest]`和默认approximate='none'；主线该条目另外列dvm。声明不等于安装包分派或自动求导实际选择，本卡不依据候选存在认证完整训练或图模式。

记录真实grad_output/self的shape、dtype、stride、approximate、兼容标志首次读取时机及实际后端，分别比较旧/V2和准确前向。尤其保留合法none/tanh与非法字符串、混合dtype和广播边界的区别；先核输出/梯度数值和实际路由，再量分配与运行代价。本卡没有运行这些检查，不提供性能数字或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluBackwardKernelNpuOpApi.cpp)（primary）：20–39。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GeluBackwardKernelNpuOpApi.cpp)（implementation）：20–39。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp)（implementation）：27–34。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuNewParams.cpp)（implementation）：26–32。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2452–2456。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2374–2377。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110。
