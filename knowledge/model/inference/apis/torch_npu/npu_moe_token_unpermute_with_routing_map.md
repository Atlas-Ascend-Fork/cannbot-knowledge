---
type: API
title: npu_moe_token_unpermute_with_routing_map：无效槽位与非确定性
description: 说明restore_shape必填、-1槽位、容量映射和可选权重，避免继承前向重排的确定性保证。
tags:
- task.lookup
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute_with_routing_map.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute_with_routing_map.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapGradKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapGradKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T06:45:04Z'
updated_at: '2026-11-09T23:08:09Z'
platforms:
- a2
- a3
- '950'
---

# npu_moe_token_unpermute_with_routing_map：无效槽位与非确定性

## 固定版本与证据边界

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交接口/包装代码，不回推发布基线。本文是静态审阅，未运行上游实现、图编译或设备性能实验。

## 接口

```text
npu_moe_token_unpermute_with_routing_map(permuted_tokens,
    sorted_indices, restore_shape, *, probs=None,
    routing_map=None, drop_and_pad=False) -> Tensor
```

restore_shape必填、恰为(N,H)，返回同dtype的二维还原结果；特征支持FP16/BF16/FP32、ND和非连续输入。probs=(N,E)，一般同特征dtype，BF16特征额外允许FP32概率。routing_map为BOOL或0/1 INT8的(N,E)；probs=None时可不传routing_map。

## 映射不能混用

无pad模式的输入行数为N*K，K≤512，sorted_indices是一维INT32槽位映射，允许-1跳过无效项。每token实际选中专家数可小于等于预留K，但对应[前向routing-map重排](npu_moe_token_permute_with_routing_map.md)要求固定K，不能由还原支持可变槽位推出前向也支持任意可变K。

drop_and_pad=True时输入与索引长度为E*capacity，sorted_indices改为[0,N-1]的token ID；按token聚合容量内专家结果。不能把这类索引送入普通逆映射路径。带权重参考应只乘一次路由权重；来源非pad公式同时出现预乘和累加乘权，不能机械照抄为两次加权。

文档列仅图模式、训练/推理，默认**非确定性**，可通过aclrtCtxSetSysParamOpt开启确定性。前向重排的确定性保证不自动传递到本还原算子。

## 警告与内部输出

文档提示未来会拦截capacity>N、特定专家数不匹配、错误routing_map类型/shape或非ND格式；当前仅warning不构成受支持输入保证。C++内部还返回反向用的索引和概率缓存，公开接口只取还原结果，不能按内部四元组设计应用调用。


## 验证

检查目标产品、执行模式、数据类型、输出形状与实际运行库入口；使用可追踪的小输入对照参考计算，覆盖边界和空值策略。Meta推导成功不等于设备支持，也不代表取得性能收益。

## 反向缓存与概率梯度类型

两版内部前向都分配out_index和permuted_token_id，提供probs才分配permute_probs，公开函数只取第一个结果。drop_and_pad的反向使用计算得到的辅助索引，普通模式则两次传入原sorted_indices；不能让应用直接把内部四返回当成公共调用协议。

两个反向C++与Meta都按上游特征梯度的dtype分配概率梯度缓冲；当特征梯度为BF16、原概率为FP32时，这里也不是FP32缓冲。后续自动求导可能还有类型转换，本卡不据此宣称用户最终grad对象一定为BF16，但不能把“前向允许FP32概率”当作内部反向全程FP32的保证。

普通unpermute的保存优化没有移植到这一分支：其反向声明仍使用permuted_tokens与probs。包装只下传一次权重，实际计算在底层，公开非pad伪公式的预乘与再乘不能顺序照抄成平方权重。-1无效槽、固定上限K≤512和未来warning条件按本接口独立限定。950仅PR及DT，默认非确定性由公开CANN运行时设置控制，没有新增Python开关。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute_with_routing_map.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute_with_routing_map.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapGradKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenUnpermuteWithRoutingMapGradKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
