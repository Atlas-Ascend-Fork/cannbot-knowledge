---
type: Optimization
title: 稀疏 Flash Attention（SFA）跨架构优化
description: 随机索引 SFA 在 Ascend910B3 与 Ascend950PR 上的暂存候选、重复读取反例、精度和编译边界，以及目标环境的验证要求。
tags: [task.optimization, topic.attention, topic.data_movement.memory_access, topic.compilation, topic.tiling, topic.precision]
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/pull/1209
  role: supporting
- resource: https://gitcode.com/cann/cannbot-skills/blob/9b3769d9a26804e77e631fb3783741349c2cb2d9/ops/triton-latency-optimizer/references/operators/sparse-flash-attention-optimization.md
  role: evidence
created_at: '2026-09-20T00:00:00Z'
updated_at: '2026-10-28T09:14:08Z'
platforms: [a2, '950']
---

# 稀疏 Flash Attention（SFA）跨架构优化

## 适用范围与证据边界

本卡用于 `sparse_indices` 已给定、KV_N=1、全部 Q 头共享稀疏集合的 MLA-absorb SFA；选块粒度为 token，KV 按索引随机读取。页内连续、可由页表仿射读取的形态应读取 [块稀疏 Attention 约束卡](../../guides/constraints/block_sparse_attention_constraints.md) 的对应骨架。

本文蒸馏固定来源中的历史报告，未在当前目标环境重现。平台字段表示卡片包含对应平台的记录，不保证同系列型号、其他 shape 或工具链有相同行为。

| 历史环境 | 测量范围与工具链 |
|---|---|
| Ascend910B3 | 随机 topk 16 case；20 cube / 40 vector core；triton-ascend 3.2.0、CANN 9.1.0；msprof 核时 |
| Ascend950PR_957c | SFA forward 61 case；28 core；triton 3.2.0、triton_ascend 3.2.2、CANN 9.1.0、bishengir-compile 1.2.0 |

这些记录提供候选与反例，不新增通用 grid 例外，不豁免当前生成流程的精度和 host 同步约束。实现轮次、无完整参数说明的实验数字及旧口径保留在固定来源中，不作为本卡选型依据。

## 暂存路线与完整路径比较

随机 gather 结果用于 `tl.dot` 时，可在目标环境比较以下候选。先确认输入语义与编译正确性，再评估工作集、重复读取及完整时延；SoC、layout 和重复次数都不能单独决定路线。

| 候选 | 历史观测 | 取用边界 |
|---|---|---|
| 直接 gather 后参与 dot | Ascend910B3 原实现记录了 unmasked 2D gather 的错值或编译失败，以及 masked 路径的额外开销 | 这是原实现的 lowering 问题，不能推定所有 gather→dot 均失败 |
| 内核内 gather 连续化暂存 | Ascend910B3 采用 gather→per-core scratch→仿射消费，原测工作集驻留 L2 | 需确认目标工具链、scratch 生命周期与读写可见性；容量估算不等于已证明驻留 |
| 独立 gather kernel 与 workspace | Ascend910B3 的两个测例劣化；Ascend950PR 的命中子集观察到收益 | 需计入集中搬运、workspace 读写、kernel 串行、重叠损失和重复访问，不能仅测 compute |

可先做 stage/consume 阶段拆解：stage 测随机行搬运，consume 测仿射读取与 QK/softmax/PV，再对照融合实现的完整核时。独立测得的两阶段核时之和不等于融合核时；阶段拆解用于定位访存或布局转换成本，不足以宣布已到硬件上限。

### Ascend910B3：拆分并不总有收益

| 输入 | 内核内暂存 | gather 与 workspace 方案的完整核时 | 差异 |
|---|---|---|---|
| B=64、QS=64、K=512 | 7.198 ms | 9.13～9.87 ms | 劣化 27%～37% |
| B=1、QS=2048、K=2048 | 13.366 ms | 19.2～19.9 ms | 劣化 44%～49% |

原报告称两方案输出 bitequal。该反例提示 workspace HBM 往返及两 kernel 串行可能抵消收益，不构成其他 gather 算子必须采用内核内暂存的规则。

### Ascend950PR：编译边界与重复读取

原 SFA forward 的内核内暂存形态在 bishengir-compile 1.2.0 上遇到 `vector.transfer_write ... permutation_map` 与 `operations cannot be fused`。原实现转向独立 gather kernel，仅 stage K/KR；12 个命中 case 的时延降低 16.5%～33.3%，记录为 bit-exact。

该实现中 `nhb = ceil(n1 / BGU)` 表示读取同一份 K/KR 的 head-block program 数，是 grid 与分块的结果，不是芯片属性。集中搬运可能减少重复随机读取，但还需结合索引 footprint、缓存和搬运成本判断。

- 同一输入仅替换索引的实验中，一个测例的 staged/非 staged 比值从原始索引的 0.700 变为随机索引的 2.264，说明重复次数并不足以保证收益。
- `s2stride == 0` 或 `layout_kv == 'TND'` 都曾被用作代理条件，并出现反方向的回退；不应据 layout 推断数据复用。
- 工作集可驻留 L2 时，内核内暂存值得优先对照；这不是禁止 workspace 的充分条件。内核内方案不可编译也不代表 workspace 必然更快。
- workspace 分配缓存不表示数据可跨调用复用；复用数据前需确认输入与索引未变化。

通用方案见 [离散访存优化](discrete_memory_access.md) 和 [Device-side Gather 连续化](device_side_gather.md)。

## 容量估算与实现边界

对原 fp16 K/KR 暂存结构，单核 scratch 为 `K × (D+DR) × 2 B`，总量另乘核数。`K=512、D=512、DR=64` 时：

- 单核 589824 B，即 576 KiB；20 核共 11796480 B，即 11.25 MiB。
- 若为每个任务物化一份，`64×64` 个任务需 2.25 GiB；`K=2048`、`1×2048` 个任务需 4.50 GiB。

这些值只是该结构的容量换算。L2 驻留、带宽和收益仍需目标环境验证；gather 的地址张量及同时存活的 tile 也需计入 UB，不能仅计算输入数据。

Ascend950PR 原报告的 UB 上限为 253952 B，即 2031616 bits。split kernel 的较大 `BGU`、同时 stage V 等候选曾编译失败，但不能将原实现的参数边界推广为后端通用上限；未附完整分配明细的数字不用于推导单个 tile 大小。

原报告记录：workspace 超过 8 GiB 或分配失败时，历史实现回退哑张量；8 GiB 是该实现的保护值。实际实现应转入已验证且满足输出契约的计算路径；没有可用路径时，应按调用契约报告失败，不能将哑张量作为有效结果。

## 精度补偿与两遍 softmax

### PV hi+lo 是否需要

Ascend910B3 原实现移除 PV 低段后，MERE 为 1.384e-3，超过 `2^-10`；保留后报告为 1e-6 级。Ascend950PR 原实现未观察到同一补偿的精度改善，并记录约 2.7% 降速。这些是不同实现的观测，不能按 SoC 决定其他输入是否启用补偿。

是否采用 hi+lo、native dtype PV 或其他舍入路径，都必须服从目标输入与参考实现的精度契约，见 [Attention 低精度契约](../../guides/tooling/precision_attention_lowprec_contract.md)。

### 两遍方案的候选条件

原 Ascend950PR 实现先求全局 max，再重算 QK，以固定的 fp16 概率参与 PV 与归一化分母累加。这改变了舍入路径，数学上的等价或误差抵消解释不能替代精度验证。

该实现只对 staged、非 split 分支尝试两遍：第二次 K/KR 读取可从连续 workspace 完成；直接 gather 分支增加随机读，split 分支重复求全局 max 也可能增加冗余。这是原实现的候选范围，不是其他 attention 必须使用 `TWO_PASS = staged` 的规则。

历史配对测量中，staged 12 case 的时延比值为 0.768，完整 61 case 为 0.9447。另有删除 softmax 后从 6.0030 ms 降到 2.4484 ms 的消融记录；后者改变了计算内容，不能写成等价两遍方案获得 2.45× 加速。

### 尚未全部通过的精度结果

原报告最终为 **59/61**，失败编号为 #26/#27。报告称厂商 AscendC 对同一 golden 也越阈，且观察到相同误差；这属于排查线索，不足以单独证明失败由输出量化造成，也不能把失败改记为通过。

新实现必须按原验收规则报告全部输入与失败项，不排除 case，不放宽阈值。更多 attention 结构经验见 [FlashAttention 优化卡](flash_attention_optimization.md)。

## 退化索引恒等式的取用范围

若同一输出行的所有有效索引都指向同一合法 V，存在有效项、对应 score 有限，且输出确为归一化加权和，则实数算术下输出等于该 V。原报告在索引全同一、`layout_kv == 'TND'`、LSE 关闭且 key/query dtype 相同的测试子集上观察到位精确一致。

该恒等式不自动保证浮点实现逐位一致。采用前还需确认行映射、有效性掩码、额外输出及参考实现的舍入契约；不能仅凭 layout 推定索引全同一，也不能将测试集的数据事实视作算子输入保证。

当前编码流程禁止把输入数据经 `.item()` 读回 host 决定实现。本卡不推荐原报告的 host 探测守卫；没有符合当前流程、已验证的适用条件时，不采用该短路。

## 编译失败记录与 grid 边界

原 Ascend950PR 实现把 head-block 放进 2D/3D grid，并记录外层 head loop 改写的编译失败。该记录不能证明压平为一维 grid 的替代实现都不可行，也不足以为当前通用规范增加例外。

因此本卡只保留历史观测，**不将多维 grid 实现作为已准入方案**。目标实现须遵守当前生成流程；如确需申请例外，应另行提供具体替代实现、目标工具链的编译与正确性结果，以及同输入、同口径的对照证据。

## 目标环境的验证要求

1. 确认随机索引、KV 共享及 MLA-absorb 语义；页内连续形态不套用本卡的随机 gather 方案。
2. 编译并验证候选完整路径，覆盖非法索引与填充、边界 shape、dtype 和必要的额外输出；触发 workspace 超限或分配失败时，检查返回状态和输出，确认哑张量不会被当作有效结果。工具链变化后重新验证，历史成功或失败均不自动延续。
3. 做同输入的完整路径 A/B，包含 gather、workspace 读写、守卫、分配与回退成本；不同批次的汇总值不直接相减，报告逐 case 失败与回退。
4. 结构、grid、分块或缓存策略变化后，重新判断工作集与收益，不复用旧实现的最优参数或失败结论。
