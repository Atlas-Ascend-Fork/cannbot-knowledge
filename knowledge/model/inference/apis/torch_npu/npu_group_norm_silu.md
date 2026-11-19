---
type: API
title: GroupNorm 与 SiLU 融合（torch_npu.npu_group_norm_silu）
description: torch_npu.npu_group_norm_silu：融合 GroupNorm 与 SiLU，同时产生归一化统计量及激活结果。 组归一化除激活结果外还提供统计量：文档列出 out、meanOut、rstdOut 以及 SiLU 输出，其中 rstdOut 为标准差的倒数；消费端必须核对返回项顺序。 说明混合精度仿射、统计输出 dtype 及图模式仅列950，不套用 Swish 接口的参数规则。
tags:
- task.lookup
- topic.compute.normalization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_group_norm_silu.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_silu.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputDtype.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_silu.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_group_norm_silu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputDtype.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T03:38:43Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- '950'
aliases:
- torch_npu.npu_group_norm_silu
- GroupNorm SiLU
---


# npu_group_norm_silu：通道分组、可选仿射与三输出

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口产品页及同提交 Schema，仅描述下列产品和参数路径，不回推到发布快照。文档支持、来源配套和设备验证分别核对。

## 接口

```text
npu_group_norm_silu(input, weight, bias, group, eps=1e-5)
    -> (out, meanOut, rstdOut)
```

先GroupNorm再SiLU。input为ND、2..8维，所有维>0，第1轴C能被正整数group整除，支持非连续；A2/950为FP16/BF16/FP32。weight/bias可传None，Schema没有默认值，调用仍须提供相应位置；两者为空时无仿射，相当于gamma=1/beta=0。非空时为一维C元素，二者dtype相同且精度不能低于input，可以与input不同。eps必须>0。

out同input形状；meanOut/rstdOut形状(N,group)。同dtype仿射的共同子集下，统计dtype同input；混合精度时见下方文档/包装/Meta差异，既不能一律input.dtype，也不能按RMSNorm固定FP32处理。训练/推理均列支持，但图模式示例明确仅950；本卡A2范围不表示A2图模式也有此承诺。产品页未列A3，不能借相邻Swish接口扩大。

- [独立 Swish 缩放与反向限制](../../../training/apis/torch_npu/npu_group_norm_swish.md)


## 核验

按同一计算顺序、激活模式和量化参数建立参考，检查输出数量、dtype、shape与别名；训练还需验证反向及保存的中间值。再比较正常负载的稳态时间和内存。本次未执行算子、图编译或设备性能测试。

## 混合精度统计量的三份证据

产品页把统计输出dtype描述为input；但同提交gen_opapi对mean/rstd调用npu_group_norm_silu_dst_type。该helper在950及以后将input与已存在weight（否则bias）做result_type提升，在较早产品只取input。因此950低精度input配FP32仿射时，Eager包装的统计量应按提升类型分配，而非一律input.dtype。这是静态分配逻辑，不是本次设备结果。

Meta在weight/bias都非None时各按它们的dtype给出统计量，任一为None时又都回到input.dtype。故低精度input配高精度仿射、尤其A2路径或仅提供一项仿射时，Meta与Eager分配可能不一致。稳定使用结论先限定同dtype仿射或同时None的共同子集；混合精度图组合保留待实际核验，不能仅根据参数表和Meta输出承诺可用。

## 发布与双语轴说明的复核

发布中文已列A2和旧Atlas推理，主线中英文增加950PR及950DT；两版本均未列A3，主线图示例只承诺950PR/DT。英文将中文“第1维”译成first dimension，结合NCHW示例N=24、C=320、group=32及仿射长度320，应按通道C即索引1理解，不将N=24要求能被32整除。

两固定声明都将weight/bias标Optional但没有默认值；允许显式None与调用省略是两回事。发布实现已有950 dtype helper分支不代表发布公开页已支持950。两版Meta和helper的混合精度统计差异如上保留，完整文档的同input dtype叙述仍不能覆盖实际分配分支。

## 已有 OpPlugin 7.3.0 文档与版本边界

### GroupNorm 与 SiLU 融合：torch_npu.npu_group_norm_silu

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

融合 GroupNorm 与 SiLU，同时产生归一化统计量及激活结果。

### 输入、输出与行为

组归一化除激活结果外还提供统计量：文档列出 out、meanOut、rstdOut 以及 SiLU 输出，其中 rstdOut 为标准差的倒数；消费端必须核对返回项顺序。

### 文档签名

```text
torch_npu.npu_group_norm_silu(input, weight, bias, group, eps=0.00001) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

该文档只明确列出 A2；融合操作的统计输出及 epsilon 等字段需与被替换的 GroupNorm+SiLU 保持一致。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_group_norm_silu.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_silu.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputDtype.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_silu.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_group_norm_silu.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputDtype.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
