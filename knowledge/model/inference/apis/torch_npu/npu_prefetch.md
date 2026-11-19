---
type: API
title: 权重 L2 预取（torch_npu.npu_prefetch）
description: torch_npu.npu_prefetch：提前将指定权重区间搬到 L2 Cache，收益取决于实际窗口和计算依赖。 适合检查较大 MatMul 的权重搬运窗口；收益取决于并行方式、实际窗口和依赖关系，不能只由权重张量大小判定预取有效。 区分预取提示与数值计算，明确 dependency、地址范围和性能收益的验证条件。
tags:
- task.lookup
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_prefetch.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prefetch.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/common_utils.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prefetch.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_prefetch.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PrefetchKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PrefetchKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py
  role: implementation
created_at: '2026-11-10T03:38:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_prefetch
---


# npu_prefetch：权重 L2 预取与图依赖

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_prefetch(input, dependency, max_size, offset=0) -> None
```

对权重 input 发出 L2 Cache 预取请求，不修改权重、不返回 Tensor。其目标是减少后续访存等待，实际收益取决于并行和配置，不能推定预取后必然加速。

## 参数与组合限制

input 不能含空指针；max_size 必须大于 0，超过权重大小时按权重最大大小处理。offset 默认 0、必须非负且严格小于实现计算的权重总字节数。单算子模式 dependency 不生效、可为 None；图模式必须提供非 None 的 dependency 表示预取起点。input/dependency 不做数据处理，不以 dtype 或格式解释其数值。

## 验证与模型关联

检查预取是否位于真实消费者之前，并在相同负载下分别测量开关后的稳态时延、带宽和数值输出；收益不足时撤回预取，不能删除原有必要同步。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/common_utils.py#L147)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 全页复核与实际字节范围

本卡覆盖发布中文及main中英文全文，主线两例明确max_size/offset单位是字节：10000个FP32为40000字节，后半段用max_size=20000、offset=20000。英文参数一句对“超过”方向的翻译不覆盖实现：两固定包装要求offset严格小于tensor_size，再把max_size截到tensor_size-offset；offset等于末尾也拒绝，不只是“不大于”。

base格式用逻辑尺寸乘itemsize，私有格式用存储描述的storage_sizes计算大小，再以data_ptr+offset提交当前流异步CMO。包装并未处理dependency数值，也没在eager消费它；不能当数据copy、Host预取或自动建立全部消费者同步。

两固定TorchAir GE转换器都拒绝dependency=None并把它作为Cmo控制依赖；offset非0使用ge.Cmo，offset0另用无offset属性的兼容构造（注释针对7.5）。支持声明的F32样例不是只支持该dtype的完整表。main产品仍A2/A3、未列950，不从其他图或量化接口范围扩展。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 权重 L2 预取：torch_npu.npu_prefetch

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

提前将指定权重区间搬到 L2 Cache，收益取决于实际窗口和计算依赖。

### 输入、输出与行为

适合检查较大 MatMul 的权重搬运窗口；收益取决于并行方式、实际窗口和依赖关系，不能只由权重张量大小判定预取有效。

### 文档签名

```text
torch_npu.npu_prefetch(input, dependency, max_size, offset=0) -> None
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_prefetch.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prefetch.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prefetch.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_prefetch.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PrefetchKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PrefetchKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py)（implementation）
