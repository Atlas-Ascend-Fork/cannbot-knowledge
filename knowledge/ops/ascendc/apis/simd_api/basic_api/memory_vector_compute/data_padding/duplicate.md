---
type: API
title: Duplicate
description: 将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/Duplicate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Duplicate

将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, 连续计算, 掩码操作, Reg矢量计算API。

本接口属于 UB 矢量计算数据填充接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 全量清零 padding 覆盖有效区 banned](../../../../../runbooks/precision/duplicate_padding_banned.md)（`exemplifies`）：“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”明确给出左端事实；“2. `Duplicate(bG, 0, count_padded)` 同样从 0 开始全量填 0，覆盖了 `bG`（gradOutput）的有效元素——`Duplicate` 不支持 offset 操作，只能从 0 开始填整个 `count_padded`，无法只清 `［count, count_padded)` 区间。”明确给出右端事实。API 从起点连续填充的语义解释了为何试图只清 padding 却覆盖有效区；排障页给出全量 Duplicate 后 ST 回归及源头/区间清零替代方向。
- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”明确给出左端事实；“UB 侧 LocalTensor 清零的正确 API 是 `Duplicate`（Vector 通道，按 mask 清零整个/部分 VReg），不是 `InitOutput`。”明确给出右端事实。API 的 LocalTensor 填充值能力正是排障页修复 InitOutput(GlobalTensor) 类型不匹配时采用的 UB 清零路径。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](../../../../../runbooks/performance/duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`exemplifies`）：`Duplicate<half>` 是 Vector 流水线指令，执行时占用 Vector 管线把 UB 填成指定值。在纯写探针里，UB 内容对 HBM 写带宽无影响（HBM 控制器按总线事务写，不关心 payload 初值），但 `Duplicate` 与 `DataCopy`（MTE3）在 kernel 里串行执行，`Duplicate` 的 Vector 执行时间被加进 kernel 总时间，拉低写带宽。即"预填充 UB"没有 HBM 侧收益，只有 Vector 侧开销。；将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。运行手册用纯写 HBM 探针实证该填充 API 会额外占用 Vector 流水线，给出不得为写带宽预填 UB 的具体性能边界。
<!-- cannbot:related:end -->
