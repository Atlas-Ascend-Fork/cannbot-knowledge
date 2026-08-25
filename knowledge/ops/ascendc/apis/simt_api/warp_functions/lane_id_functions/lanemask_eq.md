---
type: API
title: LanemaskEq
description: 获取当前线程的32位掩码，在所属Warp中只有当前线程所在的Lane位被置1，其余为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/lane_id_functions/lanemask_eq.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# lanemask_eq

获取当前线程的一个32位掩码，在当前线程所属的Warp中，只有当前线程所在的Lane位被置为1，其余位为0。

如Lane ID为0的线程，调用本接口获取到32位掩码：0000 0000 0000 0000 0000 0000 0000 0001。

如Lane ID为31的线程，调用本接口获取到32位掩码：1000 0000 0000 0000 0000 0000 0000 0000。

函数原型：int32_t lanemask_eq()

返回值：返回一个32位整数的位掩码。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [LanemaskGt](lanemask_gt.md)（`related`）：LanemaskGt 与《LanemaskEq》的实质衔接是：Laneid 与四种相对 lane mask 共同定义严格大于、大小于等于和相等的位掩码边界。
- [Laneid](laneid.md)（`same_topic`）：Laneid 与《LanemaskEq》的实质衔接是：Laneid 与 lane mask、shuffle/vote/reduce 和 warp 分支优化共同支撑 lane 级算法。
- [LanemaskLt](lanemask_lt.md)（`same_topic`）：LanemaskEq 给出当前 lane 位，LanemaskLt 给出所有更小 lane 位；二者组合可构造前缀含当前 lane 的掩码。
<!-- cannbot:related:end -->
