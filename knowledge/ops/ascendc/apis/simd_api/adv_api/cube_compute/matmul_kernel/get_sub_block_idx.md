---
type: API
title: GetSubBlockIdx
description: 获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetSubBlockIdx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetSubBlockIdx

获取当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV的子核ID分别为0, 1, ..., N-1。 Matmul::GetSubBlockIdx()与基础API接口AscendC::GetSubBlockIdx()的区别在于，Matmul::GetSubBlockIdx()用于获取当前AIV核在当前AI Core分组中的ID，而AscendC::GetSubBlockIdx\(\)获取的是AIV核在所有AI Core分组中的逻辑ID。

函数原型：__aicore__ inline uint8_t GetSubBlockIdx()

返回值：当前AIV核的ID。

约束：
- 该接口仅支持在分离架构下使用，否则返回随机值。
- 在分离架构中，AIV核的ID会在REGIST_MATMUL_OBJ()接口内部自动初始化和赋值。因此，需要在调用REGIST_MATMUL_OBJ()接口之后，再调用本接口，以获取正确的ID。
- 若在算子程序中调用SetSubBlockIdx()后， GetSubBlockIdx()接口将返回由SetSubBlockIdx接口设置的ID值。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。
