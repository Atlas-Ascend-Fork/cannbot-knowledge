---
type: API
title: Mish 激活（torch_npu.npu_mish）
description: torch_npu.npu_mish：执行 Mish 非线性激活。 Mish 的参照计算为 `x * tanh(softplus(x))`，不是单独的 tanh。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_mish.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/test/test_base_ops/test_mish.py
  role: supporting
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/op_plugin/ops/opapi/MishKernelNpuOpApi.cpp
  role: supporting
created_at: '2026-11-10T03:38:58Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_mish
---

# Mish 激活：torch_npu.npu_mish

## 用途与语义

执行 Mish 非线性激活。

## 输入、输出与行为

Mish 的参照计算为 `x * tanh(softplus(x))`，不是单独的 tanh。原索引和该版接口文档的“双曲正切”短句不完整；同一固定提交的 `test_mish.py::cpu_op_exec` 给出上述 CPU 参照。这里核对了源码，未运行其中的 NPU 测试。

## 文档签名

```text
torch_npu.npu_mish(self) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_mish.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
- [固定 Mish CPU 参照](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/test/test_base_ops/test_mish.py)（supporting）
- [固定 Mish 调用入口](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/op_plugin/ops/opapi/MishKernelNpuOpApi.cpp)（supporting）
