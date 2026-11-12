---
type: API
title: 分组批量矩阵乘（torch_npu.npu_grouped_matmul）
description: torch_npu.npu_grouped_matmul：按分组边界对多组输入和权重执行矩阵乘，group_list 编码须与路由结果一致。 将相同或相似形状的多组矩阵乘批量处理，可减少独立调用和内存访问开销；具体形状支持、分组边界与收益仍由该版参数契约及实际负载决定。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:43Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_grouped_matmul
- GroupedMatmul
---

# 分组批量矩阵乘：torch_npu.npu_grouped_matmul

## 用途与语义

按分组边界对多组输入和权重执行矩阵乘，group_list 编码须与路由结果一致。

## 输入、输出与行为

将相同或相似形状的多组矩阵乘批量处理，可减少独立调用和内存访问开销；具体形状支持、分组边界与收益仍由该版参数契约及实际负载决定。

## 文档签名

```text
npu_grouped_matmul(x, weight, *, bias=None, scale=None, offset=None, antiquant_scale=None, antiquant_offset=None, per_token_scale=None, group_list=None, activation_input=None, activation_quant_scale=None, activation_quant_offset=None, split_item=0, group_type=None, group_list_type=0, act_type=0, output_dtype=None, tuning_config=None) -> List[Tensor]
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
