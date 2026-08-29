---
type: API
title: Reg矢量计算概述
description: Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算概述

Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。

在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。

本接口组包含 asc_vf_call, RegTensor, MaskReg, LoadAlign, StoreAlign。

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。

约束：asc_vf_call启动SIMD VF子任务时，子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，且入口函数必须使用__simd_vf__修饰宏。；asc_vf_call启动SIMD VF子任务时，入参仅支持Ascend C的内置数据类型（half、int32_t、uint32_t、float等）及其组成的指针、数组、结构体类型，且指针类型必须指向UB内存。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
