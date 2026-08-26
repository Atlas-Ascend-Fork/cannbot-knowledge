---
type: Optimization
title: 昇腾性能测量失真陷阱：不代表真实访存的测量输入·折算前被截断的度量口径
description: 昇腾性能测量失真陷阱：不代表真实访存的测量输入·折算前被截断的度量口径。你在昇腾上做算子/推理的性能测量或 profiling，要判断某优化是否真有收益。测量方法本身的两类缺陷会让性能数字系统性失真——测出的「快/慢」不代表真实 workload。测量代码要和被测算法一样被审。
tags:
- task.debugging
- topic.attention
- topic.speculative_decoding
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/37
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/243
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾性能测量失真陷阱：不代表真实访存的测量输入·折算前被截断的度量口径

## 适用场景

你在昇腾上做算子/推理的性能测量或 profiling，要判断某优化是否真有收益。**测量方法本身**的两类缺陷会让性能数字系统性失真——测出的「快/慢」不代表真实 workload。测量代码要和被测算法一样被审。

## 陷阱 1：稀疏 / gather 类算子用不代表真实访存的测量输入

测 [稀疏 FlashAttention](../../../concepts/kernels/sparse_flash_attention.md) 这类按索引 gather KV 的算子性能时，稀疏索引（`sparse_indices`）必须用「在真实 KV 长度范围内、无放回采样的互异块索引」生成，不能用小值域有放回随机（如 `np.random.uniform(0, 16, ...)`）。

为何：小值域有放回随机产生大量重复索引（2048 个槽只有 16 个不同取值、每值平均重复约 128 次），稀疏 gather 实际只触碰极少数 KV 块，工作集极小、复用/命中率异常高，访存足迹与真实 top-k 稀疏选择（覆盖长 KV 的一批**互异**块）不符，测得性能偏乐观、不可信；值域也没覆盖真实 KV 块范围。

正确写法：无放回采样互异索引、采样域贴合真实 KV 有效长度：

```python
idxs = random.sample(range(s2_act - s1 + 1), sparse_block_count)   # 互异、覆盖 [0, KV_len)
sparse_indices = torch.tensor([idxs for _ in range(b * s1 * n2)]) \
    .reshape(b, s1, n2, sparse_block_count).to(torch.int32)
```

（精度对拍口径不变：`np.isclose(rtol=0.005, atol=0.0001)`、`true_ratio > 0.99`。）

## 陷阱 2：折算吞吐前把小数度量 int 截断

[MTP](../../../concepts/techniques/mtp_speculative_decoding.md) 投机解码的等效吞吐折算里，平均接受 token 数（`avg_accepted_num`，`torch.mean(...)`，通常带小数如 2.7）在参与吞吐计算前 `.to(torch.int32)` 截断会向下取整，令 `total_tokens = avg_accepted_num + cnt` 偏低、污染等效推理时间/吞吐——而 MTP 的收益恰恰体现在这个 <1 的小数接受率上，截断后系统性**低估**收益。

正确写法：折算路径用**浮点**均值，int 截断只允许出现在人读日志里：

```python
avg_accepted_num = torch.mean(total_accepted_num)                 # 保留浮点参与折算
logging.info(f"... average accepted num ... {avg_accepted_num.to(torch.int32)}")  # 仅展示转 int
total_tokens = avg_accepted_num + cnt
equivalent_infer_time = process_infer_time(infer_time_rec, total_tokens)
```

## 共性与自检

两者都不是被测算法的问题，而是**测量 harness 自身**让数字失真：陷阱 1 是测量输入不代表真实访存，陷阱 2 是度量口径在折算前被有损截断。自检：性能结论出炉前，核对测量输入是否覆盖真实 shape/分布、度量是否全程无有损转换（int 截断、值域缩水、重复采样）。

## 适用边界

陷阱 1 适用于任何按索引 gather / 稀疏选择类算子的性能对拍；陷阱 2 适用于任何「接受率/命中率带小数」的等效吞吐折算（MTP 及类似投机解码 / 缓存命中场景）。两者源均未披露 before→after 数字，结论是「测量会失真」的定性，不外推具体幅度。

## Evidence

- diff 事实 + 维护者确认（clone `@508929e0b6c3`，`ops/ascendc/examples/test_npu_sparse_flash_attention.py`）：`np.random.uniform(0, 16, (4,1,1,2048))` → `random.sample(range(s2_act - s1 + 1), sparse_block_count)` + 新增 `import random`；维护者确认「sparse_indices 生成逻辑已修复、已添加 PA 场景测试用例」。「重复索引→工作集小→访存不代表真实→性能不准」的因果链是基于 diff 事实的推断，故不写具体性能数字。
  - 溯源下探：[cann-recipes-infer-issue-37-bug-report-sparse-fa](https://gitcode.com/cann/cann-recipes-infer/issues/37)
- diff 事实（clone `@af319f1125bd`，`models/deepseek-v3.2-exp/models/model_infer.py::obtain_mtp_stats`）：`.to(torch.int32)` 由 `torch.mean(...)` 结果处移到日志 f-string 内，`total_tokens` 改用浮点均值。「截断使等效吞吐偏低」为对代码语义的确定性推演（向下取整必不增）。
  - 溯源下探：[cann-recipes-infer-pr-243-fix-perfect-eplb](https://gitcode.com/cann/cann-recipes-infer/merge_requests/243)
