---
type: API
title: SetOrgShape
description: 设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetOrgShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetOrgShape

设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。

函数原型：
__aicore__ inline void SetOrgShape(int orgM, int orgN, int orgK)
__aicore__ inline void SetOrgShape(int orgM, int orgN, int orgKa, int orgKb, int orgKc = 0)

参数：
- orgM（输入）：设置原始完整的形状M大小，单位为元素。
- orgN（输入）：设置原始完整的形状N大小，单位为元素。
- orgK（输入）：设置原始完整的形状K大小，单位为元素。原始完整形状Ka=Kb时可设置。
- orgKa（输入）：设置矩阵A原始完整的形状Ka大小，单位为元素。
- orgKb（输入）：设置矩阵B原始完整的形状Kb大小，单位为元素。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Matmul使用说明](matmul_usage.md)（`related`）：“SetOrgShape”定义：设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。；“Matmul使用说明”定义：Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。实质衔接：Host tiling 与 Kernel 对象必须对原始 M/N/K 一致；复用对象处理矩阵块时还需区分完整 org shape 与当前 single shape。
- [SetSingleShape](set_single_shape.md)（`related`）：“SetOrgShape”定义：设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。；“SetSingleShape”定义：设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。。实质衔接：Host tiling 与 Kernel 对象必须对原始 M/N/K 一致；复用对象处理矩阵块时还需区分完整 org shape 与当前 single shape。
- [SetTensorB](set_tensor_b.md)（`related`）：SetTensorB 与《SetOrgShape》的衔接是：SetTensorB 的地址范围和转置解释同时受 SetOrgShape、Tiling侧 SetBType/ISTRANS 约束；Matmul 使用流程还要求与 SetTensorA 成对准备输入。
- [SetOrgShape](../matmul_tiling/set_org_shape.md)（`same_topic`）：“SetOrgShape”定义：设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。；“SetOrgShape”定义：设置Matmul计算时的原始完整的形状M、N、K或Ka/Kb，单位均为元素个数。。实质衔接：Host tiling 与 Kernel 对象必须对原始 M/N/K 一致；复用对象处理矩阵块时还需区分完整 org shape 与当前 single shape。
<!-- cannbot:related:end -->
