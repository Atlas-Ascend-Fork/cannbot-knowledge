---
type: API
title: 量化散点更新：保留原输入（torch_npu.npu_quant_scatter）
description: torch_npu.npu_quant_scatter：量化散点更新：保留原输入。量化 updates 后按 axis 与 indices 写入新输出，保留原 input。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_scatter.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:48Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
aliases:
- torch_npu.npu_quant_scatter
- 非原地量化散点更新
---

# 量化散点更新：保留原输入：torch_npu.npu_quant_scatter

## 用途与语义

量化 updates 后按 axis 与 indices 写入新输出，保留原 input。

## 文档签名

```text
torch_npu.npu_quant_scatter(input, indices, updates, quant_scales, quant_zero_points=None, axis=0, quant_axis=1, reduce='update') -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

返回新输出与原地版本的副作用不同，图捕获时应核对调用重载与别名。该文档只明确列出 A2。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_scatter.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
