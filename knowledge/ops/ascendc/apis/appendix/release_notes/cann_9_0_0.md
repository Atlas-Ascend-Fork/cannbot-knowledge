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

<!-- cannbot:related:start -->
## 相关

- [PadMode/单参 EnQue 在 CANN9.0.0 编译失败](../../../runbooks/compilation/padmode_enque_cann9_0_0.md)（`exemplifies`）：该构建案例把 9.0.0 头文件缺失的 PadMode/EnQue 形态落实为可复现版本错配，是发布能力边界的具体实例。
- [aclrtMemsetD32Async 在 CANN 9.x 被移除](../../../runbooks/compilation/aclrtmemsetd32async_cann_9_x.md)（`exemplifies`）：该案例记录 CANN 9.x 移除 aclrtMemsetD32Async 后的编译失败与替代接口，补足版本升级时的实际兼容性判断。
- [C API](cann_9_1_0.md)（`same_topic`）：C API 与《Cann9ReleaseNotes》的实质衔接是：9.1.0 C API 发布说明承接 9.0.0 的初始能力，并以总 Release Notes、废弃表和接口改名表说明新增入口及签名修复在既有代码中的迁移落点。
- [Release Notes](release_notes.md)（`same_topic`）：发布说明总页给出 9.0.0 所处的版本序列与后续变更入口，能把本页的首发能力放回完整发布脉络。
<!-- cannbot:related:end -->
