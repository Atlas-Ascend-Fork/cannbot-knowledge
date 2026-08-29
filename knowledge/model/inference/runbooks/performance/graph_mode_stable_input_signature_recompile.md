---
type: Runbook
title: 稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss
description: 稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss。decode 逐步推理时出现图重复编译（recompile）/ 编译缓存未命中，稳态本应零重编。典型隐蔽处：不开日志看不出来，只表现为时延偏高或 cache_compile 命不中——一旦发现 decode 每步都在重编译或缓存不命中，先怀疑喂进图的输入张量签名在步间发生了漂移。
tags:
- task.debugging
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/8
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/226
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/418
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss

## 信号（现象）

decode 逐步推理时出现**图重复编译（recompile）/ 编译缓存未命中**，稳态本应零重编。典型隐蔽处：不开日志看不出来，只表现为时延偏高或 cache_compile 命不中——一旦发现 decode 每步都在重编译或缓存不命中，先怀疑喂进图的输入张量**签名在步间发生了漂移**。

## 触发条件与根因

图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图；decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。三类常见漂移：

- **shape 漂移**：整图编译默认 `dynamic=True`，decode 每步输入 shape 其实固定，但未标静态时 dynamo 把这些维度当动态，shape 一变就 guard 失效重编译。
- **stride 漂移**：喂给图的张量是切片 / `torch.cat` 后的**非连续视图**，其 stride 随迭代变化，图模式视 stride 变化为不同形态→每步重编译、命不中缓存（典型：MTP 的 `prev_hidden_states` 切片）。
- **dtype 漂移**：warm-up 用来触发编译的 dummy 输入 dtype 与正式推理输入不一致，warmup 编出的图签名对不上正式推理，正式推理时命中不同签名重新编译，warmup 白做。

## 修法（把 decode 图输入签名钉稳）

- **shape → mark_static**：约定 prefill 用动态序列长、decode 用静态序列长；只对 decode 的固定 shape 输入调 `torch._dynamo.mark_static(tensor)`。**tuple 型缓存输入的坑**（如 `past_key_values`，值是嵌套 tuple 而非单张量）——直接标 tuple 无效，必须两层遍历取到内层 `torch.Tensor` 再逐个标：
  ```python
  for item_sub in item:            # 外层元组
      for sub_item in item_sub:    # 内层元组
          if isinstance(sub_item, torch.Tensor):
              torch._dynamo.mark_static(sub_item)
  ```
  实现上用一个 `loop_list`（承载"值为 tuple、需逐元素标静态"的 key，如 `['past_key_values']`）区分普通张量 vs 缓存张量。
- **stride → .contiguous()**：写入图输入前对切片/cat 结果追加 `.contiguous()`，固定内存布局、稳定 stride：
  ```python
  input_dict['prev_hidden_states'] = torch.cat([prev, prev_hidden_states[:, -1:, :]], dim=1)[:, -L:, :].contiguous()
  ```
- **dtype → warmup dummy 与正式一致**：构造触发编译的 dummy `input_ids` 时 dtype 固定用正式推理的 dtype（如 `torch.long`），并按 `vocab_size` 范围取值：
  ```python
  dummy_input_ids = torch.randint(0, hf_config.vocab_size, (batch * seq_len,), dtype=torch.long, device=device)
  ```

## 边界与验证

- mark_static 是**按模型可选**能力、不是所有模型都要：证据里 DeepSeek-R1 / Kimi-K2 / DeepSeek-V3.2 当前不需要 mark_static，需要的网络在集成时各自传 `loop_list` 调用。**不要默认对所有模型套用**。
- `.contiguous()` 收紧仅覆盖已知的 `prev_hidden_states` 切片写入点，是否对其它切片输入通用无证据，不外推。
- 验证：稳态 decode 不再触发重编译 / 缓存命中；这类修复常无 before→after 数字（属编译稳定性修复），排障时开编译日志观察 recompile 计数。相关：cache_compile 缓存机制 [torchair-cache-compile-persisted-graph](../../optimizations/experience/rules/torchair_cache_compile_persisted_graph.md)；MTP 复用同 callable 的重编译 [mtp-speculative-decode-graph-mode-prereqs](../runtime/mtp_speculative_decode_graph_mode_prereqs.md)；动态构建落编译区导致的 cache 失败 [cache-compile-fail-dynamic-build-in-compile-region](../compilation/cache_compile_fail_dynamic_build_in_compile_region.md)。

## 参考实现及其约束

参考实现在 cann-recipes-infer 的 executor `model_runner`（`mark_inputs`/`mark_detail`）、DeepSeek-R1 与 LongCat-Flash 的 MTP `prev_hidden_states` 写入点、executor warmup（`execution_engine`）。这些是本仓建模/框架的具体落点；「图按 shape+dtype+stride 签名缓存、签名漂移即重编译」是 torchair/dynamo 图模式通则，对任何走图模式的 decode 路径可迁移。

## 相关经验
- [aclgraph 图捕获报 Alloc sq cq fail / 207005 / EL00](../runtime/aclgraph_sq_cq_alloc_fail_capture_sizes_budget.md)

- 另见 [inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测](../../optimizations/experience/rules/inductor_autofuse_partial_compile_scope.md)。


## Evidence

- diff 事实 + 维护者确认（@d23e91732136）：`dynamic=True,fullgraph=True` 编译下 decode 输入 `mark_static`、tuple 缓存两层迭代标记；「R1/K2/V3.2 不需要 mark static，需要的网络自 mark」为 review 确认。溯源下探 [cann-recipes-infer-pr-8-refactor-add-common-development](https://gitcode.com/cann/cann-recipes-infer/merge_requests/8)
- diff 事实 + 维护者确认（@41af2991a3bd）：非连续切片 stride 变化触发重编译，追加 `.contiguous()` 固定 stride；"之前跑 CI 不开日志看不出来"为实现者确认。溯源下探 [cann-recipes-infer-pr-226-fix-cache-compile-print-time](https://gitcode.com/cann/cann-recipes-infer/merge_requests/226)
- diff 事实 + 维护者确认（@2c45117）：warmup dummy `input_ids` 固定 `dtype=torch.long` 与正式推理一致、避免重编译；dtype 一致由作者答复确认。溯源下探 [cann-recipes-infer-pr-418-fix-fix-model-config-explanation-update-cann-version-and-fix-r1-multistr](https://gitcode.com/cann/cann-recipes-infer/merge_requests/418)

<!-- cannbot:related:start -->
## 相关

- [MTP 投机解码接图模式的前置与坑：独立 decode 入口避免重编译 + FIA GQA 要求 + aclgraph 取舍](../runtime/mtp_speculative_decode_graph_mode_prereqs.md)（`related`）：焦点卡记录“decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。”；MTP Runbook指出“图模式按被 trace 的 **callable（函数对象）** 缓存/注册已编译图。”。前者用于固定参数签名，后者用于排除 draft 与 target 共用 callable 的另一类重编译根因。
- [NPU 图模式（ge_graph / npugraph_ex）](../../concepts/techniques/npu_graph_mode.md)（`related`）：decode 且 `enable_gegraph` 时切到 `torchair.ops`；ExecutionEngine 在 `npugraph_ex` decode 模式下把 `actual_seq_lengths_*` 转成 `list`。；图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图；decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。。概念卡规定不同后端的 decode 输入形态，Runbook给出签名漂移导致重编译的判别与固定方法。
- [aclgraph 图捕获报 Alloc sq cq fail / 207005 / EL0006：档位过多耗尽每卡 SQ/CQ 流资源](../runtime/aclgraph_sq_cq_alloc_fail_capture_sizes_budget.md)（`related`）：图模式档位 / 输入签名与重复编译相关问题见 ［graph-mode-stable-input-signature-recompile］(../performance/graph_mode_stable_input_signature_recompile.md)。；图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图；decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。三类常见漂移：；焦点卡主动把输入签名问题交给目标卡，目标卡给出签名漂移触发重编译的具体机制。
- [inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测](../../optimizations/experience/rules/inductor_autofuse_partial_compile_scope.md)（`related`）：“据此实际加装饰的对象（观测实例落在 `Expert.forward` / `RMSNorm.forward` / `hc_head` / `hc_pre` / `hc_post` 这几个建模函数）。配套：不对输入做 padding 时，输入长度变化可能触发 dynamo 重编译（输入签名稳定见 ［graph-mode-stable-input-signature-recompile］(../../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)）。”；“图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图；decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。”。部分编译范围的 Guard 风险与输入签名漂移的诊断规则相接，可从选范围继续定位重编译原因。
- [torchair cache_compile 图编译缓存落盘复用：调用约定、缓存失效与后端/版本约束](../../optimizations/experience/rules/torchair_cache_compile_persisted_graph.md)（`related`）：焦点卡说明“图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图”；缓存规则说明“`cache_compile` 以「模型结构 + 部署方式（并行/量化布局）」为隐式 key 缓存已编译图，但**缓存不感知配置变更**”。两端分别约束单次运行的输入签名和跨重启缓存的结构部署键，排查 cache miss 时必须分层。
<!-- cannbot:related:end -->
