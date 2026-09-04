---
type: Runbook
title: MLA 开图模式硬约束 num_heads/num_kv_heads ∈ {32,64,128}（每 rank 比值出集合则图编译期 EZ9999 / CheckMlaAttrs 失败）
description: 'MLA 结构模型（DeepSeek V2-Lite/V3/R1）启用 torchair 图模式（npu-graph-mode, torchair_graph_config.enabled）时，昇腾 MLA/FusedInferAttentionScore（FIA）融合算子有固有 shape 契约：每 rank 的 num_heads/num_kv_heads（queries-per-kv 比值，按 tensor-parallel/TP 切分后计）必须 ∈ {32,64,128}。比值出集合会在图编译期（fx2ge_converter.compile → graph.compile，非运行期）由 tiling 校验 CheckMlaAttrs（incre_flash_attention_tiling_check.cc）抛 EZ9999 "numHeads / numKvHeads = 8, MLA only support {32, 64, 128}"、Compile graph failed。DeepSeek-V2-Lite 只有 16 个 attention head、比值恒出集合，图模式恒不支持（源标 TODO: support numHeads/numKvHeads<16 in MLA kernel）；V3/R1 头数够但 TP size 选得不当会把每 rank 比值推出集合。修法：开图模式前先核 TP 切分后每 rank num_heads/num_kv_heads 是否 ∈ {32,64,128}——V2-Lite 改走 eager/非图模式，V3/R1 调整 TP size 使比值落回集合。参考实现 vllm-ascend 在 attention.py/mla_v1.py 用 _ALLOWED_NUM_QUERIES_PER_KV=[32,64,128] 断言把算子内层报错前移成框架 fail-fast + FAQ，但约束本身来自融合算子、非框架限制。区别于 FIA 无量化 MLA 路径 group_num ∈ 2 的幂（561002/CheckFeatureMlaNoQuantShape）那条不同约束。'
tags:
- task.debugging
- topic.attention
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/972
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MLA 开图模式硬约束 num_heads/num_kv_heads ∈ {32,64,128}（每 rank 比值出集合则图编译期 EZ9999 / CheckMlaAttrs 失败）

## 信号（现象）

对 [MLA](../../concepts/modules/mla.md) 结构模型启用图模式（[npu-graph-mode](../../concepts/techniques/npu_graph_mode.md)，`torchair_graph_config.enabled=True`）时，图 **编译期**（`fx2ge_converter.compile → graph.compile`，非运行期）直接失败，报错栈关键行来自 [FusedInferAttentionScore（FIA）](../../concepts/kernels/fused_infer_attention_score.md) 的 tiling 检查：

```
RuntimeError: EZ9999: Inner Error!
EZ9999: numHeads / numKvHeads = 8, MLA only support {32, 64, 128}.[FUNC:CheckMlaAttrs][FILE:incre_flash_attention_tiling_check.cc][LINE:1218]
  ... Call Calculate op:FusedInferAttentionScore running param failed
  ... Compile graph failed, error code:1343225857
```

诊断由算子自陈：`CheckMlaAttrs` 直接列出支持集 `{32, 64, 128}` 与观测到的 `numHeads/numKvHeads` 比值（此处 `=8`，为报告者当时 [TP](../../concepts/parallelism/tensor_parallel.md) 切分后每 rank 的实际值）。命中该现象即落进本页范围。若在框架层被 fail-fast 断言前移（见「参考实现及其约束」），则会先看到框架侧带 `{32,64,128}` 集合的 assert 提示，而非算子内层的 EZ9999。

## 触发条件

- 走 MLA 注意力路径的模型（DeepSeek 系：V2-Lite / V3 / R1 等）。
- 启用图模式（torchair GE 图 / 图捕获），使 FIA/MLA 融合算子进入图编译期 tiling。
- **每 rank** 的 `num_heads / num_kv_heads`（即 queries-per-kv 比值，按 [TP](../../concepts/parallelism/tensor_parallel.md) 切分后计）**不落在** `{32, 64, 128}`。
  - 结构恒违约：DeepSeek-V2-Lite 原生只有 16 个 attention head（kv_head=1 时比值=16），任何切分都出集合，图模式恒不支持。
  - 配置违约：V3/R1 头数够，但 TP size 选得不当会把切分后的每 rank 比值推出 `{32,64,128}`（报错里的 `=8` 即此类）。

## 根因

这是昇腾 **MLA/FIA 融合算子的固有 shape 契约**，与具体 commit 无关：图模式下 FIA 的 tiling 校验 `CheckMlaAttrs`（`incre_flash_attention_tiling_check.cc`）只接受 `numHeads/numKvHeads ∈ {32, 64, 128}`。该比值是 **每 rank 的 queries-per-kv 比**，随 TP 切分变化——因此约束是「切分后每 rank 值」而非全模型头数。归因在算子层（融合算子不支持集合外比值），非建模代码问题。任何在图模式下用比值不在集合内的 MLA 模型都会撞上同一 EZ9999。

> 该比值约束属图模式下 MLA 路径的算子级 shape 契约。FIA 另有一条相邻但不同的硬约束：无量化 MLA 路径（rope + q/k head_dim=512）要求 `group_num ∈ {1,2,4,8,16,32,64,128}`（2 的幂），触发 561002 / `CheckFeatureMlaNoQuantShape`，见 [fia-mla-noquant-group-num-power-of-two](../compilation/fia_mla_noquant_group_num_power_of_two.md)。二者集合与错误码不同，勿混淆。

## 修法

在对 MLA 模型开图模式**前**，先核 `num_heads / num_kv_heads`（**按 TP 切分后每 rank 计**）是否 ∈ `{32, 64, 128}`——遇到 EZ9999 / `CheckMlaAttrs` 也先按这条硬约束核比值，而非怀疑建模代码：

- **头数结构性不足（如 [MLA](../../concepts/modules/mla.md) 只有 16 头的 V2-Lite）**：图模式不支持，改用 eager / 非图模式启动推理；参考实现将 `numHeads / numKvHeads < 16` 的 MLA kernel 支持标为 TODO，尚未实现。
- **V3/R1 头数够但比值出集合**：调整 [TP](../../concepts/parallelism/tensor_parallel.md) size，使切分后每 rank 比值落回 `{32,64,128}`。

## 参考实现及其约束

vllm-ascend 的处理是**把算子内层晦涩报错前移成框架层 fail-fast 断言 + FAQ**，而非放宽算子约束（约束仍由算子持有）：

- `vllm_ascend/attention/attention.py`：`_ALLOWED_NUM_QUERIES_PER_KV = [32, 64, 128]`；在 `torchair_graph_enabled` 分支下 `assert self.num_queries_per_kv in _ALLOWED_NUM_QUERIES_PER_KV`。
- `vllm_ascend/attention/mla_v1.py`：`self.num_queries_per_kv = self.num_heads // self.num_kv_heads`，同一断言。
- `docs/source/faqs.md` FAQ#15：'The allowed number of queries per kv when enabling both MLA and Graph mode only support {32,64,128} ... not supported for DeepSeek-V2-Lite, as it only has 16 attention heads'。

> 这是该参考实现（vllm-ascend + [torchair](../../concepts/frameworks/torchair.md) 图模式）落在框架侧的断言与文档，`{32,64,128}` 这条限制本身来自昇腾 FIA/MLA 融合算子、不是框架限制。约束未被放宽；V2-Lite 的图模式支持仍为 TODO。

## Evidence

- **合并态 diff**：vllm-project/vllm-ascend@8dd686dfa20d8f577cd63fb751ce0a7a98f2f516 的 `attention.py` / `mla_v1.py` 两处断言（`_ALLOWED_NUM_QUERIES_PER_KV=[32,64,128]`、`num_queries_per_kv = num_heads // num_kv_heads`）与 `docs/source/faqs.md` FAQ#15，对上报错文案与 `{32,64,128}` 集合；同一改动含 `# TODO: support numHeads / numKvHeads < 16 in MLA kernel`，PR body 记 'Adjusting tp size is required when running deepseek-v3/r1 with graph mode'。
- **维护者确认**：维护者（collaborator）明确 'graph mode not support deepseek-v2-lite currently, cause there is only 16 attention header ... not allowed by the fused op'。
- **运行时 trace**：EZ9999 `numHeads / numKvHeads = 8, MLA only support {32, 64, 128}` 于 `CheckMlaAttrs`（`incre_flash_attention_tiling_check.cc:1218`），发生在 [FusedInferAttentionScore](../../concepts/kernels/fused_infer_attention_score.md) 的 tiling / 图 compile 阶段。
- **边界**：`=8` 为报告者 TP 配置下每 rank 的比值，据 FAQ 该约束按「TP 切分后每 rank 比值」判定；V2-Lite 图模式支持仍为 TODO。
  - 溯源下探：[vllm-ascend-issue-972-new-model-deepseek-v2-lite-running-on-graph-mode](https://github.com/vllm-project/vllm-ascend/issues/972)

<!-- cannbot:related:start -->
## 相关

- [FIA 的 MLA 无量化路径硬约束 group_num ∈ {2 的幂}（否则 561002 / CheckFeatureMlaNoQuantShape 失败）](fia_mla_noquant_group_num_power_of_two.md)（`related`）：FIA 图模式约束为“图模式下 FIA 的 tiling 校验 `CheckMlaAttrs`（`incre_flash_attention_tiling_check.cc`）只接受 `numHeads/numKvHeads ∈ {32, 64, 128}`。”，FIA MLA 无量化路径则限定另一条“group_num 为 2 的幂且落在 `{1, 2, 4, 8, 16, 32, 64, 128}`”的 CheckFeatureMlaNoQuantShape 合同；对照两类约束可按错误码和支持集避免把两种 FIA/MLA 编译失败混诊。
<!-- cannbot:related:end -->
