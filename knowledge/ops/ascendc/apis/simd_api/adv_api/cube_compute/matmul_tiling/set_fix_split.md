---
type: API
title: SetFixSplit
description: 设置固定的baseM、baseN、baseK，单位为元素个数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetFixSplit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetFixSplit

设置固定的baseM、baseN、baseK，单位为元素个数。

参数：
- baseMIn（输入）：设置固定的baseM，默认值为-1，表示不设置固定baseM，由tiling函数进行计算。
- baseNIn（输入）：设置固定的baseN，默认值为-1，表示不设置固定baseN，由tiling函数进行计算。
- baseKIn（输入）：当前仅支持取值为-1，暂不支持设置其它值。

返回值：-1表示设置失败；0表示设置成功。

约束：
- baseM*baseN个输出元素所占的存储空间大小不能超过L0C Buffer大小，即baseM * baseN * sizeof(C_TYPE) <= L0CSize。
- baseM需要小于等于singleM按16个元素向上对齐后的值（如ceil(singleM/16)*16），baseN需要小于等于singleN以C0_size个元素向上对齐的值，其中singleM为单核内M轴长度，singleN为单核内N轴长度，half/bfloat16_t数据类型的C0_size为16，float数据类型的C0_size为8，int8_t数据类型的C0_size为32，int4b_t数据类型的C0_size为64。
