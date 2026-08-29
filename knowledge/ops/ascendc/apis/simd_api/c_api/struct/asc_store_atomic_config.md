---
type: API
title: AscStoreAtomicConfig
description: 原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/asc_store_atomic_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscStoreAtomicConfig

asc_store_atomic_config参数包含原子操作启用位与原子操作类型，用于asc_get_store_atomic_config接口使用。

字段：atomic_type：原子操作启用位，默认值：0。 0：无原子操作。 1：开启原子操作，进行原子操作的数据类型为float。 2：开启原子操作，进行原子操作的数据类型为half。 3：开启原子操作，进行原子操作的数据类型为int16_t。 4：开启原子操作，进行原子操作的数据类型为int32_t。 5：开启原子操作，进行原子操作的数据类型为int8_t。 6：开启原子操作，进行原子操作的数据类型为bfloat16_t。 其余值无具体含义。；atomic_op：原子操作类型，默认值：0。 0：求和操作。 其余值无具体含义。

<!-- cannbot:related:start -->
## 相关

- [AscGetStoreAtomicConfig](../simd_atomic/asc_get_store_atomic_config.md)（`related`）：asc_store_atomic_config参数包含原子操作启用位与原子操作类型，用于asc_get_store_atomic_config接口使用；获取原子操作启用位与原子操作类型的值，可用于校验asc_set_store_atomic_config_v1和asc_set_store_atomic_config_v2（废弃）设置的原子操作启用位和原子操作类型的值是否符合预期。前者定义后者返回的配置结构，后者说明读取与校验用途，构成类型与消费者的直接接口契约。
<!-- cannbot:related:end -->
