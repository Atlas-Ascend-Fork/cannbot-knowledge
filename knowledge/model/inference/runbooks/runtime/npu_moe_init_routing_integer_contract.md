---
type: Runbook
title: 昇腾融合 MoE 路由的整数契约：npu_moe_init_routing(_v2) 的 active_expert_range 只吃 int、topk_ids 须 int32
description: 昇腾融合 MoE 路由入口算子 npu_moe_init_routing(_v2) 的整数 dtype 契约（多信号 failure_signature）：其 active_expert_range 只接受 Python int，不接受 tensor——当本地专家数由 torch.sum(expert_map != -1) 等归约得到的 0-dim tensor 直接传入时（EP/expert-parallel 高发），float kernel 在 dispatch allgather 路径抛类型错误，须 .item()/int() 归一；同时下游 npu_moe_init_routing 对 topk_ids 要求 torch.int32，vllm-ascend 融合 MoE 的 select_experts 接入 custom_routing_function 时须删 NotImplementedError 硬守卫、把默认权重分支收窄为 elif is None、并在自定义分支 topk_ids.to(torch.int32) 后早返回避免二次 topk。覆盖 backend_incompatibility、moe_decode、Qwen3-30B-A3B EP smoke、Llama-4 custom routing 场景，链接 double-routing / moe-dispatch-combine-v2 / expert-parallel。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5521
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/495
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾融合 MoE 路由的整数契约：npu_moe_init_routing(_v2) 的 active_expert_range 只吃 int、topk_ids 须 int32

## 适用场景

在昇腾 NPU 上运行 MoE 推理时，token routing / dispatch 走的是融合算子 `npu_moe_init_routing` 或其 V2 版 `npu_moe_init_routing_v2`（重排 token→专家的入口算子，见 [double-routing](../../concepts/techniques/double_routing.md) 的多算子路由链路，以及作为其一体化替代的 [moe-dispatch-combine-v2](../../concepts/techniques/moe_dispatch_combine_v2.md)）。`npu_moe_init_routing(_v2)` 对若干标量入参有整数 dtype 契约：`active_expert_range` 只吃 Python int、`topk_ids` 须 int32。凡是把「由 tensor 归约/掩码派生的专家计数」或「外部自定义路由函数产出的专家索引」不加转换直接传入这些算子，就会触发下面两类失败信号之一。本页聚合这两个信号；观测到其中任一现象时，逐项核对根因并按对应修法归一 dtype。

适用前提：融合 MoE 后端（如 vllm-ascend 覆写的 `select_experts` / dispatch 路径），[expert-parallel](../../concepts/parallelism/expert_parallel.md)（EP）开启时尤其容易触发第一个信号（本地专家数由 expert-map 派生）。

---

### 信号 1：active_expert_range 收到 tensor 报类型错误（只吃 Python int）

**症状 / 现象**：`npu_moe_init_routing_v2` 的 float kernel 在 dispatch allgather 路径中收到 tensor 形态的 `active_expert_range` 时抛类型错误。算子该路径**只支持 Python int、不支持 tensor**（0-dim tensor 也不行）。

**触发条件**：`active_expert_range` 由本地专家数（`local_num_experts` / `num_local_experts`）驱动，而这个计数是通过对 expert-map 做归约得到的——典型写法 `torch.sum(self._expert_map != -1)`。`torch.sum(...)` 返回 **0-dim tensor**，于是本该是 int 的参数被隐式转为 tensor，一路传到算子处才暴露为类型错误。当上游为统一变量把散落的 int 计数一律改成走这个 tensor 派生值时，尤其容易引入该缺陷。

**根因**：这是该昇腾算子该 kernel 路径的入参类型契约（int-only）。任何把「tensor 归约 / 掩码求和 / expert-map 派生」的专家计数直接传入 `active_expert_range` 的代码都会触发同一个类型错误。

**修法**：在传给算子之前强制把标量归一为 Python int，用 `.item()`（若确定是 tensor）或对可能是 tensor / 也可能是普通数的入参做类型分支：

```python
# 计数来源处：torch.sum(...) 返回 0-dim tensor，追加 .item()
self.local_num_experts = (
    torch.sum(self._expert_map != -1).item()
    if self._expert_map is not None else self.global_num_experts
)

# dispatcher 入口：入参可能已是 tensor、也可能是普通数，做分支归一
num_experts_local = kwargs.get("num_local_experts", 0)
self.num_experts_local = (
    num_experts_local.item() if torch.is_tensor(num_experts_local)
    else int(num_experts_local)
)
```

要点：归一动作要放在**离算子最近的可控点**（或在计数源头就 `.item()`），避免中途又被某个统一变量重写回 tensor。`int(...)` 对普通数够用，但对 0-dim tensor 应走 `.item()` 而非 `int(...)` 以显式表达意图。

---

### 信号 2：自定义路由结果未转 int32 / 撞 NotImplementedError（topk_ids 须 int32 且早返回）

**症状 / 现象**：两种表现——(a) 融合 MoE 的 `select_experts` 抛 `NotImplementedError: Custom routing function is not supported now`（旧实现开头有一道硬守卫直接 raise）；(b) 即使去掉守卫，若把已由自定义路由算好的 `(topk_weights, topk_ids)` 又落进默认的 softmax/topk 权重分支二次加工，结果会错乱；或者 `topk_ids` 未转 int32 导致下游 `npu_moe_init_routing` 因 expert 索引 dtype 不符而失败。

**触发条件**：vLLM 建模层给 `FusedMoE` 传入了非 None 的 `custom_routing_function`（某些模型自带，如 Llama-4 的 `Llama4MoE`）。调用链 `FusedMoE.forward → quant_method.apply → forward_oot`（vllm-ascend 覆写）`→ select_experts(...)`；profile_run 与 decode 都会走到。

**根因**：昇腾融合 MoE 路径的两个契约叠加——(1) 早期只实现了内建 softmax/sigmoid + topk 路由，没接线让外部路由函数生效，于是用一道 raise 显式拒绝（这是 NPU 后端相对通用建模层的一处 backend_incompatibility：模型在建模层合法，但 Ascend 后端缺实现）；(2) 下游 `npu_moe_init_routing` 对 expert 索引 dtype 有固有契约——`topk_ids` 必须是 `torch.int32`（源码原注释即 `# Required by npu_moe_init_routing`），这不是 llama4 专属。

**修法**：在 `select_experts` 里同时做三件事，缺一不可：

1. 删掉开头 `if custom_routing_function is not None: raise NotImplementedError(...)` 硬守卫。
2. 把默认权重分支的条件从 `else` **收窄成 `elif custom_routing_function is None`**，将「自定义路由」从默认分支里摘出去。
3. 新增自定义分支：调用路由函数，把 `topk_ids` 转 `torch.int32`，然后**立刻 return**——跳过函数末尾针对内建路由的后处理，不让结果二次过默认 topk/softmax。

```python
elif custom_routing_function is None:
    topk_weights, topk_ids = topk_weights.topk(top_k, dim=-1)
    topk_weights = topk_weights.to(hidden_states.dtype)
else:
    topk_weights, topk_ids = custom_routing_function(
        hidden_states=hidden_states,
        gating_output=router_logits,
        topk=top_k,
        renormalize=renormalize)
    # Required by npu_moe_init_routing
    topk_ids = topk_ids.to(torch.int32)
    return topk_weights, topk_ids
```

`custom_routing_function` 的调用约定（vLLM 侧签名，供不熟上游者自包含）：入参 `hidden_states`、`gating_output=router_logits`、`topk=top_k`、`renormalize`；返回 `(topk_weights, topk_ids)` 即每 token 最终选中的专家权重与索引，已含归一化，不应再被默认 topk/softmax 二次加工。

---

## 通用抓手（去仓化）

无论哪个信号，可迁移的固有约束是同一条：**昇腾融合 MoE 路由入口 `npu_moe_init_routing(_v2)` 对标量入参有整数 dtype 契约**——`active_expert_range`（专家计数区间）只吃 Python int，`topk_ids`（expert 索引）须 `torch.int32`。任何把「tensor 派生的专家计数」或「外部路由产出的 float / int64 索引」不加转换传入的路径都会失败。在把值交给算子的最后可控点做 `.item()` / `.to(torch.int32)` 归一，是这类问题的通用防线。

## correctness / 验证

- 信号 1 修复后 accuracy smoke 通过（仓自报，无独立复测）：Qwen3-30B-A3B、`tensor_parallel_size=2`、`enable_expert_parallel=True`、`max_model_len=4096`——gsm8k strict-match 0.8939（阈值 0.89）、gsm8k flexible-extract 0.856（阈值 0.85）、ceval-valid acc 0.8373（阈值 0.84 内）。
- 信号 2 修复的验证为功能性：Llama-4-Scout-17B 起服务并正确图文问答；source 未给 before→after 数值指标。

## Evidence

- 信号 1：[npu-moe-init-routing-v2-的-active-expert-range-只吃-int-由-torch](https://github.com/vllm-project/vllm-ascend/pull/5521) — 下探 [vllm-ascend-pr-5521-smoke-bugfix-moe-init-routing-v2-active-expert-range-use-int-type](https://github.com/vllm-project/vllm-ascend/pull/5521)；merge sha `bdc721d35a25d0ec9174c3c52881b1656c4a3367`；改动落在 `vllm_ascend/ops/fused_moe/fused_moe.py`（`.item()`）与 `vllm_ascend/ops/fused_moe/token_dispatcher.py`（tensor/int 归一）。
- 信号 2：[vllm-ascend-融合-moe-接入-custom-routing-function-时须回传-int32-top](https://github.com/vllm-project/vllm-ascend/issues/495) — 下探 [vllm-ascend-issue-495-bug-notimplementederror-custom-routing-function-is-not-supported-now](https://github.com/vllm-project/vllm-ascend/issues/495)；merge sha `e56447033889ca95df512208cab22ef832bfdf07`；改动落在 `vllm_ascend/ops/fused_moe.py` 的 `select_experts`；报错行 `select_experts:239`。

## 相关

- [double-routing](../../concepts/techniques/double_routing.md) — `npu_moe_init_routing_v2` 重排 + all-to-all + finalize_routing 的多算子路由链路，本页两个 dtype 契约均落在其入口算子上。
- [moe-dispatch-combine-v2](../../concepts/techniques/moe_dispatch_combine_v2.md) — 把该路由链路收敛为一体化融合算子的 V2 替代路径。
- [expert-parallel](../../concepts/parallelism/expert_parallel.md) — EP 场景下本地专家数由 expert-map 派生，是信号 1 的高发前提。