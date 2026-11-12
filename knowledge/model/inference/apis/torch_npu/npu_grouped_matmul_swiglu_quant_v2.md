---
type: API
title: 分组矩阵乘与 SwiGLU 量化融合（torch_npu.npu_grouped_matmul_swiglu_quant_v2）
description: torch_npu.npu_grouped_matmul_swiglu_quant_v2：将 GroupedMatmul、SwiGLU 与量化组合，减少中间结果的独立处理。 链路按矩阵乘结果进入 SwiGLU
  门控激活后再量化理解，不能将单独的浮点 GMM 输出当成融合链最终输出。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:44Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_grouped_matmul_swiglu_quant_v2
---

# 分组矩阵乘与 SwiGLU 量化融合：torch_npu.npu_grouped_matmul_swiglu_quant_v2

## 用途与语义

将 GroupedMatmul、SwiGLU 与量化组合，减少中间结果的独立处理。

## 输入、输出与行为

链路按矩阵乘结果进入 SwiGLU 门控激活后再量化理解，不能将单独的浮点 GMM 输出当成融合链最终输出。

## 文档签名

```text
torch_npu.npu_grouped_matmul_swiglu_quant_v2(x, weight, weight_scale, x_scale, group_list, *, smooth_scale=None, weight_assist_matrix=None, bias=None, dequant_mode=0, dequant_dtype=0, quant_mode=0, quant_dtype=0, group_list_type=0, tuning_config=None) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
