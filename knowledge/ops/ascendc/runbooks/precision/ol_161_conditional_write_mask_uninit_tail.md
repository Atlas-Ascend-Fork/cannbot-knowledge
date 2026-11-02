---
type: Runbook
title: "条件写入的未初始化尾部：先核验收合同，再决定比较范围"
description: "条件写入可能留下随分配器状态变化的尾部；用同地址预填控制定位未写区，仅在验收合同已排除尾部时才裁切比较，冻结的全输出判据必须保留。"
tags: [task.debugging, topic.implementation.masking, topic.memory, topic.precision]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/field-notes/precision/ol-161-conditional-write-mask-uninit-tail.md
    role: primary
  - resource: https://github.com/pytorch/pytorch/blob/449b1768410104d3ed79d3bcfe4ba1d65c7f22c0/torch/nn/functional.py
    role: primary
  - resource: https://github.com/pytorch/pytorch/blob/449b1768410104d3ed79d3bcfe4ba1d65c7f22c0/torch/_meta_registrations.py
    role: implementation
  - resource: https://gitcode.com/sijiaali/ascendc-kernelgen-data/blob/dcd862931371b02f1ae1f46d99efb3b47fad0842/npu_benchmark/level3/2_GroupedMatmul.py
    role: primary
created_at: "2026-07-12T16:00:00Z"
updated_at: "2026-10-22T08:34:51Z"
platforms: ["950"]
aliases: ["OL-161"]
---

# 条件写入的未初始化尾部：先核验收合同，再决定比较范围

> 原 OKF v1 卡号：**OL-161**。
> 现象分类：precision_issue；观测置信度：single_run（单次观测）。
> 触发信号：
> - capture-replay verify reports large per-element diffs at extreme magnitudes (±1e10, ±1e-30) on a subset of cases, non-deterministic across re-runs, for an op that writes only the first realLen rows

## 现象 / 触发

Applies to `soc=Ascend950PR, cann=9.0.0, op_class=conditional_write, dynamic_length, masked_output`.
Unverified on Ascend910_V220 (A3 captures confirmed to contain garbage tails; the masking rule is
symmetric but only the A5 verification side was exercised).

When an op's contract says "compute only the first `realLen` rows; rows beyond are not part of the
output", the kernel typically **does not write** those tail rows (no `Duplicate(0)`, no
`InitGlobalMemory`). The bytes the verifier sees in the tail are whatever lived in the GM allocation
beforehand — uninitialised memory. Both the A3 capture and the A5 re-run produce DIFFERENT garbage in
the tail (depending on prior buffer state, allocator behavior, parallel kernel residue). Comparing
the full output tensor reports large per-element diffs (e.g. `-1.79e+10`, `-5.98e-34`) that have
NOTHING to do with kernel correctness.

**Detection symptoms**:
- A small subset of cases shows per-element diffs at extreme magnitudes (`±1e10`, `±1e-30`) while the
  rest of the batch is bit-exact.
- The diff is non-deterministic across re-runs of the same case.
- Re-running the SAME case on the SAME hardware twice produces different captured outputs in the
  affected region (smoking gun — kernel output is deterministic, the garbage tail is not).

## 适用场景

- 适用技术与问题域：AscendC 精度问题（现象分类：precision_issue）。
- 适用平台：Ascend 950 系列；本卡为单次观测沉淀（single_run），按卡内声明范围消费。

## 根因 / 教训

In port-mode / capture-replay verification, first confirm that the acceptance contract excludes the ignored tail. Only under that authority should the runner read whatever shape-parameter controls
the live region (`group_index`, `seq_lens`, `valid_mask`, `realBatchSize`, `dynamic_length`, ...),
compute the deterministic prefix, and slice BOTH the captured reference and the re-run output to
`[:real_len]` along the relevant axis before bit-exact comparison. Failing to do so produces false
FAILs that are pure verification noise.

**Concrete anchor** (clipped_swiglu `edge_runner.py`):
```python
# A3 capture: group_index limits how many batch rows the kernel touches.
# Rows beyond group_index[0] in 'out_a3' are uninitialised; do NOT compare them.
real_batch = int(case["scalar_inputs"]["group_index"][0])
ref  = a3_outputs[case_idx][:real_batch]   # slice along batch dim
cand = npu_out.cpu()[:real_batch]
assert torch.equal(ref, cand)              # bit-exact on the real region only
```

**Trigger classifier** — the following are diagnosis triggers. Apply slicing only when the acceptance contract already excludes the tail and one of these triggers is present:
- The op signature includes a length / index / mask scalar that bounds the active work
  (`group_index`, `seq_len`, `valid_count`, `actual_seq_qlen`, `dynamic_len`).
- The source kernel has an early-exit `if (idx >= realLen) return;` shape, OR a
  `for (i = 0; i < realLen; ++i)` loop that never touches `[realLen, full_len)`.
- Capture-replay verification is in use (A3-capture vs A5-run, source-capture, etc.).


## 冻结全输出判据时的边界

尾部未写与“获准改变比较范围”是两件事。如果调用方冻结了完整输出、原始输入、同设备 native reference 和 grader，不能借本卡裁尾、替换 oracle、放宽阈值，或把原有 FAIL 改成 PASS。有效前缀比较只用于定位；candidate 的零尾部不能拟合 native 分配器的任意旧字节。也不能把一次干净分配得到的零尾部当作 native 保证。

## 固定 GroupedMatmul 源码与只有统计时的诊断边界

原任务 `Model` 的 end-offset 说明将 `offsets[-1]` 之后的输入行排除，示意分解拼接各组乘积；它没有为完整返回的尾行定义零值。固定 PyTorch 2.10 源码中，`F.grouped_mm` 转调 `torch._grouped_mm`；`_create_grouped_mm_output_tensor` 的 2D×3D 分支仍分配 `[A.rows, B.cols]`，使用 `empty`/`empty_strided`。因此物理返回形状与数学有效域需要分别记录。这些是固定源码事实，不代替被测 NPU provider 的实测，也不保证其尾部始终未初始化或始终为零。

当归档只保存哈希、几何和比较统计时，不能把这些记录称作原始输出数组，也不能任意换 reference 重计。但存在一个有严格前提的统计诊断：冻结的诊断 gold 将尾部置零，实际返回记录独立确认整个尾部有限且全零，并保存全输出的 matched count `c`、元素数 `n` 和尾元素数 `t`，且 `n > t`，则非空有效域的匹配比例可由 `(c-t)/(n-t)` 精确恢复。还需确认全输出均有限；若已存最大绝对误差大于零，因尾误差为零，其最大点及该点的原 ULP 上限来自有效域，可保留原最大误差判据。缺少这些条件、含非有限值或没有足够的计数时，不作该推导。

已存的一例记录为 `M=376, G=48, N=336, offsets[-1]=336`：`n=126336, t=13440, c=126325`，由此得到有效域 `112885/112896 = 0.999902565...`；原最大绝对误差约 `0.000516877`，原上限 `0.01`。这只是保存统计所蕴含的有效域诊断，既没有重新读取输出张量，也没有新增设备测量。整输出尾值缺少数学定义的原记录仍保留；不能把诊断比例提升为 whole-output PASS，也不能用候选的零尾部填补原 reference。

上述证据文件分别保留比较统计和实际返回的哈希/形状；二者不包含输出张量载荷。原任务源码 SHA256 为 `68085deb6ed0416ccc466702b5c75221267e435d88e35d913a609f76227e2776`；`P_ROWS.jsonl` 为 `e9c9d7dde2b144286ca5b66919c9bf6571b53bc893ac1c4ed80dfbb43be5b5ac`，返回日志为 `d869f28f541cc5827f994cda2ab594c21d13db411ff0da67508a7c1970974e03`。经验由这些已封存材料的复核，经语义去重补入本卡；既有同地址预填实验与本次统计诊断是不同证据，不能互相替代。

## 同地址预填诊断与观测

可以在独立诊断中改变分配器状态，同时保留原 native 调用和输入：

1. 保存基线输出及有效前缀边界。
2. 另行分配一个同形状、同 dtype 的 scratch，填入有限的可区分值，完成同步后释放。
3. 再调用原 native，并记录 scratch 与返回输出的实际地址是否相等；没有地址复用时，阴性结果不能排除未写尾部。
4. 分开核对有效前缀和尾部。如果前缀逐字节不变，而复用地址的整个尾部逐元素等于 scratch 预填值，这支持当前路径未覆盖尾部。预填后的输出始终是诊断数据，不替换正常 native truth 或完整精度账本。

2026-10-09 的单个 GroupedMatmul 控制实验在 Ascend950DT_9582、CANN9.1、Torch2.10.0 / torch_npu2.10.0.post4、原 FP32 输入与 allow_hf32=False 下观测到：输出176x512，最后 end offset144，尾部32x512共16384元素。基线尾部为0；两个 scratch 分别填321和654，随后 native 返回地址都与 scratch 相同。两个尾部全部保留各自预填值，前缀 SHA 完全一致，前缀比较 matched_ratio1.0/max_abs0；全输出比较 matched_ratio0.8181818181818182，max_abs分别321和654。该实验共三次原 native 调用，没有 candidate 调用，也没有改写原模型或精度判据。

这条观测只验证该输入和运行版本的 native 未写尾部。其他形状、allocator 策略、模型版本和字段边界需重新绑定；没有复用地址的实验、偶然零尾部、仅发现随机值都不足以完成同一因果判别。该结论不解释有效前缀的长 K 算术差异，不证明所有 native 路径有相同问题，也不支持全局精度上限或精度合格声明。
