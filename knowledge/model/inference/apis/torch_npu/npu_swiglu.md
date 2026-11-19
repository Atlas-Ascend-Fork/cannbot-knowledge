---
type: API
title: SwiGLU 门控线性激活（torch_npu.npu_swiglu）
description: torch_npu.npu_swiglu：SwiGLU 门控线性激活。Swish门控线性单元激活函数，执行张量`input`的swiglu计算。 限定发布文档确认的 A2 范围，说明 SwiGLU 两半顺序、偶数切分维和非连续限制。
tags:
- task.lookup
- topic.activation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_swiglu.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_swiglu.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_swiglu.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_swiglu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:39:01Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
aliases:
- torch_npu.npu_swiglu
- Swish门控线性单元
---


# npu_swiglu：A2 对半切分、连续性与输出形状

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_swiglu(Tensor input, int dim=-1) -> (Tensor)
```

把 input 沿 dim 分成前半 A、后半 B，计算 A*sigmoid(A)*B。默认 dim=-1，输出相应维度缩小一半，dtype 与输入一致。它与奇偶切分、带 clipping 的 npu_clipped_swiglu 不是同一契约。

## 参数与组合限制

- 发布文档的产品表只确认 A2；本卡据此只声明 a2。Recipes 中出现该调用，不能单独扩大 A3 或其他平台的通用支持范围。
- input 为 1–8 维，FP16/BF16/FP32；dim 必须在 [-input.dim(), input.dim()-1] 内，被切分维度必须能被 2 整除。
- 不支持非连续或空 Tensor；输出也按连续 Tensor 使用。

## 验证与模型关联

按前半/后半顺序构造参考，检查 dim、奇数长度、空输入和非连续视图；不能把不同布局的 gated MLP 权重直接套入该切分顺序。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L313)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 合并完整版本与实现复核

本节已并入 training 树重复入口的固定来源与限定结论；本卡是 npu_swiglu 的 canonical 推理入口，历史跳转卡的 deprecated 状态只描述卡片生命周期，不表示 API 本身废弃。

### 形状与计算

npu_swiglu(self,dim=-1)沿dim分为相同大小A、B，输出A*sigmoid(A)*B。SiLU施加在前半A，交换两半会改变结果。输入rank1..8、分割轴长度为偶数，要求连续且非空；输出该轴减半，其他维不变。文档列FP16、FP32、BF16，不从此推导任意混合dtype输入。

### 版本和平台

发布产品表只确认A2；主线增加950PR/DT及其TorchAir图模式示例，两版都没有A3确认。本卡platforms仅A2，不能通过邻近RMSNorm或其他激活的A3支持推导SwiGLU也支持。主线注册含DVM也不是A3运行保证。

与手写分块组合比较时核对dim、连续化成本、前后半顺序、梯度及极值输入；不能从融合名称承诺性能收益或逐位等价。本卡审阅文档与注册/输出shape helper，未声称已读全设备实现。

## 已有 OpPlugin 7.3.0 文档与版本边界

### SwiGLU 门控线性激活：torch_npu.npu_swiglu

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

Swish门控线性单元激活函数，执行张量`input`的swiglu计算。

### 文档签名

```text
torch_npu.npu_swiglu(Tensor input, int dim=-1) -> (Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：Beta。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_swiglu.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_swiglu.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_swiglu.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_swiglu.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
