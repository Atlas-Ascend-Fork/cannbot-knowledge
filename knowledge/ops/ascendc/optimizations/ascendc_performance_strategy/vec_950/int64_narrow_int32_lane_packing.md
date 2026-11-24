---
type: Optimization
title: int64 窄域 int32 视图的偶 lane 密集化（lane packing）：过门 slice 把 2x 视图的结构性死奇 lane 压缩成 N 元素密集 int32 窗口执行已验证半宽轮体，出口一次性扩张回交错布局
description: 将int64窄域的int32视图有效lane密集打包，消除奇数死lane计算。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/int64-narrow-int32-lane-packing.md
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
      "计数与掩码纪律：密集化后数据面 API 精确到 N，Compare/Compares/Select 按 AlignUp(N,64)；unpack 写回按 2N 且零高字必须显式产生（唯一新增出口契约）；尾 lane 只触碰窗口内私有 scratch，不新增越界面",
      "in-place pack 需给出前向单调安全性论证（目的 block 的写区间不早于其后任何源读区间）；若改用专用 TBuf/索引表须恢复 host/kernel UB 预算 twin 纪律并扩大编辑面前先记录",
      "门失败 fallback 臂逐字保留，且必须以强制门失败探针验证（不以 case 集通过替代）；correctness 按全量 all_cases 口径（跨模板共享文件时零改动实例也要验证）",
      "不引入 RegTensor 数组化/动态索引（NEG-4）；新增 load/store 基址与步幅满足 32B 对齐与块粒度（NEG-3）；不引入未在本工具链验证过的跨宽 Reg::Cast",
      "向量数据面重写必须以改前/改后 A/B 逐位差分验收（L-SIMD-UNROLL-SREG-REINIT 教训），探针须覆盖值域深浅、gcd(0,0)/(n,0)/(0,n)、±1/INT_MIN/半宽边界、奇数尾块、广播形态与强制门失败臂",
      "共享窗口复用不得触碰 host：op_host 文件逐字节不变，route/驻留/blockDim 判定不变（Block Num 不变是结构不变量验收项）"
    ],
    "excluded_conditions": [
      "门命中率低的值域分布（|v| 频繁 >=2^31）——机制退化为 fallback 慢路径 + 门读回 + pack 开销，收益以门命中率为前提",
      "无数据域门或视图内全部 lane 均有效（不存在死 lane 可压缩）时不适用",
      "非 VEC-bound（搬运/带宽/launch/scalar 主导）时不预期收益",
      "交织原语在目标工具链不可用且备选载体（跨段 load / UB Gather）未经验证时不得实施（未验证载体不得顺手引入）"
    ],
    "required_conditions": [
      "已存在并被验证的数据域门窄快路径（全 slice 值域门 |A|,|B|<2^31），使半宽视图的奇数 lane 是结构性死 lane（恒零、对结果位精确 no-op）——密集化是纯布局变换的前提",
      "VEC-bound 且增量成本已标定为按向量发射吞吐运行（增量 chunk 成本 ≈ 轮体指令数×轮数/64 lane），使 lane 利用率翻倍直接转化为每元素周期减半",
      "存在已验证的半宽度轮体（normalize/chunk/final）可原样复用，且密集化只需改元素数口径与出入口布局",
      "有可用的交织/解交织类布局原语（或已验证的等价载体），并能以 in-place 窗口复用或 twin 对账的专用窗口保持 host tiling 零改动"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-27",
  "evidence": [
    {
      "case": "T3(3,6,9,13,17,20) target + int16/int32(2,4,5,8,11,12,15,16,18) control",
      "note": "同机制首轮独立实现与采集：patch sha256=3234f647… 与 round-2 逐字节相同、kernel 同哈希 2cc7b7d9d1c0cba1；terminal 为机械 rollback（checkpoint accept 的 decision-attempt 绑定缺陷，非证据否决），其独立采集与 round-2 差 <=0.4%，作为 round-2 归档条目的复现证据保留",
      "operator_class": "broadcast",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": "T3 1.4257x (R7 1.5070x / R8 1.3094x); 15-case incremental 1.171x; control 0.999-1.002x; A/B 39,466,956 elements bit-exact",
      "status": "accepted"
    },
    {
      "comparison_sha256": "d8dd676bedf08541c805b867807ae17f114e1a1ed83f0a730db62b5da5f4419e",
      "decision_sha256": "4b9ea765fa7ee2f0e6decb3c680cadb5b75cacf3939cf15e2d965dce9b39be24",
      "operator_class": "broadcast",
      "performance_sha256": "33ade70714610a83356a63526c062a44ad8cd3d8621d18485ca379a05b94936a",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "9a8465ea9b6b57d296056fdbcb871003d2504837316aba581491674ae7a79177",
      "verify_sha256": "19b904f09e1ea20c7ca15c9592cc1387c538752829fd99079339202f683d83d7"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "dead-lane-underutilization",
      "fixed-round-loop",
      "lane-utilization"
    ],
    "dtypes": [
      "int64"
    ],
    "pattern": "half-width-view-lane-packing",
    "structure": [
      "vec-iterative-loop",
      "streaming-elementwise",
      "data-gate",
      "half-width-view",
      "layout-transform",
      "dtype-scoped-dispatch"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-INT64-NARROW-INT32-LANE-PACKING",
  "implementation_steps": [
    "确认前置：数据域门窄快路径已验证、奇 lane 恒 (0,0)、增量 chunk 成本与指令计数模型吻合（发射吞吐标定）、半宽轮体已验证",
    "选择 pack/unpack 载体（首选已在本工具链验证的交织/解交织原语；任何与策略文本的载体偏差须预先论证并以后续等价证据闭合）",
    "在过门分支内实现 in-place 密集化（或 twin 对账专用窗口）：pack 到 N 元素密集窗口，半宽轮体元素数口径改为 N，出口 unpack 显式产生零高字",
    "门失败臂、abs-init、门计算与回读、not-done 早退骨架、其余 dtype 实例逐字保留；host 文件零改动",
    "全量 all_cases verify + 重建 A/B 逐位差分与强制门失败探针；frozen-tool 性能采集按目标 route / 控制组拆分验收，结构不变量复核（Block Num、MTE2 绝对时长、host 逐字节）"
  ],
  "intent": "消除半宽视图换域后残留的 50% 死 lane 结构性放大：数据域转移后每元素成本恰为 int32 域 2x（一半 lane 计算恒 (0,0) 的死数据），把有效 lane 密集化使 normalize/chunk/final 三段有效吞吐翻倍。",
  "mechanism": "门计算与回读沿用父版（abs 后 Or->ShiftRights(31)->EQ0->Reduce + 一次 TQueSync<PIPE_V,PIPE_S> 读回）；过门分支新增 pack 阶段：以 Reg::Interleave/DeInterleave（vintlv/vdintlv，与工具链 UnPack<int64_t,int32_t> 同源原语；strategy 文本给出的 DINTLV load / UB Gather 备选载体被实现者以功能等价证据替换并由 A/B 逐位差分 + 预测带内性能证实）把 a32/b32 的 2N 交错窗口压缩为 N 元素密集窗口，in-place 复用既有窗口前半段（A/B 密集窗口用 a32/b32 前半段、P 用 g32 前半段，前向单调安全：目的 block i 写 [i*64,(i+1)*64)，其后所有源读位于 2j>=i+1），因此 op_host 零改动、T3 ubFactor 与驻留/route 判定不变、Block Num 不变；ComputeGcdNarrowNormalize32/ChunkVF32/Final32 的元素数口径由 2*sliceElems 改为 sliceElems 原样跑已验证 int32 轮体；出口 unpack 把 N 密集结果扩张回 2N 交错 [res,0] 写回，奇数 lane 的零高字由 unpack 显式产生（替代父版死 lane 的隐式 Mul(0,P)=0，这是唯一的新增出口契约）。计数纪律：密集化后数据面 API 精确到 N，Compare/Compares/Select 按 AlignUp(N,64) 掩码，尾 lane 只触碰窗口内私有 scratch；not-done 早退骨架（slice 级 Reduce SUM + TQueSync + GetValue，NARROW_MAX_CHUNKS=8）逐字沿用；门失败 fallback 臂（int64 Div 截断欧几里得，MAX_ROUNDS=93）与 int64 abs-init 逐字保留；全部新代码在 sizeof(TW)==8 编译期实例内，int16/int32 实例零改动。",
  "name": "int64 窄域 int32 视图的偶 lane 密集化（lane packing）：过门 slice 把 2x 视图的结构性死奇 lane 压缩成 N 元素密集 int32 窗口执行已验证半宽轮体，出口一次性扩张回交错布局",
  "operator_class": "broadcast",
  "operator_scope": "VEC-bound 的流式 elementwise int64 迭代计算（GM->UB->VEC->UB->GM），且已落地数据域门窄快路径（全部 |A|,|B|<2^31 的 slice 按 int32 视图执行，见 ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH）：该 2x lane 视图中奇数 lane 是结构性死 lane（恒 (0,0)，对结果位精确 no-op 但仍消耗每个 lockstep 向量指令槽位），存在已验证的半宽 normalize/chunk/final 轮体可原样复用，且有交织/解交织类布局原语可用",
  "principle": "数据域门（|A|,|B|<2^31 全 slice 恒真）保证 int64 高字恒 0，int32 视图奇数 lane 是纯结构死 lane。lockstep SIMD 下向量指令按整 block 发射，死 lane 与活 lane 同价；若增量 chunk 成本已标定为按向量发射吞吐运行（实测增量 chunk 成本 ≈ 轮体指令数 × chunk 轮数 / 64 lane，误差 <3%），则把 2N 视图压缩为 N 元素密集窗口是逐元素位等价的纯布局变换，直接把三段轮体的每元素周期减半。不可减半的固定项（abs-init、门计算与回读、final、GENERAL 驻留 gather）与一次性 pack/unpack 开销远小于被消除的死 lane 成本，净收益为正；固定项占比越大的 route（如广播驻留）落点越贴近保守档，这是模型预期而非回归。",
  "related_anti_patterns": [],
  "risks": [
    "pack/unpack 索引、偏移或 N/2N 口径混用导致仅目标域出错（排查顺序：仅过门域错 -> pack 索引/零高字产生方式；控制域错 -> 作用域泄漏）",
    "密集化后 a==0 修复与 gcd(0,0)/(n,0)/(0,n) 语义在无死 lane 路径上的实现偏差（原死 lane 吸收语义不再隐式存在）",
    "载体偏差（策略文本载体 vs 实际原语）未经等价证据闭合；或引入未验证的跨宽 Cast",
    "in-place 复用破坏前向单调性造成窗口内读写冲突",
    "共享安装位指纹漂移使性能证据绑定外来 kernel（须以 build/verify/installed/产物四点 fingerprint 闭环验收）"
  ],
  "slug": "int64-narrow-int32-lane-packing",
  "summary": "对已过数据域门的 int64 slice，把 int32 视图（2N lane，奇 lane 恒 (0,0) 死 lane）中的有效偶数 lane（低字）用 Reg::Interleave/DeInterleave 压缩成 N 元素密集 int32 窗口，运行已验证的 int32 Stein normalize/chunk/final 后在出口一次性扩张回 [res,0] 交错布局（零高字显式产生）；int64 abs+门+回读与未过门 fallback 臂逐字保留，host 零改动（in-place 窗口复用）。实测 T3 目标域六 case 时延加权 1.4247x（R7-T3-SAME 1.5051x / R8-T3-GENRES 1.3094x）、9 个 int16/int32 控制 case 0.9997x（零泄漏）、15-case incremental 1.1705x、A/B 逐位差分 39,466,956 元素位精确。",
  "verification": {
    "correctness": [
      "round 2 verify ok=true 20/20（run.json.all_cases 全量），fingerprint kernel 2cc7b7d9d1c0cba1 与 build/verify/安装态闭环（git/source 四字段一致）",
      "重建 A/B 逐位差分（rounds/002/probe/ab_evidence.json）：13 探针、39,466,956 个 int64 元素、bit_exact_diff=0，相位 A 绑定 parent（baseline）kernel、相位 B 绑定本轮 kernel，覆盖 ±1e5/±100 深浅收敛、gcd(0,0)/gcd(n,0)/gcd(0,n)、±1/INT64_MIN/2^31-1 角点、奇数 sliceElems 尾块 n∈{1,63,65,255,257,319}、R8 广播驻留形态、以及 P6/P7 强制门失败臂（不以 case 集通过替代门失败臂验证）",
      "同机制 round-1 独立实现+采集（同 kernel 哈希）A/B 亦位精确，六 case 中位数与 round-2 差 <=0.4%（复现性）"
    ],
    "performance": [
      "T3 目标域六 case 时延加权 1.4247x（期望档 1.4223x，接受带 >=1.30x）：R7-T3-SAME 1.5051x、R8-T3-GENRES 1.3094x（R8 贴近保守档是 GENERAL 驻留 gather 固定开销不随密集化变化的模型预期）",
      "逐 case cyc/elem 折算全部落预测带：深收敛 SAME case 22.87-23.02 -> 15.17-15.32（带 [14.0,15.4]）、浅收敛 14.77 -> 10.80（[10.0,11.2]）、广播驻留 32.44/32.71 -> 24.80/24.97（[23.5,25.6]）",
      "9 个 int16/int32 控制 case（覆盖全部非目标 route 的 host tiling）0.9966-1.0008x、聚合 0.9997x——零作用域泄漏；15-case incremental 1.1705x、cumulative 1.1695x，6 improved / 9 unchanged / 0 regressed",
      "机制归因：MTE2 绝对时长与 baseline 持平（零新增 GM 流量，占比上升纯因总时长下降）、Block Num 全部 64（tiling/route 划分不变，与 op_host 零改动互证）、vec_ratio 微降属固定开销占比相对上升"
    ],
    "rollback_signals": [
      "任一控制 case 偏离 parent ±5%（作用域泄漏）或任一 verify 失败（重点仅过门域错 -> pack 口径；控制域错 -> 共享函数被误改）",
      "T3 聚合 <1.20x 或任一 T3 case 慢于 parent 1.02x（先排查复现环境指纹，确认非环境后判定机制不盈利并回退；不得以顺手叠加其它机制抢救）",
      "device error 507035（密集窗口指针/步幅违反计数纪律）或 507015（窗口越界/twin 失配）"
    ]
  }
}
-->

# 性能优化策略：int64 窄域 int32 视图的偶 lane 密集化（lane packing）：过门 slice 把 2x 视图的结构性死奇 lane 压缩成 N 元素密集 int32 窗口执行已验证半宽轮体，出口一次性扩张回交错布局

单一优化点：对已过数据域门的 int64 slice，把 int32 视图（2N lane，奇 lane 恒 (0,0) 死 lane）中的有效偶数 lane（低字）用 Reg::Interleave/DeInterleave 压缩成 N 元素密集 int32 窗口，运行已验证的 int32 Stein normalize/chunk/final 后在出口一次性扩张回 [res,0] 交错布局（零高字显式产生）；int64 abs+门+回读与未过门 fallback 臂逐字保留，host 零改动（in-place 窗口复用）。实测 T3 目标域六 case 时延加权 1.4247x（R7-T3-SAME 1.5051x / R8-T3-GENRES 1.3094x）、9 个 int16/int32 控制 case 0.9997x（零泄漏）、15-case incremental 1.1705x、A/B 逐位差分 39,466,956 元素位精确。

## 1. 原理

数据域门（|A|,|B|<2^31 全 slice 恒真）保证 int64 高字恒 0，int32 视图奇数 lane 是纯结构死 lane。lockstep SIMD 下向量指令按整 block 发射，死 lane 与活 lane 同价；若增量 chunk 成本已标定为按向量发射吞吐运行（实测增量 chunk 成本 ≈ 轮体指令数 × chunk 轮数 / 64 lane，误差 <3%），则把 2N 视图压缩为 N 元素密集窗口是逐元素位等价的纯布局变换，直接把三段轮体的每元素周期减半。不可减半的固定项（abs-init、门计算与回读、final、GENERAL 驻留 gather）与一次性 pack/unpack 开销远小于被消除的死 lane 成本，净收益为正；固定项占比越大的 route（如广播驻留）落点越贴近保守档，这是模型预期而非回归。

实现机制：门计算与回读沿用父版（abs 后 Or->ShiftRights(31)->EQ0->Reduce + 一次 TQueSync<PIPE_V,PIPE_S> 读回）；过门分支新增 pack 阶段：以 Reg::Interleave/DeInterleave（vintlv/vdintlv，与工具链 UnPack<int64_t,int32_t> 同源原语；strategy 文本给出的 DINTLV load / UB Gather 备选载体被实现者以功能等价证据替换并由 A/B 逐位差分 + 预测带内性能证实）把 a32/b32 的 2N 交错窗口压缩为 N 元素密集窗口，in-place 复用既有窗口前半段（A/B 密集窗口用 a32/b32 前半段、P 用 g32 前半段，前向单调安全：目的 block i 写 [i*64,(i+1)*64)，其后所有源读位于 2j>=i+1），因此 op_host 零改动、T3 ubFactor 与驻留/route 判定不变、Block Num 不变；ComputeGcdNarrowNormalize32/ChunkVF32/Final32 的元素数口径由 2*sliceElems 改为 sliceElems 原样跑已验证 int32 轮体；出口 unpack 把 N 密集结果扩张回 2N 交错 [res,0] 写回，奇数 lane 的零高字由 unpack 显式产生（替代父版死 lane 的隐式 Mul(0,P)=0，这是唯一的新增出口契约）。计数纪律：密集化后数据面 API 精确到 N，Compare/Compares/Select 按 AlignUp(N,64) 掩码，尾 lane 只触碰窗口内私有 scratch；not-done 早退骨架（slice 级 Reduce SUM + TQueSync + GetValue，NARROW_MAX_CHUNKS=8）逐字沿用；门失败 fallback 臂（int64 Div 截断欧几里得，MAX_ROUNDS=93）与 int64 abs-init 逐字保留；全部新代码在 sizeof(TW)==8 编译期实例内，int16/int32 实例零改动。

## 2. 性能问题模式

- 优化目标：消除半宽视图换域后残留的 50% 死 lane 结构性放大：数据域转移后每元素成本恰为 int32 域 2x（一半 lane 计算恒 (0,0) 的死数据），把有效 lane 密集化使 normalize/chunk/final 三段有效吞吐翻倍。
- 适用数据流：VEC-bound 的流式 elementwise int64 迭代计算（GM->UB->VEC->UB->GM），且已落地数据域门窄快路径（全部 |A|,|B|<2^31 的 slice 按 int32 视图执行，见 ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH）：该 2x lane 视图中奇数 lane 是结构性死 lane（恒 (0,0)，对结果位精确 no-op 但仍消耗每个 lockstep 向量指令槽位），存在已验证的半宽 normalize/chunk/final 轮体可原样复用，且有交织/解交织类布局原语可用
- Feature signature：`{"bottleneck": ["vec-bound", "dead-lane-underutilization", "fixed-round-loop", "lane-utilization"], "dtypes": ["int64"], "pattern": "half-width-view-lane-packing", "structure": ["vec-iterative-loop", "streaming-elementwise", "data-gate", "half-width-view", "layout-transform", "dtype-scoped-dispatch"]}`

## 3. 正确性红线

- pack/unpack 索引、偏移或 N/2N 口径混用导致仅目标域出错（排查顺序：仅过门域错 -> pack 索引/零高字产生方式；控制域错 -> 作用域泄漏）
- 密集化后 a==0 修复与 gcd(0,0)/(n,0)/(0,n) 语义在无死 lane 路径上的实现偏差（原死 lane 吸收语义不再隐式存在）
- 载体偏差（策略文本载体 vs 实际原语）未经等价证据闭合；或引入未验证的跨宽 Cast
- in-place 复用破坏前向单调性造成窗口内读写冲突
- 共享安装位指纹漂移使性能证据绑定外来 kernel（须以 build/verify/installed/产物四点 fingerprint 闭环验收）

资源与硬件约束：

- 计数与掩码纪律：密集化后数据面 API 精确到 N，Compare/Compares/Select 按 AlignUp(N,64)；unpack 写回按 2N 且零高字必须显式产生（唯一新增出口契约）；尾 lane 只触碰窗口内私有 scratch，不新增越界面
- in-place pack 需给出前向单调安全性论证（目的 block 的写区间不早于其后任何源读区间）；若改用专用 TBuf/索引表须恢复 host/kernel UB 预算 twin 纪律并扩大编辑面前先记录
- 门失败 fallback 臂逐字保留，且必须以强制门失败探针验证（不以 case 集通过替代）；correctness 按全量 all_cases 口径（跨模板共享文件时零改动实例也要验证）
- 不引入 RegTensor 数组化/动态索引（NEG-4）；新增 load/store 基址与步幅满足 32B 对齐与块粒度（NEG-3）；不引入未在本工具链验证过的跨宽 Reg::Cast
- 向量数据面重写必须以改前/改后 A/B 逐位差分验收（L-SIMD-UNROLL-SREG-REINIT 教训），探针须覆盖值域深浅、gcd(0,0)/(n,0)/(0,n)、±1/INT_MIN/半宽边界、奇数尾块、广播形态与强制门失败臂
- 共享窗口复用不得触碰 host：op_host 文件逐字节不变，route/驻留/blockDim 判定不变（Block Num 不变是结构不变量验收项）

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- 已存在并被验证的数据域门窄快路径（全 slice 值域门 |A|,|B|<2^31），使半宽视图的奇数 lane 是结构性死 lane（恒零、对结果位精确 no-op）——密集化是纯布局变换的前提
- VEC-bound 且增量成本已标定为按向量发射吞吐运行（增量 chunk 成本 ≈ 轮体指令数×轮数/64 lane），使 lane 利用率翻倍直接转化为每元素周期减半
- 存在已验证的半宽度轮体（normalize/chunk/final）可原样复用，且密集化只需改元素数口径与出入口布局
- 有可用的交织/解交织类布局原语（或已验证的等价载体），并能以 in-place 窗口复用或 twin 对账的专用窗口保持 host tiling 零改动

不适用：

- 门命中率低的值域分布（|v| 频繁 >=2^31）——机制退化为 fallback 慢路径 + 门读回 + pack 开销，收益以门命中率为前提
- 无数据域门或视图内全部 lane 均有效（不存在死 lane 可压缩）时不适用
- 非 VEC-bound（搬运/带宽/launch/scalar 主导）时不预期收益
- 交织原语在目标工具链不可用且备选载体（跨段 load / UB Gather）未经验证时不得实施（未验证载体不得顺手引入）

## 5. 实施步骤

1. 确认前置：数据域门窄快路径已验证、奇 lane 恒 (0,0)、增量 chunk 成本与指令计数模型吻合（发射吞吐标定）、半宽轮体已验证
2. 选择 pack/unpack 载体（首选已在本工具链验证的交织/解交织原语；任何与策略文本的载体偏差须预先论证并以后续等价证据闭合）
3. 在过门分支内实现 in-place 密集化（或 twin 对账专用窗口）：pack 到 N 元素密集窗口，半宽轮体元素数口径改为 N，出口 unpack 显式产生零高字
4. 门失败臂、abs-init、门计算与回读、not-done 早退骨架、其余 dtype 实例逐字保留；host 文件零改动
5. 全量 all_cases verify + 重建 A/B 逐位差分与强制门失败探针；frozen-tool 性能采集按目标 route / 控制组拆分验收，结构不变量复核（Block Num、MTE2 绝对时长、host 逐字节）

## 6. LLM 前置问题

- 目标实现是否满足：已存在并被验证的数据域门窄快路径（全 slice 值域门 |A|,|B|<2^31），使半宽视图的奇数 lane 是结构性死 lane（恒零、对结果位精确 no-op）——密集化是纯布局变换的前提？
- 目标实现是否满足：VEC-bound 且增量成本已标定为按向量发射吞吐运行（增量 chunk 成本 ≈ 轮体指令数×轮数/64 lane），使 lane 利用率翻倍直接转化为每元素周期减半？
- 目标实现是否满足：存在已验证的半宽度轮体（normalize/chunk/final）可原样复用，且密集化只需改元素数口径与出入口布局？
- 是否命中排除条件：门命中率低的值域分布（|v| 频繁 >=2^31）——机制退化为 fallback 慢路径 + 门读回 + pack 开销，收益以门命中率为前提？

## 7. 验收标准

正确性：

- round 2 verify ok=true 20/20（run.json.all_cases 全量），fingerprint kernel 2cc7b7d9d1c0cba1 与 build/verify/安装态闭环（git/source 四字段一致）
- 重建 A/B 逐位差分（rounds/002/probe/ab_evidence.json）：13 探针、39,466,956 个 int64 元素、bit_exact_diff=0，相位 A 绑定 parent（baseline）kernel、相位 B 绑定本轮 kernel，覆盖 ±1e5/±100 深浅收敛、gcd(0,0)/gcd(n,0)/gcd(0,n)、±1/INT64_MIN/2^31-1 角点、奇数 sliceElems 尾块 n∈{1,63,65,255,257,319}、R8 广播驻留形态、以及 P6/P7 强制门失败臂（不以 case 集通过替代门失败臂验证）
- 同机制 round-1 独立实现+采集（同 kernel 哈希）A/B 亦位精确，六 case 中位数与 round-2 差 <=0.4%（复现性）

性能：

- T3 目标域六 case 时延加权 1.4247x（期望档 1.4223x，接受带 >=1.30x）：R7-T3-SAME 1.5051x、R8-T3-GENRES 1.3094x（R8 贴近保守档是 GENERAL 驻留 gather 固定开销不随密集化变化的模型预期）
- 逐 case cyc/elem 折算全部落预测带：深收敛 SAME case 22.87-23.02 -> 15.17-15.32（带 [14.0,15.4]）、浅收敛 14.77 -> 10.80（[10.0,11.2]）、广播驻留 32.44/32.71 -> 24.80/24.97（[23.5,25.6]）
- 9 个 int16/int32 控制 case（覆盖全部非目标 route 的 host tiling）0.9966-1.0008x、聚合 0.9997x——零作用域泄漏；15-case incremental 1.1705x、cumulative 1.1695x，6 improved / 9 unchanged / 0 regressed
- 机制归因：MTE2 绝对时长与 baseline 持平（零新增 GM 流量，占比上升纯因总时长下降）、Block Num 全部 64（tiling/route 划分不变，与 op_host 零改动互证）、vec_ratio 微降属固定开销占比相对上升

回滚信号：

- 任一控制 case 偏离 parent ±5%（作用域泄漏）或任一 verify 失败（重点仅过门域错 -> pack 口径；控制域错 -> 共享函数被误改）
- T3 聚合 <1.20x 或任一 T3 case 慢于 parent 1.02x（先排查复现环境指纹，确认非环境后判定机制不盈利并回退；不得以顺手叠加其它机制抢救）
- device error 507035（密集窗口指针/步幅违反计数纪律）或 507015（窗口越界/twin 失配）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260826_142703-b3c56c（round=1, status=accepted, case=T3(3,6,9,13,17,20) target + int16/int32(2,4,5,8,11,12,15,16,18) control, speedup=T3 1.4257x (R7 1.5070x / R8 1.3094x); 15-case incremental 1.171x; control 0.999-1.002x; A/B 39,466,956 elements bit-exact）
- gcd-20260826_142703-b3c56c（round=2, status=accepted）

## 检索卡（短卡）

动作：将int64窄域的int32视图有效lane密集打包，消除奇数死lane计算
适用：已有已验证的全slice窄域门|A|、|B|<2^31，int64高字为0且int32视图奇lane恒死
限制：密集化后数据面API精确到N；pack/unpack的索引、偏移及N/2N口径必须一致
范围：elementwise-arithmetic的int64窄域快路径
检索词：int64、int32视图、偶lane、死lane、lockstep SIMD、pack/unpack
机会：换域后每元素成本为int32域2倍，半数lane恒为(0,0)
