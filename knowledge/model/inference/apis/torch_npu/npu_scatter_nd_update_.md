---
type: API
title: 多维索引散点原地更新（torch_npu.npu_scatter_nd_update_）
description: torch_npu.npu_scatter_nd_update_：多维索引散点原地更新。将`updates`中的值按指定的索引`indices`更新`input`中的值，并将结果保存到输出tensor，`input`中的数据被改变。 说明 scatter 原地副作用、索引类型及 updates 的精确形状关系，避免误作非原地更新。
tags:
- task.lookup
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_scatter_nd_update_.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update_.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterNdUpdateKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update_.md
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
created_at: '2026-11-10T03:38:50Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_scatter_nd_update_
---


# npu_scatter_nd_update_：原地更新、索引深度与 KV 写入

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_scatter_nd_update_(input, indices, updates) -> Tensor
```

按 indices 将 updates 写入 input，input 的数据会改变，返回更新结果。末尾下划线代表原地语义；共享该存储的消费者需考虑修改后的内容和跨流依赖。

## 参数与组合限制

- input 为 1–8 维 ND，dtype 与 updates 一致；A2/A3 支持 FP32、FP16、BF16、bool、int64、int8，支持非连续 Tensor。
- indices 为 int32/int64，至少二维，索引值不能越界；其末维大小 a 不能大于 input.dim()。
- updates.shape 必须等于 indices.shape[:-1] + input.shape[a:]。例如 input=(4,5,6)、indices=(3,2) 时 updates=(3,6)。
- 来源确认支持图模式；这不代替原地算子的函数化、别名以及 KV Cache 生命周期检查。文档未承诺重复索引的写入顺序，不能依赖自定的最后写入者规则。

## 验证与模型关联

用无重复、边界合法的索引与参考 scatter 比较，检查原 input 和别名观察值；覆盖索引深度及图模式原地行为，重复索引需另行确定实际语义。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py#L448)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线950和alias核对

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品页保留A2/A3原类型，并为950增加FP8 E4M3FN/E5M2和hifloat8；不回推原发布页。Schema声明Tensor(a!)并返回相同alias，C++直接更新self、Meta返回self，没有功能版本的整Tensor clone。索引拼接updates.shape、合法范围与重复索引未承诺次序仍适用。

需要保留原输入时使用[npu_scatter_nd_update](npu_scatter_nd_update.md)；图复用、共享view与反向保存须检查输入改变带来的影响，不能仅因为原地调用分配更少就直接替换。

## 完整版本页及两条原地实现

发布中文与主线中英文按索引尾深度拼接updates.shape的规则保持；主线原型显式补Tensor(a!)，950PR/DT增加FP8/HiFloat8，未扩到发布。两版C++直接更新self，Meta直接返回self；两个固定GE转换器也直接ScatterNdUpdate并保留副作用标记。

函数版各有clone/TensorMove，不能把它的输入保持保证套给此入口。索引值合法、更新未重叠的需求与保存供反向/图复用的旧内容分别核对，静态alias不替代跨流同步或设备验证。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 多维索引散点原地更新：torch_npu.npu_scatter_nd_update_

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将`updates`中的值按指定的索引`indices`更新`input`中的值，并将结果保存到输出tensor，`input`中的数据被改变。

### 文档签名

```text
torch_npu.npu_scatter_nd_update_(input, indices, updates) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_scatter_nd_update_.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update_.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update_.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterNdUpdateKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_nd_update_.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterNdUpdateKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_nd_update.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_nd_update.py)（implementation）
