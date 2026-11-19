---
type: API
title: npu_moe_token_permute：专家排序、逆映射与输出裁剪
description: 说明token扩展排序和sorted_indices方向，保留完整映射长度、负切片和950 INT8边界。
tags:
- task.lookup
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenPermuteKernelNpuOpApi.cpp
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

# npu_moe_token_permute：专家排序、逆映射与输出裁剪

## 固定版本与证据边界

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交接口/包装代码，不回推发布基线。本文是静态审阅，未运行上游实现、图编译或设备性能实验。

## 接口与映射

```text
npu_moe_token_permute(tokens, indices, num_out_tokens=None,
    padded_mode=False) -> (permuted_tokens, sorted_indices)
```

tokens为二维(N,H)，indices为INT32/INT64的(N,K)或一维(N,)（K=1）。将token复制K份并按专家排序。sorted_indices不是按输出顺序排列的原token ID，而是每个原token专家槽位在排序结果中的位置：在完整未裁剪结果中，permuted_tokens[sorted_indices[i]]=tokens[i//K]。

两个输出均连续，特征输出同输入dtype；映射固定INT32、长度N*K，即使裁剪特征输出也不缩短映射。

## 参数边界

num_out_tokens=None或0保留全部；正值最多保留N*K行，负值使输出长度为N*K+num_out_tokens。Meta和生成式包装没有对过小负数作Python切片的零下限归一化，不把任意负数都当成有效Python切片。按专家排序后的全局前缀截断也不等于每专家独立capacity裁剪。

padded_mode只支持False，文档中的True公式是尚未支持的模式。indices元素数和值均小于16777215，值非负。tokens支持FP16/BF16/FP32；950额外支持作为非量化值搬运的INT8，此时expert ID须小于10240，不能扩展为其他产品的INT8支持。

文档约束列训练/推理、仅图模式、确定性；虽然同时提供单算子示例，也不据此升级为已确认的Eager产品保证。输入ND、允许非连续和空Tensor，仍需保持成对维度与合法索引。

## 配套接口

完整映射可交给[npu_moe_token_unpermute](npu_moe_token_unpermute.md)。若裁剪了特征输出，映射可能指向已删除行，不能直接保证任意裁剪后的调用可逆；需按实际丢弃规则验证。


## 验证

检查目标产品、执行模式、数据类型、输出形状与实际运行库入口；使用可追踪的小输入对照参考计算，覆盖边界和空值策略。Meta推导成功不等于设备支持，也不代表取得性能收益。

## 两版生成路径与反向保存优化

两固定提交的正向都由schema生成：按indices元素数M分配完整INT32映射，特征行数为正num_out_tokens取min(n,M)、非正取M+n，None按0。因此负值小于-M会产生负的分配尺寸，没有Python切片的零下限保护；这个限制在Meta与输出尺寸辅助函数中一致，不能把任意负数宣传成合法切片。包装没有读取索引内容验证专家ID或补齐token数，产品限制继续适用。

发布反向声明仍传tokens和indices；主线改用grad_v2，只传原token行数、dtype、topK、上游梯度及sorted_indices，减少为此反向接口保存完整特征/索引输入的需要。新手写MoeTokenPermuteKernelNpuOpApi.cpp只实现grad_v2，不是正向；它对SymInt调用expect_int，不保证任意无绑定动态尺寸可执行。这里只说明保存依赖改变，未测量实际显存。

主线产品的950范围为PR及DT；INT8是非量化数值搬运，不会返回量化scale，ID上限10240也不等于其他float路径的16777215。公开仅图模式与单算子示例并存的差异保留，转换器树的局部搜索未发现独立注册，不扩为所有后端都不支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_token_permute.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeTokenPermuteKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）
