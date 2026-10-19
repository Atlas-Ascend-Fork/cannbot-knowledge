---
type: Runbook
title: 'P24 Playbook: ND↔NZ 格式转换搬运'
description: 在 GM→L1 搬运阶段同时完成 ND→NZ 格式转换，避免额外 TransData 指令。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P24_nd2nz_format_copy.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P24
---

# P24 Playbook: ND↔NZ 格式转换搬运

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P24 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P24 的核心是**在 GM→L1 搬运阶段同时完成 ND→NZ 格式转换，避免额外 TransData 指令**。

## Step 1: 定位关键结构

```bash
grep -n "DataCopy|CopyIn|CopyOut|TransData|transpose" \
    {KERNEL_DIR}/*.cpp > /tmp/p24_locations.txt
grep -n "ND|NZ|nd2nz|Nz2Nd|format|Format" \
    {KERNEL_DIR}/*.cpp >> /tmp/p24_locations.txt
grep -n "Nd2NzParams|TransData|ScatterUpdateNZ" \
    {KERNEL_DIR}/*.cpp >> /tmp/p24_locations.txt
grep -n "nValue|dValue|srcDValue|dstNzC0Stride" \
    {KERNEL_DIR}/*.cpp >> /tmp/p24_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **当前格式转换方式（TransData/DataCopy**：文件 + 行号
- **ND/NZ 使用场景**：文件 + 行号
- **对齐参数**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| 转换方式 | `?` (TransData) | DataCopy Nd2Nz | `op_kernel/*.cpp:L?` |
| 方向 | `?` (分离) | 搬运+转换融合 | `op_kernel/*.cpp:L?` |
| 对齐 | `?` (手动) | 自动对齐到 16/32 | `op_kernel/*.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — GM→L1 Nd2Nz（搬运时转换）**。
- **形态 β — 写出方向 ScatterUpdateNZ（逐 token ND→NZ）**。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
template<typename INPUT_T>
__aicore__ inline void CopyToL1Nd2Nz(const LocalTensor<INPUT_T> &l1Tensor,
    const GlobalTensor<INPUT_T> &gmTensor,
    uint32_t nValue, uint32_t dValue, uint32_t srcDValue) {
    Nd2NzParams gm2L1Nd2NzParams;
    gm2L1Nd2NzParams.nValue = nValue;
    gm2L1Nd2NzParams.dValue = dValue;
    gm2L1Nd2NzParams.srcDValue = srcDValue;
    gm2L1Nd2NzParams.dstNzC0Stride = (nValue + 15) >> 4 << 4;
    gm2L1Nd2NzParams.dstNzNStride = 1;
    DataCopy(l1Tensor, gmTensor, gm2L1Nd2NzParams);
}
```

### 3C. Variant Notes

- 对齐 padding 浪费部分 L1 空间。
- 不同数据类型对齐基数不同（fp16=16, fp8=32）。
- L1→L0 仍需标准 LoadData 路径。

## Step 4: 约束复核

- 对齐 padding 空间浪费
- 数据类型对齐基数差异
- 写出方向 MTE3 利用率低

**在 `{NOTE_FILE}` "Playbook Step 4" 中报告具体数值**（实际数值 + 是否通过）。
## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "Nd2NzParams|Nz2NdParams" modified_files/op_kernel/*.cpp  # >=1
grep -cE "dstNzC0Stride|dstNzNStride" modified_files/op_kernel/*.cpp  # >=1
grep -cE "DataCopy.*Nd2Nz|CopyToL1Nd2Nz" modified_files/op_kernel/*.cpp  # >=1
grep -cE "TransData" modified_files/op_kernel/*.cpp  # ==0（或注释说明保留场景）
grep -cE "nValue|dValue|srcDValue" modified_files/op_kernel/*.cpp  # >=1
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| padding 浪费 | 评估总空间 |
| dtype 对齐错 | 条件编译区分 fp16/fp8 |
| L1→L0 仍要 LoadData | 不混淆两段路径 |
| 写出方向低效 | 评估 ScatterUpdateNZ |

---

**完成清单**：
```
[P24 Playbook Completion]
Step 1: done (/tmp/p24_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: 对齐 padding 空间浪费; 数据类型对齐基数差异; 写出方向 MTE3 利用率低: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
