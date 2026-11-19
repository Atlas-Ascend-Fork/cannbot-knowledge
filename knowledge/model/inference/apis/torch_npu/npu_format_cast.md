---
type: API
title: 张量数据格式转换：返回新张量（torch_npu.npu_format_cast）
description: torch_npu.npu_format_cast：张量数据格式转换：返回新张量。修改`input`的数据格式为目标格式，修改后的新张量不会替换原有张量。 区分物理格式、dtype和逻辑维度，保留对象复用、原地重载及主线CANN参数边界。
tags:
- task.lookup
- topic.data_movement.layout_transform
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_format_cast.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/dsv4-flash-single-npu-moe-offload/scripts/tools/ascendc_mxfp4/mxfp4_fused_op.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast_.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:56Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_format_cast
---


# npu_format_cast：物理布局、别名与版本参数

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_format_cast(input, acl_format) -> Tensor
```

将 input 的 NPU 数据格式转换为 acl_format，返回 Tensor；是否复用原对象、改变存储描述或分配新存储取决于格式及重载，不能保证总是新 Tensor。acl_format 接受整数或 torch_npu.Format；如 ND=2、NHWC=1、FRACTAL_NZ=29。

## 参数与组合限制

- 格式编号不是 dtype，不能用本接口替代 dtype cast；逻辑 permute 与底层物理格式转换也需分别处理。
- 固定来源明确 NC1HWC0_C04=12 当前不支持；出现在 Format 枚举表不代表可直接使用。
- ND 及内部私有格式的适用算子需要核对实际消费者。动态分档对私有格式的限制不能因已执行格式转换而忽略。
- 产品表在此提交确认 A2/A3；不外推其他快照新增格式或新型号。

## 验证与模型关联

保留原 Tensor，分别检查转换前后 get_npu_format、逻辑 shape 和数值；在目标算子中验证格式能被消费，不把转换本身当作性能优化已成立。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/dsv4-flash-single-npu-moe-offload/scripts/tools/ascendc_mxfp4/mxfp4_fused_op.py#L281)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 逐版本扩展及别名修正

发布OpPlugin旧页只列input/acl_format；两固定TorchNPU注册实际上还有customize_dtype与input_dtype。不能由参数存在推断发布基线CANN9.0可用主线文档所需CANN>=9.1能力：发布非ACLNN-only路径会拒绝显式customize_dtype，主线还受SoC、CANN版本、符号可用、格式对、view等条件选择或回退。

同格式非原地调用可直接返回self；base到base可能只改原存储描述，不移动数据。原地int重载可能分配新存储再set_，不是零分配；非原地Tensor重载用dst选格式，原地Tensor-src重载则实际把src内容写到self的现有格式中。后者与文档“将input转换为src格式”存在实质差异，不能当通用格式模板方案。物理格式转换也不是逻辑permute。

## 主线参数、950及文档冲突

A2/A3主线customize_dtype=3表示C0=8；常规FP32/INT32的C0=16、INT8为32，不能把dtype编码和Format编号混为一谈。950非原地页列2..6维，原地页只列2/3维，不能互相补范围；其ND=2/NZ=29及实际C0格式矩阵需要按路径判断。主线实现把50..54等NZ变体规范化到29再消费参数，4字节输入还可能默认按FP16选择C0。

950矩阵包含FP4实际dtype与FP32、INT8/UINT8载体组合，部分INT32载体配FP16/BF16转换后实际返回格式50。它不是允许任意数值cast的证明。input_dtype示例给int8却与列出的实际dtype集合不一致，原地页“仅29”与含2的表格冲突，950原地示例又调用非原地入口；保留这些冲突，不拼成可执行配方。

MX scale行只在非原地页：uint8载体的实际FP8_E8M0、逻辑3/4D、各轴正数、最后两轴约束，物理存储形状为(...,ceil(N/16),KScale,16,2)，逻辑shape保持；仅eager。不能移植到原地或旧版。950 NZ后限制contiguous/pad/view/slice，尾两维有1时限制transpose，FP16/BF16特定k=1组合不支持，不连续NZ→ND也不支持；不是所有NZ张量可自由进入普通视图组合。

allow_internal_format文档注释为False，与另一个_MM_BMM_ND_ENABLE变量的True不是同一开关，不构造默认值冲突。主线get_npu_format还显式拒绝Fake/Meta存储；Fake推导不能替代真实存储查询。本卡仍保守仅标A2/A3，950上述信息按主线限定阅读，C++同名重载与产品支持另见[框架格式接口](cpp_npu_format_cast.md)。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 张量数据格式转换：返回新张量：torch_npu.npu_format_cast

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

修改`input`的数据格式为目标格式，修改后的新张量不会替换原有张量。

### 文档签名

```text
torch_npu.npu_format_cast(input, acl_format) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_format_cast.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast_.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastHelper.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastHelper.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）
