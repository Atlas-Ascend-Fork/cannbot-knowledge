---
type: API
title: SetLocalWorkspace
description: 设置Matmul内部额外占用的UB临时空间，由用户预留并申请LocalTensor后传入，需在Iterate前调用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetLocalWorkspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---


# SetLocalWorkspace

对于某些场景Matmul内部需要额外占用UB（VECCALC）空间，如果用户希望在算子中复用这个额外占用的UB（VECCALC）空间，则该空间需要用户预留，并申请好LocalTensor，将其起始物理地址传入给Matmul。具体需要申请的UB（VECCALC）临时空间大小由tiling接口MatmulGetTmpBufSize给出，满足以下任一条件时需要传入 UB 临时空间：C 位于 GM、C 为 ND 格式、A 或 B 为 ND 格式，或存在 Bias 且 Bias 不位于 VECCALC。

函数原型：__aicore__ inline void SetLocalWorkspace(const LocalTensor<uint8_t>& tmpBuffer)

参数：
- tmpBuffer（输入）：临时空间，由用户申请并管理，TPosition为VECCALC。

支持：Ascend 950PR/Ascend 950DT、Atlas 推理系列产品AI Core。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。
