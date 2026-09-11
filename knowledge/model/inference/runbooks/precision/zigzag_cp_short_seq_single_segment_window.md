---
type: Runbook
title: zigzag-CP 下短序列全部落入单段（last_rank==0）→ 滑动窗口 last-window 元数据负索引回卷静默取错
description: zigzag-CP 下短序列全部落入单段（last_rank==0）→ 滑动窗口 last-window 元数据负索引回卷静默取错。滑动窗口注意力 + zigzag-cp prefill，喂短序列时结果异常，但不报错、不崩溃——是静默 correctness bug：短序列 case 的 win_kv / last_win（最后 window_size 个有效 token 构成的窗口）内容或 position_ids 错误，滑窗看进了不该看的 token。 长序列同一路径正常；症状只在序列短到有效 KV 全部落进单个 CP 段时出现。
tags:
- task.debugging
- topic.attention
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/459
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# zigzag-CP 下短序列全部落入单段（last_rank==0）→ 滑动窗口 last-window 元数据负索引回卷静默取错

## 信号（症状，供对号入座）

- **滑动窗口注意力** + [zigzag-cp](../../concepts/parallelism/zigzag_cp.md) prefill，喂**短序列**时结果异常，但**不报错、不崩溃**——是静默 correctness bug：短序列 case 的 `win_kv` / `last_win`（最后 `window_size` 个有效 token 构成的窗口）内容或 `position_ids` 错误，滑窗看进了不该看的 token。
- 长序列同一路径正常；症状**只在序列短到有效 KV 全部落进单个 CP 段时**出现。

## 触发条件

序列按 zigzag 切成 `cp_segment_num` 个段、每段有各自的 `split_kv_len` / `split_position_ids`。当输入序列**短**到所有有效 KV 都落在**第 0 段**时——即
```python
last_rank_before_zz = ((split_kv_len > 0).sum(dim=1) - 1).item()   # == 0
```
且该段有效长 `last_kv_len < window_size`（整段不够一个完整窗口），就会触发。

## 根因

「last window」的取法原本只有两个分支，且**隐含假设「最后一个有效段之前还有段可借」**（旧代码注释直白写 `last_rank ... should be >= 1`）：

- 若最后有效段的 `last_kv_len >= window_size`：整段够一个窗口，直接用整段；
- 否则（`last_kv_len < window_size`）：用最后有效段的前缀，再**借上一段** `segment[last_rank - 1]` 的尾部拼满 `window_size`。

当 `last_rank == 0` 且 `last_kv_len < window_size` 时会走进 else 分支去取 `segment[last_rank - 1]` → `segment[-1]`。**Python 负索引 `-1` 不报错**，而是静默回卷取到**最后一段**的窗口 / `position_ids` 拼进来 → 短序列滑窗内容/位置错误。这是一类通用坑：**任何按「N−1 借上一段」写的分段元数据，若不显式处理 `N==1` 边界，`N−1` 就成 `-1`、Python 索引静默回卷、无报错**。

## 修法

补一条**显式的 `last_rank == 0` 分支**：段 0 即全部有效序列所在段、无「上一段」可借，直接用段 0 自身窗口；并把 `last_kv_len` 上提为标量（`.item()`）供 `>= window_size` 判断统一驱动，避免张量与标量比较歧义。

`Attention.forward`（`all_win` 取窗口处）：
```python
if last_kv_len >= self.window_size:
    last_win = all_win[last_rank]
elif last_rank == 0:                      # 新增：段 0 自身即窗口，无上一段可借
    last_win = all_win[last_rank]
else:
    last_win = all_win[last_rank, :, :last_kv_len]
    second_last_win = all_win[last_rank - 1]
```

`AttnMetaData`（`position_ids_last_win`）对称补一条 `elif last_rank_before_zz == 0` 分支，直接取段 0 起始处的 `:window_size`，不再 `cat` 上一段尾部。

注意此修法是让模型**支持**短序列（把有效 token 正确放进 `win_kv`），**不是拦截/拒绝**短序列（维护者澄清：「这个不拦截短序列」）——故补分支而非 `raise`/`assert`。

## 验证 / 边界

- 修后短序列（有效 KV 全在段 0）的滑窗元数据取到「段 0 起始处的有效 token」，不再负索引回卷到最后一段。
- 无 before→after benchmark 数字，价值在 correctness 边界修复本身。
- 范围限定到 [deepseek-v4](../../concepts/models/deepseek_v4.md) 的 CP 滑动窗口实现；「负索引静默回卷」为对 Python 索引语义的据实推断（非显式崩溃/报错），已标为静默 correctness、不外推为特定报错文本。
- 本页是 [causal-cp-prefill-zigzag-actual-seqlens](../../optimizations/experience/rules/causal_cp_prefill_zigzag_actual_seqlens.md) 头尾配对方案在**短序列单段**下的边界失效点；上 zigzag-CP 前先确认序列不会短到落入单段（或已补 `N==1` 分支）。

## Evidence

- **diff 事实**（clone `@b27dd963cd7b,e306e5aa82dc`，`curl` merged patch）：`models/deepseek-v4/models/modeling_deepseek.py::Attention.forward` 新增 `elif last_rank == 0` 分支（+2/-0）、`models/deepseek-v4/models/modules/attention_data.py::AttnMetaData` 新增 `elif last_rank_before_zz == 0` 分支并把 `last_kv_len` 上提为 `.item()` 标量、删除旧注释 `should be >= 1,`（+7/-4）；diff 与断言逐条对上。
- **维护者确认**：reviewer 问「加拦截会不会一碰短序列就挂」，作者答「这个不拦截短序列」，佐证改动是**支持**短序列而非拦截，与「补分支而非 raise」的代码一致。
- 溯源下探：[cann-recipes-infer-pr-459-fix-deepseek-v4-cp-short-sequence-window](https://gitcode.com/cann/cann-recipes-infer/merge_requests/459)