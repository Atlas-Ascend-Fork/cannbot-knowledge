---
type: API
title: AscGetBlockNum
description: 获取当前任务配置的核数，用于多核逻辑控制。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_block_num.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetBlockNum

获取当前任务配置的核数，用于代码内部的多核逻辑控制等。 此接口后续版本会废弃，请使用内置变量block_num。
函数原型：int64_t asc_get_block_num()
返回值：当前任务配置的核数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [SIMT 内读块号致 Bisheng 崩溃—移到核入口](../../../../runbooks/compilation/simt_move_block_metadata_to_vector_shell.md)（`exemplifies`）：SIMT 内读块号致 Bisheng 崩溃—移到核入口 与《AscGetBlockNum》的实质衔接是：块级 GetBlockIdx/GetBlockNum 必须在 __aicore__ caller 读取并把标量区间传给 __simt_vf__；C/C++ 查询卡给出正确入口，SIMT helper/纯 SIMT 参数与混合入口卡共同限定 caller/callee 作用域。
- [per-core zero-out 经 grid-stride ZeroOutS](../../../../runbooks/precision/per_core_zero_out_grid_stride_zeroout_simt_overshoot.md)（`exemplifies`）：per-core zero-out 经 grid-stride ZeroOutS 与《AscGetBlockNum》的实质衔接是：该故障由 ZeroOutSimt 使用 blockIdx/gridDim 的跨核 grid-stride 导致；SIMT builtin、block 数接口与 SyncAll 共同解释索引越界和回退同步要求。
- [AscGetSubBlockNum](asc_get_sub_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《AscGetBlockNum》说明获取当前任务配置的核数，用于多核逻辑控制。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscGetBlockIdx](asc_get_block_idx.md)（`same_topic`）：AscGetBlockNum 与《AscGetBlockIdx》的实质衔接是：AscGetBlockNum 与 GetBlockIdx 共同定义多核分片的总数和当前索引；C++ 对应入口及系统变量页给出内置 block_num 迁移上下文。
- [GetBlockIdx](../../basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)（`same_topic`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《AscGetBlockNum》明确提供“获取当前任务配置的核数，用于多核逻辑控制。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [GetBlockNum](../../basic_api/tool_interface/system_resources_and_variables/get_block_num.md)（`same_topic`）：AscGetBlockNum 与《GetBlockNum》的实质衔接是：AscGetBlockNum 与 GetBlockIdx 共同定义多核分片的总数和当前索引；C++ 对应入口及系统变量页给出内置 block_num 迁移上下文。
- [系统变量](system_variables.md)（`same_topic`）：AscGetBlockNum 与《系统变量》的实质衔接是：AscGetBlockNum 与 GetBlockIdx 共同定义多核分片的总数和当前索引；C++ 对应入口及系统变量页给出内置 block_num 迁移上下文。
<!-- cannbot:related:end -->
