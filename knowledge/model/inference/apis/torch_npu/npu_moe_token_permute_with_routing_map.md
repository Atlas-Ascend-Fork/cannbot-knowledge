---
type: API
title: npu_moe_token_permute_with_routing_map：路由矩阵与容量取整
description: 区分固定K和drop/pad模式，说明num_out_tokens默认N、实际输出向下取整及可选概率输出。
tags:
- task.lookup
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute_with_routing_map.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute_with_routing_map.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapGradOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapGradOpApi.cpp
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

# npu_moe_token_permute_with_routing_map：路由矩阵与容量取整

## 固定版本与证据边界

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交接口/包装代码，不回推发布基线。本文是静态审阅，未运行上游实现、图编译或设备性能实验。

## 接口

```text
npu_moe_token_permute_with_routing_map(tokens, routing_map, *,
    probs=None, num_out_tokens=None, drop_and_pad=False)
    -> (permuted_tokens, permuted_probs, sorted_indices)
```

tokens=(N,H)、FP16/BF16/FP32；routing_map=(N,E)、BOOL或仅0/1的INT8，表示token被哪些专家选中。probs若提供为(N,E)、一般与tokens同dtype，BF16 tokens额外允许FP32 probs；不传时概率输出无有效Tensor，不把它视为已计算的全零权重。

## 两种模式与输出长度

- drop_and_pad=False：每个token选择相同K个专家，K=num_out_tokens//N，输出行数K*N，按专家排列。映射是每token专家槽位到排序行的位置。
- drop_and_pad=True：按每专家capacity=num_out_tokens//E分配，输出行数capacity*E，包含drop/pad；此时映射表示token ID，不能沿用普通模式的逆置换解释。

num_out_tokens=None在包装和Meta中均默认N，**不会自动统计routing_map中的总选中数**；范围[0,N*E]。实际行数向下取整为N或E的倍数，不是无条件等于传入的num_out_tokens。无pad模式K<512，K*N、N、E等文档上限小于16777215。零维度会涉及整除，不能只凭支持空Tensor就认为所有N=0或E=0组合可用。

sorted_indices为INT32，长度等于实际输出行数；有probs时permuted_probs也为相同行数的一维结果。ND输入可非连续；文档列训练/推理、仅图模式及确定性。

- [配套还原接口](npu_moe_token_unpermute_with_routing_map.md)


## 验证

检查目标产品、执行模式、数据类型、输出形状与实际运行库入口；使用可追踪的小输入对照参考计算，覆盖边界和空值策略。Meta推导成功不等于设备支持，也不代表取得性能收益。

## 完整双语与空轴、可选概率

两个固定C++和Meta都先按routing_map的某一轴做整除：普通模式除tokens轴，drop_and_pad除experts轴。该轴为0时没有先行分支处理，所以“支持空Tensor”不能覆盖所有零token/零expert组合。它们也不在包装内核实每行true数、binary值或概率dtype；分配成功不证明路由矩阵符合公开契约。

probs=None时C++返回未分配的可选概率槽，Meta返回None，不能要求统一的可读零元素Tensor或当作全零权重。提供probs时概率只随路由重排，不在这里乘进tokens；普通模式默认num_out_tokens=N要求实际固定K与该值匹配，不能自动统计map中所有true。

反向对tokens与probs两个输出可微，sorted_indices不可微；Grad包装用显式T/E尺寸，概率梯度仅在存在上游probs_grad时分配并沿用其dtype。BF16 tokens配FP32 probs的例外不自动扩为所有混合dtype，也不等同于配套unpermute内部概率梯度缓冲的类型策略。drop/pad的公式与分配并未给出所有填充值的数值保证。950明确仅PR及DT。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute_with_routing_map.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute_with_routing_map.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapGradOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenPermuteWithRoutingMapGradOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
