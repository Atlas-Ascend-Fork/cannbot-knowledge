---
type: API
title: AscStorealign
description: 将矢量数据寄存器或掩码寄存器中的数据以32B对齐方式搬出到UB，支持连续、偏移、非连续等多种搬出模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscStorealign

将矢量数据寄存器或掩码寄存器中的数据以对齐的方式搬出到Unified Buffer（UB）。当源操作数为矢量数据寄存器时，单次搬出量为VL（256字节），支持配置掩码用于指示参与搬出的元素，掩码为1的元素写入目的地址，掩码为0的元素保留目的地址原数据。当源操作数为掩码寄存器时，单次搬出量为掩码寄存器长度（32字节），将掩码寄存器中的数据直接搬出，不支持配置掩码。搬运过程中数据格式与内容保持不变。本接口在Vector Function（__simd_vf__标记的函数）内使用，目的操作数为UB地址。 矢量数据寄存器搬出场景提供以下四种模式： 掩码寄存器搬出场景提供以下三种模式：
约束：非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；dst_align32b/dst起始地址需32字节对齐，否则会报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
