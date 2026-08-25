---
type: API
title: Cann9ReleaseNotes
description: CANN 9.0.0首次面向Ascend 950PR/950DT提供试验性C语言扩展层SIMD API，覆盖数据搬运、标量操作、矩阵计算、同步控制等能力。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/Release_Notes/CANN_9_0_0.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Cann9ReleaseNotes

CANN 9.0.0首次面向Ascend 950PR/Ascend 950DT（3510架构）提供试验性C语言扩展层单指令多数据（Single Instruction Multiple Data，SIMD）API。基于指针编程，提供C完备编程能力，通过声明静态数组管理本地内存，由开发者自主管理同步与内存，适配C语言开发习惯，开放全部底层硬件能力，支撑精细化调优与极致性能实现。接口覆盖数据结构、数据搬运、标量操作、矩阵计算、同步控制、系统变量、缓存控制、原子操作、其他操作、Reg数据搬运和Reg矢量计算等能力。

涵盖以下类别：数据结构、数据搬运、标量操作、矩阵计算、同步控制、系统变量、缓存控制、原子操作、Reg数据搬运、Reg矢量计算。
