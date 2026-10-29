---
type: Runbook
title: MoE 优化/并行在 decode 静默不生效的四类根因：硬编码 False / yaml 键名不匹配 / 漏切间接层 / 误挂 is_prefill
description: MoE 优化/并行在 decode 静默不生效的四类根因：硬编码 False / yaml 键名不匹配 / 漏切间接层 / 误挂 is_prefill。配置里明明开了某项优化（superkernel / 多流 / 新量化分支 / 张量并行），运行时却看不到预期的 overlap / 加速 / 切分，而且不报错、不告警。尤其常发生在 decode 路径。遇到「配了却像没生效」，优先按下面四类根因逐一核查开关到建模侧的真实传播链，而不是先怀疑功能本身。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/345
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/262
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/410
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/26
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MoE 优化/并行在 decode 静默不生效的四类根因：硬编码 False / yaml 键名不匹配 / 漏切间接层 / 误挂 is_prefill

## 信号（现象）

配置里明明开了某项优化（[superkernel](../../concepts/techniques/superkernel.md) / [多流](../../concepts/techniques/moe_multi_stream.md) / 新量化分支 / 张量并行），运行时却**看不到预期的 overlap / 加速 / 切分**，而且**不报错、不告警**。尤其常发生在 decode 路径。遇到「配了却像没生效」，优先按下面四类根因逐一核查开关到建模侧的**真实传播链**，而不是先怀疑功能本身。

## 四类根因 → 修法

### 1. 使能标志在 `__init__` 里被硬编码为 False
建模类构造函数直接 `self.enable_multi_streams = False` / `self.enable_superkernel = False`，无论 yaml/`custom_params` 配了什么都是关。伴随 bug：`self.layer_idx = kwargs.get("layer_idx")` 但 `layer_idx` 没在 kwargs 里透传、实际取到 `None`，导致按 `None` 索引 `events` 破坏 per-layer 的 tagged-event 调度。
**修法**：三处开关改为从 `infer_config.model_config.custom_params.get("enable_...", False)` 读取；把 `layer_idx` 形参化并在构造子模块时显式 `layer_idx=layer_idx` 透传。

### 2. yaml 键名与代码读取键不逐字一致 → `.get` 默认 False
建模用 `runner_settings.get("model_config").get("enable_superkernel", False)` 带默认值读取。yaml 里键名拼错（如遗留 `enable_super_kernel` vs 规范 `enable_superkernel`）时，`.get` **静默回落 False**、优化被悄悄关闭。且 superkernel 只在 decode 分支通过 `superkernel_scope(...)` 生效，故失效只发生在被 scope 包住的 decode 路径、且静默。
**修法**：yaml 键名与建模 `.get(...)` 读取键**逐字一致**（规范名 `enable_superkernel`）。遇到「superkernel 配了却 decode 无效」，先核 yaml 键拼写。

### 3. 新增量化/计算分支挂在属性间接层，但 forward 调用点漏切
`__init__` 里绑 `self.moe_ffn = self.experts_w4a8int4 if gmm_quant_mode=="w4a8int4" else self.experts`，但 forward 的专家调用点仍写死 `self.experts(**gmm_args)`。后果：即便配置选了新分支，新方法**从不被调用**，静默回落默认路径——**无报错的静默错路**（功能/性能/精度都不是目标模式，但不崩不告警）。MoE 类常有**两个**专家调用点（prefill 的 `forward_expert` 与 decode 的 `moe_infer_dispatch_combine`）。
**修法**：**两处调用点都**改成走间接层 `self.moe_ffn(**gmm_args)`。给 MoE 加新量化/计算分支时，务必检查所有专家调用点是否都切到了间接入口。

### 4. 并行/优化的使能条件误挂在 `is_prefill` 下 → decode 静默失效
昇腾推理栈里模块常共用 `forward(x, is_prefill=False)` 做 prefill/decode 分流。若把并行手段的触发条件写成 `is_prefill and dense_tp_size>1 and moe_ep_size>1`，`is_prefill` 会把整段 TP 通信（all-gather / reduce-scatter）钉死在 prefill，decode 永不进分支——配了 `dense_tp_size>1` 也观察不到 dense-MLP 被切分，不报错、只是不生效。
**修法**：门控条件去掉 `is_prefill`，改为 `dense_tp_size>1 and moe_ep_size>1`，prefill/decode 一致执行（沿 batch 维 `all_gather_into_tensor` 得 `[bsz*dense_tp_size, q_len, hidden]` 直接用、MLP 后 `reduce_scatter_tensor` 归约）。前置仓级约定：启用前须 `world_size % dense_tp_size == 0`，否则 `check_parallel_settings` 抛 `ValueError`。

## 共性 / 迁移

这四类都是「使能信号从配置到建模侧执行分支的传播被某处悄悄截断」，共同症状是**配了不报错但不生效、且倾向只在 decode 暴露**。给 MoE 加任何「可开关的优化 / 新分支 / 并行」时，核查链条：yaml 键名 → `.get` 读取键 → `__init__` 赋值（有没有硬编码 False）→ forward 每个调用点（有没有都走间接层）→ 门控条件（有没有误混 `is_prefill`）。

## 相关经验
- [MoE token dispatcher 把中间张量挂 self. 属性阻止 GC：aclg](../performance/moe_token_dispatcher_self_attr_oom_aclgraph.md)
- [MoE + 投机解码：draft dummy_run 误带 profile-run 语义触发](../precision/mtp_draft_dummy_run_in_profile_run_random_experts.md)
- [序列并行(FlashComm V1)分支用只查环境变量的窄谓词门控：漏掉 shared_ex](../precision/sp_gate_narrow_env_predicate_misses_shared_expert_dp.md)

- 另见 [量化 MoE 专家 GMM 的 phase-gated bias 跳过：Prefill 去 bias 提速、Decode 保留](../../optimizations/rules/w4a8_moe_gmm_prefill_skip_bias.md)。


## Evidence

- 三处 `enable_*=False` 硬编码 → 改读 `custom_params`、`layer_idx=None` 取值 bug → 形参化透传：diff 事实 @caa72a0c8625。溯源下探 [cann-recipes-infer-pr-345-fix-fix-r1-multistream-and-superkernel-add-time-printing](https://gitcode.com/cann/cann-recipes-infer/merge_requests/345)。
- `.get("enable_superkernel", False)` 键名不匹配静默回落 + decode-only `superkernel_scope` 门控：diff 事实 @699396c6be87。溯源下探 [cann-recipes-infer-pr-262-fix-fix-longcat-config-yaml](https://gitcode.com/cann/cann-recipes-infer/merge_requests/262)。
- 间接层 `self.moe_ffn` 绑定但 forward 两处调用点写死 `self.experts` → 新 int4 分支从不被调用 → 两处切 `self.moe_ffn`：diff 事实 @6857a2062f66 + 维护者确认（报告死代码 + 复审确认接入两条路径）。溯源下探 [cann-recipes-infer-pr-410-feat-w4a8int4](https://gitcode.com/cann/cann-recipes-infer/merge_requests/410)。
- dense-MLP TP 门控误挂 `is_prefill` → decode 不切分、去 `is_prefill` + all-gather 布局改沿 batch 维 + `world_size % dense_tp_size` 整除校验：diff 事实 @29f28af1e40c + reviewer 要求补校验。溯源下探 [cann-recipes-infer-pr-26-bugfix-support-dense-mlp-tp](https://gitcode.com/cann/cann-recipes-infer/merge_requests/26)。