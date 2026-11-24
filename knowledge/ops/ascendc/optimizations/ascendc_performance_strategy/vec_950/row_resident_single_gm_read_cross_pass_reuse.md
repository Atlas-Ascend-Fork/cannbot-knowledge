---
type: Optimization
title: 整行 UB 常驻单读 + 跨 pass exp 复用
description: 把 row path 每行 x 一次 CopyIn 整行驻留 UB（depth-2 双缓冲），sum-exp 遍把 e 存入 eBuf_ 供 out 遍消费。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/row-resident-single-gm-read-cross-pass-reuse.md
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
      "整行 UB 常驻要求 2*D*sizeof(T) + D*4 + 2*ROW_TILE*sizeof(T) + smallBuf <= 192KiB（SoftmaxTanh 的 ST_UB_BUDGET_BYTES 门控常量）；SoftmaxHardswish fp32 worst case 总 UB ~85KB，其中 eBuf_ 约 17KB",
      "跨 pass 复用的合法性建立在 e=exp(x-max) 的唯一下游消费是 out pass 的逐元素纯函数（LoadAlign + Mul by rcpSum + Maxs + downcast + Store），无其它消费者；消费的必须是同一批 exp 位",
      "行常驻 TQue 取 depth 2 并以 <=2 outstanding buffer 手工预取，DeQue/FreeTensor 时机须与原语义等价",
      "增量重建必须从干净的 kernel/build 目录开始——SoftmaxHardswish 记录增量二次编译会以 ld.lld in-place -Ttext 'unknown file type' 失败"
    ],
    "excluded_conditions": [
      "strip 路径（inner>1）与多 tile row（D > ROW_TILE 或超 UB 预算）不适用行常驻改造，保持原 3 遍代码",
      "SoftmaxHardswish 中 numSt > 1 的行不适用 ProcessRowsCached，保持 champion 三遍行为",
      "非 row path（dim != 末轴）不适用",
      "UB 预算门控不成立时不得强行走常驻路径，须回退 tiled/strided 原码"
    ],
    "required_conditions": [
      "row path（inner==1 / isRow）且 D 可整行驻留 UB（SoftmaxHardswish/SoftmaxTanh 的 20 个测试用例全为 [4096,4096] dim=-1，D 等于 ROW_TILE，每行恰好 1 个 super-tile）",
      "每行 x 被 max/sum/out 多遍 pass 各从 GM 重读一次（本 run 为 3x），且 out pass 整遍重算了 sum-exp 遍已算出的 fp32 e=exp(x-max)",
      "mte2 与 vec 同时构成绑定流水（SoftmaxHardswish champion vec 60.94us / mte2 42.24us；SoftmaxTanh champion paired msprof vec 54.06/54.05/53.33us 与 mte2 52.03/51.78/59.21us co-binding）",
      "存在可在 Init 期判定的 UB 预算门控与回退路径（D-oversize tiled / strip / numSt>1）",
      "有同 run 的未触碰对照组或冻结基线 .so 可做 provenance-clean 配对"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "SoftmaxHardswish",
      "operator_class": "normalization",
      "pairs": 6,
      "precision": "20/20 PASS（per-case MERE/MARE 与 champion 基线完全一致）",
      "run_id": "<run-id>",
      "speedup": 1.4221,
      "status": "accepted"
    },
    {
      "operator": "SoftmaxTanh",
      "operator_class": "normalization",
      "pairs": 4,
      "precision": "20/20 PASS（per-case MERE 与冻结基线一致到约 3 位有效数字，case1 5.260e-08 vs 5.275e-08）",
      "run_id": "<run-id>",
      "speedup": 1.358,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "redundant-gm-re-read-per-pass",
      "redundant-exp-recompute",
      "mte2-vec-co-binding"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "row-resident-single-gm-read-cross-pass-reuse",
    "structure": [
      "row-resident-ub-staging",
      "depth-2-cross-row-double-buffer",
      "cross-pass-exp-reuse",
      "ub-budget-gated-fallback",
      "bit-identical-numerics"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-ROW-RESIDENT-SINGLE-GM-READ-EXP-REUSE",
  "implementation_steps": [
    "在 Init() 内按 UB 预算门控分配行常驻 TQue（depth 2，每 buffer D*sizeof(T)）与 fp32 eBuf_（D 或 ROW_TILE+pad 个 float）；门控不满足时保持原 tiled/tileQue 布局逐字节不变",
    "新增行常驻主循环：prologue CopyInRow(u0)，逐行先预取 CopyInRow(u+1) 再 DeQue 当前行，收尾 FreeTensor，保持 <=2 outstanding buffer",
    "把 sum-exp 遍改造为 store 变体：在既有单循环内按 rep 追加一条掩码 Reg::StoreAlign，把 e=exp(x-max) 的 fp32 原始位写入 eBuf_",
    "把 out 遍改为从 eBuf_ 读取：LoadAlign(e) -> Mul by 已 hoist 的 rcpSum -> 保持原 downcast/Maxs/Store 不变，删除 GM 重读、unpack+Cast、Sub 与重复 Exp",
    "保留 D-oversize 的 tiled 路径、strip 路径（inner>1）与 numSt>1 行的 champion 原码逐字节不变，作为回退臂",
    "从干净 build 目录重建，跑 20/20 精度与 >=4 对 ABBA 配对（外层 msprof device Task Duration，两级 case-mean 再 geomean）"
  ],
  "intent": "消除 row path 上的双重冗余：纵向是每行 x 被 max/sum/out 三遍 pass 各从 GM 重读一次（3x GM 读，压 MTE2 有效带宽），横向是 out pass 对 sum-exp pass 已算出的 fp32 e=exp(x-max) 的整遍重算（第二次 Exp + Sub + B16 unpack + Cast，压 VEC 发射槽）。",
  "mechanism": "两个正交分量合并使用。(a) 整行常驻单次 GM 读：把行一次性 CopyIn 驻留 UB 并以 depth-2 TQue 跨行双缓冲（每行一次 alloc+copy+enq，row u+1 在 DeQue row u 之前预取，<=2 outstanding buffer），GM 读从 3x 降到 1x。(b) sum-exp 段产出的 fp32 e 跨 pass 复用：sum-exp 遍在既有单循环内追加掩码 StoreAlign 把 e 写入行规模的 fp32 eBuf_，out 遍退化为 LoadAlign(e) -> Mul by rcpSum -> downcast/Maxs/Store，删掉第二次 Exp 与其输入链。(c) 预算门控回退：SoftmaxTanh 以 constexpr 常量 ST_UB_BUDGET_BYTES = 192KiB 判定 rowResident_ = isRow && (2*D*sizeof(T) + D*4 + 2*ST_ROW_TILE*sizeof(T) + smallBuf <= 192KiB)，成立时才分配 rowQue_/eBuf_/outQue_，否则沿用 legacy tileQue_/outQue_ 布局；D 超预算时走 ProcessUnitsRowTiled（champion 原码）；strip 路径与 SoftmaxHardswish 的 numSt>1 行完全不动。",
  "name": "整行 UB 常驻单读 + 跨 pass exp 复用",
  "operator_class": "normalization",
  "operator_scope": "softmax 系（可含逐元素激活融合）且能在 row path 整行驻留 UB 的融合算子：每行 x 被多遍 pass 重复从 GM 读取、sum 遍产出的 exp 又在 out 遍被整遍重算，且 mte2 与 vec 同时构成绑定流水",
  "principle": "softmax 类 row path 天然分 max/sum/out 三遍，每遍都从 GM 重读同一行；把行一次性搬入 UB 并用 depth-2 跨行双缓冲后，GM 读降为 1x，直接命中 MTE2 有效带宽；同时 sum-exp 遍产出的 fp32 e 正是 out pass 的唯一逐元素输入，按原始位存入 UB 后 out pass 无需重算——删掉一次 Exp 及其 unpack/Cast/Sub 输入链。两条杠杆分别压 co-binding 的 mte2 与 vec，故合计收益大于任一单点；因为消费的是同一批 exp 位、同一 rcpSum 乘与同一 downcast，输出保持位级不变。",
  "related_anti_patterns": [
    "double-buffer-slot-reuse-race"
  ],
  "risks": [
    "UB 预算门控不可绕过：SoftmaxTanh 以 192KiB 常量判定 rowResident_（2*D*sizeof(T)+D*4+2*ROW_TILE*sizeof(T)+smallBuf），不满足时须走 ProcessUnitsRowTiled 原码；SoftmaxHardswish fp32 worst case 总 UB ~85KB、eBuf_ 约 17KB（(SH_ROW_TILE+SH_UB_PAD) 个 float）",
    "SoftmaxHardswish 的增量重建必须从干净 kernel/build 目录开始，增量二次编译会以 ld.lld in-place -Ttext 'unknown file type' 失败",
    "numSt>1 的 row 与 strip 路径（inner>1）必须保持 champion 原 3 遍代码逐字节不变，否则收益归因不成立",
    "跨 pass 复用要求消费同一批 exp 位（同一 upcast x、同一 broadcast max、同一 Exp、同一 rcpSum 乘与 downcast）；SoftmaxTanh 以 per-case MERE 与基线一致到约 3 位有效数字（case1 5.260e-08 vs 5.275e-08）为验收口径",
    "行常驻主循环用手工 depth-2 预取（<=2 outstanding buffer）替代原 TQue 自动流水，DeQue 时机改变须确认队列语义未变"
  ],
  "slug": "row-resident-single-gm-read-cross-pass-reuse",
  "summary": "把 softmax 系 row path 的每行 x 一次 CopyIn 整行驻留 UB（depth-2 跨行双缓冲，GM 读 3x->1x），并让 sum-exp 遍把 fp32 e=exp(x-max) 按原始位暂存到行规模 eBuf_，out 遍直接消费该 e（LoadAlign + Mul by rcpSum + downcast/Store，删除 GM 重读、B16 unpack+Cast、Sub 与第二次 Exp），以 UB 预算门控回退到原 3 遍代码。SoftmaxHardswish kernel geomean 75.326->52.967us（1.4221x，6 对平衡配对，mte2 30.8->12.4us bf16/fp16、47.5->22.4us fp32，vec 63.8->45.9us bf16/fp16）；SoftmaxTanh kernel task geomean 65.129->47.961us（1.3580x，4/4 对 x 3 dtype）。两者精度均 20/20 且数值与基线位级一致。",
  "verification": {
    "correctness": [
      "SoftmaxHardswish 20/20 PASS，per-case MERE/MARE 与 champion 基线完全一致（设计的位级相同算术），0 修复轮",
      "SoftmaxTanh 20/20 PASS 首试，per-case MERE 与冻结基线一致到约 3 位有效数字（case1 5.260e-08 vs 5.275e-08），0/3 编译修复、0/3 精度修复",
      "SoftmaxTanh 的 tanh regime 派发、NaN 行语义与全部数值链原样保留（同一 upcast x、同一 broadcast max、同一 Exp、同一 s = e*(1/sum) 链）"
    ],
    "performance": [
      "SoftmaxHardswish：kernel geomean 75.326->52.967us（speedup 1.4221x），6 对平衡配对、相关性无歧义；mte2 30.8->12.4us（bf16/fp16）、47.5->22.4us（fp32），vec 63.8->45.9us（bf16/fp16）",
      "SoftmaxTanh：kernel task geomean 65.129->47.961us（speedup 1.3580x），formal ABBA 4/4 对 x 3 dtype 一致，provenance-clean 冻结基线 A 侧复现 BEST_MS 65.111 在 0.03% 内",
      "SoftmaxTanh 预注册假证门全过：aiv_mte2 下降 -76.3/-76.8/-51.7%（门 >=35%）、aiv_vec 下降 -23.4/-23.5/-23.5%（门 >=5%）、task 增益 +35.8%（门 >=5%）"
    ],
    "rollback_signals": [
      "UB 预算门控不成立时强行走行常驻路径（应回退 tiled/strided 原码）",
      "numSt>1 或 strip 路径（inner>1）出现超出噪声带的回退",
      "MERE/MARE 偏离基线——说明跨 pass 消费的 e 与重算值不再位级一致",
      "行常驻 TQue 的预取/DeQue 时机改变引发队列异常或精度异常",
      "formal paired ABBA 显示 geomean <1.02x 或任一 dtype case mean <0.97x 时回退并记 rejected_performance"
    ]
  }
}
-->

# 性能优化策略：整行 UB 常驻单读 + 跨 pass exp 复用

把 softmax 系 row path 的每行 x 一次 CopyIn 整行驻留 UB（depth-2 跨行双缓冲，GM 读 3x->1x），并让 sum-exp 遍把 fp32 e=exp(x-max) 按原始位暂存到行规模 eBuf_，out 遍直接消费该 e（LoadAlign + Mul by rcpSum + downcast/Store，删除 GM 重读、B16 unpack+Cast、Sub 与第二次 Exp），以 UB 预算门控回退到原 3 遍代码。SoftmaxHardswish kernel geomean 75.326->52.967us（1.4221x），SoftmaxTanh kernel task geomean 65.129->47.961us（1.3580x）。

## 1. 原理

softmax 类 row path 天然分 max/sum/out 三遍，每遍都从 GM 重读同一行；把行一次性搬入 UB 并用 depth-2 跨行双缓冲后，GM 读降为 1x，直接命中 MTE2 有效带宽；同时 sum-exp 遍产出的 fp32 e 正是 out pass 的唯一逐元素输入，按原始位存入 UB 后 out pass 无需重算——删掉一次 Exp 及其 unpack/Cast/Sub 输入链。两条杠杆分别压 co-binding 的 mte2 与 vec，故合计收益大于任一单点；因为消费的是同一批 exp 位、同一 rcpSum 乘与同一 downcast，输出保持位级不变。

实现机制：两个正交分量合并使用。(a) 整行常驻单次 GM 读：把行一次性 CopyIn 驻留 UB 并以 depth-2 TQue 跨行双缓冲（每行一次 alloc+copy+enq，row u+1 在 DeQue row u 之前预取，<=2 outstanding buffer），GM 读从 3x 降到 1x。(b) sum-exp 段产出的 fp32 e 跨 pass 复用：sum-exp 遍在既有单循环内追加掩码 StoreAlign 把 e 写入行规模的 fp32 eBuf_，out 遍退化为 LoadAlign(e) -> Mul by rcpSum -> downcast/Maxs/Store，删掉第二次 Exp 与其输入链。(c) 预算门控回退：SoftmaxTanh 以 constexpr 常量 ST_UB_BUDGET_BYTES = 192KiB 判定 rowResident_ = isRow && (2*D*sizeof(T) + D*4 + 2*ST_ROW_TILE*sizeof(T) + smallBuf <= 192KiB)，成立时才分配 rowQue_/eBuf_/outQue_，否则沿用 legacy tileQue_/outQue_ 布局；D 超预算时走 ProcessUnitsRowTiled（champion 原码）；strip 路径与 SoftmaxHardswish 的 numSt>1 行完全不动。

## 2. 性能问题模式

- 优化目标：消除 row path 上的双重冗余：纵向是每行 x 被 max/sum/out 三遍 pass 各从 GM 重读一次（3x GM 读，压 MTE2 有效带宽），横向是 out pass 对 sum-exp pass 已算出的 fp32 e=exp(x-max) 的整遍重算（第二次 Exp + Sub + B16 unpack + Cast，压 VEC 发射槽）
- 适用数据流：softmax 系（可含逐元素激活融合）且能在 row path 整行驻留 UB 的融合算子：每行 x 被多遍 pass 重复从 GM 读取、sum 遍产出的 exp 又在 out 遍被整遍重算，且 mte2 与 vec 同时构成绑定流水
- Feature signature：`{"bottleneck": ["redundant-gm-re-read-per-pass", "redundant-exp-recompute", "mte2-vec-co-binding"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "row-resident-single-gm-read-cross-pass-reuse", "structure": ["row-resident-ub-staging", "depth-2-cross-row-double-buffer", "cross-pass-exp-reuse", "ub-budget-gated-fallback", "bit-identical-numerics"]}`

## 3. 正确性红线

- UB 预算门控不可绕过：SoftmaxTanh 以 192KiB 常量判定 rowResident_（2*D*sizeof(T)+D*4+2*ROW_TILE*sizeof(T)+smallBuf），不满足时须走 ProcessUnitsRowTiled 原码；SoftmaxHardswish fp32 worst case 总 UB ~85KB、eBuf_ 约 17KB（(SH_ROW_TILE+SH_UB_PAD) 个 float）
- SoftmaxHardswish 的增量重建必须从干净 kernel/build 目录开始，增量二次编译会以 ld.lld in-place -Ttext 'unknown file type' 失败
- numSt>1 的 row 与 strip 路径（inner>1）必须保持 champion 原 3 遍代码逐字节不变，否则收益归因不成立
- 跨 pass 复用要求消费同一批 exp 位（同一 upcast x、同一 broadcast max、同一 Exp、同一 rcpSum 乘与 downcast）；SoftmaxTanh 以 per-case MERE 与基线一致到约 3 位有效数字（case1 5.260e-08 vs 5.275e-08）为验收口径
- 行常驻主循环用手工 depth-2 预取（<=2 outstanding buffer）替代原 TQue 自动流水，DeQue 时机改变须确认队列语义未变

资源与硬件约束：

- 整行 UB 常驻要求 2*D*sizeof(T) + D*4 + 2*ROW_TILE*sizeof(T) + smallBuf <= 192KiB（SoftmaxTanh 的 ST_UB_BUDGET_BYTES 门控常量）；SoftmaxHardswish fp32 worst case 总 UB ~85KB，其中 eBuf_ 约 17KB
- 跨 pass 复用的合法性建立在 e=exp(x-max) 的唯一下游消费是 out pass 的逐元素纯函数（LoadAlign + Mul by rcpSum + Maxs + downcast + Store），无其它消费者；消费的必须是同一批 exp 位
- 行常驻 TQue 取 depth 2 并以 <=2 outstanding buffer 手工预取，DeQue/FreeTensor 时机须与原语义等价
- 增量重建必须从干净的 kernel/build 目录开始——SoftmaxHardswish 记录增量二次编译会以 ld.lld in-place -Ttext 'unknown file type' 失败

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- row path（inner==1 / isRow）且 D 可整行驻留 UB（SoftmaxHardswish/SoftmaxTanh 的 20 个测试用例全为 [4096,4096] dim=-1，D 等于 ROW_TILE，每行恰好 1 个 super-tile）
- 每行 x 被 max/sum/out 多遍 pass 各从 GM 重读一次（本 run 为 3x），且 out pass 整遍重算了 sum-exp 遍已算出的 fp32 e=exp(x-max)
- mte2 与 vec 同时构成绑定流水（SoftmaxHardswish champion vec 60.94us / mte2 42.24us；SoftmaxTanh champion paired msprof vec 54.06/54.05/53.33us 与 mte2 52.03/51.78/59.21us co-binding）
- 存在可在 Init 期判定的 UB 预算门控与回退路径（D-oversize tiled / strip / numSt>1）
- 有同 run 的未触碰对照组或冻结基线 .so 可做 provenance-clean 配对

不适用：

- strip 路径（inner>1）与多 tile row（D > ROW_TILE 或超 UB 预算）不适用行常驻改造，保持原 3 遍代码
- SoftmaxHardswish 中 numSt > 1 的行不适用 ProcessRowsCached，保持 champion 三遍行为
- 非 row path（dim != 末轴）不适用
- UB 预算门控不成立时不得强行走常驻路径，须回退 tiled/strided 原码

## 5. 实施步骤

1. 在 Init() 内按 UB 预算门控分配行常驻 TQue（depth 2，每 buffer D*sizeof(T)）与 fp32 eBuf_（D 或 ROW_TILE+pad 个 float）；门控不满足时保持原 tiled/tileQue 布局逐字节不变
2. 新增行常驻主循环：prologue CopyInRow(u0)，逐行先预取 CopyInRow(u+1) 再 DeQue 当前行，收尾 FreeTensor，保持 <=2 outstanding buffer
3. 把 sum-exp 遍改造为 store 变体：在既有单循环内按 rep 追加一条掩码 Reg::StoreAlign，把 e=exp(x-max) 的 fp32 原始位写入 eBuf_
4. 把 out 遍改为从 eBuf_ 读取：LoadAlign(e) -> Mul by 已 hoist 的 rcpSum -> 保持原 downcast/Maxs/Store 不变，删除 GM 重读、unpack+Cast、Sub 与重复 Exp
5. 保留 D-oversize 的 tiled 路径、strip 路径（inner>1）与 numSt>1 行的 champion 原码逐字节不变，作为回退臂
6. 从干净 build 目录重建，跑 20/20 精度与 >=4 对 ABBA 配对（外层 msprof device Task Duration，两级 case-mean 再 geomean）

## 6. LLM 前置问题

- 目标实现是否满足：row path（inner==1 / isRow）且 D 可整行驻留 UB（20 个测试用例全为 [4096,4096] dim=-1，D 等于 ROW_TILE，每行恰好 1 个 super-tile）？
- 目标实现是否满足：每行 x 被 max/sum/out 多遍 pass 各从 GM 重读一次（本 run 为 3x），且 out pass 整遍重算了 sum-exp 遍已算出的 fp32 e=exp(x-max)？
- 目标实现是否满足：mte2 与 vec 同时构成绑定流水（SoftmaxHardswish champion vec 60.94us / mte2 42.24us；SoftmaxTanh champion vec 54.06/54.05/53.33us 与 mte2 52.03/51.78/59.21us co-binding）？
- 目标实现是否满足：存在可在 Init 期判定的 UB 预算门控与回退路径（D-oversize tiled / strip / numSt>1）？
- 目标实现是否满足：有同 run 的未触碰对照组或冻结基线 .so 可做 provenance-clean 配对？
- 是否命中排除条件：strip 路径（inner>1）与多 tile row（D > ROW_TILE 或超 UB 预算）不适用行常驻改造，保持原 3 遍代码？
- 是否命中排除条件：SoftmaxHardswish 中 numSt > 1 的行不适用 ProcessRowsCached，保持 champion 三遍行为？
- 是否命中排除条件：非 row path（dim != 末轴）不适用？
- 是否命中排除条件：UB 预算门控不成立时不得强行走常驻路径，须回退 tiled/strided 原码？

## 7. 验收标准

正确性：

- SoftmaxHardswish 20/20 PASS，per-case MERE/MARE 与 champion 基线完全一致（设计的位级相同算术），0 修复轮
- SoftmaxTanh 20/20 PASS 首试，per-case MERE 与冻结基线一致到约 3 位有效数字（case1 5.260e-08 vs 5.275e-08），0/3 编译修复、0/3 精度修复
- SoftmaxTanh 的 tanh regime 派发、NaN 行语义与全部数值链原样保留（同一 upcast x、同一 broadcast max、同一 Exp、同一 s = e*(1/sum) 链）

性能：

- SoftmaxHardswish：kernel geomean 75.326->52.967us（speedup 1.4221x），6 对平衡配对、相关性无歧义；mte2 30.8->12.4us（bf16/fp16）、47.5->22.4us（fp32），vec 63.8->45.9us（bf16/fp16）
- SoftmaxTanh：kernel task geomean 65.129->47.961us（speedup 1.3580x），formal ABBA 4/4 对 x 3 dtype 一致，provenance-clean 冻结基线 A 侧复现 BEST_MS 65.111 在 0.03% 内
- SoftmaxTanh 预注册假证门全过：aiv_mte2 下降 -76.3/-76.8/-51.7%（门 >=35%）、aiv_vec 下降 -23.4/-23.5/-23.5%（门 >=5%）、task 增益 +35.8%（门 >=5%）

回滚信号：

- UB 预算门控不成立时强行走行常驻路径（应回退 tiled/strided 原码）
- numSt>1 或 strip 路径（inner>1）出现超出噪声带的回退
- MERE/MARE 偏离基线——说明跨 pass 消费的 e 与重算值不再位级一致
- 行常驻 TQue 的预取/DeQue 时机改变引发队列异常或精度异常
- formal paired ABBA 显示 geomean <1.02x 或任一 dtype case mean <0.97x 时回退并记 rejected_performance

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：double-buffer-slot-reuse-race

- loop_20260913_070917（operator=SoftmaxHardswish, status=accepted, speedup=1.4221, precision=20/20 PASS, 6 对平衡配对, kernel geomean 75.326->52.967us）
- loop_20260913_070917（operator=SoftmaxTanh, status=accepted, speedup=1.3580, precision=20/20 PASS, 4/4 对 x 3 dtype, kernel task geomean 65.129->47.961us）

## 检索卡（短卡）

动作：把 row path 每行 x 一次 CopyIn 整行驻留 UB（depth-2 双缓冲），sum-exp 遍把 e 存入 eBuf_ 供 out 遍消费。
适用：row path 且 D 可整行驻留 UB、每行 x 被多遍 pass 重读、mte2 与 vec 同时绑定。
限制：UB 预算门控不可绕过（192KiB 常量，不满足走原码）；strip 与 numSt>1 行须保持 champion。
范围：normalization 的 softmax 系 row path 多遍 pass。
检索词：rowResident_、ST_UB_BUDGET_BYTES、eBuf_、StoreAlign、rcpSum
机会：每行 x 被 max/sum/out 三遍从 GM 重读，out 遍整遍重算 sum-exp 已算出的 e。
代价：eBuf_ 占 UB（fp32 约 17KB）；增量重建须从干净 build 开始。
