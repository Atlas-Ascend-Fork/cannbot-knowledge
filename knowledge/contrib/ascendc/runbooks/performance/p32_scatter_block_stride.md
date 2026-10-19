---
type: Runbook
title: 'P32 Playbook: Scatter Block Update Stride 寻址'
description: 支持输入张量 dim-0 非连续（通过 inputStride0_ 和 inputStride1_），实现 input[indices[k,0],
  indices[k,1], :] = update[k, :] 的散射写入。
tags:
- task.optimization
- topic.compute.indexing
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P32_scatter_block_stride.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P32
---

# P32 Playbook: Scatter Block Update Stride 寻址

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P32 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P32 的核心是**支持输入张量 dim-0 非连续（通过 inputStride0_/inputStride1_），实现散射写入而无需预先 reshape**。

## Step 1: 定位关键结构

```bash
grep -n "Scatter|scatter|Index|index|indices" \
    {KERNEL_DIR}/*.cpp > /tmp/p32_locations.txt
grep -n "DataCopy|DataCopyPad|CopyIn|CopyOut" \
    {KERNEL_DIR}/*.cpp >> /tmp/p32_locations.txt
grep -n "stride|Stride|offset|Offset" \
    {KERNEL_DIR}/*.cpp >> /tmp/p32_locations.txt
grep -n "gmOffset|inputStride|updateDim" \
    {KERNEL_DIR}/*.cpp >> /tmp/p32_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **当前 scatter 实现方式**：文件 + 行号
- **DataCopy 模式**：文件 + 行号
- **是否支持非连续张量**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| 寻址 | `?` (连续) | stride 寻址 | `op_kernel/*.cpp:L?` |
| indices | `?` (无) | UB 解析 | `op_kernel/*.cpp:L?` |
| 写入 | `?` (逐行) | DataCopyPad block | `op_kernel/*.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — 完整 stride 散射（indices UB 解析 + DataCopyPad）**。
- **形态 β — 仅 offset 计算**：不修改写入方式。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
for (int64_t i = 0; i < loadCount; i++) {
    IndexT idx0 = indLocal.GetValue(i * INDICES_LAST_DIM);
    IndexT idx1 = indLocal.GetValue(i * INDICES_LAST_DIM + 1);
    int64_t gmOffset = static_cast<int64_t>(idx0) * inputStride0_
                     + static_cast<int64_t>(idx1) * inputStride1_;
    DataCopyExtParams copyParams;
    copyParams.blockCount = 1;
    copyParams.blockLen = updateDimSize_ * sizeof(T);
    DataCopyPad(inputGm_[gmOffset], updLocal[i * updateRowElements_], copyParams);
}
```

### 3C. Variant Notes

- 逐行写出每次只搬 1 行，MTE3 效率低。
- indices 需先搬入 UB 解析，增加 MTE2 搬运和标量计算。
- 适合非连续张量 scatter 场景。

## Step 4: 约束复核

- MTE3 逐行效率低
- indices UB 占用
- 标量计算开销

## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "inputStride0_|inputStride1_" modified_files/op_kernel/*.cpp  # >=1
grep -cE "DataCopyPad|DataCopyExtParams" modified_files/op_kernel/*.cpp  # >=1
grep -cE "indLocal|indices|INDICES" modified_files/op_kernel/*.cpp  # >=1
grep -cE "gmOffset|offset" modified_files/op_kernel/*.cpp  # >=1
grep -cE "GetValue" modified_files/op_kernel/*.cpp  # >=1
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| MTE3 效率低 | 合并多行写入 |
| indices UB 过大 | 分页加载 |
| 标量计算重 | 预计算 offset 表（见 P33） |
| 连续张量 | 直接 DataCopy，无需 stride |

---

**完成清单**：
```
[P32 Playbook Completion]
Step 1: done (/tmp/p32_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: MTE3 逐行效率低; indices UB 占用; 标量计算开销: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
