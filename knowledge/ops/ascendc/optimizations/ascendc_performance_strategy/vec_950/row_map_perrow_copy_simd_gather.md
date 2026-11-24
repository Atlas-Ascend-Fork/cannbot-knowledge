---
type: Optimization
title: 非恒等行映射的逐行精确拷贝 + SIMD 向量 Gather（32B padded slot 数据流）
description: 当行映射不可证明恒等但可解析表达时，放弃『单块连续拷贝』契约，改为批内逐行精确拷贝：第 r 行从源张量按行映射起点拷入 32B padded slot，随后既有 SIMD 向量 Gather 按 slot 收集输出；对任意行映射按构造逐位精确，无需恒等证明。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/row-map-perrow-copy-simd-gather.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "slot 32B padding 使行起点恒对齐，尾 padding 不参与收集",
      "拷贝契约改动不得触碰恒等判据与其余路由字段（非目标 case 逐字段一致）"
    ],
    "excluded_conditions": [
      "行映射本身恒等（应走整行缓存恒等路径，更少拷贝描述）",
      "行映射依赖索引数据值（host 不可解析）"
    ],
    "required_conditions": [
      "行映射可由 stride/dim 字段无歧义解析（非数据依赖）",
      "批内行数与 xDim 使 padded slot 集合在 UB 预算内",
      "既有 SIMD 收集路径可按 slot 行号索引"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "case 20（x[4,255,2049] fp32，行映射带 128 行空洞置换，T1 标量回退 353.66us）",
      "note": "与 row-map-identity-analytic 互补：恒等走整行缓存、非恒等可解析走逐行精确拷贝，两者合起来覆盖 T1 行映射判据的两半",
      "operator_class": "index-gather",
      "precision": "20/20 PASS",
      "round": 2,
      "run_id": "<run-id>",
      "speedup": "53.29x（353.63→6.64us/inv；独立 probe 6.48us 交叉验证 Δ2.4%；incremental 1.0516）",
      "status": "accepted"
    },
    {
      "comparison_sha256": "90a298ecd61f326ad0e6a91c64bdf0e4cf904a7e5aaf22931d4619ef36260a1a",
      "decision_sha256": "d7b8dd601ca7bfd533389a659f14a0581d9cbde7fa72e4edeab8d7c4b25305db",
      "operator_class": "index-gather",
      "performance_sha256": "b38bcda0b22c63e88ea7b0b0843bb9c6f793cd39040c31ef089c1c1398e85045",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "37ce91d37d3ee762f6bd0227a7ac619b9e8433e4e5e902d65e7578bacd3242eb",
      "verify_sha256": "f9eb2d41e6c1bdaff33067af61109446204be2110f0ed7e5f42972e313995da3"
    }
  ],
  "feature_signature": {
    "bottleneck": "scalar per-element GM reads due to copy contract",
    "primitives": [
      "per-row single-block DataCopy",
      "32B padded slot",
      "SIMD Reg::Gather"
    ],
    "route": "t1-row-map-nonidentity-scalar-fallback"
  },
  "generality": "op_class",
  "id": "GATHER-row-map-perrow-copy-simd-gather",
  "implementation_steps": [
    "在 host 判据树中于恒等分支后新增逐行拷贝分支（解析行映射 + UB 预算门）",
    "kernel 批循环加逐行单块拷入 padded slot（不新增 buffer，复用 xLocal）",
    "收集端沿用既有 SIMD Gather 路径（slot 号=批内行号）",
    "全 case 精度 + 非目标 case tiling 逐字段一致核验"
  ],
  "intent": "消除『拷贝契约要求恒等映射』造成的 T1 标量回退（向量路由被 host 判据错误排除）。",
  "mechanism": "host 保留既有恒等判据不动，新增逐行拷贝分支：行映射函数由 stride 字段解析表达且每行源范围在结构校验内即可启用；kernel 批循环内第 r 行单块 DataCopy 拷入 32B 对齐 padded slot（行起点恒对齐），复用既有 SIMD Reg::Gather 收集路径；越界由既有结构校验（index.shape<=x.shape）排除。",
  "name": "非恒等行映射的逐行精确拷贝 + SIMD 向量 Gather（32B padded slot 数据流）",
  "operator_class": "index-gather",
  "operator_scope": "索引 gather 类 T1 路由：行映射非恒等（源行置换/空洞）导致整行缓存判据失败而落标量回退，但每批行数小、x 行可逐行精确定位",
  "principle": "标量回退的代价来自逐元素 GM 读；只要每行能被精确定位拷入 UB，收集端即可走已验证的 UB 内向量 Gather 速率，行映射是否恒等只影响拷入方式（整块 vs 逐行），不影响收集端向量化。",
  "related_anti_patterns": [],
  "risks": [
    "逐行描述符成本随批行数线性增长（小批可行，大批应评估整块 vs 逐行）",
    "行映射解析错误会产生系统性错行（精度兜底捕获）"
  ],
  "slug": "row-map-perrow-copy-simd-gather",
  "summary": "当行映射不可证明恒等但可解析表达时，放弃『单块连续拷贝』契约，改为批内逐行精确拷贝：第 r 行从源张量按行映射起点拷入 32B padded slot，随后既有 SIMD 向量 Gather 按 slot 收集输出；对任意行映射按构造逐位精确，无需恒等证明。",
  "verification": {
    "correctness": [
      "全 case accuracy pass；正确性按构造（逐行精确定位）而非判定放宽"
    ],
    "performance": [
      "目标 case 标量回退翻转为 SIMD 路由（vec_time 0→正值、scalar 占比下降）；control 逐字段一致"
    ],
    "rollback_signals": [
      "任一 case MISMATCH；control 回归超门；非目标 case tiling 字段漂移"
    ]
  }
}
-->

# 性能优化策略：非恒等行映射的逐行精确拷贝 + SIMD 向量 Gather（32B padded slot 数据流）

单一优化点：当行映射不可证明恒等但可解析表达时，放弃『单块连续拷贝』契约，改为批内逐行精确拷贝：第 r 行从源张量按行映射起点拷入 32B padded slot，随后既有 SIMD 向量 Gather 按 slot 收集输出；对任意行映射按构造逐位精确，无需恒等证明。

## 1. 原理

标量回退的代价来自逐元素 GM 读；只要每行能被精确定位拷入 UB，收集端即可走已验证的 UB 内向量 Gather 速率，行映射是否恒等只影响拷入方式（整块 vs 逐行），不影响收集端向量化。

实现机制：host 保留既有恒等判据不动，新增逐行拷贝分支：行映射函数由 stride 字段解析表达且每行源范围在结构校验内即可启用；kernel 批循环内第 r 行单块 DataCopy 拷入 32B 对齐 padded slot（行起点恒对齐），复用既有 SIMD Reg::Gather 收集路径；越界由既有结构校验（index.shape<=x.shape）排除。

## 2. 性能问题模式

- 优化目标：消除『拷贝契约要求恒等映射』造成的 T1 标量回退（向量路由被 host 判据错误排除）。
- 适用数据流：索引 gather 类 T1 路由：行映射非恒等（源行置换/空洞）导致整行缓存判据失败而落标量回退，但每批行数小、x 行可逐行精确定位
- Feature signature：`{"bottleneck": "scalar per-element GM reads due to copy contract", "primitives": ["per-row single-block DataCopy", "32B padded slot", "SIMD Reg::Gather"], "route": "t1-row-map-nonidentity-scalar-fallback"}`

## 3. 正确性红线

- 逐行描述符成本随批行数线性增长（小批可行，大批应评估整块 vs 逐行）
- 行映射解析错误会产生系统性错行（精度兜底捕获）

资源与硬件约束：

- slot 32B padding 使行起点恒对齐，尾 padding 不参与收集
- 拷贝契约改动不得触碰恒等判据与其余路由字段（非目标 case 逐字段一致）

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- 行映射可由 stride/dim 字段无歧义解析（非数据依赖）
- 批内行数与 xDim 使 padded slot 集合在 UB 预算内
- 既有 SIMD 收集路径可按 slot 行号索引

不适用：

- 行映射本身恒等（应走整行缓存恒等路径，更少拷贝描述）
- 行映射依赖索引数据值（host 不可解析）

## 5. 实施步骤

1. 在 host 判据树中于恒等分支后新增逐行拷贝分支（解析行映射 + UB 预算门）
2. kernel 批循环加逐行单块拷入 padded slot（不新增 buffer，复用 xLocal）
3. 收集端沿用既有 SIMD Gather 路径（slot 号=批内行号）
4. 全 case 精度 + 非目标 case tiling 逐字段一致核验

## 6. LLM 前置问题

- 目标实现是否满足：行映射可由 stride/dim 字段无歧义解析（非数据依赖）？
- 目标实现是否满足：批内行数与 xDim 使 padded slot 集合在 UB 预算内？
- 目标实现是否满足：既有 SIMD 收集路径可按 slot 行号索引？
- 是否命中排除条件：行映射本身恒等（应走整行缓存恒等路径，更少拷贝描述）？

## 7. 验收标准

正确性：

- 全 case accuracy pass；正确性按构造（逐行精确定位）而非判定放宽

性能：

- 目标 case 标量回退翻转为 SIMD 路由（vec_time 0→正值、scalar 占比下降）；control 逐字段一致

回滚信号：

- 任一 case MISMATCH；control 回归超门；非目标 case tiling 字段漂移

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gather-20260831_113139-a1e0e0（round=2, status=accepted, case=case 20（x[4,255,2049] fp32，行映射带 128 行空洞置换，T1 标量回退 353.66us）, speedup=53.29x（353.63→6.64us/inv；独立 probe 6.48us 交叉验证 Δ2.4%；incremental 1.0516））
- gather-20260831_113139-a1e0e0（round=2, status=accepted）

## 检索卡（短卡）

动作：放弃单块连续拷贝的恒等契约，改为批内逐行精确拷贝：第 r 行按行映射起点单块 DataCopy 拷入 32B padded slot，再由 SIMD Gather 收集。
适用：行映射可由 stride/dim 字段无歧义解析、padded slot 集合在 UB 预算内、收集路径可按 slot 行号索引。
限制：行映射解析错误会产生系统性错行；拷贝契约改动不得触碰恒等判据与其余路由字段。
范围：index-gather 的 T1 路由行映射非恒等导致的标量回退。
检索词：per-row DataCopy、padded slot、Reg::Gather、xLocal、结构校验、T1 路由
机会：拷贝契约要求恒等映射把向量路由错误排除，退化为逐元素 GM 标量读。
代价：逐行描述符成本随批行数线性增长，大批应评估整块 vs 逐行。
