---
type: API
title: GroupBarrier使用说明
description: 当同一个CubeResGroupHandle中的两个AIV任务之间存在依赖关系时，可以使用GroupBarrier控制同步。假设一组AIV
  A做完任务x以后，另外一组AIV B才可以开始后续业务，称AIV A组为Arrive组，AIV B组为Wait组。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/GroupBarrier_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# GroupBarrier使用说明

当同一 CubeResGroupHandle 中的两组 AIV 任务存在依赖关系时，使用 GroupBarrier 控制同步。Arrive 组完成任务后调用 Arrive()，Wait 组调用 Wait() 阻塞等待，直到 Arrive 组全部完成。

使用流程：GetWorkspaceLen 获取所需 GM 空间 → 分配 workspace → 构造 GroupBarrier(workspace, arriveBlockDim, waitBlockDim) → Arrive 组 AIV 调用 Arrive() → Wait 组 AIV 调用 Wait()。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [GroupBarrier构造函数](group_barrier_constructor.md)（`related`）：“原型：`__aicore__ inline GroupBarrier(GM_ADDR workspace, uint8_t arriveBlockDim, uint8_t waitBlockDim)`。”给出对象构造所需 workspace 和两组 block 数；“使用流程：GetWorkspaceLen 获取所需 GM 空间 → 分配 workspace → 构造 GroupBarrier(workspace, arriveBlockDim, waitBlockDim) → Arrive 组 AIV 调用 Arrive() → Wait 组 AIV 调用 Wait()。”把构造参数放进完整同步调用顺序。
<!-- cannbot:related:end -->
