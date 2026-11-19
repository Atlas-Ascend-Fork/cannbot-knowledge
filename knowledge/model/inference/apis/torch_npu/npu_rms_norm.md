---
type: API
title: RMSNorm 均方根归一化（torch_npu.npu_rms_norm）
description: torch_npu.npu_rms_norm：RMSNorm 均方根归一化。RmsNorm算子是大模型常用的归一化操作，相比LayerNorm算子，其去掉了减去均值的部分。 说明发布来源的 RMSNorm 计算、A2/A3 混合权重类型及 rstd，保留权重维数的文档歧义；另含 npu_rms_norm_backward 反向入口（aclops ACE 与 opapi aclnn 双路径）。
tags:
- task.lookup
- topic.compute.normalization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_rms_norm.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_rms_norm.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_rms_norm.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_rms_norm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RmsNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RmsNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RmsNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RmsNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RmsNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RmsNormBackwardKernelOpApi.cpp
  role: implementation
created_at: '2026-11-10T03:39:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_rms_norm
---


# npu_rms_norm：归一化尾维、权重类型与双输出

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_rms_norm(self, gamma, epsilon=1e-06) -> (Tensor, Tensor)
```

接口计算 x / sqrt(mean(x²)+epsilon) * gamma，不执行 LayerNorm 的减均值。返回归一化 Tensor 和 FP32 的 rstd；前者与 self 的 shape、dtype 相同，后者是反向可使用的均方根倒数，不能当作第二份归一化输出。epsilon 默认 1e-6。

## 参数与组合限制

- self 为 2–8 维 ND Tensor；gamma 的形状必须匹配 self 末尾参与归一化的维度。两者支持非连续和空 Tensor。
- A2/A3 支持 (self,gamma)=(FP16,FP16)、(BF16,BF16)、(FP32,FP32)，也允许 FP16/BF16 输入配 FP32 权重，不能推导任意混合类型均有效。
- 来源参数段将 gamma 写为 2–8 维，但同页示例使用一维权重；一维形态需结合所安装包声明与实现复核，不能静默把该文档差异消除。
- rstd 按两固定实现保留归一化尾轴为1，不能将文档简写的未归一化前缀直接作为完整shape；带残差的三输出接口另见 npu_add_rms_norm。

## 验证与模型关联

用显式 FP32 均方根归一化作参考，检查 epsilon、尾维、FP32 权重和两个返回值；验证前不要把替换带来的精度变化归因为融合收益。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L207)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 合并完整版本与实现复核

本节已并入 training 树重复入口的固定来源与限定结论；本卡是 npu_rms_norm 的 canonical 推理入口，历史跳转卡的 deprecated 状态只描述卡片生命周期，不表示 API 本身废弃。

### 公式和shape

npu_rms_norm(self,gamma,epsilon=1e-6)返回(y,rstd)，y=self*rsqrt(mean(self²)+epsilon)*gamma，不减均值，epsilon在平方根内。gamma描述归一化后缀，self.rank>=gamma.rank；文档一处写gamma为2..8维，自己的样例又用1D，不能机械拒绝该样例或承诺任意rank。

两固定ACL Op与OpAPI形状helper把rstd分配为未归一化前缀加归一化轴上的1，dtype FP32；例如self(B,S,H)、gamma(H)对应(B,S,1)，不是文档简写的(B,S)。消费者应保留这些维度以便广播，不用squeeze改变训练中间协议。y逻辑shape跟随self，文档列ND并允许不连续/空Tensor，实际Kernel组合仍需核验。

### 类型与产品条件

A2/A3文档给五种(self,gamma,y)配对：FP16/FP16/FP16、FP16/FP32/FP16、FP32/FP32/FP32、BF16/BF16/BF16、BF16/FP32/BF16，不从列表拼出任意混合dtype。旧Atlas训练/推理仅前述FP16/FP32两类同dtype配对，旧推理另有数据量>=32字节及Inf/NaN限制；旧称不自动映射950。

主线增加950产品及TorchAir图模式示例，发布没有该图模式证据，本卡平台保守保持A2/A3。主线“Inf输出Inf”文字只记录为该快照文档声明，不证明所有输入分布、返回rstd或旧版本数值行为相同。

## npu_rms_norm_backward 反向入口

前向合同见上文；反向 `npu_rms_norm_backward(dy, self, gamma, rstd)` 在 yaml custom 段两 pin 均 `acl_op+op_api all_version`，返回 `(dx, dgamma)`。aclops `RmsNormBackwardKernelNpu.cpp`（42 行，两 pin 去空白等价，读毕）为 ACE `RmsNormGrad` 命令路径。opapi `RmsNormBackwardKernelOpApi.cpp`（两 pin 去空白等价，`tr -d` 比对）：`DO_COMPATIBILITY(aclnnRmsNormGrad, acl_op::npu_rms_norm_backward)` 后，dx 按 `rms_norm_grad_npu_output_size(self,gamma)[0]` + `self.options()` + `ACL_FORMAT_ND` 分配，dgamma 按 `[1]` + **FP32** + ND 分配，`EXEC_NPU_CMD(aclnnRmsNormGrad, dy, self, rstd, gamma, dx, dgamma)`；GE 侧实参顺序差异见 torchair 层卡。消费面：torch_npu inductor 分解注册面针对 `npu.npu_rms_norm.default` 与 `npu_rms_norm_backward.default`（见 triton 分解卡）。两命令设备数值语义未核验。

## 已有 OpPlugin 7.3.0 文档与版本边界

### RMSNorm 均方根归一化：torch_npu.npu_rms_norm

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

RmsNorm算子是大模型常用的归一化操作，相比LayerNorm算子，其去掉了减去均值的部分。

### 文档签名

```text
torch_npu.npu_rms_norm(self, gamma, epsilon=1e-06) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_rms_norm.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_rms_norm.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_rms_norm.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_rms_norm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RmsNormKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RmsNormKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RmsNormKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [RmsNormBackwardKernelNpu.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RmsNormBackwardKernelNpu.cpp)（implementation）：全文 42 行；发布去空白等价。
- [RmsNormBackwardKernelOpApi.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormBackwardKernelOpApi.cpp)（implementation）：全文 37 行；发布仅行尾差异（去空白等价）。
