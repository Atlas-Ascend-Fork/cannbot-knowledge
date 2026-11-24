---
type: Optimization
title: int64 数据门控的 int32 域窄快路径：|A|,|B|<2^31 的 slice 按 int32 视图执行已验证轮体，未过门 slice 走父版 int64 Div 路径
description: 以 slice 全量 |A|、|B|<2^31 为门，将计算从 int64 原生域转移到半宽 int32 轮体。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/int64-narrow-int32-domain-fastpath.md
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
      "门必须 abs 后计算（abs-with-wrap，INT64_MIN 回绕为负使算术 >>31 非零 -> 慢路径，与父版域语义一致）；假过门不可能（门为 0 <=> 全部 int64 高字为 0）",
      "int32 视图计数纪律：数据面 API 精确 2*cnt、Compare/Compares/Select 按 AlignUp(2*cnt,64) 掩码；尾 lane 只触碰私有 scratch（2*SIMD_SLICE int32 占满 g32Buf_ 不越界）",
      "奇数 lane (0,0) 语义（a==0 修复保持 (0,0)、B==0 吸收、P 回绕无害）需由 gcd(0,0) 等 case 验证",
      "慢路径（未过门）由源码级逐字等价 + 既有 20/20 覆盖；若要求运行时强制门验证需构造 |x|>=2^31 输入（超出常规 case 集编辑范围）",
      "host g32 项与 kernel g32Buf_ 注册门控必须同真同假（507015 UB 溢出防线）"
    ],
    "excluded_conditions": [
      "输入值域频繁超过 2^31 时快路径命中率低，机制退化为慢路径 + 每次 slice 一次门读回开销，不适用",
      "无法复用已验证 int32 轮体（无同算子 int32 实例/提升域）或 int64/int32 不共享模板时不适用",
      "int64 域轮体替换（而非数据域转移）不可行——B64 软件序列单价高，见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64",
      "非 VEC-bound route 不预期收益"
    ],
    "required_conditions": [
      "完整 msprof 显示 VEC 为唯一关键流水，且热链为 TW=int64 原生域的分块逐 lane 迭代（int64 宽度惩罚占主导）",
      "算子值域按输入分布经常落在 32 位以内（全部 |v|<2^31），使数据门在目标 case 集上基本恒真",
      "存在已验证的高效 int32 计算路径可复用（同算子 int32 实例或提升域实例），且 int64/int32 共享轮体模板",
      "数据门可向量化计算（abs 后 Or -> ShiftRights(31) -> EQ 0 -> Reduce）且与既有跨流水读回/早退通道同层（aicore 层，不在 __simd_vf__ 内引数据依赖分支）",
      "host 与 kernel 能对账新增 UB 预算（g32Buf_/simdWorkB twin），int32 视图写回 byte 偏移与 int64 CopyOut 逐字节重合"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "T3(3,6,9,13,17,20) target + int32(2,4,5,7,11,12,14,16,18) control",
      "operator_class": "broadcast",
      "round": 3,
      "run_id": "<run-id>",
      "speedup": "T3 8.3256x; int32 0.9992x; incremental 4.6497x; cumulative 5.5321x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "916ec9fc990192aaf924edb90a33bb0570fc883b8ccb4dcb905689d9c578ee00",
      "decision_sha256": "320c0b71e26f6726f0f6999e799a269ca25d8ba5d2a615ea69557c7592585784",
      "operator_class": "broadcast",
      "performance_sha256": "0094d79300afa85fd36f3ab972aed3f253f39c83b191a077bac270fc7bb91f7d",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "c0e406be9d353ce6e975bdc6de174bf1cab47dbbd4f8176ff6a708bb71f619bb",
      "verify_sha256": "6443e90da365d503d974c0139d71d64b47f81b886d4cf58bea5aa7edd858a5f0"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "fixed-round-loop",
      "int64-width-penalty",
      "software-emulated-b64"
    ],
    "dtypes": [
      "int64"
    ],
    "pattern": "data-domain-narrow-fastpath",
    "structure": [
      "vec-iterative-loop",
      "streaming-elementwise",
      "data-gate",
      "half-width-view",
      "ub-persistent-state"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH",
  "implementation_steps": [
    "确认 int64 宽度惩罚来自轮体寄存器序列而非数据；确认目标 case 值域全部 <2^31（数据门基本恒真）",
    "在 int64 臂 abs-init 循环后追加全 lane 值域门计算与一次 V->S 读回，保持父版循环体语句逐字不动",
    "把 int64 A/B 窗口按 int32 视图（reinterpret_cast，2x lane）接入已验证的 int32 轮体模板（normalize/chunk/final），复用既有 not-done 早退骨架",
    "host 侧为 DT_INT64 追加 g32 simdWorkB 项（与 kernel g32Buf_ 注册 twin），T1/T2 分支零改动",
    "全 all_cases verify（含 gcd(0,0)、非对齐 T3、T3 大值域）+ validation_cases frozen-tool 性能采集，按 T3 目标 / int32 控制拆分验收"
  ],
  "intent": "消除 int64 原生域的轮体宽度惩罚（每元素 128-250 cyc/el vs int32 域 15-57）：当数据值域远小于 64 位时，把计算转移到半宽度的 int32 轮体，而不是在 B64 上替换轮体（后者被证伪，见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64）。",
  "mechanism": "ComputeGcdAbsInit int64 臂在父版循环体末尾追加门计算（Or(|A|,|B|) -> ShiftRights(31) -> Compares EQ 0 -> Select -> Reduce SUM -> slice 级 gateSum），一次 TQueSync<PIPE_V,PIPE_S>+GetValue(0) 读回；gate==0 的快路径（ComputeGcdNarrowNormalize32/ComputeGcdNarrowChunkVF32/ComputeGcdNarrowFinal32）把 winX1/winX2 reinterpret 为 int32 视图（2*cnt lane，奇数 lane=(0,0)：a==0 修复保持 (0,0)、B==0 吸收不驱动额外 chunk、P 回绕为负但 Mul(0,P)=0 写回高字恰 0），复用轮 2 已验证的 GcdSteinNormalize<int32_t>/GcdSteinRounds<int32_t,8> 模板与既有 not-done 早退骨架（NARROW_MAX_CHUNKS=8）；gate!=0 的慢路径走父版 int64 chunk 循环 + ComputeGcdFinalVF 原样。g32Buf_ 仅 sizeof(TW)==8 注册（2*SIMD_SLICE*4B=2048B），host simdWorkB 对 DT_INT64 +2048B（twin 对账），T1/T2 实例编译期丢弃全部新代码；int32 视图写回的 byte 偏移与 parent int64 CopyOut 逐字节重合。",
  "name": "int64 数据门控的 int32 域窄快路径：|A|,|B|<2^31 的 slice 按 int32 视图执行已验证轮体，未过门 slice 走父版 int64 Div 路径",
  "operator_class": "broadcast",
  "operator_scope": "VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链为 TW=int64 原生域的分块逐 lane 迭代循环（如截断欧几里得 GCD），int64 轮体每元素成本远高于 int32（32 vs 64 lane、B64 软件序列），且算子值域按输入分布经常落在 32 位以内，存在已验证的高效 int32 轮体可复用",
  "principle": "int64 宽度惩罚绑定在 int64 寄存器指令序列（B64 软件 Div/移位）而非数据本身。若 slice 内所有 |A|,|B| 都 < 2^31，则 int64 元素高 32 位恒为 0，把窗口重解释为 int32（2x lane）后执行已验证的 int32 轮体，每元素成本降为 int32 域成本的一半利用率（64-lane int32 block 承载 32 个真实 int64 元素 = 2x int32 域 cyc/el，仍 ~10x 低于 int64 域）。数据门在 abs 后计算（|v|<2^31 => bit31 清 0，(|A|||B|)>>31==0；|v|>=2^31 => bit31 置位，INT64_MIN 保持负使算术 >>31 非 0），门为 0 恰表示全部 int64 高字为 0，快路径位精确；未过门 slice 走父版 Div 路径逐字。这是'数据域转移'而非'指令序列替换'，规避 B64 软件序列单价问题。",
  "related_anti_patterns": [],
  "risks": [
    "门计算/回读对慢路径无泄漏但多一次 TQueSync（无害重复同步），需确认不改变任何 A/B/y 数据面",
    "奇数 lane (0,0) 的 P=2^g 回绕为负 int32，依赖 Mul(0,P)=0 写回高字 0；改动 a==0 修复或 final 折回顺序会破坏该语义",
    "int32 视图 2x lane 的掩码/计数纪律出错导致尾 lane 越界或 done 计数错误",
    "强制门（|x|>=2^31）输入未在 round 内实测，慢路径依赖源码级逐字等价（边界已声明）",
    "门命中率在推广 case 集下降时，收益稀释为慢路径 + 门读回开销"
  ],
  "slug": "int64-narrow-int32-domain-fastpath",
  "summary": "对 TW=int64 计算域的每 slice，在 abs 后计算全 lane 值域门（|A|,|B| 全部 < 2^31）；过门 slice 把 int64 A/B 窗口按 int32 视图（2x lane，奇数 lane=高字恒 0）送入已验证的 int32 Stein 轮体与 P=2^g 折回，未过门 slice 逐功能走父版 int64 Div 截断欧几里得体（MAX_ROUNDS=93 原样）。把 int64 宽度惩罚转移到数据域而非在 B64 上替换轮体，实测 T3 目标域 8.3256x 聚合、int32 控制域 0.9992x（零泄漏）、增量 4.6497x、累计 5.5321x、零回归。",
  "verification": {
    "correctness": [
      "round 3 verify ok=true，20/20（run.json.all_cases），kernel 5e26142cfb36087a 与 build/verify/已安装 kernel/worktree 复核指纹一致",
      "T3 ±1e5 值域全部过门，int32 视图 normalize/P 折回/奇数 lane (0,0) 在真实数据上执行；非对齐 T3（case 6/17）验证 2x lane 计数纪律；gcd(0,0) 验证奇数 lane 吸收语义"
    ],
    "performance": [
      "T3 目标域（6 case）8.3256x 聚合（6.2559-10.9474x 每 case），aiv cyc/el 坍缩 250.2->23.0（case 3）、127.9->14.8（case 6）、197.5->22.9（case 9）、203.5->32.5（case 13）、197.8->23.0（case 17）、207.7->32.8（case 20）= 恰 2x int32 域 Stein 成本",
      "int32 控制域（9 case）0.9992x 聚合，cyc/el 复现轮 2 至 0.1-0.2 cyc/el（case 7 6.39 vs 6.4、case 5 19.66 vs 19.6）——零泄漏",
      "增量 compare 4.6497x、累计 5.5321x（minimum_final_cumulative_speedup=1.02），6 improved / 9 unchanged / 0 regression",
      "vec_ratio 下降与 scalar/mte2 ratio 上升为纯 composition 效应（绝对 scalar/mte2 时间持平或微升，vec 时间坍缩 8-10x）"
    ],
    "rollback_signals": [
      "任一 int32 控制 case 偏离轮 2 ±5%（scope 泄漏）",
      "任一 T3 case 慢于 parent 1.02x 或门命中率下降使收益消失",
      "任一 verify 位精确失败（尤其 gcd(0,0)/奇数 lane 语义）"
    ]
  }
}
-->

# 性能优化策略：int64 数据门控的 int32 域窄快路径：|A|,|B|<2^31 的 slice 按 int32 视图执行已验证轮体，未过门 slice 走父版 int64 Div 路径

单一优化点：对 TW=int64 计算域的每 slice，在 abs 后计算全 lane 值域门（|A|,|B| 全部 < 2^31）；过门 slice 把 int64 A/B 窗口按 int32 视图（2x lane，奇数 lane=高字恒 0）送入已验证的 int32 Stein 轮体与 P=2^g 折回，未过门 slice 逐功能走父版 int64 Div 截断欧几里得体（MAX_ROUNDS=93 原样）。把 int64 宽度惩罚转移到数据域而非在 B64 上替换轮体，实测 T3 目标域 8.3256x 聚合、int32 控制域 0.9992x（零泄漏）、增量 4.6497x、累计 5.5321x、零回归。

## 1. 原理

int64 宽度惩罚绑定在 int64 寄存器指令序列（B64 软件 Div/移位）而非数据本身。若 slice 内所有 |A|,|B| 都 < 2^31，则 int64 元素高 32 位恒为 0，把窗口重解释为 int32（2x lane）后执行已验证的 int32 轮体，每元素成本降为 int32 域成本的一半利用率（64-lane int32 block 承载 32 个真实 int64 元素 = 2x int32 域 cyc/el，仍 ~10x 低于 int64 域）。数据门在 abs 后计算（|v|<2^31 => bit31 清 0，(|A|||B|)>>31==0；|v|>=2^31 => bit31 置位，INT64_MIN 保持负使算术 >>31 非 0），门为 0 恰表示全部 int64 高字为 0，快路径位精确；未过门 slice 走父版 Div 路径逐字。这是'数据域转移'而非'指令序列替换'，规避 B64 软件序列单价问题。

实现机制：ComputeGcdAbsInit int64 臂在父版循环体末尾追加门计算（Or(|A|,|B|) -> ShiftRights(31) -> Compares EQ 0 -> Select -> Reduce SUM -> slice 级 gateSum），一次 TQueSync<PIPE_V,PIPE_S>+GetValue(0) 读回；gate==0 的快路径（ComputeGcdNarrowNormalize32/ComputeGcdNarrowChunkVF32/ComputeGcdNarrowFinal32）把 winX1/winX2 reinterpret 为 int32 视图（2*cnt lane，奇数 lane=(0,0)：a==0 修复保持 (0,0)、B==0 吸收不驱动额外 chunk、P 回绕为负但 Mul(0,P)=0 写回高字恰 0），复用轮 2 已验证的 GcdSteinNormalize<int32_t>/GcdSteinRounds<int32_t,8> 模板与既有 not-done 早退骨架（NARROW_MAX_CHUNKS=8）；gate!=0 的慢路径走父版 int64 chunk 循环 + ComputeGcdFinalVF 原样。g32Buf_ 仅 sizeof(TW)==8 注册（2*SIMD_SLICE*4B=2048B），host simdWorkB 对 DT_INT64 +2048B（twin 对账），T1/T2 实例编译期丢弃全部新代码；int32 视图写回的 byte 偏移与 parent int64 CopyOut 逐字节重合。

## 2. 性能问题模式

- 优化目标：消除 int64 原生域的轮体宽度惩罚（每元素 128-250 cyc/el vs int32 域 15-57）：当数据值域远小于 64 位时，把计算转移到半宽度的 int32 轮体，而不是在 B64 上替换轮体（后者被证伪，见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64）。
- 适用数据流：VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链为 TW=int64 原生域的分块逐 lane 迭代循环（如截断欧几里得 GCD），int64 轮体每元素成本远高于 int32（32 vs 64 lane、B64 软件序列），且算子值域按输入分布经常落在 32 位以内，存在已验证的高效 int32 轮体可复用
- Feature signature：`{"bottleneck": ["vec-bound", "fixed-round-loop", "int64-width-penalty", "software-emulated-b64"], "dtypes": ["int64"], "pattern": "data-domain-narrow-fastpath", "structure": ["vec-iterative-loop", "streaming-elementwise", "data-gate", "half-width-view", "ub-persistent-state"]}`

## 3. 正确性红线

- 门计算/回读对慢路径无泄漏但多一次 TQueSync（无害重复同步），需确认不改变任何 A/B/y 数据面
- 奇数 lane (0,0) 的 P=2^g 回绕为负 int32，依赖 Mul(0,P)=0 写回高字 0；改动 a==0 修复或 final 折回顺序会破坏该语义
- int32 视图 2x lane 的掩码/计数纪律出错导致尾 lane 越界或 done 计数错误
- 强制门（|x|>=2^31）输入未在 round 内实测，慢路径依赖源码级逐字等价（边界已声明）
- 门命中率在推广 case 集下降时，收益稀释为慢路径 + 门读回开销

资源与硬件约束：

- 门必须 abs 后计算（abs-with-wrap，INT64_MIN 回绕为负使算术 >>31 非零 -> 慢路径，与父版域语义一致）；假过门不可能（门为 0 <=> 全部 int64 高字为 0）
- int32 视图计数纪律：数据面 API 精确 2*cnt、Compare/Compares/Select 按 AlignUp(2*cnt,64) 掩码；尾 lane 只触碰私有 scratch（2*SIMD_SLICE int32 占满 g32Buf_ 不越界）
- 奇数 lane (0,0) 语义（a==0 修复保持 (0,0)、B==0 吸收、P 回绕无害）需由 gcd(0,0) 等 case 验证
- 慢路径（未过门）由源码级逐字等价 + 既有 20/20 覆盖；若要求运行时强制门验证需构造 |x|>=2^31 输入（超出常规 case 集编辑范围）
- host g32 项与 kernel g32Buf_ 注册门控必须同真同假（507015 UB 溢出防线）

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- 完整 msprof 显示 VEC 为唯一关键流水，且热链为 TW=int64 原生域的分块逐 lane 迭代（int64 宽度惩罚占主导）
- 算子值域按输入分布经常落在 32 位以内（全部 |v|<2^31），使数据门在目标 case 集上基本恒真
- 存在已验证的高效 int32 计算路径可复用（同算子 int32 实例或提升域实例），且 int64/int32 共享轮体模板
- 数据门可向量化计算（abs 后 Or -> ShiftRights(31) -> EQ 0 -> Reduce）且与既有跨流水读回/早退通道同层（aicore 层，不在 __simd_vf__ 内引数据依赖分支）
- host 与 kernel 能对账新增 UB 预算（g32Buf_/simdWorkB twin），int32 视图写回 byte 偏移与 int64 CopyOut 逐字节重合

不适用：

- 输入值域频繁超过 2^31 时快路径命中率低，机制退化为慢路径 + 每次 slice 一次门读回开销，不适用
- 无法复用已验证 int32 轮体（无同算子 int32 实例/提升域）或 int64/int32 不共享模板时不适用
- int64 域轮体替换（而非数据域转移）不可行——B64 软件序列单价高，见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64
- 非 VEC-bound route 不预期收益

## 5. 实施步骤

1. 确认 int64 宽度惩罚来自轮体寄存器序列而非数据；确认目标 case 值域全部 <2^31（数据门基本恒真）
2. 在 int64 臂 abs-init 循环后追加全 lane 值域门计算与一次 V->S 读回，保持父版循环体语句逐字不动
3. 把 int64 A/B 窗口按 int32 视图（reinterpret_cast，2x lane）接入已验证的 int32 轮体模板（normalize/chunk/final），复用既有 not-done 早退骨架
4. host 侧为 DT_INT64 追加 g32 simdWorkB 项（与 kernel g32Buf_ 注册 twin），T1/T2 分支零改动
5. 全 all_cases verify（含 gcd(0,0)、非对齐 T3、T3 大值域）+ validation_cases frozen-tool 性能采集，按 T3 目标 / int32 控制拆分验收

## 6. LLM 前置问题

- 目标实现是否满足：完整 msprof 显示 VEC 为唯一关键流水，且热链为 TW=int64 原生域的分块逐 lane 迭代（int64 宽度惩罚占主导）？
- 目标实现是否满足：算子值域按输入分布经常落在 32 位以内（全部 |v|<2^31），使数据门在目标 case 集上基本恒真？
- 目标实现是否满足：存在已验证的高效 int32 计算路径可复用（同算子 int32 实例或提升域实例），且 int64/int32 共享轮体模板？
- 是否命中排除条件：输入值域频繁超过 2^31 时快路径命中率低，机制退化为慢路径 + 每次 slice 一次门读回开销，不适用？

## 7. 验收标准

正确性：

- round 3 verify ok=true，20/20（run.json.all_cases），kernel 5e26142cfb36087a 与 build/verify/已安装 kernel/worktree 复核指纹一致
- T3 ±1e5 值域全部过门，int32 视图 normalize/P 折回/奇数 lane (0,0) 在真实数据上执行；非对齐 T3（case 6/17）验证 2x lane 计数纪律；gcd(0,0) 验证奇数 lane 吸收语义

性能：

- T3 目标域（6 case）8.3256x 聚合（6.2559-10.9474x 每 case），aiv cyc/el 坍缩 250.2->23.0（case 3）、127.9->14.8（case 6）、197.5->22.9（case 9）、203.5->32.5（case 13）、197.8->23.0（case 17）、207.7->32.8（case 20）= 恰 2x int32 域 Stein 成本
- int32 控制域（9 case）0.9992x 聚合，cyc/el 复现轮 2 至 0.1-0.2 cyc/el（case 7 6.39 vs 6.4、case 5 19.66 vs 19.6）——零泄漏
- 增量 compare 4.6497x、累计 5.5321x（minimum_final_cumulative_speedup=1.02），6 improved / 9 unchanged / 0 regression
- vec_ratio 下降与 scalar/mte2 ratio 上升为纯 composition 效应（绝对 scalar/mte2 时间持平或微升，vec 时间坍缩 8-10x）

回滚信号：

- 任一 int32 控制 case 偏离轮 2 ±5%（scope 泄漏）
- 任一 T3 case 慢于 parent 1.02x 或门命中率下降使收益消失
- 任一 verify 位精确失败（尤其 gcd(0,0)/奇数 lane 语义）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260826_015717-b0d16d（round=3, status=accepted, case=T3(3,6,9,13,17,20) target + int32(2,4,5,7,11,12,14,16,18) control, speedup=T3 8.3256x; int32 0.9992x; incremental 4.6497x; cumulative 5.5321x）
- gcd-20260826_015717-b0d16d（round=3, status=accepted）

## 检索卡（短卡）

动作：以 slice 全量 |A|、|B|<2^31 为门，将计算从 int64 原生域转移到半宽 int32 轮体
适用：int64逐lane热链受宽域指令主导，可对全slice的|A|、|B|<2^31采用数据门快路径
限制：abs-with-wrap后门控并核验INT64_MIN边界；全slice |A|、|B|<2^31，A/B/y不变
范围：elementwise-arithmetic 的 int64 分块逐 lane 迭代
检索词：int64 原生域、int32 轮体、值域门、B64 软件 Div/移位、TQueSync
机会：瓶颈来自 int64 寄存器指令序列中的 B64 软件 Div/移位，而非数据本身
代价：门计算与回读会多一次 TQueSync
