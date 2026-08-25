---
type: API
title: AscCopyL0c2L1
description: 将数据从L0C搬运到L1 Buffer的接口，包含不同架构版本的具体实现。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l0c2l1/asc_copy_l0c2l1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AscCopyL0c2L1

将数据从L0C搬运到L1 Buffer的接口，包含不同架构版本的具体实现。

矩阵计算完成后，对结果进行量化处理，之后将处理结果搬运到L1 Buffer中。量化模式共分为9种，分别为： - NoQuant：不开启量化功能。 - DEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。 - F322BF16：float量化成bfloat16_t。量化结果不支持INF_NAN模式。 - F322F16：float量化成half。量化结果不支持INF_NAN模式。 - QF322B8_PRE：float量化成uint8_t/int8_t。scalar量化。 - REQ8：int32_t量化成uint8_t/int8_t。scalar量化。 - VDEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。 - VQF322B8_PRE：float量化成uint8_t/int8_t。矢量量化。 - VREQ8：int32_t量化成ui

本接口组包含 asc_copy_l0c2l1_arch_2201, asc_copy_l0c2l1_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_l0c2l1指令，且asc_copy_l0c2l1指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_l0c2l1指令的串行化，防止出现异常数据。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
