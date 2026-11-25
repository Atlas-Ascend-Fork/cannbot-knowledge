---
type: Optimization
title: "F17: 想靠「抬 baseM / 预置 NZ / K 轴切块」降低 L1 回填体积——三条路全被 L0C 与 L2 带宽锁死"
description: "int8 grouped GEMM 的 A 面板常驻几何下，靠「抬 baseM / 预置 NZ / K 轴切块」降低 L1 回填体积的三条路全部失败：L0C 只有单个输出 tile 的累加器，跨 K 段持久部分和无处安放；手写 tiling 字段不会恢复框架常驻；ND→NZ 预置只改描述符粒度、不改字节数。"
tags:
  - task.debugging
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreMemSize.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f17_basem_amplification_blocked_by_l0c_single_tile.json
    role: evidence
created_at: "2026-10-26T00:00:00Z"
updated_at: "2026-10-26T00:00:00Z"
platforms:
  - a2
---
> 证据：基线/变体与逐 case 数据见 [证据包 cases/f17_basem_amplification_blocked_by_l0c_single_tile.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f17_basem_amplification_blocked_by_l0c_single_tile.json)。

> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F17: 想靠「抬 baseM / 预置 NZ / K 轴切块」降低 L1 回填体积——三条路全被 L0C 与 L2 带宽锁死

## 现象
int8 grouped GEMM（M=16384, N=8192, K=4096, E=8）在 A 面板 L1 常驻几何（baseM≤96）下，
mm kernel 的回填量已受 L2 带宽约束。直觉上的三条降体积路全部实测失败，且失败机制各不相同：

| 尝试 | 结论 | 失败机制 |
|---|---|---|
| K 轴切块 + 抬 baseM（2 段 / 4 段） | 慢 | 部分和被迫落 GM，fixpipe drain 次数随段数增长，且多为 atomic RMW |
| 手工给 baseM 授予整 K 面板（含手改 baseK） | 慢 | 手写字段不恢复框架常驻循环，A 变成按 base-N tile 重读 |
| baseM=128（framework 静默退回 stepKa=1） | 慢 | 同上：常驻不成立，A 重读体积反而增加 |
| 预置 NZ 权重平面（降低描述符粒度） | 净亏 | 描述符数大降，但搬运字节数不变，转换开销吃掉收益 |
| dbL0C=2（半宽 tile 双缓冲） | 慢 | L0C 容量被切成两份，单 tile 宽度下降且流水仍不满 |

（具体耗时与体积随 shape 与 run 变化，本卡不提供可复核的固定数值；结论方向来自多组变体的同向观测。）

## 根因
1. **L0C 只有一个输出 tile 的累加器**（128KB int32 = 32768 个）。A 面板要在 L1 里跨 K 段复用，
 就必须让它服务窗口内多个 n-base-tile；而每个 n-tile 都需要一个跨 K 段的持久部分和 ⇒
 需要 n_Tiles 份累加器，物理上不存在。于是只能二选一：部分和落 GM（每个 tile 多次 fixpipe
 drain，且多为 atomic RMW），或者 A 按输出 tile 重读（回填体积比原来更大）。
2. **常驻只有 GetTiling 自己给才算数**：手写 tiling 字段（stepKa/depthA1/baseK）不会恢复
 框架的常驻循环，baseM 抬高后一律退回 stepKa=1 → A 变成按 base-N tile 重读。
3. **回填是 L2 带宽 bound，不是描述符粒度 bound**：把 ND→NZ 预置化能大幅减少每 base tile 的
 描述符数，但字节数不变，cube 收益很小。

## Resolution
在 L0C=128KB / L1=512KB 的 910B2C 上，`A 面板常驻（baseM ≤ 96）+ 全 N 单次 IterateAll` 就是
回填体积的框架内下限。要继续提升只能**换维度**：
(a) 把向量后段融进同一个 MIX kernel 藏到搬运阴影（见 X113）；
(b) 接受 mm 与 epilogue 顺序执行的地板。
判据：若某方案声称体积下降却要求跨 tile 持久部分和，先算 L0C 累加器够不够，再上板。

## 证据
与 msprof aic-metrics 观测。定量结果未附公开原始记录，待复核；本卡保留可复用的判据与失败机制。

## 验证状态

本卡为 `status: draft`：结论来自特定运行条件下的失败观测，不应外推为通用结论；定量结果与运行标识见证据包 `cases/f17_basem_amplification_blocked_by_l0c_single_tile.json`。
