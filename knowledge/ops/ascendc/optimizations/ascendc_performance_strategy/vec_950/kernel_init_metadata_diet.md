---
type: Optimization
title: 内核入口元数据瘦身：按 kernel 分档 tiling 复制 + host 预计算与片上同式重导出 + 入口 icode 收缩
description: 把 kernel Init 的整结构体 tiling 逐字节复制改为按消费字段的有界字粒度复制，host 预计算与片上同式重导出。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/kernel-init-metadata-diet.md
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
      "本工具链上 plain __gm__ 标量装载宽度必须 <= 4B：avgpool1d round-1 的 8B 形态（6×uint64 + 1×uint32 tiling 复制）实测精度 0/20——8B plain __gm__ 标量装载静默损坏 tiling 读、kernel 提前退出，且诊断探针显示其 -64% 是工作被跳过的假象；round-2 的 13×uint32 才通过 20/20 且 MERE/MARE 与 champion 相同",
      "片上重导出必须与 host 使用完全相同的整数/浮点表达式才能逐位一致：boxElemCap/rowsPerBlock 走 host 同公式整数预计算（boxElemCap=maxWd*maxWh*rowStride+128、rowsPerBlock 按 poolBlockDim=min(64,totalRows)），invW/wStart/wEnd 用与 host FillTiling 相同的整数除法与 float 转换/除法表达式，不得简化 ceil 公式或 ww=max(ew-sw,1)",
      "有界复制的字节上限必须按各 kernel 实际消费字段的偏移界定，并随调用点显式传入：ELU 侧 offsetof(EluAdaptiveAvgPool3dTiling, totalRows)=16B、pool 侧 offsetof(EluAdaptiveAvgPool3dTiling, invW)=60B；invW/wStart/wEnd 的 GM 直读路径、数值路径、Op Name、tiling 结构与 host 侧均未改动",
      "avgpool1d 侧 host（kernel/pybind11.cpp）与 tiling/分区不变，avgpool1d_tiling.h 结构在回退 round-1 的 alignas(8) 实验后保持原样；runtime-k 化必须保住 champion 的 j 序 gather/add 逐 lane 算术，PipeBarrier 与队列机制原位保留"
    ],
    "excluded_conditions": [
      "tiling 复制本来就是字粒度/有界，或 kernel 确实消费整个结构体时，没有可裁剪的复制载荷",
      "标量管不是节拍源时不适用（例如 mte2/vec 主导）：本机制不减少任何一条向量/MTE 指令，只削 Init/entry 的标量发射与取指",
      "per-launch 固定成本主要来自 launch/block-dispatch 机制而非代码镜像时不适用：avgpool1d d003 的 round-1 零工作探针证明 ~8.7us 标量截距大部分在镜像之外（64-block 零工作 launch 仍 8.1-9.1us device / 8.1-8.7us scalar），本机制只能拿到 icache/装载数那一份——实测 1.0300x，而非 projected 的 -12..-20%",
      "结构性语义不同的 Init 面不在本机制作用域内：InitBuffer/GetPhyAddr 的组织是 init-buffer-pool-consolidation 的域，host 静态恒等判定与 UB 预算重平衡是 host-gated-cheap-path 的域，把整个 tiling 改成 launch 按值参数（删 GM 读路径与每调用 H2D）是 launch-arg-by-value-tiling-fetch-elimination 的域"
    ],
    "required_conditions": [
      "标量管是 pacing pipe 且 Init/entry 是 per-launch 固定项：eluadaptiveavgpool3d 的 pool kernel aiv_scalar_time≈8.03-8.12us、aiv_vec≈0.25-0.29us、aiv_mte2≈0.16-0.31us、aiv_mte3≈0.2us（标量约占 kernel 时长 90%），elu kernel aiv_scalar_time=8.089us 与 pool kernel 相当；direction_001 采纳后 pool kernel aiv_scalar_time 仍有 ~2.75-3.0us（占比 ~76-78%），elu kernel ~1.24-1.5us",
      "tiling 结构体按字节循环整体复制、且远大于任一 kernel 实际消费的字段：eluadaptiveavgpool3d 的结构为 15×uint32 头（60B）+ invW/wStart/wEnd[64]×float（768B），数组占 93% 字节，EluAAP3dCopyTiling 对 sizeof=828 字节逐字节 GM 标量复制；avgpool1d 的 AvgPool1dCopyTiling 每核 Init 从 GM 逐字节复制 sizeof(AvgPool1dTiling)=52 字节，即 52 次标量 GM 装载/launch/核",
      "存在 host 已算过或可零成本预算、而 kernel 片上重算的派生几何量：boxElemCap 在 host 已算过 maxWh*rowStride+128 但漏了 maxWd 因子，kernel 被迫用两个 EluAAP3dMaxWindow 循环（D_out+H_out 次迭代、每迭代 2 次整数除法）重导出框容量；rowsPerBlock=CeilDiv(totalRows,blockNum) 每核一次整数除法，而 host 在 run_elu_adaptive_avg_pool3d 中本就计算 poolBlockDim",
      "存在可由已装载字段同式重导出的表：invW/wStart/wEnd 完全由 W_in/W_out 决定，host FillTiling 的公式与 kernel 可用的整数/浮点表达式一致（sw=(ow*W_in)/W_out、ew=ceil、ww=max(ew-sw,1)、invW=1.0f/(float)ww），而原实现按 3*W_out 次逐元素 GM 标量读把三张表搬入 UB 并配 PipeBarrier<PIPE_ALL>",
      "入口代码体积可收缩且冷取指确实被付掉：avgpool1d 每个 dtype entry 都实例化完整的 7 k × CIP{0,1} 模板扇出（AvgPool1dTileKDispatch -> AvgPool1dTileSegments -> FastVF/EmitBlocks 内联 VF 体），icache_miss 短 case 0.03-0.168 vs 长 case 0.005-0.018"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "eluadaptiveavgpool3d",
      "operator_class": "pool",
      "precision": "20/20 PASS（与基线逐位一致）",
      "run_id": "<run-id>",
      "speedup": 3.1307,
      "status": "accepted"
    },
    {
      "operator": "eluadaptiveavgpool3d",
      "operator_class": "pool",
      "precision": "20/20 PASS（round-1/round-2 均一次通过，与基线逐位一致）",
      "run_id": "<run-id>",
      "speedup": 1.1495,
      "status": "accepted"
    },
    {
      "operator": "avgpool1d",
      "operator_class": "pool",
      "precision": "20/20 PASS（MERE/MARE 与 champion 基线一致；round-1 的 8B 装载形态 0/20 已证伪）",
      "run_id": "<run-id>",
      "speedup": 1.03,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "kernel-init-fixed-cost",
      "per-launch-gm-tiling-fetch",
      "byteswise-scalar-tiling-copy",
      "host-recomputable-init-scalar",
      "cold-icode-fetch-floor"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "kernel-entry-metadata-diet",
    "reduce_mode": "",
    "structure": [
      "per-kernel-bounded-tiling-copy",
      "word-granular-scalar-copy",
      "host-precomputed-derived-fields",
      "onchip-identical-formula-rederivation",
      "runtime-k-emission-chain-collapse",
      "icache-footprint-diet"
    ]
  },
  "generality": "op_class",
  "id": "KERNEL-ENTRY-METADATA-DIET",
  "implementation_steps": [
    "按 kernel 清点 tiling 字段的消费面与偏移：ELU kernel 只读 totalLength/blockLength/tileLength（前 12 字节），pool kernel 只读字节 20..60（totalRows/rowStride/N/C/D_in/H_in/W_in/D_out/H_out/W_out），并确认 invW/wStart/wEnd 是另外三张 GM 表、boxElemCap/totalLength/blockLength/tileLength/eluBufLength 在该路径未使用",
    "把 EluAAP3dCopyTiling 改成带 bytes 上限的 uint32 字粒度复制循环，两个调用点分别传 offsetof(..., totalRows)=16B（4 次字加载）与 offsetof(..., invW)=60B（15 次字加载）；avgpool1d 侧把 AvgPool1dCopyTiling 的 52 次逐字节装载换成 13×uint32（#pragma unroll）",
    "host 侧补全派生量：kernel/pybind11.cpp 用与 kernel 原公式逐字一致的 MaxWindowU32 计算 boxElemCap=maxWd*maxWh*rowStride+128，按 poolBlockDim=min(64,totalRows) 预计算 rowsPerBlock，并在 EluAdaptiveAvgPool3dTiling 尾部新增 rowsPerBlock 字段",
    "pool Init 删除两个 EluAAP3dMaxWindow 循环与 CeilDiv(totalRows,blockNum)，改读 tiling_.boxElemCap/tiling_.rowsPerBlock；invW/wStart/wEnd 改片上同式推导并删除 sSrc/eSrc/iSrc 的 3*W_out 次 GM 标量装载循环（保留 PipeBarrier<PIPE_ALL> 与队列机制）；round-2 删除已死的 768B GM 表数组（tiling 832->64B），ELU kernel 零改动",
    "avgpool1d 侧去掉 emission body 的 KernelSize 模板参量（k 改为运行期传入）、删除 7 路 per-tile k if-chain 与死 DivIsK 体，使 emission 链 28->4；以逐 case MERE/MARE 与冻结基线逐位一致 + 平衡交替 ABBA 配对（无 case 回退）验收，任一精度失败或未补偿回退即回滚"
  ],
  "intent": "消除每核每 launch 都要付的 kernel Init/entry 固定标量成本中可裁剪的部分：828B（eluadaptiveavgpool3d）/52B（avgpool1d）tiling 的逐字节 GM 标量复制、pool Init 的 8-13 次整数除法循环 + 3*W_out 次逐元素 GM 标量表装载 + 1 次 rowsPerBlock 除法，以及每次 launch 都要取指的 7 路 k emission 链冷 icode（短 case icache_miss 0.03-0.168）。",
  "mechanism": "kernel-entry-metadata-diet 三个分量，全部只动 Init/entry 标量面，不改数值路径、累加顺序与 tiling/分区。(a) 按 kernel 分档的有界 tiling 复制——EluAAP3dCopyTiling 增加 bytes 上限参数并改为 uint32 字粒度复制循环，ELU kernel 传 offsetof(EluAdaptiveAvgPool3dTiling, totalRows)（仅 16B/4 次字加载），pool kernel 传 offsetof(EluAdaptiveAvgPool3dTiling, invW)（仅 60B/15 次字加载）；原实现是 sizeof(EluAdaptiveAvgPool3dTiling)=828 字节逐字节 GM 标量复制，两个 kernel 的 Init 都无条件调用；方向文档给出的载荷下界估计为 ELU≈16B、pool≈44B，落地实现形态为 16B/60B。avgpool1d 的 AvgPool1dCopyTiling 把 52 次逐字节 GM 装载换成 13×uint32（#pragma unroll，champion 证明的 4B plain __gm__ 宽度）。(b) host 预计算 + 片上同式重导出——kernel/pybind11.cpp 用与 kernel 原公式逐字一致的 MaxWindowU32 helper 把 boxElemCap 补全为 maxWd*maxWh*rowStride+128，并按 poolBlockDim=min(64,totalRows) 预计算 rowsPerBlock 写入 tiling（作为 EluAdaptiveAvgPool3dTiling 尾部新增字段）；pool Init 删除两个 EluAAP3dMaxWindow 循环（D_out+H_out 次迭代、每迭代 2 次整数除法）与 CeilDiv(totalRows,blockNum)，改读 tiling_.boxElemCap/tiling_.rowsPerBlock；invW/wStart/wEnd 改片上推导（sw=(ow*W_in)/W_out、ew=ceil 公式、ww=max(ew-sw,1)、invW=1.0f/(float)ww，与 host FillTiling 逐位一致），删除 sSrc/eSrc/iSrc 三张表按 3*W_out 次逐元素 GM 标量读的装载循环（PipeBarrier<PIPE_ALL> 与队列机制原样保留）；round-2 进一步删除已死的 768B GM 表数组（tiling 832->64B），elu kernel 零改动。(c) entry icode 收缩（avgpool1d）——emission body 去掉 KernelSize 模板参量（k 改为运行期 int32_t 传入），删除 7 路 per-tile k if-chain（AvgPool1dTileKDispatch）与已死的 DivIsK=true 通用体，镜像内 emission 链由 7 k × 2 CIP × 2 dtype = 28 条收敛为 2 CIP × 2 dtype = 4 条，.so 9688576 -> 9217544 字节，短 case 的 aiv_icache_miss_rate 塌缩（case_11 0.168->0.003、case_14 0.134->0.024、case_07 0.088->0.012），j 序 gather/add 逐 lane 算术保持 champion 不变。",
  "name": "内核入口元数据瘦身：按 kernel 分档 tiling 复制 + host 预计算与片上同式重导出 + 入口 icode 收缩",
  "operator_class": "pool",
  "operator_scope": "kernel Init/entry 在每核每 launch 付固定标量成本、tiling 结构体远大于各 kernel 实际消费字段、且其中含 host 已算/可零成本预算或可由已装载字段同式重导出的派生量的算子；典型如池化家族的 eluadaptiveavgpool3d（elu 与 pool 两个 pass，828B tiling、pool kernel Block Num=4-9）与 avgpool1d（52B tiling + 7×2 k/CIP 模板扇出、Block Num=64）",
  "principle": "当标量管是 pacing pipe 时，per-launch 的 kernel Init/entry 固定标量成本直接决定每个 case 的地板，而与数据量无关：eluadaptiveavgpool3d 的 pool kernel aiv_scalar_time≈8.03-8.12us，而 aiv_vec≈0.25-0.29us、aiv_mte2≈0.16-0.31us、aiv_mte3≈0.2us（标量约占 kernel 时长 90%），测试 case 又极小（如 case1 N1C1 6×6×8→288 元素、totalRows=4，kernel 实际向量/MTE 工作量 <0.6us，Task Duration ~8.5-9.6us 几乎全是固定开销）；elu kernel 的 aiv_scalar_time=8.089us 与 pool kernel 相当，说明两个 kernel 共享同一固定标量开销模式。avgpool1d 侧在其 d002 之后 scalar_t 是 16/20 个 case 的最大流水项（suite 级标量份额 43-88%），且可拟合为 INTERCEPT(~8.7us) + ~0.09us/row + ~0.25us/tile——一个 d001（host blockDim）与 d002（per-row/per-tile 队列事件摊销）都没碰过的 per-launch 固定项。这笔固定成本由三部分组成，且三部分都能在不改数值路径的前提下削减：(a) tiling 结构体的逐字节标量 GM 复制，而结构体里 93% 的字节是 invW/wStart/wEnd[64] 数组，没有任何 kernel 读完；(b) kernel 片上重算 host 早已算过、或可由已装载字段同式重导出的派生量；(c) entry 路径每次 launch 都要付的冷 icode 取指（icache_miss 短 case 0.03-0.168 vs 长 case 0.005-0.018）。这是与 init-buffer-pool-consolidation（削 InitBuffer/GetPhyAddr 描述符数量与组织）与 host-gated-cheap-path（host 静态判定的恒等条件编码 + UB 预算按实际队列数重平衡）正交的第三个 Init 面：前两者都不覆盖 per-kernel tiling 复制载荷的裁剪、host 预计算/片上同式重导出、以及入口代码体积；launch-arg-by-value-tiling-fetch-elimination 虽然同样针对 tiling 获取，但它删的是整条 GM 读路径与 host 每调用 H2D（改成 launch 按值参数），本机制保留 GM tiling 读，只把每个 kernel 的复制载荷收缩到它真正消费的字段。avgpool1d 侧的先验诊断还给出了这条杠杆的上界：round-1 的零工作探针（64 block、全部 launch 平铺在 device 8.1-9.1us / scalar 8.1-8.7us）证明 ~8.7us 标量截距大部分是 launch/block-dispatch 机制而非代码镜像，本机制只能拿到 icache/装载数那一份。",
  "related_anti_patterns": [
    "init-buffer-pool-consolidation",
    "host-gated-cheap-path",
    "launch-arg-by-value-tiling-fetch-elimination"
  ],
  "risks": [
    "实现形态决定成败（装载宽度）：avgpool1d round-1 的 8B 形态 0/20，诊断探针进一步显示这个『-64%』是工作跳过假象（所有 launch 平铺 8-9us）；必须用 <=4B 的 plain __gm__ 宽度或显式 API，本 run 的可用形态是 13×uint32",
    "片上重导出与 host 表达式的逐位一致是隐式契约：任何一处公式简化（ceil、ww=max(ew-sw,1)、float 转换顺序）都只在部分 shape 上显形而破坏逐位一致；验收必须用逐 case MERE/MARE 与冻结基线逐位相同，而不是只看 20/20 通过数",
    "收益上界受 launch 机制约束：avgpool1d 零工作 64-block 探针测得 device 8.1-9.1us / scalar 8.1-8.7us，说明 ~8.7us 截距大部分不在代码镜像内，性能门会如实地停在约 1.03x；这不是机制反例，而是该方向的物理上界",
    "有界复制的上限与 kernel 实际消费字段脱节就会读到未初始化 tiling 字段：一旦某个 kernel 回头消费被裁掉的字段（如 pool 侧再读 boxElemCap/totalLength/blockLength/tileLength/eluBufLength），必须同步抬高该调用点的字节上限，而不是靠结构体整体复制兜底",
    "sub-1% 的布局噪声需与机制收益区分：round-1 配对里 elu 三 case 系统性 +0.3~1.2%（elu kernel 代码与设备代码未触碰、cycles +42/icache 相同），round-2 删除 768B 死数组后符号翻转（elu_fp16 +1.2% -> -2.6%），证实是 .so/数据布局噪声而非机制回归"
  ],
  "slug": "kernel-init-metadata-diet",
  "summary": "池化家族的 kernel Init/entry 在标量管上付一笔 per-launch 固定成本：eluadaptiveavgpool3d 的两个 kernel 各自把 828B 的 EluAdaptiveAvgPool3dTiling 逐字节从 GM 标量复制一遍（pool kernel aiv_scalar_time≈8.03-8.12us，约占 kernel 时长 90%），而 ELU kernel 只读前 12B、pool kernel 只读字节 20..60；avgpool1d 每核 Init 逐字节复制 52B tiling，entry 还带着 7 k × 2 CIP × 2 dtype = 28 条 emission 链的冷 icode。三个成员把这三笔固定成本分别削掉：按 kernel 分档的有界字粒度复制（16B/60B、13×uint32）、host 预计算（boxElemCap=maxWd*maxWh*rowStride+128、rowsPerBlock=CeilDiv(totalRows,blockNum)）与片上同式重导出（invW/wStart/wEnd，删 3*W_out 次 GM 标量表装载与 8-13 次整数除法循环）、以及 emission 链 28->4 的 icode 收缩（.so 9688576->9217544B，短 case icache_miss 0.168->0.003）。外层 msprof 平衡交替配对实测：eluadaptiveavgpool3d geomean 8.859->2.830us（3.1307x），其后再把 pool Init 的再计算削掉 2.827->2.460us（1.1495x，pool aiv_scalar -36%），avgpool1d 24.079->23.379us（1.0300x）；三者精度均与冻结基线逐位一致。",
  "verification": {
    "correctness": [
      "eluadaptiveavgpool3d direction_001：精度 20/20 PASS 且与基线逐位一致（bitwise_identical_to_baseline=true），编译 0 修复轮",
      "eluadaptiveavgpool3d direction_002：round-1 与 round-2 均一次通过 20/20 且与基线逐位一致；片上推导使用与 host FillTiling 完全相同的整数/浮点表达式，数值路径未触碰，elu kernel（Phase A）零改动",
      "avgpool1d direction_003：round-2 20/20，MERE/MARE 与 champion 基线一致；round-1 的 8B 装载形态 0/20 已归档为证伪子形态（诊断探针证明其降幅是工作跳过假象）",
      "三成员的改动均限定在 kernel Init/entry 路径（avgpool1d 侧 host 与 avgpool1d_tiling.h 未改），tiling 结构与 Op Name 不变"
    ],
    "performance": [
      "eluadaptiveavgpool3d direction_001：外层 msprof 4 对平衡交替 24/24 case 级比较一致向快，geomean 8.8595->2.8299us（pair geomean_ratio 0.3187-0.3207），elu aiv_scalar_time 8.0->1.3us、pool 8.1->2.9us；case 级 elu_bf16 8.550->1.897us、elu_fp16 8.681->1.995us、elu_fp32 8.547->1.894us、pool_bf16 9.143->4.109us、pool_fp16 9.138->4.211us、pool_fp32 9.123->4.139us",
      "eluadaptiveavgpool3d direction_002：4 对配对全部 candidate_faster（pair geomean_ratio 0.8691-0.8716），pool 12/12 case 级 -23.2~-24.7%，pool aiv_scalar_time 2.89-2.94 -> 1.82-1.90us（-36%），pool Task Duration 4.11-4.23 -> 3.11-3.21us（-24%），geomean 2.827->2.460us（1.1495x）；实测收益 ~1.05us 超出预估上限（预估 0.3-0.8us），elu 侧 <=1% 的布局噪声被两轮构建的符号翻转归因为非机制因素",
      "avgpool1d direction_003：形式化 ABBA suite-regime 5/5 对 candidate-faster（1.0273/1.0315/1.0307/1.0304/1.0299，mean 1.0300），20/20 case 全改善（最差 case_04 -0.6%，最好 case_07 -9.6%、case_06 -8.0%、case_10 -7.4%），短 case icache_miss 塌缩（case_11 0.168->0.003、case_14 0.134->0.024），镜像 9688576->9217544 字节"
    ],
    "rollback_signals": [
      "任何 case 的精度不再与冻结基线逐位一致（结构体复制/推导不等价的直接信号）",
      "出现 >4B 的 plain __gm__ 标量装载形态（round-1 的 0/20 形态），或编译产物出现未初始化的 tiling 字段读",
      "性能停在约 1.0x：说明消除的不是 launch-mechanics 之外的 pacing 工作，收益无法归因",
      "任一 dtype case 回退或形式化配对 geomean 未达采纳门（avgpool1d 回滚条件含任一 accuracy failure 或未补偿的 per-case 回退）"
    ]
  }
}
-->

# 性能优化策略：内核入口元数据瘦身：按 kernel 分档 tiling 复制 + host 预计算与片上同式重导出 + 入口 icode 收缩

池化家族的 kernel Init/entry 在标量管上付一笔 per-launch 固定成本：eluadaptiveavgpool3d 的两个 kernel 各自把 828B 的 EluAdaptiveAvgPool3dTiling 逐字节从 GM 标量复制一遍（pool kernel aiv_scalar_time≈8.03-8.12us，约占 kernel 时长 90%），而 ELU kernel 只读前 12B、pool kernel 只读字节 20..60；avgpool1d 每核 Init 逐字节复制 52B tiling，entry 还带着 7 k × 2 CIP × 2 dtype = 28 条 emission 链的冷 icode。三个成员把这三笔固定成本分别削掉：按 kernel 分档的有界字粒度复制（16B/60B、13×uint32）、host 预计算（boxElemCap=maxWd*maxWh*rowStride+128、rowsPerBlock=CeilDiv(totalRows,blockNum)）与片上同式重导出（invW/wStart/wEnd，删 3*W_out 次 GM 标量表装载与 8-13 次整数除法循环）、以及 emission 链 28->4 的 icode 收缩（.so 9688576->9217544B，短 case icache_miss 0.168->0.003）。外层 msprof 平衡交替配对实测：eluadaptiveavgpool3d geomean 8.859->2.830us（3.1307x），其后再把 pool Init 的再计算削掉 2.827->2.460us（1.1495x，pool aiv_scalar -36%），avgpool1d 24.079->23.379us（1.0300x）；三者精度均与冻结基线逐位一致。

## 1. 原理

当标量管是 pacing pipe 时，per-launch 的 kernel Init/entry 固定标量成本直接决定每个 case 的地板，而与数据量无关：eluadaptiveavgpool3d 的 pool kernel aiv_scalar_time≈8.03-8.12us，而 aiv_vec≈0.25-0.29us、aiv_mte2≈0.16-0.31us、aiv_mte3≈0.2us（标量约占 kernel 时长 90%），测试 case 又极小（如 case1 N1C1 6×6×8→288 元素、totalRows=4，kernel 实际向量/MTE 工作量 <0.6us，Task Duration ~8.5-9.6us 几乎全是固定开销）；elu kernel 的 aiv_scalar_time=8.089us 与 pool kernel 相当，说明两个 kernel 共享同一固定标量开销模式。avgpool1d 侧在其 d002 之后 scalar_t 是 16/20 个 case 的最大流水项（suite 级标量份额 43-88%），且可拟合为 INTERCEPT(~8.7us) + ~0.09us/row + ~0.25us/tile——一个 d001（host blockDim）与 d002（per-row/per-tile 队列事件摊销）都没碰过的 per-launch 固定项。这笔固定成本由三部分组成，且三部分都能在不改数值路径的前提下削减：(a) tiling 结构体的逐字节标量 GM 复制，而结构体里 93% 的字节是 invW/wStart/wEnd[64] 数组，没有任何 kernel 读完；(b) kernel 片上重算 host 早已算过、或可由已装载字段同式重导出的派生量；(c) entry 路径每次 launch 都要付的冷 icode 取指（icache_miss 短 case 0.03-0.168 vs 长 case 0.005-0.018）。这是与 init-buffer-pool-consolidation（削 InitBuffer/GetPhyAddr 描述符数量与组织）与 host-gated-cheap-path（host 静态判定的恒等条件编码 + UB 预算按实际队列数重平衡）正交的第三个 Init 面：前两者都不覆盖 per-kernel tiling 复制载荷的裁剪、host 预计算/片上同式重导出、以及入口代码体积；launch-arg-by-value-tiling-fetch-elimination 虽然同样针对 tiling 获取，但它删的是整条 GM 读路径与 host 每调用 H2D（改成 launch 按值参数），本机制保留 GM tiling 读，只把每个 kernel 的复制载荷收缩到它真正消费的字段。avgpool1d 侧的先验诊断还给出了这条杠杆的上界：round-1 的零工作探针（64 block、全部 launch 平铺在 device 8.1-9.1us / scalar 8.1-8.7us）证明 ~8.7us 标量截距大部分是 launch/block-dispatch 机制而非代码镜像，本机制只能拿到 icache/装载数那一份。

实现机制：kernel-entry-metadata-diet 三个分量，全部只动 Init/entry 标量面，不改数值路径、累加顺序与 tiling/分区。(a) 按 kernel 分档的有界 tiling 复制——EluAAP3dCopyTiling 增加 bytes 上限参数并改为 uint32 字粒度复制循环，ELU kernel 传 offsetof(EluAdaptiveAvgPool3dTiling, totalRows)（仅 16B/4 次字加载），pool kernel 传 offsetof(EluAdaptiveAvgPool3dTiling, invW)（仅 60B/15 次字加载）；原实现是 sizeof(EluAdaptiveAvgPool3dTiling)=828 字节逐字节 GM 标量复制，两个 kernel 的 Init 都无条件调用；方向文档给出的载荷下界估计为 ELU≈16B、pool≈44B，落地实现形态为 16B/60B。avgpool1d 的 AvgPool1dCopyTiling 把 52 次逐字节 GM 装载换成 13×uint32（#pragma unroll，champion 证明的 4B plain __gm__ 宽度）。(b) host 预计算 + 片上同式重导出——kernel/pybind11.cpp 用与 kernel 原公式逐字一致的 MaxWindowU32 helper 把 boxElemCap 补全为 maxWd*maxWh*rowStride+128，并按 poolBlockDim=min(64,totalRows) 预计算 rowsPerBlock 写入 tiling（作为 EluAdaptiveAvgPool3dTiling 尾部新增字段）；pool Init 删除两个 EluAAP3dMaxWindow 循环（D_out+H_out 次迭代、每迭代 2 次整数除法）与 CeilDiv(totalRows,blockNum)，改读 tiling_.boxElemCap/tiling_.rowsPerBlock；invW/wStart/wEnd 改片上推导（sw=(ow*W_in)/W_out、ew=ceil 公式、ww=max(ew-sw,1)、invW=1.0f/(float)ww，与 host FillTiling 逐位一致），删除 sSrc/eSrc/iSrc 三张表按 3*W_out 次逐元素 GM 标量读的装载循环（PipeBarrier<PIPE_ALL> 与队列机制原样保留）；round-2 进一步删除已死的 768B GM 表数组（tiling 832->64B），elu kernel 零改动。(c) entry icode 收缩（avgpool1d）——emission body 去掉 KernelSize 模板参量（k 改为运行期 int32_t 传入），删除 7 路 per-tile k if-chain（AvgPool1dTileKDispatch）与已死的 DivIsK=true 通用体，镜像内 emission 链由 7 k × 2 CIP × 2 dtype = 28 条收敛为 2 CIP × 2 dtype = 4 条，.so 9688576 -> 9217544 字节，短 case 的 aiv_icache_miss_rate 塌缩（case_11 0.168->0.003、case_14 0.134->0.024、case_07 0.088->0.012），j 序 gather/add 逐 lane 算术保持 champion 不变。

## 2. 性能问题模式

- 优化目标：消除每核每 launch 都要付的 kernel Init/entry 固定标量成本中可裁剪的部分：828B（eluadaptiveavgpool3d）/52B（avgpool1d）tiling 的逐字节 GM 标量复制、pool Init 的 8-13 次整数除法循环 + 3*W_out 次逐元素 GM 标量表装载 + 1 次 rowsPerBlock 除法，以及每次 launch 都要取指的 7 路 k emission 链冷 icode（短 case icache_miss 0.03-0.168）。
- 适用数据流：kernel Init/entry 在每核每 launch 付固定标量成本、tiling 结构体远大于各 kernel 实际消费字段、且其中含 host 已算/可零成本预算或可由已装载字段同式重导出的派生量的算子；典型如池化家族的 eluadaptiveavgpool3d（elu 与 pool 两个 pass，828B tiling、pool kernel Block Num=4-9）与 avgpool1d（52B tiling + 7×2 k/CIP 模板扇出、Block Num=64）
- Feature signature：`{"bottleneck": ["kernel-init-fixed-cost", "per-launch-gm-tiling-fetch", "byteswise-scalar-tiling-copy", "host-recomputable-init-scalar", "cold-icode-fetch-floor"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "kernel-entry-metadata-diet", "reduce_mode": "", "structure": ["per-kernel-bounded-tiling-copy", "word-granular-scalar-copy", "host-precomputed-derived-fields", "onchip-identical-formula-rederivation", "runtime-k-emission-chain-collapse", "icache-footprint-diet"]}`

## 3. 正确性红线

- 实现形态决定成败（装载宽度）：avgpool1d round-1 的 8B 形态 0/20，诊断探针进一步显示这个『-64%』是工作跳过假象（所有 launch 平铺 8-9us）；必须用 <=4B 的 plain __gm__ 宽度或显式 API，本 run 的可用形态是 13×uint32
- 片上重导出与 host 表达式的逐位一致是隐式契约：任何一处公式简化（ceil、ww=max(ew-sw,1)、float 转换顺序）都只在部分 shape 上显形而破坏逐位一致；验收必须用逐 case MERE/MARE 与冻结基线逐位相同，而不是只看 20/20 通过数
- 收益上界受 launch 机制约束：avgpool1d 零工作 64-block 探针测得 device 8.1-9.1us / scalar 8.1-8.7us，说明 ~8.7us 截距大部分不在代码镜像内，性能门会如实地停在约 1.03x；这不是机制反例，而是该方向的物理上界
- 有界复制的上限与 kernel 实际消费字段脱节就会读到未初始化 tiling 字段：一旦某个 kernel 回头消费被裁掉的字段（如 pool 侧再读 boxElemCap/totalLength/blockLength/tileLength/eluBufLength），必须同步抬高该调用点的字节上限，而不是靠结构体整体复制兜底
- sub-1% 的布局噪声需与机制收益区分：round-1 配对里 elu 三 case 系统性 +0.3~1.2%（elu kernel 代码与设备代码未触碰、cycles +42/icache 相同），round-2 删除 768B 死数组后符号翻转（elu_fp16 +1.2% -> -2.6%），证实是 .so/数据布局噪声而非机制回归

资源与硬件约束：

- 本工具链上 plain __gm__ 标量装载宽度必须 <= 4B：avgpool1d round-1 的 8B 形态（6×uint64 + 1×uint32 tiling 复制）实测精度 0/20——8B plain __gm__ 标量装载静默损坏 tiling 读、kernel 提前退出，且诊断探针显示其 -64% 是工作被跳过的假象；round-2 的 13×uint32 才通过 20/20 且 MERE/MARE 与 champion 相同
- 片上重导出必须与 host 使用完全相同的整数/浮点表达式才能逐位一致：boxElemCap/rowsPerBlock 走 host 同公式整数预计算（boxElemCap=maxWd*maxWh*rowStride+128、rowsPerBlock 按 poolBlockDim=min(64,totalRows)），invW/wStart/wEnd 用与 host FillTiling 相同的整数除法与 float 转换/除法表达式，不得简化 ceil 公式或 ww=max(ew-sw,1)
- 有界复制的字节上限必须按各 kernel 实际消费字段的偏移界定，并随调用点显式传入：ELU 侧 offsetof(EluAdaptiveAvgPool3dTiling, totalRows)=16B、pool 侧 offsetof(EluAdaptiveAvgPool3dTiling, invW)=60B；invW/wStart/wEnd 的 GM 直读路径、数值路径、Op Name、tiling 结构与 host 侧均未改动
- avgpool1d 侧 host（kernel/pybind11.cpp）与 tiling/分区不变，avgpool1d_tiling.h 结构在回退 round-1 的 alignas(8) 实验后保持原样；runtime-k 化必须保住 champion 的 j 序 gather/add 逐 lane 算术，PipeBarrier 与队列机制原位保留

## 4. 泛化条件

- 策略作用域：op_class：pool

适用：

- 标量管是 pacing pipe 且 Init/entry 是 per-launch 固定项：eluadaptiveavgpool3d 的 pool kernel aiv_scalar_time≈8.03-8.12us、aiv_vec≈0.25-0.29us、aiv_mte2≈0.16-0.31us、aiv_mte3≈0.2us（标量约占 kernel 时长 90%），elu kernel aiv_scalar_time=8.089us 与 pool kernel 相当；direction_001 采纳后 pool kernel aiv_scalar_time 仍有 ~2.75-3.0us（占比 ~76-78%），elu kernel ~1.24-1.5us
- tiling 结构体按字节循环整体复制、且远大于任一 kernel 实际消费的字段：eluadaptiveavgpool3d 的结构为 15×uint32 头（60B）+ invW/wStart/wEnd[64]×float（768B），数组占 93% 字节，EluAAP3dCopyTiling 对 sizeof=828 字节逐字节 GM 标量复制；avgpool1d 的 AvgPool1dCopyTiling 每核 Init 从 GM 逐字节复制 sizeof(AvgPool1dTiling)=52 字节，即 52 次标量 GM 装载/launch/核
- 存在 host 已算过或可零成本预算、而 kernel 片上重算的派生几何量：boxElemCap 在 host 已算过 maxWh*rowStride+128 但漏了 maxWd 因子，kernel 被迫用两个 EluAAP3dMaxWindow 循环（D_out+H_out 次迭代、每迭代 2 次整数除法）重导出框容量；rowsPerBlock=CeilDiv(totalRows,blockNum) 每核一次整数除法，而 host 在 run_elu_adaptive_avg_pool3d 中本就计算 poolBlockDim
- 存在可由已装载字段同式重导出的表：invW/wStart/wEnd 完全由 W_in/W_out 决定，host FillTiling 的公式与 kernel 可用的整数/浮点表达式一致（sw=(ow*W_in)/W_out、ew=ceil、ww=max(ew-sw,1)、invW=1.0f/(float)ww），而原实现按 3*W_out 次逐元素 GM 标量读把三张表搬入 UB 并配 PipeBarrier<PIPE_ALL>
- 入口代码体积可收缩且冷取指确实被付掉：avgpool1d 每个 dtype entry 都实例化完整的 7 k × CIP{0,1} 模板扇出（AvgPool1dTileKDispatch -> AvgPool1dTileSegments -> FastVF/EmitBlocks 内联 VF 体），icache_miss 短 case 0.03-0.168 vs 长 case 0.005-0.018

不适用：

- tiling 复制本来就是字粒度/有界，或 kernel 确实消费整个结构体时，没有可裁剪的复制载荷
- 标量管不是节拍源时不适用（例如 mte2/vec 主导）：本机制不减少任何一条向量/MTE 指令，只削 Init/entry 的标量发射与取指
- per-launch 固定成本主要来自 launch/block-dispatch 机制而非代码镜像时不适用：avgpool1d d003 的 round-1 零工作探针证明 ~8.7us 标量截距大部分在镜像之外（64-block 零工作 launch 仍 8.1-9.1us device / 8.1-8.7us scalar），本机制只能拿到 icache/装载数那一份——实测 1.0300x，而非 projected 的 -12..-20%
- 结构性语义不同的 Init 面不在本机制作用域内：InitBuffer/GetPhyAddr 的组织是 init-buffer-pool-consolidation 的域，host 静态恒等判定与 UB 预算重平衡是 host-gated-cheap-path 的域，把整个 tiling 改成 launch 按值参数（删 GM 读路径与每调用 H2D）是 launch-arg-by-value-tiling-fetch-elimination 的域

## 5. 实施步骤

1. 按 kernel 清点 tiling 字段的消费面与偏移：ELU kernel 只读 totalLength/blockLength/tileLength（前 12 字节），pool kernel 只读字节 20..60（totalRows/rowStride/N/C/D_in/H_in/W_in/D_out/H_out/W_out），并确认 invW/wStart/wEnd 是另外三张 GM 表、boxElemCap/totalLength/blockLength/tileLength/eluBufLength 在该路径未使用
2. 把 EluAAP3dCopyTiling 改成带 bytes 上限的 uint32 字粒度复制循环，两个调用点分别传 offsetof(..., totalRows)=16B（4 次字加载）与 offsetof(..., invW)=60B（15 次字加载）；avgpool1d 侧把 AvgPool1dCopyTiling 的 52 次逐字节装载换成 13×uint32（#pragma unroll）
3. host 侧补全派生量：kernel/pybind11.cpp 用与 kernel 原公式逐字一致的 MaxWindowU32 计算 boxElemCap=maxWd*maxWh*rowStride+128，按 poolBlockDim=min(64,totalRows) 预计算 rowsPerBlock，并在 EluAdaptiveAvgPool3dTiling 尾部新增 rowsPerBlock 字段
4. pool Init 删除两个 EluAAP3dMaxWindow 循环与 CeilDiv(totalRows,blockNum)，改读 tiling_.boxElemCap/tiling_.rowsPerBlock；invW/wStart/wEnd 改片上同式推导并删除 sSrc/eSrc/iSrc 的 3*W_out 次 GM 标量装载循环（保留 PipeBarrier<PIPE_ALL> 与队列机制）；round-2 删除已死的 768B GM 表数组（tiling 832->64B），ELU kernel 零改动
5. avgpool1d 侧去掉 emission body 的 KernelSize 模板参量（k 改为运行期传入）、删除 7 路 per-tile k if-chain 与死 DivIsK 体，使 emission 链 28->4；以逐 case MERE/MARE 与冻结基线逐位一致 + 平衡交替 ABBA 配对（无 case 回退）验收，任一精度失败或未补偿回退即回滚

## 6. LLM 前置问题

- 目标实现是否满足：标量管是 pacing pipe 且 Init/entry 是 per-launch 固定项：eluadaptiveavgpool3d 的 pool kernel aiv_scalar_time≈8.03-8.12us、aiv_vec≈0.25-0.29us、aiv_mte2≈0.16-0.31us、aiv_mte3≈0.2us（标量约占 kernel 时长 90%），elu kernel aiv_scalar_time=8.089us 与 pool kernel 相当；direction_001 采纳后 pool kernel aiv_scalar_time 仍有 ~2.75-3.0us（占比 ~76-78%），elu kernel ~1.24-1.5us？
- 目标实现是否满足：tiling 结构体按字节循环整体复制、且远大于任一 kernel 实际消费的字段：eluadaptiveavgpool3d 的结构为 15×uint32 头（60B）+ invW/wStart/wEnd[64]×float（768B），数组占 93% 字节，EluAAP3dCopyTiling 对 sizeof=828 字节逐字节 GM 标量复制；avgpool1d 的 AvgPool1dCopyTiling 每核 Init 从 GM 逐字节复制 sizeof(AvgPool1dTiling)=52 字节，即 52 次标量 GM 装载/launch/核？
- 目标实现是否满足：存在 host 已算过或可零成本预算、而 kernel 片上重算的派生几何量：boxElemCap 在 host 已算过 maxWh*rowStride+128 但漏了 maxWd 因子，kernel 被迫用两个 EluAAP3dMaxWindow 循环（D_out+H_out 次迭代、每迭代 2 次整数除法）重导出框容量；rowsPerBlock=CeilDiv(totalRows,blockNum) 每核一次整数除法，而 host 在 run_elu_adaptive_avg_pool3d 中本就计算 poolBlockDim？
- 目标实现是否满足：存在可由已装载字段同式重导出的表：invW/wStart/wEnd 完全由 W_in/W_out 决定，host FillTiling 的公式与 kernel 可用的整数/浮点表达式一致（sw=(ow*W_in)/W_out、ew=ceil、ww=max(ew-sw,1)、invW=1.0f/(float)ww），而原实现按 3*W_out 次逐元素 GM 标量读把三张表搬入 UB 并配 PipeBarrier<PIPE_ALL>？
- 目标实现是否满足：入口代码体积可收缩且冷取指确实被付掉：avgpool1d 每个 dtype entry 都实例化完整的 7 k × CIP{0,1} 模板扇出（AvgPool1dTileKDispatch -> AvgPool1dTileSegments -> FastVF/EmitBlocks 内联 VF 体），icache_miss 短 case 0.03-0.168 vs 长 case 0.005-0.018？
- 是否命中排除条件：tiling 复制本来就是字粒度/有界，或 kernel 确实消费整个结构体时，没有可裁剪的复制载荷？
- 是否命中排除条件：标量管不是节拍源时不适用（例如 mte2/vec 主导）：本机制不减少任何一条向量/MTE 指令，只削 Init/entry 的标量发射与取指？
- 是否命中排除条件：per-launch 固定成本主要来自 launch/block-dispatch 机制而非代码镜像时不适用：avgpool1d d003 的 round-1 零工作探针证明 ~8.7us 标量截距大部分在镜像之外（64-block 零工作 launch 仍 8.1-9.1us device / 8.1-8.7us scalar），本机制只能拿到 icache/装载数那一份——实测 1.0300x，而非 projected 的 -12..-20%？
- 是否命中排除条件：结构性语义不同的 Init 面不在本机制作用域内：InitBuffer/GetPhyAddr 的组织是 init-buffer-pool-consolidation 的域，host 静态恒等判定与 UB 预算重平衡是 host-gated-cheap-path 的域，把整个 tiling 改成 launch 按值参数（删 GM 读路径与每调用 H2D）是 launch-arg-by-value-tiling-fetch-elimination 的域？

## 7. 验收标准

正确性：

- eluadaptiveavgpool3d direction_001：精度 20/20 PASS 且与基线逐位一致（bitwise_identical_to_baseline=true），编译 0 修复轮
- eluadaptiveavgpool3d direction_002：round-1 与 round-2 均一次通过 20/20 且与基线逐位一致；片上推导使用与 host FillTiling 完全相同的整数/浮点表达式，数值路径未触碰，elu kernel（Phase A）零改动
- avgpool1d direction_003：round-2 20/20，MERE/MARE 与 champion 基线一致；round-1 的 8B 装载形态 0/20 已归档为证伪子形态（诊断探针证明其降幅是工作跳过假象）
- 三成员的改动均限定在 kernel Init/entry 路径（avgpool1d 侧 host 与 avgpool1d_tiling.h 未改），tiling 结构与 Op Name 不变

性能：

- eluadaptiveavgpool3d direction_001：外层 msprof 4 对平衡交替 24/24 case 级比较一致向快，geomean 8.8595->2.8299us（pair geomean_ratio 0.3187-0.3207），elu aiv_scalar_time 8.0->1.3us、pool 8.1->2.9us；case 级 elu_bf16 8.550->1.897us、elu_fp16 8.681->1.995us、elu_fp32 8.547->1.894us、pool_bf16 9.143->4.109us、pool_fp16 9.138->4.211us、pool_fp32 9.123->4.139us
- eluadaptiveavgpool3d direction_002：4 对配对全部 candidate_faster（pair geomean_ratio 0.8691-0.8716），pool 12/12 case 级 -23.2~-24.7%，pool aiv_scalar_time 2.89-2.94 -> 1.82-1.90us（-36%），pool Task Duration 4.11-4.23 -> 3.11-3.21us（-24%），geomean 2.827->2.460us（1.1495x）；实测收益 ~1.05us 超出预估上限（预估 0.3-0.8us），elu 侧 <=1% 的布局噪声被两轮构建的符号翻转归因为非机制因素
- avgpool1d direction_003：形式化 ABBA suite-regime 5/5 对 candidate-faster（1.0273/1.0315/1.0307/1.0304/1.0299，mean 1.0300），20/20 case 全改善（最差 case_04 -0.6%，最好 case_07 -9.6%、case_06 -8.0%、case_10 -7.4%），短 case icache_miss 塌缩（case_11 0.168->0.003、case_14 0.134->0.024），镜像 9688576->9217544 字节

回滚信号：

- 任何 case 的精度不再与冻结基线逐位一致（结构体复制/推导不等价的直接信号）
- 出现 >4B 的 plain __gm__ 标量装载形态（round-1 的 0/20 形态），或编译产物出现未初始化的 tiling 字段读
- 性能停在约 1.0x：说明消除的不是 launch-mechanics 之外的 pacing 工作，收益无法归因
- 任一 dtype case 回退或形式化配对 geomean 未达采纳门（avgpool1d 回滚条件含任一 accuracy failure 或未补偿的 per-case 回退）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：init-buffer-pool-consolidation, host-gated-cheap-path, launch-arg-by-value-tiling-fetch-elimination

- loop_20260917_024611（round=1, status=accepted, speedup=3.1307, precision=20/20 PASS（与基线逐位一致））
- loop_20260917_024611（round=2, status=accepted, speedup=1.1495, precision=20/20 PASS（round-1/round-2 均一次通过，与基线逐位一致））
- loop_20260916_125427（round=2, status=accepted, speedup=1.03, precision=20/20 PASS（MERE/MARE 与 champion 基线一致；round-1 的 8B 装载形态 0/20 已证伪））

## 检索卡（短卡）

动作：把 kernel Init 的整结构体 tiling 逐字节复制改为按消费字段的有界字粒度复制，host 预计算与片上同式重导出。
适用：标量管是 pacing pipe、tiling 远大于 kernel 消费字段、含可同式重导出的派生量。
限制：plain __gm__ 装载宽度须 <=4B（8B 形态 0/20）；片上重导出须与 host 同式逐位一致。
范围：池化家族等 Init/entry 付固定标量成本的算子。
检索词：EluAAP3dCopyTiling、MaxWindowU32、rowsPerBlock、icache_miss、字粒度复制
机会：tiling 逐字节标量复制、片上重算派生量、冷 icode 取指，标量约占 kernel 时长 90%。
代价：per-launch 截距多在 launch/block-dispatch 机制而非镜像内。
