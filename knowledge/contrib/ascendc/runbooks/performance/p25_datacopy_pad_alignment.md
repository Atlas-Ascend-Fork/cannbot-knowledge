---
type: Runbook
title: 'P25 Playbook: DataCopyPad 带 Padding 的搬运'
description: 当源数据列数不对齐 32B 时，使用 DataCopyPad + DataCopyPadExtParams 在搬运过程中自动补零对齐。
tags:
- task.optimization
- topic.compute.composite
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P25_datacopy_pad_alignment.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P25
---

# P25 Playbook: DataCopyPad 带 Padding 的搬运

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P25 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P25 的核心是**当源数据列数不对齐 32B 时，使用 DataCopyPad + DataCopyPadExtParams 在搬运过程中自动补零对齐**。

## Step 1: 定位关键结构

```bash
grep -n "DataCopy|DataCopyPad|CopyIn|CopyOut" \
    {KERNEL_DIR}/*.cpp > /tmp/p25_locations.txt
grep -n "Align|对齐|pad|Pad|padding" \
    {KERNEL_DIR}/*.cpp >> /tmp/p25_locations.txt
grep -n "blockLen|srcStride|dstStride|blockCount" \
    {KERNEL_DIR}/*.cpp >> /tmp/p25_locations.txt
grep -n "DataCopyExtParams|DataCopyPadExtParams" \
    {KERNEL_DIR}/*.cpp >> /tmp/p25_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **当前对齐方式**：文件 + 行号
- **DataCopy 参数**：文件 + 行号
- **是否需要补零**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| 对齐方式 | `?` (手动/无) | DataCopyPad 自动 | `op_kernel/*.cpp:L?` |
| 补零 | `?` (后续处理) | 搬运时完成 | `op_kernel/*.cpp:L?` |
| 参数 | `?` (无) | DataCopyPadExtParams | `op_kernel/*.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — 完整 DataCopyPad（含 DataCopyPadExtParams）**。
- **形态 β — 仅 DataCopyExtParams**：不做 padding，只做 stride。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
uint32_t attenMaskSizeAlign = Align(info.s2dealNum, 32U);
DataCopyExtParams dataCopyParams;
dataCopyParams.blockCount = s1EndIdx - s1StartIdx;
dataCopyParams.blockLen = info.s2dealNum;
dataCopyParams.srcStride = info.attenMaskStride - info.s2dealNum;
dataCopyParams.dstStride = 0;
DataCopyPadExtParams<bool> padParams{true, 0,
    static_cast<uint8_t>(attenMaskSizeAlign - info.s2dealNum), 0};
DataCopyPad(attenMaskUb, srcGmAddr[maskOffset], dataCopyParams, padParams);
```

### 3C. Variant Notes

- padding 参数为 uint8_t，最大补零 255 字节。
- blockLen 单位为字节需注意转换。
- 补零后数据参与后续计算，需确保补零不影响算法正确性（ReduceSum 安全，ReduceMax 可能受影响）。

## Step 4: 约束复核

- padding 上限 255 字节
- blockLen 单位转换
- 算法正确性影响

**在 `{NOTE_FILE}` "Playbook Step 4" 中报告具体数值**（实际数值 + 是否通过）。
## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "DataCopyPad|DataCopyPadExtParams" modified_files/op_kernel/*.cpp  # >=1
grep -cE "padParams|PadExtParams" modified_files/op_kernel/*.cpp  # >=1
grep -cE "Align.*32|attenMaskSizeAlign" modified_files/op_kernel/*.cpp  # >=1
grep -cE "blockLen|srcStride|dstStride" modified_files/op_kernel/*.cpp  # >=1
grep -cE "DataCopy\(.*,.*,.*\).*无.*pad" modified_files/op_kernel/*.cpp  # ==0
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| padding 超 255 | 分块搬运 |
| blockLen 单位错 | 确认字节 vs 元素 |
| ReduceMax 受影响 | 评估算法正确性 |
| 已对齐 | 无需 DataCopyPad |

---

**完成清单**：
```
[P25 Playbook Completion]
Step 1: done (/tmp/p25_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: padding 上限 255 字节; blockLen 单位转换; 算法正确性影响: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
