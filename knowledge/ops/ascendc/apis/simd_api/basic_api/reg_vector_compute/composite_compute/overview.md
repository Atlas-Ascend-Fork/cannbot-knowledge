---
type: API
title: 复合计算概述
description: 复合计算支持以下接口：
tags: [task.lookup, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/composite_compute/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 复合计算概述

复合计算支持以下接口：

该接口根据mask将srcReg0与srcReg1逐元素相减再求绝对值，计算结果写入dstReg。 计算公式如下：

本接口组包含 AbsSub, Axpy, ExpSub, MulDstAdd, MulAddDst。

本接口属于 Reg 矢量计算复合算术接口，组合多个基础运算。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
