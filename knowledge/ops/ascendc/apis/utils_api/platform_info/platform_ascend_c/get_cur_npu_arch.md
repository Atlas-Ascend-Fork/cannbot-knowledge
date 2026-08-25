---
type: API
title: GetCurNpuArch
description: 获取当前硬件平台芯片架构版本号。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCurNpuArch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCurNpuArch

## 功能说明
获取当前硬件平台芯片架构版本号。
## 函数原型
## 参数说明
无
## 返回值
当前硬件平台架构号的枚举类。该枚举类和AI处理器型号的对应关系请通过CANN软件安装后文件存储路径下include/platform/soc_spec.h头文件获取。
- Ascend 950PR/Ascend 950DT：DAV_3510
- Atlas A3 训练系列产品/Atlas A3 推理系列产品：DAV_2201
- Atlas A2 训练系列产品/Atlas A2 推理系列产品：DAV_2201
- Atlas 200I/500 A2 推理产品：DAV_3002
- Atlas 推理系列产品AI Core：DAV_2002
- Atlas 推理系列产品Vector Core：DAV_2002
- Atlas 训练系列产品：DAV_1001
## 约束说明
无
