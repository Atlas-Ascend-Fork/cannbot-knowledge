---
type: API
title: 符号位打包（torch_npu.npu_sign_bits_pack）
description: torch_npu.npu_sign_bits_pack：把浮点值的符号编码到 uint8 字节中，以每字节八个位保存。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_sign_bits_pack.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:39:01Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_sign_bits_pack
---

# 符号位打包：torch_npu.npu_sign_bits_pack

## 用途与语义

把浮点值的符号编码到 uint8 字节中，以每字节八个位保存。

## 文档签名

```text
torch_npu.npu_sign_bits_pack(self, size) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

## 接入特性

输入为一维 float16/float32，编码后的元素类型为 uint8；每个字节承载8个符号位，按小端序打包。不满8个输入时按该版规则补齐到字节边界，size 用于输出第一维重排。

| 输入符号 | 编码位 |
| --- | --- |
| -1.0 | 0 |
| 1.0 | 1 |

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_sign_bits_pack.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
