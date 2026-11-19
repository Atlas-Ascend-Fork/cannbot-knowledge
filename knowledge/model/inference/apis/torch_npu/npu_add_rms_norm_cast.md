---
type: API
title: npu_add_rms_norm_cast：950 双精度输出与残差
description: 说明 FP32/输入精度双输出、残差和统计形状，保留 rstd 名称与来源语义差异。
tags:
- task.lookup
- topic.compute.normalization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_cast.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_cast.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T01:56:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_add_rms_norm_cast：950 双精度输出与残差

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_add_rms_norm_cast(x1, x2, gamma, epsilon=1e-06) -> (Tensor, Tensor, Tensor, Tensor)
```

融合 x=x1+x2、RMSNorm 与类型转换，按返回说明顺序为 (y1,y2,rstd,x)：y1 为 FP32，y2 与 x1 同 dtype，二者 shape 同 x1；最后一项为残差相加结果。调用方应按返回说明确认 dtype，不按公式中的 y1/y2 命名猜测转换顺序。

## 参数与组合限制

x1/x2 为 shape/dtype 相同的 1–8 维 FP16/BF16 ND，gamma 与 x1 同 dtype、匹配归一化尾维；支持空和非连续。rstd 为 FP32、与 x1 同维，归一化的维度为 1，输入为空时统计也为空。所有轴大小≤2147483647。来源将 rstd 称为标准差，而同类 RMSNorm 接口通常描述倒数；本文不跨接口推定其数值定义，需结合实际实现验证后再用于统计或反向。

## 验证与模型关联

先检查四项返回的 dtype/shape，再分别对比残差与归一化输出；对 rstd 的值建立独立探针，不仅检查名称与长度。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py#L1390)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 950PR/DT与生成式四输出证据

主线双语明确仅950PR及950DT，训练/推理、单算子与图模式；发布没有此公开页，同名代码和schema存在也不补出发布支持合同。两固定生成式声明均按FP32、x1.dtype、FP32、x1.dtype依次分配四输出，形状沿用普通RMS helper；两版Meta同样分配，不由公式里命名顺序交换y1/y2。

产品页将rstd表述为标准差/均方根而公式和同族语义不一致；包装与Meta只分配形状/类型，不能据此确认其数值究竟为哪种统计量。本卡保留该未解冲突，尤其反向或统计消费前须做实际数值探针。空输入时统计也为空的公开约束仍保留，不能以helper仅将归一化轴置1便推定所有零轴组合有效。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_cast.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_cast.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
