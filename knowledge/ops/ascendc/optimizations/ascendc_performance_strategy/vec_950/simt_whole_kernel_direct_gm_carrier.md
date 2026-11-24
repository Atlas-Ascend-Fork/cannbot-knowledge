---
type: Optimization
title: size/dtype 门控的整核 SIMT direct-GM 载体（入口早分叉 + 每核一次 VF_CALL + GM 直达读写）
description: 把逐 slice TQue/UB 载体改为 host size+dtype 门控的整核 SIMT direct-GM 数据流，入口在 UB 初始化前分叉、每核一次 VF_CALL。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-whole-kernel-direct-gm-carrier.md
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
      "GM 直达读写意味着无 UB 缓存效应：小热 operand 的窗口化 staging 只有均匀索引（每核连续行窗口）或 by-value 标量形态可行，decompose 驱动的随机索引 UB gather 会被 bank-stall 证伪（本 run r004 负向边界，knowledge/anti-pattern-r004.json）",
      "保留原 VEC 全路径逐字节不变作为 gate 排除 case 的结构与性能控制（control 带 [0.97,1.03]）",
      "int64 用 dim3(512) wave（参考实现 int64 wave），与 int16/int32 的 dim3(1024) 分开实例化"
    ],
    "excluded_conditions": [
      "不得带任何 UB/TQue 窗口形态混入 SIMT 分支：入口分叉点必须在 InitBuffer 之前，否则回到足迹/分发税",
      "门控不得只按 size 不按 dtype（dtype 决定 wave 宽度与每线程体；见 simt-direct-gm-size-gate-regression 与 simt-direct-gm-dtype-aware-gate）",
      "outDimNum 超过 decompose 表宽（8）或 totalNum 超过 int32 索引域时不得启用",
      "fp 类 dtype 在本证据域内未验证（整数角点/收敛域是本载体正确性前提）"
    ],
    "required_conditions": [
      "VEC_BOUND 的整数同/broadcast-shape elementwise 路由，瓶颈是每元素向量指令数或每-slice 载体开销",
      "存在可逐字移植的参考 per-thread 载体（硬件 ctz/ffs、逐元素精确收敛、退化早退），且 arch35 __simt_vf__ 可编译",
      "host tiling 能在 dtype 已知处做 size+dtype 门控，把小 case 留在原 VEC 路径",
      "broadcast 偏移可由每线程在既有 tiling 表上 stride-0 短路 decompose（维数<=表宽）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "boundary_relation": "与 simt-vf-carrier-per-tile-footprint-bound（同 op 前序 run 的 per-tile/per-256-slice 负向边界）互补：该卡明示载体未被否定，本卡给出通过形态",
      "facts": "int16/int32 整核载体；probe go（6 case 2.2–4.94x）；20-case 增量 1.8637x、零回归；最终官方分 62.64→70.01",
      "operator_class": "broadcast",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted"
    },
    {
      "comparison_sha256": "cf4805b6cf9eedcea4463af027fcc419a5732c0337981a1eb6ed6325b84cbb56",
      "decision_sha256": "0f74fd63dc1726807d1d6c90ea5e2b3a73c93fb8ad4cc781638ae6e2dfbd252e",
      "operator_class": "broadcast",
      "performance_sha256": "1df038ea647244f86064949b54fcf77598fa86024e2823a73e8e622b78c5911a",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "791629f594b2fde718d90a0bea941cae4666c03a1e7a8e1da2fb7aa654c051b8",
      "verify_sha256": "d4aae197a0249bbe7946a839edaac2d81f5d4d87c3378355f98234dc4149232f"
    },
    {
      "facts": "int64/T3 dtype 扩展；probe go（6 case 1.13–1.64x）；增量 1.2204x、零回归；同轮 7 control 全在 [0.9953,1.0078]",
      "operator_class": "broadcast",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted"
    },
    {
      "comparison_sha256": "0b4add6649d1b3abc54c64e9b15bb10b311037182f20b23869ed87c778b92ec3",
      "decision_sha256": "1edd180963de73a609c044207adb8965fb15c7fa72bebc9ce932fe37dc406a64",
      "operator_class": "broadcast",
      "performance_sha256": "ed5514a48f97610775e5e2daf75bcd5d91377846f603935f21b42af796cd2dd4",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "05f852b134cef318f78a710c7dac184a23b04a8ca22e695d60a91dbd771329fc",
      "verify_sha256": "50a2be41f004fdf481fdcae24e19aa710b0e1a02d821cfe483b57fb7b7866255"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "per-slice-dispatch-overhead",
      "carrier-volume",
      "broadcast-staging"
    ],
    "dtypes": [
      "int16",
      "int32",
      "int64"
    ],
    "pattern": "whole-kernel-simt-direct-gm-second-dataflow",
    "structure": [
      "simt-vf",
      "host-size-dtype-gate",
      "entry-branch-before-ub-init",
      "one-vf-call-per-core",
      "gm-direct-io",
      "per-thread-broadcast-decompose"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-SIMT-WHOLE-KERNEL-DIRECT-GM",
  "implementation_steps": [
    "从参考实现逐字提取 per-thread 二进制 GCD 体（含退化早退与符号处理），包成 __simt_vf__ LAUNCH_BOUND 体，TW 计算域按 dtype 选择",
    "host tiling 加 size+dtype 门控（dtype 白名单 + totalNum 下限 + 维数上限 + int32 索引域上限）置 useSimt",
    "kernel 入口在 TQue/UB 初始化之前分叉进 SimtDirectGm::Process，每核一次 Simt::VF_CALL，thread-stride 循环覆盖 dataCount",
    "每线程 x2 偏移按 BCT 三分派（SAME/SCALAR 提升/GENERAL decompose，stride-0 维短路）",
    "gate 排除的原路径逐字节不动，作 control 验证编辑作用域；verify 全量 golden 后按 run 阈值测增量"
  ],
  "intent": "消除逐 slice 载体的三重税：B1 每-slice TQue/UB 流量与队列编排、B2 每-slice asc_vf_call 分发 + PIPE_V 屏障地板、B3 broadcast 分级 staging（V-A/period-tile 组装），把 VEC_BOUND 整数路由的每元素指令数换成参考 per-thread 载体。",
  "mechanism": "host：gcd_tiling.cpp 门控四条件（dtype 白名单、totalNum>=1.0M、outDimNum<=8、totalNum<=INT32_MAX）置 useSimt；kernel：gcd_kernel.cpp 入口在 InitBuffer/TQue 之前 if(useSimt) 分叉进 SimtDirectGm::Process，每核一次 Simt::VF_CALL；op_kernel/gcd_simt.h 提供 __simt_vf__ __aicore__ LAUNCH_BOUND(1024/512) 的 GcdSimtKernel/GcdSimtKernelInt64：thread loop `for(i=GetThreadIdx(); i<dataCount; i+=GetThreadNum())`，逐线程 x2 偏移按 BCT 分派（SAME→i；SCALAR→0 提升；GENERAL→在 outDims[8]/x2DimStrides[8] 上 decompose，broadcast 维 stride=0 短路），int64 体用 union 32-bit-halves __builtin_ffs（高字 +32）取尾零。VF 体逐字取自参考实现 per-thread GCD。",
  "name": "size/dtype 门控的整核 SIMT direct-GM 载体（入口早分叉 + 每核一次 VF_CALL + GM 直达读写）",
  "operator_class": "broadcast",
  "operator_scope": "VEC_BOUND 整数 broadcast-elementwise kernel 的整核数据流替换段：逐 slice TQue/UB 载体 → host tiling 门控的 SimtDirectGm 第二数据流（int16/int32/int64 dtype 模板）",
  "principle": "(1) ascend950/A5 的 asc_vf_call 单次解引用 UB 足迹上限（8192B→507035）与每-slice 分发成本地板都只约束『经过 UB 的访问形态』；让 VF 体直接解引用 GM 指针则两个限制同时消失——负向卡 simt-vf-carrier-per-tile-footprint-bound 否定的是 per-tile/per-256-slice 形态而非载体本身，本卡给出可行形态。(2) 每核一次 VF_CALL 把分发成本摊到整核元素域，per-thread 收敛效率（数据相关早退）才转化为 wall-time。(3) 门控必须 size+dtype 双条件：小 case 留在 VEC（门控过宽回归，见 simt-direct-gm-size-gate-regression），dtype 决定每线程体与 wave 宽度（int64 用 512 wave）。",
  "related_anti_patterns": [],
  "risks": [
    "入口分叉点若落在 InitBuffer 之后，TQue/UB 初始化税仍在，收益被吞",
    "门控过宽（小 case 进 SIMT）会在 VEC 占优 regime 回归；过窄丢大 case 增益",
    "GENERAL decompose 的每元素整除/取模成本会侵蚀收益：int64 臂需配合 offset 算术节食（simt-int64-offset-arithmetic-diet）；同款节食的 prologue 状态在 1024-lane 臂会寄存器溢出（本 run r003 负向边界，knowledge/anti-pattern-r003.json：4 目标全回归，canary 0.722x）",
    "新增纯增量代码会漂移 gate 排除路径的指令布局（TU-size 效应，本 run r004：+506 行使逐字节未改的 c18 回归 5.7%），rejected 形态的代码必须从最终形态中移除"
  ],
  "slug": "simt-whole-kernel-direct-gm-carrier",
  "summary": "在 host tiling 用 size+dtype 门控（totalNum>=1.0M、outDimNum<=8、totalNum<=INT32_MAX、dtype ∈ {int16,int32,int64}）置 useSimt=1 时，kernel 入口在任何 TQue/UB 初始化之前分叉进 SimtDirectGm::Process：每核只发一次 Simt::VF_CALL（int16/int32 dim3(1024)、int64 dim3(512)），__simt_vf__ 体内逐线程执行参考实现的 per-thread 二进制 GCD（硬件 __builtin_ffs、逐元素收敛、a==0/b==0 退化早退），x1/x2/y 全部直接在 GM 读写；broadcast 偏移由每线程在既有 TilingData 表（outDims/x1DimStrides/x2DimStrides）上做 stride-0 短路 decompose。无 TQue、无 UB 窗口、无 per-slice 分发、无 V-A/period-tile 组装。gcd 上 20-case 增量 1.8637x（14 目标 2.06–4.95x、control 0.987–0.996）；最终官方分 62.64→70.01、官方口径累计 1.8991x、零回归。",
  "verification": {
    "correctness": [
      "gcd-20260902 r1：官方 verify 20/20 golden 全过（kernel_hash a4053ab5d00e878f 与 build/verify/performance 指纹一致）",
      "r2 扩展 int64 后再次 20/20；最终 final official_eval correctness 20/20"
    ],
    "performance": [
      "r1 增量 total 1.8637x（14 目标 case 2.06–4.95x，4 个 T3 control 0.987–0.996，阈值 0.95）",
      "r2 int64 扩展增量 1.2204x（6 目标 1.13–1.61x，7 control [0.9953,1.0078]）",
      "最终官方口径（official_eval per-case elapsed_us）：累计 1.8991x、20/20 case 全改善（1.16–4.53x）、regressed_cases=0；官方分 62.64→70.01（+7.37）"
    ],
    "rollback_signals": [
      "任一 gate 排除 control case 跌破 max_case_regression=0.95 → 编辑作用域泄漏，回退",
      "增量 < minimum_incremental_speedup=1.02 → 拒绝该轮",
      "verify 任一 golden 失败 → 立即回退父核"
    ]
  }
}
-->

# 性能优化策略：size/dtype 门控的整核 SIMT direct-GM 载体（入口早分叉 + 每核一次 VF_CALL + GM 直达读写）

单一优化点：在 host tiling 用 size+dtype 门控（totalNum>=1.0M、outDimNum<=8、totalNum<=INT32_MAX、dtype ∈ {int16,int32,int64}）置 useSimt=1 时，kernel 入口在任何 TQue/UB 初始化之前分叉进 SimtDirectGm::Process：每核只发一次 Simt::VF_CALL（int16/int32 dim3(1024)、int64 dim3(512)），__simt_vf__ 体内逐线程执行参考实现的 per-thread 二进制 GCD（硬件 __builtin_ffs、逐元素收敛、a==0/b==0 退化早退），x1/x2/y 全部直接在 GM 读写；broadcast 偏移由每线程在既有 TilingData 表（outDims/x1DimStrides/x2DimStrides）上做 stride-0 短路 decompose。无 TQue、无 UB 窗口、无 per-slice 分发、无 V-A/period-tile 组装。gcd 上 20-case 增量 1.8637x（14 目标 2.06–4.95x、control 0.987–0.996）；最终官方分 62.64→70.01、官方口径累计 1.8991x、零回归。

## 1. 原理

(1) ascend950/A5 的 asc_vf_call 单次解引用 UB 足迹上限（8192B→507035）与每-slice 分发成本地板都只约束『经过 UB 的访问形态』；让 VF 体直接解引用 GM 指针则两个限制同时消失——负向卡 simt-vf-carrier-per-tile-footprint-bound 否定的是 per-tile/per-256-slice 形态而非载体本身，本卡给出可行形态。(2) 每核一次 VF_CALL 把分发成本摊到整核元素域，per-thread 收敛效率（数据相关早退）才转化为 wall-time。(3) 门控必须 size+dtype 双条件：小 case 留在 VEC（门控过宽回归，见 simt-direct-gm-size-gate-regression），dtype 决定每线程体与 wave 宽度（int64 用 512 wave）。

实现机制：host：gcd_tiling.cpp 门控四条件（dtype 白名单、totalNum>=1.0M、outDimNum<=8、totalNum<=INT32_MAX）置 useSimt；kernel：gcd_kernel.cpp 入口在 InitBuffer/TQue 之前 if(useSimt) 分叉进 SimtDirectGm::Process，每核一次 Simt::VF_CALL；op_kernel/gcd_simt.h 提供 __simt_vf__ __aicore__ LAUNCH_BOUND(1024/512) 的 GcdSimtKernel/GcdSimtKernelInt64：thread loop `for(i=GetThreadIdx(); i<dataCount; i+=GetThreadNum())`，逐线程 x2 偏移按 BCT 分派（SAME→i；SCALAR→0 提升；GENERAL→在 outDims[8]/x2DimStrides[8] 上 decompose，broadcast 维 stride=0 短路），int64 体用 union 32-bit-halves __builtin_ffs（高字 +32）取尾零。VF 体逐字取自参考实现 per-thread GCD。

## 2. 性能问题模式

- 优化目标：消除逐 slice 载体的三重税：B1 每-slice TQue/UB 流量与队列编排、B2 每-slice asc_vf_call 分发 + PIPE_V 屏障地板、B3 broadcast 分级 staging（V-A/period-tile 组装），把 VEC_BOUND 整数路由的每元素指令数换成参考 per-thread 载体。
- 适用数据流：VEC_BOUND 整数 broadcast-elementwise kernel 的整核数据流替换段：逐 slice TQue/UB 载体 → host tiling 门控的 SimtDirectGm 第二数据流（int16/int32/int64 dtype 模板）
- Feature signature：`{"bottleneck": ["vec-bound", "per-slice-dispatch-overhead", "carrier-volume", "broadcast-staging"], "dtypes": ["int16", "int32", "int64"], "pattern": "whole-kernel-simt-direct-gm-second-dataflow", "structure": ["simt-vf", "host-size-dtype-gate", "entry-branch-before-ub-init", "one-vf-call-per-core", "gm-direct-io", "per-thread-broadcast-decompose"]}`

## 3. 正确性红线

- 入口分叉点若落在 InitBuffer 之后，TQue/UB 初始化税仍在，收益被吞
- 门控过宽（小 case 进 SIMT）会在 VEC 占优 regime 回归；过窄丢大 case 增益
- GENERAL decompose 的每元素整除/取模成本会侵蚀收益：int64 臂需配合 offset 算术节食（simt-int64-offset-arithmetic-diet）；同款节食的 prologue 状态在 1024-lane 臂会寄存器溢出（本 run r003 负向边界，knowledge/anti-pattern-r003.json：4 目标全回归，canary 0.722x）
- 新增纯增量代码会漂移 gate 排除路径的指令布局（TU-size 效应，本 run r004：+506 行使逐字节未改的 c18 回归 5.7%），rejected 形态的代码必须从最终形态中移除

资源与硬件约束：

- GM 直达读写意味着无 UB 缓存效应：小热 operand 的窗口化 staging 只有均匀索引（每核连续行窗口）或 by-value 标量形态可行，decompose 驱动的随机索引 UB gather 会被 bank-stall 证伪（本 run r004 负向边界，knowledge/anti-pattern-r004.json）
- 保留原 VEC 全路径逐字节不变作为 gate 排除 case 的结构与性能控制（control 带 [0.97,1.03]）
- int64 用 dim3(512) wave（参考实现 int64 wave），与 int16/int32 的 dim3(1024) 分开实例化

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- VEC_BOUND 的整数同/broadcast-shape elementwise 路由，瓶颈是每元素向量指令数或每-slice 载体开销
- 存在可逐字移植的参考 per-thread 载体（硬件 ctz/ffs、逐元素精确收敛、退化早退），且 arch35 __simt_vf__ 可编译
- host tiling 能在 dtype 已知处做 size+dtype 门控，把小 case 留在原 VEC 路径
- broadcast 偏移可由每线程在既有 tiling 表上 stride-0 短路 decompose（维数<=表宽）

不适用：

- 不得带任何 UB/TQue 窗口形态混入 SIMT 分支：入口分叉点必须在 InitBuffer 之前，否则回到足迹/分发税
- 门控不得只按 size 不按 dtype（dtype 决定 wave 宽度与每线程体；见 simt-direct-gm-size-gate-regression 与 simt-direct-gm-dtype-aware-gate）
- outDimNum 超过 decompose 表宽（8）或 totalNum 超过 int32 索引域时不得启用
- fp 类 dtype 在本证据域内未验证（整数角点/收敛域是本载体正确性前提）

## 5. 实施步骤

1. 从参考实现逐字提取 per-thread 二进制 GCD 体（含退化早退与符号处理），包成 __simt_vf__ LAUNCH_BOUND 体，TW 计算域按 dtype 选择
2. host tiling 加 size+dtype 门控（dtype 白名单 + totalNum 下限 + 维数上限 + int32 索引域上限）置 useSimt
3. kernel 入口在 TQue/UB 初始化之前分叉进 SimtDirectGm::Process，每核一次 Simt::VF_CALL，thread-stride 循环覆盖 dataCount
4. 每线程 x2 偏移按 BCT 三分派（SAME/SCALAR 提升/GENERAL decompose，stride-0 维短路）
5. gate 排除的原路径逐字节不动，作 control 验证编辑作用域；verify 全量 golden 后按 run 阈值测增量

## 6. LLM 前置问题

- 目标实现是否满足：VEC_BOUND 的整数同/broadcast-shape elementwise 路由，瓶颈是每元素向量指令数或每-slice 载体开销？
- 目标实现是否满足：存在可逐字移植的参考 per-thread 载体（硬件 ctz/ffs、逐元素精确收敛、退化早退），且 arch35 __simt_vf__ 可编译？
- 目标实现是否满足：host tiling 能在 dtype 已知处做 size+dtype 门控，把小 case 留在原 VEC 路径？
- 是否命中排除条件：不得带任何 UB/TQue 窗口形态混入 SIMT 分支：入口分叉点必须在 InitBuffer 之前，否则回到足迹/分发税？

## 7. 验收标准

正确性：

- gcd-20260902 r1：官方 verify 20/20 golden 全过（kernel_hash a4053ab5d00e878f 与 build/verify/performance 指纹一致）
- r2 扩展 int64 后再次 20/20；最终 final official_eval correctness 20/20

性能：

- r1 增量 total 1.8637x（14 目标 case 2.06–4.95x，4 个 T3 control 0.987–0.996，阈值 0.95）
- r2 int64 扩展增量 1.2204x（6 目标 1.13–1.61x，7 control [0.9953,1.0078]）
- 最终官方口径（official_eval per-case elapsed_us）：累计 1.8991x、20/20 case 全改善（1.16–4.53x）、regressed_cases=0；官方分 62.64→70.01（+7.37）

回滚信号：

- 任一 gate 排除 control case 跌破 max_case_regression=0.95 → 编辑作用域泄漏，回退
- 增量 < minimum_incremental_speedup=1.02 → 拒绝该轮
- verify 任一 golden 失败 → 立即回退父核

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260902_124740-96739f（round=1, status=accepted）
- gcd-20260902_124740-96739f（round=1, status=accepted）
- gcd-20260902_124740-96739f（round=2, status=accepted）
- gcd-20260902_124740-96739f（round=2, status=accepted）

## 检索卡（短卡）

动作：把逐 slice TQue/UB 载体改为 host size+dtype 门控的整核 SIMT direct-GM 数据流，入口在 UB 初始化前分叉、每核一次 VF_CALL。
适用：VEC_BOUND 整数 broadcast，totalNum>=1.0M 且 outDimNum<=8。
限制：门控须 size+dtype 双条件；入口分叉须在 InitBuffer 之前；不得混入 UB/TQue 窗口形态。
范围：VEC_BOUND 整数 broadcast kernel 的整核数据流替换
检索词：SimtDirectGm、VF_CALL、__simt_vf__、LAUNCH_BOUND、stride-0 短路 decompose
机会：逐 slice TQue/UB 流量、VF_CALL 分发与 PIPE_V 屏障地板三重税
代价：新增增量代码漂移未编辑路径指令布局（+506 行使 c18 回归 5.7%）
