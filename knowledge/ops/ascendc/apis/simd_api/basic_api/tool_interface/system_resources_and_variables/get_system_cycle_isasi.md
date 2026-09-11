---
type: API
title: GetSystemCycle
description: 获取系统计数器当前的cycle值，通过前后差值可计算代码段执行时间。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSystemCycle_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/basic_api/kernel_operator_sys_var_intf.h
---

# GetSystemCycle(ISASI)

## 功能说明

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。


针对Ascend 950PR/Ascend 950DT，若换算成时间需要按照1GHz的频率，时间单位为us，换算公式为：time = (cycle数/1000)us。



针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，若换算成时间需要按照50MHz的频率，时间单位为us，换算公式为：time = (cycle数/50)us。



针对Atlas A2 训练系列产品/Atlas A2 推理系列产品，若换算成时间需要按照50MHz的频率，时间单位为us，换算公式为：time = (cycle数/50)us。
 

## 函数原型

```cpp
__aicore__ inline int64_t GetSystemCycle()
```

## 参数说明

无

## 返回值说明

返回系统计数器当前的cycle值。

## 约束说明

该接口属于PIPE\_S流水，若需要测试其他流水的指令时间，需要在调用该接口前通过[PipeBarrier](../../sync_control/intra_core_sync/pipe_barrier_isasi.md)插入对应流水的同步，具体请参考[调用示例](#example2)。

## 调用示例

- 如下示例通过`GetSystemCycle`获取系统cycle数，并换算成时间（单位：us）。

    ```cpp
    #include "kernel_operator.h"

    __aicore__ inline void InitTilingParam(int32_t& totalSize, int32_t& loopSize)
    {
        int64_t systemCycleBefore = AscendC::GetSystemCycle(); // 调用GetBlockNum指令前的cycle数
        loopSize = totalSize / AscendC::GetBlockNum();
        int64_t systemCycleAfter = AscendC::GetSystemCycle(); // 调用GetBlockNum指令后的cycle数
        int64_t GetBlockNumCycle = systemCycleAfter - systemCycleBefore; // 执行GetBlockNum指令所用的cycle数
        int64_t CycleToTimeBase = 50; // cycle数转换成时间的基准单位
        /* 在Ascend 950PR/Ascend 950DT上为1000
        在Atlas A3 训练系列产品/Atlas A3 推理系列产品上为50
        在Atlas A2 训练系列产品/Atlas A2 推理系列产品上为50 */
        int64_t GetBlockNumTime = GetBlockNumCycle / CycleToTimeBase; // 执行GetBlockNum指令所用时间，单位为us
    };
    ```

- <a id="example2"></a>如下示例为获取矢量计算Add指令时间的关键代码片段，在调用`GetSystemCycle`之前，插入了`PIPE_ALL`同步，可以保证相关指令执行完后再获取cycle数。

    ```cpp
    PipeBarrier<PIPE_ALL>();
    int64_t systemCycleBefore = AscendC::GetSystemCycle(); // 调用Add指令前的cycle数
    AscendC::Add(dstLocal, src0Local, src1Local, 512);
    PipeBarrier<PIPE_ALL>();
    int64_t systemCycleAfter = AscendC::GetSystemCycle(); // 调用Add指令后的cycle数
    int64_t GetBlockNumCycle = systemCycleAfter - systemCycleBefore; // 执行Add指令所用的cycle数
    int64_t CycleToTimeBase = 50; // cycle数转换成时间的基准单位
    /* 在Ascend 950PR/Ascend 950DT上为1000
    在Atlas A3 训练系列产品/Atlas A3 推理系列产品上为50
    在Atlas A2 训练系列产品/Atlas A2 推理系列产品上为50 */
    int64_t GetBlockNumTime = GetBlockNumCycle / CycleToTimeBase; // 执行Add指令所用时间，单位为us
    ```


<!-- cannbot:related:start -->
## 相关

- [选择低延迟指令，优化归约操作性能](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md)（`explains`）：“输入shape为30000，数据类型为float时，如下示例的性能数据对比如下，数据单位为cycle，使用GetSystemCycle接口获取。”；“获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。”。GetSystemCycle 是指南中比较归约方案 cycle 的直接测量接口，并给出平台频率换算合同。
- [AscGetSystemCycle](../../../c_api/utils/sys_var/asc_get_system_cycle.md)（`same_topic`）：获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。；读取当前系统cycle计数器，返回int64_t类型的当前计数值。该计数器为只读系统计数器，宽度64bit，复位值为0，随系统时钟持续递增，反映硬件运行以来的累计cycle数，常用于性能统计、耗时测量与执行序的时序判断。本接口在AIC与AIV上均可调用，返回值含义一致。。两张 API 卡描述同一只读系统 cycle 计数器的 C++ 与 C 接口语义，均用于前后差值计时。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 9 / 9 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AttentionToFfn A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/attention_to_ffn.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 441 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/common/op_kernel/moe_distribute_base.h#L441)
- [DistributeBarrier A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/distribute_barrier.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 441 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/common/op_kernel/moe_distribute_base.h#L441)
- [DistributeBarrier 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/distribute_barrier_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 112 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/distribute_barrier/op_kernel/distribute_barrier.h#L112)
- [FfnToAttention A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/ffn_to_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 441 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/common/op_kernel/moe_distribute_base.h#L441)
- [MoeDistributeCombine A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_combine.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 229 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_a2_layered.h#L229)
- [MoeDistributeCombineAddRmsNorm A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_combine_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 1068 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_v2.h#L1068)
- [MoeDistributeCombineAddRmsNorm 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_combine_add_rms_norm_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 1068 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_v2.h#L1068)
- [MoeDistributeDispatch A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 364 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_a2_layered.h#L364)
- [MoeDistributeDispatch 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSystemCycle(...)` 的直接调用（第 1156 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_v2.h#L1156)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
