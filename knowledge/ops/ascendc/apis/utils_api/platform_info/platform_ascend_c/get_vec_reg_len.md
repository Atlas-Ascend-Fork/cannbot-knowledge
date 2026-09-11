---
type: API
title: GetVecRegLen
description: 获取当前硬件平台芯片架构Vec计算单元位宽。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.programming_model.system_variable
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetVecRegLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/utils/tiling/platform/platform_ascendc.h
---

# GetVecRegLen<a name="ZH-CN_TOPIC_0000002556048947"></a>

## 功能说明<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section36583473819"></a>

获取当前硬件平台芯片架构Vec计算单元位宽。

## 函数原型<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section13230182415108"></a>

```
uint32_t GetVecRegLen(void) const
```

## 参数说明<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section189014013619"></a>

无

## 返回值<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section25791320141317"></a>

-   对于RegBase硬件平台芯片架构，返回当前硬件平台Vector计算单元位宽。
-   对于非RegBase硬件平台芯片架构，返回0 。

## 约束说明<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section320753512363"></a>

```
void GetLayerNormMaxMinTmpSize(...)
{
       platform_ascendc::PlatformAscendC* platform = platform_ascendc::PlatformAscendCManager::GetInstance();
        ...
        const uint32_t vecLenB32 = platform->GetVecRegLen() / LAYERNORM_SIZEOF_FLOAT;
        const uint32_t vecLenB16 = platform->GetVecRegLen() / LAYERNORM_SIZEOF_HALF;
        ...
}
```



<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [AddRmsNormDynamicQuant 950 Direct Invoke 算子知识](../../../../operators/direct/nn/norm/add_rms_norm_dynamic_quant_950.md)（`related`）：算子正文包含对 `GetVecRegLen(...)` 的直接调用；本卡提供该接口契约。
- [GroupNorm 950 Direct Invoke 算子知识](../../../../operators/direct/nn/norm/group_norm_950.md)（`related`）：算子正文包含对 `GetVecRegLen(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
