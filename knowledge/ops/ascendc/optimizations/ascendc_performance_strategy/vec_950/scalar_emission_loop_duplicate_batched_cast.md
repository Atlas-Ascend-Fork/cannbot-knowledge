---
type: Optimization
title: T2 scalar 管发射循环消除：SetValue 复位循环 -> 向量 Duplicate 广播；逐行 Cast 加宽循环 -> 守卫式整 tile 单次批量 Cast
description: 把 VF 外围的标量发射循环换成整寄存器向量操作：SetValue 复位改两条 Duplicate，逐行 Cast 改守卫式整 tile 批量 Cast。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/scalar-emission-loop-duplicate-batched-cast.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "Duplicate 与后续 VF LoadAlign 的 V->V 次序仍需原 PipeBarrier 保护（注释同步更新而非删除）",
      "批量 Cast 元素计数按 tile 参数 rows×laneChunk 精确计算，防御性跳过空 tile",
      "dtype 视图（int32/int64）分支须各自替换，不允许跨视图共享广播值"
    ],
    "excluded_conditions": [
      "循环体内含逐元素条件语义、地址去重或跨行依赖",
      "单次批量 Cast 的元素计数无法由 tile 参数精确表达（非 2 幂/尾块须显式计数）",
      "试图借机删除或移动屏障（可见性契约不属于本机制）",
      "非 reduction 的 VF 扫描核心（elementwise 等）：kernel 中不存在 SetValue 哨兵复位循环与 int32->int64 逐行 Cast 循环时，两个替换机制均无的放矢，直接判 no_applicable（选路阶段先全文检索这两类循环）"
    ],
    "required_conditions": [
      "标量发射循环体是常量广播（哨兵/零值初始化）或纯 dtype 加宽（无逐元素条件逻辑、无跨行依赖）",
      "批量 Cast 要求源/目的工作 tile 行距相等（stride 等式守卫），不满足时必须回退逐行循环",
      "涉及的屏障位置全部原位保留（只删标量发射，不动同步语义）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "T2 目标子集（level2/cummin_5/17/10/14）",
      "note": "correctness 20/20；control band 0.9905-1.0028（14 个 T1 control 字节级不动，聚合 1.0000x）。放大效应记录：case5 实测省 10461.8us，远超策略模型仅消除 Cast 发射循环的 ~697us 预测——scalar 循环消除同时解除串行相位发射阻塞，使向量相位与 MTE 相位重叠改善（同一机制、同一表示内的放大，implementation.md 已记录）。增量超 1.2 触发强制抽查：spot_check case5 官方路径 reproducible=true（ratio 1.027，实测快于申报），单 case 官方综合得分 87.06。",
      "operator_class": "reduction",
      "round": 4,
      "run_id": "<run-id>",
      "speedup": "case5 2.4654x、case17 2.1539x、case10 1.6994x、case14 1.2768x；T2 子集聚合 2.0429x；incremental 1.2528x、cumulative 1.5638x、0 回归 15 case improved",
      "status": "accepted"
    },
    {
      "comparison_sha256": "8878396859e1fc02857479ad662a512517df2131626022e9179c97938d3eff4a",
      "decision_sha256": "4682b5a7dbe2d90a211422a0f311798941fb6fc120c02200afdda36f08c2c786",
      "operator_class": "reduction",
      "performance_sha256": "36bf85fafafe769f14b774f35f81f58e5b40557580c23d1f2d8bc7f736980dd5",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "343e1983f13fa91a0c31d630784a6699b30c8c38bc709084669fd6ada765f473",
      "verify_sha256": "437a30b912ed3989891c0fce88c0c3aaf2ecc82611235efe8edc38cf389612c5"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-pipe-issue-loop",
      "serial-phase-blocked-overlap",
      "per-row-cast-emission"
    ],
    "pattern": "scalar-emission-loop-elimination",
    "structure": [
      "duplicate-vector-broadcast",
      "guarded-batched-cast",
      "barriers-preserved",
      "phase-overlap-recovery"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-SCALAR-EMISSION-LOOP-ELIM",
  "implementation_steps": [
    "识别 VF 核心外围的标量发射循环：任务/chunk 级哨兵复位（SetValue 循环）与 tile 级逐行 dtype 加宽（Cast 循环），确认循环体为常量广播或纯加宽",
    "复位循环替换为两条向量 Duplicate（值哨兵 + 索引零值），屏障原位保留并更新其保护语义注释",
    "逐行 Cast 循环替换为行距等式守卫的单次整 tile 批量 Cast，守卫不满足时逐字回退逐行循环",
    "probe/首测对比 scalar 管绝对时长与向量相位重叠（aiv_vec 绝对时长下降幅度可大于发射槽节省模型）",
    "全量 all_cases verify；其他 route control case 字节级不动确认"
  ],
  "intent": "消除 VF 核心外的第二串行相位：每 chunk 的哨兵 SetValue 复位与每 tile 的逐行 Cast 在 scalar 管按元素串行发射，既消耗发射槽又阻塞向量相位与 MTE 相位的重叠。",
  "mechanism": "Process 内两个分支的 2×wc SetValue 哨兵复位循环各替换为 Duplicate<DX>(carryValLocal, carrySentinel, wc) + Duplicate<int32_t|int64_t>(carryIdxLocal, 0, wc)（后续 Duplicate->VF LoadAlign 的 V->V 次序仍由原 PipeBarrier 保护）；int32-carry 核心的逐行 Cast 加宽循环替换为守卫式单次 Cast——当 idxRowStride32 == idxRowStride64（int32/int64 工作 tile 行距相等）时按 tile 参数 rows×laneChunk 元素数整 tile 一次 Cast，否则回退原逐行循环；尾部屏障原位保留；int64 旧核心 wrapper 不动。",
  "name": "T2 scalar 管发射循环消除：SetValue 复位循环 -> 向量 Duplicate 广播；逐行 Cast 加宽循环 -> 守卫式整 tile 单次批量 Cast",
  "operator_class": "reduction",
  "operator_scope": "VF 扫描核心外围的 scalar 管固定发射段：chunk/任务级哨兵复位循环（per-chunk 常量 SetValue）与 tile 级逐行 dtype 加宽循环（int32 工作 tile -> int64 出口），屏障与数据流契约不变",
  "principle": "标量管按元素发射的常量初始化与纯 dtype 加宽循环，可用整寄存器向量指令等价替代：Duplicate<T> 一次广播整段的哨兵/零值；单次批量 Cast 一次完成整 tile 的 int32->int64 加宽（符号扩展位等价）。收益来自两层：(1) 发射槽按元素数线性减少；(2) 更关键的是串行标量相位被删除后，向量相位与 MTE 相位不再被其发射阻塞而重新重叠——第二层通常远大于第一层，验收模型不应只按发射槽节省估算。屏障（PipeBarrier<PIPE_ALL>）原位保留，不改变任何可见性契约。",
  "related_anti_patterns": [],
  "risks": [
    "行距等式守卫写错（按字节 vs 按元素混用）导致批量 Cast 跨行错位——精度 gate 可捕获",
    "误删/移动屏障引入可见性竞态（本机制不动同步，任何屏障变化都属范围外）",
    "仅按发射槽节省建模会低估收益（相位重叠解除是主要收益源），也可能在短 tile 上高估（批量 Cast + 屏障固定开销在 tile 很小时反噬）"
  ],
  "slug": "scalar-emission-loop-duplicate-batched-cast",
  "summary": "把 VF 核心外围的两类标量发射循环替换为整寄存器向量操作：chunk 哨兵复位的 2×wc SetValue 循环 -> Duplicate<DX>(carryValLocal, carrySentinel, wc) + Duplicate<int>(carryIdxLocal, 0, wc) 两条广播；int32 路径的逐行 Cast 加宽循环 -> 行距相等（idxRowStride32 == idxRowStride64）守卫下的整 tile 单次批量 Cast，不等则回退逐行循环；全部 PipeBarrier 原位保留，同步语义零改动。除发射槽本身外，更重要的收益是解除串行标量相位的发射阻塞，使向量/MTE 相位重新重叠——实测收益可远超发射槽节省模型。",
  "verification": {
    "correctness": [
      "全量 all_cases verify 通过（含全 NaN 值域下 +Inf 哨兵 Duplicate 与 NaN 粘性）",
      "行距守卫两个分支（相等/不等）都须被执行验证，不以 case 集通过替代守卫失败臂",
      "其他 route control case 字节级不动"
    ],
    "performance": [
      "incremental total_speedup 达任务阈值且无 case 低于 max_case_regression；目标 route 子集聚合提升",
      "kernel_details 级归因：scalar 管绝对时长下降 + 向量相位重叠改善（收益可大于发射槽节省模型，属同机制放大效应）",
      "超阈值增量触发官方路径 spot_check 复现"
    ],
    "rollback_signals": [
      "任一精度失败（批量 Cast 错位/哨兵值错误）",
      "短 tile 任务回归（批量 Cast + 屏障固定开销未摊销）",
      "control case 字节变动（作用域泄漏）"
    ]
  }
}
-->

# 性能优化策略：T2 scalar 管发射循环消除：SetValue 复位循环 -> 向量 Duplicate 广播；逐行 Cast 加宽循环 -> 守卫式整 tile 单次批量 Cast

> 📌 **适用域收紧（2026-09-22）**：本卡 `op_class=reduction`，机制强依赖 **VF 扫描核心外围**的「SetValue 哨兵复位循环」与「int32→int64 逐行 Cast 加宽循环」（源自 cummin）。**选路阶段必须先全文检索目标 kernel 是否含这两类循环**：均不存在时直接判 `no_applicable_strategy`，不得投到 elementwise/softmax 等无此结构的算子上（实测投到 softplus_backward 时两类模式 0 处、两机制均无的放矢；投到 cat_softmax 仅 1.033× 不达标）。

单一优化点：把 VF 核心外围的两类标量发射循环替换为整寄存器向量操作：chunk 哨兵复位的 2×wc SetValue 循环 -> Duplicate<DX>(carryValLocal, carrySentinel, wc) + Duplicate<int>(carryIdxLocal, 0, wc) 两条广播；int32 路径的逐行 Cast 加宽循环 -> 行距相等（idxRowStride32 == idxRowStride64）守卫下的整 tile 单次批量 Cast，不等则回退逐行循环；全部 PipeBarrier 原位保留，同步语义零改动。除发射槽本身外，更重要的收益是解除串行标量相位的发射阻塞，使向量/MTE 相位重新重叠——实测收益可远超发射槽节省模型。

## 1. 原理

标量管按元素发射的常量初始化与纯 dtype 加宽循环，可用整寄存器向量指令等价替代：Duplicate<T> 一次广播整段的哨兵/零值；单次批量 Cast 一次完成整 tile 的 int32->int64 加宽（符号扩展位等价）。收益来自两层：(1) 发射槽按元素数线性减少；(2) 更关键的是串行标量相位被删除后，向量相位与 MTE 相位不再被其发射阻塞而重新重叠——第二层通常远大于第一层，验收模型不应只按发射槽节省估算。屏障（PipeBarrier<PIPE_ALL>）原位保留，不改变任何可见性契约。

实现机制：Process 内两个分支的 2×wc SetValue 哨兵复位循环各替换为 Duplicate<DX>(carryValLocal, carrySentinel, wc) + Duplicate<int32_t|int64_t>(carryIdxLocal, 0, wc)（后续 Duplicate->VF LoadAlign 的 V->V 次序仍由原 PipeBarrier 保护）；int32-carry 核心的逐行 Cast 加宽循环替换为守卫式单次 Cast——当 idxRowStride32 == idxRowStride64（int32/int64 工作 tile 行距相等）时按 tile 参数 rows×laneChunk 元素数整 tile 一次 Cast，否则回退原逐行循环；尾部屏障原位保留；int64 旧核心 wrapper 不动。

## 2. 性能问题模式

- 优化目标：消除 VF 核心外的第二串行相位：每 chunk 的哨兵 SetValue 复位与每 tile 的逐行 Cast 在 scalar 管按元素串行发射，既消耗发射槽又阻塞向量相位与 MTE 相位的重叠。
- 适用数据流：VF 扫描核心外围的 scalar 管固定发射段：chunk/任务级哨兵复位循环（per-chunk 常量 SetValue）与 tile 级逐行 dtype 加宽循环（int32 工作 tile -> int64 出口），屏障与数据流契约不变
- Feature signature：`{"bottleneck": ["scalar-pipe-issue-loop", "serial-phase-blocked-overlap", "per-row-cast-emission"], "pattern": "scalar-emission-loop-elimination", "structure": ["duplicate-vector-broadcast", "guarded-batched-cast", "barriers-preserved", "phase-overlap-recovery"]}`

## 3. 正确性红线

- 行距等式守卫写错（按字节 vs 按元素混用）导致批量 Cast 跨行错位——精度 gate 可捕获
- 误删/移动屏障引入可见性竞态（本机制不动同步，任何屏障变化都属范围外）
- 仅按发射槽节省建模会低估收益（相位重叠解除是主要收益源），也可能在短 tile 上高估（批量 Cast + 屏障固定开销在 tile 很小时反噬）

资源与硬件约束：

- Duplicate 与后续 VF LoadAlign 的 V->V 次序仍需原 PipeBarrier 保护（注释同步更新而非删除）
- 批量 Cast 元素计数按 tile 参数 rows×laneChunk 精确计算，防御性跳过空 tile
- dtype 视图（int32/int64）分支须各自替换，不允许跨视图共享广播值

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- 标量发射循环体是常量广播（哨兵/零值初始化）或纯 dtype 加宽（无逐元素条件逻辑、无跨行依赖）
- 批量 Cast 要求源/目的工作 tile 行距相等（stride 等式守卫），不满足时必须回退逐行循环
- 涉及的屏障位置全部原位保留（只删标量发射，不动同步语义）

不适用：

- **非 reduction 的 VF 扫描核心（elementwise/softmax 等）**：kernel 中不存在 SetValue 哨兵复位循环与 int32→int64 逐行 Cast 循环时，两个替换机制均无的放矢（选路先检索，命中即 no_applicable）
- 循环体内含逐元素条件语义、地址去重或跨行依赖
- 单次批量 Cast 的元素计数无法由 tile 参数精确表达（非 2 幂/尾块须显式计数）
- 试图借机删除或移动屏障（可见性契约不属于本机制）

## 5. 实施步骤

1. 识别 VF 核心外围的标量发射循环：任务/chunk 级哨兵复位（SetValue 循环）与 tile 级逐行 dtype 加宽（Cast 循环），确认循环体为常量广播或纯加宽
2. 复位循环替换为两条向量 Duplicate（值哨兵 + 索引零值），屏障原位保留并更新其保护语义注释
3. 逐行 Cast 循环替换为行距等式守卫的单次整 tile 批量 Cast，守卫不满足时逐字回退逐行循环
4. probe/首测对比 scalar 管绝对时长与向量相位重叠（aiv_vec 绝对时长下降幅度可大于发射槽节省模型）
5. 全量 all_cases verify；其他 route control case 字节级不动确认

## 6. LLM 前置问题

- 目标实现是否满足：标量发射循环体是常量广播（哨兵/零值初始化）或纯 dtype 加宽（无逐元素条件逻辑、无跨行依赖）？
- 目标实现是否满足：批量 Cast 要求源/目的工作 tile 行距相等（stride 等式守卫），不满足时必须回退逐行循环？
- 目标实现是否满足：涉及的屏障位置全部原位保留（只删标量发射，不动同步语义）？
- 是否命中排除条件：循环体内含逐元素条件语义、地址去重或跨行依赖？

## 7. 验收标准

正确性：

- 全量 all_cases verify 通过（含全 NaN 值域下 +Inf 哨兵 Duplicate 与 NaN 粘性）
- 行距守卫两个分支（相等/不等）都须被执行验证，不以 case 集通过替代守卫失败臂
- 其他 route control case 字节级不动

性能：

- incremental total_speedup 达任务阈值且无 case 低于 max_case_regression；目标 route 子集聚合提升
- kernel_details 级归因：scalar 管绝对时长下降 + 向量相位重叠改善（收益可大于发射槽节省模型，属同机制放大效应）
- 超阈值增量触发官方路径 spot_check 复现

回滚信号：

- 任一精度失败（批量 Cast 错位/哨兵值错误）
- 短 tile 任务回归（批量 Cast + 屏障固定开销未摊销）
- control case 字节变动（作用域泄漏）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260831_113913-196633（round=4, status=accepted, case=T2 目标子集（level2/cummin_5/17/10/14）, speedup=case5 2.4654x、case17 2.1539x、case10 1.6994x、case14 1.2768x；T2 子集聚合 2.0429x；incremental 1.2528x、cumulative 1.5638x、0 回归 15 case improved）
- cummin-20260831_113913-196633（round=4, status=accepted）

## 检索卡（短卡）

动作：把 VF 外围的标量发射循环换成整寄存器向量操作：SetValue 复位改两条 Duplicate，逐行 Cast 改守卫式整 tile 批量 Cast。
适用：标量发射循环体是常量广播或纯 dtype 加宽、批量 Cast 源/目的 tile 行距相等、屏障原位保留。
限制：行距等式守卫不满足须回退逐行循环；不得删除/移动屏障；元素计数按 tile 算；非 reduction VF 核心无此循环→不选
范围：reduction 扫描类算子 VF 核心外围的 scalar 管固定发射段。
检索词：Duplicate、SetValue、批量 Cast、PipeBarrier<PIPE_ALL>、idxRowStride32
机会：每 chunk 复位与每 tile 逐行 Cast 在 scalar 管串行发射，阻塞向量/MTE 重叠。
代价：短 tile 上批量 Cast+屏障开销未摊销会反噬；仅按发射槽节省建模低估收益。
