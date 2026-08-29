---
type: Guide
title: NPU架构版本3510
description: 本节介绍__NPU_ARCH__版本号为3510的硬件架构和其功能说明。
tags: [task.lookup, topic.programming_model.execution_unit]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# NPU架构版本3510

本节介绍__NPU_ARCH__版本号为3510的硬件架构和其功能说明。
## 硬件架构图
如下图所示，本架构中AI Core分为AIC和AIV两个独立的核，分别用于矩阵计算和向量计算。AIC核与AIV核配比为1：2。每个核都有自己的Scalar单元，能独立加载自己的代码段。
该架构的关键特点有：
-   增加L0C Buffer -> Unified Buffer、Unified Buffer  L1 Buffer的数据通路。
-   删除Global Memory -> L0A Buffer、Global Memory -> L0B Buffer的数据通路。
-   删除L1 Buffer-> Global Memory的数据通路。
-   SSBuffer，用于AIC和AIV的核间通信。
-   增加SIMD Register File存储层次，在SIMD程序中，数据从Unified Buffer搬运到Register进行计算，产生的中间结果可以不用传回Unified Buffer，直接在寄存器计算。
-   新增SIMT相关硬件单元。SIMT相关硬件单元介绍如下：
## 计算单元
Cube计算单元和Vector计算单元分离部署
本架构中，Cube计算单元和Vector计算单元分别部署在AIC核和AIV核上，每个核都有自己的Scalar单元，能独立加载自己的代码段。
Vector计算单元
-   Vector计算单元支持U8、U16、U32、S8、S16、S32、BF16、FP16、FP32数据类型。
-   Vector计算单元每拍可处理256字节的数据。
-   Vector计算单元处理的数据来源来自于Register。
-   在本架构版本中，高维切分接口中的传入的掩码值会被转化为MaskReg传入Vector计算单元，而在NPU架构版本2201中，掩码值从特殊的掩码寄存器中读取。
Cube计算单元
-   Cube计算单元支持FP32/FP16/BF16/HiF8/FP8_E4M3/FP8_E5M2/U8/S8。一拍完成一个float16数据类型的16x16与16x16大小的矩阵乘；如果是int8_t数据类型，则一拍完成16*32与32*16大小的矩阵乘。
-   Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和中间结果。
Scalar单元
-   Scalar单元支持U16/S16/U32/S32/U64/S64/FP64数据类型。
-   在Regbase架构中，Aux Scalar计算单元单独处理SIMD_VF函数内的Scalar计算，Scalar计算单元处理SIMD_VF函数外的Scalar计算。
## 存储单元
获取存储单元的内存空间大小
开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。
