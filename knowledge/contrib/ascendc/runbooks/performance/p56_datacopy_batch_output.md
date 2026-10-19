---
type: Runbook
title: 'P56 Playbook: DataCopy UB2GM 合并输出'
description: 将多次小批量 DataCopy UB2GM 操作合并为一次大批量写回，减少 MTE3 指令发射次数，提升写回效率。
tags:
- task.optimization
- topic.compute.indexing
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P56_datacopy_batch_output.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P56
---

# P56 Playbook: DataCopy UB2GM 合并输出

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P56 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P56 的核心是**将循环内多次小批量 DataCopy UB2GM 合并为循环外一次性大批量写回，减少 MTE3 指令发射次数**。

## Step 1: 定位关键结构

```bash
grep -n "DataCopy|CopyOut|Fixpipe|UB2GM" \
    {KERNEL_DIR}/*.cpp > /tmp/p56_locations.txt
grep -n "for.*DataCopy|循环.*写回|loop.*output" \
    {KERNEL_DIR}/*.cpp >> /tmp/p56_locations.txt
grep -n "EnQue|DeQue|AllocTensor|FreeTensor" \
    {KERNEL_DIR}/*.cpp >> /tmp/p56_locations.txt
grep -n "loopCount|gSplitSize|tailSplitSize" \
    {KERNEL_DIR}/*.cpp >> /tmp/p56_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **当前输出模式（循环内/外**：文件 + 行号
- **DataCopy 次数**：文件 + 行号
- **UB 队列使用**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| 写回位置 | `?` (循环内) | 循环外统一 | `op_kernel/*.cpp:L?` |
| DataCopy 次数 | `?` (loopCount) | 1次 | `op_kernel/*.cpp:L?` |
| UB 累积 | `?` (无) | 有 | `op_kernel/*.cpp:L?` |
| dealRowCount | `?` (无) | 计算总量 | `op_kernel/*.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — 完整合并（循环内不 DataCopy，循环外统一写回）**。
- **形态 β — 部分合并**：仅合并相邻几次。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
// 原始：循环内每次都 DataCopy
for (uint32_t i = 0; i < loopCount; i++) {
    DealBmm1ResBaseBlock(info, ...);  // 包含 DataCopy
}

// 优化：循环外统一 DataCopy
LocalTensor<int32_t> nInt32Out = outputQue2.template AllocTensor<int32_t>();
for (uint32_t i = 0; i < loopCount; i++) {
    DealBmm1ResBaseBlock(info, nInt32Out, ...);  // 不包含 DataCopy
}
outputQue2.EnQue(nInt32Out);
outputQue2.DeQue<int32_t>();
uint32_t dealRowCount = (loopCount - 1) * gSplitSize + tailSplitSize;
DataCopy(nUpdateGm[...], nInt32Out, dealRowCount);  // 一次性写回
outputQue2.FreeTensor(nInt32Out);
```

### 3C. Variant Notes

- 需要额外 UB 空间累积结果。
- 增加代码复杂度，需管理累积计数。
- 首次迭代可能有额外判断逻辑。

## Step 4: 约束复核

- UB 空间是否足够累积
- 累积计数管理复杂度
- 尾块处理

**在 `{NOTE_FILE}` "Playbook Step 4" 中报告具体数值**（实际数值 + 是否通过）。
## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "dealRowCount|gSplitSize|tailSplitSize" modified_files/op_kernel/*.cpp  # >=1
grep -cE "EnQue|DeQue" modified_files/op_kernel/*.cpp  # >=1
grep -cE "for.*Deal.*DataCopy" modified_files/op_kernel/*.cpp  # ==0
grep -cE "DataCopy.*nUpdateGm|DataCopy.*output" modified_files/op_kernel/*.cpp  # >=1
grep -cE "loopCount.*DataCopy" modified_files/op_kernel/*.cpp  # ==0（循环外）
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| UB 不足 | 减 tile 或部分合并 |
| 计数错误 | 验证 (loopCount-1)*gSplitSize+tail |
| 尾块遗漏 | 单独处理 tailSplitSize |
| 单循环 | 不适用 |

---

**完成清单**：
```
[P56 Playbook Completion]
Step 1: done (/tmp/p56_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: UB 空间是否足够累积; 累积计数管理复杂度; 尾块处理: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
