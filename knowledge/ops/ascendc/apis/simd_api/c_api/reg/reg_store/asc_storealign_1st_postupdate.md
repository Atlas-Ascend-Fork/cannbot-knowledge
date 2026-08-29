---
type: API
title: AscStorealign1stPostupdate
description: 从矢量数据寄存器搬出第一个元素到UB，忽略mask，接口调用后自动更新目的操作数地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_1st_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStorealign1stPostupdate

从矢量数据寄存器搬出第一个元素到UB的接口，忽略mask，向dst_align32b中搬运src第一个元素，接口调用后自动更新目的操作数地址。支持数据类型为b8、b16、b32。
函数原型：void asc_storealign_1st_postupdate(__ubuf__ int8_t*& dst_align32b, vector_int8_t src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStorealign1st](asc_storealign_1st.md)（`related`）：“从矢量数据寄存器搬出第一个元素到UB的接口，忽略mask”给出焦点端事实；“接口调用后自动更新目的操作数地址。”给出候选端事实。基础接口定义首元素对齐存储，postupdate 变体在相同搬运语义上增加目的地址自动更新；二者直接支持调用变体选择。
<!-- cannbot:related:end -->
