---
type: API
title: GetWithOffset
description: 以TBuf为基地址，向后偏移指定长度，将偏移后的地址作为起始地址，提取长度为指定值的Tensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/GetWithOffset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetWithOffset

头文件路径为："basic_api/kernel_tpipe.h"。

以TBuf为基地址，向后偏移指定长度，将偏移后的地址作为起始地址，提取长度为指定值的Tensor。

约束：size的数值是Tensor中元素的个数，size*sizeof(T) + bufOffset不能超过TBuf初始化时的长度。

bufOffset需满足32字节对齐的要求。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：确认 `TBuf`/`TQue` 的 `InitBuffer` 分配的基址本身 32B 对齐（`Get` / `GetWithOffset(…, 0)` 返回的起始地址对齐），问题只在 `operator［］` 偏移。；bufOffset需满足32字节对齐的要求。。运行手册用 GetWithOffset 的零偏移返回值确认 TBuf 基址对齐，API 卡给出非零 bufOffset 的 32 字节硬约束，从而定位 operator［］ 元素偏移破坏对齐的根因。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“LocalTensor<WSTYPE> tmpBuf = wsBuf_.GetWithOffset<WSTYPE>(wsTypeNum, wsBufferSize_ / 2);”给出 DequantBias 将 TBuf 一分为二的实际调用；“size*sizeof(T) + bufOffset不能超过TBuf初始化时的长度。”给出该 offset 子视图的越界条件。
<!-- cannbot:related:end -->
