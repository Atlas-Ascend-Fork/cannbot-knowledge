---
type: Runbook
title: 'P72 Playbook: Matmul 多核切 K'
description: 当矩阵 M 和 N 较小无法有效切分多核时，可沿 K 轴切分实现多核并行。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.implementation.tiling
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P72_matmul_split_k.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P72
---

# P72 Playbook: Matmul 多核切 K

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P72 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P72 的核心是**当 M/N 较小无法切多核时，沿 K 轴切分实现多核并行，结果通过 AtomicAdd 在 GM 累加**。

## Step 1: 定位关键结构

```bash
grep -n "M|N|K|m|n|k|singleCore|split" \
    {KERNEL_DIR}/*.cpp > /tmp/p72_locations.txt
grep -n "Matmul|matmul|EnableMultiCore|AtomicAdd" \
    {KERNEL_DIR}/*.cpp >> /tmp/p72_locations.txt
grep -n "Fill|清零|zero|SetGlobalBuffer" \
    {KERNEL_DIR}/*.cpp >> /tmp/p72_locations.txt
grep -n "GetBlockNum|coreNum|blockIdx" \
    {KERNEL_DIR}/*.cpp >> /tmp/p72_locations.txt
grep -n "IterateAll|Iterate|enAtomic" \
    {KERNEL_DIR}/*.cpp >> /tmp/p72_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **M/N/K 大小**：文件 + 行号
- **当前分核方式**：文件 + 行号
- **是否支持 AtomicAdd**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| M/N | `?` (小) | 不变 | `?_tiling.cpp:L?` |
| K | `?` (大) | 切分 | `?_tiling.cpp:L?` |
| 分核方式 | `?` (无/M/N) | K 轴 | `?_tiling.cpp:L?` |
| 累加方式 | `?` (无) | AtomicAdd | `?_kernel.cpp:L?` |
| GM 清零 | `?` (无) | 有 | `?_kernel.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — 标准 Split-K（最常见）**：EnableMultiCoreSplitK + AtomicAdd。
- **形态 β — 分块 K + 本地归约**：先本地累加再写 GM。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
// Tiling 侧
cubeTiling.SetOrgShape(M, N, K);
cubeTiling.SetShape(M, N, K);
cubeTiling.EnableMultiCoreSplitK(true);
cubeTiling.GetTiling(tilingData);

// Kernel 侧
cGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ cType*>(c), tiling.M * tiling.N);
Fill(cGlobal, tiling.M * tiling.N, (cType)0);  // GM 清零

uint8_t enAtomic = 1;
matmulObj.IterateAll(cGlobal, enAtomic);  // AtomicAdd 累加
```

### 3C. Variant Notes

- 与 P71 协同：Split-K 后多核共享 B 矩阵，配合 IBShare 减少搬运。
- 不支持 Bias 参与矩阵乘。

## Step 4: 约束复核

- GM 清零开销
- 仅支持输出到 GM
- M/N 必须小到无法切多核

**在 `{NOTE_FILE}` "Playbook Step 4" 中报告具体数值**（实际数值 + 是否通过）。
## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "EnableMultiCoreSplitK|SplitK" modified_files/op_kernel/*.cpp  # >=1
grep -cE "Fill.*zero|Fill.*0" modified_files/op_kernel/*.cpp  # >=1
grep -cE "AtomicAdd|enAtomic" modified_files/op_kernel/*.cpp  # >=1
grep -cE "IterateAll.*enAtomic|IterateAll.*cGlobal" modified_files/op_kernel/*.cpp  # >=1
grep -cE "SetOrgShape|SetShape" modified_files/op_kernel/*.cpp  # >=1
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| GM 未清零 | 添加 Fill |
| 有 Bias | 不支持，分离计算 |
| 输出到 UB | 不支持，改 GM |
| K 太小 | 收益 < 开销，不触发 |

---

**完成清单**：
```
[P72 Playbook Completion]
Step 1: done (/tmp/p72_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: GM 清零开销; 仅支持输出到 GM; M/N 必须小到无法切多核: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
