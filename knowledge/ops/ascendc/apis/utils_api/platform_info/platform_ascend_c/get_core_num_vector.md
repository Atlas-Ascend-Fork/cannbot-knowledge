---
type: API
title: GetCoreNumVector
description: 用于获取硬件平台独立的Vector Core的核数。 该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNumVector.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCoreNumVector

## 功能说明
用于获取硬件平台独立的Vector Core的核数。
该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。
## 函数原型
## 参数说明
无
## 返回值说明
返回硬件平台Vector Core的核数。
## 约束说明
Atlas 训练系列产品，不支持该接口，返回0
Atlas 推理系列产品，支持该接口，返回硬件平台Vector Core的核数
Atlas A2 训练系列产品/Atlas A2 推理系列产品不支持该接口，返回0
Atlas A3 训练系列产品/Atlas A3 推理系列产品不支持该接口，返回0
Atlas 200I/500 A2 推理产品不支持该接口，返回0
Ascend 950PR/Ascend 950DT不支持该接口，返回0
