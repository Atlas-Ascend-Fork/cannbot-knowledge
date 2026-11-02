---
type: Runbook
title: "参考算子偏离 CPU 规格时：先冻结验收依据，再分列精度结论"
description: "区分 CPU 数学真值合同与显式 CANN 输出兼容合同；固定同输入、同序 first/repeat 或 warm/timed 参考、比较器和完整分母。CPU64 诊断不暗中叠加为 CANN 主门禁，容差通过不等于原始摘要相同；保留旧失败与不同依据的结果。"
tags:
- task.design
- topic.architecture
status: draft
sources: []
created_at: "2026-09-16T00:00:00Z"
updated_at: "2026-10-21T10:19:29Z"
platforms: ["950"]
aliases: ["OL-319"]
---

# OL-319 — OL-319: A5Ops additive extension

> **来源说明（2026-10-15）**：本卡内容来自车队私有实测/推理，暂无可公开复核的原始出处；按社区评审要求降为 draft，待补可复核来源后回升。
## 适用场景

- 适用范围：参考依据与比较器的组织方法；不从本卡推导任意 SoC/CANN 的数值行为、允许切换参考的项目权限或原生实现等价关系。
- 验证来源：2_FFN bf16 inner_precise=0 + fp16 ip=1 cases (2026-07-25/26, Ascend910_9382, CANN 9.0.0)。

**OL-319** — 参考与 CPU 规格不一致时，先确认当前任务究竟验收数学精度还是已明确允许的参考输出兼容性。二者是不同判定依据，不能自动互换；CPU 两层判据只适用于声明该判据的合同。

- Former A5Ops ID: `OL-319`
- Fusion disposition: `additive_new`

`applies_to: declared oracle/grader contract; no silicon-wide numerical claim`
`verified_on: 2_FFN bf16 inner_precise=0 + fp16 ip=1 cases (2026-07-25/26, Ascend910_9382, CANN 9.0.0)`

**CPU 数学真值合同**：候选与参考分别对独立 CPU 规格计算误差。只有任务原先声明了两层判据时，才继续检查 `ours_err <= ref_err`；否则按原阈值保留各自结论。参考失败不证明候选正确，也不能单凭差异认定参考的具体实现缺陷。下面的历史 FFN 案例保留为这一口径的来源叙述，仍受开头的 draft 证据边界限制。

## 显式参考输出合同的配对方法

触发条件是任务已在本轮执行前明确允许以实际 CANN 返回作为兼容性验收依据，且数学规格诊断与主验收分别记录。本卡不授予这种权限，也不把 CANN 输出称为高精度数学真值。

1. 冻结参考实现/Model、候选源与 DSO、运行时 provider、比较器版本、dtype/shape、完整输入分母和参考关系。先声明哪些比较决定主状态；旧 CPU 严格合同继续保留。
2. 对每例保存同一份实际输入的值摘要、布局和属性，交给候选与参考。P 的 `candidate_first` 只配 `reference_first`，repeat 同序配对；Q 的 warm/timed、重复序号和计时臂分别标识。不能用缓存旧输出、最佳参考或另一输入代替当前配对。
3. 消费者先验证完整返回结构、dtype/shape、输入关联、候选和参考的实际输出摘要、源/provider 身份，再对每个输出执行冻结的比较器。缺少规定的配对参考时，主结果保留 ERROR/NOT_RUN，不能用 CPU 诊断填补。
4. CPU 高精度实现独立读取同一实际输入，输出另列为诊断。若合同明确其不参与主验收，诊断 FAIL、不可用或内部错误不应偷偷成为 `CANN_PASS AND CPU_PASS`；这些问题仍须完整披露。若合同要求 CPU 真值，则不能套用此分离方式绕过失败。
5. 分别汇总“候选对 CANN”“候选对 CPU”“CANN 对 CPU”的计数、误差及缺失项。同一 Model 包装的 CANN 调用是一条参考路径，不能计作 Model 与裸 CANN 两份独立验证。原始 SHA 相同可证明有限输入的字节身份；容差通过允许 SHA 不同，二者不是冲突。
6. 新参考依据只作用于新冻结的一轮。保持旧失败、花费和原比较口径，不追溯改判；新源/DSO仍要自己的完整 P/Q。性能使用该轮预先声明的时间域、配对和分母，不能把不同精度路线的跨轮差异归因为某一算术步骤。

这一方法补充的是验收依据和消费者状态的边界，不修改 CPU 真值标准或比较器阈值。公开 CANN 源码可提供移植线索；只有算子名、源码相似或 provider 哈希，均不能建立所读源码与商业二进制选中内核的对应关系。编译通过、静态 dtype 推导、有限例兼容通过，也不证明全域精度、唯一性能原因或新消费者复现。

## 历史 CPU 真值案例与未验证边界

**Concrete anchor (2_FFN, bf16 `inner_precise=0`)**: the npu_ffn docstring says ip=0 means fp32 inner compute. Measured on 220x / CANN 9.0.0: ref-vs-CPU-truth MARE = 2e+1..1.2e+3 (the vendor op does something else, likely reduced-precision inner), while our kernel-vs-truth MARE = 6e-3..2e-1. An inline cand-vs-ref comparison FAILs these cases by construction — it would be grading against a reference that is itself 3 orders of magnitude off its own spec. Same shape on pseudo-quant (ref-vs-truth 1.3e+3).

**Companion aliasing hazard**: fp16 `max_abs_diff = 32` is 1 ULP at |y| ~ 32768 (fp16 ULP at 32768 is exactly 32) — a repeated identical max_abs=32 across cases is ULP-at-large-magnitude + small-value MARE aliasing, not a kernel bug. Check magnitude before treating a big absolute diff as a defect.

**Evidence**: 2_FFN (2026-07-25/26): bf16 ip=0 ref-vs-truth MARE 2e+1..1.2e+3 vs docstring spec; 8 fp16 cases with uniform max_abs=32 resolved as 1-ULP at |y|~32768 (MERE 1e-6..4e-5). Two-tier ladder adjudicated both correctly; inline comparison would have mis-failed both.

**Other instances (predicted)**: fused/precision-reduced vendor implementations may differ from a mathematical decomposition. This is a diagnostic hypothesis, not proof of a particular native kernel path. Check same-input reference-vs-truth evidence, then retain the declared contract or explicitly freeze an authorized new one; do not automatically switch the verdict. The historical numerical observations above have no new public-source validation in this revision.
