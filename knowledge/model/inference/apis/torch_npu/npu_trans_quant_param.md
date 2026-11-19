---
type: API
title: 量化 scale 编码（torch_npu.npu_trans_quant_param）
description: torch_npu.npu_trans_quant_param：将浮点 scale 编码成量化矩阵乘需要的整数位域表示，可同时编码 offset。 这里的输入是 float32 scale，编码后的位域用 int64 张量承载；输入浮点精度与输出承载类型是两项不同约束。 说明 FP32 scale 编码为 INT64/图内 UINT64，区分位编码与普通数值 cast 及分组形状。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_trans_quant_param.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_trans_quant_param.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_trans_quant_param.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_trans_quant_param.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TransQuantParamKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransQuantParamKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/transquantparam.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/transquantparam.py
  role: implementation
created_at: '2026-11-10T03:38:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_trans_quant_param
---


# npu_trans_quant_param：量化 scale 的位编码转换

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_trans_quant_param(scale, offset=None, round_mode=0) -> Tensor
```

把 FP32 scale 按量化接口要求编码到 64 位数据，并可编码 offset；它不是 Tensor.to(int64) 的数值转换。round_mode=0 表示高位截断填充，1 表示 R_INT。返回 INT64，图模式内部为 UINT64，应与对应量化消费者配套。

## 参数与组合限制

- scale/offset 为连续、非空 FP32 ND，一维或二维；无 offset 时输出 shape 同 scale。
- 普通 matmul 的 scale 支持 (1,)、(N,) 或 (1,N)。分组 matmul 只在 M 轴分组 group_type=0 时使用，支持 (G,)、(G,1)、(G,N)。
- 提供 offset 时仅用于普通 matmul；scale/offset/out 按 (1,)、(N,) 或 (1,N) 的规则配合，不能套用 G 轴分组。
- offset 会按来源编码规则取整并限制到 [-256,255]；结果是消费者解释的编码值，不应再次按普通浮点比例运算。

## 验证与模型关联

在固定消费者中比较直接浮点 scale 与编码 scale 的输出，区分 int64 存储值和实际数值系数；同时验证图模式的数据类型衔接。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py#L2568)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 位域修正、V3门槛与图Meta限制

发布公式实际把scale高19位保留在out的低32位，原说明“32位处”容易误读；主线中英文已明确bit0..31，第46位置1，offset的9位放37..45。round_mode=1是FP32到FP19的R_INT处理，不是先把scale按普通整数round再编码。主线新增950PR及950DT，并明确它可配量化和分组matmul；分组只M轴、无offset，不能任意扩到别的分组或产品。

两版C++输出Long/ND，scale一维且有offset时取两者长度较大者；静态缓存aclnnTransQuantParamV3是否存在，缺失时只接受round_mode=0走V2，round_mode=1明确报需升级CANN。不能从V2名字或公开参数存在推导R_INT已生效。

两版Meta仅接受一维或首维为1的二维scale，因此文档的(G,N)/(G,1)在G>1时不能据此直接承诺图支持；它还校验一维非标量offset长度、二维scale/offset同形。两个固定TorchAir Converter直接生成GE TransQuantParamV2并传round_mode，GE V2不是上述ACLNN V2。图内部UINT64应按消费者接线，不把页面“PyTorch不支持UINT64”一句扩展为所有现代PyTorch dtype的普遍事实。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 量化 scale 编码：torch_npu.npu_trans_quant_param

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将浮点 scale 编码成量化矩阵乘需要的整数位域表示，可同时编码 offset。

### 输入、输出与行为

这里的输入是 float32 scale，编码后的位域用 int64 张量承载；输入浮点精度与输出承载类型是两项不同约束。

### 文档签名

```text
torch_npu.npu_trans_quant_param(scale, offset=None, round_mode=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

这是位域编码，不是对 scale 做数值 `.to(int64)`。输出张量用 int64 承载；图模式还涉及 uint64 表示，应与 npu_quant_matmul 配套消费。带 offset 时不能照搬无 offset 的 grouped-matmul 使用条件。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_trans_quant_param.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_trans_quant_param.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_trans_quant_param.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_trans_quant_param.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TransQuantParamKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransQuantParamKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/transquantparam.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/transquantparam.py)（implementation）
