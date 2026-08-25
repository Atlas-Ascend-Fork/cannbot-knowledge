---
type: API
title: __hnex2_mask
description: 比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hnex2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hnex2_mask

功能：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __hnex2_mask(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否不相等的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。特殊值：任一分量含nan→0x0000；±0→0x0000；inf→0x0000；inf→0xFFFF；ASCRT_MAX_NORMAL_BF16→0x0000。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbnex2](_hbnex2.md)（`same_topic`）：mask 版本把逐 lane 比较结果编码为掩码，适合后续分支/选择而非直接 packed 布尔结果。
- [__heqx2_mask](_heqx2_mask.md)（`same_topic`）：__heqx2_mask 与《__hnex2_mask》的实质衔接是：这些 bfloat16x2 比较入口共享双 lane 掩码契约；ne、无序 eq、值返回 eq 与 isnan 用于区分 NaN 时的 ordered/unordered 结果。
- [__hneux2_mask](_hneux2_mask.md)（`same_topic`）：__hnex2_mask 与 __hneux2_mask 都返回两 lane 的不等掩码，差异集中在 NaN 时 ordered/unordered 的 0x0000/0xFFFF 结果。
- [__hnex2](_hnex2.md)（`same_topic`）：《__hnex2_mask》明确“比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0。”；它与《__hnex2》的“比较两个bfloat16x2_t类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hnex2_mask](../../half_type/half2_compare_functions/_hnex2_mask.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hnex2_mask正文说明“比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量不相等，则对应16位掩码为0xFFFF，否则为0x0”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
<!-- cannbot:related:end -->
