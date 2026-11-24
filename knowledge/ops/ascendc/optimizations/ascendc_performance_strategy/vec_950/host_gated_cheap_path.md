---
type: Optimization
title: host 侧放行：恒等条件下的取模消除 / UB 预算按实际队列数重平衡抬高 tile 容量
description: 两类 host 侧放行的合并族。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/host-gated-cheap-path.md
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
      "恒等门控必须在 host 侧静态判定（post-split gatherLen==1 且 !trailMismatch），以内核可派发的编码下发（kind=3/4），非命中路径保持原编码",
      "内核侧的分派必须外提到热循环之外（本 run repair-r2 把 modKind 分派提升到行循环内、p 热循环外），否则循环内分派会吃掉收益",
      "原路径必须逐指令等价保留为回退分支，新的编码不得改变原编码（0/1/2）的语义",
      "UB 预算必须重新对账：单缓冲化会改变队列占用，新的每元素预算须与 UB 总量核对（本 run 7F ≤ 253952B）",
      "容量上调后保持 dtype 的子元素对齐粒度（本 run 16 元素/32B 对齐）"
    ],
    "excluded_conditions": [
      "取模域落在 pow2/magic 快路径的 case 不适用恒等门控：原编码已足够，本机制只覆盖「原先每元素完整运行时除法」的域（本 run kind=0/1/2 保留原样）",
      "批深很大、关键路径本就由 MTE 带宽决定时，容量上调收益有限（本 run case_5 fp16 仅 -1.1%）",
      "out 单缓冲会引入 MTE3 串行化（V(t+1) 需等 MTE3(t)）；若 MTE2 余量不足以遮蔽该次级效应则净负",
      "trailMismatch 或非 split 模式不适用恒等门控"
    ],
    "required_conditions": [
      "存在可由 host 静态判定的恒等/放行条件（本 run gather：post-split gatherLen==1 ⇒ rowLen==inner ⇒ 逐元素 m=p%inner 退化为恒等 p）",
      "恒等条件恰好覆盖成本最高的域（本 run case10 inner=136891 非 pow2 非 magic，原先每元素走完整运行时 u32 除法）",
      "tile 数与关键路径元素数受每元素 UB 预算约束，且预算当前按队列均分而非按实际队列数（本 run foreach：ComputeFmax 用 ubSize/8 假定 QUEUE_COUNT=4×BUFFER_NUM=2，但 in/out 队列实际为 IN_BUFFER_NUM=2×IN_STREAM_NUM=3 + OUT_BUFFER_NUM=1 = 7）",
      "关键路径元素数对 tile 数敏感（本 run case_1 tilesPerCore 5→4 使关键路径元素 39680→36224）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 223.871,
      "before_us": 242.004,
      "mechanism": "split-row-modulo-identity-flat-u32",
      "operator": "gather",
      "operator_class": "index-gather",
      "pairs": 45,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.081,
      "status": "accepted"
    },
    {
      "after_us": 27.7243,
      "before_us": 29.3726,
      "mechanism": "out-queue-singlebuf-fmax-upscale",
      "operator": "foreach_addcdiv_scalar",
      "operator_class": "elementwise",
      "pairs": 15,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.0595,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "runtime-modulo-per-element",
      "ub-budget-misallocation",
      "tile-count-key-path"
    ],
    "pattern": "host-gated-cheap-path",
    "structure": [
      "host-side-identity-detection",
      "modkind-encoded-dispatch",
      "queue-based-ub-budget-rebalance",
      "fallback-branch-instruction-identical"
    ]
  },
  "generality": "op_class",
  "id": "HOST-GATED-CHEAP-PATH",
  "implementation_steps": [
    "恒等门控路径（gather）：在 host T2 的 modKind 编码块新增门——post-split gatherLen==1 且 !trailMismatch 时下发 kind=3（xDim·inner≤2^32，identity + u32 im）/ kind=4（巨张量 identity + u64 im）；pow2/magic/原取模路径保持原编码不变",
    "内核侧把 modKind 分派从 p 热循环内提升到行循环内、p 热循环外（repair-r2，消除 r1 的循环内分派回退）；kind=3 走 (u32)idx*inner+p 无取模平坦循环，kind=4 走 u64 平坦循环，kind 0/1/2 内层循环与 champion 逐指令等价",
    "tiling_data 字段注释扩展 kind=3/4 语义（无结构体变更、无 tiling-key/模板实例变更）",
    "UB 预算重平衡路径（foreach）：host ComputeFmax 的每元素预算由 ubSize/8（假定 QUEUE_COUNT=4 × BUFFER_NUM=2 均分）改为 ubSize/7（按实际队列数 IN_BUFFER_NUM=2 × IN_STREAM_NUM=3 + OUT_BUFFER_NUM=1）",
    "内核侧 out 队列由双缓冲改单缓冲 InitBuffer(outQueueY, 1, bufSize)（in 队列仍双缓冲保 MTE2 预取），UB 总占用 7F ≤ 253952B",
    "容量上调后保持 dtype 的子元素对齐粒度（本 run F_max fp32 7936→9056、fp16/bf16 15872→18128，+14.2%，保持 16 元素/32B 对齐）"
  ],
  "intent": "利用 host 侧的静态信息或预算重算，让内核走更省的路径：host 能判定某个运行时开销（如逐元素取模）退化为恒等时下发专门的编码，内核按编码走无开销快路径；宿主发现 UB 预算按错误的队列数均分时，按实际队列数重平衡以抬高 tile 容量、缩短关键路径。",
  "mechanism": "两类 host 侧放行。(a) 恒等条件下的取模消除：split 行（post-split gatherLen==1 ⇒ rowLen==inner）使逐元素 m=p%inner 恒等于 p，host 以 modKind=3/4 下发（区分 xDim·inner≤2^32 的 u32 域与巨张量 u64 域），内核把 modKind 分派提升到 p 热循环外，命中时走 (u32)idx*inner+p 的无取模平坦循环；非命中编码 0/1/2 逐指令等价保留。(b) UB 预算按实际队列数重平衡：把每元素预算从 ubSize/8（错误假定 4 队列 × 2 缓冲均分）改为 ubSize/7（实际 in 2×3 + out 1），同步把 out 队列改单缓冲（in 保持双缓冲以保 MTE2 预取），使 F_max 上调 14.2%、tile 数下降、关键路径元素数缩短。",
  "name": "host 侧放行：恒等条件下的取模消除 / UB 预算按实际队列数重平衡抬高 tile 容量",
  "operator_class": "index-gather",
  "operator_scope": "内核热循环中存在可由 host 静态判定其恒等或可解除的运行时开销（如逐元素取模），或 host 的每次元素 UB 预算按错误的队列数/缓冲数均分而实际队列结构不同、导致 tile 容量被低估的算子",
  "principle": "有一类收益不需要改算法，只需要 host 侧知道得更多：内核里某些逐元素开销（取模、分支、参数重算）在特定形状下逻辑上退化为恒等，而 host 掌握形状信息因而能判定这个条件并下发专门的编码；同样，host 的容量推导若沿用了与实际队列结构不符的均分系数，就会系统性低估容量。两者的共同点是「host 算得比内核准」——收益来自把这个信息传下去或把系数修正，而不是来自内核代码更快。判定要点是恒等条件必须静态可判、且分派外提到热循环之外，否则循环内分支会吃掉全部收益。",
  "related_anti_patterns": [],
  "risks": [
    "分派位置决定成败：本 run gather round_01 把 modKind 分派留在 p 热循环内，分派开销抵消收益导致回退，repair-r2 外提到行循环内才兑现。这是该机制的典型失败模式",
    "容量上调受次级效应限制：out 单缓冲使 V(t+1) 需等 MTE3(t)，本 run case_5（fp16，mte2 97% 饱和）仅 -1.1%，次级效应靠 MTE2 余量遮蔽；余量不足时会净负",
    "UB 预算公式改动须与总占用对账（本 run 7F ≤ 253952B），否则越界",
    "恒等条件判定若漏掉 trailMismatch 等否定项，会在边界形状上产生错误结果"
  ],
  "slug": "host-gated-cheap-path",
  "summary": "两类 host 侧放行的合并族。(a) 恒等条件下的取模消除（gather）：split 行使 m=p%inner 恒等，host 下发 modKind=3/4，内核把分派外提到 p 热循环外后走无取模平坦循环，case10（inner=136891 非 pow2 非 magic，原每元素完整运行时 u32 除法）1.1496x、case1/5 1.064x/1.033x，45 对配对全胜，geomean 242.004→223.871us（×1.0810）。(b) UB 预算按实际队列数重平衡（foreach_addcdiv_scalar）：每元素预算 ubSize/8 → ubSize/7（in 2×3 + out 1），out 队列改单缓冲，F_max 上调 14.2% 使 tile 数下降，geomean 29.3726→27.7243us（×1.0595）。两者精度均 20/20。",
  "verification": {
    "correctness": [
      "gather：三重门全通过（编译 0 修复、精度 20/20）；非命中编码 0/1/2 的内层循环与 champion 逐指令等价；无 tiling-key/模板实例变更",
      "foreach：编译/精度均无修复消耗；单轮应用；精度 20/20"
    ],
    "performance": [
      "gather：形式化 45 对平衡交替配对候选全胜，geomean 242.004→223.871us（1.0810x）；case1 1.0643x、case5 1.0325x、case10 1.1496x，无 case 回退",
      "foreach：每 case 15 对同 shape、溯源干净、平衡交替配对，geomean 29.3726→27.7243us（-5.61%，1.0595x）；case_10 -12.0%、case_1 -5.4% 方向明确，case_5 +1.05% 中性（<2% 回滚阈值）",
      "foreach 机制级直接效应（scalar 管道下降、MTE2 关键路径缩短）与预测吻合；容量上调量化：case_1 264→232 tile（tilesPerCore 5→4，关键路径元素 39680→36224，-8.7%）、case_10 133→117（3→2，23808→18112，-23.9%）、case_5 4230→3704（67→58，-1.1%）"
    ],
    "rollback_signals": [
      "分派未外提到热循环外，循环内分支吃掉收益（本 run gather round_01 已实证）",
      "out 单缓冲的 MTE3 串行化次级效应未被 MTE2 余量遮蔽（case_5 类饱和 case 恶化）",
      "UB 总占用超预算或恒等条件漏判否定项导致边界形状结果错误",
      "非命中路径不再与原实现逐指令等价"
    ]
  }
}
-->

# 性能优化策略：host 侧放行：恒等条件下的取模消除 / UB 预算按实际队列数重平衡抬高 tile 容量

两类 host 侧放行的合并族。(a) 恒等条件下的取模消除（gather）：split 行使 m=p%inner 恒等，host 下发 modKind=3/4，内核把分派外提到 p 热循环外后走无取模平坦循环，case10（inner=136891 非 pow2 非 magic，原每元素完整运行时 u32 除法）1.1496x、case1/5 1.064x/1.033x，45 对配对全胜，geomean 242.004→223.871us（×1.0810）。(b) UB 预算按实际队列数重平衡（foreach_addcdiv_scalar）：每元素预算 ubSize/8 → ubSize/7（in 2×3 + out 1），out 队列改单缓冲，F_max 上调 14.2% 使 tile 数下降，geomean 29.3726→27.7243us（×1.0595）。两者精度均 20/20。

## 1. 原理

有一类收益不需要改算法，只需要 host 侧知道得更多：内核里某些逐元素开销（取模、分支、参数重算）在特定形状下逻辑上退化为恒等，而 host 掌握形状信息因而能判定这个条件并下发专门的编码；同样，host 的容量推导若沿用了与实际队列结构不符的均分系数，就会系统性低估容量。两者的共同点是「host 算得比内核准」——收益来自把这个信息传下去或把系数修正，而不是来自内核代码更快。判定要点是恒等条件必须静态可判、且分派外提到热循环之外，否则循环内分支会吃掉全部收益。

实现机制：两类 host 侧放行。(a) 恒等条件下的取模消除：split 行（post-split gatherLen==1 ⇒ rowLen==inner）使逐元素 m=p%inner 恒等于 p，host 以 modKind=3/4 下发（区分 xDim·inner≤2^32 的 u32 域与巨张量 u64 域），内核把 modKind 分派提升到 p 热循环外，命中时走 (u32)idx*inner+p 的无取模平坦循环；非命中编码 0/1/2 逐指令等价保留。(b) UB 预算按实际队列数重平衡：把每元素预算从 ubSize/8（错误假定 4 队列 × 2 缓冲均分）改为 ubSize/7（实际 in 2×3 + out 1），同步把 out 队列改单缓冲（in 保持双缓冲以保 MTE2 预取），使 F_max 上调 14.2%、tile 数下降、关键路径元素数缩短。

## 2. 性能问题模式

- 优化目标：利用 host 侧的静态信息或预算重算，让内核走更省的路径：host 能判定某个运行时开销（如逐元素取模）退化为恒等时下发专门的编码，内核按编码走无开销快路径；宿主发现 UB 预算按错误的队列数均分时，按实际队列数重平衡以抬高 tile 容量、缩短关键路径
- 适用数据流：内核热循环中存在可由 host 静态判定其恒等或可解除的运行时开销（如逐元素取模），或 host 的每次元素 UB 预算按错误的队列数/缓冲数均分而实际队列结构不同、导致 tile 容量被低估的算子
- Feature signature：`{"bottleneck": ["runtime-modulo-per-element", "ub-budget-misallocation", "tile-count-key-path"], "pattern": "host-gated-cheap-path", "structure": ["host-side-identity-detection", "modkind-encoded-dispatch", "queue-based-ub-budget-rebalance", "fallback-branch-instruction-identical"]}`

## 3. 正确性红线

- 分派位置决定成败：本 run gather round_01 把 modKind 分派留在 p 热循环内，分派开销抵消收益导致回退，repair-r2 外提到行循环内才兑现。这是该机制的典型失败模式
- 容量上调受次级效应限制：out 单缓冲使 V(t+1) 需等 MTE3(t)，本 run case_5（fp16，mte2 97% 饱和）仅 -1.1%，次级效应靠 MTE2 余量遮蔽；余量不足时会净负
- UB 预算公式改动须与总占用对账（本 run 7F ≤ 253952B），否则越界
- 恒等条件判定若漏掉 trailMismatch 等否定项，会在边界形状上产生错误结果

资源与硬件约束：

- 恒等门控必须在 host 侧静态判定（post-split gatherLen==1 且 !trailMismatch），以内核可派发的编码下发（kind=3/4），非命中路径保持原编码
- 内核侧的分派必须外提到热循环之外（本 run repair-r2 把 modKind 分派提升到行循环内、p 热循环外），否则循环内分派会吃掉收益
- 原路径必须逐指令等价保留为回退分支，新的编码不得改变原编码（0/1/2）的语义
- UB 预算必须重新对账：单缓冲化会改变队列占用，新的每元素预算须与 UB 总量核对（本 run 7F ≤ 253952B）
- 容量上调后保持 dtype 的子元素对齐粒度（本 run 16 元素/32B 对齐）

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- 存在可由 host 静态判定的恒等/放行条件（本 run gather：post-split gatherLen==1 ⇒ rowLen==inner ⇒ 逐元素 m=p%inner 退化为恒等 p）
- 恒等条件恰好覆盖成本最高的域（本 run case10 inner=136891 非 pow2 非 magic，原先每元素走完整运行时 u32 除法）
- tile 数与关键路径元素数受每元素 UB 预算约束，且预算当前按队列均分而非按实际队列数（本 run foreach：ComputeFmax 用 ubSize/8 假定 QUEUE_COUNT=4×BUFFER_NUM=2，但 in/out 队列实际为 IN_BUFFER_NUM=2×IN_STREAM_NUM=3 + OUT_BUFFER_NUM=1 = 7）
- 关键路径元素数对 tile 数敏感（本 run case_1 tilesPerCore 5→4 使关键路径元素 39680→36224）

不适用：

- 取模域落在 pow2/magic 快路径的 case 不适用恒等门控：原编码已足够，本机制只覆盖「原先每元素完整运行时除法」的域（本 run kind=0/1/2 保留原样）
- 批深很大、关键路径本就由 MTE 带宽决定时，容量上调收益有限（本 run case_5 fp16 仅 -1.1%）
- out 单缓冲会引入 MTE3 串行化（V(t+1) 需等 MTE3(t)）；若 MTE2 余量不足以遮蔽该次级效应则净负
- trailMismatch 或非 split 模式不适用恒等门控

## 5. 实施步骤

1. 恒等门控路径（gather）：在 host T2 的 modKind 编码块新增门——post-split gatherLen==1 且 !trailMismatch 时下发 kind=3（xDim·inner≤2^32，identity + u32 im）/ kind=4（巨张量 identity + u64 im）；pow2/magic/原取模路径保持原编码不变
2. 内核侧把 modKind 分派从 p 热循环内提升到行循环内、p 热循环外（repair-r2，消除 r1 的循环内分派回退）；kind=3 走 (u32)idx*inner+p 无取模平坦循环，kind=4 走 u64 平坦循环，kind 0/1/2 内层循环与 champion 逐指令等价
3. tiling_data 字段注释扩展 kind=3/4 语义（无结构体变更、无 tiling-key/模板实例变更）
4. UB 预算重平衡路径（foreach）：host ComputeFmax 的每元素预算由 ubSize/8（假定 QUEUE_COUNT=4 × BUFFER_NUM=2 均分）改为 ubSize/7（按实际队列数 IN_BUFFER_NUM=2 × IN_STREAM_NUM=3 + OUT_BUFFER_NUM=1）
5. 内核侧 out 队列由双缓冲改单缓冲 InitBuffer(outQueueY, 1, bufSize)（in 队列仍双缓冲保 MTE2 预取），UB 总占用 7F ≤ 253952B
6. 容量上调后保持 dtype 的子元素对齐粒度（本 run F_max fp32 7936→9056、fp16/bf16 15872→18128，+14.2%，保持 16 元素/32B 对齐）

## 6. LLM 前置问题

- 目标实现是否满足：存在可由 host 静态判定的恒等/放行条件（本 run gather：post-split gatherLen==1 ⇒ rowLen==inner ⇒ 逐元素 m=p%inner 退化为恒等 p）？
- 目标实现是否满足：恒等条件恰好覆盖成本最高的域（本 run case10 inner=136891 非 pow2 非 magic，原先每元素走完整运行时 u32 除法）？
- 目标实现是否满足：tile 数与关键路径元素数受每元素 UB 预算约束，且预算当前按队列均分而非按实际队列数（本 run foreach：ComputeFmax 用 ubSize/8 假定 QUEUE_COUNT=4×BUFFER_NUM=2，但 in/out 队列实际为 IN_BUFFER_NUM=2×IN_STREAM_NUM=3 + OUT_BUFFER_NUM=1 = 7）？
- 目标实现是否满足：关键路径元素数对 tile 数敏感（本 run case_1 tilesPerCore 5→4 使关键路径元素 39680→36224）？
- 是否命中排除条件：取模域落在 pow2/magic 快路径的 case 不适用恒等门控：原编码已足够，本机制只覆盖「原先每元素完整运行时除法」的域（本 run kind=0/1/2 保留原样）？

## 7. 验收标准

正确性：

- gather：三重门全通过（编译 0 修复、精度 20/20）；非命中编码 0/1/2 的内层循环与 champion 逐指令等价；无 tiling-key/模板实例变更
- foreach：编译/精度均无修复消耗；单轮应用；精度 20/20

性能：

- gather：形式化 45 对平衡交替配对候选全胜，geomean 242.004→223.871us（1.0810x）；case1 1.0643x、case5 1.0325x、case10 1.1496x，无 case 回退
- foreach：每 case 15 对同 shape、溯源干净、平衡交替配对，geomean 29.3726→27.7243us（-5.61%，1.0595x）；case_10 -12.0%、case_1 -5.4% 方向明确，case_5 +1.05% 中性（<2% 回滚阈值）
- foreach 机制级直接效应（scalar 管道下降、MTE2 关键路径缩短）与预测吻合；容量上调量化：case_1 264→232 tile（tilesPerCore 5→4，关键路径元素 39680→36224，-8.7%）、case_10 133→117（3→2，23808→18112，-23.9%）、case_5 4230→3704（67→58，-1.1%）

回滚信号：

- 分派未外提到热循环外，循环内分支吃掉收益（本 run gather round_01 已实证）
- out 单缓冲的 MTE3 串行化次级效应未被 MTE2 余量遮蔽（case_5 类饱和 case 恶化）
- UB 总占用超预算或恒等条件漏判否定项导致边界形状结果错误
- 非命中路径不再与原实现逐指令等价

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260907_170122-free-002（operator=gather, mechanism=split-row-modulo-identity-flat-u32, status=accepted, speedup=1.0810, 242.004→223.871us, 45 对配对）
- loop_20260907_170122-free-002（operator=foreach_addcdiv_scalar, mechanism=out-queue-singlebuf-fmax-upscale, status=accepted, speedup=1.0595, 29.3726→27.7243us, 15 对配对）

## 检索卡（短卡）

动作：把内核每元素取模改为 host 判定恒等后下发编码走无取模平坦循环，分派外提到热循环外
适用：存在 host 可静态判定的恒等条件（post-split gatherLen==1），或 UB 预算按错误队列数均分
限制：分派须外提到热循环之外，循环内分派会吃掉收益；out 单缓冲的 MTE3 串行化须被 MTE2 余量遮蔽
范围：index-gather 的取模热循环与 elementwise 的 UB 预算推导
检索词：modKind、gatherLen==1、u32 平坦循环、ubSize/7、单缓冲 outQueueY
机会：原先每元素走完整运行时 u32 除法（inner=136891 非 pow2/magic）
代价：out 单缓冲使 V(t+1) 等 MTE3(t)，MTE2 余量不足时净负
