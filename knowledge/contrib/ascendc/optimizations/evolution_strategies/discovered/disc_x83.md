---
type: Optimization
title: "X83: chunk-scan 内核的 AIV/AIC 双流解耦软件流水（状态链外提 + 索引偏移重排握手）"
description: "MIX(Cube+Vector) 的 chunk-scan / SSM / 线性递归内核常写成每 chunk 内 V、C 交替 rendezvous 的锁步结构，两个单元交替空转。把只依赖本 chunk 输入的工作从状态递推链上外提后，AIV 与 AIC 可按不同 chunk 下标独立推进，稳态每 chunk 耗时由两者之和变为最大值。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X83: chunk-scan 内核的 AIV/AIC 双流解耦软件流水（状态链外提 + 索引偏移重排握手）

## 核心思路

MIX(Cube+Vector) 的 chunk-scan / SSM / 线性递归内核通常写成「每 chunk 内 V、C 交替 rendezvous」的
锁步结构。锁步下单个 core group 的每 chunk 耗时 = **向量工作 + cube 工作之和**，两个单元交替空转。

把每 chunk 的数据依赖展开后可以看到，真正的**状态递推链只有**：

```
S(i-1) --状态更新相关 GEMM--> v_new(i) --输出/状态更新--> S(i)
```

而门控与全部操作数预备、`QKT/KKT`、`Aqk/Minv`、以及 `W/U` 两个 GEMM **全部只依赖本 chunk 输入**，
与状态无关，因此可以任意超前计算。

于是把 AIV 与 AIC 拆成两条在**不同 chunk 下标上独立推进的软件流水**（用跨核 flag 精确握手），
稳态下每 chunk 耗时从 `(T_vector + T_cube)` 变为 `max(T_vector, T_cube)`。

## 适用场景

- MIX_AIC_1_1 实现的 chunk-scan / SSM / 线性注意力 / 门控 delta-rule 内核，per-chunk 结构为
  「向量阶段 ↔ cube 阶段」多次 rendezvous 的锁步；
- 判定信号：`aiv_busy_frac` 与 `aic_busy_frac` 都明显小于 1（两单元交替空转）、per-chunk 时间
  近似等于两单元时间之和；展开依赖图后**存在与状态无关的 cube 与向量工作**（这是该法成立的前提）；
- 反向不适用：若所有 cube 工作都在状态链上（纯递推小状态），无可外提的量。

## 实现要点

1. **先画依赖图**，标出状态链上的量与 chunk-local 量；
2. 两条流水各按自己的 index 偏移推进（例如 AIV 超前若干 chunk 做操作数、再提前做逆；
   AIC 在轮末超前做 `QKT/KKT`）；
3. 把**只依赖 S** 的 GEMM 单独提前（例如 `OP1 = qg@S` 在 S 回写后立即发起），缩短状态链上的 cube 段；
4. **1-deep handshake 纪律**：每个 flag 构造成「至多 1 个 set 未被消费」，需要回执的握手显式加一条
   反向 flag；
5. **死锁环排查**：超前 chunk 的 cube 工作如果放在轮首，会被「等上一轮 AIV 发布」反向卡住 ——
   必须放在轮末；
6. UB 分区仍可按相位叠加布局（两条流水各自内部相位仍顺序执行），但需注意前导阶段会先于后续阶段
   覆写同一缓冲，为此需额外保留一份 per-chunk 拷贝（如 `beta` 拷贝）；
7. **不改变任何逐元素算术** → 精度与基线逐位一致；但握手与缓冲生命周期重排后仍需全量精度门禁
   确认缓冲未被覆写。

## 常见陷阱

- ❌ 只做局部 rendezvous 次数削减：不解除锁步，收益有限；必须整体重排两条流水。
- ❌ flag 不设回执 / 允许多个未消费 set：在超前深度 ≥2 时会出现缓冲被覆写或死锁。
- ❌ 把 chunk-local 工作按「同一下标」外提（如 AIV 与 AIC 都超前相同 chunk 但互相等待）：等于没解耦。
- ❌ 短序列（chunk 数 ≤2）场景收益被 prologue 摊薄，需要保留一条不启用流水的退化路径或接受该损失。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 流水/握手类改动额外做长序列与短序列两组形状，确认无死锁且退化路径正确。
