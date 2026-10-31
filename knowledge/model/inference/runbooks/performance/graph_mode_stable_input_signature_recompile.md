---
type: Runbook
title: 稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss
description: 从重编译与 guard 日志定位 shape、stride、dtype 和 warm-up 差异；仅对确认的输入试验静态化或连续化，区分动态支持与持久缓存失效。
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
updated_at: '2026-10-29T15:29:20Z'
platforms:
- agnostic
---

# 稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss

## 信号（现象）

decode 逐步推理时出现**图重复编译（recompile）/ 编译缓存未命中**，稳态本应零重编。典型隐蔽处：不开日志看不出来，只表现为时延偏高或 cache_compile 命不中——一旦发现 decode 每步都在重编译或缓存不命中，先怀疑喂进图的输入张量**签名在步间发生了漂移**。

## 触发条件与根因

图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图；输入变化若不满足已有图的 guard 或后端约束，才可能触发重编译；动态维并非每次变化都需要新图。三类常见漂移：

- **shape 漂移**：先检查实际 `dynamic` 设置和 guard 日志；固定维度与后端静态化要求不一致可能触发重编译，`dynamic=True` 本身不等于每次 shape 变化都重编译。
- **stride 漂移**：喂给图的张量是切片后的非连续视图或步间布局发生变化，其 stride 随迭代变化，图模式视 stride 变化为不同形态→每步重编译、命不中缓存（典型：MTP 的 `prev_hidden_states` 切片）。
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
- 验证：稳态 decode 不再触发重编译 / 缓存命中；这类修复常无 before→after 数字（属编译稳定性修复），排障时开编译日志观察 recompile 计数。相关：cache_compile 缓存机制 [torchair-cache-compile-persisted-graph](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)；MTP 复用同 callable 的重编译 [mtp-speculative-decode-graph-mode-prereqs](../runtime/mtp_speculative_decode_graph_mode_prereqs.md)；动态构建落编译区导致的 cache 失败 [cache-compile-fail-dynamic-build-in-compile-region](../compilation/cache_compile_fail_dynamic_build_in_compile_region.md)。

## 参考实现及其约束

参考实现在 cann-recipes-infer 的 executor `model_runner`（`mark_inputs`/`mark_detail`）、DeepSeek-R1 与 LongCat-Flash 的 MTP `prev_hidden_states` 写入点、executor warmup（`execution_engine`）。这些是本仓建模/框架的具体落点；这些维度是 guard 排查线索；是否重编译取决于具体 guard、动态配置和后端，不把所有签名变化都当作必然重编译，对任何走图模式的 decode 路径可迁移。

## 相关经验
- [aclgraph 图捕获报 Alloc sq cq fail / 207005 / EL00](../runtime/aclgraph_sq_cq_alloc_fail_capture_sizes_budget.md)

- 另见 [inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测](../../optimizations/rules/inductor_autofuse_partial_compile_scope.md)。


## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/8)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/226)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/418)（evidence）

## 最小排查与回退

先打开 `torch._logging.set_logs(recompiles=True)`，保存触发 guard 和对应输入的 shape、stride、dtype；同时区分本次进程的重编译与跨进程持久缓存未命中。只对日志确认的输入试验静态标记或连续化，核对输出、复制开销和稳态编译次数。无改善时撤回标记，继续检查地址、Python guard 与后端限制。
