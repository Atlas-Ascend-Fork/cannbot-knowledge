---
type: Optimization
title: gather 操作数寄存器驻留：tile 外层跨行复用 + Reg::Gather dst 直出
description: 把行无关的操作数表从逐行从UB重取改为跨行寄存器驻留，gather改为dst直出寄存器并融合，循环重排为tile外层、行内层。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/register-resident-gather-operands.md
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
      "gather 操作数必须是行无关且跨行可复用的（本 run：u32 元素索引 idx0/idx1、lx 权重、满 mask 在全部 768 行上相同）——行相关操作数不能寄存器驻留",
      "Reg::Gather 要求 dst 为寄存器、index/mask 为寄存器操作数，且 B32 源配 u32 索引：改表语义（ShiftLefts/ShiftRights）时必须与 UB 级 AscendC::Gather 的隐式转换对齐（本 run 表改存 u32 元素索引，与 UB 级内部 ShiftRights(2) 等价）",
      "寄存器操作数只能在一个 __simd_vf__ 作用域内跨 repeat 存活：__simd_vf__ 函数不接受 RegTensor 引用参数（指针参数必须落在 __ubuf__），跨 repeat 复用必须宏内联展开融合体",
      "快臂的 UB 预算守卫必须显式（本 run slabRegOk_：in + out + 16*wElem*4B <= 128KB），并保留逐行回退臂；两条臂共用同一内联序列以保证位级一致"
    ],
    "excluded_conditions": [
      "操作数行相关（每行不同）时不能驻留：跨行复用是收益来源",
      "aiv_scalar 而非 aiv_vec 是节拍源时不适用：本机制删除的是 vec 管上的取数往返发射，scalar 主导的算子无可回收对象（本 run 后继瓶颈已转为 aiv_scalar 64.6us，aiv_time ≈ scalar + 1us）",
      "已把表常驻 UB 但仍逐行读的形态（covh-init-precompute-ub-resident）不属于本机制：本机制消除的正是逐行读",
      "没有 gather 操作数、也不存在 Reg::Gather dst 直出融合的场景（small-matrix-register-residency），以及消除逐元素中间量 UB store→reload 往返的场景（in-register-s-forwarding）都不属于本机制：本机制消除的是 gather 操作数表与 gather 结果的取数往返"
    ],
    "required_conditions": [
      "vec 管是唯一主导瓶颈且 mte 已充分重叠：本 run champion 双上下文 profiling 稳定，aiv_vec 179.33/179.31/175.10us（vec_ratio 全部 0.92），aiv_scalar 122.53/122.59/115.51us，aiv_mte2 全测试 20.7-22.8us（热张量 ABBA 口径仅 7.1-7.4us）、aiv_mte3 5.8-8.1us——aiv_time ≈ vec + 11-16us，scalar 大部分被 vec 掩盖",
      "存在被每 (行,tile,repeat) 重复取用的行无关操作数表：本 run 每行 ~44 条纯搬运/设置类 v-insn（索引 LoadAlign×8、ShiftRights×8、gather 结果 Store+Load×16、lx LoadAlign×4、UpdateMask×8），全是行无关量被逐行重做",
      "目标 API 组合存在：CANN 9.1.0 dav_3510 头文件证实 UB 级 AscendC::Gather 展开为每 repeat UpdateMask + LoadAlign(offsetReg) + vgather2 + StoreAlign(结果回 UB)（kernel_operator_vec_gather_impl.h），且 Reg 级 AscendC::Reg::Gather(dstReg, baseAddr, indexReg, mask) 存在（kernel_reg_compute_datacopy_intf_impl.h:368 → DataCopyGatherImpl → vgather2，dst=寄存器、index/mask=寄存器操作数，vector_float 覆盖，B32 源配 u32 索引；asc_gather_impl.h）",
      "循环结构可重排为 tile 外层/行内层使操作数寄存器跨行存活：本 run ProcessSlab 的行×tile 循环可按 tile 分片驻留索引寄存器，VB 输出落 vrowSlab UB 供 vgather2 取数（真实 shape [64,3,128,128] sf=2 → totalRows=49152、blockDim=64 → 768 行/核；bilinear align_corners=True、ry=127/255）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "task_0363_upsample",
      "operator_class": "upsample-interpolate",
      "precision": "20/20 PASS（首次通过，0 次修复；同时设备侧核实 vgather2 B32 索引单位=u32 元素，元素选择与全部数学指令及操作数值与 champion 代码等价、预期位级一致）",
      "run_id": "<run-id>",
      "speedup": 2.9625,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-operand-roundtrip",
      "row-invariant-gather-operand-refetch",
      "gather-result-ub-store-reload"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "register-resident-gather-operands",
    "reduce_mode": "",
    "structure": [
      "register-resident-gather-operand-table",
      "reg-level-vgather2-dst-register",
      "tile-outer-row-inner-loop",
      "vrowslab-ub-prewrite",
      "bitwise-identical-element-selection"
    ]
  },
  "generality": "op_class",
  "id": "UPSAMPLE-REG-RESIDENT-GATHER",
  "implementation_steps": [
    "Init 期把索引表改为 u32 元素索引（idx0All/idx1All，去 ShiftLefts(2)），新增 vrowSlabBuf_ 与 slabRegOk_ 守卫（in + out + 16*wElem*4B <= 128KB），移除 g0Buf_/g1Buf_",
    "新增 UPSAMPLE_GATHER_BLEND_REPEAT 内联序列（Reg::Gather ×2 + Sub + MulDstAdd + Cast/StoreAlign）与 GatherBlendTileRegImpl（per-tile 装载变体，逐行臂与 slab 慢臂共用）",
    "新增 BlendSlabTileOuterRegImpl：把 ProcessSlab 的行×tile 循环改为 tile 外层/行内层，VB 行预写 vrowSlab 后 off0Reg/off1Reg/lxReg/mask 每 (slab 批,tile) 只装载一次、供 16 行复用",
    "删除全部 UB 级 AscendC::Gather 调用点，使快臂/慢臂/逐行臂都走同一内联融合序列（数学指令 Muls/Axpy/Sub/MulDstAdd/Cast 与 vgather2 元素选择不变）",
    "以位级等价的精度门（20/20 首次通过，含 vgather2 索引单位的设备侧核实）与 4 对平衡交替 ABBA 的 profile 签名验收：预期 aiv_vec / aiv_scalar 显著下降、mte2/mte3 不升；出现 spill 指纹（vec/mte 不降反升）即回退"
  ],
  "intent": "消除逐行重复付出的操作数取数往返：行无关的 gather 操作数（u32 元素索引 idx0/idx1、lx 权重、满 mask）被每 (行,tile,repeat) 从 UB 重取，水平混合又走 UB 级 AscendC::Gather（每次调用 LoadAlign 索引表 + vgather2 + StoreAlign 结果回 UB），随后 HBlend 再 LoadAlign 回读 g0/g1/lx 并逐调用 UpdateMask——本 run 每行 ~44 条纯搬运/设置类 v-insn（索引 LoadAlign×8、ShiftRights×8、gather 结果 Store+Load×16、lx LoadAlign×4、UpdateMask×8）全是行无关量被逐行重做。",
  "mechanism": "register-resident-gather-operands。结构上把 ProcessSlab 的行×tile 循环改为 tile 外层 / 行内层：VB 输出行预写 vrowSlab UB 缓冲供 vgather2 取数，off0Reg/off1Reg/lxReg/mask 每 (slab 批,tile) 只装载一次、供 16 行复用；slabRegOk_ 守卫（in + out + 16*wElem*4B <= 128KB）决定热路径走快臂还是回退。水平混合从 UB tensor API AscendC::Gather 换成 Reg 级 Reg::Gather（vgather2，dst 直接进寄存器、索引与 mask 均为寄存器操作数）加 Sub + MulDstAdd + Cast/Store 的内联融合序列（UPSAMPLE_GATHER_BLEND_REPEAT 宏），从而去掉 gather 结果的 UB 写+读往返、索引表与 lx 的重复 LoadAlign、以及逐调用 UpdateMask。Init 表改存 u32 元素索引（去 ShiftLefts(2)），与 UB 级 AscendC::Gather 内部的隐式 ShiftRights(2) 等价，vgather2 的元素选择位级不变；g0Buf_/g1Buf_ 与全部 UB 级 AscendC::Gather 调用点被移除。逐行回退臂与 slab 慢臂共用 GatherBlendTileRegImpl，与快臂保持同一数学序列（Muls/Axpy/Sub/MulDstAdd/Cast），因此逐行路径也位级一致。实现坑：__simd_vf__ 函数不接受 RegTensor 引用参数（指针参数必须落在 __ubuf__），跨 repeat 复用寄存器操作数必须在单一 __simd_vf__ 作用域内用宏内联展开（本 run 唯一一次编译修复）。",
  "name": "gather 操作数寄存器驻留：tile 外层跨行复用 + Reg::Gather dst 直出",
  "operator_class": "upsample-interpolate",
  "operator_scope": "逐行/按 slab 处理、每行重复取用行无关操作数表（索引、权重、掩码）、且水平混合走 UB 级 gather 的元素级/插值类算子；本 run 为 task_0363_upsample（ascend950dt_9582，真实 shape [64,3,128,128] sf=2、totalRows=49152、blockDim=64 → 768 行/核，bilinear align_corners=True、ry=127/255）",
  "principle": "在 vec_ratio=0.92、mte 已重叠到 <4% 的算子上，唯一杠杆是减少 vec 管发射；但发射里占比最大的一类不是数学指令，而是行无关操作数的取数往返——索引表、权重、掩码每行每 tile 从 UB 重取，UB 级 Gather 又把 gather 结果写回 UB 再读回，随后 HBlend 再 LoadAlign 回读 g0/g1/lx。这类 v-insn 的条数占比不等于成本占比：LoadAlign/StoreAlign/UpdateMask 受 LSU/发射吞吐约束，真实权重远高于条数占比（本 run 最终兑现 2.96x，远超保守预期的 1.15-1.3x，而 direction_002 把便宜指令换成更贵融合 MAC 的转化率仅约 1:0.12）。因此正确做法是纯删除加驻留：把行无关操作数提升为跨行存活的寄存器、把 gather 从 UB tensor API 换成 dst 直出寄存器的 Reg::Gather，使每个 tile 只装载一次操作数供全部 768 行复用。数学指令（Muls/Axpy/Sub/MulDstAdd/Cast）与 vgather2 的元素选择逐位不变，正确性风险只剩寄存器压力与索引单位两处。与之对照：covh-init-precompute-ub-resident 把表常驻 UB 但仍逐行读（没消除往返）；small-matrix-register-residency 没有 gather 操作数、也没有 Reg::Gather 的 dst 直出融合；in-register-s-forwarding 消除的是逐元素中间量的 UB store→reload 往返，不是 gather 操作数表。",
  "related_anti_patterns": [
    "covh-init-precompute-ub-resident",
    "small-matrix-register-residency",
    "in-register-s-forwarding"
  ],
  "risks": [
    "__simd_vf__ 函数不接受 RegTensor 引用参数（指针参数必须落在 __ubuf__）：跨 repeat 复用寄存器操作数必须在单一 __simd_vf__ 作用域内用宏内联展开——本 run 唯一一次编译修复（attempt 1 失败、attempt 2 通过），把融合 repeat 体展开为 UPSAMPLE_GATHER_BLEND_REPEAT 宏",
    "vgather2 的索引单位必须设备侧核实：本 run 20/20 同时证明 B32 索引单位是 u32 元素（字节单位误判会立即产生 O(1) 垃圾值 FAIL）；Init 表因此去掉 ShiftLefts(2)，与 UB 级 AscendC::Gather 内部的隐式 ShiftRights(2) 等价",
    "寄存器压力是主要回退形态：若编译器 spill，流水签名会表现为 vec/mte 不降反升；本 run 未出现 spill 指纹（aiv_vec 组内 -76.7%~-77.6%、aiv_scalar -44.2%~-47.4%、mte2/mte3 不变）",
    "vrowSlab UB 缓冲与 slabRegOk_ 守卫（in + out + 16*wElem*4B <= 128KB）是快臂的准入条件：UB 预算不足时回退到逐行臂；两条臂必须保持同一数学序列，否则只有部分形状位级一致",
    "收益量级远超预期（预期 1.15-1.3x、实际 2.96x）说明往返类 v-insn 的真实成本权重远高于条数占比：反过来，若目标算子的往返类指令占比不大、或数学指令本身已主导发射，同一机制不会给出同等收益"
  ],
  "slug": "register-resident-gather-operands",
  "summary": "把行无关的 gather 操作数（u32 元素索引 idx0/idx1、lx 权重、满 mask）从『每行每 tile 从 UB 重取』改为跨行寄存器驻留，水平混合从 UB 级 AscendC::Gather（LoadAlign 索引表 + vgather2 + StoreAlign 结果回 UB，再被 HBlend LoadAlign 回读 g0/g1/lx）换成 Reg 级 Reg::Gather（vgather2、dst 直出寄存器、索引/mask 为寄存器操作数）加 Sub + MulDstAdd + Cast 的内联融合；ProcessSlab 改为 tile 外层/行内层，VB 行预写 vrowSlab，每 tile 的操作数寄存器供 16 行复用。全测试口径 kernel geomean 194.251 → 65.712us（2.956x）；正式 ABBA 4 对 pooled 193.670 → 65.369us（speedup 2.9625，逐对 2.9588-2.9662，区间完全不重叠），aiv_vec 179 → 41.8us、aiv_scalar 122.6 → 64.6us、mte2/mte3 不变，20/20 PASS 且元素选择与数学指令与 champion 代码等价。",
  "verification": {
    "correctness": [
      "20/20 PASS 首次通过（0 次修复）；元素选择与全部数学指令（Muls/Axpy/Sub/MulDstAdd/Cast）及操作数值与 champion 代码等价（vgather2 元素索引 = 字节偏移/4 精确等价），预期位级一致（难度对照：若 vgather2 的索引单位被误判为字节，会立即产生 O(1) 垃圾值而 FAIL，不会以容差内偏差的形式出现）",
      "设备侧核实 vgather2 B32 索引单位 = u32 元素：字节单位误判会立即产生 O(1) 垃圾值并 FAIL；测试输入为无种子随机生成，跨 run MERE 数值不可比，以阈值门（fp16 T=2^-10 / bf16 T=2^-7 / fp32 T=2^-13 + 三区兜底）为准",
      "编译经 1 次修复通过：attempt 1 因 __simd_vf__ 函数不接受 RegTensor 引用参数失败（pointer arguments to simd_vf functions must reside in '__ubuf__'），改为宏内联展开后 attempt 2 通过"
    ],
    "performance": [
      "全测试口径 kernel geomean 194.251 → 65.712us（ratio_geomean 0.3382，speedup 2.956，improvement 66.2%）；3 dtype 均值 upsample_bf16 195.461 → 65.478us、fp16 196.219 → 66.255us、fp32 191.112 → 65.406us",
      "正式 ABBA 4 对 / 24 次测量（顺序 A,B,B,A,A,B,B,A，单位 run×case、每 run 14 launches；A=冻结基线重编 module sha 5d06942c、B=候选 module sha 2a4ec097，双目录同模块名 _upsample_ext 子进程交替加载）：A pooled 193.670 → B pooled 65.369us，speedup 2.9625，逐对 speedup 2.9588-2.9662（spread 0.25%），A run geomean 区间 [193.628,193.721] 与 B 区间 [65.301,65.444] 完全不重叠",
      "流水签名：aiv_vec 179 → 41.8us（bf16/fp16）/ 175.3 → 39.3us（fp32），组内 -76.7% / -76.7% / -77.6%；aiv_scalar 122.6 → 64.6us（-44.2%~-47.4%）；aiv_mte2 不变（约 22us 全测试冷上下文）、aiv_mte3 不变（约 7us）——无 spill 指纹",
      "量级对照：方向保守预期 1.15-1.3x 被大幅超越（实际 2.96x），说明往返类 v-insn 的真实成本权重远高于条数占比（vec 管受 LSU/发射吞吐约束而非条数约束），纯删除型机制转化约 1:1.6，与 direction_002 融合 MAC 的约 1:0.12 形成对照"
    ],
    "rollback_signals": [
      "出现寄存器 spill 指纹：aiv_vec/mte 不降反升，或 aiv_time 未随 aiv_vec 下降",
      "mte2/mte3 上升：说明 VB 预写 vrowSlab 引入了新的搬运（本 run 预期并实测 mte 维持不变）",
      "任一 case 的 vgather2 元素选择或数学指令序列与 champion 不再代码等价（位级一致被破坏）",
      "UB 预算守卫（slabRegOk_）失效导致快臂在大形状下越界，或快臂与逐行臂的结果不一致"
    ]
  }
}
-->

# 性能优化策略：gather 操作数寄存器驻留：tile 外层跨行复用 + Reg::Gather dst 直出

把行无关的 gather 操作数（u32 元素索引 idx0/idx1、lx 权重、满 mask）从『每行每 tile 从 UB 重取』改为跨行寄存器驻留，水平混合从 UB 级 AscendC::Gather（LoadAlign 索引表 + vgather2 + StoreAlign 结果回 UB，再被 HBlend LoadAlign 回读 g0/g1/lx）换成 Reg 级 Reg::Gather（vgather2、dst 直出寄存器、索引/mask 为寄存器操作数）加 Sub + MulDstAdd + Cast 的内联融合；ProcessSlab 改为 tile 外层/行内层，VB 行预写 vrowSlab，每 tile 的操作数寄存器供 16 行复用。全测试口径 kernel geomean 194.251 → 65.712us（2.956x）；正式 ABBA 4 对 pooled 193.670 → 65.369us（speedup 2.9625，逐对 2.9588-2.9662，区间完全不重叠），aiv_vec 179 → 41.8us、aiv_scalar 122.6 → 64.6us、mte2/mte3 不变，20/20 PASS 且元素选择与数学指令与 champion 代码等价。

## 1. 原理

在 vec_ratio=0.92、mte 已重叠到 <4% 的算子上，唯一杠杆是减少 vec 管发射；但发射里占比最大的一类不是数学指令，而是行无关操作数的取数往返——索引表、权重、掩码每行每 tile 从 UB 重取，UB 级 Gather 又把 gather 结果写回 UB 再读回，随后 HBlend 再 LoadAlign 回读 g0/g1/lx。这类 v-insn 的条数占比不等于成本占比：LoadAlign/StoreAlign/UpdateMask 受 LSU/发射吞吐约束，真实权重远高于条数占比（本 run 最终兑现 2.96x，远超保守预期的 1.15-1.3x，而 direction_002 把便宜指令换成更贵融合 MAC 的转化率仅约 1:0.12）。因此正确做法是纯删除加驻留：把行无关操作数提升为跨行存活的寄存器、把 gather 从 UB tensor API 换成 dst 直出寄存器的 Reg::Gather，使每个 tile 只装载一次操作数供全部 768 行复用。数学指令（Muls/Axpy/Sub/MulDstAdd/Cast）与 vgather2 的元素选择逐位不变，正确性风险只剩寄存器压力与索引单位两处。与之对照：covh-init-precompute-ub-resident 把表常驻 UB 但仍逐行读（没消除往返）；small-matrix-register-residency 没有 gather 操作数、也没有 Reg::Gather 的 dst 直出融合；in-register-s-forwarding 消除的是逐元素中间量的 UB store→reload 往返，不是 gather 操作数表。

实现机制：register-resident-gather-operands。结构上把 ProcessSlab 的行×tile 循环改为 tile 外层 / 行内层：VB 输出行预写 vrowSlab UB 缓冲供 vgather2 取数，off0Reg/off1Reg/lxReg/mask 每 (slab 批,tile) 只装载一次、供 16 行复用；slabRegOk_ 守卫（in + out + 16*wElem*4B <= 128KB）决定热路径走快臂还是回退。水平混合从 UB tensor API AscendC::Gather 换成 Reg 级 Reg::Gather（vgather2，dst 直接进寄存器、索引与 mask 均为寄存器操作数）加 Sub + MulDstAdd + Cast/Store 的内联融合序列（UPSAMPLE_GATHER_BLEND_REPEAT 宏），从而去掉 gather 结果的 UB 写+读往返、索引表与 lx 的重复 LoadAlign、以及逐调用 UpdateMask。Init 表改存 u32 元素索引（去 ShiftLefts(2)），与 UB 级 AscendC::Gather 内部的隐式 ShiftRights(2) 等价，vgather2 的元素选择位级不变；g0Buf_/g1Buf_ 与全部 UB 级 AscendC::Gather 调用点被移除。逐行回退臂与 slab 慢臂共用 GatherBlendTileRegImpl，与快臂保持同一数学序列（Muls/Axpy/Sub/MulDstAdd/Cast），因此逐行路径也位级一致。实现坑：__simd_vf__ 函数不接受 RegTensor 引用参数（指针参数必须落在 __ubuf__），跨 repeat 复用寄存器操作数必须在单一 __simd_vf__ 作用域内用宏内联展开（本 run 唯一一次编译修复）。

## 2. 性能问题模式

- 优化目标：消除逐行重复付出的操作数取数往返：行无关的 gather 操作数（u32 元素索引 idx0/idx1、lx 权重、满 mask）被每 (行,tile,repeat) 从 UB 重取，水平混合又走 UB 级 AscendC::Gather（每次调用 LoadAlign 索引表 + vgather2 + StoreAlign 结果回 UB），随后 HBlend 再 LoadAlign 回读 g0/g1/lx 并逐调用 UpdateMask——本 run 每行 ~44 条纯搬运/设置类 v-insn（索引 LoadAlign×8、ShiftRights×8、gather 结果 Store+Load×16、lx LoadAlign×4、UpdateMask×8）全是行无关量被逐行重做。
- 适用数据流：逐行/按 slab 处理、每行重复取用行无关操作数表（索引、权重、掩码）、且水平混合走 UB 级 gather 的元素级/插值类算子；本 run 为 task_0363_upsample（ascend950dt_9582，真实 shape [64,3,128,128] sf=2、totalRows=49152、blockDim=64 → 768 行/核，bilinear align_corners=True、ry=127/255）
- Feature signature：`{"bottleneck": ["vec-operand-roundtrip", "row-invariant-gather-operand-refetch", "gather-result-ub-store-reload"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "register-resident-gather-operands", "reduce_mode": "", "structure": ["register-resident-gather-operand-table", "reg-level-vgather2-dst-register", "tile-outer-row-inner-loop", "vrowslab-ub-prewrite", "bitwise-identical-element-selection"]}`

## 3. 正确性红线

- __simd_vf__ 函数不接受 RegTensor 引用参数（指针参数必须落在 __ubuf__）：跨 repeat 复用寄存器操作数必须在单一 __simd_vf__ 作用域内用宏内联展开——本 run 唯一一次编译修复（attempt 1 失败、attempt 2 通过），把融合 repeat 体展开为 UPSAMPLE_GATHER_BLEND_REPEAT 宏
- vgather2 的索引单位必须设备侧核实：本 run 20/20 同时证明 B32 索引单位是 u32 元素（字节单位误判会立即产生 O(1) 垃圾值 FAIL）；Init 表因此去掉 ShiftLefts(2)，与 UB 级 AscendC::Gather 内部的隐式 ShiftRights(2) 等价
- 寄存器压力是主要回退形态：若编译器 spill，流水签名会表现为 vec/mte 不降反升；本 run 未出现 spill 指纹（aiv_vec 组内 -76.7%~-77.6%、aiv_scalar -44.2%~-47.4%、mte2/mte3 不变）
- vrowSlab UB 缓冲与 slabRegOk_ 守卫（in + out + 16*wElem*4B <= 128KB）是快臂的准入条件：UB 预算不足时回退到逐行臂；两条臂必须保持同一数学序列，否则只有部分形状位级一致
- 收益量级远超预期（预期 1.15-1.3x、实际 2.96x）说明往返类 v-insn 的真实成本权重远高于条数占比：反过来，若目标算子的往返类指令占比不大、或数学指令本身已主导发射，同一机制不会给出同等收益

资源与硬件约束：

- gather 操作数必须是行无关且跨行可复用的（本 run：u32 元素索引 idx0/idx1、lx 权重、满 mask 在全部 768 行上相同）——行相关操作数不能寄存器驻留
- Reg::Gather 要求 dst 为寄存器、index/mask 为寄存器操作数，且 B32 源配 u32 索引：改表语义（ShiftLefts/ShiftRights）时必须与 UB 级 AscendC::Gather 的隐式转换对齐（本 run 表改存 u32 元素索引，与 UB 级内部 ShiftRights(2) 等价）
- 寄存器操作数只能在一个 __simd_vf__ 作用域内跨 repeat 存活：__simd_vf__ 函数不接受 RegTensor 引用参数（指针参数必须落在 __ubuf__），跨 repeat 复用必须宏内联展开融合体
- 快臂的 UB 预算守卫必须显式（本 run slabRegOk_：in + out + 16*wElem*4B <= 128KB），并保留逐行回退臂；两条臂共用同一内联序列以保证位级一致

## 4. 泛化条件

- 策略作用域：op_class：upsample-interpolate

适用：

- vec 管是唯一主导瓶颈且 mte 已充分重叠：本 run champion 双上下文 profiling 稳定，aiv_vec 179.33/179.31/175.10us（vec_ratio 全部 0.92），aiv_scalar 122.53/122.59/115.51us，aiv_mte2 全测试 20.7-22.8us（热张量 ABBA 口径仅 7.1-7.4us）、aiv_mte3 5.8-8.1us——aiv_time ≈ vec + 11-16us，scalar 大部分被 vec 掩盖
- 存在被每 (行,tile,repeat) 重复取用的行无关操作数表：本 run 每行 ~44 条纯搬运/设置类 v-insn（索引 LoadAlign×8、ShiftRights×8、gather 结果 Store+Load×16、lx LoadAlign×4、UpdateMask×8），全是行无关量被逐行重做
- 目标 API 组合存在：CANN 9.1.0 dav_3510 头文件证实 UB 级 AscendC::Gather 展开为每 repeat UpdateMask + LoadAlign(offsetReg) + vgather2 + StoreAlign(结果回 UB)（kernel_operator_vec_gather_impl.h），且 Reg 级 AscendC::Reg::Gather(dstReg, baseAddr, indexReg, mask) 存在（kernel_reg_compute_datacopy_intf_impl.h:368 → DataCopyGatherImpl → vgather2，dst=寄存器、index/mask=寄存器操作数，vector_float 覆盖，B32 源配 u32 索引；asc_gather_impl.h）
- 循环结构可重排为 tile 外层/行内层使操作数寄存器跨行存活：本 run ProcessSlab 的行×tile 循环可按 tile 分片驻留索引寄存器，VB 输出落 vrowSlab UB 供 vgather2 取数（真实 shape [64,3,128,128] sf=2 → totalRows=49152、blockDim=64 → 768 行/核；bilinear align_corners=True、ry=127/255）

不适用：

- 操作数行相关（每行不同）时不能驻留：跨行复用是收益来源
- aiv_scalar 而非 aiv_vec 是节拍源时不适用：本机制删除的是 vec 管上的取数往返发射，scalar 主导的算子无可回收对象（本 run 后继瓶颈已转为 aiv_scalar 64.6us，aiv_time ≈ scalar + 1us）
- 已把表常驻 UB 但仍逐行读的形态（covh-init-precompute-ub-resident）不属于本机制：本机制消除的正是逐行读
- 没有 gather 操作数、也不存在 Reg::Gather dst 直出融合的场景（small-matrix-register-residency），以及消除逐元素中间量 UB store→reload 往返的场景（in-register-s-forwarding）都不属于本机制：本机制消除的是 gather 操作数表与 gather 结果的取数往返

## 5. 实施步骤

1. Init 期把索引表改为 u32 元素索引（idx0All/idx1All，去 ShiftLefts(2)），新增 vrowSlabBuf_ 与 slabRegOk_ 守卫（in + out + 16*wElem*4B <= 128KB），移除 g0Buf_/g1Buf_
2. 新增 UPSAMPLE_GATHER_BLEND_REPEAT 内联序列（Reg::Gather ×2 + Sub + MulDstAdd + Cast/StoreAlign）与 GatherBlendTileRegImpl（per-tile 装载变体，逐行臂与 slab 慢臂共用）
3. 新增 BlendSlabTileOuterRegImpl：把 ProcessSlab 的行×tile 循环改为 tile 外层/行内层，VB 行预写 vrowSlab 后 off0Reg/off1Reg/lxReg/mask 每 (slab 批,tile) 只装载一次、供 16 行复用
4. 删除全部 UB 级 AscendC::Gather 调用点，使快臂/慢臂/逐行臂都走同一内联融合序列（数学指令 Muls/Axpy/Sub/MulDstAdd/Cast 与 vgather2 元素选择不变）
5. 以位级等价的精度门（20/20 首次通过，含 vgather2 索引单位的设备侧核实）与 4 对平衡交替 ABBA 的 profile 签名验收：预期 aiv_vec / aiv_scalar 显著下降、mte2/mte3 不升；出现 spill 指纹（vec/mte 不降反升）即回退

## 6. LLM 前置问题

- 目标实现是否满足：vec 管是唯一主导瓶颈且 mte 已充分重叠（本 run aiv_vec 175-179us、vec_ratio 全部 0.92，aiv_time ≈ vec + 11-16us）？
- 目标实现是否满足：存在被每 (行,tile,repeat) 重复取用的行无关操作数表（本 run 每行 ~44 条纯搬运/设置类 v-insn）？
- 目标实现是否满足：目标 API 组合存在（CANN 9.1.0 dav_3510 的 Reg::Gather → DataCopyGatherImpl → vgather2，dst 寄存器直出；UB 级 AscendC::Gather 展开含 StoreAlign 回 UB）？
- 目标实现是否满足：循环结构可重排为 tile 外层/行内层，使操作数寄存器跨行存活（本 run 768 行/核）？
- 是否命中排除条件：操作数行相关时不适用？
- 是否命中排除条件：aiv_scalar 而非 aiv_vec 是节拍源时不适用？
- 是否命中排除条件：已把表常驻 UB 但仍逐行读（covh-init-precompute-ub-resident）时不属于本机制？
- 是否命中排除条件：无 gather 操作数/无 Reg::Gather dst 直出融合（small-matrix-register-residency）、或消除的是逐元素中间量 store→reload 往返（in-register-s-forwarding）时不属于本机制？

## 7. 验收标准

正确性：

- 20/20 PASS 首次通过（0 次修复）；元素选择与全部数学指令（Muls/Axpy/Sub/MulDstAdd/Cast）及操作数值与 champion 代码等价（vgather2 元素索引 = 字节偏移/4 精确等价），预期位级一致（难度对照：若 vgather2 的索引单位被误判为字节，会立即产生 O(1) 垃圾值而 FAIL，不会以容差内偏差的形式出现）
- 设备侧核实 vgather2 B32 索引单位 = u32 元素：字节单位误判会立即产生 O(1) 垃圾值并 FAIL；测试输入为无种子随机生成，跨 run MERE 数值不可比，以阈值门（fp16 T=2^-10 / bf16 T=2^-7 / fp32 T=2^-13 + 三区兜底）为准
- 编译经 1 次修复通过：attempt 1 因 __simd_vf__ 函数不接受 RegTensor 引用参数失败（pointer arguments to simd_vf functions must reside in '__ubuf__'），改为宏内联展开后 attempt 2 通过

性能：

- 全测试口径 kernel geomean 194.251 → 65.712us（ratio_geomean 0.3382，speedup 2.956，improvement 66.2%）；3 dtype 均值 upsample_bf16 195.461 → 65.478us、fp16 196.219 → 66.255us、fp32 191.112 → 65.406us
- 正式 ABBA 4 对 / 24 次测量（顺序 A,B,B,A,A,B,B,A，单位 run×case、每 run 14 launches；A=冻结基线重编 module sha 5d06942c、B=候选 module sha 2a4ec097，双目录同模块名 _upsample_ext 子进程交替加载）：A pooled 193.670 → B pooled 65.369us，speedup 2.9625，逐对 speedup 2.9588-2.9662（spread 0.25%），A run geomean 区间 [193.628,193.721] 与 B 区间 [65.301,65.444] 完全不重叠
- 流水签名：aiv_vec 179 → 41.8us（bf16/fp16）/ 175.3 → 39.3us（fp32），组内 -76.7% / -76.7% / -77.6%；aiv_scalar 122.6 → 64.6us（-44.2%~-47.4%）；aiv_mte2 不变（约 22us 全测试冷上下文）、aiv_mte3 不变（约 7us）——无 spill 指纹
- 量级对照：方向保守预期 1.15-1.3x 被大幅超越（实际 2.96x），说明往返类 v-insn 的真实成本权重远高于条数占比（vec 管受 LSU/发射吞吐约束而非条数约束），纯删除型机制转化约 1:1.6，与 direction_002 融合 MAC 的约 1:0.12 形成对照

回滚信号：

- 出现寄存器 spill 指纹：aiv_vec/mte 不降反升，或 aiv_time 未随 aiv_vec 下降
- mte2/mte3 上升：说明 VB 预写 vrowSlab 引入了新的搬运（本 run 预期并实测 mte 维持不变）
- 任一 case 的 vgather2 元素选择或数学指令序列与 champion 不再代码等价（位级一致被破坏）
- UB 预算守卫（slabRegOk_）失效导致快臂在大形状下越界，或快臂与逐行臂的结果不一致

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：covh-init-precompute-ub-resident, small-matrix-register-residency, in-register-s-forwarding

- loop_20260915_161957（round=01, status=accepted, speedup=2.9625, precision=20/20 PASS（首次通过，0 次修复；同时设备侧核实 vgather2 B32 索引单位=u32 元素，元素选择与全部数学指令及操作数值与 champion 代码等价、预期位级一致））

## 检索卡（短卡）

动作：把行无关的操作数表从逐行从UB重取改为跨行寄存器驻留，gather改为dst直出寄存器并融合，循环重排为tile外层、行内层
适用：vec管唯一主导且mte已充分重叠；存在被每(行,tile)重取的行无关操作数表；循环可重排为tile外层/行内层
限制：复用寄存器须同一__simd_vf__宏内联；索引单位须为u32元素；UB预算(in+out+16*wElem*4B<=128KB)不足回退逐行臂
范围：逐行/按slab处理、重复取用行无关操作数表的元素级插值类算子
检索词：Reg::Gather、vgather2、RegTensor、__simd_vf__、UpdateMask、LoadAlign
机会：vec管主导且mte已重叠：每行约44条行无关量的搬运/设置类v-insn被逐行重做
代价：寄存器压力引发spill时vec/mte不降反升；vrowSlab预写可能抬高mte2/mte3
