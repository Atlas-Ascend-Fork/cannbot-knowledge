---
type: API
title: 量化 scale 编码（torch_npu.npu_trans_quant_param）
description: torch_npu.npu_trans_quant_param：将浮点 scale 编码成量化矩阵乘需要的整数位域表示，可同时编码 offset。 这里的输入是 float32 scale，编码后的位域用
  int64 张量承载；输入浮点精度与输出承载类型是两项不同约束。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_trans_quant_param.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:51Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_trans_quant_param
---

# 量化 scale 编码：torch_npu.npu_trans_quant_param

## 用途与语义

将浮点 scale 编码成量化矩阵乘需要的整数位域表示，可同时编码 offset。

## 输入、输出与行为

这里的输入是 float32 scale，编码后的位域用 int64 张量承载；输入浮点精度与输出承载类型是两项不同约束。

## 文档签名

```text
torch_npu.npu_trans_quant_param(scale, offset=None, round_mode=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

这是位域编码，不是对 scale 做数值 `.to(int64)`。输出张量用 int64 承载；图模式还涉及 uint64 表示，应与 npu_quant_matmul 配套消费。带 offset 时不能照搬无 offset 的 grouped-matmul 使用条件。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_trans_quant_param.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
