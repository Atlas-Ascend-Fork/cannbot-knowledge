---
type: API
title: SetSingleShape
description: 设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetSingleShape

设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。

函数原型：__aicore__ inline void SetSingleShape(int singleM, int singleN, int singleK)

参数：
- singleM（输入）：设置的singleCoreM大小，单位为元素。
- singleN（输入）：设置的singleCoreN大小，单位为元素。
- singleK（输入）：设置的singleCoreK大小，单位为元素。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Matmul workspace 预偏移 totalN 回读 banned](../../../../../runbooks/precision/matmul_workspace_totaln_banned.md)（`exemplifies`）：SetSingleShape 在运行时确定 singleCoreM/N/K，Runbook 应以其中 singleCoreN 而非全局 totalN 计算每核输出区域。
- [SetOrgShape](set_org_shape.md)（`related`）：“SetOrgShape”定义：设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。；“SetSingleShape”定义：设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。。实质衔接：Host tiling 与 Kernel 对象必须对原始 M/N/K 一致；复用对象处理矩阵块时还需区分完整 org shape 与当前 single shape。
- [SetSingleShape](../matmul_tiling/set_single_shape.md)（`related`）：Host tiling 的 SetSingleShape 固化 singleCoreM/N/K，而 Kernel 侧同名接口在复用 Matmul 对象或尾块时运行时修改实际单核 shape；两端共同约束单核计算区域。
- [GetSingleShape](../matmul_tiling/get_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [SetTail](set_tail.md)（`same_topic`）：两接口都在不重做 Tiling 时重设 singleCoreM/N/K；SetSingleShape 正文明确说明与 SetTail 功能一致并推荐使用前者。
<!-- cannbot:related:end -->
