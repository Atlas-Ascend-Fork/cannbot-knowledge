---
type: Runbook
title: 'P75 Playbook: Dual AIV M/S1 轴工作量分裂'
description: 利用 Ascend 910B 的 1:2 AIC:AIV 核比例，将 Vector 阶段的 M 轴或 S1 轴工作量在两个 AIV 核之间分裂。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.mixture_of_experts
- topic.implementation.tiling
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P75_dual_aiv_workload_split.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P75
---

# P75 Playbook: Dual AIV M/S1 轴工作量分裂

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P75 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P75 的核心是**利用 1:2 AIC:AIV 核比例，将 Vector 阶段 M/S1 轴工作量在两个 AIV 核间分裂，实现 Cube:Vector = 1:2 匹配**。

## Step 1: 定位关键结构

```bash
grep -n "GetBlockIdx|GetBlockNum|BLOCK_DIM|coreNum" \
    {KERNEL_DIR}/*.cpp > /tmp/p75_locations.txt
grep -n "Cube.*Vector|Vector.*Cube|CV|MIX" \
    {KERNEL_DIR}/*.cpp >> /tmp/p75_locations.txt
grep -n "vecStart|vecDeal|aivIdx|aivNum" \
    {KERNEL_DIR}/*.cpp >> /tmp/p75_locations.txt
grep -n "mSize|s1Size|mBaseSize" \
    {KERNEL_DIR}/*.cpp >> /tmp/p75_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **AIC:AIV 比例确认**：文件 + 行号
- **当前 Vector 工作量分配**：文件 + 行号
- **M/S1 轴大小**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| AIC:AIV | `?` (1:1) | 1:2 匹配 | `op_kernel/*.cpp:L?` |
| Vector 分配 | `?` (单 AIV) | 双 AIV 分裂 | `op_kernel/*.cpp:L?` |
| 分裂粒度 | `?` (无) | M/S1 轴 | `op_kernel/*.cpp:L?` |
| 对齐 | `?` (无) | 16 对齐 | `op_kernel/*.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — M 轴完整分裂（16 对齐 + 双 AIV 独立 workspace）**。
- **形态 β — S1 轴分裂**：当 M 轴过短时备选。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
// M 轴分裂公式
info.mSizeV = (info.mSize <= 16) ? info.mSize :
    (((info.mSize + 15) / 16 + 1) / 2 * 16);

// AIV 核区分
uint32_t aivIdx = GetBlockIdx() % 2;
if (aivIdx == 0) {
    vecStartM = 0;
    vecDealM = mSizeV;
} else {
    vecStartM = mSizeV;
    vecDealM = mSize - mSizeV;
}
```

### 3C. Variant Notes

- M/S1 <= 16 时无法分裂，退化为单 AIV。
- 分裂边界需 16 对齐，可能有少量负载不均。
- 两个 AIV 需独立 workspace 区域。

## Step 4: 约束复核

- M/S1 <= 16 退化
- 分裂边界对齐约束
- 独立 workspace 内存开销

**在 `{NOTE_FILE}` "Playbook Step 4" 中报告具体数值**（实际数值 + 是否通过）。
## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "GetBlockIdx.*%.*2|aivIdx" modified_files/op_kernel/*.cpp  # >=1
grep -cE "mSizeV|vecStartM|vecDealM" modified_files/op_kernel/*.cpp  # >=1
grep -cE "mSize.*<=.*16|<= 16" modified_files/op_kernel/*.cpp  # >=1
grep -cE "Cube.*Vector|ExecuteTask|SyncAll" modified_files/op_kernel/*.cpp  # >=1
grep -cE "vecDealM = mSize" modified_files/op_kernel/*.cpp  # ==0（或退化分支）
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| M<=16 无法分裂 | 退化单 AIV |
| 负载不均 | 检查 16 对齐边界 |
| workspace 不足 | 分配双 AIV 区域 |
| 非 CV 融合 | 不适用 |

---

**完成清单**：
```
[P75 Playbook Completion]
Step 1: done (/tmp/p75_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: M/S1 <= 16 退化; 分裂边界对齐约束; 独立 workspace 内存开销: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
