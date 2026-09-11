---
type: API
title: AutoContiguous
description: 配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。
  该接口仅在如下场景支持： - 通过单算子API执行的方式开发单算子调用应用。 - 间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.implementation.operator_registration
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/AutoContiguous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
---

# AutoContiguous<a name="ZH-CN_TOPIC_0000002114052037"></a>

## 功能说明<a name="zh-cn_topic_0000001711819448_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section36583473819"></a>

配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。

**该接口仅在如下场景支持：**

-   通过单算子API执行的方式开发单算子调用应用。
-   间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。

## 函数原型<a name="zh-cn_topic_0000001711819448_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section13230182415108"></a>

```
OpParamDef &AutoContiguous()
```

## 参数说明<a name="zh-cn_topic_0000001711819448_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section75395119104"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001711819448_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section25791320141317"></a>

OpParamDef算子定义，OpParamDef请参考[OpParamDef](index.md)。

## 约束说明<a name="zh-cn_topic_0000001711819448_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section19165124931511"></a>

当一个Input调用了AutoContigous\(\)后，其他未调用IgnoreContiguous\(\)的Input也会在框架中默认进行非连续tensor转连续tensor的处理。



<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：在 `Input("self")` 的 `OpParamDef` 链尾追加 `.AutoContiguous()` 后，非连续 view（transpose/slice）用例 ST 通过；配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。。运行手册用真实 transpose 和 slice 用例验证在 Input 定义追加 AutoContiguous 可修复非连续输入，API 卡解释其自动转换为连续 tensor 的框架行为，是规则在故障修复中的直接实例。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例（部分算子）

展示 10 / 111 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [StridedSliceAssignV2 A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/strided_slice_assign_v2.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [FatreluMul A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/fatrelu_mul.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [IncreFlashAttention A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/incre_flash_attention.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [AngleV2 A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/math/angle_v2.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [GeluMul A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/gelu_mul.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [SimThreadExponential A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/random/sim_thread_exponential.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [GeluMul 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/gelu_mul_950.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。
- [AlltoAllvGroupedMatMul A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/allto_allv_grouped_mat_mul.md)（`related`）：算子正文包含对 `AutoContiguous(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
