---
type: Runbook
title: MTP 投机解码接图模式的前置与坑：独立 decode 入口避免重编译 + FIA GQA 要求 + aclgraph 取舍
description: MTP 投机解码接图模式的前置与坑：独立 decode 入口避免重编译 + FIA GQA 要求 + aclgraph 取舍。给一个已在图模式跑通的模型加 MTP/投机解码（draft 模型与 target 模型交替走 decode 图）时，会撞上几个 target 单模型不会出现的图模式坑。接入前逐条对照。MTP 本身的接入/草稿缓存正确性见 mtp-speculative-decode-model-onboarding / mtp-draft-cache-state-correctness；本页只讲"接图模式"这一层。
tags:
- task.debugging
- topic.attention
- topic.graph_execution
- topic.speculative_decoding
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/17
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/210
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/270
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/288
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MTP 投机解码接图模式的前置与坑：独立 decode 入口避免重编译 + FIA GQA 要求 + aclgraph 取舍

## 适用场景

给一个已在图模式跑通的模型加 [MTP/投机解码](../../concepts/techniques/mtp_speculative_decoding.md)（draft 模型与 target 模型交替走 decode 图）时，会撞上几个 target 单模型不会出现的图模式坑。接入前逐条对照。MTP 本身的接入/草稿缓存正确性见 [mtp-speculative-decode-model-onboarding](../../guides/experience/interventions/mtp_speculative_decode_model_onboarding.md) / [mtp-draft-cache-state-correctness](../../optimizations/experience/rules/mtp_draft_cache_state_correctness.md)；本页只讲"接图模式"这一层。

## 坑 1：draft 与 target 复用同一 decode callable → 图重编译

- **信号**：aclgraph / gegraph 下开 MTP，decode 第二轮执行触发重编译、缓存未命中（本应零重编）。
- **根因**：图模式按被 trace 的 **callable（函数对象）** 缓存/注册已编译图。若 draft（MTP）模型继承 target 的 `decode`、或两个实例把**同一个绑定方法**交给 `cache_compile` 只靠 `cache_dir` 后缀区分——两条 decode 图撞同一注册键，交替调用触发重编译。`cache_compile` 疑似以 callable 为编译注册键、而非以 `cache_dir` 为键。
- **修法**：给 MTP 模型一个**独立的 decode 函数对象**——即便函数体与 target 逐字相同，也另建一个方法名：
  ```python
  # DeepseekV3ModelMTP 新增独立 decode（否则继承自 target、共用同一 callable）
  def decode(self, **kwargs):
      # graph modes(aclgraph, gegraph): mtp model and target model require different
      # decode functions, otherwise recompiling is triggered.
      return self.forward(is_prefill=False, **kwargs)
  ```
  cache_compile 场景同理：`cache_model = self.main_decode_mtp if self.is_mtp else self.main_decode`（两个独立函数对象 + 各自 `cache_dir`）。

## 坑 2：MTP + graph mode 的 FIA 解码路径要求 GQA

- **信号**：MTP + graph mode 启动即抛
  `ValueError: When the MTP scenario enables the graph mode, it needs to meet the GQA requirement, which means tp_q_head_num > tp_k_head_num`。
- **根因/守卫**：MTP 的 [FIA](../../concepts/kernels/fused_infer_attention_score.md) 解码分支在 graph mode 下只支持 GQA 布局；`tp_q_head_num == tp_k_head_num`（MHA，q/k 头数相等）且开图模式时代码主动早失败，避免 graph mode 下 MHA FIA 走出隐性错误结果。
- **对号入座后怎么办**：① 保证注意力是 GQA（`tp_q_head_num > tp_k_head_num`，通常靠 TP 切分让每卡 KV 头数 < Q 头数）；或 ② 关掉 graph mode 跑该 MTP 配置。开图前先确认注意力是 GQA。

## 坑 3：aclgraph 对某些 MTP 配置不划算——保 ge_graph

- 维护者确认：在 MTP `next_n=3`（"mtp3"）+ A3 部署这一组合上，把 decode 图从 ge_graph 换成 aclgraph 期望拿收益会踩坑——"aclgraph + mtp3 存在性能问题"，据此拒绝了加 aclgraph 交叉验证 case 的建议，CI 保持 `exe_mode: ge_graph`。
- **不要做**：在该类 MTP-3 场景无脑把 decode 从 ge_graph 切 aclgraph 求收益。**边界**：只给了定性"性能问题"结论、**未披露根因/劣化幅度**；不外推到"所有模型的 aclgraph"或"无 MTP 时"——aclgraph 代码路径本身仍在，只是当前不作 MTP-3 的推荐/验证路径。选后端对照 [graph-mode-decode-only-compile-backends](../../optimizations/experience/rules/graph_mode_decode_only_compile_backends.md)。

## 参考实现及其约束

参考实现：DeepSeek-R1/V3 建模的 `DeepseekV3ModelMTP.decode`、DeepSeek-V3.2-Exp 的 `cache_compile` MTP 分支、Qwen3-Next SGLang `AscendAttnBackend` 的 MTP FIA GQA 守卫、GLM-5 的 CI config（`glm_5_rank_64_64ep.yaml` 保持 ge_graph）。GQA 守卫落在 SGLang `AscendAttnBackend` 的 MTP FIA 分支、mtp3 性能结论落在 GLM-5+A3 具体组合，均不外推整栈；"draft 须独立 decode callable、否则图重编译"是图模式按 callable 缓存的通用后果，跨 MTP 模型可迁移。MTP 场景的多流 event 重复创建/流转发坑另见 [graph-mode-multi-stream-sync-failures](graph_mode_multi_stream_sync_failures.md)。

## 相关经验
- [FIA/qlens 的 block_table 首维 / num_reqs / TND se](fia_qlens_block_table_num_reqs_batch_contract.md)
- [MoE + 投机解码：draft dummy_run 误带 profile-run 语义触发](../precision/mtp_draft_dummy_run_in_profile_run_random_experts.md)

## Evidence

- diff 事实 + 维护者确认（@611360a882f4）：cache_compile 第二轮重编译，修法按 `is_mtp` 传独立 callable；"cache_compile 以 callable 为键"为推断、已标注。溯源下探 [cann-recipes-infer-pr-17-fix-cache-compile](https://gitcode.com/cann/cann-recipes-infer/merge_requests/17)
- diff 事实 + 维护者注释（@f12bd2742493）：`DeepseekV3ModelMTP` 新增独立 `decode`，注释写明"graph modes 下 mtp 与 target 须用不同 decode 函数否则重编译"。溯源下探 [cann-recipes-infer-pr-210-fix-ds-r1-solve-recompile-bug-in-mtp-case](https://gitcode.com/cann/cann-recipes-infer/merge_requests/210)
- diff 事实（@be33ff59ad77）：`ascend_backend.py` 新增 `tp_q_head_num == tp_k_head_num and graph_mode` → `raise ValueError`，报错文案逐字对上。溯源下探 [cann-recipes-infer-pr-270-feat-qwen3-next-rmsnormgated-gdr](https://gitcode.com/cann/cann-recipes-infer/merge_requests/270)
- 维护者确认 + diff 佐证（@b451d3e789c2）：mtp3 场景 aclgraph 有性能问题，CI 保 `exe_mode: ge_graph`；根因未披露。溯源下探 [cann-recipes-infer-pr-288-glm-5-adapt-class-name-and-function-name-support-bf16-fix-bug-caused-by](https://gitcode.com/cann/cann-recipes-infer/merge_requests/288)

<!-- cannbot:related:start -->
## 相关

- [MTP Speculative Decoding](../../concepts/techniques/mtp_speculative_decoding.md)（`related`）：焦点卡区分 R1“`ge_graph` + MTP 可同开”与 Qwen3-Next 图模式互斥，候选卡进一步限定“在 graph mode 下只支持 GQA 布局”；它为决定是否接图模式和排查重复编译/FIA 布局失败提供具体前置条件。
- [图模式多流跨流同步的失败签名：漏配同步/守卫不一致/重复创建 event/流未转发](graph_mode_multi_stream_sync_failures.md)（`related`）：“MTP 触发 tagged-event 重复创建”与“draft 模型与 target 模型交替走 decode 图”说明 MTP 的交替图执行是重复创建事件这一失败签名的具体触发场景。
- [稀疏注意力接 aclgraph FULL_DECODE_ONLY 全图 decode：申报级别与 metadata 切片口径的两类捕获失败](sfa_dsa_aclgraph_full_decode_only_capture.md)（`related`）：MTP 的 ［FIA］(../../concepts/kernels/fused_infer_attention_score.md) 解码分支在 graph mode 下只支持 GQA 布局；在昇腾上要让某注意力后端在 `FULL_DECODE_ONLY` 图模式下**同时支持 MTP** 时，先确认该后端 `get_cudagraph_support()` 申报的是 `UNIFORM_BATCH`；接入 MTP 全图 decode 时，前者要求 FIA 路线先满足 Q/K 头布局，后者要求稀疏注意力后端覆盖多 token uniform batch，两项构成同一次图捕获上线检查的独立必备条件。
- [稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss](../performance/graph_mode_stable_input_signature_recompile.md)（`related`）：焦点卡记录“decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。”；MTP Runbook指出“图模式按被 trace 的 **callable（函数对象）** 缓存/注册已编译图。”。前者用于固定参数签名，后者用于排除 draft 与 target 共用 callable 的另一类重编译根因。
<!-- cannbot:related:end -->
