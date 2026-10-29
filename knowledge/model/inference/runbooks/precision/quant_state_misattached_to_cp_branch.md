---
type: Runbook
title: SFA C8 Prefill 在 cp_size=1 时缺少 per-token scale
description: DeepSeek-V3.2-Exp 的 C8 状态初始化误放在 cp_size>1 分支，未启用 CP 时 Prefill 缺少 pertoken_scale，而 Decode 正常；将赋值移到量化开关下。cp_size=1 不代表总共只用一张卡。
tags:
- task.debugging
- topic.attention
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/76
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/8bf2846517723eff5bc40970a7c6ec846af1e85d/models/deepseek-v3.2-exp/models/modeling_deepseek.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-23T08:05:13Z'
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
- 已知落点是 [DeepSeek-V3.2-Exp](../../concepts/models/deepseek_v3_2_exp.md) 的 [MLA-Prolog](../../concepts/kernels/mla_prolog.md) 与 [SFA](../../concepts/kernels/sparse_flash_attention.md) 路径，且 `kv_cache_c8=True`。`cp_size=1` 仅表示 CP 度为 1，不能据此推断总设备数或其他并行度。

## 触发条件

开某量化特性（`kv_cache_c8=True`）+ 该特性所需的状态填充语句恰好被写在某并行分支（`if cp_size > 1:`）内 + 实际并行度使该分支被跳过（`cp_size=1`）。

`cp_size>1` 的长上下文 CP 优化任务不满足这个已知故障的触发条件；仅因查询出现 CP 或 Prefill，不能把本页当作该任务的故障诊断。Scope 用 Prefill 与 `parallelism.none_of: [cp]` 记录已知必要条件：已确认启用 CP 时排除，未说明 CP 状态时保留为未知。满足这些声明项后，仍须核对 `kv_cache_c8`、模型路径、固定版本及是否已包含修复，不能据此确认目标环境仍有该故障。

## 根因 = 失败签名

**特性 X 必需的状态赋值，被误挂在与 X 无关的条件分支（此处是 CP 度）里；跳过该分支的配置就静默丢掉该状态。**

具体：下游 C8 注意力需要 per-token 反量化 scale `c8_input_dict['pertoken_scale']`（取自 MLA-Prolog 算子 `npu_mla_prolog_v3` 的第 5 个返回 `dequant_q_norm`）。该键的填充语句被写在 `if cp_size > 1:` 块内的 C8 子分支里：

```python
if self.cp_size > 1:
    ...
    if self.kv_cache_c8:
        c8_input_dict.update({'pertoken_scale': dequant_q_norm})   # 只在 cp_size>1 时执行
```

当 `cp_size=1` 时整个 `if cp_size > 1:` 块被跳过，`pertoken_scale` 永不写入，下游 C8 注意力拿不到 scale 而报错。

**判据线索**：Decode 路径本就把同一句放在 CP 分支之外、仅由 `if kv_cache_c8:` 守卫，因此已知 bug 只存在于 Prefill 一侧。遇到量化报错依赖某个并行度的现象时，先对比两条路径的初始化与守卫条件，不能仅凭症状就判定根因。

## 修法与可迁移通则

- **修法**：把 `pertoken_scale` 填充从 CP 分支中移出，改由量化开关独立守卫（`if kv_cache_c8:`，与 `cp_size` 无关），使 prefill 与 decode 对齐——只要开 C8 KV cache 就一定填 scale。
- **可迁移通则**：凡"特性 X 必需的状态赋值"落在与 X 无关的条件分支里，跳过该分支的配置就会静默丢状态。**量化 / 特性所需状态应由该特性自己的开关守卫，不由并行度等无关维度守卫**；改动任一注意力路径的量化分支后，务必对拍 prefill vs decode 的守卫条件是否对称。

## 相关

- MLA-Prolog + CP 的 prefill KV cache 写入两段式（另一处 prefill/decode 路径差异易踩的坑）见 [mla-prolog-zigzag-cp-kv-write](../../optimizations/rules/mla_prolog_zigzag_cp_kv_write.md)。
- C8 KVCache 与 PyPTO Lightning Indexer 的互斥约束见 [c8-kvcache-disables-pypto-lightning-indexer](../../optimizations/anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。
- 范围：限定 cann-recipes-infer 本仓 DeepSeek-V3.2-Exp 建模文件 `mlaprolog_prefill`，及可迁移到同类"量化状态被误挂 CP / 并行分支"的失败签名；不外推到整个昇腾栈。

## Evidence

- **diff 与固定源码**（`8bf2846517723eff5bc40970a7c6ec846af1e85d`）：PR 删除 CP 分支内的赋值并在分支外按 `if self.kv_cache_c8` 补回；同提交 `mlaprolog_prefill` 的约 L1072–L1098 展示修复后位置，`mlaprolog_decode` 的约 L1161–L1162 已按量化开关赋值。PR 描述和测试条件明确为 `cp_size=1`、SFA C8；来源未给具体报错文本。本次只做静态核对，没有执行模型或复现故障。
- 溯源下探：[cann-recipes-infer-pr-76-fix-sfa-c8-cp-size-1-bugfix](https://gitcode.com/cann/cann-recipes-infer/merge_requests/76)
