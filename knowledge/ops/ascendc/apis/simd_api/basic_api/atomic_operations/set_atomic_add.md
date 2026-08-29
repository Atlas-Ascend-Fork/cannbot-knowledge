---
type: API
title: SetAtomicAdd
description: 对后续搬运到GM的数据开启原子累加，将拷贝内容与GM已有值求和后写入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicAdd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetAtomicAdd

设置DMA搬运时的随路原子操作为累加。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。

函数原型：__aicore__ inline void SetAtomicAdd<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；浮点数累加可能产生非确定性结果。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：约束：与SetAtomicAdd/SetAtomicMax等配合使用，成对调用。；设置DMA搬运时的随路原子操作为累加。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。。SetAtomicAdd 开启随路原子累加，DisableDmaAtomic 在同一 DMA 搬运状态链末端关闭该模式，文档明确要求成对调用。
- [UnfoldGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/unfold_grad.md)（`related`）：UnfoldGrad 实现记录“普通与 second-axis body 都遵循 `CopyIn→可选 T1→FP32 Cast→transpose/rearrange/add→Atomic CopyOut`”；SetAtomicAdd 规定“后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。”。该 API 正是重叠窗口梯度写回的冲突合并机制。
- [关键特性说明（原子操作）](key_features.md)（`related`）：函数原型：__aicore__ inline void SetAtomicAdd<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；浮点数累加可能产生非确定性结果。头文件：basic_api/kernel_operator_atomic_intf.h。；非确定性计算产生的前提条件：原子操作类型为累加（最大值/最小值满足结合律不受影响）、数据类型为浮点数（整数加法满足结合律不受影响）、带随路原子操作的搬运指令达到3条及以上。。候选特性卡补全焦点接口何时出现非确定性以及如何规避。
- [AscSetAtomicAdd](../../c_api/simd_atomic/asc_set_atomic_add.md)（`same_topic`）：设置DMA搬运时的随路原子操作为累加。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。；本接口对后续目的地址为GM的数据搬运指令开启原子累加。两接口在 Basic API 和 C API 中设置同一后续 GM 搬运原子累加语义。
<!-- cannbot:related:end -->
