---
type: Operator
title: Ascend 950 线性注意力高 GVA 任务切分与数据排布
description: 从 head 归属和读写依赖推导分组、分核、片上窗口及写回位置，以 GDN 反向 G4 到 G16 的扩展验证设计。
tags:
- task.design
- topic.attention
status: draft
sources:
- resource: https://github.com/flashserve/flash-linear-attention-npu/blob/9367f8d941cc53dd4064ddfb5b9940f87ef0c21f/fla/ops/ascendc/gdn/chunk_gdn_bwd/chunk_gated_delta_rule_bwd_finalize/docs/design.md
  role: primary
- resource: https://github.com/flashserve/flash-linear-attention-npu/pull/1142
  role: supporting
- resource: https://github.com/flashserve/flash-linear-attention-npu/blob/dc1113e2e9f2ed8c2b29ab94b3a385990be0fbeb/fla/ops/ascendc/gdn/chunk_gdn_fwd/chunk_gated_delta_rule_fwd_prepare/README.md
  role: supporting
- resource: https://github.com/flashserve/flash-linear-attention-npu/blob/dc1113e2e9f2ed8c2b29ab94b3a385990be0fbeb/fla/ops/ascendc/gdn/recurrent_gdn/recurrent_gated_delta_rule/docs/api.md
  role: supporting
created_at: '2026-11-20T02:28:00Z'
updated_at: '2026-11-23T07:25:49Z'
platforms:
- '950'
---

# Ascend 950 线性注意力高 GVA 任务切分与数据排布

## 接口与概念

当多个 value head 共享一个 Q/K head 时，扩大 GVA 比例会增加同组消费者的数量。设计从一个输出元素开始：它读取哪个 head 的数据，哪些读取可以复用，最终由哪个任务写回？这个问题同样适用于正向、反向和递归推理。接口没有这种分组语义时跳过本卡。

对连续分组，先按输入布局找到 HK、HV 轴，确认两者为正且 HV 能被 HK 整除。令 `G = HV // HK`，则 `hk = hv // G`。例如 HK=2、HV=10 时，hv=4 属于第一组，hv=5 已进入第二组。序列、chunk、状态槽和 token 的索引按各自契约计算，再用实际 stride 合成地址。

### 算子算法

给每个输入、中间量和输出标出其表达式依赖的索引，再决定怎样排布。同一个 kernel 内可以同时出现下列依赖。

| 从表达式看到的依赖 | 对任务和存储的含义 |
|---|---|
| 值只随 hk 变化，组内 G 个 hv 都要读取 | 考虑让这些消费者落到同核或同一 tile，计算或搬入一次后复用。例如 GDN Prepare 同组复用 K·Kᵀ。若表达式还依赖每个 hv 的 gate，只能复用乘 gate 之前的公共部分。 |
| 结果随 hv 变化，或还依赖该 hv 在上一 token 的状态 | 各 hv 写各自的结果。可沿独立 head 分核；存在时间依赖时保留同一状态槽内的读、更新、写回顺序。 |
| 同一 hk 的输出由多个 hv 共同贡献 | 先确定贡献何时收齐、由谁最终写回。让一个核负责全组可省掉跨核合并；若为提高并行度而拆组，须为部分结果安排存储、合并次序和同步。 |

### 分核策略与基本块切分

先在序列、chunk 和 head 轴上圈出能独立完成的最小工作。若同组复用收益高或需要组内归约，可将整个 hk 组交给同一个任务，并从其他独立轴补充并行度。若独立组数少于工作核数，比较拆组带来的并行收益与重复搬运、跨核合并的代价。只接收逐 hv 张量且没有共享读写的阶段，先检查已有调度能否直接处理更大的 HV。

### 数据路径与存储层级

逻辑组宽 G 描述共享关系，片上窗口 W 取决于该 tile 同时存活的数据。列出共享输入、每个活跃 hv 的私有块、双缓冲和跨窗保留量，分别核算 UB、L1 等容量。若 G 超过 W，逐窗处理同一组，共享数据留到最后一个消费者用完；只有跨窗仍需使用的结果才需保留。选 W 时还要比较搬运次数和实际工作核数。

### 流水排布、同步关系与数值精度

在每个缓冲槽上标出生产者、最后一次读取和下一次覆盖。分别标出每个 hv 局部结果的舍入点、组内累计的 dtype 和最终输出的转换点，按参考实现保留三者的顺序。递归状态也按其接口区分单步更新、checkpoint 写回和下次读取的精度。窗口尾部要分别核对有效 head 和参与配对同步的核，二者数量可能不同。

## 用法

在直调工程中，先从调用方传给 kernel 的 shape、stride 和 tiling 参数确认 HK、HV 与实际工作核数，再核对 workspace 的分配者与各核偏移。下文的窗口宽度和空间实测取自 GDN 反向案例，迁移时按目标 kernel 的 tile 和同时存活的缓冲区重新推导。

将旧上限、首个超过窗口的比例和目标上限代入同一排布。逐窗记下共享读取范围、私有输出范围、跨窗保留量及最后一次写回的位置。对照父链和子算子各自的接口及 tiling，定位真正受比例限制的阶段。

## 代码模式

```text
# 对一个已分配的 hk，枚举该组内各物理窗口的有效 head
for offset in range(0, G, W):
    first_hv = hk * G + offset
    count = min(W, G - offset)
    # 本窗的全局 head 范围为 [first_hv, first_hv + count)
```

地址用实际 G 计算。若 tiling key 只表示“小比例”或“大比例”路径，从运行时 tiling 读取真实组宽。

## 约束

**GDN 反向实证。** Ascend 950 从 G4 扩到 G16 时，DHU 已覆盖目标范围，Intra 扩展了分派。Finalize 的片上窗口只能容纳 4 个 hv，因此把一个 (chunk, hk) 交给同一核。G5 依次处理 4+1，G16 处理四个满窗。每个 hv 先得到已舍入为 BF16 的 `dq_hv` 和 `dk_raw`。各 AIV 将这两个值分别扩为 FP32，跨窗累计到自己的 dq、dk 槽。末窗由 AIV0 以 FP32 合并两份 dq，再合并两份 dk，每个合并结果各舍入一次到 BF16；启用 Q/K L2Norm 时，按原设计在此之后执行。

G5 的末窗只有一个有效 hv，AIV1 没有 head 要计算，仍需参加双 AIV 握手。同一核领取下一个 (chunk, hk) 前，先用 `MTE3_V` 等待上一任务的最终输出写回完成，再清零累计区。这个实现还曾在 S12 和 S14 复用同一段 UB 时发生写后写竞争；修复是在 S14 重新搬入 Q 前配对使用已有的 `V_MTE2` 事件。迁移时按实际缓冲区的读写顺序确定事件。

本例每个 AIC 的两个 AIV 各有一个 65,536 字节槽，28 个工作核共新增 3.5 MiB。G1～4 新增为零，G5～16 定长与变长均新增 3.5 MiB。迁移时按目标 tile、活跃核数和实际申请核算跨窗保存部分结果的代价。

## 失败表现

仅第二组起始 head 出错时，核对组首地址是否用了 W 代替 G。仅首个尾窗出错时，核对有效 lane、最终写回时机和同步参与者。

## 验证方法

- 用至少两个 hk，给不同组的共享输入、同组各 hv 的私有数据赋予可区分的值。覆盖旧上限、首个尾窗和最大比例，逐 head 与参考实现比较；定长和变长按各自的序列边界取址。
- 对上述 Finalize 实例，用 G5 并让同一核连续处理两个输入可区分的任务。检查 S14 重载 Q 前的 `V_MTE2` 配对、4+1 尾窗两个 AIV 的握手，以及下一任务清零前的 `MTE3_V` 等待；分别核对两次写回的 dq/dk。
- 对逐 hv 状态，连续执行两次更新并比较每个有效状态槽；对组内归约，分别核对各 hv 的参考贡献及按 hk 合并后的输出。这样能区分寻址、写回冲突和累计精度问题。
- 用跨窗抵消检查舍入点。例如 G5 的两个窗口分别有一个 hv 的未舍入贡献为 257 和 −256，其余贡献为 0。按最近偶数舍入到 BF16，257 变为 256，−256 保持原值，扩为 FP32 累计后结果为 0。若跳过逐 hv 的 BF16 舍入，会错误地得到 1。
- 在原支持比例上用同卡、同输入和同一接口边界检查性能回归。首个跨窗比例若出现耗时跳升，可对照窗口数，检查共享数据是否被重复搬运、部分结果是否被反复写回。
