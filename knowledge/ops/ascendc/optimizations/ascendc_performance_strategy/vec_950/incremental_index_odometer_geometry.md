---
type: Optimization
title: 行几何里程计：寄存器进位计数器 + 闭式区间计数替代每行重算
description: 把每行从行号反解的 (plane,d,h) 改为寄存器进位计数器（h++/d++/plane++），并把 CountRange 枚举换成闭式一对 clamp。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/incremental-index-odometer-geometry.md
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
      "里程计必须落在寄存器态（h++/d++/plane++ 进位计数器 + imul 派生 dBase/hBase）：本 run round_01 用 64x24B 栈上表实现（含 fill 预扫）实测回退（duration 0.9502x screening），依赖载入延迟与 MTE2 前串行化吃掉了削减下来的发射槽位；只有 round_02 的寄存器形式兑现收益",
      "增量分解出的 (plane,d,h) 序列必须与逐行 RowGeom(rowStart_) 重算逐值一致，且 copy-in / compute / copy-out 三条行循环共享同一里程计推进序列，不得只改其中一条",
      "CountInterval 必须与原 CountRange 符号等价（#{i in [0,k): lo <= base+i < hi} 化为一对 clamp），numDH 保留原 float clamp 语义（<=0 -> 1.0f），只把重算位置从 per-(row,chunk) 提到 per-row",
      "VF 体（AccumulateRowsHoisted）、同步结构、cast 回退路径必须原样不动，收益归因只能落在标量几何计算上"
    ],
    "excluded_conditions": [
      "每核处理的行不是连续区间时不适用：里程计依赖 rowStart_ = coreIdx * blockRows 的连续块，否则 (plane,d,h) 无法用进位计数器维护",
      "原实现已经不在每行重算几何（几何已 hoist 或每核只跑一行）时没有可消除对象",
      "运行时取模/整除已由 host 静态判定为恒等而被消去的算子不在本机制作用域内（那是 host-gated-cheap-path 的域）；本机制针对的是每行真实执行、且被多条循环重复计算的整数几何"
    ],
    "required_conditions": [
      "每核行区间连续（本 run rowStart_ = coreIdx * blockRows），(plane,d,h) 可由 h++ 回绕到 d++、d++ 回绕到 plane++ 维护",
      "存在多条 per-row 循环各自独立重算同一几何：本 run ProcessRows 的 copy-in 循环（L595-632）、compute 循环（L694-702）、copy-out 循环（L707-716）各调一次 RowGeom，合计每输出行 6 次运行期 u32 除法",
      "tap 窗口枚举与 per-(row,chunk) 的 numDV/numHV/numDH 重推可被闭式区间计数替代（kD*kH 窗口推导原本每行跑两次：copy-in 循环 + CountValidTaps）",
      "标量管道是该算子的节拍源：本 run 冻结 champion 的 sca/dur = 0.826/0.935/0.890，且 direction_001 削减 vec 43-46% 时标量持平（bf16 22.56->23.39us、fp16 38.29->39.60us），证明时间由 per-row 整数/控制工作决定而非 VF 发射"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "avgpool3d",
      "operator_class": "pool3d",
      "precision": "18/20 PASS（baseline-parity 签名，失败集 {11,12} bad=0 为 pre-existing inf-overflow comparator 限制；v1/v2 全部 20 case 的 MERE/MARE 与冻结基线逐字节相同）",
      "rounds": 2,
      "run_id": "<run-id>",
      "speedup": 1.1369,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-pipe-paced",
      "per-row-runtime-u32-division",
      "duplicated-tap-window-enumeration",
      "per-row-chunk-count-re-derivation"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "incremental-index-odometer-geometry",
    "reduce_mode": "avg-pool",
    "structure": [
      "register-odometer-carry-counter",
      "closed-form-interval-count",
      "single-geometry-shared-across-row-loops",
      "bitwise-identical-output",
      "no-runtime-gate"
    ]
  },
  "generality": "op_class",
  "id": "POOL3D-INCREMENTAL-INDEX-ODOMETER",
  "implementation_steps": [
    "在 kernel 中新增 curPlane_/curD_/curH_ 成员，Init 期用 RowGeom(rowStart_) 播种一次（每核每 kernel 2 次除法，替代原先每行 6 次）",
    "ProcessRows 的每条行循环各持自己的里程计推进（h++ 到 Hout 回绕 -> d++ 到 Dout 回绕 -> plane++），copy-out 循环把推进后的状态写回，使四条循环看到同一个 (plane,d,h) 序列",
    "用 CountInterval（原 CountRange 的闭式：一对 clamp 求 #{i in [0,k): lo <= base+i < hi}）每行计价一次 numDV/numHV，以及 count_include_pad 感知的 numD/numH（边界 [-pD,D+pD)/[-pH,H+pH)）",
    "把 numDH 从 per-(row,chunk) 重推改为 per-row 一次（保留原 float clamp：<=0 -> 1.0f）；dBase/hBase 改为按 sH/sD 走 imul 派生，删除 countVar 路径内的 dLo/dHi/hLo/hHi + CountRange x2 重推",
    "ComputeRow 签名收敛为 (inLocal, outLocal, numRows, numDH)，删除 CountValidTaps 与 CountRange，RowGeom 只保留在 Init；dBase/hBase 交给里程计",
    "以 bitwise 输出的精度证据（20 个 case 的 MERE/MARE 与冻结基线逐字节相同）与标量管道忙时下降（aiv_scalar -18..-28%）验收，而不是只看 duration"
  ],
  "intent": "消除 champion 中每输出行重复付出的整数几何成本：三条 per-row 循环各自调用的 2 次运行期 u32 除法（合计每行 6 次）、每行跑两次的 kD*kH tap 窗口枚举、以及 per-(row,chunk) 的 numDV/numHV/numDH 重推；这些工作全部落在 pacing 的标量管道上，是 duration 的真实节拍源。",
  "mechanism": "incremental-index-odometer-geometry 两个分量：(a) 寄存器态行几何里程计——每核行区间连续，故 (plane,d,h) 可由进位计数器（h++ 到 Hout 回绕触发 d++、d++ 到 Dout 回绕触发 plane++）维护，Init 期用 RowGeom(rowStart_) 播种一次，dBase/hBase 由 sH/sD 经 imul 派生，三条行循环各持自己的里程计并把推进后的状态写回，使四条循环共享同一序列；(b) 闭式 tap 区间计数——CountRange 枚举循环替换为 CountInterval 一对 clamp，每行计价一次 numDV/numHV 与 count_include_pad 感知的 numD/numH，numDH 也提到 per-row（保留原 float clamp）。无运行期门控，对全部 dtype 与形状生效；正确性由 bitwise 等价保证（同 slot 布局、gather 索引、掩码、tap 访问顺序与除数值）。实现形态是成败关键：round_01 的栈上表（64x24B + fill 预扫）虽然把 aiv_scalar busy 削了 15-21%（case1 168.52->134.68us、case3 73.97->56.31us），但 duration 回退到 0.9502x，因为依赖载入延迟与首个 MTE2 拷贝前的串行化代价超过省下的发射槽位；revert 后 round_02 完全用寄存器实现同一机制，screening 1.0989x 且无 dtype 回退。",
  "name": "行几何里程计：寄存器进位计数器 + 闭式区间计数替代每行重算",
  "operator_class": "pool3d",
  "operator_scope": "每核处理连续行区间、且多条 per-row 循环各自重算同一整数几何（运行期 u32 除法、tap 窗口枚举、per-row-chunk 计数重推）的池化/滑窗类算子，标量管道为节拍源的场景",
  "principle": "当标量管道是 pacing pipe 时，duration 由每行的整数/控制工作决定而非 VF 发射：本 run direction_001 把 vec 削减 43-46% 而标量持平（bf16 22.56->23.39us、fp16 38.29->39.60us），说明时间在别处。行索引 (plane,d,h) 本质是一个以 Hout/Dout 为基的混合基计数器，核内行连续使它可以状态化（进位）而不是每行从行号反解（除法）；tap 窗口与有效 tap 计数是区间求交，闭式一对 clamp 等价于整段枚举。两者都把 per-row 的除法与循环换成常量级寄存器操作，直接减少标量管道的发射槽位。",
  "related_anti_patterns": [
    "flat-zone-coordinate-hoist-load-latency-bound"
  ],
  "risks": [
    "实现形态决定成败：栈上表形态（round_01 v1）实测回退——aiv_scalar busy -15..-21% 却 duration 0.9502x，per-row 依赖载入 + MTE2 前串行化是失败原因；必须用寄存器形式（round_02 v2，screening 1.0989x）",
    "三条行循环共享同一里程计是隐式契约：任何一条漏改/改错推进序列都会导致行错位或越界，且只在部分 shape 上显形；须以逐 case MERE/MARE 与冻结基线逐字节相同作为验收证据（本 run 20/20 case 逐字节相同）",
    "精度门是 baseline-parity 签名而非全通过：18/20 且失败集 {11,12} bad=0（pre-existing inf-overflow comparator 限制，pre-loop original 与所有 loop 基线同样如此），不得把 18/20 当作回归，也不得把该失败集当作本机制引入",
    "收益依赖标量管道为节拍源，且行必须连续：换到 VF/MTE 主导的形状或每核只跑一行时无可消除对象",
    "nDH 的 float clamp 语义（<=0 -> 1.0f）与 count_include_pad 的边界（[-pD,D+pD)/[-pH,H+pH)）若在闭式改造中被简化，只会在 padding 边界 case 上出错"
  ],
  "slug": "incremental-index-odometer-geometry",
  "summary": "avgpool3d 的 champion 由 aiv_scalar 管道节拍（sca/dur 0.826-0.935），其时间来自每行的整数几何：三条 per-row 循环各调 RowGeom（每行 6 次运行期 u32 除法）、kD*kH tap 窗口每行枚举两次、countVar 路径 per-(row,chunk) 重推 CountRange x2 + numDH。改为寄存器态里程计（Init 期播种一次，h++/d++/plane++ 进位，dBase/hBase 走 imul）三条行循环共享同一序列，并把 CountRange 枚举换成闭式 CountInterval 一对 clamp（numDV/numHV/numDH 均提到 per-row）。msprof device Task Duration geomean 30.025 -> 26.408us（1.1369x；fp16 1.222x、fp32 1.138x、bf16 1.057x），aiv_scalar busy -18..-28%，20 个 case 的 MERE/MARE 与冻结基线逐字节相同。",
  "verification": {
    "correctness": [
      "精度为 baseline-parity 签名：18/20 PASS，失败集 {11,12} bad=0，与 pre-loop original 及全部 loop 基线一致（pre-existing inf-overflow comparator 限制）",
      "v1 与 v2 在全部 20 个 case 上的 per-case MERE/MARE 与冻结基线逐字节相同 -> 输出位级一致；同 slot 布局、gather 索引、掩码、tap 访问顺序与除数值均未变",
      "CountInterval 与 CountRange 在符号上等价，并经 20 个 case 的经验验证"
    ],
    "performance": [
      "形式化配对 1.1369x geomean（device Task Duration 30.025 -> 26.408us），三个 dtype 组均值在两对中均改善，对间 speedup 偏差 0.0009，顺序平衡 C1B1B2C2，provenance-clean 双树基线",
      "aiv_scalar busy 下降 18-28%（组级），与预测的 25-45% 标量削减方向一致（预测值偏乐观）",
      "round_01 栈上表形态的对照已归档：aiv_scalar -15..-21% 但 duration 0.9502x，证明收益归因于寄存器形态而非表形态"
    ],
    "rollback_signals": [
      "几何改走内存/表形态（per-row 依赖载入、MTE2 前串行化）导致 duration 回退——本 run round_01 已实证 0.9502x",
      "三条行循环的里程计序列不一致，在部分 shape 上出现行错位或越界",
      "任何 case 的 MERE/MARE 不再与冻结基线逐字节相同（说明分解不再等价）",
      "标量管道忙时未下降：说明消除的不是 pacing 工作，收益无法归因"
    ]
  }
}
-->

# 性能优化策略：行几何里程计：寄存器进位计数器 + 闭式区间计数替代每行重算

avgpool3d 的 champion 由 aiv_scalar 管道节拍（sca/dur 0.826-0.935），其时间来自每行的整数几何：三条 per-row 循环各调 RowGeom（每行 6 次运行期 u32 除法）、kD*kH tap 窗口每行枚举两次、countVar 路径 per-(row,chunk) 重推 CountRange x2 + numDH。改为寄存器态里程计（Init 期播种一次，h++/d++/plane++ 进位，dBase/hBase 走 imul）三条行循环共享同一序列，并把 CountRange 枚举换成闭式 CountInterval 一对 clamp（numDV/numHV/numDH 均提到 per-row）。msprof device Task Duration geomean 30.025 -> 26.408us（1.1369x；fp16 1.222x、fp32 1.138x、bf16 1.057x），aiv_scalar busy -18..-28%，20 个 case 的 MERE/MARE 与冻结基线逐字节相同。

## 1. 原理

当标量管道是 pacing pipe 时，duration 由每行的整数/控制工作决定而非 VF 发射：本 run direction_001 把 vec 削减 43-46% 而标量持平（bf16 22.56->23.39us、fp16 38.29->39.60us），说明时间在别处。行索引 (plane,d,h) 本质是一个以 Hout/Dout 为基的混合基计数器，核内行连续使它可以状态化（进位）而不是每行从行号反解（除法）；tap 窗口与有效 tap 计数是区间求交，闭式一对 clamp 等价于整段枚举。两者都把 per-row 的除法与循环换成常量级寄存器操作，直接减少标量管道的发射槽位。

实现机制：incremental-index-odometer-geometry 两个分量：(a) 寄存器态行几何里程计——每核行区间连续，故 (plane,d,h) 可由进位计数器（h++ 到 Hout 回绕触发 d++、d++ 到 Dout 回绕触发 plane++）维护，Init 期用 RowGeom(rowStart_) 播种一次，dBase/hBase 由 sH/sD 经 imul 派生，三条行循环各持自己的里程计并把推进后的状态写回，使四条循环共享同一序列；(b) 闭式 tap 区间计数——CountRange 枚举循环替换为 CountInterval 一对 clamp，每行计价一次 numDV/numHV 与 count_include_pad 感知的 numD/numH，numDH 也提到 per-row（保留原 float clamp）。无运行期门控，对全部 dtype 与形状生效；正确性由 bitwise 等价保证（同 slot 布局、gather 索引、掩码、tap 访问顺序与除数值）。实现形态是成败关键：round_01 的栈上表（64x24B + fill 预扫）虽然把 aiv_scalar busy 削了 15-21%（case1 168.52->134.68us、case3 73.97->56.31us），但 duration 回退到 0.9502x，因为依赖载入延迟与首个 MTE2 拷贝前的串行化代价超过省下的发射槽位；revert 后 round_02 完全用寄存器实现同一机制，screening 1.0989x 且无 dtype 回退。

## 2. 性能问题模式

- 优化目标：消除 champion 中每输出行重复付出的整数几何成本：三条 per-row 循环各自调用的 2 次运行期 u32 除法（合计每行 6 次）、每行跑两次的 kD*kH tap 窗口枚举、以及 per-(row,chunk) 的 numDV/numHV/numDH 重推；这些工作全部落在 pacing 的标量管道上，是 duration 的真实节拍源。
- 适用数据流：每核处理连续行区间、且多条 per-row 循环各自重算同一整数几何（运行期 u32 除法、tap 窗口枚举、per-row-chunk 计数重推）的池化/滑窗类算子，标量管道为节拍源的场景
- Feature signature：`{"bottleneck": ["scalar-pipe-paced", "per-row-runtime-u32-division", "duplicated-tap-window-enumeration", "per-row-chunk-count-re-derivation"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "incremental-index-odometer-geometry", "reduce_mode": "avg-pool", "structure": ["register-odometer-carry-counter", "closed-form-interval-count", "single-geometry-shared-across-row-loops", "bitwise-identical-output", "no-runtime-gate"]}`

## 3. 正确性红线

- 实现形态决定成败：栈上表形态（round_01 v1）实测回退——aiv_scalar busy -15..-21% 却 duration 0.9502x，per-row 依赖载入 + MTE2 前串行化是失败原因；必须用寄存器形式（round_02 v2，screening 1.0989x）
- 三条行循环共享同一里程计是隐式契约：任何一条漏改/改错推进序列都会导致行错位或越界，且只在部分 shape 上显形；须以逐 case MERE/MARE 与冻结基线逐字节相同作为验收证据（本 run 20/20 case 逐字节相同）
- 精度门是 baseline-parity 签名而非全通过：18/20 且失败集 {11,12} bad=0（pre-existing inf-overflow comparator 限制，pre-loop original 与所有 loop 基线同样如此），不得把 18/20 当作回归，也不得把该失败集当作本机制引入
- 收益依赖标量管道为节拍源，且行必须连续：换到 VF/MTE 主导的形状或每核只跑一行时无可消除对象
- nDH 的 float clamp 语义（<=0 -> 1.0f）与 count_include_pad 的边界（[-pD,D+pD)/[-pH,H+pH)）若在闭式改造中被简化，只会在 padding 边界 case 上出错

资源与硬件约束：

- 里程计必须落在寄存器态（h++/d++/plane++ 进位计数器 + imul 派生 dBase/hBase）：本 run round_01 用 64x24B 栈上表实现（含 fill 预扫）实测回退（duration 0.9502x screening），依赖载入延迟与 MTE2 前串行化吃掉了削减下来的发射槽位；只有 round_02 的寄存器形式兑现收益
- 增量分解出的 (plane,d,h) 序列必须与逐行 RowGeom(rowStart_) 重算逐值一致，且 copy-in / compute / copy-out 三条行循环共享同一里程计推进序列，不得只改其中一条
- CountInterval 必须与原 CountRange 符号等价（#{i in [0,k): lo <= base+i < hi} 化为一对 clamp），numDH 保留原 float clamp 语义（<=0 -> 1.0f），只把重算位置从 per-(row,chunk) 提到 per-row
- VF 体（AccumulateRowsHoisted）、同步结构、cast 回退路径必须原样不动，收益归因只能落在标量几何计算上

## 4. 泛化条件

- 策略作用域：op_class：pool3d

适用：

- 每核行区间连续（本 run rowStart_ = coreIdx * blockRows），(plane,d,h) 可由 h++ 回绕到 d++、d++ 回绕到 plane++ 维护
- 存在多条 per-row 循环各自独立重算同一几何：本 run ProcessRows 的 copy-in 循环（L595-632）、compute 循环（L694-702）、copy-out 循环（L707-716）各调一次 RowGeom，合计每输出行 6 次运行期 u32 除法
- tap 窗口枚举与 per-(row,chunk) 的 numDV/numHV/numDH 重推可被闭式区间计数替代（kD*kH 窗口推导原本每行跑两次：copy-in 循环 + CountValidTaps）
- 标量管道是该算子的节拍源：本 run 冻结 champion 的 sca/dur = 0.826/0.935/0.890，且 direction_001 削减 vec 43-46% 时标量持平（bf16 22.56->23.39us、fp16 38.29->39.60us），证明时间由 per-row 整数/控制工作决定而非 VF 发射

不适用：

- 每核处理的行不是连续区间时不适用：里程计依赖 rowStart_ = coreIdx * blockRows 的连续块，否则 (plane,d,h) 无法用进位计数器维护
- 原实现已经不在每行重算几何（几何已 hoist 或每核只跑一行）时没有可消除对象
- 运行时取模/整除已由 host 静态判定为恒等而被消去的算子不在本机制作用域内（那是 host-gated-cheap-path 的域）；本机制针对的是每行真实执行、且被多条循环重复计算的整数几何

## 5. 实施步骤

1. 在 kernel 中新增 curPlane_/curD_/curH_ 成员，Init 期用 RowGeom(rowStart_) 播种一次（每核每 kernel 2 次除法，替代原先每行 6 次）
2. ProcessRows 的每条行循环各持自己的里程计推进（h++ 到 Hout 回绕 -> d++ 到 Dout 回绕 -> plane++），copy-out 循环把推进后的状态写回，使四条循环看到同一个 (plane,d,h) 序列
3. 用 CountInterval（原 CountRange 的闭式：一对 clamp 求 #{i in [0,k): lo <= base+i < hi}）每行计价一次 numDV/numHV，以及 count_include_pad 感知的 numD/numH（边界 [-pD,D+pD)/[-pH,H+pH)）
4. 把 numDH 从 per-(row,chunk) 重推改为 per-row 一次（保留原 float clamp：<=0 -> 1.0f）；dBase/hBase 改为按 sH/sD 走 imul 派生，删除 countVar 路径内的 dLo/dHi/hLo/hHi + CountRange x2 重推
5. ComputeRow 签名收敛为 (inLocal, outLocal, numRows, numDH)，删除 CountValidTaps 与 CountRange，RowGeom 只保留在 Init；dBase/hBase 交给里程计
6. 以 bitwise 输出的精度证据（20 个 case 的 MERE/MARE 与冻结基线逐字节相同）与标量管道忙时下降（aiv_scalar -18..-28%）验收，而不是只看 duration

## 6. LLM 前置问题

- 目标实现是否满足：每核行区间连续（本 run rowStart_ = coreIdx * blockRows），(plane,d,h) 可由 h++ 回绕到 d++、d++ 回绕到 plane++ 维护？
- 目标实现是否满足：存在多条 per-row 循环各自独立重算同一几何（本 run 三条行循环各调 RowGeom，合计每输出行 6 次运行期 u32 除法）？
- 目标实现是否满足：tap 窗口枚举与 per-(row,chunk) 的 numDV/numHV/numDH 重推可被闭式区间计数替代？
- 目标实现是否满足：标量管道是该算子的节拍源（本 run sca/dur 0.826/0.935/0.890，vec 削减 43-46% 时标量持平）？
- 是否命中排除条件：每核处理的行不是连续区间时不适用（里程计依赖连续行块）？
- 是否命中排除条件：原实现已经不在每行重算几何（几何已 hoist 或每核只跑一行）时没有可消除对象？
- 是否命中排除条件：运行时取模/整除已由 host 静态消去（host-gated-cheap-path 域）时不在本机制作用域内？

## 7. 验收标准

正确性：

- 精度为 baseline-parity 签名：18/20 PASS，失败集 {11,12} bad=0，与 pre-loop original 及全部 loop 基线一致（pre-existing inf-overflow comparator 限制）
- v1 与 v2 在全部 20 个 case 上的 per-case MERE/MARE 与冻结基线逐字节相同 -> 输出位级一致；同 slot 布局、gather 索引、掩码、tap 访问顺序与除数值均未变
- CountInterval 与 CountRange 在符号上等价，并经 20 个 case 的经验验证

性能：

- 形式化配对 1.1369x geomean（device Task Duration 30.025 -> 26.408us），三个 dtype 组均值在两对中均改善，对间 speedup 偏差 0.0009，顺序平衡 C1B1B2C2，provenance-clean 双树基线
- aiv_scalar busy 下降 18-28%（组级），与预测的 25-45% 标量削减方向一致（预测值偏乐观）
- round_01 栈上表形态的对照已归档：aiv_scalar -15..-21% 但 duration 0.9502x，证明收益归因于寄存器形态而非表形态

回滚信号：

- 几何改走内存/表形态（per-row 依赖载入、MTE2 前串行化）导致 duration 回退——本 run round_01 已实证 0.9502x
- 三条行循环的里程计序列不一致，在部分 shape 上出现行错位或越界
- 任何 case 的 MERE/MARE 不再与冻结基线逐字节相同（说明分解不再等价）
- 标量管道忙时未下降：说明消除的不是 pacing 工作，收益无法归因

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：flat-zone-coordinate-hoist-load-latency-bound

- loop_20260913_124740（round=2, status=accepted, speedup=1.1369, precision=18/20 PASS baseline-parity，v1/v2 全 20 case 输出逐字节一致）

## 检索卡（短卡）

动作：把每行从行号反解的 (plane,d,h) 改为寄存器进位计数器（h++/d++/plane++），并把 CountRange 枚举换成闭式一对 clamp
适用：每核行区间连续，且多条 per-row 循环各自重算同一几何、标量管道为节拍源
限制：里程计须落在寄存器态（栈上表形态实测 0.9502x 回退）；三条行循环须共享同一推进序列；numDH 的 float clamp 语义不可简化
范围：pool3d 的池化/滑窗类算子 per-row 整数几何
检索词：进位计数器、CountInterval、RowGeom、dBase/hBase imul、sca/dur、tap 窗口枚举
机会：三条 per-row 循环各调 RowGeom（每行 6 次运行期 u32 除法），是标量管道的节拍源
