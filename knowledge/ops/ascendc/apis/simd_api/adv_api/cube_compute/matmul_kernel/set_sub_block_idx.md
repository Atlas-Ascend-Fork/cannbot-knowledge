---
type: API
title: SetSubBlockIdx
description: 设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0,
  1, ..., N-1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetSubBlockIdx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetSubBlockIdx

设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0, 1, ..., N-1。

函数原型：__aicore__ inline void SetSubBlockIdx(uint8_t subBlockIdx)

参数：
- subBlockIdx（输入）：当前AIV核的ID。

约束：
- 该接口仅支持在分离架构下使用。
- 在分离架构中，AIV核的ID会在REGIST_MATMUL_OBJ()接口内部自动初始化和赋值。如果在算子程序中使用了REGIST_MATMUL_OBJ()接口，则不建议调用此接口；若未使用REGIST_MATMUL_OBJ\(\)接口，则请调用此接口并将子核ID设置为0。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [GetSubBlockIdx](get_sub_block_idx.md)（`related`）：若在算子程序中调用SetSubBlockIdx()后， GetSubBlockIdx()接口将返回由SetSubBlockIdx接口设置的ID值；设置当前AIV核的ID。前者明确读取值由后者写入，二者共同构成 AIV 子核 ID 的设置与读取契约。
<!-- cannbot:related:end -->
