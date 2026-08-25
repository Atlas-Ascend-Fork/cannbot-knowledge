---
type: API
title: AscGetBlockIdx
description: 获取当前运行核的索引。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_block_idx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetBlockIdx

获取当前运行核的索引。 此接口后续版本会废弃，请使用内置变量block_idx。
函数原型：int64_t asc_get_block_idx()
返回值：当前运行核的索引。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [SIMT 内读块号致 Bisheng 崩溃—移到核入口](../../../../runbooks/compilation/simt_move_block_metadata_to_vector_shell.md)（`exemplifies`）：SIMT 内读块号致 Bisheng 崩溃—移到核入口 与《AscGetBlockIdx》的实质衔接是：块级 GetBlockIdx/GetBlockNum 必须在 __aicore__ caller 读取并把标量区间传给 __simt_vf__；C/C++ 查询卡给出正确入口，SIMT helper/纯 SIMT 参数与混合入口卡共同限定 caller/callee 作用域。
- [block 数应覆盖可用 Vector 核](../../../../runbooks/performance/block_count_uses_all_available_vector_cores.md)（`exemplifies`）：AscGetBlockIdx 与《block 数应覆盖可用 Vector 核》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [blockLength 对齐 slice 致 numBlocks 塌缩单核](../../../../runbooks/performance/blocklength_slice_numblocks.md)（`exemplifies`）：AscGetBlockIdx 与《blockLength 对齐 slice 致 numBlocks 塌缩单核》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [多核 ceil 尾块为负 — 每核按 remaining 截断](../../../../runbooks/precision/ceil_partition_each_core_must_clamp_remaining.md)（`exemplifies`）：AscGetBlockIdx 与《多核 ceil 尾块为负 — 每核按 remaining 截断》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [多核共享首段行区间导致部分输出未写](../../../../runbooks/precision/multiblock_launch_must_derive_row_range_from_block_index.md)（`exemplifies`）：AscGetBlockIdx 与《多核共享首段行区间导致部分输出未写》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [逐 block 串行启动退化多核并行](../../../../runbooks/performance/block.md)（`exemplifies`）：AscGetBlockIdx 与《逐 block 串行启动退化多核并行》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [SIMD算子实现主块均分](../../../../guides/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/main_block_even_split.md)（`explains`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《AscGetBlockIdx》说明获取当前运行核的索引。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [GetBlockNum](../../basic_api/tool_interface/system_resources_and_variables/get_block_num.md)（`related`）：AscGetBlockIdx 与《GetBlockNum》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [GetSubBlockIdx](../../adv_api/cube_compute/matmul_kernel/get_sub_block_idx.md)（`related`）：GetSubBlockIdx 与《AscGetBlockIdx》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [asc_get_core_id](asc_get_core_id.md)（`related`）：AscGetCoreId 返回当前物理核编号，AscGetBlockIdx 返回任务的 block 索引；多核寻址时必须区分硬件身份与调度索引。
- [AscGetBlockNum](asc_get_block_num.md)（`same_topic`）：AscGetBlockNum 与《AscGetBlockIdx》的实质衔接是：AscGetBlockNum 与 GetBlockIdx 共同定义多核分片的总数和当前索引；C++ 对应入口及系统变量页给出内置 block_num 迁移上下文。
- [GetBlockIdx](../../basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)（`same_topic`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《AscGetBlockIdx》明确提供“获取当前运行核的索引。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [系统变量](system_variables.md)（`same_topic`）：AscGetBlockIdx 与《系统变量》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
<!-- cannbot:related:end -->
