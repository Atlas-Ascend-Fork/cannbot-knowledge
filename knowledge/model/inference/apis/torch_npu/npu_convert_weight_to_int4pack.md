---
type: API
title: INT4 权重交叠打包（torch_npu.npu_convert_weight_to_int4pack）
description: torch_npu.npu_convert_weight_to_int4pack：INT4 权重交叠打包。将`int32`类型的输入`tensor`打包为`int4`存放，每8个`int4`数据通过一个`int32`数据承载，并进行交叠排放。 说明 INT32 承载 INT4 的离线权重打包、对齐和预留 inner_k_tiles 参数。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_convert_weight_to_int4pack.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_convert_weight_to_int4pack.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/pangu_7b/utils/convert_model.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_convert_weight_to_int4pack.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_convert_weight_to_int4pack.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvertWeightToINT4PackKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvertWeightToINT4PackKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_convert_weight_to_int4pack
---


# npu_convert_weight_to_int4pack：权重数值范围与八值打包

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_convert_weight_to_int4pack(weight,inner_k_tiles=0) -> Tensor
```

将每 8 个 INT4 权重值交叠打包到一个 INT32 元素，返回 INT32 Tensor。它接收已经量化的整数权重，不负责从浮点权重估计量化 scale 或 offset。

## 参数与组合限制

weight 必须是二维、连续 INT32，值在 [-8,7] 内，输入格式支持 ND/FRACTAL_NZ。形状为 (K,N) 或 (N,K)，最后一维需 8 对齐；输出相应为 (K,N/8) 或 (N,K/8)，格式 ND。inner_k_tiles 默认 0，在该版本是未使用的预留参数，不能作为可调 tiling 优化项。来源支持 A2/A3 推理和图模式。

## 验证与模型关联

解包后逐值比较原始整数权重；核对转置发生在打包前还是打包后及下游 antiquant 参数布局，不能只检查输出 dtype。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/pangu_7b/utils/convert_model.py#L237)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线950的FP4与物理格式

发布公开页仅A2/A3、二维连续INT32与[-8,7]；主线中英文新增950PR及950DT，允许二维/三维INT32或FP32。FP32在此承载已按FP4 E2M1表达的值，范围[-6,6]，打包后仍用FP32容器，每个元素存8个四位编码；不是普通FP32数值张量可直接参与浮点运算。主线说明PyTorch2.7及以前的例子用ml_dtypes>=0.5.0先得到FP4表示，2.8起另有原生FP4类型；本次没有安装或导入它们。

两固定实现其实都已有950分支，但不能据此补出发布公开支持。INT4包装直接取每个值低4位，局部参数检查没有逐值检查[-8,7]；FP4通过位掩码与编码表转换，未命中表时返回零编码，不是校准或对任意实数保证最近值舍入的量化器。应先准备符合消费者合同的量化值，再打包。

发布页将输出写ND，而两版的NZ输入路径实际构造NZ存储并更新描述；主线称格式同weight也只能按格式家族理解，950的NZ_C0_16/32会对应到更小C0打包格式。逻辑尾维缩8倍与物理存储块是不同信息，不能靠普通view修改这些描述来替代正确打包。

## 这是含Host处理的准备过程

两固定实现均将数据搬到Host，用CPU向量完成八值打包再回Device；NZ路径还显式同步当前流并进行Device/Host复制。inner_k_tiles未使用，不能当tiling旋钮。公开图模式样例都在编译forward外完成打包，再把结果交模型，不证明能把这段Host处理直接放进任意捕获区，也不承诺逐token调用开销可忽略。

## 已有 OpPlugin 7.3.0 文档与版本边界

### INT4 权重交叠打包：torch_npu.npu_convert_weight_to_int4pack

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将`int32`类型的输入`tensor`打包为`int4`存放，每8个`int4`数据通过一个`int32`数据承载，并进行交叠排放。

### 文档签名

```text
torch_npu.npu_convert_weight_to_int4pack(weight,inner_k_tiles=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_convert_weight_to_int4pack.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_convert_weight_to_int4pack.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_convert_weight_to_int4pack.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_convert_weight_to_int4pack.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvertWeightToINT4PackKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvertWeightToINT4PackKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
