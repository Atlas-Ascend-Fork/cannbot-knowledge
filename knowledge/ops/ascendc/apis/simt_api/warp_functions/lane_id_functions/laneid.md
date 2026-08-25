---
type: API
title: Laneid
description: 获取线程在其所在Warp内的索引。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/lane_id_functions/laneid.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# laneid

获取线程在其所在Warp内的索引。

函数原型：int32_t laneid()

返回值：线程在其Warp内的索引，当前一个Warp中的线程数量为固定值32，故Lane ID的取值范围为[0,31]。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [LanemaskGe](lanemask_ge.md)（`related`）：Laneid 返回边界索引，LanemaskGe 直接把该索引编码成包含自身的后缀 bitmask；自定义掩码计算时二者互为原始索引与派生结果。
- [LanemaskGt](lanemask_gt.md)（`related`）：Laneid 返回当前线程的 Lane ID；LanemaskGt 正是以该 ID 为边界，将所有严格更大 Lane 的位设为 1，因此前者给出后者掩码边界的标量坐标。
- [LanemaskLe](lanemask_le.md)（`related`）：Laneid 与《LanemaskLe》的实质衔接是：Laneid 与 lane mask、shuffle/vote/reduce 和 warp 分支优化共同支撑 lane 级算法。
- [LanemaskLt](lanemask_lt.md)（`related`）：LanemaskLt 的位边界由当前线程 Lane ID 决定；Laneid 返回该索引，便于验证预期掩码和构造基于 lane 的控制流。
- [LanemaskEq](lanemask_eq.md)（`same_topic`）：Laneid 与《LanemaskEq》的实质衔接是：Laneid 与 lane mask、shuffle/vote/reduce 和 warp 分支优化共同支撑 lane 级算法。
<!-- cannbot:related:end -->
