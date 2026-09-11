---
type: API
title: GetLibApiWorkSpaceSize
description: 获取AscendC API需要的workspace空间大小。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.programming_model.system_variable
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetLibApiWorkSpaceSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/utils/tiling/platform/platform_ascendc.h
---

# GetLibApiWorkSpaceSize<a name="ZH-CN_TOPIC_0000002114097981"></a>

## 功能说明<a name="zh-cn_topic_0000001663835704_zh-cn_topic_0000001391767420_section36583473819"></a>

获取AscendC API需要的workspace空间大小。

## 函数原型<a name="zh-cn_topic_0000001663835704_zh-cn_topic_0000001391767420_section13230182415108"></a>

```
uint32_t GetLibApiWorkSpaceSize(void) const
```

## 参数说明<a name="zh-cn_topic_0000001663835704_zh-cn_topic_0000001391767420_section189014013619"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001663835704_zh-cn_topic_0000001391767420_section25791320141317"></a>

返回uint32\_t数据类型的结果，该结果代表当前系统workspace的大小，单位为字节。接口正常返回workspace大小，当返回`std::numeric_limits<uint32_t>::max()`（即`UINT32_MAX`）则接口异常。

## 约束说明<a name="zh-cn_topic_0000001663835704_zh-cn_topic_0000001391767420_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001663835704_zh-cn_topic_0000001391767420_section320753512363"></a>

```
// 用户自定义的tiling函数
static ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    AddApiTiling tiling;
    ...
    size_t usrSize = 256; // 设置用户需要使用的workspace大小。
    // 如需要使用系统workspace需要调用GetLibApiWorkSpaceSize获取系统workspace的大小。
    auto ascendcPlatform = platform_ascendc:: PlatformAscendC(context->GetPlatformInfo());
    uint32_t sysWorkspaceSize = ascendcPlatform.GetLibApiWorkSpaceSize();
    if (sysWorkspaceSize == std::numeric_limits<uint32_t>::max()) {
        return ge::GRAPH_FAILED;
    }
    size_t *currentWorkspace = context->GetWorkspaceSizes(1); // 通过框架获取workspace的指针，GetWorkspaceSizes入参为所需workspace的块数。当前限制使用一块。
    currentWorkspace[0] = usrSize + sysWorkspaceSize; // 设置总的workspace的数值大小，总的workspace空间由框架来申请并管理。
    ...
}
```


<!-- cannbot:related:start -->
## 相关

- [GetSysWorkSpacePtr](../../../simd_api/basic_api/resource_management/workspace/get_sys_work_space_ptr.md)（`related`）：获取AscendC API需要的workspace空间大小。；获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。。GetLibApiWorkSpaceSize 给出 Host 侧预留容量，GetSysWorkSpacePtr 明确该容量由 Host 申请后在 Kernel 侧取得系统 workspace 指针，二者是同一 workspace 生命周期的容量端与地址端。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例（部分算子）

展示 10 / 82 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Im2colBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [ChunkCat A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/chunk_cat.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [Celu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/celu_950.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [FusedCausalConv1d 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/fused_causal_conv1d_950.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [RoiPoolingWithArgMax 950 ACLNN 算子知识](../../../../operators/aclnn/cv/objdetect/roi_pooling_with_arg_max_950.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [ChunkCat 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/chunk_cat_950.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [NsaCompress A2 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/nsa_compress.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [CircularPad3d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_3d.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。
- [HardswishBackwardV2 A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/hardswish_backward_v2.md)（`related`）：算子正文包含对 `GetLibApiWorkSpaceSize(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
