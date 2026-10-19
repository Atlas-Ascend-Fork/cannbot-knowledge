---
type: Runbook
title: 'P71 Playbook: Matmul IBShare L1 共享'
description: MIX 场景下多个 AIV 核使用相同的 A 或 B 矩阵数据时，默认每个 AIV 都独立从 GM 搬运到 L1。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.memory
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P71_matmul_ibshare_l1.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P71
---

# P71 Playbook: Matmul IBShare L1 共享

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P71 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P71 的核心是**在 MIX 场景下使能 IBShare，让第一个 AIV 搬入的矩阵缓存在 L1 供其他 AIV 复用，避免重复 MTE2 搬运**。

## Step 1: 定位关键结构

```bash
grep -n "MIX|mix|Matmul|matmul|AIV|aiv|IBShare" \
    {KERNEL_DIR}/*.cpp > /tmp/p71_locations.txt
grep -n "weight|bias|共享|same.*matrix|共用" \
    {KERNEL_DIR}/*.cpp >> /tmp/p71_locations.txt
grep -n "MatmulType|LayoutMode|CubeFormat" \
    {KERNEL_DIR}/*.cpp >> /tmp/p71_locations.txt
grep -n "L1|l1|L1Buffer|LoadData" \
    {KERNEL_DIR}/*.cpp >> /tmp/p71_locations.txt
grep -n "GetSubBlockNum|subBlock|aivNum" \
    {KERNEL_DIR}/*.cpp >> /tmp/p71_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **MIX 场景确认**：文件 + 行号
- **共享矩阵类型**：文件 + 行号
- **L1 搬运次数**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| 场景 | `?` (MIX) | MIX | `?_kernel.cpp:L?` |
| 共享矩阵 | `?` (A/B) | 使能 IBShare | `?_kernel.cpp:L?` |
| 当前搬运 | `?` (每 AIV 独立) | 首 AIV 搬入后复用 | `?_kernel.cpp:L?` |
| L1 全载 | `?` (否) | 是 | `?_kernel.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — B 矩阵 IBShare（最常见）**：weight/B 矩阵共享。
- **形态 β — A 矩阵 IBShare**：输入 A 矩阵共享。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
// B 矩阵使能 IBShare（最后一个参数 true）
using B_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND,
    BType, false, LayoutMode::NONE, true>;

AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_IBSHARE_NORM> matmulObj;
```

### 3C. Variant Notes

- A/B 同时使能时只支持 IterateAll 输出到 GM。
- 与 P72 协同：Split-K 后多核共享 B 矩阵，IBShare 收益更大。

## Step 4: 约束复核

- 仅 MIX 场景
- 共享矩阵必须 L1 全载
- A/B 同时使能有限制

**在 `{NOTE_FILE}` "Playbook Step 4" 中报告具体数值**（实际数值 + 是否通过）。
## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "IBSHARE|IBShare|ibshare" modified_files/op_kernel/*.cpp  # >=1
grep -cE "LayoutMode::NONE,\s*true" modified_files/op_kernel/*.cpp  # >=1
grep -cE "MatmulType.*true\s*\)" modified_files/op_kernel/*.cpp  # >=1
grep -cE "MIX|mix" modified_files/op_kernel/*.cpp  # >=1
grep -cE "A_TYPE|B_TYPE|C_TYPE" modified_files/op_kernel/*.cpp  # >=1
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| A/B 同时使能报错 | 改用 IterateAll 输出 GM |
| L1 放不下 | 检查矩阵大小 |
| 非 MIX 场景 | 不适用 |

---

**完成清单**：
```
[P71 Playbook Completion]
Step 1: done (/tmp/p71_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: 仅 MIX 场景; 共享矩阵必须 L1 全载; A/B 同时使能有限制: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
