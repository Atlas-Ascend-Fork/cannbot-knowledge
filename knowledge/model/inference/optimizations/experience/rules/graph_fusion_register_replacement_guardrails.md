---
type: Optimization
title: torchair register_replacement 图融合三守则：head_dim 硬门控 / scale 直传免冗余 / extra_check 拒跨流
description: torchair/npugraph_ex register_replacement 图融合三守则（写 Ascend 图后端融合 pass 的可迁移规则）：(1) head_dim 布局硬门控——QKNorm+RoPE 融合(qkv_rmsnorm_rope)按 head_dim/q_hidden_size/kv_hidden_size 组织，注册硬门控到 head_size==128 且 dtype∈{bf16,fp16}，非 128 直接不注册 pattern、仅打 debug 日志、无回退，运行时融合静默失效不报错；(2) 量化 scale 直传——W8A8 下 npu_add_rms_norm_quant 融合的 replacement 不要现算 1./scale（会往图里插入 reciprocal 等冗余算子），该算子当前实现直接吃 scale 本身，倒数逻辑交给 torch.ops.vllm.quantize，pattern 端把 scale 与 scale_reciprocal 作独立输入传入；契约随算子版本变，跨版本以实际算子签名为准；(3) extra_check 拒跨流——register_replacement 用 extra_stream_scope_check 遍历 match 内 call_function 节点的 stream_label(挂 fx node meta)，多个不同非默认流或默认流与非默认流混用则返回 False 拒绝融合，因融合 kernel 不支持跨 stream、跨流融合会破坏多流并行语义。参考实现 vLLM-Ascend v0.13.0 npugraph_ex graphex_qknorm_rope_fusion_pass/graphex_norm_quant_fusion_pass，验证模型 Qwen3-32B/Qwen3-235B-A22B-W8A8/Qwen3-8b-w8a8。涉及 torchair、npu-graph-mode、multi-stream、QK-Norm、RMSNorm、RoPE、W8A8 量化、fx graph pattern fusion。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5721
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# torchair register_replacement 图融合三守则：head_dim 硬门控 / scale 直传免冗余 / extra_check 拒跨流

## 适用场景

在 Ascend 图编译后端（[npu-graph-mode](../../../concepts/techniques/npu_graph_mode.md)，含 [torchair](../../../concepts/frameworks/torchair.md) 的 `ge_graph` 与 `npugraph_ex`）下，通过 `torchair.register_replacement(search_fn, replace_fn, example_inputs, extra_check)` 把一串小算子的 fx 图 pattern 替换成单个融合 kernel（典型如 QKNorm+RoPE → `qkv_rmsnorm_rope`、AddRMSNorm+Quant → `npu_add_rms_norm_quant`）。当你在写这类融合 pass、或在诊断"pass 开了但融合没生效 / 图里多了冗余算子 / 多流场景下融合破坏并行语义"时，本页给三条与融合算子布局契约、量化算子契约、多流调度耦合的守则。

三条守则各自独立，可分别核对；它们的共性是：**融合 kernel 对 shape 布局 / 标量方向 / 流归属都有硬契约，register_replacement 层要么在注册时门控、要么在 replacement 里对齐、要么用 `extra_check` 拒绝不合契约的 match**，而不是让运行时静默走进"没融合上"或"跨流误融合"。

三条守则对应融合生命周期的三个阶段：head_dim 是注册期门控（满足条件才注册融合），scale 直传是替换期契约（不在图里现算倒数），extra_check 拒跨流是匹配期守卫。

## 守则一：head_dim 布局硬门控（不满足直接不注册，无回退）

QKNorm+RoPE 类融合（对 per-head 的 q/k 先做 RMSNorm、再做 RoPE，如 QK-Norm 结构的 [qwen3-moe](../../../concepts/models/qwen3_moe.md) 族）把 `QKV split -> npu_rms_norm(q) -> npu_rms_norm(k) ->（可选 +q_bias/+k_bias）-> npu_apply_rotary_pos_emb` 替换为单算子 `torch.ops.vllm.qkv_rmsnorm_rope`。

融合的 `example_inputs` / `get_inputs()` 按 `head_dim` 构造，替换算子按 `head_dim` / `q_hidden_size=num_heads*head_dim` / `kv_hidden_size=num_kv_heads*head_dim` 组织。因此**注册被硬门控到 `head_size == 128`**：用「第一层 Attention」的 `head_size` 代表全模型，非 128 则**不注册该 pattern、仅打 debug 日志、无任何回退路径**——head_dim 非 128 的模型即使开了 `enable_npugraph_ex`，运行时逐项核对会发现融合没生效、且**不报错**。

另有一道前置门控（在 head_dim 判定之前先执行）：模型 `dtype` 必须 ∈ {bf16, fp16}，否则整 pass 早退。

```python
dtype = vllm_config.model_config.dtype
if dtype not in (torch.bfloat16, torch.float16):
    logger.debug("QKNorm and Rope fusion not enabled: unsupported dtype %s", dtype)
    return
attn_layers = get_layers_from_vllm_config(vllm_config, Attention)
if len(attn_layers) == 0:
    return
layer = next(iter(attn_layers.values()))
for epsilon in [1e-6, 1e-5]:              # 覆盖两个 RMSNorm epsilon
    if layer.head_size != 128:
        logger.debug("QKNorm and Rope fusion not enabled: head_dim %d is not equal of 128", layer.head_size)
        continue                          # 硬门控：非 128 直接跳过注册
    GraphEXQKNormRopeFusionPattern(vllm_config, head_dim=layer.head_size, ...).register()
    GraphEXQKNormRopeFusionPatternWithBias(...).register()
```

融合覆盖两个 RMSNorm epsilon（1e-6、1e-5），并有 WithBias 变体（RMSNorm 后加 `q_bias`/`k_bias`，替换算子传 `q_bias`/`k_bias`，否则传 None）。

**给 agent 的动作**：诊断"融合 pass 开了但没生效"时先核 head_dim 与 dtype——这类融合对 head_dim 有**固有布局约束**，非 128 的模型该融合天然不适用，不是配置漏开；这条约束系于 NPU 融合算子对 head_dim 的布局假设，属 QK-Norm 结构族的可迁移判断。

## 守则二：量化 scale 直传，别在图里现算 `1./scale`（否则插入冗余 reciprocal）

针对 W8A8（[w8a8c8](../../../concepts/quantization/w8a8c8.md)）下 AddRMSNorm+Quant 融合（`npu_add_rms_norm_quant`，含普通 / WithBias / SP all-gather 变体）：

**不要做**：在 replacement 里对量化 scale 计算 `1.0 / scale` 再传给融合算子。历史实现曾这样写并附注释「The inverse of scale is required by npu_add_rms_norm_quant kernel which is opposite to the npu_quantize kernel.」——即当时以为该算子要吃 scale 的倒数（与 `npu_quantize` 相反）。

**为何不要**：该融合算子的当前实现**直接消费 scale 本身**。在图里现算 `1./scale` 会额外引入两个冗余算子（如 reciprocal）——图融合的目的就是削算子，这里反而往图里加算子。

**正确做法**：replacement 直接传 `scale`；scale 的倒数 `scale_reciprocal` 作为独立输入传给量化算子 `torch.ops.vllm.quantize`，同样不在图里现算（pattern 端把 scale 与其预先算好的倒数分别作为独立输入传入）。

```python
# pattern 端：scale 与倒数各作独立输入，不在图里现算
torch.ops.vllm.quantize(out0, scale, scale_reciprocal, offset)
# replacement 端：融合算子直接吃 scale
output = torch.ops.npu.npu_add_rms_norm_quant(
    rms_norm_input, residual, rms_norm_weight, scale, offset, epsilon=self.eps)  # 直接 scale，不是 1./scale
# WithBias 变体额外传 beta=bias
# 对比被删旧版：npu_add_rms_norm_quant(..., 1.0 / scale, offset, epsilon=...)
```

**适用边界**：这是**该算子当前版本的契约**（`npu_add_rms_norm_quant` 吃 scale 本身），不是普适的「量化 scale 永远直接传」规则——旧版注释表明历史上曾需传倒数，故**跨版本前须以实际算子签名为准**。「消除冗余算子 + 无精度问题」在 Qwen3-8b-w8a8 与 Qwen3-235B-A22B 网络上验证成立。

## 守则三：`extra_check` 拒绝跨流匹配（融合不支持跨 stream）

在 Ascend 多流调度（[multi-stream](../../../concepts/techniques/multi_stream.md)）下，图里不同算子可能被打上不同的 `stream_label`（挂在 fx node 的 `meta`）。一个融合算子把多个小算子合成一个 kernel 执行，**若被合并的原算子分布在不同流上，融合会破坏原本的多流并行语义 / 不被算子支持**。因此匹配前须先核对整个 match 是否落在同一个流内——用 `register_replacement` 的 `extra_check` 钩子做这件事，不合流的 match 直接拒绝替换。

vLLM-Ascend 把该检查抽为公共 util `extra_stream_scope_check(match)`，作为**所有** `register_replacement(..., extra_check=extra_stream_scope_check)` 的额外校验：遍历 match 里所有 `call_function` 节点的 `stream_label`，出现多个不同非默认流、或默认流与非默认流混用 → 判跨流、拒绝融合。

```python
non_default_streams = set(); has_default = False
for node in match.nodes:
    if node.op == "call_function":
        s = node.meta.get("stream_label")
        if s is None:
            has_default = True
        else:
            non_default_streams.add(s)
            if len(non_default_streams) > 1:
                return False   # 多个不同非默认流 -> 拒绝
if has_default and len(non_default_streams) > 0:
    return False               # 默认流与非默认流混用 -> 拒绝
return True                    # 全默认 / 全同一非默认流 -> 允许
```

判定表：全默认流 → 允许；全同一非默认流 → 允许；两个不同非默认流 → 拒绝；默认流+非默认流混用 → 拒绝；空匹配 → 允许。

**给 agent 的动作**：写任何 NPU 图融合 pattern 时都要加同流校验，避免跨流误融合把并行语义合没了。适用面限定到 torchair `register_replacement` 型图融合；「融合不支持跨流」的因果来自守卫与代码注释本身，未见独立算子文档佐证，不外推到所有 NPU 融合形态。

## 参考实现及其约束

参考实现：vLLM-Ascend（vLLM v0.13.0）`npugraph_ex` 图后端的 `graphex_qknorm_rope_fusion_pass.py`（守则一）、`graphex_norm_quant_fusion_pass.py`（守则二，替代被删的 `add_rms_norm_quant.py`）、`npugraph_ex_passes/utils/npugraph_ex_utils_check.py` 的 `extra_stream_scope_check`（守则三）。开启配置 `additional_config={"enable_npugraph_ex": True}` + `compilation_config.cudagraph_mode=FULL_DECODE_ONLY`；验证模型 Qwen3-32B（QKVNormRope）、Qwen3-235B-A22B-W8A8（QKVNormRopeWithBias）、Qwen3-8b-w8a8。

`head_size==128`、`enable_npugraph_ex` 开关名、具体 epsilon 列表、`vllm.quantize` / `npu_add_rms_norm_quant` 签名是该参考实现的落点与当前算子版本契约；「按融合算子布局契约门控注册」「量化 scale 方向以算子实际签名为准、别在图里现算倒数」「`extra_check` 拒跨流」是跨模型可迁移的图融合写法。上游描述称 W8A8 模型上该融合显著提升吞吐（无独立复测数字）。

## 相关经验
- [aclgraph 图捕获前 monkeypatch upstream graph_captu](../../../runbooks/runtime/aclgraph_capture_patch_module_base_vs_mro.md)

## Evidence

- 合并态 diff（merge sha 1402cf68…）：`GraphEXQKNormRopeFusionPass.__init__` 中 `head_size != 128 -> continue` 硬门控 + dtype ∈ {bf16,fp16} 早退，WithBias 变体与 `torch.ops.vllm.qkv_rmsnorm_rope(q_bias=..., k_bias=...)` 签名一致。溯源下探 [vllm-ascend-pr-5721-graph-fusion-add-qkvnormrope-and-qkvnormropewithbias](https://github.com/vllm-project/vllm-ascend/pull/5721)
- 合并态 diff（merge sha 1402cf68…）：新版 `graphex_norm_quant_fusion_pass.py` replacement 直接传 `scale`、pattern 用 `vllm.quantize`；被删 `add_rms_norm_quant.py` 含 `1.0 / scale` 及「inverse of scale is required」注释。「1./scale 引入冗余算子、改直传无精度问题」为维护者 review 与作者验证回复所载。溯源下探 [vllm-ascend-pr-5721-graph-fusion-add-qkvnormrope-and-qkvnormropewithbias](https://github.com/vllm-project/vllm-ascend/pull/5721)
- 合并态 diff（merge sha 1402cf68…）：`extra_stream_scope_check` 由内联 `_extra_stream_scope_check` 抽为公共 util，在 `graphex_norm_quant_fusion_pass.py` 与 `graphex_qknorm_rope_fusion_pass.py` 的每个 register_replacement 作为 extra_check 传入；单测覆盖与判定表一致。溯源下探 [vllm-ascend-pr-5721-graph-fusion-add-qkvnormrope-and-qkvnormropewithbias](https://github.com/vllm-project/vllm-ascend/pull/5721)