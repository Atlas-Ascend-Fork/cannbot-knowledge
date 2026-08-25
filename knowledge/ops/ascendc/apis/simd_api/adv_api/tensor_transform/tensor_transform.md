---
type: API
title: 张量变换
description: 张量变换接口导航页，涵盖Transpose、TransData、Pad、Broadcast等张量形状与排布变换接口。
tags: [task.lookup, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/tensor_transform.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 张量变换

Ascend C SIMD 高阶 API 张量变换导航页，提供张量形状与排布格式变换的 Kernel 侧接口。
涵盖 Transpose/TransData 转置与格式转换、Pad/UnPad 填充与裁剪、Broadcast 广播及 Fill 填充等操作。
Transpose、TransData、Pad、UnPad 均提供对应的 Tiling 接口或临时空间查询方法（GetTransDataMaxMinTmpSize、GetBroadCastMaxMinTmpSize）。
