---
type: Optimization
title: 'F5: cv_split_fa:ring_iteration_cost:gm_bytes_bound'
description: CV 分离（AIC 算 QK^T/P@V，AIV 算 softmax，S/P 经 GM workspace 中转）的 FA 内核，
tags:
- task.debugging
- topic.data_movement
- topic.programming_model
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/4917980395de8b8703aa7ec62213fafbe7bec01e/plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/runbooks/failure-patterns/f5-cv-split-fa-ring-cost-equals-gm-bytes.md
  role: evidence
created_at: '2026-10-29T20:40:00Z'
updated_at: '2026-10-30T13:20:00Z'
platforms:
- a2
- a3
---

# F5: cv_split_fa:ring_iteration_cost:gm_bytes_bound

> 进化失败模式元数据（迁移自旧 OKF，机器可读副本见 ascendc-evolution-knowledge/references/okf_compat.json）：
> key: "cv_split_fa:ring_iteration_cost:gm_bytes_bound"
> phenomenon: performance_negative
> severity: major
> failed_combination: ["P122", "P18", "X38"]
> operator_type: ["attention", "flash_attention"]
> occurrences: 2

## Symptom
CV 分离（AIC 算 QK^T/P@V，AIV 算 softmax，S/P 经 GM workspace 中转）的 FA 内核，
对其施加「加深 ring 在飞深度」「放大 KV tile（BLOCK_N）」「把 AIC 侧 GM 搬运点前移」三类改动，
性能均为中性或为负：
- RING 3→4 + PRELAUNCH 2→3：机制生效（aic/aiv scalar 各降 4~7pp）但同窗口 A/B −0.15%（中性）；
- D=256 层 BLOCK_N 128→256 + kv_slots 2→1：−1.79%（13 个 D=256 case 慢 3~20%）；改 K 单槽/V 双槽非对称只收回一半（−0.96%）；
- 把 ws_p 的 GM→L1 读 + SIG_P_READY 等待从 C2 前端提前到 C1 之前（纯调度、零算术）：−1.29%。

## Root cause class
带宽/字节账 —— 不是固定握手开销、也不是 AIC 搬运点位置问题。

四档独立 tile 配置（bm=128/bn=256/da=128、bm=80/bn=128/da=256、bm=128/bn=256/da=64、bm=16/bn=256/da=128 decode）
的「实测 us/迭代 ÷ 每核 GM 字节」全部落在 **55–80 GB/s** 同一区间：

| 档位 | 字节/迭代 | 实测 us/迭代 | 有效带宽 |
|---|---|---|---|
| bm=128 bn=256 da=128（≈30 case） | 384 KB | 4.7–5.3 | 72–82 GB/s |
| bm=80 bn=128 da=256（D=256 档） | 208 KB | 2.8–3.1 | 67–74 GB/s |
| bm=128 bn=256 da=64（D=64 case） | 320 KB | 7.3 | 44 GB/s |
| bm=16 bn=256 da=128（decode） | 160 KB | 2.9 | 55 GB/s |

即 **ring 单迭代成本 ≈ 每核 GM 字节 / (55–80 GB/s)**，与 ring 深度、握手条数、搬运点位置都无关。
每 score 的 12B 中，ws_s 往返 4B + ws_p 往返 4B = 8B，K/V 只占 4B → 真正的杠杆是「减少 ws 往返字节」，
而不是调度类改动。

## Failed combination
- P122 / P18（KV 大块化 / 双缓冲）+ X38（KV-tile 宽度缩放）：在本内核上放大 BLOCK_N 必然挤掉 K/V 双槽（L1 512KB 装不下），
  字节/score 不变而预取重叠丢失。
- P14 / P125（预发射 / 跨任务预取）延伸的「ring 加深」：字节不变 → 时间不变。
- 任何「把 AIC 侧 ws_p 读前移」的软件流水重排：AIC 搬运点本来就不在临界路径。

## Resolution
1. 先做字节账：`每核 GM 字节 = K bn*da*2 + V bn*da*2 + ws_s 2*(bm*bn*2) + ws_p 2*(bm*bn*2)`，除以实测 us/迭代，
   若落在 55–80 GB/s 区间即判定为带宽受限，**停止调度类优化**。
2. 只能从字节侧下手：跳过被 mask 掉的列（causal 对角块 N 收缩）、减少 S/P 通道、或提高 block_m（受 L0C/UB 限制）。
3. 若确实要放大 BLOCK_N，必须同时保住 K 与 V 的双槽预取（L1 预算 ≤ 480KB），否则净收益为负。

## Evidence
- 105_FusedInferAttentionScoreTorch_evo_20261029_162830（Ascend910_9391 / DAV-C220，24 AIC）：
  round_1 parallel_2（ws_p 前移）26.5147x vs 种子 26.8615x；round_1 parallel_1（BLOCK_N=256+单槽）26.3798x；
  round_2 parallel_1（非对称槽）26.6049x；round_1 parallel_0（ring 3→4 的上游会话）同窗口 A/B −0.15%。


## 2026-10-30 更新（105_FusedInferAttentionScoreTorch 第二轮进化，910B2C / 24 AIC）

同一算子上对上面三类改动之外的**四类新改动**做了同窗口实测，f5 的"字节账"结论需要两条重要修正：

| 改动 | 每 score 字节 | 同窗口结果 | 结论 |
|---|---|---|---|
| K/V L1 槽位 2→3 + 预取 lead 1→2（D=256 K3V3 / D<=128 K3V2，事件 id 重排） | 不变 | certify 764.19us vs 种子 763.32（+0.10%）；A/B 两组互相矛盾（±噪声） | 字节不变 ⇒ 时间不变，**再一次**确认 |
| ws_s/ws_p 合成单通道（AIV 原地覆写 S 槽，环足迹 12MB→6MB） | 不变 | certify 757.60us vs 同窗口种子 763.46（-0.77%）；20 例 interleaved A/B 0.998（中性） | 足迹/L2 容量不是约束；-0.77% 在 ±1% 漂移内，不可当稳定收益 |
| D=256 层 block_m 80→96（S 的 L0C 分块 128→64 列；L0C 122.9KB 合规） | 20.8→18.4B（-11.5%） | 13 个 D=256 case 同窗口 A/B geo **+3.46%（变慢）**；D<=128 对照持平 | **减字节但增加迭代内事件（mma 2→4、FIX 1→2）⇒ 净负** |
| decode 欠核 split-KV（Sq==1，splits=2/3，SyncAll + fp32 合并，50/50 PASS） | 不变 | case1 57.9→48.9us（+18%），case0 持平，全量 -1.0%（中性） | 并行度不是该形状的主约束（launch/爬坡地板） |

由此得到两条比 f5 原文更精确的判据：

1. **有效带宽是窗口相关的**：同一台 910B2C 在 3 个 lane 并发（compare-batch pipeline 补采）时会从 ~145GB/s 掉到 55–80GB/s，绝对时延被抬高 ~1.9x。f5 原文的 55–80GB/s 是在拥挤窗口测的，**跨窗口的带宽数字不可迁移**；安静窗口实测为每核 ~145GB/s（24 核 ≈ 3.5TB/s，高于 HBM 峰值 ⇒ ring 流量主要由 L2 承担）。
2. **只有"字节与迭代内事件数同向"的改动才线性换时间**：D=256 层的最高管道是 aic_scalar 0.889（MTE2 仅 0.692），该层每多一个迭代内事件约 +0.7%；S 分块 128→64 单独（字节不变）就已 -3.46%。而 bm=96 还需要 Q 离开 L0A 常驻（L0A：`d_chunks*bm*128 + bm*128` fp16 ≤ 64KB 也把 bm 卡在 85），非驻留 Q 重填只有 `PipeBarrier<PIPE_ALL>` 能过（否则 aicore 507015 L0A read/write conflict，与 f4 一致），代价 ~35%。
3. **正确的 K/V 字节杠杆是跨 q-block 的 K/V 复用（任务合并，不增加迭代内事件）**：同一算子的 host-only 调度改动（m_group ∈ {4,2,1} × {contiguous, strided} 联合枚举、删掉 kv_end 等长门控）拿到 certify -1.48% / A/B -2.5%，见 OKF X65。
