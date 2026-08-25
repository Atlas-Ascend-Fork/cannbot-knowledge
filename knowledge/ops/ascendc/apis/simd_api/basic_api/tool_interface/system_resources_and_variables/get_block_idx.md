---
type: API
title: GetBlockIdx
description: 获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetBlockIdx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetBlockIdx

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取当前逻辑AI Core的索引，用于代码内部的多核逻辑控制及多核偏移量计算等。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [DAV_2201 element-wise unary kernel 骨架 多核](../../../../../runbooks/compilation/dav2201_elementwise_unary_kernel_skeleton_relu.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《DAV_2201 element-wise unary kernel 骨架 多核》明确提供“在 DAV_2201（Ascend 910B3）上用 ops-direct-invoke 实现单入单出 element-wise unary 算子（以 ReLU fp16 为例）的完整 kernel 骨架：运行时取核数→尾核 tailing→TQue 双缓冲→DataCopyPad Ext 搬运→AscendC::Relu 矢量计算→GlobalTensor 显式偏移。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [MIX_AIC_1_1 仅启用 28/56 AIV 带宽不饱和](../../../../../runbooks/performance/mix_aic_1_1_underutilizes_aiv_on_1_to_2_topology.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《MIX_AIC_1_1 仅启用 28/56 AIV 带宽不饱和》明确提供“A5（Ascend950PR，28 CubeCore:56 VectorCore）上 KERNEL_TYPE_MIX_AIC_1_1 强制 1:1 配比，blockNum 上限=28，只启用 28/56 AIV（50%），HBM 带宽无法饱和；测 HBM 带宽应回退到 AIV_ONLY 56 核路线，MIX_AIC_1_1 在此场景 banned。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [SIMT 内读块号致 Bisheng 崩溃—移到核入口](../../../../../runbooks/compilation/simt_move_block_metadata_to_vector_shell.md)（`exemplifies`）：SIMT 内读块号致 Bisheng 崩溃—移到核入口 与《GetBlockIdx》的实质衔接是：块级 GetBlockIdx/GetBlockNum 必须在 __aicore__ caller 读取并把标量区间传给 __simt_vf__；C/C++ 查询卡给出正确入口，SIMT helper/纯 SIMT 参数与混合入口卡共同限定 caller/callee 作用域。
- [block 数应覆盖可用 Vector 核](../../../../../runbooks/performance/block_count_uses_all_available_vector_cores.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《block 数应覆盖可用 Vector 核》明确提供“Host 的固定 block 上限低于目标设备实测 Vector Core 数；把上限绑定到同设备探针结果后，配对端到端性能改善且正确性未退化。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [blockLength 对齐 slice 致 numBlocks 塌缩单核](../../../../../runbooks/performance/blocklength_slice_numblocks.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《blockLength 对齐 slice 致 numBlocks 塌缩单核》明确提供“SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [empty分支SetBlockDim(0)与aUbFactor误式判别](../../../../../runbooks/compilation/empty_setblockdim_0_aubfactor.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《empty分支SetBlockDim(0)与aUbFactor误式判别》明确提供“空 tensor 归约算子（EMPTY_A/EMPTY_R 分支）的 empty-branch TilingUT 0/14 全 FAILED；按 MISMATCH 字段分流——仅 blockDim mismatch 指向 EMPTY_A 的 SetBlockDim(0)（应为 max(usedCoreNum,1)=1），aLoopCntTotal/aUbFactor/usedCoreNum 全 mismatch 指向 EMPTY_R 的 aUbFactor=min(aTotal,maxSingleUb)（应为 min(maxSingleUb,CeilDiv(aTotal,coreNum))）；修正后 14/14。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [多核 ceil 尾块为负 — 每核按 remaining 截断](../../../../../runbooks/precision/ceil_partition_each_core_must_clamp_remaining.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《多核 ceil 尾块为负 — 每核按 remaining 截断》明确提供“ceil 分块后预计算末核 tail 可为负并让中后核越界；改为每核按 total-start 截断。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [多核共享首段行区间导致部分输出未写](../../../../../runbooks/precision/multiblock_launch_must_derive_row_range_from_block_index.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《多核共享首段行区间导致部分输出未写》明确提供“host 把首个行区间传给所有 block，多个核重复处理同一段；kernel 用 GetBlockIdx 推导本核区间后恢复覆盖。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [每核最少行数地板压低 AIV 并行度—按可用核数切分](../../../../../runbooks/performance/row_reduction_min_rows_floor_underutilizes_aiv.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《每核最少行数地板压低 AIV 并行度—按可用核数切分》明确提供“行级归约 tiling 不应先用每核最少行数限制 block 数；按可用 AIV 核数上限切分可恢复并行度。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [逐 block 串行启动退化多核并行](../../../../../runbooks/performance/block.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《逐 block 串行启动退化多核并行》明确提供“Ascend950 上按行切分多核的算子，若 launch 函数用 host 侧 for 循环逐 block 调 <<<1, nullptr, stream>>>，多核并行会退化为'启动开销 × block 数'的串行链；改单次 <<<numBlocks>>> + kernel 内 GetBlockIdx/GetBlockNum 自算行区间后，case1 耗时 42866µs→705µs（约 60× 相对）、20/20 精度不变。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [SIMD算子实现主块均分](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/main_block_even_split.md)（`explains`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《GetBlockIdx》说明获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [SIMD算子实现尾块均分](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/tail_block_even_split.md)（`explains`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《SIMD算子实现尾块均分》明确提供“该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [GetSubBlockIdx](../../../adv_api/cube_compute/matmul_kernel/get_sub_block_idx.md)（`related`）：GetSubBlockIdx 与《GetBlockIdx》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [AscGetBlockIdx](../../../c_api/sys_var/asc_get_block_idx.md)（`same_topic`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《AscGetBlockIdx》明确提供“获取当前运行核的索引。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [AscGetBlockNum](../../../c_api/sys_var/asc_get_block_num.md)（`same_topic`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《AscGetBlockNum》明确提供“获取当前任务配置的核数，用于多核逻辑控制。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [GetBlockNum](get_block_num.md)（`same_topic`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《GetBlockNum》明确提供“获取当前任务配置的逻辑AI Core的数量，用于多核逻辑控制等。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
<!-- cannbot:related:end -->
