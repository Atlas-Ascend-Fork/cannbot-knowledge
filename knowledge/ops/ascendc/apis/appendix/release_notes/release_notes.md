---
type: API
title: Release Notes
description: 汇总Ascend C API各CANN版本的发布说明，包含版本间接口变更和新特性介绍。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/Release_Notes/release_notes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Release Notes

汇总 Ascend C API 在各 CANN 版本的发布说明，记录版本间接口变更与新增特性。当前覆盖 CANN 9.0.0 与 CANN 9.1.0 两个版本。

CANN 9.1.0 面向 Ascend 950PR/Ascend 950DT（3510 架构）C API，新增矢量计算（bitsort、mrgsort4、transpose 等）、数据搬运（gm/ub/l1/l0 各级 buffer 间 copy 及格式转换）、标量原子操作、矩阵乘加（mmad 支持 FP8/HiF8/HF32 等混合精度）、同步控制（lock/unlock、核间信号、内存屏障）以及系统变量与缓存控制接口，并修复 9.0.0 中函数命名、类型声明和地址自更新签名问题。

<!-- cannbot:related:start -->
## 相关

- [废弃接口](../deprecated_interface.md)（`related`）：“废弃接口”定义：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。；“Release Notes”定义：汇总Ascend C API各CANN版本的发布说明，包含版本间接口变更和新特性介绍。。实质衔接：三者分别提供 C API 废弃清单、接口替换变更表和发布演进记录，可从旧接口定位推荐替代而不把清单与每个成员全连接。
- [C API](cann_9_1_0.md)（`same_topic`）：C API 与《Release Notes》的实质衔接是：9.1.0 C API 发布说明承接 9.0.0 的初始能力，并以总 Release Notes、废弃表和接口改名表说明新增入口及签名修复在既有代码中的迁移落点。
- [Cann9ReleaseNotes](cann_9_0_0.md)（`same_topic`）：发布说明总页给出 9.0.0 所处的版本序列与后续变更入口，能把本页的首发能力放回完整发布脉络。
<!-- cannbot:related:end -->
