---
type: API
title: Int8 Channel Merge
description: Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/int8_channel_merge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Int8 Channel Merge

Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置。

Int8 Channel Merge：当目标数据类型为`int8_t`或`uint8_t`时，NZ输出自动启用该特性。硬件会将分形矩阵从16×16扩展为16×32。若输出通道数N是16的偶数倍，则N方向上每两个相邻的16×16分形矩阵合并为一个16×32分形矩阵。若N是16的奇数倍，则前N - 16个通道参与合并，最后16个通道保持16×16分形矩阵不变。针对Ascend 950PR/Ascend 950DT，`hifloat8_t`、`fp8_e4m3fn_t`类型也支持该特性。

## 使用示例

Int8 Channel Merge：当目标数据类型为`int8_t`，M为32，N为48时，硬件会将N方向上前两个16×16分形矩阵合并成一个16×32分形矩阵，剩余的一个16×16分形矩阵保持不变并输出。

**图1**  Int8 Channel Merge示意图

## 约束说明

- Channel Merge为硬件自动使能，不能通过参数配置。
- Int8 Channel Merge在NZ输出且目的类型为`int8_t`或`uint8_t`时自动启用。Ascend 950PR/Ascend 950DT上`hifloat8_t`、`fp8_e4m3fn_t` NZ输出也支持该特性。

<!-- cannbot:related:start -->
## 相关

- [Int8 Channel Merge](../../cube_compute/cube_store_key_features/int8_channel_merge.md)（`same_topic`）：硬件会将分形矩阵从16×16扩展为16×32；NZ输出时该特性自动启用。两卡描述同一 NZ 搬出时的 Int8 Channel Merge 硬件行为，但分别处于 Tensor API 与基础 Cube API 编程入口；对照可确认两种入口的自动启用规则一致。
<!-- cannbot:related:end -->
