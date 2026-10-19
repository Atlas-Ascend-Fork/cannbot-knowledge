---
type: Optimization
title: "X83: chunk-scan 内核的 AIV/AIC 双流解耦软件流水（状态链外提 + 索引偏移重排握手）"
description: "MIX(Cube+Vector) 的 chunk-scan / SSM / 线性递归内核通常写成「每 chunk 内 V、C 交替 rendezvous」的锁步结构（本算子每 chunk 4 次：V0门控 → C0 QKT/KKT → V1 Aqk/求逆 → C1 W/U/WS → V2 v_new…"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X83: chunk-scan 内核的 AIV/AIC 双流解耦软件流水（状态链外提 + 索引偏移重排握手）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> id: X83
> origin: discovered
> discovered_round: 1
> discovered_from: round_1/parallel_2 (node x0, open_exploration)
> base_speedup: "vs PyTorch geomean 128.749x(基线) -> 158.653x；相对基线内核 1.2323x (asc geomean 1132.4us -> 918.9us, 全量 40 case, device 5, batch 口径)"
> ```

## 核心思路

MIX(Cube+Vector) 的 chunk-scan / SSM / 线性递归内核通常写成「每 chunk 内 V、C 交替 rendezvous」的
锁步结构（本算子每 chunk 4 次：`V0门控 → C0 QKT/KKT → V1 Aqk/求逆 → C1 W/U/WS → V2 v_new → C2 OP1/OP3/SD → V3 O/状态更新`）。
锁步下单个 core group 的每 chunk 耗时 = **向量工作 + cube 工作之和**，两个单元交替空转。

把每 chunk 的数据依赖展开后可以看到，真正的**状态递推链只有**：

```
S(i-1) --C1/WU·WS--> v_new(i) --C2/OP3·SD--> S(i)
```

而门控与全部操作数预备（`qg/kgq/kg3/kgl/rhs1/rhs2`）、`QKT/KKT`、`Aqk/Minv`、以及 `W/U` 两个
GEMM **全部只依赖本 chunk 输入**，与状态无关，因此可以任意超前计算。

于是把 AIV 与 AIC 拆成两条在**不同 chunk 下标上独立推进的软件流水**（用跨核 flag 精确握手），
稳态下每 chunk 耗时从 `(T_vector + T_cube)` 变为 `max(T_vector, T_cube)`。

## 适用场景

- MIX_AIC_1_1 实现的 chunk-scan / SSM / 线性注意力 / 门控 delta-rule 内核，per-chunk 结构为
  「向量阶段 ↔ cube 阶段」多次 rendezvous 的锁步；
- 判定信号：`aiv_busy_frac` 与 `aic_busy_frac` 都明显 <1（两单元交替空转）、per-chunk 时间
  近似等于两单元时间之和；展开依赖图后**存在与状态无关的 cube 与向量工作**（这是该法成立的前提）；
- 反向不适用：若所有 cube 工作都在状态链上（纯递推小状态），无可外提的量。

## 实现要点

1. **先画依赖图**，标出状态链上的量（本算子只有 C1 的 `WS` 与 C2 的 `OP3/SD`）与 chunk-local 量；
2. 两条流水各按自己的 index 偏移推进（本实现：AIV 超前 2 chunk 做操作数、超前 1 chunk 做逆；
   AIC 轮末超前 2 chunk 做 `QKT/KKT`）；
3. 把**只依赖 S** 的 GEMM 单独提前（`OP1 = qg@S` 在 S 回写后立即发起），缩短状态链上的 cube 段；
4. **1-deep handshake 纪律**：每个 flag 构造成「至多 1 个 set 未被消费」，需要回执的握手显式加一条
   反向 flag（本实现 `F_AK2`）；
5. **死锁环排查**：超前 chunk 的 cube 工作如果放在轮首，会被「等上一轮 AIV 发布」反向卡住 ——
   必须放在轮末（本实现实测消除了一处真实死锁环）；
6. UB 分区仍可按相位叠加布局（两条流水各自内部相位仍顺序执行），但需注意前导阶段
   （Prep 会先于 Inv 覆写同一缓冲）而额外保留一份 per-chunk 拷贝（本实现新增 `beta` 拷贝）；
7. **不改变任何逐元素算术** → 精度与基线逐位一致（实测 40/40 pass，CPU fp32 抽查 max_abs ≈ 2e-6~4e-6）。

## 常见陷阱

- ❌ 只做「四段 rendezvous 减成三段」这类局部改动：不解除锁步，收益有限；必须整体重排两条流水。
- ❌ flag 不设回执 / 允许多个未消费 set：在超前深度 ≥2 时会出现缓冲被覆写或死锁。
- ❌ 把 chunk-local 工作按「同一下标」外提（如 AIV 与 AIC 都超前 2 chunk 但互相等待）：等于没解耦。
- ❌ 短序列（chunk 数 ≤2）场景收益被 prologue 摊薄，需要保留一条不启用流水的退化路径或接受该损失。

## 来源

自动发现于第 1 轮进化，算子 `13_ChunkKdaWithFusedGateFwd`（910B2C，device 5，进化基线内核模式）：
`round_1/parallel_2`（node `x0`, `open_exploration`），全量 40 case：
asc geomean 1132.4us → 918.9us（**1.2323x**，逐 case 1.138x~1.269x，40/40 case 全部变快、无退化）；
vs PyTorch geomean 128.749x → **158.653x**。
profiling 佐证：`aiv_busy_frac=0.9865`、`aic_busy_frac=0.9822`（基线为交替空转），
剩余最大项转为 `aiv_scalar_ratio=0.43`（块内串行前代求逆）与 `aic_mac_ratio=0.077`（cube 以固定开销为主）。
