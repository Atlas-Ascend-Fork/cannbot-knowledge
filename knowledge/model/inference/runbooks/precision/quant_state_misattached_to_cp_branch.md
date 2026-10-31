---
type: Runbook
title: SFA C8 Prefill 在 cp_size=1 时缺少 per-token scale
description: 当前MLAProlog已在CP分支之外填投影scale；保留旧PR失败签名的诊断方法，避免重复修复已纠正分支。
tags:
- task.debugging
- topic.attention
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/76
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:49:38Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      parallelism:
        none_of:
        - cp
---

# SFA C8 Prefill 在 cp_size=1 时缺少 per-token scale

## 信号（症状，供对号入座）

- 开启 SFA C8 后，未启用 [CP](../../concepts/parallelism/context_parallel.md) 的 `cp_size=1` 配置在 Prefill 报错，Decode 正常；具体错误文本源未披露。
- 已知落点是 [DeepSeek-V3.2-Exp](../../concepts/models/deepseek_v3_2_exp.md) 的 [MLA-Prolog](../../concepts/kernels/mla_prolog.md) 与 [SFA](../../concepts/kernels/sparse_flash_attention.md) 路径，且启用相应C8量化。`cp_size=1` 仅表示 CP 度为 1，不能据此推断总设备数或其他并行度。

## 触发条件

旧故障是在启用C8量化时+ 该特性所需的状态填充语句恰好被写在某并行分支（`if cp_size > 1:`）内 + 实际并行度使该分支被跳过（`cp_size=1`）。

`cp_size>1` 的长上下文 CP 优化任务不满足这个已知故障的触发条件；仅因查询出现 CP 或 Prefill，不能把本页当作该任务的故障诊断。Scope 用 Prefill 与 `parallelism.none_of: [cp]` 记录已知必要条件：已确认启用 CP 时排除，未说明 CP 状态时保留为未知。满足这些声明项后，仍须核对实际量化配置、模型路径、固定版本及是否已包含修复，不能据此确认目标环境仍有该故障。

## 当前探针与已修正状态

当前mlaprolog_prefill在CP恢复与写缓存之后，独立按weight_quant_mode==1填c8_input_dict['pertoken_scale']=dequant_q_norm，已位于enable_cp分支之外。旧PR报告的量化状态误挂CP问题已修正，不能据当前cp_size=1直接判为仍有此缺陷。当前模型用kv_cache_quant_mode/int8及量化配置判定，不再有旧kv_cache_c8布尔接口。

排查同类故障时，记录实际量化模式，比较Prefill/Decode返回的dequant_q_norm、字典键及下游wq_b的dynamic scale；确认只要当前量化投影需要scale，其初始化不被无关并行条件跳过。不要只看到C8和CP关键词就改动已经正确的分支。

若目标代码确实把必需scale赋值放在enable_cp内，先保存输出基线，再移到真实量化门控下，覆盖CP1与CP>1、量化与非量化、Prefill与Decode。不以绕过CP或关闭量化作为已经修复的证明。本次仅核对源码，没有复现原故障。

## 相关

- MLA-Prolog + CP 的 prefill KV cache 写入两段式（另一处 prefill/decode 路径差异易踩的坑）见 [mla-prolog-zigzag-cp-kv-write](../../optimizations/rules/mla_prolog_zigzag_cp_kv_write.md)。
- C8 KVCache 与 PyPTO Lightning Indexer 的互斥约束见 [c8-kvcache-disables-pypto-lightning-indexer](../../optimizations/anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。
- 范围：限定 cann-recipes-infer 本仓 DeepSeek-V3.2-Exp 建模文件 `mlaprolog_prefill`，及可迁移到同类"量化状态被误挂 CP / 并行分支"的失败签名；不外推到整个昇腾栈。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/76)（evidence）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
