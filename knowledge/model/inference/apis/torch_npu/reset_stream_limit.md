---
type: API
title: 流资源限制重置（torch.npu.reset_stream_limit）
description: torch.npu.reset_stream_limit：恢复指定 Stream 的默认资源限制，与 set_stream_limit 的设置操作配套。 先前由 set_stream_limit 设置的指定
  Stream 可恢复默认资源限制，随后通过 get_stream_limit 读取核对；重置操作不推导其他流或其他进程的状态。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-reset_stream_limit.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:51Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch.npu.reset_stream_limit
- 流资源限制重置
---

# 流资源限制重置：torch.npu.reset_stream_limit

## 用途与语义

恢复指定 Stream 的默认资源限制，与 set_stream_limit 的设置操作配套。

## 输入、输出与行为

先前由 set_stream_limit 设置的指定 Stream 可恢复默认资源限制，随后通过 get_stream_limit 读取核对；重置操作不推导其他流或其他进程的状态。

## 文档签名

```text
torch.npu.reset_stream_limit(stream) -> None
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

重置的是参数指定的流，不能因当前流被重置就推断所有流均已恢复。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-reset_stream_limit.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
