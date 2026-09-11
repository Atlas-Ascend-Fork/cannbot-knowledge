---
type: API
title: asc_get_store_atomic_config
description: 获取原子操作启用位与原子操作类型的值，可用于校验asc_set_store_atomic_config_v1和asc_set_store_atomic_config_v2（废弃）设置的原子操作启用位和原子操作类型的值是否符合预期。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/atomic/scalar_atomic/asc_get_store_atomic_config.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/atomic/scalar_atomic.h
---

# asc_get_store_atomic_config

## 功能说明

获取原子操作启用位与原子操作类型的值，可用于校验[asc_set_store_atomic_config_v1](asc_set_store_atomic_config_v1.md)和[asc_set_store_atomic_config_v2（废弃）](../../deprecated_interface/asc_set_store_atomic_config_v2_deprecated.md)设置的原子操作启用位和原子操作类型的值是否符合预期。


**Ascend 950PR/Ascend 950DT产品上该接口已废弃。原子加操作可以直接使用[asc_atomic_add](asc_atomic_add.md)实现。无需再对原子操作启用位和原子操作类型的值进行配置和校验。**


## 函数原型

```cpp
__aicore__ inline void asc_get_store_atomic_config(asc_store_atomic_config& config)
```

## 参数说明

**表1** 参数说明

| 参数名  | 输入/输出 | 描述 |
| :----- | :------- | :------- |
| config | 输出 | 用于获取原子操作启用位和原子操作类型的值，详细说明请参考[asc_store_atomic_config](../../defs/union/asc_store_atomic_config.md)。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

需配合[asc_set_store_atomic_config_v1](asc_set_store_atomic_config_v1.md)和[asc_set_store_atomic_config_v2（废弃）](../../deprecated_interface/asc_set_store_atomic_config_v2_deprecated.md)接口使用，该接口用于设置原子操作启用位和原子操作类型的值。

## 调用示例

```cpp
uint16_t atomic_type = 1; // 开启原子操作,进行原子操作的数据类型为float，值为1
uint16_t atomic_op = 0; // 求和操作,值为0
asc_set_store_atomic_config_v1(atomic_type, atomic_op);
asc_store_atomic_config get_config;    // 用于获取原子操作启用位和原子操作类型的值
asc_get_store_atomic_config(get_config);    // get_config.atomic_type = 1; get_config.atomic_op = 0;
```
