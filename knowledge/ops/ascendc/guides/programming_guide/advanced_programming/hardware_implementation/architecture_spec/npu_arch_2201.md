---
type: Guide
title: NPU架构版本2201
description: 本节介绍__NPU_ARCH__版本号为2201的硬件架构和其功能说明。对应的产品型号为：
tags: [task.lookup, topic.programming_model.execution_unit]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# NPU架构版本2201

本节介绍__NPU_ARCH__版本号为2201的硬件架构和其功能说明。对应的产品型号为：
-   Atlas A3 训练系列产品/Atlas A3 推理系列产品
-   Atlas A2 训练系列产品/Atlas A2 推理系列产品
## 硬件架构图
如下图所示，本架构中AI Core分为AIC和AIV两个独立的核，分别用于矩阵计算和向量计算。AIC核与AIV核配比为1：2。每个核都有自己的Scalar单元，能独立加载自己的代码段。AIV与AIC之间通过Global Memory进行数据传递。
## 计算单元
Cube计算单元和Vector计算单元分离部署
本架构中，Cube计算单元和Vector计算单元分别部署在AIC核和AIV核上，每个核都有自己的Scalar单元，能独立加载自己的代码段。
Vector计算单元
-   Vector计算单元的数据来自于Unified Buffer，要求32字节对齐。
Cube计算单元
-   Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和中间结果。
## 存储单元
获取存储单元的内存空间大小
开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。
