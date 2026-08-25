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

- [Duplicate 全量清零 padding 覆盖有效区 banned](../../../../../runbooks/precision/duplicate_padding_banned.md)（`exemplifies`）：“Duplicate”定义：将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。；“Duplicate 全量清零 padding 覆盖有效区 banned”定义：模式2 Select 在 count 非 64 整数倍时 padding 区垃圾 mask 污染有效元素；用 Duplicate(buf,0,count_padded) 全量清零 padding 会因 Duplicate 无 offset 语义覆盖有效 gradOutput 致回归——banned，须源头清零或区间清零。。实质衔接：这些卡分别限定 Duplicate 的等价 Reg/C API、UB 清零和标量广播正用法，以及全量 padding 覆盖、归约标量来源和纯写预填充的失败/性能边界。
- [Duplicate 掩码向量化未修复 triu 大 shape 失败](../../../../../runbooks/performance/duplicate_triu_shape.md)（`exemplifies`）：《Duplicate》给出“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”；该约束/探针可直接复现、解释或前置验证《Duplicate 掩码向量化未修复 triu 大 shape 失败》中的“triu 大 shape Case9 失败初判为标量 SetValue 掩码瓶颈，改 Duplicate 0 填充向量化后仍失败；后续 timing 定位实为 per-tile event flag 耗尽的正确性问题（非超时），Duplicate 向量化路线 banned。”。
- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：“Duplicate”定义：将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。；“InitOutput GM 专用，UB 清零用 Duplicate”定义：AscendC InitOutput(GlobalTensor<T>, uint32_t, T) 是 GM 专用清零 API，把 LocalTensor 作为第一参数传入会触发 'no known conversion from LocalTensor to GlobalTensor'；UB LocalTensor 清零应改用 Duplicate(local, value, mask)。判别依据为编译器候选函数 note 显示 InitOutput 唯一签名第一参数为 GlobalTensor<T>。。实质衔接：这些卡分别限定 Duplicate 的等价 Reg/C API、UB 清零和标量广播正用法，以及全量 padding 覆盖、归约标量来源和纯写预填充的失败/性能边界。
- [Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer](../../../../../runbooks/precision/count_based_max_min_is_element_wise_not_scalar_broadcast.md)（`exemplifies`）：“Duplicate”定义：将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。；“Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer”定义：AscendC count-based Max/Min(dst,src0,src1,count) 是逐元素比较，src1 必须是与 src0 同长度的完整 tensor，不做标量广播；要用标量做 clamp 须先 Duplicate(scalar) 填充同长度 tensor，且该 buffer 容量须 ≥ N×sizeof(float)（32B clampBuf 远不够），应复用阶段内已空闲的 N×float buffer。。实质衔接：这些卡分别限定 Duplicate 的等价 Reg/C API、UB 清零和标量广播正用法，以及全量 padding 覆盖、归约标量来源和纯写预填充的失败/性能边界。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](../../../../../runbooks/precision/reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`exemplifies`）：“Duplicate”定义：将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。；“Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差”定义：仅限 fp32 末轴 Softmax 的安全回退：归约结果经 32B UB 槽 GetValue 后标量 Duplicate；FP16/BF16 不适用，应走 UB 槽 LoadAlign 到 Reg 后广播。。实质衔接：这些卡分别限定 Duplicate 的等价 Reg/C API、UB 清零和标量广播正用法，以及全量 padding 覆盖、归约标量来源和纯写预填充的失败/性能边界。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](../../../../../runbooks/performance/duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《Duplicate》具体提供“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [arch35 小 per-channel 输出读旧值判别与规避](../../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《Duplicate》提供“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [AscDuplicate](../../../c_api/vector_compute/asc_duplicate.md)（`related`）：“Duplicate”定义：将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。；“AscDuplicate”定义：执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。。实质衔接：这些卡分别限定 Duplicate 的等价 Reg/C API、UB 清零和标量广播正用法，以及全量 padding 覆盖、归约标量来源和纯写预填充的失败/性能边界。
- [AscDuplicateHighest](../../../c_api/reg/data_fill/asc_duplicate_highest.md)（`same_topic`）：AscDuplicateHighest 与《Duplicate》的实质衔接是：AscDuplicateHighest 从 src 最高 lane 广播到 mask 选中位置；Merge/Scalar/普通 Duplicate 的来源与未选中位置处理不同，相关错例直接约束枚举、范围和归约结果广播。
- [Brcb](brcb.md)（`same_topic`）：焦点处理Brcb 把 8 个输入分别广播到 8 个 DataBlock 的填充模式；Duplicate正文说明“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式”。候选提供同一 DataBlock 广播在 C API/Reg load 中的等价形态或标量广播替代。
- [Duplicate](../../reg_vector_compute/data_padding/duplicate.md)（`same_topic`）：Memory Tensor Duplicate 与 Reg Duplicate 都执行标量广播，但输出载体与 mask 语义不同。
<!-- cannbot:related:end -->
