---
type: API
title: ReduceMin
description: 从所有输入数据中找出最小值，可选返回最小值索引。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/ReduceMin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: ['950', a2, a3]
---

# ReduceMin

从所有输入数据中找出最小值，可选返回最小值索引。

ReduceMin接口用于从所有输入数据中找出最小值和最小值索引。 ReduceMin计算过程如下图所示：首先，在每个repeat迭代中计算得到最小值和repeat内部索引，这些中间结果暂存于sharedTmpBuffer工作区中；然后，在中间结果的基础上继续按repeat迭代得到最终的最小值和最小值索引。需要注意的是，每次repeat迭代获取的最小值索引是repeat内部索引，返回最终结果时，需要根据迭代位置和repeat内部索引推导全量数据的最小值索引。 图1 ReduceMin计算示意图

本接口属于 UB 矢量计算接口。

参数说明：T：操作数数据类型。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN、VECCALC、VECOUT。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN、VECCALC、VECOUT。；sharedTmpBuffer：输入 指令执行期间存储中间结果，用于内部计算所需操作空间，需特别注意空间大小。详情请参考[关键特性说明](#关键特性说明)。 类型为LocalTensor，支持的TPosition为VECIN、VECCALC、VECOUT。；count：输入 参与计算的元素个数。关于该参数的具体说明请参考[连续计算](../simd_compute/continuous_compute.md)。最大处理的数据量不能超过UB大小限制。

约束：源操作数及sharedTmpBuffer的地址对齐约束请参考通用地址对齐约束，起始地址需要32字节对齐；目的操作数的起始地址对齐约束请参考ReduceRepeat-表3。；操作数地址重叠约束请参考通用地址重叠约束。；需要使用sharedTmpBuffer的情况下，支持dst与sharedTmpBuffer地址重叠（通常情况下dst比sharedTmpBuffer所需的空间要小），此时sharedTmpBuffer必须满足所需空间要求，详情请参考关键特性说明。；当参数count或repeatTime取值为0时，该接口的行为如下：

<!-- cannbot:related:start -->
## 相关

- [950 循环内 ReduceMin 取索引致 vector core 异常](../../../../../runbooks/precision/950_reducemin_vector_core.md)（`exemplifies`）：从所有输入数据中找出最小值，可选返回最小值索引。；触发（tool_observed）：在 950（arch 3510）上，kernel 的 `for` 循环内反复调用 `ReduceMin(dst, src, workBuf, count, calIndex=true)` + `reinterpret_cast<uint32_t*>(&tempIndex)` 取最小值索引时，plog 报 `AIV Kernel happen error, retCode=0x31`（vector core exception），对应 error code 264、subErrType 0x4（D-cache 读写 UB、总线返回非零）。同一 V2 用例、同一数据跑 10 次出现 3 PASS/7 FAIL 的非确定崩溃；`numSeqs` 越大（`ComputeInputTokens` 的 `for` 循环迭代越多、`ReduceMin` 调用越频繁）崩溃率越高。。API允许返回最小值索引，Runbook精确限定 950 循环内反复以 calIndex=true 取索引会触发非确定 vector core 异常。
<!-- cannbot:related:end -->
