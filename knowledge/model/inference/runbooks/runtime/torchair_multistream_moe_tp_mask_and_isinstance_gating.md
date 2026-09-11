---
type: Runbook
title: torchair 图模式 multistream MoE 的两处静默错配：mc2_mask 漏切致 shape mismatch + isinstance 打在非-torchair 基类致 overlap 恒失效
description: >-
  vLLM-Ascend torchair 图模式的 multistream MoE 有两处错配。其一，replace_allreduce=True 时
  hidden_states 已按 TP rank 切分，mc2_mask 却因切分逻辑被嵌在 not replace_allreduce 分支而保持全长，
  在 MC2 dispatch/combine 处发生 shape mismatch；应将 mask 切分提到 tp_size>1 的公共分支，使其与
  token 张量对齐。其二，W8A8Dynamic 量化 overlap 用非 torchair 基类做 isinstance 门控，实际子类无法命中，
  导致优化静默失效；门控应对准 TorchairAscendW8A8DynamicFusedMoEMethod。该修复不覆盖
  tp_size>1 且使用 V1 scheduler 时的另一处 multistream shape mismatch。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/2681
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# torchair 图模式 multistream MoE 的两处静默错配：mc2_mask 漏切致 shape mismatch + isinstance 打在非-torchair 基类致 overlap 恒失效

## 适用场景

在 [torchair](../../concepts/frameworks/torchair.md) 图模式下跑 MoE 前向、走 [MoE 多流](../../concepts/techniques/moe_multi_stream.md)（[multi-stream](../../concepts/techniques/multi_stream.md)）叠加 [MC2 dispatch/combine](../../concepts/techniques/moe_dispatch_combine_v2.md) 通信路径时，存在两处**独立的静默错配**——一处会以 shape mismatch 报错、一处完全无报错只是把优化白关掉。两者的共性是：图模式路径为通信掩码切分、量化方法类都 fork 了自己的一套逻辑/子类，凡是**沿用了图模式外的条件嵌套或基类判断**，就会在图模式分支里失配。

编辑或审查 torchair MoE / 量化路径、或观测到「开了 multistream_moe 却无预期 overlap 收益」「replace_allreduce 分支异常」时，按 mc2_mask 切分同步与 overlap 门控类型两个信号逐一核对。

前提场景：
- 框架：vllm-ascend（vLLM 昇腾 NPU 后端）torchair 图模式，`vllm_ascend/torchair/ops/torchair_fused_moe.py` 的 `TorchairAscendFusedMoE.forward`。
- `fused_moe_state` 走 MC2 类通信路径（即 `not in {AllGather, AllGatherEP, NaiveMulticast}`；overlap 分支进一步要求 `== FusedMoEState.MC2`）。
- 量化为 [W8A8Dynamic](../../concepts/quantization/w8a8c8.md)；`multistream_moe` 开启。

---

## 信号 1：replace_allreduce=True 时 mc2_mask 与 hidden_states 形状对不上

**信号 / 症状**：`tp_size > 1` 且 `replace_allreduce=True` 时，MC2 通信处触发 shape mismatch——hidden_states 已按 tp_size 在 token 维切分，而 mc2_mask 仍是全长。

### 触发条件
- 走 MC2 类 fused-moe 路径（`fused_moe_state not in {AllGather, AllGatherEP, NaiveMulticast}`）、`tp_size > 1`。
- `mc2_mask = forward_context.mc2_mask` 是 MC2 dispatch/combine 用的通信掩码，须与被 TP 切分后的 hidden_states 在 token 维（`dim=0`）对齐。
- `replace_allreduce=True`。

### 根因
原代码把整段「padding + TP 切分 hidden_states/router_logits + 切分 mc2_mask」都包在外层 `... and not replace_allreduce` 条件里。当 `replace_allreduce=True`：hidden_states 仍需按 tp_size 切分给各 rank，但 mc2_mask 的切分被连带跳过 → mc2_mask 保持全长、与已切分的 hidden_states 形状不匹配。根因是切分逻辑的**条件嵌套错误**，不是 replace_allreduce 机制本身有害。

### 修法
把 mc2_mask 的 TP 切分从 `not replace_allreduce` 内提到 `if tp_size > 1` 顶层——只要走 MC2 类路径且 `tp_size > 1` 就**无条件**切 mc2_mask；padding 与 hidden_states/router_logits 的切分保留在内层 `if not replace_allreduce`：

```python
         if (fused_moe_state not in [
                 FusedMoEState.AllGather, FusedMoEState.AllGatherEP,
                 FusedMoEState.NaiveMulticast
-        ] and not replace_allreduce):
-            ... padding + split hidden_states + split mc2_mask（全嵌在 not replace_allreduce 内）
+        ]):
+            if tp_size > 1:
+                tp_rank = get_tensor_model_parallel_rank()
+                chunk_mc2_mask = torch.tensor_split(mc2_mask, tp_size, dim=0)
+                mc2_mask = chunk_mc2_mask[tp_rank]   # mc2_mask 无条件切分
+            if not replace_allreduce:
+                ... padding + split hidden_states/router_logits（仅 not replace_allreduce 时）
```

**可迁移判断**：在 MC2 类 fused-moe 通信路径下，通信掩码 mc2_mask 必须与被 TP 切分的 token 张量在 `dim=0` 上按同一 tp_rank **同步切分**。把掩码切分嵌进任何与 padding / allreduce 相关的支路条件里，都会在该条件不满足的分支上留下掩码-张量形状错配。

### 边界（不外推）
`multistream_moe` 在 `tp_size > 1` + v1 scheduler 下**仍有另一处 shape mismatch**，属独立残留问题、不在本处切分同步修复的覆盖范围内。此信号只覆盖 mc2_mask 与 replace_allreduce 分支的切分同步这一处。

---

## 信号 2：multistream 并行量化 overlap 被 isinstance 静默恒关

**信号 / 症状**：开了 `multistream_moe` + W8A8Dynamic + `FusedMoEState.MC2`，却**观测不到**预期的量化/路由 overlap 收益；无异常、无精度问题，就是优化像没开。

### 触发条件
- `enable_multistream_moe` 开启、量化为 W8A8Dynamic、`fused_moe_state == FusedMoEState.MC2`。
- overlap 分支的门控里有一个 `isinstance(self.quant_method.quant_method, AscendW8A8DynamicFusedMoEMethod)` 判断（基类，定义在 `vllm_ascend.quantization.w8a8_dynamic`）。

### 根因
torchair 图模式路径 fork 出了自己的量化方法子类：实例实际是 `TorchairAscendW8A8DynamicFusedMoEMethod`（定义在 `vllm_ascend.torchair.quantization.torchair_w8a8_dynamic`），它**不是**被检查的基类 `AscendW8A8DynamicFusedMoEMethod`。于是 `isinstance` 恒为 False → overlap 分支从不进入。这是**静默失败**：无异常、无精度问题，只是 multistream 并行量化优化被白白关掉。

overlap 分支要做的事：在次级流上把 `torch_npu.npu_dynamic_quant`（对 shared-expert 输入做动态量化）与主流上的 `gate(hidden_states)` 路由计算并行，用 `npu_stream_switch("moe_secondary", 0)` 切次级流，从而把量化开销掩盖进路由计算。isinstance 恒 False 时这层掩盖从不发生。

### 修法
把 import 与 isinstance 目标由基类换成 torchair 子类：

```python
-        from vllm_ascend.quantization.w8a8_dynamic import \
-            AscendW8A8DynamicFusedMoEMethod
+        from vllm_ascend.torchair.quantization.torchair_w8a8_dynamic import \
+            TorchairAscendW8A8DynamicFusedMoEMethod
         if self.enable_multistream_moe:
             ...
             if hasattr(self.quant_method, "quant_method") and \
                isinstance(self.quant_method.quant_method,
-                          AscendW8A8DynamicFusedMoEMethod
+                          TorchairAscendW8A8DynamicFusedMoEMethod
                           ) and fused_moe_state == FusedMoEState.MC2:
```

**可迁移判断**：当 torchair（或任何图模式/后端专属）路径为某个方法/量化类**另 fork 了一个 `Torchair*` 子类**时，凡是用 `isinstance` 打在**非-torchair 基类**上的能力门控，都会在图模式路径下静默恒 False、把对应快路径关掉。审查/编辑 torchair MoE 或量化路径时，`isinstance` / 类型判断要对准该路径**实际实例化的 `Torchair*` 子类**，而非同名基类。

---

## 通用启示

两类错配同源：torchair 图模式对通信掩码切分、量化方法都各有一套 fork 出来的逻辑/类，而复用图模式外的**条件嵌套**（信号 1）或**基类型别判断**（信号 2）就会失配。条件嵌套错配会硬报 shape mismatch、易发现；基类型别错配完全静默、只表现为「优化不生效」，须靠对齐子类型别或断点确认分支是否真进入来定位。

## Evidence

- vllm-ascend PR merged diff（mergeCommit `79a910ef4730d3f1be14496a1681eee2566f64a0`，state MERGED），改动文件 `vllm_ascend/torchair/ops/torchair_fused_moe.py`：mc2_mask 切分由 `not replace_allreduce` 内提到 `if tp_size > 1` 顶层；overlap 门控的 import 与 isinstance 目标由基类 `AscendW8A8DynamicFusedMoEMethod` 换成 torchair 子类 `TorchairAscendW8A8DynamicFusedMoEMethod`。
- e2e 验证配置 DP32TP1EP32、vLLM v0.10.2（该配置 TP1，故信号 1 的 `tp_size > 1` 分支由其它 TP 配置覆盖）；无 before→after 性能数字，user-facing 无变化、e2e serving 通过。
- 溯源：[torchair-图模式-moe-mc2-mask-未随-replace-allreduce-true-分支做-tp-切](https://github.com/vllm-project/vllm-ascend/pull/2681) · [torchair-图模式下-multistream-moe-的并行量化-overlap-被静默禁用-isinstance](https://github.com/vllm-project/vllm-ascend/pull/2681)