---
type: API
title: GetBlockNum
description: 获取当前任务配置的逻辑AI Core的数量，用于多核逻辑控制等。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetBlockNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetBlockNum

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [SIMT 内读块号致 Bisheng 崩溃—移到核入口](../../../../../runbooks/compilation/simt_move_block_metadata_to_vector_shell.md)（`exemplifies`）：SIMT 内读块号致 Bisheng 崩溃—移到核入口 与《GetBlockNum》的实质衔接是：块级 GetBlockIdx/GetBlockNum 必须在 __aicore__ caller 读取并把标量区间传给 __simt_vf__；C/C++ 查询卡给出正确入口，SIMT helper/纯 SIMT 参数与混合入口卡共同限定 caller/callee 作用域。
- [per-core zero-out 经 grid-stride ZeroOutS](../../../../../runbooks/precision/per_core_zero_out_grid_stride_zeroout_simt_overshoot.md)（`exemplifies`）：per-core zero-out 经 grid-stride ZeroOutS 与《GetBlockNum》的实质衔接是：该故障由 ZeroOutSimt 使用 blockIdx/gridDim 的跨核 grid-stride 导致；SIMT builtin、block 数接口与 SyncAll 共同解释索引越界和回退同步要求。
- [多核 ceil 尾块为负 — 每核按 remaining 截断](../../../../../runbooks/precision/ceil_partition_each_core_must_clamp_remaining.md)（`exemplifies`）：该 API 提供任务配置的逻辑核数，focal 的 ceil factor 与错误 tail 公式都依赖该值；结合 GetBlockIdx 可逐核计算 remaining。
- [AscGetBlockIdx](../../../c_api/sys_var/asc_get_block_idx.md)（`related`）：AscGetBlockIdx 与《GetBlockNum》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [WaitPreBlock](../../sync_control/inter_core_sync/wait_pre_block.md)（`related`）：WaitPreBlock 与《GetBlockNum》的实质衔接是：WaitPreBlock 必须与 NotifyNextBlock 等次数配对并先初始化 workspace；GetBlockNum 决定 GM/UB workspace 下限，关键特性说明其按 blockIdx 串行的确定性语义。
- [AscGetBlockNum](../../../c_api/sys_var/asc_get_block_num.md)（`same_topic`）：AscGetBlockNum 与《GetBlockNum》的实质衔接是：AscGetBlockNum 与 GetBlockIdx 共同定义多核分片的总数和当前索引；C++ 对应入口及系统变量页给出内置 block_num 迁移上下文。
- [GetBlockIdx](get_block_idx.md)（`same_topic`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《GetBlockNum》明确提供“获取当前任务配置的逻辑AI Core的数量，用于多核逻辑控制等。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
<!-- cannbot:related:end -->
