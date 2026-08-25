---
type: API
title: AscGetSmmuTagVersion
description: 获取SMMU版本信息。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_smmu_tag_version.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetSmmuTagVersion

获取SMMU（System Memory Management Unit）版本信息。
函数原型：int64_t asc_get_smmu_tag_version()
返回值：SMMU版本信息。各bit含义如下：
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [系统变量](system_variables.md)（`same_topic`）：AscGetSmmuTagVersion 与《系统变量》的实质衔接是：AscGetSmmuTagVersion 属于系统变量读取；候选中只有系统变量总览提供该硬件状态的使用域，其他共享 Get 前缀不足以构成关系。
<!-- cannbot:related:end -->
