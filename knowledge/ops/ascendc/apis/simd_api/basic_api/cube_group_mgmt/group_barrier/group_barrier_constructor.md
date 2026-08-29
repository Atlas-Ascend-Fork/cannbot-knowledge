---
type: API
title: GroupBarrier构造函数
description: 创建GroupBarrier对象，通过设置构造函数参数，确定Arrive组的Block个数和Wait组的Block个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/GroupBarrier_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# GroupBarrier构造函数

创建 GroupBarrier 对象，确定 Arrive 组和 Wait 组的 Block 个数，用于同一 CubeResGroupHandle 内 AIV 间的依赖同步。

原型：`__aicore__ inline GroupBarrier(GM_ADDR workspace, uint8_t arriveBlockDim, uint8_t waitBlockDim)`。参数：workspace（GM 工作空间地址）、arriveBlockDim（Arrive 组 Block 数量）、waitBlockDim（Wait 组 Block 数量）。Arrive 组所有 Block 调用 Arrive 后，Wait 组 Block 才能从 Wait 返回。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [GroupBarrier使用说明](group_barrier_usage.md)（`related`）：“原型：`__aicore__ inline GroupBarrier(GM_ADDR workspace, uint8_t arriveBlockDim, uint8_t waitBlockDim)`。”给出对象构造所需 workspace 和两组 block 数；“使用流程：GetWorkspaceLen 获取所需 GM 空间 → 分配 workspace → 构造 GroupBarrier(workspace, arriveBlockDim, waitBlockDim) → Arrive 组 AIV 调用 Arrive() → Wait 组 AIV 调用 Wait()。”把构造参数放进完整同步调用顺序。
<!-- cannbot:related:end -->
