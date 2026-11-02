---
type: Runbook
title: MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标
description: MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标。给开启 MTP（多 token 预测 / 投机解码）的 decode 采集时延统计时，日志里的 decode 时延数值失真——无报错、无异常，只是数不对：单步耗时被系统性低估、按记录数算的平均和 IQR 离群过滤口径被打乱、拿到一个含义模糊的 "average inference time cost" 分不清是每步还是每 token。
tags:
- task.debugging
- topic.speculative_decoding
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/61
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- agnostic
---

# MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标

## 信号（现象）

给开启 [MTP](../../concepts/techniques/mtp_speculative_decoding.md)（多 token 预测 / 投机解码）的 decode 采集时延统计时，日志里的 decode 时延数值失真——无报错、无异常，只是数不对：单步耗时被系统性低估、按记录数算的平均和 IQR 离群过滤口径被打乱、拿到一个含义模糊的 "average inference time cost" 分不清是每步还是每 token。

## 适用场景

用于检查 MTP/投机解码的计时采集粒度、分母和统计窗口。通用部分关注 main 与全部 draft 的完整步骤；下文 Kimi K3 专节限定 950PR/DT 的 DSpark 固定批次实现。先核对具体循环和日志采集位置，不把一种草稿时序当成全部模型的统一实现。本卡未提供本轮硬件时延或加速结果。

## 触发条件 / 根因

一个 decode 步 = 1 次 main 前向 + `next_n` 次 draft(MTP) 前向，产出 `1 + accepted_num` 个 token。若计时采集有以下缺陷即失真：

1. **只回传最后一个 draft 步的耗时**：draft 循环里把当轮耗时赋给标量、每轮覆盖，结束只返回最后一轮 → 前 `next_n-1` 个 draft 前向耗时被丢弃，单步耗时被低估。
2. **main 与 draft 耗时被拆成两条独立记录追加**：于是 `len(rec) == 2 × 步数`，每条记录只是「半个 step」（纯 main 或单个 draft），混进按记录数的平均（`总时间 / token_count`，`avg_token_per_round = token_count / len(rec)`）与 IQR 离群过滤，统计口径被打乱。
3. **只输出一个泛化标注的时延**：无法区分「每 decode 步时延」与「每生成 token 时延」这两个语义不同的量。

## 修法

- **累加一个 decode 步内所有 draft 前向的耗时**（把「返回标量」改成「返回逐步耗时 list」），不要只留最后一个。
- **每个 decode 步记一条完整耗时** `infer_time_main + sum(所有 draft 步耗时)`，令 `len(rec) == 步数`，使按记录的平均与 IQR 离群过滤口径正确。
- **分两个语义不同的指标上报**：
  - 每步平均时延 = 总时间 / 步数；
  - MTP-N 等效单 token 时延 = 总时间 / 生成 token 数（`total_tokens = 被接受的 draft token 数 + main token 数`）——反映投机解码相对单 token 解码的加速收益。

## Kimi K3：实际接受长度、参考分母与 Proposal/Verify 配对

以下实现边界限定在 950PR/DT 的固定批次 DSpark 路线。通用 MTP“一个 main 加多个 draft 前向”与 DSpark“Proposal 后由下一次 Verify 验证”不能机械采用同一个数组下标规则。入口是 `model_infer.py` 的 `_speculative_round_times`、`_decode_timing_skip_rounds`、`_log_acceptance_stats` 和 Verify 后的统计汇总。

### 先还原一次完整投机轮

主模型第一次调用先建立 anchor，此时还没有可验证的 DSpark proposal。随后才执行 Proposal P0，再由下一次主模型调用 V1 验证；后面依次为 P1→V2、P2→V3。请求结束时还可能留下未验证的尾部 proposal。

因此，令主模型耗时数组为 `decode_times`，草稿耗时数组为 `draft_times`，完整轮数是 `min(max(len(decode_times)-1, 0), len(draft_times))`。第 i 个完整轮的耗时为 `draft_times[i] + decode_times[i+1]`。完整配对函数如下；只有列表切片，无模型依赖：

```python
@staticmethod
def _speculative_round_times(decode_times, draft_times, skip_rounds=0):
    # The first main-model Decode bootstraps the anchor before DSpark has
    # proposed anything. A trailing proposal may likewise remain unverified.
    round_count = min(max(len(decode_times) - 1, 0), len(draft_times))
    first_round = min(max(skip_rounds, 0), round_count)
    return (
        decode_times[first_round + 1 : round_count + 1],
        draft_times[first_round:round_count],
    )
```

读用时先检查返回的两份列表等长；启动 anchor 和未验证尾部都没有进入完整轮。不要把“两个列表长度碰巧相同”当成应按同下标配对的理由，也不要把最后一次未验证 proposal 当作产出完整 token 的一轮。

### 区分四个统计量

| 量 | 定义 | 不能混用的口径 |
|---|---|---|
| 平均完整轮耗时 `T_round` | 配对窗口中 Verify 与 Proposal 耗时之和，除以完整轮数 | 不是单次 Verify，也不是单 token 时延 |
| 实际平均接受长度 `L_actual` | `A/V + 1`；A 是接受的 draft token 累计数，V 是 Verify 中被统计的请求行数 | 不是接受率，也不一定是全局图调用次数 |
| draft 接受率 `r` | `A/(V*next_n)` | 分母是候选 draft 槽数，不包含主模型补充 token |
| 参考接受长度 `L_fixed` | 人工固定的展示分母 | 不表示本次请求实际接受了这么多 token |

`verify_count` 在 Verify 的 active 请求行循环内累计；一次 batched Verify 可统计多行。不要从这个变量名推断它等于主模型调用轮数。`+1` 是日志归一所采用的主模型 token 口径，生成结束、EOS 截断和实际输出长度还需看真实提交结果，不能反过来用它替代端到端 token 计数。

日志等效指标为 `T_round/L_actual`。如果 T 的单位是秒，输出 ms 还要乘 `1000`。完整轮数为零时，函数返回空列表，汇总不会构造平均轮耗时；`V=0` 时接受长度与接受率为零，不能进行正向收益解读。

### 原样统计实现与显示差异

有的实现把固定分母 `3.85` 称为 `official acceptance length`；另一显示方式改称 `fixed acceptance length` 并使用 `4`。下面保留后一版完整方法，依赖原类的 `attn_tp_group`、rank、`next_n`、device、model_runner 及 `torch.distributed`；这段只说明日志语义，不是本轮运行输出：

```python
def _log_acceptance_stats(
    self, stats: DSparkAcceptanceStats, average_round_time=None
):
    if dist.is_initialized():
        totals = torch.tensor(
            [stats.total_accepted_tokens, stats.verify_count],
            dtype=torch.int64,
            device=self.device,
        )
        dist.all_reduce(totals, group=self.attn_tp_group)
        total_accepted_tokens, verify_count = totals.tolist()
    else:
        total_accepted_tokens = stats.total_accepted_tokens
        verify_count = stats.verify_count
    if self.attn_tp_rank != 0:
        return
    total_spec_tokens = verify_count * self.next_n
    accept_length = (
        total_accepted_tokens / verify_count + 1
        if verify_count
        else 0.0
    )
    accept_rate = (
        total_accepted_tokens / total_spec_tokens
        if total_spec_tokens
        else 0.0
    )
    logging.info("The speculation accept length: %.4f", accept_length)
    logging.info("The speculation accept rate: %.4f", accept_rate)
    if average_round_time is not None:
        if accept_length > 0:
            logging.info(
                "%s model average equivalent latency with actual acceptance "
                "length %.4f is %.2f ms",
                self.model_runner.model_name,
                accept_length,
                average_round_time / accept_length * 1000,
            )
        reference_accept_length = 4
        logging.info(
            "%s model average equivalent latency with fixed acceptance "
            "length %d is %.2f ms",
            self.model_runner.model_name,
            reference_accept_length,
            average_round_time / reference_accept_length * 1000,
        )
```

固定分母从 `3.85` 改为 `4`，在相同 `T_round` 下参考值按 `3.85/4` 改变，但计算图、实际接受长度和真实产出均可能完全不变。因此比较日志时先对齐分母标签，不能把数值下降归因为模型加速；也不能将这个固定参考值外推成其他模型的接受长度。

### 稳态窗口必须与产出窗口对齐

该实现还会从耗时列表排除启动轮及 profiler 活跃窗口。下面完整 helper 依赖类中的启动跳过轮数、profiler 活跃轮数和开关：

```python
def _decode_timing_skip_rounds(self):
    # Profiler skip_first rounds also serve as startup stabilization. Its
    # active rounds carry instrumentation overhead and are excluded too.
    skipped = self.DECODE_STARTUP_SKIP_ROUNDS
    if self.enable_profiler:
        skipped += self.DECODE_PROFILE_ACTIVE_ROUNDS
    return skipped
```

但接受计数仍可来自整次生成，不能静默假设它与截取后的耗时样本相同。若要严格稳定阶段 TPOT，应对同一请求集合、同一时间窗口统计耗时与实际提交 token，并交代 EOS、长度上限及已结束请求如何计数。整次接受长度归一的结果只能按其真实范围解释为日志等效指标。

### 判别、验收与坏实践

1. 从采集点确认每条记录对应 main、draft、Proposal、Verify 还是完整轮；先确定对象，再谈平均。
2. 检查 `_speculative_round_times` 对 anchor、尾部和 `skip_rounds` 的处理，核对两份保留列表的长度与对应关系。
3. 检查接受计数的更新位置、分布式归约组和实际输出 rank；不要把不同 owner/rank 的统计再次无条件求和。
4. 对齐 actual/fixed 分母、计时单位、warmup/profiler 开关与采样窗口。任一口径变化都需在性能比较中单独标记。
5. 使用捕获的真实逐轮记录重算，验证配对总时长和实际提交 token 的统计。不以修改参考分母、删除失败请求或扩大离群剔除范围制造加速结果。

### 已有核对与未验证项

本轮核对的是固定代码中的切片、分母与统计窗口，未执行上游推理或复测性能；没有修前/修后 benchmark 可供宣称收益。迁移时若部署代码的 Proposal/Verify 时序不同，应先恢复实际时间线，不套用这里的 `i+1`。

## 可迁移原则

- 给投机解码 / MTP 做计时：一个 decode 步 = 1 main + N draft，**别只计一个 draft、别把 main 与 draft 拆成两条「半步」记录**，否则按记录数的平均与离群过滤全部失真。每步一条 `main + sum(draft)` 完整记录是正确的采集粒度。
- 投机解码要分「每步时延」与「等效单 token 时延」两个口径报——前者是执行开销、后者才反映加速收益，混用会读错加速比。
- 这类缺陷静默失真（不 crash），只能靠核对采集逻辑发现；性能回归时若 MTP 时延数飘忽 / 不合理，先查采集粒度。

## 参考实现及其约束

参考 cann-recipes-infer DeepSeek-V3.2-Exp（[deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md)）的 MTP 计时路径（`model_infer.py` 的 `mtp_post_process` / `obtain_mtp_stats`、executor 的 `process_infer_time`：跳过首条 prefill、按 IQR 上界剔离群后返回 `总时间 / token_count`）。等效单 token 时延的**归一基数**另有讲究（取稳态平均接受数而非首 batch）见下「相关经验」。源未给修复前后 ms 数值。

## 相关经验

- MTP 等效时延的归一基数（用稳态平均接受 token 数、别用首 batch）与 DSA 上 MTP 收益按模块分化（SFA 不吃 MTP）见 [mtp-benefit-sparse-attention-and-latency-metric](../../optimizations/cases/mtp_benefit_sparse_attention_and_latency_metric.md)。
- 多卡 MTP 计时前 `dist.barrier` 对齐各 rank、剔除卡间异步抖动见 [multicard-mtp-timing-barrier](../validations/multicard_mtp_timing_barrier.md)。

## Evidence

- `diff 事实`（@4444dbc5）：`model_infer.py`（+18/-10）三处改动——draft 耗时改累加 list、采集改 `infer_time_main + sum(mtp)` 单条记录、`obtain_mtp_stats` 拆「每步平均」与「MTP-N 等效单 token」双指标；`process_infer_time` 的 `总时间 / token_count` 语义确认两指标口径。归因主语为本仓 DeepSeek-V3.2-Exp 建模脚本 / 该修复，非模型厂商；无 benchmark 数值故不作加速比断言。溯源下探：[cann-recipes-infer-pr-61-fix-fix-mtp-time-collection-bug](https://gitcode.com/cann/cann-recipes-infer/merge_requests/61)
