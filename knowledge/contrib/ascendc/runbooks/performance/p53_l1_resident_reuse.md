---
type: Runbook
title: 'P53 Playbook: L1 Resident Reuse'
description: 在 FlashAttention/IFA 等 Cube 密集型算子中，将 Q 矩阵（左矩阵）在首次 N 方向迭代时加载到 L1 后常驻，后续
  N 迭代直接复用 L1 中已有数据，消除冗余搬运。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.attention
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P53_l1_resident_reuse.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P53
---

# P53 Playbook: L1 Resident Reuse

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> 本 Playbook 为**强制流程**。采纳 P53 策略的子 agent 必须逐步执行，每步填写/验证后才能进入下一步。禁止跳步。
>
> P53 的核心是**在 Cube 密集型算子中，将 Q/左矩阵在首次 N 迭代加载到 L1 后常驻，后续迭代直接复用，消除冗余 GM→L1 搬运**。

## Step 1: 定位关键结构

```bash
grep -n "CopyQ|LoadData|左矩阵|Q.*L1" \
    {KERNEL_DIR}/*.cpp > /tmp/p53_locations.txt
grep -n "L1|l1|CubeInBuffer|AllocTensor|GetBuffer" \
    {KERNEL_DIR}/*.cpp >> /tmp/p53_locations.txt
grep -n "for.*nloops|nloops|callTimes|reuseLeft" \
    {KERNEL_DIR}/*.cpp >> /tmp/p53_locations.txt
grep -n "Matmul|matmul|FlashAttention|IFA" \
    {KERNEL_DIR}/*.cpp >> /tmp/p53_locations.txt
```

**交付物**（必须记录到 `{NOTE_FILE}` 的 "Playbook Step 1" 段落）：
- **Q 搬运位置**：文件 + 行号
- **L1 Buffer 分配**：文件 + 行号
- **N 迭代结构**：文件 + 行号
- **常驻复用标识**：文件 + 行号
## Step 2: 改造计划表

| 元素 | 当前值 | 目标值 | 修改位置 |
|---|---|---|---|
| Q 搬运 | `?` (每轮) | 首轮加载+常驻 | `op_kernel/*.cpp:L?` |
| 复用标识 | `?` (无) | reuseLeft / callTimes | `op_kernel/*.cpp:L?` |
| L1 空间 | `?` | 常驻区 <20% | `op_kernel/*.cpp:L?` |
| 搬运次数 | `?` (O(N)) | O(1) | `op_kernel/*.cpp:L?` |

## Step 3: 代码改造

### 3A. 形态识别

- **形态 α — 大常驻（跨多个 S2 循环复用）**。
- **形态 β — 小常驻（单基本块内部复用）**。

**必须在 {NOTE_FILE} "Playbook Step 3A" 明确声明**：`form: alpha | beta | gamma`
### 3B. Canonical Template

```cpp
__aicore__ inline LocalTensor<TRANS_T> LoadData(int curRow, int curCol,
    int tileHeight, int tileWidth, int batchNum = -1) {
    LocalTensor<TRANS_T> l1;
    UserDefDataType flag = MATMUL_PARAM_VAR.dataPtr_;
    LocalTensor<TRANS_T> dst;
    if (flag.reuseLeft) {
        // 非首轮：复用 L1 已有数据
        l1 = MATMUL_MODULE(CubeInBuffer)->GetBuffer(flag.leftBufIdx);
        dst = l1[static_cast<int64_t>(callTimes_) * baseWidth_ * 64];
        ++callTimes_;
        return dst;
    } else {
        // 首轮：从 GM 加载
        l1 = MATMUL_MODULE(CubeInBuffer)->AllocTensor(flag.leftBufIdx);
        dst = l1[static_cast<int64_t>(callTimes_) * baseWidth_ * 64];
        // DataCopy nd2nz...
    }
    ++callTimes_;
    return dst;
}
```

### 3C. Variant Notes

- 常驻区占 L1 空间需 <20%。
- M 方向 >128 时不支持大常驻（128×576×2 = 144KB）。
- 与 P83（多 buffer 分区）互补，P83 侧重分区管理，P53 侧重复用逻辑。

## Step 4: 约束复核

- 常驻期间 L1 空间被占用，BMM2 阶段无法释放供 P 使用
- M 方向 >128 限制
- C1/C2 首次循环数据量大可能断流

**在 `{NOTE_FILE}` "Playbook Step 4" 中报告具体数值**（实际数值 + 是否通过）。
## Step 5: 编码后自检
**严格度**：任一失败 → 回到 Step 3 重做。禁止在 `{NOTE_FILE}` 中把失败 grep 标记为"不适用"。


```bash
grep -cE "reuseLeft|flag\.reuseLeft" modified_files/op_kernel/*.cpp  # >=1
grep -cE "CubeInBuffer|GetBuffer|AllocTensor" modified_files/op_kernel/*.cpp  # >=1
grep -cE "callTimes|callTimes_" modified_files/op_kernel/*.cpp  # >=1
grep -cE "CopyQ|LoadData.*Q|Q.*L1" modified_files/op_kernel/*.cpp  # >=1
grep -cE "for.*nloops.*CopyQ|每.*轮.*搬运" modified_files/op_kernel/*.cpp  # ==0（消除冗余）
```

## Step 6: Known Pitfalls

| 现象 | 修复 |
|---|---|
| L1 溢出 | 常驻 <20%，或减小 tile |
| M>128 不支持 | 回退小常驻或取消 |
| BMM2 缺空间 | 大常驻期间释放策略 |
| 首次循环断流 | 预加载或容忍 |

---

**完成清单**：
```
[P53 Playbook Completion]
Step 1: done (/tmp/p53_locations.txt written)
Step 2: plan table filled
Step 3: form = alpha/beta/gamma, canonical/variant applied
Step 4: 常驻期间 L1 空间被占用，BMM2 阶段无法释放供 data tile; M 方向 >128 限制; C1/C2 首次循环数据量大可能断流: yes/no
Step 5: all 5 grep checks passed (详见下文)
Step 6: no pitfalls triggered / {列出触发的}
```
