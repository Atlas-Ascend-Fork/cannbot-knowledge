---
type: API
title: API流水类型汇总（附录）
description: 本节汇总介绍了一些主要的API的流水类型，以下内容针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/api_pipeline_type_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [agnostic]
---


# API流水类型汇总（附录）

本节汇总介绍了一些主要的API的流水类型，以下内容针对如下型号生效： - Ascend 950PR/Ascend 950DT - Atlas A3 训练系列产品/Atlas A3 推理系列产品 - Atlas A2 训练系列产品/Atlas A2 推理系列产品 针对Ascend 950PR/Ascend 950DT：单个VF是PIPE_V流水，用户不需要管理VF和VF之间的同步，VF内的不同的Reg矢量接口存在数据依赖时需要调用LocalMemBar进行同步。 表1 Memory矢量计算API流水类型汇总 | API类型 | API接口名称 | 执行核（AIC/AIV） | 流水类型

适用：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。
