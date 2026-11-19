---
type: API
title: GELU 与乘法融合（torch_npu.npu_gelu_mul）
description: torch_npu.npu_gelu_mul：将输入末维分成两部分，对一部分做 GELU 后与另一部分相乘，适配门控激活路径。 说明前半激活、尾维上限和32字节对齐的性能前提，不与奇偶切分门控混同。
tags:
- task.lookup
- topic.activation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_gelu_mul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gelu_mul.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gelu_mul.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gelu_mul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuNewParams.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T03:38:42Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_gelu_mul
---


# npu_gelu_mul：对半切分与 GELU 乘法融合

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口产品页及同提交 Schema，仅描述下列产品和参数路径，不回推到发布快照。文档支持、来源配套和设备验证分别核对。

## 接口

```text
torch_npu.npu_gelu_mul(input, *, approximate='none') -> Tensor
```

沿最后一维等分A/B，输出GELU(A)*B；不是奇偶交错切分。approximate为none或tanh，默认none。input为ND、2..8维、FP16/BF16/FP32，支持非连续；尾维为正偶数且≤1024，其他维度乘积≤200000。输出同dtype，尾维缩小一半，其他维不变。

来源建议尾轴32B对齐时采用融合API，非32B对齐考虑拆分小算子；这是收益评估条件，不等于文档给出了所有输入的性能保证，也不能把32B直接写成32个元素。输出比对必须用同一approximate和相同权重切分顺序。

产品表列A2/A3/950。本页没有完整反向或图后端矩阵，不从融合名推导任意训练、图模式组合支持。


## 核验

按同一计算顺序、激活模式和量化参数建立参考，检查输出数量、dtype、shape与别名；训练还需验证反向及保存的中间值。再比较正常负载的稳态时间和内存。本次未执行算子、图编译或设备性能测试。

## 发布形状错误与950DT限定

发布中文公式末尾一处称输出与原输入完全同形，但同页返回说明、两固定形状helper与Meta都将尾维除2；主线中英文已改为尾维减半。迁移按半尾维接线，不将旧公式文字作为分配依据。

主线仅新增950DT，未列950PR；A2/A3与旧Atlas产品各按原表消费。两版生成式包装验证none/tanh字符串并调用aclnnGeluMul，helper只是除2不负责全部形状合法性，不能用Meta分配成功证明偶数、维数上限或32字节性能条件均满足。

## 已有 OpPlugin 7.3.0 文档与版本边界

### GELU 与乘法融合：torch_npu.npu_gelu_mul

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将输入末维分成两部分，对一部分做 GELU 后与另一部分相乘，适配门控激活路径。

### 文档签名

```text
torch_npu.npu_gelu_mul(input, *, approximate="none") -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

该版融合路径要求输入尾轴的32B对齐条件；不满足时不能直接引用融合收益，应核对官方建议的拆分计算路径。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_gelu_mul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gelu_mul.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gelu_mul.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gelu_mul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuNewParams.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
