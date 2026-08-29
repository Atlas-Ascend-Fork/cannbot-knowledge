---
type: API
title: HCCL Kernel侧接口
description: 提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/HCCL_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Kernel侧接口

提供 Ascend C HCCL 集合通信的 Kernel 侧接口，通过模板参数配置通信数据类型与编排模式。
核心通信算子包括 AllReduce、AllGather、ReduceScatter、AlltoAll、AlltoAllV，以及 AlltoAllvWrite 和 BatchWrite 等数据写入接口。
执行流程为 InitV2 初始化并 SetCcTilingV2 设置 Tiling 后，调用 Commit 提交通信任务，再通过 Wait/Query/Iterate 管理执行状态，最终 Finalize 释放资源。
Init/SetCcTiling 为废弃接口，新代码应使用 V2 版本。
