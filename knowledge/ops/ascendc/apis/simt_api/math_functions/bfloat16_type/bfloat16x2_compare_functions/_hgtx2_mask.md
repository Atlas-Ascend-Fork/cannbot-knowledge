---
type: API
title: __hgtx2_mask
description: 比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hgtx2_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgtx2_mask

功能：比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。

函数原型：unsigned int __hgtx2_mask(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于第二个数的结果：满足时对应16位掩码结果为0xFFFF，不满足时对应16位掩码结果为0x0。特殊值：±0→0x0000；任一分量含nan→0x0000；inf→0xFFFF；inf→0xFFFF；-inf→0x0000；-inf→0x0000；ASCRT_MAX_NORMAL_BF16→0xFFFF。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgex2_mask](_hgex2_mask.md)（`related`）：大于等于包含等值边界，条件语义不同。
- [__hltx2_mask](_hltx2_mask.md)（`related`）：小于是相反方向谓词。
- [__hbgtx2](_hbgtx2.md)（`same_topic`）：__hgtx2_mask说明比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgtx2_mask》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hgtx2](_hgtx2.md)（`same_topic`）：两卡执行相同 ordered 大于比较；focal 返回 bfloat16x2 的 1.0/0.0，mask 版本返回两个 FFFF/0000 半字，决定后续数值计算还是位选择。
- [__hgtx2_mask](../../half_type/half2_compare_functions/_hgtx2_mask.md)（`same_topic`）：half2 版本执行同一逐 lane 大于 mask，源精度不同。
<!-- cannbot:related:end -->
