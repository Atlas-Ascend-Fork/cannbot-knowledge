---
type: API
title: INT4 权重交叠打包（torch_npu.npu_convert_weight_to_int4pack）
description: torch_npu.npu_convert_weight_to_int4pack：INT4 权重交叠打包。将`int32`类型的输入`tensor`打包为`int4`存放，每8个`int4`数据通过一个`int32`数据承载，并进行交叠排放。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_convert_weight_to_int4pack.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:40Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_convert_weight_to_int4pack
---

# INT4 权重交叠打包：torch_npu.npu_convert_weight_to_int4pack

## 用途与语义

将`int32`类型的输入`tensor`打包为`int4`存放，每8个`int4`数据通过一个`int32`数据承载，并进行交叠排放。

## 文档签名

```text
torch_npu.npu_convert_weight_to_int4pack(weight,inner_k_tiles=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_convert_weight_to_int4pack.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
