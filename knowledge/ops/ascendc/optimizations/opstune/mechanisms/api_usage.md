---
type: Optimization
title: "优化机制卡：API 使用与计算量优化（标量削减六法 / Cast 削减 / 融合指令 / 头开销）"
description: 标量削减六法（缩小 TilingData/减少核数/TPipe 外置/循环不变量外提/标量向量化/地址计算优化）对应 L1_SCALAR_BOUND 与 L2_HEAD_OVERHEAD；Vec bound 的 Cast 削减（fp32 ratio 高 → 减 Cast 或批量转换）；mul+add 等融合指令查表合并；深度 VEC bound 的减少计算量策略。
tags: [task.optimization, topic.performance.analysis, topic.implementation.api_layer.basic_api, topic.tiling]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/api-usage.md
    role: primary
created_at: "2026-11-05T03:50:00Z"
updated_at: "2026-11-05T03:50:00Z"
platforms: [a2, a3, "950"]
---

# 优化机制卡：API 使用与计算量优化（标量削减六法 / Cast 削减 / 融合指令 / 头开销）

对应判定规则：L1_SCALAR_BOUND、L1_VEC_BOUND（Cast 重反证）、L0_ICACHE_MISS、L2_HEAD_OVERHEAD。

## 标量削减六法（L1_SCALAR_BOUND）

| # | 方法 | 说明 |
| --- | --- | --- |
| 1 | 缩小 TilingData | 字段越少 host→device 搬运越快 |
| 2 | 减少核数 | 数据量小时少核 = 少头开销（与 A2 满核约 20-21us 头开销权衡） |
| 3 | TPipe 外置 | 避免 TPipe 对象在核内创建初始化 |
| 4 | 循环不变量外提 | 移到 Host 侧或 kernel 顶层 |
| 5 | 标量参数向量化 | 常量标量用 Muls/广播替代逐元素标量路径 |
| 6 | 地址计算优化 | areg 地址生成等 |

scalar >90% 且 vec/mte 低 → 标量访问/地址计算主导：查指针运算与分支，而不是数据量。

## Cast 削减（L1_VEC_BOUND + fp32 ratio 高反证）

- 检查 `aiv_vec_fp32_ratio` vs `aiv_vec_fp16_ratio`：fp32 远高于预期 = 大量 fp16→fp32 转换；
- 精度允许 → 直接 fp16 计算（**语义变更类**：须精度代价标注 + 边界位型验证）；
- 必须转换 → 批量一次转换，禁止循环内逐元素 Cast。

## 融合指令与头开销

- mul+add → Axpy 类、mul+sub 等可融合序列查表合并；Compare+Select 链合并；
- 头开销（L2_HEAD_OVERHEAD）：Task Duration − max(aic,aiv) 占比 >30% 说明数据量太小或核数太多——先减核再谈其它；
- ICache 缺失（L0_ICACHE_MISS）：代码布局/分支整理，减少封装带来的 scalar 开销；循环展开小循环减少分支代价，按 tiling 最简化循环轴。

## 减少计算量（深度 VEC BOUND 核心策略）

VEC bound 接近极限（>80%）时优化空间在数据量与算法侧：算法等价改写减少实际计算次数、提前剪枝、查表替代计算等，与搬运/流水机制正交叠加。

## 验证与回滚

同口径 verdict 复跑（scalar_ratio / vec_fp32_ratio 下降为机制生效证据）；语义变更类（fp16 计算）精度用例必附。噪声带内 → revert。

## 失效边界

- 六法中「减少核数」与 L2_UNDERUTILIZATION 的「增核」方向相反——按判定结果决定，不叠加；
- 融合指令与向量化改写在 RegBase/VF 路径（A5）另有深度机制（RegBase VF 机制卡）；
- 标量族模板资产留工具仓 ops-family（scalar guide、elementwise vector_efficiency_design）。
