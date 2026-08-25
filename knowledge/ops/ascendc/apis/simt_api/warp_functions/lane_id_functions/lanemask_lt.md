---
type: API
title: LanemaskLt
description: 获取当前线程的32位掩码，在所属Warp中将Lane ID严格小于当前线程的线程对应位设为1，其余位为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/lane_id_functions/lanemask_lt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# lanemask_lt

获取当前线程的一个32位掩码，在当前线程所属的Warp中，将“Lane ID严格小于当前线程”的线程的对应位设为1，其余位为0。

如Lane ID为0的线程，调用本接口获取到32位掩码：0000 0000 0000 0000 0000 0000 0000 0000。

如Lane ID为31的线程，调用本接口获取到32位掩码：0111 1111 1111 1111 1111 1111 1111 1111。

函数原型：int32_t lanemask_lt()

返回值：返回一个32位整数的位掩码。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [Laneid](laneid.md)（`related`）：LanemaskLt 的位边界由当前线程 Lane ID 决定；Laneid 返回该索引，便于验证预期掩码和构造基于 lane 的控制流。
- [LanemaskGe](lanemask_ge.md)（`related`）：LanemaskLt 选择当前 lane 之前的线程，LanemaskGe 选择当前及之后线程，二者形成不重叠的前后区间。
- [LanemaskGt](lanemask_gt.md)（`related`）：LanemaskGt 生成严格大于当前 Lane 的后缀掩码，与 LanemaskLt 的前缀掩码互补。
- [LanemaskEq](lanemask_eq.md)（`same_topic`）：LanemaskEq 给出当前 lane 位，LanemaskLt 给出所有更小 lane 位；二者组合可构造前缀含当前 lane 的掩码。
- [LanemaskLe](lanemask_le.md)（`same_topic`）：LanemaskLe 与 LanemaskLt 的唯一区别是是否把当前 Lane 自身置 1，适合明确前缀扫描是否包含本线程。
<!-- cannbot:related:end -->
