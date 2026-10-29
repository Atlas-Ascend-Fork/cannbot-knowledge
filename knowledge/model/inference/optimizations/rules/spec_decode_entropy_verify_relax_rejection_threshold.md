---
type: Optimization
title: 投机解码接受率低时用熵校验放松拒绝采样阈值：threshold = min(exp(-H·α), posterior_threshold)
description: 投机解码/MTP 接受率低时用熵校验（entropy verify）放松拒绝采样阈值以提升接受率与端到端加速比。把标准接受判据 target_prob/draft_prob >= u 改为 >= threshold·u，其中 threshold = min(exp(-H·posterior_alpha), posterior_threshold)、H 为目标分布的熵：目标分布越不确定(高熵)→threshold 越小→越易接受，低熵时放松程度较小，但默认 posterior_threshold=0.95 时仍会放松。熵须在未裁剪的原始目标分布 ori_target_probs 上计算。与 block verify(cumprod 累积概率块判定)正交可叠加；n-gram 等 draft-prob-free 方法 draft_prob=1.0 时同样放松高熵 token。这是用少量采样精度换接受率的 trade-off：posterior_alpha 越大越激进、接受率越高但精度越低。参考实现为昇腾推理后端 vllm-ascend 的 rejection_sampler_config（enable_entropy_verify / enable_block_verify / posterior_threshold=0.95 / posterior_alpha=0.4），提供 Triton kernel 与 PyTorch fallback 两路径；熵 kernel 需遍历整个词表算 -Σp·log(p+ε)，单算子耗时可上升约 21×，可用 SUB_BLOCK 分块粒度旋钮部分回收。算法为采样/验证数学层、硬件无关。仓自报 benchmark：DeepSeek-V4-Flash-w8a8-mtp、Qwen3.5-397B/122B w8a8-mtp 上接受率与投机接受长度上升、多数配置 TPS 提升(无独立复测)。
tags:
- task.optimization
- topic.speculative_decoding
- topic.precision
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/9047
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-10-22T10:41:21Z'
platforms:
- agnostic
---

# 投机解码接受率低时用熵校验放松拒绝采样阈值：threshold = min(exp(-H·α), posterior_threshold)

## 适用场景

- workload：投机解码 / MTP（[mtp-speculative-decoding](../../concepts/techniques/mtp_speculative_decoding.md)）的 decode 阶段，target 模型对 draft token 做拒绝采样验证，接受率偏低拖累端到端加速比。
- 判断通向本规则：投机解码的端到端加速比由**接受率**主导——一次前向验证放行的 token 越多，等效 per-token 时延（TPOT）越低、TPS 越高。标准拒绝采样判据 `target_prob/draft_prob >= u`（`u` 为均匀采样量）在数学上严格保持目标分布，但接受率有天花板。当你观测到「投机长度设了 K，实际投机接受长度远小于 K」「接受率明显低于预期」而模型本身容忍极小采样偏差时，可用**熵校验（entropy verify）**在牺牲少量采样精度下系统性抬升接受率。
- 前提 / 何时不适用：这是**用精度换接受率**的 trade-off，不是无损优化。对精度敏感、不能接受输出分布小幅漂移的场景不要开；接受率已接近 1 或 decode 已计算 bound 时收益有限。

## 条件 → 优先尝试什么

- **核心思想**：把标准接受判据里的均匀量 `u` 乘一个 `threshold ∈ (0,1]` 再比较，即
  `target_prob/draft_prob >= threshold · u`。`threshold ≤ 1` 恒使接受更容易；`threshold` 由**目标分布的熵 H** 动态决定：目标分布越不确定（高熵）→ `threshold` 越小 → 越易接受；目标分布越确定（低熵、单峰）→ `threshold` 越接近上界 → 越严格。
- **为何有效**：当目标分布本身很不确定（高熵、多个候选 token 概率接近）时，放松对 draft token 的接受几乎不改变输出质量；反之目标分布很确定（低熵）时应保持严格。熵把「这一步值不值得放松」量化成了一个逐 token 的阈值旋钮，从而把接受率增益集中在几乎不损精度的位置。
- **阈值公式**（逐 token）：
  ```
  threshold = min( exp(-H · posterior_alpha), posterior_threshold )
  ```
  - `H` = 目标分布的熵；
  - `posterior_alpha (α) ≥ 0`：熵对阈值的缩放系数，越大越激进（高熵 token 阈值压得越低 → 接受率越高、精度损失越大）；
  - `posterior_threshold ∈ (0,1]`：熵调整后阈值的**上界**。按此公式，即使 H=0，默认值 0.95 也会使阈值低于标准拒绝采样的 1，仍然放松接受条件；它不能保证低熵位置保持原判据。
- **算法（PyTorch 参考实现，逐 token）**：
  ```python
  EPSILON = 1e-10
  entropy = -(all_target_dist * torch.log(all_target_dist + EPSILON)).sum(dim=-1)   # H
  exp_neg_entropy = torch.exp(-entropy * POSTERIOR_ALPHA)
  threshold = torch.minimum(exp_neg_entropy, posterior_threshold_device)            # min(exp(-H·α), posterior_threshold)
  modified_uniform_token_probs = threshold * uniform_token_probs                     # threshold · u
  acceptance_condition = (draft_token_probs > 0) & \
      (target_token_probs / draft_token_probs >= modified_uniform_token_probs)
  ```
- **熵必须在原始目标分布上算**：熵在**未经 reduce/裁剪的原始目标分布** `ori_target_probs` 上计算，参考实现专门把 `raw_target_logits` 透传为 `ori_target_logits`、`softmax` 得 `ori_target_probs` 供熵用；只有拿不到原始分布时才退回当前已处理的 `target_probs`。用被裁剪过的分布算熵会低估不确定度、削弱增益。
- **与 block verify 正交可叠加**：block verify 把整块 draft token 当一个块，用累积概率乘积判定（`pi = cumprod(clamp(target/draft, max=1))`，判 `pi >= cumprod(u)`）而非逐 token；叠加熵校验时对 `cumprod(u)` 乘同一 `threshold`。block verify 主要提接受率，熵校验叠加进一步小幅提接受率与投机接受长度。
- **draft-prob-free 方法（如 n-gram）**：`draft_probs=None`、draft_prob 取 1.0，接受只由 target_prob 决定；熵校验同样对高熵 token 放松其阈值。

## 依据（支撑的 case，仓自报 benchmark，无独立复测）

参考实现的自报表格（投机长度=3，仓自报口径、无独立复测），趋势一致：block verify 主要提接受率，熵校验叠加进一步小幅提接受率与投机接受长度，`α` 增大放大接受率增益但压低精度。

- **DeepSeek-V4-Flash-w8a8-mtp**：接受率 67.60%（baseline）→ 69.03%（block）→ 69.95%（block+熵）→ 70.12%（block+熵，α=1）；投机接受长度 2.03→2.12；TPS 1725→约 1844。
- **Qwen3.5-397B-A17B-w8a8-mtp**（α=0.4）：接受率 80.13%→87.14%（block）→87.60%（block+熵）；投机接受长度 2.40→2.63；TPS 1861→2051；block+熵组 5 次复测精度均值 85.66%。
- **Qwen3.5-122B-A10B**（α=0.4）：接受率 77.34%→90.52%（block）→91.58%（block+熵）；α=1.0 时进一步到 93.59%、投机接受长度 2.81，但精度从 α=0.4 档降到 79.80%——印证 α 越大越提接受率越损精度。

接受率与实际加速的换算、以及 MTP 等效时延的正确度量口径，见 [mtp-benefit-sparse-attention-and-latency-metric](../cases/mtp_benefit_sparse_attention_and_latency_metric.md)。

## 反例 / 代价

- **不是无损**：这是精度换接受率。参考实现文档明确把 `α` / 阈值标为精度/性能 trade-off，须按模型权重与场景调参；α 过大会显著掉精度（如上 Qwen3.5-122B-A10B α=1.0 掉到 79.80%）。
- **熵 kernel 单算子耗时可能大幅上升**：熵校验分支需按分块粒度遍历**整个词表**做 `-Σ p·log(p+ε)`，比原本只读单个 token 概率多一整趟全词表 load+归约。参考实现 Triton kernel 上算子级观测：`rejection_random_sample_kernel` 8700ns（熵关）→约 186740ns（熵开），约 21×；把分块粒度旋钮 `SUB_BLOCK` 从默认 4*1024 增大到 8*1024 可部分回收到约 145380ns。故在词表极大的模型上，接受率增益可能被熵计算的算子开销部分抵消，需实测净收益，并用分块粒度旋钮回收。
- 接受率已接近 1 或 decode 已计算 bound 时收益有限——投机解码用相近数据搬运换更多计算，计算已满时放宽接受意义不大。

## 参考实现及其约束

- 参考实现：昇腾推理后端 vllm-ascend（[sglang](../../concepts/frameworks/sglang.md) 之外的另一投机解码宿主框架），配置通过 `additional_config.rejection_sampler_config` 下发：
  - `enable_entropy_verify: bool = False`
  - `enable_block_verify: bool = False`（正交优化，需投机长度 `max_spec_len >= 3`，现由该开关显式使能，此前隐式条件是 `draft_probs is not None`）
  - `posterior_threshold: float = 0.95`（必须 ∈ (0,1]）
  - `posterior_alpha: float = 0.4`（必须 ≥0）
- 同时提供 Triton kernel 与 PyTorch fallback 两条路径，行为一致；上文公式在两条路径与文档三处一致对上。
- **约束边界**：以上开关名 / 默认值 / 需 `max_spec_len >= 3`、`SUB_BLOCK` 回收旋钮，是该参考实现的工程约束，**不是熵校验算法本身的限制**。算法为采样/验证数学层、硬件无关；昇腾侧只是其参考实现之一，公式 `threshold = min(exp(-H·α), posterior_threshold)` 与逐 token 接受判据可迁移到任何投机解码拒绝采样实现。

## Evidence

- 核心断言（阈值公式、配置字段与校验、开关语义、熵在原始分布上计算、block verify 叠加方式、n-gram draft-prob-free 处理）为合并态 diff 事实：`rejection_sampler.py` 两条 PyTorch fallback 的 ENTROPY_VERIFY 分支、`reject_sample.py` Triton kernel 的熵计算分支、`ascend_config.py` 的 `RejectionSamplerConfig` 校验、`speculative_decoding.md` 语义三处一致。
- 熵 kernel 全词表遍历与 `SUB_BLOCK` 回收为合并态 diff 事实（`reject_sample.py` 的 `if ENTROPY_VERIFY:` 分块循环 + `SUB_BLOCK` 常量），非推断。
- benchmark 数字取自参考实现 PR body 自报表格，**无独立复测**，仅陈述报告内这几组配置、不外推单调规律。
- 合并 sha `77ff28652b`；溯源下探：
  - [投机解码接受率低时用熵校验-entropy-verify-放松拒绝采样阈值-threshold-min-exp-h-po](https://github.com/vllm-project/vllm-ascend/issues/9047)
  - [熵校验-magicmtp-在-deepseek-v4-flash-qwen3-5-moe-w8a8-mtp-上的自报接受](https://github.com/vllm-project/vllm-ascend/issues/9047)
