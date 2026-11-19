---
type: API
title: npu_moe_token_unpermute：K推导、加权还原与反向保存
description: 说明无probs时K固定为1，并区分CANN 9.1反向显存分支和950后端入口的来源差异。
tags:
- task.lookup
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenUnpermuteKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
created_at: '2026-11-09T06:45:04Z'
updated_at: '2026-11-09T23:08:09Z'
platforms:
- a2
- a3
- '950'
---

# npu_moe_token_unpermute：K推导、加权还原与反向保存

## 固定版本与证据边界

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交接口/包装代码，不回推发布基线。本文是静态审阅，未运行上游实现、图编译或设备性能实验。

## 接口与形状

```text
npu_moe_token_unpermute(permuted_tokens, sorted_indices,
    probs=None, padded_mode=False, restore_shape=None) -> Tensor
```

输入特征二维，FP16/BF16/FP32；sorted_indices为一维INT32、无重复、合法完整范围的映射，语义与[npu_moe_token_permute](npu_moe_token_permute.md)配套。有probs=(N,K)时，按映射收回各专家结果，乘路由权重并沿K求和，输出(N,H)。无probs时Meta与C++都令K=1，输出行数等于映射长度；不能把None理解成省掉权重仍按原始多专家K归并。

padded_mode只False，restore_shape只None。A2/A3的K≤512；文档列ND、输入可非连续、输出连续，训练/推理、图模式、确定性。没有额外残差与专家bias参数，不等同于finalize_routing全功能接口。

## 反向保存与版本

同提交包装只在有probs、CANN低于9.1或产品为950时保留permuted_tokens供反向使用。因而A2/A3、CANN≥9.1且不传probs的路径可避免该份前向特征保存；这不是所有产品/带权重训练都可省去的激活。

公开接口只返回还原结果；内部_npu接口的额外保存Tensor不是新的公开返回值。零行梯度有专门分支，不能从Meta形状推定所有空输入都进入同一底层梯度算子。SymInt参数包装中expect_int也不能作为任意无绑定动态形状可用的证明。

## 来源差异

产品页描述950调用aclnnMoeFinalizeRoutingV2，但此提交C++前向实际写的是aclnnMoeTokenUnpermute，950判断用于反向保存策略。本文不承诺该文档所述950底层入口；部署时应核对真正装载的实现与运行库。


## 验证

检查目标产品、执行模式、数据类型、输出形状与实际运行库入口；使用可追踪的小输入对照参考计算，覆盖边界和空值策略。Meta推导成功不等于设备支持，也不代表取得性能收益。

## 双版本梯度、Meta与占位的完整核对

发布正向和梯度由schema生成，主线公共正向调用内部_npu入口，额外保存Tensor仅供反向；公开仍只返回还原结果。主线Meta却无条件把输入permuted_tokens作为内部第二返回，不模拟实际C++按CANN≥9.1、pre950且无probs省去保存的条件，不能从Meta输出推断训练显存。

两版尺寸辅助函数用sorted_indices长度除K，而非只看特征行数，且C++要求K>0；Meta在K=0时直接整除，没有同样的显式检查。旧与新梯度的概率槽即使probs缺失仍会分配底层要求的占位，辅助shape为{}，而Meta返回None；不承诺三条路径统一返回None或零元素Tensor。

主线grad_v2在原始permuted token行数为0时跳过底层梯度调用，将非空的概率梯度缓冲清零；非空路径才调ACLNN。提供probs时内部概率梯度采用probs dtype，特征梯度采用保存的原始dtype。该行为不取消公开padded_mode=False、restore_shape=None及完整索引范围约束，也不证明所有空输入前向有效。文档950的FinalizeRoutingV2说明与本层直接调用MoeTokenUnpermute分别保留。

公开中英文均列仅图模式，且包含单算子示例；产品页的确定性说明不继承到带routing_map的另一接口。主线950只按PR及DT使用。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenUnpermuteKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_unpermute.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）
