---
type: API
title: DisableDmaAtomic
description: 关闭数据搬运随路原子操作，后续搬运时GM原始数据将被新数据完全覆盖。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.atomic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/DisableDmaAtomic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
source_headers:
- include/basic_api/kernel_operator_set_atomic_intf.h
---

# DisableDmaAtomic<a name="ZH-CN_TOPIC_0000001839732381"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_set_atomic_intf.h"`。

关闭数据搬运随路原子操作功能，后续执行数据搬运时，GM中原始数据将被新搬运数据完全覆盖。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void DisableDmaAtomic()
```

## 参数说明<a name="section622mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

[SetAtomicAdd](set_atomic_add.md)、[SetAtomicMax](set_atomic_max_isasi.md)、[SetAtomicMin](set_atomic_min_isasi.md)使用完成后，通过DisableDmaAtomic清空原子操作的状态，以免影响后续相关指令功能。

## 调用示例<a name="section177231425115410"></a>

```cpp
AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;
AscendC::LocalTensor<T> srcLocal = ubAllocator.Alloc<T, SIZE>();

AscendC::DisableDmaAtomic();
AscendC::DataCopy(srcLocal, srcGlobal, SIZE);
AscendC::SetFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
AscendC::WaitFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
AscendC::SyncAll();

// 开启原子累加，将Unified Buffer（UB）数据原子累加到GM
AscendC::SetAtomicAdd<T>();
AscendC::DataCopy(dstGlobal, srcLocal, SIZE);

// 关闭原子累加
AscendC::DisableDmaAtomic();
```

完整样例请参考[DataMovementWithAtomicOperations样例](https://gitcode.com/cann/asc-devkit/blob/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/06_atomic/data_movement_with_atomic_operations/data_movement_with_atomic_operations.asc)。


<!-- cannbot:related:start -->
## 相关

- [SetAtomicAdd](set_atomic_add.md)（`related`）：约束：与SetAtomicAdd/SetAtomicMax等配合使用，成对调用。；设置DMA搬运时的随路原子操作为累加。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。。SetAtomicAdd 开启随路原子累加，DisableDmaAtomic 在同一 DMA 搬运状态链末端关闭该模式，文档明确要求成对调用。
- [SetAtomicMax](set_atomic_max_isasi.md)（`related`）：设置DMA搬运时的随路原子操作为取最大值。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子取最大值（旧值和新值中的最大值）。；函数原型：__aicore__ inline void DisableDmaAtomic()。参数：无。约束：与SetAtomicAdd/SetAtomicMax等配合使用，成对调用。头文件：basic_api/kernel_operator_atomic_intf.h。；焦点开启后续 DMA AtomicMax 状态，目标接口是合同要求的配对关闭动作。
- [关键特性说明（原子操作）](key_features.md)（`related`）：解决方案：通过DisableDmaAtomic禁用DMA原子操作；使用SetAtomicType配置原子类型；对浮点数累加结果进行reorder控制；或使用标量原子操作替代DMA随路原子操作。；禁用DMA搬运时的随路原子操作。调用后，后续从UB/L0C/L1到GM的DataCopy搬运不再执行原子操作，恢复为普通覆盖写入。。候选接口直接实现焦点卡针对浮点原子累加非确定性的关闭动作。
- [SetAtomicMin](set_atomic_min_isasi.md)（`same_topic`）：函数原型：__aicore__ inline void SetAtomicMin<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；取最小值满足结合律，不存在非确定性问题。头文件：basic_api/kernel_operator_atomic_intf.h。 调用后，后续从UB/L0C/L1到GM的DataCopy搬运不再执行原子操作，恢复为普通覆盖写入。 SetAtomicMin 开启随路原子最小后必须由 DisableDmaAtomic 收口，否则后续 DataCopy 仍受原子状态影响。
- [SetAtomicType](set_atomic_type.md)（`same_topic`）：函数原型：template <typename T> __aicore__ inline void SetAtomicType(AtomicType atomicType)。模板参数T指定数据类型。参数：atomicType为原子操作类型枚举。约束：与DisableDmaAtomic配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。 调用后，后续从UB/L0C/L1到GM的DataCopy搬运不再执行原子操作，恢复为普通覆盖写入。 SetAtomicType 选择随路原子类型，DisableDmaAtomic 在使用后清状态，避免后续搬运继续执行原子操作。
<!-- cannbot:related:end -->
