---
type: API
title: 矩阵乘 AI Core 硬件校验（torch_npu.matmul_checksum）
description: torch_npu.matmul_checksum：对 matmul 的计算过程进行校验，用于定位 AI Core 硬件故障；校验通过不代表整网数值精度通过。 该接口基于 `torch.matmul`
  和 `Tensor.matmul` 做 AI Core 硬件故障检测。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-matmul_checksum.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:40Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
aliases:
- torch_npu.matmul_checksum
- AI Core 矩阵乘硬件检测
---

# 矩阵乘 AI Core 硬件校验：torch_npu.matmul_checksum

## 用途与语义

对 matmul 的计算过程进行校验，用于定位 AI Core 硬件故障；校验通过不代表整网数值精度通过。

## 输入、输出与行为

该接口基于 `torch.matmul` 和 `Tensor.matmul` 做 AI Core 硬件故障检测。校验误差超过实时门限时，按该检测机制判定 AI Core 错误；这与整网精度容差不是同一判据。

## 文档签名

```text
torch_npu.matmul_checksum(a, b, c) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-matmul_checksum.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
