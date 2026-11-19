---
type: API
title: npu_clipped_swiglu：GPT-OSS 门控截断与分组
description: 说明奇偶/前后切分、clamp 顺序、分组 token 数量和变体 SwiGLU 参数。
tags:
- task.lookup
- topic.activation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_clipped_swiglu.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/davinci-magihuman/inference/model/dit/dit_module.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_clipped_swiglu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_clipped_swiglu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T01:52:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_clipped_swiglu：GPT-OSS 门控截断与分组

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_clipped_swiglu(x, *, group_index=None, dim=-1, alpha=1.702, limit=7.0, bias=1.0, interleaved=True) -> Tensor
```

按 dim 合轴后切分 x；interleaved=True 在合并的cut*after轴取奇偶元素，False 取前后两半，详细顺序见下文。对 A 仅做上界 limit 截断，对 B 做 [-limit,limit] 截断，再计算 A*sigmoid(alpha*A)*(B+bias)。默认 alpha=1.702、limit=7、bias=1、interleaved=True；输出 dim 轴减半，dtype 同 x。

## 参数与组合限制

- x 为连续 ND Tensor，FP16/BF16/FP32，维数必须大于 1，dim 对应长度为偶数；dim 在 [-x.dim(),x.dim()-1] 内。
- 可选 group_index 是一维 int64 Tensor，每项为一组需要处理的合轴 token 数。来源按其总和过滤合轴后的 pre 轴；它不是累计边界或专家 ID。
- 本接口支持 A2/A3 推理、单算子和图模式。默认奇偶切分与普通 npu_swiglu 的前后切分不同，不能直接替换而不核对权重排列。

## 验证与模型关联

按完整 clamp、切分和 bias 顺序构造参考；覆盖两种 interleaved、group_index 与负值截断，检查 GPT-OSS 的参数是否与模型定义一致。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/davinci-magihuman/inference/model/dit/dit_module.py#L58)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线产品与分组输出边界

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品页新增列出950，A2/A3仍遵守原有连续输入与推理/单算子/图模式限制。group_index是每组计数，不是累计边界。主线生成式包装和Meta仅将dim轴减半，输出分配保留其余轴长度，不按sum(group_index)缩短pre轴；文档中的过滤步骤不能理解为返回一个动态缩短Tensor，尾部哪些行有效需要按真实处理数量核对。

## 奇偶切分的合轴顺序与950范围

发布中文和主线中英文完整公式先以dim合为(pre,cut,after)，再将cut与after并为cut*after，随后在这个合并轴按奇偶或前后切分。dim不是末轴且after>1时，“奇偶”不能直接当作原dim轴上的隔项索引；需要按实际展平顺序重建参考。

主线明确950PR及950DT，发布仅A2/A3；推理、连续ND、dim偶数及默认参数仍保持。group_index用每组计数总和控制pre轴处理前缀，而两版生成式形状helper/Meta只把dim轴除2，没有按该和缩短输出；未处理尾部的有效值没有由分配证明，不能当作已填零或可直接消费。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_clipped_swiglu.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_clipped_swiglu.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_clipped_swiglu.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
