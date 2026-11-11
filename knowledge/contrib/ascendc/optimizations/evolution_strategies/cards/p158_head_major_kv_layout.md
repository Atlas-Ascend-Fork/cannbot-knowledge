---
type: Optimization
title: "P158: head-major K/V 布局把 strided 小 burst 变成连续 burst"
description: "BSH 布局下 K/V 每行只有 D*sizeof(dtype) 字节，行 stride 为 Hkv*D；当 D 较小（例如 fp16 D=128 时每行 256B）时，AIC MTE2 以小 burst 读取，成为瓶颈。用 npu_confusion_transpose 一次性把 K/V 转成 [B,Hkv,S,D] 连续布局，kernel 用 native stride 寻址后每个 [S_tile,D] 是连续大 burst。收益需扣除转置成本；K/V 小、Sq 小或大 D 时可能不划算。"
tags:
  - task.optimization
  - topic.attention
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x173.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p158_head_major_kv_layout.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P158.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# P158: head-major K/V 布局把 strided 小 burst 变成连续 burst

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 晋升自 X173（discovered，draft）。详细发现记录见 [../discovered/disc_x173.md](../discovered/disc_x173.md)。

## 核心思想
BSH 布局下 K/V 的行主序是 `[B, S, Hkv, D]`：每一行（一个 token 的一个 KV head）只有 `D * sizeof(dtype)` 字节，行间 stride 为 `Hkv * D`。当 D 较小（例如 fp16 D=128 时每行 256B）时，AIC MTE2 以 256B 小 burst 跨行读取，DMA 效率低，`aic_mte2` 可能成为瓶颈。

把 K/V 一次性转成 head-major 连续布局 `[B, Hkv, S, D]` 后，每个 `[S_tile, D]` 在内存中连续，DMA 可以发大 burst；kernel 只需用 native strides 直接寻址，不需要改计算逻辑。

## 适用场景
BSH/BSND 布局的 attention 前向，K/V 每行字节较小、AIC MTE2 以小 burst 读取，且 D 轴连续、转置成本可被 kernel 侧 DMA 节省覆盖时。

## 做法
1. wrapper：`npu_confusion_transpose(k, (0,2,1,3), k.shape, False)` → `[B,Hkv,S,D]` contiguous；再 `transpose(1,2)` 成 BSND view，strides 为 `(Hkv*S*D, D, S*D, 1)` 传给 op（innermost=1）。
2. 门控：仅在目标 dtype（如 fp16）+ BSH/BSND + `Sq` 足够大时启用；其它形状走原 BSH 路径，并保留关闭开关。
3. 变换成本：转置需要读+写 K/V 全量字节；先按目标带宽估算 `transpose_bytes / bandwidth`，再与 kernel 侧节省的 DMA 时间比较。若 K/V 小、Sq 小或 D 很大（行本身已经是较大 burst），转置可能不划算。
4. 不跨调用缓存 head-major 结果：真实 forward 每次输入都可能不同，缓存会引入正确性与内存风险。

## 证据形态（不是固定数值）
- 收益来自 kernel 侧 `aic_mte2` 忙占比下降、MAC 占比上升；端到端收益 = kernel 节省 − 转置成本。
- 转置后的输出应与原路径逐 bit 相同（纯布局变换）。
- 需要同时验证 BSND/BSH 原路径不变，以及 BNSD 等其它布局的回退。

## 常见陷阱
- host 侧可能硬性要求 k/v strides 相同；单边转 K 或 V 会触发检查失败。
- bf16、BNSD 等未覆盖的 dtype/布局不进入该路径。
- 转置成本按 `K+V` 全量字节计算；若 `.transpose` 视图没有被 kernel 正确消费（strides 传错），会静默读错数据。
- 不改变 S/P GM 往返；若 CV 环的 S/P 链是主瓶颈，本卡的收益会被限制。

## 验证方法
- 同 run A/B：原 BSH vs head-major，交替多轮。
- 输出逐 bit 对比；50-case 精度门禁。
- msprof 观察 AIC MTE2 占比与 burst 形状；单独测转置 kernel 的带宽。
- 覆盖 fp16/bf16、BSH/BSND/BNSD、Sq 大/小。

## 关联策略
- 与 [X179](../discovered/disc_x179.md)（转置放 wrapper 还是 kernel）直接配套：本卡是"值得转"的机制，X179 是"在哪转"的成本选择。
- 与 [X160](../discovered/disc_x160.md)（原生 stride 寻址）同属布局优化，但 X160 是零拷贝视图，本卡是显式物化 head-major。
