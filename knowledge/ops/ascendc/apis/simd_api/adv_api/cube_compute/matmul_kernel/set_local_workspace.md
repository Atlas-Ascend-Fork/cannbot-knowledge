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

<!-- cannbot:related:start -->
## 相关

- [如何使用workspace](../../../../../guides/programming_guide/appendix/common_operations/how_to_use_workspace.md)（`explains`）：Matmul local workspace 是具体消费接口。
- [核函数内删除Workspace相关冗余操作](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《SetLocalWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [GetNormalConfig](get_normal_config.md)（`related`）：GetNormalConfig 与《SetLocalWorkspace》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetUserWorkspace](../../../basic_api/resource_management/workspace/get_user_workspace.md)（`related`）：GetUserWorkspace 与《SetLocalWorkspace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [SetWorkspace](set_workspace.md)（`related`）：SetWorkspace说明Iterate计算的异步场景，调用本接口申请一块临时空间来缓存计算结果，然后调用GetTensorC时会在该临时空间中获取C的矩阵分片。 IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。
- [GetMDLConfig](get_mdl_config.md)（`same_topic`）：GetMDLConfig 与《SetLocalWorkspace》的实质衔接是：GetMDLConfig 生成 MatmulConfig；其 batchLoop、VecND2NZ 和模板参数会直接要求 IterateNBatch、GetMatmulApiTiling 与 local workspace 等配套路径。
- [MatmulGetTmpBufSize](../get_matmul_compute_space/matmul_get_tmp_buf_size.md)（`same_topic`）：MatmulGetTmpBufSize 与《SetLocalWorkspace》的实质衔接是：Matmul 临时空间查询与 V2/batch/multicore、buffer 预算、tiling 和 workspace 注册共同决定可用空间。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；SetLocalWorkspace正文界定“设置Matmul内部额外占用的UB临时空间，由用户预留并申请LocalTensor后传入，需在Iterate前调用”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
<!-- cannbot:related:end -->
