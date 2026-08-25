---
type: API
title: AscCopyUb2GmAlign
description: 提供数据非对齐搬运功能，将数据从UB搬运到GM，支持8位/16位/32位数据类型搬运。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscCopyUb2GmAlign

将数据从Unified Buffer (UB)搬运到Global Memory (GM)，支持8位/16位/32位数据类型搬运。 本接口支持以下两种数据搬运方式，均不支持设置填充值： 若搬运数据长度非32字节对齐，搬出时会在读取UB数据时自动补充dummy假数据，将搬运数据补齐至32字节对齐。写入GM时会丢弃补充的dummy假数据。
函数原型：void asc_copy_ub2gm_align(__gm__ int8_t* dst, __ubuf__ int8_t* src, uint32_t size)
约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；当n_burst、len_burst中任意一个值为0时，该接口被视为NOP（空操作）。；当size值为0时，该接口被视为NOP（空操作）。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
