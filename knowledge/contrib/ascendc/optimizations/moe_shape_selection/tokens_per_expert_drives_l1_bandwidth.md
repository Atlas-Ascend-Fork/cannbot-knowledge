---
type: Optimization
title: "MoE 分组 GEMM：L1 读带宽利用率由【每专家 token 数】驱动，不由填充率驱动"
description: "在 arch22 (A3) 的融合 MoE 算子上实测：aic_l1_read_bw 随 tok/expert 单调上升；恒定填充率下把 tok/expert 提高一档可得 +12.4pp，跨 H=1024/3584 复现到 0.06pp。填充率与 m_tiles 均为该量的代理，非驱动量。"
tags: ["task.optimization", "topic.performance.optimization.optimization_overview", "topic.data_movement.memory_access"]
status: stable
created_at: "2026-09-28T21:10:00Z"
updated_at: "2026-09-28T21:10:00Z"
platforms: ["a3"]
sources:
  - resource: https://gitcode.com/cann/ops-transformer/blob/6f0d3ec620b338cab4f2d00322ff2e0d141419d2/mc2/mega_moe/op_kernel/arch22/mega_moe_a2.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/6f0d3ec620b338cab4f2d00322ff2e0d141419d2/mc2/mega_moe/op_host/op_tiling/arch22/mega_moe_tiling_arch22.cpp
    role: supporting
---

# 结论（Reasoning 类，前提见下表）

**在 arch22 融合 MoE 算子（bf16、厂商出厂件、零源码改动）上**，
`aic_l1_read_bw`（L1 读带宽，占同机稠密 bf16 matmul 饱和参照的百分比）
**单调于【每专家每 rank 的 token 数】`tok/expert`**，
**不单调于填充率 `fill`**，也**不由 `m_tiles` 的整数跳变决定**。

```
tok/expert = BS × topk / (epWorldSize × expertPerRank)
fill       = tok/expert / (ceil(tok/expert / 128) × 128)      # 128 = L1TileShape::M
```

## 实测证据

### ① 判别实验（同窗 ABBA，每臂重复，`aic_mac_ratio` 口径）
三臂**刻意让 fill 与 tok/expert 的排序相反**：

| 臂 | tok/expert | fill | m_tiles | `aic_mac_ratio` |
|---|---|---|---|---|
| A | 96 | 0.750 | 1 | 0.4560 |
| B | 128 | 1.000 | 1 | 0.5290 |
| C | **160** | **0.625（最低）** | 2 | **0.5770（最高）** |

- **C 的 fill 最低却 mac 最高 ⇒ fill 排序被违反**；
- **A 与 B 同为 `m_tiles=1` 却差 0.073 ⇒ 纯 `m_tiles` 读法不成立**；
- **按 `tok/expert` 排（96→128→160）严格单调。**

### ② 跨 `H` 复现（`aic_l1_read_bw` 口径，`local_E` 与 `fill` 均恒定）
| H | tok/expert 提高一档 | 效应 |
|---|---|---|
| 1024 | 128 → 256 | **+12.46pp** |
| 3584 | 128 → 256 | **+12.40pp** |

**两个 `H` 相差 3.5 倍，效应差 0.06pp**（该机同窗交错复现能力 ≈0.31%，跨窗 ≈6.5%）。

## ⚠ 前提表（P6 格式，引用前逐条核对）

| # | 前提 | 状态 |
|---|---|---|
| 1 | 平台 = arch22 / `Ascend910_9382`，bf16 路径 | ✅ 实测 |
| 2 | `L1TileShape::M = 128`（决定 128 这个模数） | ✅ 读装机源码取值 |
| 3 | 效应量级在 `H=8192` 上同样成立 | ⚠ **未完成**（该臂 HCCL 挂起，未取到数） |
| 4 | 带宽提升可转成**时间**提升 | ⛔ **未成立** —— 同项目实测「带宽差距 ≠ 时间差距」 |
| 5 | `tok/expert` 可由 kernel 调整 | ⛔ **不成立** —— 它由 `BS`/`topk`/`E`/`W` 即**部署配置**决定 |

## ⇒ 正确用法与边界

✅ **可用于【选 shape / 评估部署配置】**：
同样的算子，把每专家 token 数从「不足一个 tile」提到「满两个 tile」，
**L1 读带宽利用率可差 12pp 以上**；据此可解释「为何某些并发/专家数组合带宽利用率偏低」。

⛔ **不可用于**：
1. **推断加速比** —— 本卡全部是带宽/MAC 口径，**不是 wall time**；
2. **当作 kernel 优化项** —— `tok/expert` 不是 kernel 可调量；
3. **外推到其它平台或 dtype** —— 仅在 arch22 + bf16 上实测。

## 反例价值（为什么这张卡值得存在）

该算子的 **tile 常量层已被厂商顶格**（`L0C` 钉死 `M×N ≤ 32768`，厂商取 `128×256` 正好顶格；
`L0B` 在 `K0=64` 已 100% 占满）。
⇒ **带宽利用率的差异不来自"厂商没调好"，而来自【部署 shape】。**
⇒ 对后来者的意义：**看到低带宽利用率时，先算 `tok/expert`，不要先去改 tile。**
