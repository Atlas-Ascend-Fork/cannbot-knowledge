---
type: API
title: 多维索引散点更新：保留原输入（torch_npu.npu_scatter_nd_update）
description: torch_npu.npu_scatter_nd_update：多维索引散点更新：保留原输入。将`updates`中的值按指定的索引`indices`更新`input`中的值，并将结果保存到输出tensor，`input`本身的数据不变。 说明多维索引拼接shape、功能版本clone开销及950新增dtype，区分原地版本。
tags:
- task.lookup
- topic.compute.indexing
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_scatter_nd_update.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterNdUpdateKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterNdUpdateKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_nd_update.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_nd_update.py
  role: implementation
created_at: '2026-11-10T03:38:49Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_scatter_nd_update
---


# npu_scatter_nd_update：索引子块覆盖与输入副本

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页与同提交包装/Schema，未运行上游实现或设备实验。本文限定A2/A3/950分支，不把主线新dtype回推发布基线。

## 接口与输入保留

```text
npu_scatter_nd_update(input, indices, updates) -> Tensor
```

将updates写入由indices指定的input子块，返回更新后的副本，原input不变。C++先self.clone()再对副本调用aclnnScatterNdUpdate，Meta也返回新Tensor；即使更新很少，仍不能按只复制更新片段估计显存/带宽。

input为rank1..8的ND，updates同dtype，输入允许非连续。indices为INT32/64 ND，rank至少2，尾维a≤input.rank；updates.shape必须为indices.shape[:-1]+input.shape[a:]。例如input=(4,5,6)、indices=(3,2)时，updates=(3,6)。索引不允许越界，不从PyTorch其他索引接口推定负索引受支持。

A2/A3支持FP16/BF16/FP32、BOOL、INT8/INT64；950额外支持FP8 E4M3FN/E5M2和hifloat8。产品页列单算子与TorchAir图模式。没有对冲突重复索引的覆盖次序保证，也不把update误认为重复位置的累加reduce。

## 验证与选择

检查更新位置、未更新位置和原input均符合预期。需要保留原值时使用此功能版本；允许修改输入时可核对[npu_scatter_nd_update_](npu_scatter_nd_update_.md)的alias与图生命周期，不能仅因性能诉求自动改成原地。

## 发布类型与GE复制复核

发布中文的A2/A3同类型和索引深度合同与主线基本一致；主线中英文仅为950PR及950DT额外列FP8/HiFloat8，不回推发布。旧Atlas产品只列FP16/FP32/BOOL，不从现代产品类型补齐。

两固定C++功能版都clone后更新；两个固定TorchAir Converter也先TensorMove再ScatterNdUpdate，原地入口则直接写self并用dont_prune_me保留副作用。不能因更新少就忽略全输入复制，也不能把直接原地转换器存在当所有函数化/图复用组合均已验证。重复索引没有由随机样例保证覆盖顺序。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 多维索引散点更新：保留原输入：torch_npu.npu_scatter_nd_update

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将`updates`中的值按指定的索引`indices`更新`input`中的值，并将结果保存到输出tensor，`input`本身的数据不变。

### 文档签名

```text
torch_npu.npu_scatter_nd_update(input, indices, updates) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_scatter_nd_update.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterNdUpdateKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterNdUpdateKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_nd_update.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_nd_update.py)（implementation）
