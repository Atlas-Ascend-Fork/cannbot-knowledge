---
type: API
title: 张量 Dtype 转换与 FakeTensor（torch_npu.npu_dtype_cast）
description: torch_npu.npu_dtype_cast：张量 Dtype 转换与 FakeTensor。执行张量数据类型（dtype）转换。 说明 dtype 转换与 FakeTensor 支持，保留计划废弃状态和迁移验证条件。
tags:
- task.lookup
- topic.compute.elementwise.type_conversion
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_dtype_cast.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_dtype_cast.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4_1/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_dtype_cast
---


# npu_dtype_cast：类型转换与计划废弃入口

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_dtype_cast(input, dtype) -> Tensor
```

把 input 转换为指定 torch.dtype，返回转换后的 Tensor；来源明确支持 FakeTensor 模式。dtype 转换改变数值表示，不是布局或设备迁移的同义操作。

## 参数与组合限制

来源标注该接口计划废弃，并给出 torch.to 作为替代方向；实际 Tensor 代码通常通过 Tensor.to(dtype=...) 表达。计划状态不等于接口已经删除；文档未给出所有类型对的支持清单，不能据此承诺任意转换都可用。

## 验证与模型关联

迁移时核对 dtype、数值截断/溢出、设备和 FakeTensor shape 推导；不依赖上游样例中的随机值作为精度基准。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4_1/models/modeling_deepseek.py#L1299)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 旧接口页面和声明的边界

本卡完整核对发布中文及主线收录的同名中英文页，计划废弃和FakeTensor说明保持。页面仍只给input,dtype，不能因此获得任意dtype对、舍入或溢出保证；FakeTensor只解决元数据推导。两个TorchNPU固定声明还带可选input_dtype，属于额外声明能力，不在这个旧页面里定义完整硬件/类型矩阵，不从npu_format_cast同名参数推导其语义。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 张量 Dtype 转换与 FakeTensor：torch_npu.npu_dtype_cast

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

执行张量数据类型（dtype）转换。

### 文档签名

```text
torch_npu.npu_dtype_cast(input, dtype) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

### 接入特性

该固定文档声明支持 FakeTensor 模式，可在元信息路径描述 dtype 变换，不据此声称真实设备转换已验证。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_dtype_cast.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_dtype_cast.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）
