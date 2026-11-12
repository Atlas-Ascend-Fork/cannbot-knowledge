---
type: API
title: SwiGLU 后动态或静态分组量化（torch_npu.npu_swiglu_quant）
description: torch_npu.npu_swiglu_quant：SwiGLU 后动态或静态分组量化。在swiglu激活函数后添加quant操作，执行输入`x`的`SwiGluQuant`计算，支持`int8`或`int4`量化输出，支持MoE场景和非MoE场景（`group_index`为空），支持分组量化，支持动态/静态量化。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_swiglu_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:50Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_swiglu_quant
---

# SwiGLU 后动态或静态分组量化：torch_npu.npu_swiglu_quant

## 用途与语义

在swiglu激活函数后添加quant操作，执行输入`x`的`SwiGluQuant`计算，支持`int8`或`int4`量化输出，支持MoE场景和非MoE场景（`group_index`为空），支持分组量化，支持动态/静态量化。

## 文档签名

```text
torch_npu.npu_swiglu_quant(x, *, smooth_scales=None, offsets=None, group_index=None, activate_left=False, quant_mode=0, group_list_type=0, dst_type=None) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_swiglu_quant.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
