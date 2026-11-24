---
type: Optimization
title: 逐元素链迁回原生半精度域（128-lane b16）
description: 把 fp16/bf16 逐元素链从 fp32 加宽域迁回原生 half 域（oneRepSize 64->128），bf16 经 bf16<->half 交叉 cast 借用 half 通路。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/native-narrow-half-domain-compute.md
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
      "dtype 门控必须由编译期 constexpr / if constexpr 承载，fp32 路径与 legacy bf16（f32Buf 往返）路径逐字节不变：ForeachDiv 的 fp32 分支与 bf16 legacy 分支原样保留，GeluSoftplus 的 float 走原 fp32 路径逐字节不动",
      "bf16 借用 half 数据通路要求后端提供 bf16<->half 的 packed vcvt 且 CastTraits 为 NO_SAT + CAST_RINT + ZEROING；缺失时同机制内降档为 fp32-bridged 两跳 cast",
      "half 域字面量必须是 fp16-RNE 精确可表示的常量（GeluSoftplus 的 ERFH_B0..B4 与 Softplus 阈值 20.0h）",
      "UB 预算：ForeachDiv 的 f32Buf_（3*tileLength*4B = 126KB）仅对 bfloat16_t 分配，fp16 不再分配；ReluSoftmax 未新增 staging buffer（机制是寄存器宽度变更）",
      "迁入 half 域的中间量必须在 half 范围内，超出范围或会溢出的子链保留 fp32 尾（GeluSoftplus 保留 hybrid fp32 尾的域外防御语义）"
    ],
    "excluded_conditions": [
      "需要 bfloat16_t 原生 Div/Exp/Abs 的路径不适用——dav_3510 Reg 类型表不含 bfloat16_t",
      "在 half 域溢出的子链不适用：GeluAll 的 tanh 模式 exp(2z) 在 |z|>5.5 时 fp16 溢出，保持 fp32",
      "要求位级等价的场景不适用——本机制是非整数域的近似迁移，验收口径是容差门而非逐位一致",
      "16-bit 但 D%128!=0 的 masked 尾 rep 不适用（ReluSoftmax 保持 64-lane masked 路径），fp32 用例一律走原路径",
      "后端无 bf16<->half packed vcvt 且不接受 fp32-bridged 两跳 cast 时，bf16 侧不适用"
    ],
    "required_conditions": [
      "T 属于 {half, bfloat16_t} 的逐元素或融合链，且链上算子在该后端 Reg 类型表内支持 half（dav_3510 binary/binary_scalar/cmpsel/unary(Exp/Ln)/Div 等）",
      "该链当前以 fp32 加宽域实现：upcast -> 64-lane fp32 链 -> downcast 往返，oneRepSize 被 fp32 宽度锁死在 64",
      "aiv_vec 是唯一或主导关键路径（GeluAll：三个 dtype case 上 AIV Vector 均为唯一关键路径，scalar/mte2/mte3 完全被 vec 覆盖；GeluSoftplus：vec 56.73/56.73/54.55us = 89.7/89.7/88.9%）",
      "存在可编译期判定的 dtype 派发与逐字节不变的 fp32 回退臂（GeluSoftplus 已含 hybrid fp32 尾作为域外防御与降档臂）",
      "允许以容差门验收，且有 CPU 逐 op 舍入仿真可预验 MERE/MARE 余量（GeluSoftplus 的 select/native_half_accuracy_probe.py 口径）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "ForeachDiv",
      "operator_class": "elementwise",
      "pairs": 4,
      "precision": "20/20 PASS（fp16 native vdiv 1-2ulp 未触发三区兜底，±65504 / 0 / 小分母 / NaN 对抗面全 PASS）",
      "run_id": "<run-id>",
      "speedup": 1.0644,
      "status": "accepted"
    },
    {
      "operator": "GeluAll",
      "operator_class": "elementwise",
      "pairs": 4,
      "precision": "20/20 PASS（fp16 MERE 7.820-7.825e-04 = 0.801x 门槛，与 CPU 逐 op RTN 仿真 7.8207e-04 吻合；fp32/bf16 位级一致）",
      "run_id": "<run-id>",
      "speedup": 1.2181,
      "status": "accepted"
    },
    {
      "operator": "GeluAll",
      "operator_class": "elementwise",
      "pairs": 4,
      "precision": "20/20 PASS（bf16 交叉 cast 链 MERE 9.78-9.80e-04 = 0.125x of 2^-7 门槛；fp16 7.82e-04、fp32 1.325e-07 位级一致）",
      "run_id": "<run-id>",
      "speedup": 1.1765,
      "status": "accepted"
    },
    {
      "operator": "GeluSoftplus",
      "operator_class": "elementwise",
      "pairs": 4,
      "precision": "20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8；设备 MERE 与 CPU 仿真偏差 <2%，fp32 与 champion 位级一致）",
      "run_id": "<run-id>",
      "speedup": 1.4398,
      "status": "accepted"
    },
    {
      "operator": "ReluSoftmax",
      "operator_class": "normalization",
      "pairs": 4,
      "precision": "20/20 PASS（round_02 UnPack 修复后 direct 通过；round_01 Part-Cast 变体 8/20 失败已归档）",
      "run_id": "<run-id>",
      "speedup": 1.0578,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-b16-lane-underfill",
      "fp32-promoted-chain-emission-bound",
      "upcast-downcast-roundtrip"
    ],
    "dtypes": [
      "fp16",
      "bf16"
    ],
    "pattern": "native-narrow-half-domain-compute",
    "structure": [
      "native-128lane-b16-datapath",
      "cross-dtype-half-emulation-for-bf16",
      "constexpr-dtype-gated-dispatch",
      "fp32-tail-retained-for-out-of-domain",
      "tolerance-gate-not-bit-exact"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-NATIVE-NARROW-HALF-DOMAIN",
  "implementation_steps": [
    "核查目标链每个算子是否在该后端 Reg 类型表内支持 half（binary / binary_scalar / cmpsel / unary Exp/Ln / Div 等），并定位必须保留 fp32 的子链（tanh 的 exp(2z) 溢出域、域外防御尾）",
    "把硬编码 float 的 Reg 实现模板化为 <T storage, M math>（RegTensor<T> / UpdateMask<T> / Div<T> / oneRepSize = GetVecLen()/sizeof(T)），T==M 时改用 native load/store",
    "fp16 走 native half 链：DIST_NORM 直载直存（0 cast）、oneRepSize 提到 128，并按与 fp32 链完全相同的多项式形式与算子顺序展开（half 域字面量须 fp16-RNE 精确可表示）",
    "bf16 经交叉 cast 借用 half 数据通路：packed b16 LoadAlign -> 单条 Reg::Cast<half,bfloat16_t>（NO_SAT/CAST_RINT/ZEROING）-> 同一 half 链 -> 单条 Reg::Cast<bfloat16_t,half,CAST_RINT> -> packed b16 StoreAlign，不做 32-bit 槽解包",
    "以编译期 constexpr dtype 门控派发：fp32 与 legacy bf16（f32Buf 往返）路径逐字节不变，f32Buf_ 仅对 bfloat16_t 分配；masked 尾 rep 保持 64-lane 路径",
    "先跑 CPU 逐 op 舍入仿真确认 MERE/MARE 余量，再上设备跑 20/20 精度与 >=4 对 ABBA 配对（外层 msprof device Task Duration，两级 case-mean 再 geomean）"
  ],
  "intent": "消除 fp16/bf16 逐元素链因「提升到 fp32 域再算」带来的双重成本：每 256B 向量槽只填 64 个 fp32 lane，per-element 发射条数被 dtype 无关的 fp32 链锁死（半精度 dtype 移动一半字节却跑得更慢）；以及链两端 upcast/downcast 与 f32Buf UB 往返的向量管开销。",
  "mechanism": "把 fp16/bf16 的逐元素或融合链按完全相同的算子形式与算子顺序迁回原生 half 域，oneRepSize 从 64（fp32 加宽域）改为 128（原生 b16 lanes/vector register），每条 v-insn 覆盖 128 lane。fp16 用 DIST_NORM 直载直存（0 cast）；bf16 经 bf16<->half 精确交叉 cast 借用 half 数据通路（dav_3510 的 Reg::Div/Exp/Abs 只接受 half/float，不含 bfloat16_t）；fp32 用例与 legacy bf16 路径按 constexpr/if constexpr dtype 门控走原实现逐字节不动；无法在 half 域表达的子链保留 fp32 尾（GeluAll 的 tanh 因 exp(2z) 在 |z|>5.5 溢出 fp16）。精度护栏从位级等价换成容差门 + 设备/CPU 舍入模型一致。",
  "name": "逐元素链迁回原生半精度域（128-lane b16）",
  "operator_class": "elementwise",
  "operator_scope": "T 属于 {half, bfloat16_t} 且当前按 fp32 加宽域实现的逐元素/融合链：链上算子在 dav_3510 Reg 类型表内支持 half，aiv_vec 为唯一或主导关键路径，存在可编译期判定的 dtype 门控与 fp32 回退臂",
  "principle": "半精度存储的 16-bit dtype 在 fp32 加宽域上计算时向量槽被浪费一半：GeluAll 的 fp16/bf16 用例字节数是 fp32 的一半却更慢，因为 erf 链无论存储 dtype 都在 fp32 寄存器里逐元素执行、per-element 数学成本与 dtype 无关再叠加 2 次 cast；ReluSoftmax 的 fp16/bf16 vec 36.6us 与 fp32 vec 35.2us 几乎相同，正是「16-bit 前端把每 256B 向量槽的一半 lane 浪费在 Load/relu/max 上」的指纹。迁回原生半精度域后同一算子序的发射槽约减半（GeluSoftplus 50 -> 约 23 槽/128 元素，实测 fp16 vec -50.2%、bf16 vec -44.5%）。精度上：16-bit 的 relu/max 与 half->f32 upcast 是精确的，新增误差只来自 half 域的 Div/Exp 等超越函数；该误差由容差门界定并以 CPU 逐 op 舍入仿真预验（GeluSoftplus 设备 MERE 与仿真偏差 <2%；GeluAll fp16 设备 MERE 7.820-7.825e-04 与仿真 7.8207e-04 吻合），属于非整数域的近似迁移而非位级等价。",
  "related_anti_patterns": [
    "bf16-scalar-cast-unsupported",
    "simt-lowprecision-scalar-cast-intrinsic"
  ],
  "risks": [
    "后端类型表门控：dav_3510 的 Reg::Div 类型表含 half（ActualT==half 走 vdiv 或 DivIEEE754HalfImpl）但**不含 bfloat16_t**，Reg::Cast 仅有 f322f16/f322bf16 收缩方向与 packed 的 bf162f16/f162bf16，无 half/bf16->f32 宽化——bf16 的原生域计算被该 API 面证伪，只能经 bf16<->half 交叉 cast 借用 half 数据通路，且 bf16->half 仅对范围内值精确（8-bit 尾数扩进 10-bit）",
    "与既有 native-uint16-stein-domain-no-promotion（int16 Stein 域）的区别必须说明：那张卡是整数域免提升实例，无舍入语义、可用位级等价论证；本卡是浮点半精度实例，bf16 还多一层交叉 cast，精度护栏必须换成容差门 + 设备/CPU 舍入模型一致（CPU 逐 op 舍入仿真预验），不能套用整数域的位级等价论证",
    "精度不再位级等价，须以容差门验收：ReluSoftmax round_01 的 Part-Cast 变体（在 packed register 上做 Cast RegLayout ZERO/ONE）被证伪，12 个 half dtype case MERE~0.34 全失败（fp32 8/8 控制通过），round_02 改用 UnPack(LOWEST/HIGHEST) 后 20/20 direct 通过，消耗 1 轮（上限 3）修复预算",
    "half 域超越函数引入新的舍入地板，余量必须逐 case 核：ForeachDiv fp16 的 1-2 ulp vdiv（相对误差 <=2^-11）落在 2^-10 门槛内且未触发三区兜底；GeluAll fp16 MERE 7.820-7.825e-04 为 0.801x 门槛；GeluSoftplus bf16 MARE 7.634e-03 为 0.098x 门槛——对抗面覆盖不均（ForeachDiv 含 ±65504/0/小分母/NaN，GeluSoftplus 20 case 全为 4096x4096、value_range [-1,1]、无 inf/nan）",
    "half 域不可表达或会溢出的子链必须保留 fp32：GeluAll 的 tanh 模式 exp(2z) 在 |z|>5.5 溢出 fp16 故保持 fp32；ReluSoftmax 仅 16-bit 且 (D & 127)==0 走 native，masked 尾 rep（D%128!=0）保持 64-lane 路径，fp32 一律走原路径"
  ],
  "slug": "native-narrow-half-domain-compute",
  "summary": "把 fp16/bf16 的逐元素或融合链从「提升到 fp32 加宽域再算（64-lane、upcast/downcast 往返）」迁回原生 half 域按同一算子序计算（128 lanes/256B v-insn）：fp16 直载直存 0 cast；bf16 经 bf16<->half 精确交叉 cast 借用 half 数据通路（dav_3510 无 bfloat16_t 的 Div/Exp/Abs）；fp32 与溢出子链按编译期 dtype 门控保留原路径。GeluSoftplus geomean 62.743->43.579us（1.4398x，fp16 1.803x、bf16 1.656x），GeluAll 65.823->54.037us（1.2181x，fp16 1.8074x）与 54.017->45.912us（1.1765x，bf16 1.6275x），ForeachDiv 37.159->34.913us（1.0644x，fp16 -16.9%），ReluSoftmax 43.274->40.911us（1.0578x）。精度全部 20/20，以容差门 + 设备/CPU 舍入模型一致验收。",
  "verification": {
    "correctness": [
      "ForeachDiv 20/20 PASS：fp16 native vdiv 的 1-2 ulp 未触发三区兜底，±65504、0/小分母、NaN 对抗面全 PASS；编译与精度均 0 修复预算",
      "GeluAll fp16 20/20 PASS 首试：fp16 MERE 7.820-7.825e-04（0.801x of 2^-10 门槛），与 CPU 逐 op RTN 仿真 7.8207e-04 吻合，证明设备 f16 vdiv/vexp 为 round-to-nearest；fp32/bf16 路径位级一致",
      "GeluAll bf16 20/20 PASS 首试：bf16 交叉 cast 链 MERE 9.78-9.80e-04（0.125x of 2^-7 门槛）；fp16 7.82e-04 与 fp32 1.325e-07 位级一致",
      "GeluSoftplus 20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8）：设备 MERE 与 CPU 仿真偏差 <2%（fp16 2.699e-04 vs 2.73e-04；bf16 3.391e-04 vs 3.4e-04），fp32 MERE 与 champion 位级一致（门控路径 verbatim）",
      "ReluSoftmax 20/20 PASS（round_02 UnPack 修复后 direct 通过）；round_01 Part-Cast 变体 8/20 失败已归档"
    ],
    "performance": [
      "GeluSoftplus：geomean 62.743->43.579us（1.4398x），4/4 对候选更快、min pair ratio 1.4383；fp16 vec 56.72->28.25us（-50.2%）、bf16 vec 56.75->31.50us（-44.5%），fp32 按设计持平",
      "GeluAll：fp16 67.870->37.551us（1.8074x）、geomean 65.823->54.037us（1.2181x）、min pair ratio 1.2174；bf16 67.790->41.653us（1.6275x）、geomean 54.017->45.912us（1.1765x）、min pair ratio 1.1759；两轮均为 4 对平衡交替 ABBA，未触碰 dtype 在 0.15%/0.21% 噪声带内",
      "ForeachDiv：fp16 TaskDuration 27.184->22.593us（-16.9%）、geomean 37.159->34.913us（1.0644x），4 对 ABBA，非目标 dtype 无回退；bf16/fp32 路径字节级不变",
      "ReluSoftmax：geomean 43.274->40.911us（1.0578x；bf16 1.087x、fp16 1.089x、fp32 1.0003x），4/4 对 >=1.0；每 128 元素向量指令数 30->23（max sweep 8->3、sum sweep 14->12、scale 8 不变）"
    ],
    "rollback_signals": [
      "精度超容差门，且同一机制内降档（hybrid fp32 尾、两跳 cast、单 dtype 门控）后仍不过 -> rejected_accuracy",
      "half 指令非全宽单发射或目标 dtype 增益 <5% -> rejected_performance",
      "Reg half 编码 / bf16<->fp16 cast trait 编译面失败且同方向内无法降档 -> rejected_build",
      "fp32 或非目标 dtype 路径出现超出噪声带的回退（门控失效的指纹）",
      "把 fp16 溢出域（tanh 的 exp(2z)，|z|>5.5）误迁入 half 域"
    ]
  }
}
-->

# 性能优化策略：逐元素链迁回原生半精度域（128-lane b16）

把 fp16/bf16 的逐元素或融合链从「提升到 fp32 加宽域再算（64-lane、upcast/downcast 往返）」迁回原生 half 域按同一算子序计算（128 lanes/256B v-insn）。GeluSoftplus geomean 62.743->43.579us（1.4398x），GeluAll 65.823->54.037us（1.2181x，fp16 1.8074x）与 54.017->45.912us（1.1765x，bf16 1.6275x），ForeachDiv 37.159->34.913us（1.0644x），ReluSoftmax 43.274->40.911us（1.0578x）。

## 1. 原理

半精度存储的 16-bit dtype 在 fp32 加宽域上计算时向量槽被浪费一半：GeluAll 的 fp16/bf16 用例字节数是 fp32 的一半却更慢，因为 erf 链无论存储 dtype 都在 fp32 寄存器里逐元素执行、per-element 数学成本与 dtype 无关再叠加 2 次 cast；ReluSoftmax 的 fp16/bf16 vec 36.6us 与 fp32 vec 35.2us 几乎相同，正是「16-bit 前端把每 256B 向量槽的一半 lane 浪费在 Load/relu/max 上」的指纹。迁回原生半精度域后同一算子序的发射槽约减半（GeluSoftplus 50 -> 约 23 槽/128 元素，实测 fp16 vec -50.2%、bf16 vec -44.5%）。精度上：16-bit 的 relu/max 与 half->f32 upcast 是精确的，新增误差只来自 half 域的 Div/Exp 等超越函数；该误差由容差门界定并以 CPU 逐 op 舍入仿真预验（GeluSoftplus 设备 MERE 与仿真偏差 <2%；GeluAll fp16 设备 MERE 7.820-7.825e-04 与仿真 7.8207e-04 吻合），属于非整数域的近似迁移而非位级等价。

实现机制：把 fp16/bf16 的逐元素或融合链按完全相同的算子形式与算子顺序迁回原生 half 域，oneRepSize 从 64（fp32 加宽域）改为 128（原生 b16 lanes/vector register），每条 v-insn 覆盖 128 lane。fp16 用 DIST_NORM 直载直存（0 cast）；bf16 经 bf16<->half 精确交叉 cast 借用 half 数据通路（dav_3510 的 Reg::Div/Exp/Abs 只接受 half/float，不含 bfloat16_t）；fp32 用例与 legacy bf16 路径按 constexpr/if constexpr dtype 门控走原实现逐字节不动；无法在 half 域表达的子链保留 fp32 尾（GeluAll 的 tanh 因 exp(2z) 在 |z|>5.5 溢出 fp16）。精度护栏从位级等价换成容差门 + 设备/CPU 舍入模型一致。

## 2. 性能问题模式

- 优化目标：消除 fp16/bf16 逐元素链因「提升到 fp32 域再算」带来的双重成本：每 256B 向量槽只填 64 个 fp32 lane，per-element 发射条数被 dtype 无关的 fp32 链锁死（半精度 dtype 移动一半字节却跑得更慢）；以及链两端 upcast/downcast 与 f32Buf UB 往返的向量管开销
- 适用数据流：T 属于 {half, bfloat16_t} 且当前按 fp32 加宽域实现的逐元素/融合链：链上算子在 dav_3510 Reg 类型表内支持 half，aiv_vec 为唯一或主导关键路径，存在可编译期判定的 dtype 门控与 fp32 回退臂
- Feature signature：`{"bottleneck": ["vec-b16-lane-underfill", "fp32-promoted-chain-emission-bound", "upcast-downcast-roundtrip"], "dtypes": ["fp16", "bf16"], "pattern": "native-narrow-half-domain-compute", "structure": ["native-128lane-b16-datapath", "cross-dtype-half-emulation-for-bf16", "constexpr-dtype-gated-dispatch", "fp32-tail-retained-for-out-of-domain", "tolerance-gate-not-bit-exact"]}`

## 3. 正确性红线

- 后端类型表门控：dav_3510 的 Reg::Div 类型表含 half（ActualT==half 走 vdiv 或 DivIEEE754HalfImpl）但**不含 bfloat16_t**，Reg::Cast 仅有 f322f16/f322bf16 收缩方向与 packed 的 bf162f16/f162bf16，无 half/bf16->f32 宽化——bf16 的原生域计算被该 API 面证伪，只能经 bf16<->half 交叉 cast 借用 half 数据通路，且 bf16->half 仅对范围内值精确（8-bit 尾数扩进 10-bit）
- 与既有 native-uint16-stein-domain-no-promotion（int16 Stein 域）的区别必须说明：那张卡是整数域免提升实例，无舍入语义、可用位级等价论证；本卡是浮点半精度实例，bf16 还多一层交叉 cast，精度护栏必须换成容差门 + 设备/CPU 舍入模型一致（CPU 逐 op 舍入仿真预验），不能套用整数域的位级等价论证
- 精度不再位级等价，须以容差门验收：ReluSoftmax round_01 的 Part-Cast 变体（在 packed register 上做 Cast RegLayout ZERO/ONE）被证伪，12 个 half dtype case MERE~0.34 全失败（fp32 8/8 控制通过），round_02 改用 UnPack(LOWEST/HIGHEST) 后 20/20 direct 通过，消耗 1 轮（上限 3）修复预算
- half 域超越函数引入新的舍入地板，余量必须逐 case 核：ForeachDiv fp16 的 1-2 ulp vdiv（相对误差 <=2^-11）落在 2^-10 门槛内且未触发三区兜底；GeluAll fp16 MERE 7.820-7.825e-04 为 0.801x 门槛；GeluSoftplus bf16 MARE 7.634e-03 为 0.098x 门槛——对抗面覆盖不均（ForeachDiv 含 ±65504/0/小分母/NaN，GeluSoftplus 20 case 全为 4096x4096、value_range [-1,1]、无 inf/nan）
- half 域不可表达或会溢出的子链必须保留 fp32：GeluAll 的 tanh 模式 exp(2z) 在 |z|>5.5 溢出 fp16 故保持 fp32；ReluSoftmax 仅 16-bit 且 (D & 127)==0 走 native，masked 尾 rep（D%128!=0）保持 64-lane 路径，fp32 一律走原路径

资源与硬件约束：

- dtype 门控必须由编译期 constexpr / if constexpr 承载，fp32 路径与 legacy bf16（f32Buf 往返）路径逐字节不变：ForeachDiv 的 fp32 分支与 bf16 legacy 分支原样保留，GeluSoftplus 的 float 走原 fp32 路径逐字节不动
- bf16 借用 half 数据通路要求后端提供 bf16<->half 的 packed vcvt 且 CastTraits 为 NO_SAT + CAST_RINT + ZEROING；缺失时同机制内降档为 fp32-bridged 两跳 cast
- half 域字面量必须是 fp16-RNE 精确可表示的常量（GeluSoftplus 的 ERFH_B0..B4 与 Softplus 阈值 20.0h）
- UB 预算：ForeachDiv 的 f32Buf_（3*tileLength*4B = 126KB）仅对 bfloat16_t 分配，fp16 不再分配；ReluSoftmax 未新增 staging buffer（机制是寄存器宽度变更）
- 迁入 half 域的中间量必须在 half 范围内，超出范围或会溢出的子链保留 fp32 尾（GeluSoftplus 保留 hybrid fp32 尾的域外防御语义）

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- T 属于 {half, bfloat16_t} 的逐元素或融合链，且链上算子在该后端 Reg 类型表内支持 half（dav_3510 binary/binary_scalar/cmpsel/unary(Exp/Ln)/Div 等）
- 该链当前以 fp32 加宽域实现：upcast -> 64-lane fp32 链 -> downcast 往返，oneRepSize 被 fp32 宽度锁死在 64
- aiv_vec 是唯一或主导关键路径（GeluAll：三个 dtype case 上 AIV Vector 均为唯一关键路径，scalar/mte2/mte3 完全被 vec 覆盖；GeluSoftplus：vec 56.73/56.73/54.55us = 89.7/89.7/88.9%）
- 存在可编译期判定的 dtype 派发与逐字节不变的 fp32 回退臂（GeluSoftplus 已含 hybrid fp32 尾作为域外防御与降档臂）
- 允许以容差门验收，且有 CPU 逐 op 舍入仿真可预验 MERE/MARE 余量（GeluSoftplus 的 select/native_half_accuracy_probe.py 口径）

不适用：

- 需要 bfloat16_t 原生 Div/Exp/Abs 的路径不适用——dav_3510 Reg 类型表不含 bfloat16_t
- 在 half 域溢出的子链不适用：GeluAll 的 tanh 模式 exp(2z) 在 |z|>5.5 时 fp16 溢出，保持 fp32
- 要求位级等价的场景不适用——本机制是非整数域的近似迁移，验收口径是容差门而非逐位一致
- 16-bit 但 D%128!=0 的 masked 尾 rep 不适用（ReluSoftmax 保持 64-lane masked 路径），fp32 用例一律走原路径
- 后端无 bf16<->half packed vcvt 且不接受 fp32-bridged 两跳 cast 时，bf16 侧不适用

## 5. 实施步骤

1. 核查目标链每个算子是否在该后端 Reg 类型表内支持 half（binary / binary_scalar / cmpsel / unary Exp/Ln / Div 等），并定位必须保留 fp32 的子链（tanh 的 exp(2z) 溢出域、域外防御尾）
2. 把硬编码 float 的 Reg 实现模板化为 <T storage, M math>（RegTensor<T> / UpdateMask<T> / Div<T> / oneRepSize = GetVecLen()/sizeof(T)），T==M 时改用 native load/store
3. fp16 走 native half 链：DIST_NORM 直载直存（0 cast）、oneRepSize 提到 128，并按与 fp32 链完全相同的多项式形式与算子顺序展开（half 域字面量须 fp16-RNE 精确可表示）
4. bf16 经交叉 cast 借用 half 数据通路：packed b16 LoadAlign -> 单条 Reg::Cast<half,bfloat16_t>（NO_SAT/CAST_RINT/ZEROING）-> 同一 half 链 -> 单条 Reg::Cast<bfloat16_t,half,CAST_RINT> -> packed b16 StoreAlign，不做 32-bit 槽解包
5. 以编译期 constexpr dtype 门控派发：fp32 与 legacy bf16（f32Buf 往返）路径逐字节不变，f32Buf_ 仅对 bfloat16_t 分配；masked 尾 rep 保持 64-lane 路径
6. 先跑 CPU 逐 op 舍入仿真确认 MERE/MARE 余量，再上设备跑 20/20 精度与 >=4 对 ABBA 配对（外层 msprof device Task Duration，两级 case-mean 再 geomean）

## 6. LLM 前置问题

- 目标实现是否满足：T 属于 {half, bfloat16_t} 的逐元素或融合链，且链上算子在该后端 Reg 类型表内支持 half（dav_3510 binary/binary_scalar/cmpsel/unary(Exp/Ln)/Div 等）？
- 目标实现是否满足：该链当前以 fp32 加宽域实现（upcast -> 64-lane fp32 链 -> downcast 往返，oneRepSize 被 fp32 宽度锁死在 64）？
- 目标实现是否满足：aiv_vec 是唯一或主导关键路径（GeluAll 三个 dtype case 的 AIV Vector 为唯一关键路径；GeluSoftplus vec 占比 89.7/89.7/88.9%）？
- 目标实现是否满足：存在可编译期判定的 dtype 派发与逐字节不变的 fp32 回退臂（GeluSoftplus 已含 hybrid fp32 尾）？
- 目标实现是否满足：允许以容差门验收，且有 CPU 逐 op 舍入仿真可预验 MERE/MARE 余量？
- 是否命中排除条件：需要 bfloat16_t 原生 Div/Exp/Abs 的路径不适用——dav_3510 Reg 类型表不含 bfloat16_t？
- 是否命中排除条件：在 half 域溢出的子链不适用（GeluAll tanh 的 exp(2z)，|z|>5.5）？
- 是否命中排除条件：要求位级等价的场景不适用——本机制是非整数域的近似迁移？
- 是否命中排除条件：16-bit 但 D%128!=0 的 masked 尾 rep 不适用，fp32 用例一律走原路径？
- 是否命中排除条件：后端无 bf16<->half packed vcvt 且不接受 fp32-bridged 两跳 cast 时，bf16 侧不适用？

## 7. 验收标准

正确性：

- ForeachDiv 20/20 PASS：fp16 native vdiv 的 1-2 ulp 未触发三区兜底，±65504、0/小分母、NaN 对抗面全 PASS；编译与精度均 0 修复预算
- GeluAll fp16 20/20 PASS 首试：fp16 MERE 7.820-7.825e-04（0.801x of 2^-10 门槛），与 CPU 逐 op RTN 仿真 7.8207e-04 吻合，证明设备 f16 vdiv/vexp 为 round-to-nearest；fp32/bf16 路径位级一致
- GeluAll bf16 20/20 PASS 首试：bf16 交叉 cast 链 MERE 9.78-9.80e-04（0.125x of 2^-7 门槛）；fp16 7.82e-04 与 fp32 1.325e-07 位级一致
- GeluSoftplus 20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8）：设备 MERE 与 CPU 仿真偏差 <2%（fp16 2.699e-04 vs 2.73e-04；bf16 3.391e-04 vs 3.4e-04），fp32 MERE 与 champion 位级一致
- ReluSoftmax 20/20 PASS（round_02 UnPack 修复后 direct 通过）；round_01 Part-Cast 变体 8/20 失败已归档

性能：

- GeluSoftplus：geomean 62.743->43.579us（1.4398x），4/4 对候选更快、min pair ratio 1.4383；fp16 vec 56.72->28.25us（-50.2%）、bf16 vec 56.75->31.50us（-44.5%），fp32 按设计持平
- GeluAll：fp16 67.870->37.551us（1.8074x）、geomean 65.823->54.037us（1.2181x）、min pair ratio 1.2174；bf16 67.790->41.653us（1.6275x）、geomean 54.017->45.912us（1.1765x）、min pair ratio 1.1759；两轮均为 4 对平衡交替 ABBA，未触碰 dtype 在 0.15%/0.21% 噪声带内
- ForeachDiv：fp16 TaskDuration 27.184->22.593us（-16.9%）、geomean 37.159->34.913us（1.0644x），4 对 ABBA，非目标 dtype 无回退；bf16/fp32 路径字节级不变
- ReluSoftmax：geomean 43.274->40.911us（1.0578x；bf16 1.087x、fp16 1.089x、fp32 1.0003x），4/4 对 >=1.0；每 128 元素向量指令数 30->23（max sweep 8->3、sum sweep 14->12、scale 8 不变）

回滚信号：

- 精度超容差门，且同一机制内降档（hybrid fp32 尾、两跳 cast、单 dtype 门控）后仍不过 -> rejected_accuracy
- half 指令非全宽单发射或目标 dtype 增益 <5% -> rejected_performance
- Reg half 编码 / bf16<->fp16 cast trait 编译面失败且同方向内无法降档 -> rejected_build
- fp32 或非目标 dtype 路径出现超出噪声带的回退（门控失效的指纹）
- 把 fp16 溢出域（tanh 的 exp(2z)，|z|>5.5）误迁入 half 域

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：bf16-scalar-cast-unsupported, simt-lowprecision-scalar-cast-intrinsic

- loop_20260913_043336（operator=ForeachDiv, status=accepted, speedup=1.0644, precision=20/20 PASS, 4 对 ABBA, geomean 37.159->34.913us）
- loop_20260913_043336（operator=GeluAll, status=accepted, speedup=1.2181, precision=20/20 PASS, 4 对 ABBA, fp16 67.870->37.551us, geomean 65.823->54.037us）
- loop_20260913_043336（operator=GeluAll, status=accepted, speedup=1.1765, precision=20/20 PASS, 4 对 ABBA, bf16 67.790->41.653us, geomean 54.017->45.912us）
- loop_20260912_174322（operator=GeluSoftplus, status=accepted, speedup=1.4398, precision=20/20 PASS, 4/4 对, geomean 62.743->43.579us）
- loop_20260913_070917（operator=ReluSoftmax, status=accepted, speedup=1.0578, precision=20/20 PASS, 4/4 对 >=1.0, geomean 43.274->40.911us）

## 检索卡（短卡）

动作：把 fp16/bf16 逐元素链从 fp32 加宽域迁回原生 half 域（oneRepSize 64->128），bf16 经 bf16<->half 交叉 cast 借用 half 通路。
适用：T 属于 {half,bfloat16_t}、链上算子在该后端 Reg 类型表内支持 half、aiv_vec 为唯一关键路径。
限制：dav_3510 Reg 表不含 bfloat16_t；|z|>5.5 的 exp(2z) 保留 fp32；D%128!=0 保持 64-lane。
范围：elementwise 逐元素/融合链的发射槽。
检索词：oneRepSize、RegTensor、DIST_NORM、Reg::Cast、CAST_RINT、NO_SAT
机会：16-bit 前端把每 256B 向量槽一半 lane 浪费，半精度字节数更少却跑得更慢。
代价：half 域超越函数引入新舍入地板，余量须逐 case 核。
