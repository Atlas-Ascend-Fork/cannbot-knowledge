---
type: API
title: SetAtomicMax
description: 对后续搬运到GM的数据开启原子取大，将拷贝内容与GM已有值比较后写入最大值。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.atomic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicMax_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/basic_api/kernel_operator_set_atomic_intf.h
---

# SetAtomicMax\(ISASI\)<a name="ZH-CN_TOPIC_0000001685721321"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_set_atomic_intf.h"`。

设置后续搬运到GM的数据是否执行原子比较：将待拷贝的内容和GM已有内容进行比较，然后将最大值写入GM。SetAtomicMax接口可通过设置模板参数来设定不同的数据类型。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T>
__aicore__ inline void SetAtomicMax() 
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
|--------|------|
| T | 设定不同的原子最大操作数据类型。 |

## 数据类型

支持的数据类型为int8_t、int16_t、half、bfloat16_t、int32_t、float。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>


- Ascend 950PR/Ascend 950DT，支持的数据通路为UB/L0C Buffer->GM。



- Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据通路为UB/L0C Buffer/L1 Buffer->GM。



- Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据通路为UB/L0C Buffer/L1 Buffer->GM。


- 使用完后，建议通过[DisableDmaAtomic](disable_dma_atomic.md)关闭原子最大操作，以免影响后续相关功能。
- 该接口执行前不会自动清零GM数据。开发者需根据算子逻辑判断是否清零，如需清零，请在执行前手动完成。
- SetAtomicMax内部已集成与[SetAtomicType](set_atomic_type.md)相同的功能。建议调用上述接口时，通过设置模板参数显式指定原子操作的数据类型，无需额外调用SetAtomicType接口。

## 调用示例<a name="section177231425115410"></a>

```cpp
#include "kernel_operator.h"

constexpr uint32_t SIZE = 256;
__aicore__ inline void CopyIn()
{
    AscendC::LocalTensor<T> srcLocal = queueSrc.AllocTensor<T>();
    // 清空原子操作的状态
    AscendC::DisableDmaAtomic();
    AscendC::DataCopy(srcLocal, srcGlobal, SIZE);
    queueSrc.EnQue(srcLocal);
    // 核间同步
    AscendC::SyncAll();
}

__aicore__ inline void CopyOut()
{
    AscendC::LocalTensor<T> srcLocal = queueSrc.DeQue<T>();
    // 开启原子MAX模式，3个核取最大值
    AscendC::SetAtomicMax<T>();
    AscendC::DataCopy(dstGlobal, srcLocal, SIZE);
    // 关闭原子操作
    AscendC::DisableDmaAtomic();
    queueSrc.FreeTensor(srcLocal);
}

/*
每个核的输入数据为: 
Src0: [1,1,1,1,1,...,1] // 256个1
Src1: [2,2,2,2,2,...,2] // 256个2
最终输出数据: [2,2,2,2,2,...,2] // 256个2
*/
```

完整样例请参考[DataMovementWithAtomicOperations样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/06_atomic/data_movement_with_atomic_operations)。


<!-- cannbot:related:start -->
## 相关

- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：设置DMA搬运时的随路原子操作为取最大值。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子取最大值（旧值和新值中的最大值）。；函数原型：__aicore__ inline void DisableDmaAtomic()。参数：无。约束：与SetAtomicAdd/SetAtomicMax等配合使用，成对调用。头文件：basic_api/kernel_operator_atomic_intf.h。；焦点开启后续 DMA AtomicMax 状态，目标接口是合同要求的配对关闭动作。
- [DynamicQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/quant/dynamic_quant_950.md)（`related`）：“｜ partial extrema ｜ `SetAtomicMax/Min<float>` ｜ M-block cores ｜ GM workspace ｜ FP32 extrema ｜ conflicts on same b,n ｜”记录 DynamicQuant split-M 的并发归约动作；“设置DMA搬运时的随路原子操作为取最大值。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子取最大值（旧值和新值中的最大值）。”给出 SetAtomicMax 的搬运合同，可直接核验 phase-1 extrema 合并。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 5 / 5 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [MoeDistributeCombine A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_combine.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicMax(...)` 的直接调用（第 1557 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_v2.h#L1557)
- [MoeDistributeCombineAddRmsNorm A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_combine_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicMax(...)` 的直接调用（第 1557 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_v2.h#L1557)
- [MoeDistributeCombineAddRmsNorm 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_combine_add_rms_norm_950.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicMax(...)` 的直接调用（第 1557 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_v2.h#L1557)
- [MoeDistributeDispatch A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicMax(...)` 的直接调用（第 1180 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_v2.h#L1180)
- [MoeDistributeDispatch 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_950.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicMax(...)` 的直接调用（第 1180 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_v2.h#L1180)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
