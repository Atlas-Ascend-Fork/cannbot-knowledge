---
type: Guide
title: aclgraph decode 稳态期优化：warm-up 后 skip_guard_eval_unsafe 跳 guard 复评 + custom op reinplace 映射
description: 已在 acl_graph（torch.compile + ACLGraph 捕获）跑通 decode、想再压 host 侧开销时的两项稳态优化。前提：exe_mode == "acl_graph" 且 torch.compile 编译路径生效的 decode；仅对非 warm-up 的稳态步开启——warm-up 首编译步必须保留 guard、正常编译（warm-up 阶段本身的静默长耗时 / dummy 缓存坑见 warmup-silent-slow-and-dummy-cache）。ge_graph 等非 acl_graph 路径不适用。图模式启用骨架见 graph-mode-decode-only-compile-backends。
tags:
- task.debugging
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/236
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/204
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# aclgraph decode 稳态期优化：warm-up 后 skip_guard_eval_unsafe 跳 guard 复评 + custom op reinplace 映射

## 适用场景

已在 acl_graph（torch.compile + ACLGraph 捕获）跑通 decode、想再压 host 侧开销时的两项稳态优化。前提：`exe_mode == "acl_graph"` 且 torch.compile 编译路径生效的 decode；**仅对非 warm-up 的稳态步开启**——warm-up 首编译步必须保留 guard、正常编译（warm-up 阶段本身的静默长耗时 / dummy 缓存坑见 [warmup-silent-slow-and-dummy-cache](../../../runbooks/performance/warmup_silent_slow_and_dummy_cache.md)）。ge_graph 等非 acl_graph 路径不适用。图模式启用骨架见 [graph-mode-decode-only-compile-backends](../../../optimizations/experience/rules/graph_mode_decode_only_compile_backends.md)。

## 手段 1：稳态 decode 跳过 torch.compile 的 guard 复评

torch.compile 每步默认要复评 guard 判断是否需重编译；稳态 decode 形状/配置固定，跳过复评即省掉每步 guard 检查开销。warm-up 后（编译完成、cache 命中后）用 `torch.compiler.set_stance(skip_guard_eval_unsafe=True)` 包裹前向：
```python
# warm-up 步正常编译带 guard；后续稳态步跳过 guard 复评
if exe_mode == "acl_graph" and skip_guard and not warm_up:      # 或 enable_cache_compile and not warm_up
    with torch.compiler.set_stance(skip_guard_eval_unsafe=True):
        logits, prev_hidden_states = model_runner.model.decode(**model_inputs)
else:
    logits, prev_hidden_states = model_runner.model.decode(**model_inputs)
```
- **风险（名义 unsafe）**：预热后不再复评 guard，若输入形状/配置在预热后变化不会被 guard 拦截，可能用错编译产物。故**仅在稳态形状确定的 decode 用**（保证 decode 形状/配置在 warm-up 后不变）。
- **前置**：warm-up 阶段需首次编译后，后续稳态步才使用跳过 guard 校验（维护者确认）。
- **rollback**：关掉该开关（回到每步复评 guard）。

## 手段 2：为 custom op 注册 functional→in-place 的 reinplace 映射

acl_graph decode 前把 functional 版 custom op 映射为 in-place 版以提性能（本例 [MLA-prolog](../../../concepts/kernels/mla_prolog.md) 的 `npu_mla_prolog_v3`）。TorchAir 提供 `inplaceable_npu_ops` 供更新：
```python
if exe_mode == "acl_graph":
    try:
        from torchair._acl_concrete_graph.graph_pass import (
            inplaceable_npu_ops, InplaceableNpuOp, check_multi_stream_for_multi_reinplace)
        inplaceable_npu_ops.update({
            torch.ops.custom.npu_mla_prolog_v3_functional.default:
                InplaceableNpuOp(inplace_op=torch.ops.custom.npu_mla_prolog_v3.default,
                                 mutated_arg=[9, 10],           # 9=kv_cache, 10=kr_cache 被就地写入
                                 extra_check=check_multi_stream_for_multi_reinplace)})
    except ImportError:
        logging.warning("custom op reinplace needs to update torch_npu version 7.3.0")
```
- **前置**：`torchair._acl_concrete_graph.graph_pass` 需 **torch_npu ≥ 7.3.0**；导入失败则告警并跳过（feature 降级、不报错）。
- **版本背景**：torchair 自某商发起默认策略已改为 reinplace，reinplace 不成功会**静默跳过**该 pass、不再抛 RuntimeError，故旧的 `disable_reinplace_inplaceable_ops_pass = True` 应删除。`mutated_arg` 下标须对应算子最新 IR 声明里被就地写入的入参。

## 参考实现及其约束

参考实现：DeepSeek-V3.2-Exp 的 `Infer.inference`（skip_guard 分支 + reinplace 注册）。`mutated_arg=[9,10]`、torch_npu≥7.3.0 版本门控是该算子/版本的具体落点；"稳态 decode 用 skip_guard_eval_unsafe 省 guard 复评（仅非预热步、须稳态形状）""为 functional custom op 注册 reinplace 映射降开销（带版本门控与降级）"是可迁移的 acl_graph decode 部署手段。收益面向性能，源未给 before→after 数字。

## Evidence

- diff 事实：`exe_mode == "acl_graph"` 且非 warm-up 时用 `torch.compiler.set_stance(skip_guard_eval_unsafe=True)` 包裹 decode；收益无独立数据。溯源下探 [cann-recipes-infer-pr-236-fix-duplicate-creation-of-multi-stream-events-when-mtp-enable-skip-guard](https://gitcode.com/cann/cann-recipes-infer/merge_requests/236)
- diff 事实 + 维护者确认（@f8bb1545）：reinplace 注册块（`mutated_arg=[9,10]`、ImportError 告警文案）+ warm-up 后 skip_guard 分支；reinplace 的版本门控/静默跳过与 skip_guard 的"warm-up 后才跳"由 review 佐证。溯源下探 [cann-recipes-infer-pr-204-feat-dsv3-2-support-acl-graph](https://gitcode.com/cann/cann-recipes-infer/merge_requests/204)

<!-- cannbot:related:start -->
## 相关

- [NPU LLM 图模式启用骨架：decode-only 编译 + ge_graph / acl_graph / npugraph_ex 后端编译入口与配置约束](../../../optimizations/experience/rules/graph_mode_decode_only_compile_backends.md)（`related`）：已在 acl_graph（torch.compile + ACLGraph 捕获）跑通 decode、想再压 host 侧开销时的两项稳态优化。；实现上把 prefill / decode 的 forward 拆成不同方法，**只对 decode 方法** `torch.compile(...)`，prefill 保持 eager。前者是在后者完成 decode-only 编译与预热之后追加 skip_guard/reinplace 的稳态优化步骤。
- [推理 warmup 静默长耗时易误判卡死 + 同质 minibatch 冗余前向可 dummy 缓存跳过](../../../runbooks/performance/warmup_silent_slow_and_dummy_cache.md)（`related`）：warmup 诊断警示“**看似卡死**：warmup 阶段全程无日志输出”，不能在首编译阶段误杀进程；稳态优化则限定“**仅对非 warm-up 的稳态步开启**”，明确跳 guard/reinplace 的启用时点必须等 warmup 完成。
<!-- cannbot:related:end -->
