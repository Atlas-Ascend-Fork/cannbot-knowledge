---
type: Runbook
title: GE 图下 MoE 路由门控（gate/classifier）权重布局坑：转置/NZ/非连续致图性能劣化或路由结果错
description: 现象：权重加载路径对 gate/router 权重做了转置，转置后 tensor 内存非连续（non-contiguous）；非连续 gate 权重进 GE 图造成图性能劣化。 修法：在权重后处理循环里，对模块名含 gate 的权重在 process_weights_after_loading 之后强制转连续：；判据是 "gate" in module_name 子串匹配；转连续发生在后处理之后、图 build 之前，一次性 pay 在权重加载阶段。
tags:
- task.debugging
- topic.graph_execution
- topic.data_movement.layout_transform
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/430
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/358
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# GE 图下 MoE 路由门控（gate/classifier）权重布局坑：转置/NZ/非连续致图性能劣化或路由结果错

## 适用场景

在 GE 图模式下部署 MoE 模型，`process_weights_after_loading`（加载后权重后处理，含转置 / NZ 分形 / 量化）对**所有** MatMul 权重统一处理，但 **MoE 路由门控（gate / router / classifier）的权重对布局敏感**——统一处理会让它在 GE 图下要么性能劣化、要么路由结果算错。给 MoE 开 GE 图时，把门控权重从统一后处理里单独拎出来。两类坑：

## 坑 1：gate 权重转置后非连续 → GE 图性能劣化

- **现象**：权重加载路径对 gate/router 权重做了转置，转置后 tensor 内存非连续（non-contiguous）；非连续 gate 权重进 GE 图造成图性能劣化。
- **修法**：在权重后处理循环里，对模块名含 `gate` 的权重在 `process_weights_after_loading` 之后强制转连续：
  ```python
  quant_method.process_weights_after_loading(module, is_nz=self.enable_weight_nz, scales_dtype=scales_dtype)
  if "gate" in module_name:
      # Avoid GE graph performance degradation: make gate tensor contiguous after transpose.
      module.weight.data = module.weight.data.contiguous()
  ```
- 判据是 `"gate" in module_name` 子串匹配；转连续发生在后处理之后、图 build 之前，一次性 pay 在权重加载阶段。

## 坑 2：classifier 权重被错误转置/NZ 化 → router_logits 错

- **现象**：路由门控 `classifier` 线性层权重与其它 MatMul 权重一样被 `process_weights_after_loading` 施加了转置 + NZ 格式化（`enable_weight_nz` 默认 True），但路由 forward 走 `nn.Linear` 语义（`x @ W.T`）期望的是原始 `[out, in]` ND 未转置布局；二者不一致 → GE 图下路由 MatMul 权重被错误转置/NZ 化，得到错误 router_logits。
- **修法**：把 `classifier` 从加载后权重后处理中**排除**（保持原始 ND 未转置布局），并在 forward 里改用 `F.linear` 直接消费原始权重：
  ```python
  is_nz = False if ("classifier" in module_name) else True
  is_transpose = False if ("classifier" in module_name) else True
  quant_method.process_weights_after_loading(module, is_nz=is_nz, is_transpose=is_transpose, scales_dtype=scales_dtype)
  ```
  ```python
  # forward: router 打分改 F.linear 直接吃原始权重、无 bias
  router_logits = F.linear(hidden_states.type(torch.float32), self.classifier.weight, None)
  # 其后 torch_npu.npu_moe_gating_top_k(router_logits, k=self.top_k, ...)
  ```
- 「转置/NZ 后处理与路由 forward 布局不一致致 MatMul 转置错误」是据两处协同修改推断（`process_weights_after_loading` 实现体未读，`is_nz`/`is_transpose` 语义按参数名推断），核心的"排除门控权重 + 用 F.linear"是 diff 事实。

## 边界与验证

- 两坑分别落在带 gate 的 MoE 建模（DeepSeek-R1 / Qwen3-MoE）与 LongCat-Flash 的 `classifier`；对其它在 GE 图下转置/NZ 门控权重的 MoE 建模可迁移同一判断——**GE 图下路由门控权重加载后先按需转连续/排除 NZ 与转置**。均为纠正性能/正确性的修复，源未给 before→after 数字，用路由输出正确性 + GE 图时延校验。相关权重 NZ 概念见 [weight-nz](../../concepts/techniques/weight_nz.md)；同一图模式下 MoE 专家分发（dispatch/combine）须可图化的另一类坑见 [moe-ep-decode-graphmode-dispatch](../../optimizations/rules/moe_ep_decode_graphmode_dispatch.md)。

## 参考实现及其约束

参考实现：DeepSeek-R1 / Qwen3-MoE 的 `*ForCausalLM` 权重加载循环（`"gate" in module_name` 转连续）、LongCat-Flash `LongcatFlashRunner._process_weight_after_loading` + `LongcatFlashTopkRouter.forward`（`classifier` 排除 NZ/transpose + F.linear）。`"gate"`/`"classifier"` 子串判据、`enable_weight_nz` 默认值是本仓落点；"GE 图下 MoE 门控权重对布局敏感、须从统一权重后处理里单独处理"是可迁移判断。

## Evidence

- diff 事实 + 实施者注释确认（@c138154bdc57）：DeepSeek-R1 / Qwen3-MoE 权重加载循环新增 `if "gate" in module_name: module.weight.data = module.weight.data.contiguous()`，注释"Avoid GE graph performance degradation: make gate tensor contiguous after transpose."。溯源下探 [cann-recipes-infer-pr-430-refactor-unify-infer-sh-and-fix-dsr1-qwen3-moe-gate-on-gegraph](https://gitcode.com/cann/cann-recipes-infer/merge_requests/430)
- diff 事实（@31111a5d0967）：`classifier` 排除 `is_nz`/`is_transpose` + forward 改 `F.linear(..., self.classifier.weight, None)`；失败机制为推断、已标注。溯源下探 [cann-recipes-infer-pr-358-fix-ge-graph-mode-longcat-mm-transpose-bugfix](https://gitcode.com/cann/cann-recipes-infer/merge_requests/358)
