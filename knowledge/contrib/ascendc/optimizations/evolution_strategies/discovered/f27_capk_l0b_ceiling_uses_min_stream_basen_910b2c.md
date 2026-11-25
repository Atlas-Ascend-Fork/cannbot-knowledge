---
type: Optimization
title: "F27: baseK 的 L0B 上界必须用「realize 后的 baseN」校验，不能用常量下界"
description: "host tiling 中 baseK 的 L0B 上界必须用 realize 后的 baseN 计算，不能用常量下界，否则部分 plan 会在设备侧触发 ACL 507015。"
tags:
  - task.debugging
  - topic.programming_model.execution_unit.cube
  - topic.tiling
  - topic.precision
  - topic.compute.elementwise.arithmetic
  - topic.compute.composite
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreMemSize.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f27_capk_l0b_ceiling_uses_min_stream_basen_910b2c.json
    role: evidence
created_at: "2026-10-29T00:00:00Z"
updated_at: "2026-10-29T00:00:00Z"
platforms:
  - a2
---
> 证据：基线/变体与逐 case 数据见 [证据包 cases/f27_capk_l0b_ceiling_uses_min_stream_basen_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f27_capk_l0b_ceiling_uses_min_stream_basen_910b2c.json)。

> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。


> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 capk-l0b-ceiling-uses-min-stream-basen-910b2c）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: 权重流 tiling 里 baseK 的 L0B 上界用常量 MIN_STREAM_BASE_N 校验、而非 plan 实际 realize 的 baseN，导致在 bN=128 的遗留 plan 上把 baseK 64→128 放开（128×128×4 = 64 KB > L0B/2 = 32 KB），host tiling 通过但设备侧 ACL 507015 硬崩
> severity: high
> occurrences: 1
> failed_combination: [X125, P117]
> op_families: [matmul, cv-mix]
> operator_type: [matmul, cv-mix]
> ```

# F: baseK 的 L0B 上界必须用「realize 后的 baseN」校验，不能用常量下界

## 现象

在权重流 GEMM 的 host tiling 重构里，给 `baseK` 设了一个上界 `capK`：

```cpp
capK = min(l0aSize/2/(4*baseM), l0bSize/2/(4*MIN_STREAM_BASE_N), 512);
 // ^^^^^^^^^^^^^^^^^^ 常量（本例 = 32）
```

其中 `MIN_STREAM_BASE_N` 是「至少要有多少列才能流水」的常量下界。于是 `capK` 隐含假设
B 片段只有 `MIN_STREAM_BASE_N` 列宽。但**实际 plan 的 baseN 可能是别的值**：本算子有一个
遗留 plan realize 出 `baseN = 128`，其 B 片段实际占 `128 * baseK * 4` 字节。

后果：该 plan 的 `baseK` 被允许从 64 抬到 128，`128 × 128 × 4 = 65,536 B = 64 KB`，
超过 `L0B/2`（910B2C 上 32 KB，双缓冲预算），**host 侧 tiling 全部通过**，
设备侧以 `ACL 507015` 硬崩（不是性能退化，是跑不起来）。

## 根因

- 预算校验用的是**请求/常量侧的代理量**（`MIN_STREAM_BASE_N`），而不是**实际生效的几何**
 （realize 后的 `baseN`）。
- 这个 bug 只在 `baseN > MIN_STREAM_BASE_N` 的 plan 上发作，而绝大多数 plan 恰好
 `baseN == 32`，所以常规 50 例 sweep 会把它掩盖成「偶发单例崩溃」。
- 与 X125 的「API 钳位即丢弃」同源：两者都是**算过的几何 ≠ 实际跑的几何**这一类错误，
 区别是这里错在**自己写的预算式**，而不是错在没读 API 的返回值。

## Resolution

- 任何形如 `bM·bK` / `bN·bK` / `bM·bN` 的 L0 预算校验，**右端必须代入本 plan realize 后的
 实际块尺寸**；不允许用常量下界代替某个维度的实际值。
- `baseN` 与 `baseK` 的预算校验必须**放在同一处、按先后顺序**执行：先定 baseN，再据它
 重算 capK。两地分写必然漂移（本例 baseN 在别处被抬升，capK 不知道）。
- 复核方式：对每个改变过的 plan，打印 `(baseM, baseN, baseK, baseM*baseK*4, baseN*baseK*4,
 L0A/2, L0B/2)`，断言两个字节量都 ≤ 半区；并在 50 例全量上跑一次（单 case 冒烟会漏）。
- 相关硬约束（同族，见 F22 / X189）：`baseN*baseK*4 ≤ L0B/2`，越过即全例 `ACL 507015`。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f27_capk_l0b_ceiling_uses_min_stream_basen_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

