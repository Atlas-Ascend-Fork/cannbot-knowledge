---
type: API
title: HCCL Tiling侧接口
description: 提供HCCL集合通信的Host侧Tiling接口，包含TilingData结构体、GetTiling及通信类型、分组、队列等参数设置方法。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/HCCL_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Tiling侧接口

提供 HCCL 集合通信的 Host 侧 Tiling 接口，通过 TilingData 结构体承载通信切分参数。
核心方法 GetTiling 获取最终 Tiling 数据；SetOpType 设置通信算子类型，SetGroupName 设置通信组名，SetReduceType 设置归约操作类型，SetAlgConfig 配置算法参数。
另提供 SetCommBlockNum/SetQueueNum/SetCommEngine 控制通信引擎与队列分配，SetSkipLocalRankCopy/SetSkipBufferWindowCopy 跳过特定拷贝路径以优化性能，SetDebugMode 支持调试模式。
v1/v2 版本 TilingData 已废弃，新代码应使用当前版本结构体。
