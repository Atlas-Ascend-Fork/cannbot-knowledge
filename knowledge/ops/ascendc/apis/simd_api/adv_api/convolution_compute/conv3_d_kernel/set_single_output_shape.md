---
type: API
title: SetSingleOutputShape
description: 设置单核上结果矩阵Output的形状。 Conv3D高阶API目前支持M合轴模式的输出方式。在M合轴模式下，Conv3D API内部将Wout和Hout视为同一轴处理，输出时先沿Wout方向输出，完成一整行Wout输出后，再进行下一行的Wout输出。
  图1 M合轴模式示意图 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/SetSingleOutputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleOutputShape

设置单核上结果矩阵Output的形状。 Conv3D高阶API目前支持M合轴模式的输出方式。在M合轴模式下，Conv3D API内部将Wout和Hout视为同一轴处理，输出时先沿Wout方向输出，完成一整行Wout输出后，再进行下一行的Wout输出。 图1 M合轴模式示意图

函数原型：__aicore__ inline void SetSingleOutputShape(uint64_t singleCo, uint64_t singleDo, uint64_t singleM)

参数：
- singleCo（输入）：单核上Output的C维度大小。
- singleDo（输入）：单核上Output的D维度大小。
- singleM（输入）：单核上Output的M维度大小，即H维度大小与W维度大小的乘积。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Kernel侧接口](conv3d_kernel.md)（`related`）：SetSingleOutputShape 与《Conv3D Kernel侧接口》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [Conv3D Tiling使用说明](../conv3_d_tiling/conv3_d_tiling_usage.md)（`related`）：SetSingleOutputShape 与《Conv3D Tiling使用说明》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [Conv3D Tiling侧接口](../conv3_d_tiling/conv3d_tiling.md)（`related`）：SetSingleOutputShape 与《Conv3D Tiling侧接口》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [Conv3D Tiling构造函数](../conv3_d_tiling/conv3d_tiling_constructor.md)（`related`）：SetSingleOutputShape 与《Conv3D Tiling构造函数》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [Conv3DUsage](conv3_d_usage.md)（`related`）：SetSingleOutputShape 与《Conv3DUsage》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [Conv3D模板参数](conv3_d_template_params.md)（`related`）：SetSingleOutputShape 与《Conv3D模板参数》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [GetSingleShape](../../cube_compute/matmul_tiling/get_single_shape.md)（`related`）：SetSingleOutputShape 与《GetSingleShape》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [IterateAll](iterate_all.md)（`related`）：SetSingleOutputShape 与《IterateAll》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [卷积计算End](end.md)（`related`）：SetSingleOutputShape 与《卷积计算End》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [卷积计算Init](init.md)（`related`）：SetSingleOutputShape 与《卷积计算Init》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [SetSingleOutputShape](../conv3_d_tiling/set_single_output_shape.md)（`same_topic`）：《SetSingleOutputShape》明确“设置单核上结果矩阵Output的形状。 Conv3D高阶API目前支持M合轴模式的输出方式。在M合轴模式下，Conv3D API内部将Wout和Hout视为同一轴处理，输出时先沿Wout方向输出，完成一整行Wout输出后，再进行下一行的Wout输出。 图1 M合轴模式示意图”；它与《SetSingleOutputShape》的“设置单核上结果矩阵Output的形状。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
