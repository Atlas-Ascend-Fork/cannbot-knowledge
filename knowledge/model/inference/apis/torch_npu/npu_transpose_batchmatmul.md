---
type: API
title: 三维转置批量矩阵乘（torch_npu.npu_transpose_batchmatmul）
description: torch_npu.npu_transpose_batchmatmul：执行张量`input`与张量`weight`的矩阵乘计算。 三维转置批量矩阵乘，仅支持三维输入并限定转置排列。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_transpose_batchmatmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:51Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_transpose_batchmatmul
- 转置批量矩阵乘
---

# 三维转置批量矩阵乘：torch_npu.npu_transpose_batchmatmul

## 用途与语义

执行张量`input`与张量`weight`的矩阵乘计算。

## 输入、输出与行为

该版转置批量矩阵乘仅支持三维 Tensor。转置排列由 perm_x1/perm_x2/perm_y 分别指定：perm_x1 对应 input，perm_x2 对应 weight，perm_y 对应输出。

| 输入维数 | 是否支持 |
| --- | --- |
| 2 | no |
| 3 | yes |
| 4 | no |

该表只判断维数，三维输入还须满足该版具体约束：perm_x1 支持 [0,1,2] 或 [1,0,2]，perm_x2 仅支持 [0,1,2]，perm_y 仅支持 [1,0,2]；不能把“支持转置”理解为任意排列。K、N 需能被128整除；带 scale 时 batch_split_factor 只能为1，bias 当前不支持。

## 文档签名

```text
torch_npu.npu_transpose_batchmatmul(input, weight, *, bias=None, scale=None, perm_x1=[0,1,2], perm_x2=[0,1,2], perm_y=[1,0,2], batch_split_factor=1) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_transpose_batchmatmul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
