---
type: Optimization
title: AscendC 融合算子 Tiling 定块与片上 Buffer 预算：核间 m 轴取舍 + L1/L0 字节账 + UB double-buffer 全计入
description: 给 ascendc 融合算子（sparse-flash-attention / lightning-indexer 等注意力算子、RoPE 类算子）定 Tiling 时。片上 Buffer 有限，任何计算都要切块；基本块大小直接决定右矩阵重复搬运次数、进而影响访存效率与算力利用率。定块的核心是精确核每块占多少片上 buffer（L1 / L0 / UB），预算算大 → 装不下或运行期越界。硬件参考 atlas-a3：L1 512KB、L0A/L0B 各 64KB、L0C 128KB、UB 为 Vector 核 buffer，均开 double buffer（pingpong）。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/5
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/456
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:39:39Z'
platforms:
- a3
---

# AscendC 融合算子 Tiling 定块与片上 Buffer 预算：核间 m 轴取舍 + L1/L0 字节账 + UB double-buffer 全计入

## 适用场景

给 [ascendc](../../concepts/frameworks/ascendc.md) 融合算子（[sparse-flash-attention](../../concepts/kernels/sparse_flash_attention.md) / [lightning-indexer](../../concepts/kernels/lightning_indexer.md) 等注意力算子、RoPE 类算子）定 Tiling 时。片上 Buffer 有限，任何计算都要切块；基本块大小直接决定右矩阵重复搬运次数、进而影响访存效率与算力利用率。定块的核心是**精确核每块占多少片上 buffer**（L1 / L0 / UB），预算算大 → 装不下或运行期越界。硬件参考 [atlas-a3](../../concepts/platforms/atlas_a3.md)：L1 512KB、L0A/L0B 各 64KB、L0C 128KB、UB 为 Vector 核 buffer，均开 double buffer（pingpong）。

## 核间 m 轴取舍（越大越省重复搬运，但被三重约束封顶）

- 基本块 m 轴（行方向）切分越大，右矩阵（KV）的重复访存越少（如 Q_index 基本块 `(128,128)` 时 K_index 需重复搬 `⌈S_q/128⌉` 次，放大到 `(512,128)` 降到 `⌈S_q/512⌉`）；左矩阵一次迭代内常驻 L1 只搬一次，右矩阵分配多块 Buffer（3-Buffer）消除搬运阻塞。
- 但 m 轴**并非越大越好**，被三重约束封顶：① 流水头尾开销；② 合适的粒度使访存不成为瓶颈；③ 片上 Buffer 容量。取值落到「L1 容量与流水开销允许的上限」而非最大（LI 基本块取 `(512,512)`、SFA 取 `(256,512)`，都不是把 m 取满）。

## L1 预算反推 m（不取最大、用容量反算）

`左矩阵常驻 + 右矩阵 3-Buffer ≤ L1 容量`，饱和点即 m 上限：
- 左矩阵（Q/P）小、迭代内常驻 L1 只搬一次 → 占用 ≈ `m × headdim × dtype`。
- 右矩阵（K/V）大、3-Buffer 循环复用 → 占用 ≈ `块行 × headdim × dtype × 3`。
- SFA 落地（L1=512KB、headdim=576 分两个 288 块、bf16）：左 `256×576×2 = 288KB` + 右 `128×288×2×3 = 216KB` = `504KB ≈ 512KB` → m 无法再放大，取 **256**。

## L0 子块字节账（bf16 进 / fp32 出，三块拉通复用）

连续多个矩阵乘（SFA 的 mm_qk、mm_pv）做 L1→L0 子切分时：
- **m/n 按该实现的 128 粒度选块，k 轴按容量与流水分别选择**：mm_qk 取 96、mm_pv 取 128；不能将 128 当作三轴统一约束。
- **按 dtype 核每块字节装进 pingpong 半区**（matmul 数据流 bf16 进 2B、fp32 出 4B）：A/B 块 = `m/k × k/n × 2` 须 ≤ 32KB（L0A/L0B 半区）；C 块 = `m × n × 4` 须 ≤ 64KB（L0C 半区）。
- **相邻矩阵乘拉通复用同三块 L0 Buffer**，而非各占一份。SFA 落地：mm_qk mnk=128/128/96（A/B `128×96×2=24KB`、C `128×128×4=64KB`）、mm_pv mnk=128/128/128（A/B `128×128×2=32KB` 占满、C 64KB），两乘的 L0A/B/C 跨 mm_qk↔mm_pv 复用。

## 失败签名 · UB 预算漏算 double-buffer 多队列 → 运行期 MTE 写越界

计算 per-block UB 预算时，若漏算 double-buffer 的多队列占用（如 no-broadcast RoPE kernel 的 qIn/qOut/cos/sin 共 4 队列、每队列 double buffer），会把 `ubFactorB` 选得过大 → 运行期 MTE 写地址越出 UB 分配范围：
- **失败信号**：返回码 `507035`、日志含 `The write address of the MTE instruction is out of range`、表现为 `vector core exception`。
- **关键**：tiling 阶段**不报错**（RC=0），错误延迟到 kernel 执行期才暴露——不能只靠 tiling 是否成功判断 UB 预算正确。
- **修法**：per-block UB 预算必须**把每个队列的 double buffer 计满**（4 队列 = 8 份缓冲）；混合精度下按**每张量 dtype 分别求和**（如 x=half 2B、cos/sin=fp32 4B，`4*dSizeX + 4*dSizeCosSin`），不能拿单一 dSize × 缓冲数近似。

## 参考实现及其约束

参考 cann-recipes-infer 为 [deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md) 设计的 LI / SFA Ascend C 算子（算子指南 + 维护者在 issue 里补出的 L0 字节账 / L1 反推逻辑，doc 未写全）、以及 `InplacePartialRotaryMul` 的 5 个 tiling 变体（各按自身队列布局定 X/cos-sin 因子）。取向为「有界设计取舍」，非单调律；范围限定本仓这些算子，不升为整栈通用律。字节数为对 doc 块形的直接算术。

## Evidence

- `doc 披露` + `维护者确认`（@2c45117d78）：算子指南 LI/SFA Tiling 设计两节（重复搬运公式、L0 尺寸 2×32/2×32/2×64KB、块形 `(256,512)` / `(128,96)` / `(128,128)`、Q/P 288KB + K/V 216KB）+ 维护者补出 m 轴三重约束、L1 反推「504≈512 故取 256」、L0 字节账「bf16 进 fp32 出、三块拉通复用」。
- `diff 事实` + `维护者确认`（@85729e9c4246）：`ComputeUbFactor` 的 `NO_BROADCAST` 分支修为 `(dSizeX + dSizeCosSin) * UB_FACTOR`（mixed）/ `dSizeX * UB_FACTOR * DOUBLE_BUFFER`（same-dtype），5 个 tiling 变体加 per-dtype 预算；reviewer 反向复现 `507035`（回退 `/2` 复现、修正公式消失）。
- 溯源下探：
  - [cann-recipes-infer-issue-5-requirement-ascend-c-tiling](https://gitcode.com/cann/cann-recipes-infer/issues/5)
  - [cann-recipes-infer-pr-456-950-inplace-partial-rotary-mul](https://gitcode.com/cann/cann-recipes-infer/merge_requests/456)