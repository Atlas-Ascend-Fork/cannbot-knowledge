---
type: API
title: NPU 设备标记与 Host 内存张量分配（torch_npu.empty_with_swapped_memory）
description: torch_npu.empty_with_swapped_memory：NPU 设备标记与 Host 内存张量分配。申请一个device信息为NPU且实际内存在host侧的`Tensor`。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-empty_with_swapped_memory.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:39Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.empty_with_swapped_memory
---

# NPU 设备标记与 Host 内存张量分配：torch_npu.empty_with_swapped_memory

## 用途与语义

申请一个device信息为NPU且实际内存在host侧的`Tensor`。

## 文档签名

```text
torch_npu.empty_with_swapped_memory(size, dtype=None, device=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-empty_with_swapped_memory.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
