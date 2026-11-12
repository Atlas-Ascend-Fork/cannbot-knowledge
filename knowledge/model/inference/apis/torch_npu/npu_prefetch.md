---
type: API
title: 权重 L2 预取（torch_npu.npu_prefetch）
description: torch_npu.npu_prefetch：提前将指定权重区间搬到 L2 Cache，收益取决于实际窗口和计算依赖。 适合检查较大 MatMul 的权重搬运窗口；收益取决于并行方式、实际窗口和依赖关系，不能只由权重张量大小判定预取有效。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_prefetch.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:47Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
aliases:
- torch_npu.npu_prefetch
---

# 权重 L2 预取：torch_npu.npu_prefetch

## 用途与语义

提前将指定权重区间搬到 L2 Cache，收益取决于实际窗口和计算依赖。

## 输入、输出与行为

适合检查较大 MatMul 的权重搬运窗口；收益取决于并行方式、实际窗口和依赖关系，不能只由权重张量大小判定预取有效。

## 文档签名

```text
torch_npu.npu_prefetch(input, dependency, max_size, offset=0) -> None
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_prefetch.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
