---
type: API
title: asc_set_store_atomic_config_v1
description: 设置原子操作启用位与原子操作类型的值。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/atomic/scalar_atomic/asc_set_store_atomic_config_v1.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
source_headers:
- include/c_api/atomic/scalar_atomic.h
---

# asc_set_store_atomic_config_v1

## 功能说明

设置原子操作启用位与原子操作类型的值。

## 函数原型

```c
__aicore__ inline void asc_set_store_atomic_config_v1(uint16_t type, uint16_t op)
```

## 参数说明

**表1** 参数说明

| 参数名  | 输入/输出 | 描述 |
| :----- | :------- | :------- |
| type | 输入 | 原子操作启用位。<br>0：无原子操作。<br>1：开启原子操作，进行原子操作的数据类型为float。<br>2：开启原子操作，进行原子操作的数据类型为half。<br>3：开启原子操作，进行原子操作的数据类型为int16_t。<br>4：开启原子操作，进行原子操作的数据类型为int32_t。<br>5：开启原子操作，进行原子操作的数据类型为int8_t。<br>6：开启原子操作，进行原子操作的数据类型为bfloat16_t。<br>其余值无具体含义。 |
| op | 输入 | 原子操作类型。<br>0：求和操作。<br>其余值无具体含义。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

- 使用完成后，建议通过[asc_disable_dma_atomic](../datamove_atomic/asc_disable_dma_atomic.md)清空原子操作的状态，以免影响后续相关指令功能。
- 该指令执行前不会对GM的数据做清零操作，开发者需在需要时手动添加清零操作。

## 调用示例

```c
uint16_t type = 1;
uint16_t op = 0;
asc_set_store_atomic_config_v1(type, op);
```
