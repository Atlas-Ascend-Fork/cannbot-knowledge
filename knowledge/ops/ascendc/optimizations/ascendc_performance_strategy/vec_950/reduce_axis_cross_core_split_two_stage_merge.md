---
type: Optimization
title: 归约轴跨核切分两级归并：低扇出 launch 的核数补全 + GM workspace partial 合并
description: 把从未切分的长归约轴切成每核一段，各核写 partial 到 GM workspace，再做两级合并。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/reduce-axis-cross-core-split-two-stage-merge.md
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
      "两阶段必须由独立 kernel launch 或 SyncAll<true>() 排序：(a) 走同 stream 顺序两次 launch（跨核可见性由 stream 顺序保证）；(b) 走 KERNEL_TYPE_MIX_AIV_1_0 + SyncAll<true>()，且所有实际 launch 的核必须以相同轮次到达屏障（group 对齐 wave 分派）",
      "放大前必须先做最小探针：构造 grSegs=2、单 row、单 dtype 的隔离 case 确认两阶段路径能运行到完成（NEG-GR-SYNCALL-DEADLOCK 在 A5 上曾以 GM workspace + AIV-only SyncAll + combine 的组合确定性死锁 507034，所有已 launch 的核卡在同一 PC）",
      "写侧可见性用 SyncAll 内部已含的 PipeBarrier<PIPE_ALL>，不要引入 S_MTE3/MTE2_S 原生事件（NEG-S-MTE3-MIX-SYNCALL：在 MIX_AIV_1_0 + 硬 SyncAll 上下文触发设备 507035）；TQue 管理的核内 V_MTE3/MTE2_V 事件不受影响",
      "host 门控必须精确镜像 kernel 门与 UB 预算公式，否则出现 ws 未分配而 kernel 走 split 的缺配",
      "(a) 变体的 tiling 结构体字节数必须保持不变：每核逐字节标量拷贝 tiling 是固定 launch 开销，字段追加（52B→68B）会给门控外全部 case 每次 launch +0.4~1.1us；用 union overlay 到内核从不读取的 totalOutputs/totalLength 槽位可零成本携带新参数",
      "归一化写出必须复用 legacy CopyChunkOut（staging 的源 stride 是 tileInner pitch 而非 slabPitch；case 18 fp32 因 slabPitch==tileInner 侥幸正确）"
    ],
    "excluded_conditions": [
      "外轴已足够占满核数（blockDim >= coreNum）时不适用：切段只增加 partial 写入与合并开销，没有核饥饿可补——门控必须与之互斥（argmaxidentity：mode==1 && totalWindows<coreNum && d1>=262144；catsoftmax：cSplitCount>1 && inner>1 && !resident && !degenerate && blockNum>=S）",
      "归约轴太短、段负载不足以摊销合并阶段（第二次 launch 或 SyncAll 屏障）时不适用：argmaxidentity 以 d1>=262144 为下限",
      "已有 degenerate / resident 快路径覆盖的形状不在本机制域内：split 路径必须与之互斥，不得覆盖已优化的 case",
      "要求合并结果与单遍串行逐位一致、且归约是浮点求和的场景须先对账舍入：fp32 sum 折放有舍入风险（本 run case 18 fp32 1e-5 容差）",
      "归并阶段不能用标量实现：CCE 不支持 __aicore__ 标量浮点分支 / 标量 GM 读写（GetValue/SetValue）/ int64 标量写，merge kernel 必须全向量队列化"
    ],
    "required_conditions": [
      "host 定核公式为 blockDim = min(并行任务数, coreNum) 且并行任务数只由外轴给出——本 run 两例：catsoftmax workTotal = B×ceil(S/tileInner) = 2/4（pybind blockDim = min(workTotal, coreNum)）；argmaxidentity Path B 的 totalWindows = d0 = 1（blockDim = min(64,d0)）",
      "归约轴长且从未被切分：catsoftmax channelTotal=2049、argmaxidentity d1=1000003；核饥饿是结构性证据而非推测（case12 Block Num=1、aiv_vec_time 114.9/117.0us、vec_ratio 0.982、63/64 核闲置）",
      "归约具有可结合/可折放的合并规则：max 逐元素 max、argmax 带 tie-break 的全序逐对归并、softmax 的 sum 以 exp(maxB-maxG) 在线重缩放折放",
      "top wall 落在该路径上并主导 geomean：catsoftmax case 18/19（fp32 [2,1024,511]+[2,1025,511] 与 bf16 [4,1024,255]+[4,1025,255]）单独把 geomean 从 ~26us 拉到 32.5us；argmaxidentity case 12 是 20 case 中唯一 Block Num=1 的 launch",
      "(b) 变体还需：kernel 可声明 KERNEL_TYPE_MIX_AIV_1_0 使 SyncAll() 硬同步可用，且切段后每核 slab 能装入 UB 预算（192KiB）而顺带把 GM 读 3x 降为 1x"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "catsoftmax",
      "operator_class": "fused-composite",
      "precision": "20/20 PASS（1 次精度修复；最差 case 18 MERE 3.769e-07 < 1e-05）",
      "run_id": "<run-id>",
      "speedup": 1.2413,
      "status": "accepted"
    },
    {
      "operator": "argmaxidentity",
      "operator_class": "sort-select",
      "precision": "20/20 PASS（int64 bit-exact vs torch.argmax）",
      "run_id": "<run-id>",
      "speedup": 1.1373,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-underutilization",
      "reduction-axis-not-split",
      "low-fanout-launch"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "reduce-axis-cross-core-split-two-stage-merge",
    "reduce_mode": "",
    "structure": [
      "reduce-axis-cross-core-split",
      "gm-fp32-workspace-partials",
      "two-stage-merge",
      "group-aligned-wave-syncall",
      "same-stream-second-launch-merge-kernel",
      "ub-resident-slab-single-read"
    ]
  },
  "generality": "op_class",
  "id": "SPLIT-REDUCE-AXIS-TWO-STAGE-MERGE",
  "implementation_steps": [
    "先量化核饥饿与并行度结构：算清 host 定核公式（blockDim = min(并行任务数, coreNum)）与并行任务数的来源，确认长归约轴从不跨核切分（catsoftmax workTotal=B×ceil(S/tileInner)=2/4；argmaxidentity totalWindows=d0=1），并用 profiling 坐实核数与瓶颈一一对应（case12 Block Num=1、aiv_vec_time 114.9/117.0us、vec_ratio 0.982）",
    "在放大前先做最小探针：构造 grSegs=2、单 row、单 dtype 的隔离 case 跑通两阶段路径（NEG-GR-SYNCALL-DEADLOCK 红线），确认 SyncAll<true>()（或同 stream 双 launch）在该工程 launch 方式下可用",
    "host 侧切段并精确镜像 kernel 门：把归约轴切成 S/segPerWin 段（catsoftmax 按 192KiB UB 预算取 blockRowsMax，S = max(ceil(C/blockRowsMax), floor(coreNum/(B*tiles))) 并 clamp，blockDim = min(B*tiles*S, coreNum)；argmaxidentity segPerWin = coreNum/totalWindows、segLen = alignUp(ceil(d1/segPerWin),64)），新增 tiling 字段并分配 partial workspace（fp32，每 (b,t,cb) 槽 2*wsPitch floats 的 [maxB|sumB] 或 (val, idx) 对）",
    "kernel 侧写 partial：每核只读自己那一段（(b) 顺带 slab UB 常驻，GM 读 3x→1x），算出块内 partial 向量/值写 workspace，空段写哨兵（argmaxidentity 为 (-inf, INT32_MAX)、归并初始化 maxRun=-inf 使首槽 exp(-inf-maxB)=0 安全）",
    "合并与写出：(a) 独立归并 kernel 同 stream 第二次 launch，逐窗口把 partial 向量归并后写最终输出；(b) group 对齐 wave 分派（每 wave floor(blockNum/S) 个 group）后 SyncAll<true>()，各核在线合并本 group 全部槽（max 逐元素 / sum 折放 exp(maxB-maxG)），再从驻留 slab 归一化并用 legacy CopyChunkOut 写出"
  ],
  "intent": "消除 blockDim = min(outer, coreNum) 造成的核饥饿：外轴（B×tiles 或窗口数 d0）短于核数时长归约轴从不跨核切分，全部工作压在 1-4 个核上串行完成（catsoftmax case 18/19 的 2/4 核、argmaxidentity case 12 的 1 核），其余 60+ 个向量核空闲；把归约轴切成每核一段以补全并行度，同时让切段后的 slab 能 UB 常驻、把该路径的 GM 读由 3x 降为 1x。",
  "mechanism": "两个已验证实现共享『归约轴切段 + partial 落 GM workspace + 两级合并』骨架，区别只在合并阶段如何排序。(a) 独立归并 kernel（argmaxidentity，门：mode==1 && totalWindows<coreNum && d1>=262144）：segPerWin = coreNum/totalWindows、segLen = alignUp(ceil(d1/segPerWin),64)、totalUnits = totalWindows*segPerWin；stage-1 kernel argmax_identity_<dt>_seg 以 totalUnits blocks launch，每核处理一个 (window,segment) 单元，chunk 循环复用 champion ArgmaxComputeChunkPathB（d1 形参传 segEnd、posBase 从 segStart 起），ArgmaxTreeReduce 后把 (bestVal[0], bestIdx[0]) 以两次 4B DataCopyPad 写 GM workspace（空段写 (-inf, INT32_MAX) 哨兵）；stage-2 kernel argmax_identity_<dt>_merge 以 totalWindows blocks launch，把本窗口 segPerWin 对 (val, globalIdx) 经 VECIN 队列载入 UB，一次 champion ArgmaxUpdate(laneMask=segPerWin) + ArgmaxTreeReduce（eq&Idx tie-break、nv-first-NaN-lock）选出 winner 后写 int64；host 用 torch::empty 分配 workspace、两 launch 同 stream 顺序提交，跨核可见性由 stream 顺序保证，无需屏障。(b) 同 launch 内两阶段（catsoftmax，门：cSplitCount>1 && inner>1 && !resident && !degenerate && blockNum>=S，host 精确镜像）：host 按 192KiB UB 预算取 blockRowsMax，S = max(ceil(C/blockRowsMax), floor(coreNum/(B*tiles))) 并 clamp，blockDim = min(B*tiles*S, coreNum)，tiling 增加 cSplitCount/cSplitRows/wsPitch 三字段并按每 (b,t,cb) 槽 2*wsPitch floats 分配 fp32 workspace（[maxB|sumB]）；kernel 逐 wave 按 group 对齐分派（每 wave floor(blockNum/S) 个 group，所有核以相同轮次各到达一次 SyncAll<true>()），SplitPartial 单读 slab 驻留 UB 后算块内 partial（MaxChunkReg/SumChunkReg）经 VECOUT TQue 写 [maxB|sumB] 槽，SyncAll<true>() 后 SplitNormalize 用 wsInQ 逐槽 CatMergeSlotReg 在线合并（maxRun=max；sumRun=sumRun*exp(oldMax-newMax)+sumB*exp(maxB-newMax)），再以 SoftmaxChunkSplitReg 双 pitch 从驻留 slab 归一化、legacy CopyChunkOut 写出。唯一设计偏离：块内 fp32 e 持久化改为归一化时 exp 复算（块数下限接近核数时 e 无法跨 SyncAll 边界存活；slab-only 驻留使 blockRows 翻倍、merge 流量减半）。",
  "name": "归约轴跨核切分两级归并：低扇出 launch 的核数补全 + GM workspace partial 合并",
  "operator_class": "reduction",
  "operator_scope": "host 定核公式为 blockDim = min(并行任务数, coreNum)、并行任务数只由外轴（batch×tile 数、窗口数）给出的归约型算子，且归约轴长而从未跨核切分；典型如同 launch 内按 (b,t) 做通道归约的 fused softmax（catsoftmax，channelTotal=2049）与低扇出 launch 的跨窗口选择归约（argmaxidentity Path B，s==1，d1=1000003）。",
  "principle": "并行度由 host 的定核公式决定，而不是由工作量决定：当 blockDim = min(并行任务数, coreNum) 而并行任务数只由外轴（batch×tile 数、或窗口数 d0）给出时，只要外轴短于核数，核数就被压死，而真正长的归约轴反而留在 1-4 个核里串行跑完。此时唯一能兑现的杠杆是给归约轴本身制造并行度：把它切成与核数同阶的段、每核只读自己那一段并输出一个 partial，再用一次跨核合并把 partial 还原成全局统计量。合并的可行性来自归约的代数性质——max 的合并就是 max，argmax 的合并是带 tie-break 的逐对全序归并，softmax 的 sum 可以用 flash 式在线重缩放（sumRun*exp(oldMax-newMax)+sumB*exp(maxB-newMax)）折放，因此两级合并与单遍串行在数学上等价，代价只有 workspace 往返与一次屏障（或一次额外 launch）。它还顺带修掉第二个 wall：切段后每核的 slab 变小到能 UB 常驻，legacy 3-pass 的 3x GM 重读在该路径上降为 1x。",
  "related_anti_patterns": [
    "s-mte3-event-mix-syncall-error"
  ],
  "risks": [
    "SyncAll 悬挂/死锁：AIV-only 硬屏障必须被所有实际 launch 且继续执行的核以相同次数到达，任一核提前 return、wave 轮次不一致或 combine 非终止都会让全部核卡在同一 PC（507034）；本 run 靠 group 对齐 wave 分派规避，(b) 变体首次实证可用（全核等轮次 + PipeBarrier<PIPE_ALL> 写侧可见性 + 未使用 S_MTE3/MTE2_S 原生事件）",
    "在线合并的 fp32 舍入：sum 折放 exp(maxB-maxG) 在 case 18 fp32 的 1e-5 容差下有舍入风险（估算 ~1e-6 量级相对误差）；回退方案是用全局 max 重新归约",
    "精度首次失败：归一化输出 copy 误用 slabPitch 计算 staging 源 stride（staging 实为 tileInner pitch），case 18 fp32 因 slabPitch==tileInner 侥幸正确、其余 16 行 chunk 仅行 0 正确；性能探测确认显著收益后 1 次修复（复用 legacy CopyChunkOut）",
    "门控外回归：catsoftmax 其余 18 case 中 4 个（case 1/11/13/20）六对均值 +2.2%~+3.1%（仅 case 1 逐对一致 ~+0.9us，二进制布局效应；tiling 结构体 +12B 亦有微小贡献），geomean 影响约 -0.3%；argmaxidentity 门控外 19 case 配对比值 0.976~1.050（均值 1.005，噪声带、无系统性回退）——后者是靠 tiling union 恢复 52B 才消除的（68B 形态会给门控外 19 case 每次 launch +0.4~1.1us）",
    "标量 merge kernel 编译失败：CCE backend 无法切分标量浮点分支 / GetValue-SetValue / int64 标量写（clang frontend segfault，编译修复 #1），merge kernel 必须全向量队列化",
    "尾块 C-block 掩码与空段哨兵：尾块的通道掩码、空段哨兵与归并初值必须同时正确，否则只在部分 shape 上显形"
  ],
  "slug": "reduce-axis-cross-core-split-two-stage-merge",
  "summary": "当 host 用 blockDim = min(并行任务数, coreNum) 定核、而并行任务数只由外轴给出时，长归约轴从不跨核切分：catsoftmax 的 workTotal = B×ceil(S/tileInner) 在 case 18/19 上是 2/4，blockDim 被压到 2/4（62/60 个向量核空闲），channelTotal=2049 留在 2/4 个核上串行跑三遍（legacy 3-pass，每核 3x GM 重读）；argmaxidentity 的 Path B 低扇出 launch 里 totalWindows = d0 = 1，blockDim = min(64,d0) = 1，case 12 [1,1000003] bf16 单核串行归约 100 万元素（Block Num=1、aiv_vec_time 114.9/117.0us、vec_ratio 0.982、63/64 核闲置）。机制是把归约轴切成每核一段：各核只读自己那一段、把 partial 写 GM workspace，再做两级合并。两个已验证实现：(a) argmaxidentity 走独立归并 kernel、与 stage-1 同 stream 顺序第二次 launch（无屏障），合并在 (val, idx) 全序 tie-break 下逐对归并；(b) catsoftmax 走 KERNEL_TYPE_MIX_AIV_1_0 + SyncAll<true>() 的 group 对齐 wave 分派，全局统计量以 exp(max_b - max_g) 折放回写；(b) 的副作用是每 block slab 变为 UB 常驻，该路径 GM 读由 3x 降为 1x。geomean：catsoftmax 32.4653→26.1551us（1.2413x，case 18/19 约 9.7x/9.2x，blockNum 2/4→64）；argmaxidentity 41.678→36.6475us（1.1373x，case 12 117.16→15.69us）。两成员精度均 20/20。",
  "verification": {
    "correctness": [
      "catsoftmax：20/20 PASS（1 次精度修复；最差 case 18 MERE 3.769e-07 < 1e-05）",
      "argmaxidentity：20/20 PASS，int64 bit-exact vs torch.argmax（段内复用 champion ArgmaxComputeChunkPathB+ArgmaxTreeReduce 逐指令不变，跨段归并与单遍 first-wins / NaN-aware 语义等价，空段 -inf 哨兵不参与归并）",
      "未触碰路径原样保留：(b) 的 degenerate / resident 路径与其余 18 case 零语义接触；(a) 的门控外 19 case 逐字段走 champion 路径"
    ],
    "performance": [
      "catsoftmax：形式化 ABBA 6 对（12 runs）全部无歧义（pair ratio 0.8017~0.8098），geomean 32.4653→26.1551us（1.2413x）；case 18 fp32 289.614→29.7188us、case 19 bf16 221.0955→24.0667us（约 9.7x/9.2x，blockNum 2/4→64）",
      "argmaxidentity：formal ABBA 10/10 paired measurements faster（geomean_ops 41.678→36.6475us，1.1373x）；case 12 [1,1000003] bf16 117.16→15.69us（ratio 0.1339，stage-1 ~12.4us + merge ~3.0us）",
      "副作用兑现：(b) 该路径每 block slab UB 常驻，GM 读由 3x 降为 1x",
      "门控外扰动已披露：catsoftmax case 1/11/13/20 六对均值 +2.2%~+3.1%（geomean 影响约 -0.3%）；argmaxidentity 门控外 19 case 比例 0.976~1.050（均值 1.005）"
    ],
    "rollback_signals": [
      "SyncAll 悬挂或设备报 507034/507035：核未以相同轮次到达屏障，或引入了 S_MTE3/MTE2_S 原生事件",
      "门控外任一 case 系统性回退：catsoftmax 有 case 回归 >2% 即回滚；argmaxidentity 门控外 case 超出 0.976~1.050 噪声带即回滚",
      "workspace 缺配（host 门与 kernel 门不一致，ws 未分配但 kernel 走 split）",
      "在线合并舍入使 fp32 case 精度超出 1e-5 容差",
      "tiling 结构体膨胀导致门控外固定 launch 开销（52B→68B 的 +0.4~1.1us 形态）"
    ]
  }
}
-->

# 性能优化策略：归约轴跨核切分两级归并：低扇出 launch 的核数补全 + GM workspace partial 合并

当 host 用 blockDim = min(并行任务数, coreNum) 定核、而并行任务数只由外轴给出时，长归约轴从不跨核切分：catsoftmax 的 workTotal = B×ceil(S/tileInner) 在 case 18/19 上是 2/4，blockDim 被压到 2/4（62/60 个向量核空闲），channelTotal=2049 留在 2/4 个核上串行跑三遍（legacy 3-pass，每核 3x GM 重读）；argmaxidentity 的 Path B 低扇出 launch 里 totalWindows = d0 = 1，blockDim = min(64,d0) = 1，case 12 [1,1000003] bf16 单核串行归约 100 万元素（Block Num=1、aiv_vec_time 114.9/117.0us、vec_ratio 0.982、63/64 核闲置）。机制是把归约轴切成每核一段：各核只读自己那一段、把 partial 写 GM workspace，再做两级合并。两个已验证实现：(a) argmaxidentity 走独立归并 kernel、与 stage-1 同 stream 顺序第二次 launch（无屏障），合并在 (val, idx) 全序 tie-break 下逐对归并；(b) catsoftmax 走 KERNEL_TYPE_MIX_AIV_1_0 + SyncAll<true>() 的 group 对齐 wave 分派，全局统计量以 exp(max_b - max_g) 折放回写；(b) 的副作用是每 block slab 变为 UB 常驻，该路径 GM 读由 3x 降为 1x。geomean：catsoftmax 32.4653→26.1551us（1.2413x，case 18/19 约 9.7x/9.2x，blockNum 2/4→64）；argmaxidentity 41.678→36.6475us（1.1373x，case 12 117.16→15.69us）。两成员精度均 20/20。

## 1. 原理

并行度由 host 的定核公式决定，而不是由工作量决定：当 blockDim = min(并行任务数, coreNum) 而并行任务数只由外轴（batch×tile 数、或窗口数 d0）给出时，只要外轴短于核数，核数就被压死，而真正长的归约轴反而留在 1-4 个核里串行跑完。此时唯一能兑现的杠杆是给归约轴本身制造并行度：把它切成与核数同阶的段、每核只读自己那一段并输出一个 partial，再用一次跨核合并把 partial 还原成全局统计量。合并的可行性来自归约的代数性质——max 的合并就是 max，argmax 的合并是带 tie-break 的逐对全序归并，softmax 的 sum 可以用 flash 式在线重缩放（sumRun*exp(oldMax-newMax)+sumB*exp(maxB-newMax)）折放，因此两级合并与单遍串行在数学上等价，代价只有 workspace 往返与一次屏障（或一次额外 launch）。它还顺带修掉第二个 wall：切段后每核的 slab 变小到能 UB 常驻，legacy 3-pass 的 3x GM 重读在该路径上降为 1x。

实现机制：两个已验证实现共享『归约轴切段 + partial 落 GM workspace + 两级合并』骨架，区别只在合并阶段如何排序。(a) 独立归并 kernel（argmaxidentity，门：mode==1 && totalWindows<coreNum && d1>=262144）：segPerWin = coreNum/totalWindows、segLen = alignUp(ceil(d1/segPerWin),64)、totalUnits = totalWindows*segPerWin；stage-1 kernel argmax_identity_<dt>_seg 以 totalUnits blocks launch，每核处理一个 (window,segment) 单元，chunk 循环复用 champion ArgmaxComputeChunkPathB（d1 形参传 segEnd、posBase 从 segStart 起），ArgmaxTreeReduce 后把 (bestVal[0], bestIdx[0]) 以两次 4B DataCopyPad 写 GM workspace（空段写 (-inf, INT32_MAX) 哨兵）；stage-2 kernel argmax_identity_<dt>_merge 以 totalWindows blocks launch，把本窗口 segPerWin 对 (val, globalIdx) 经 VECIN 队列载入 UB，一次 champion ArgmaxUpdate(laneMask=segPerWin) + ArgmaxTreeReduce（eq&Idx tie-break、nv-first-NaN-lock）选出 winner 后写 int64；host 用 torch::empty 分配 workspace、两 launch 同 stream 顺序提交，跨核可见性由 stream 顺序保证，无需屏障。(b) 同 launch 内两阶段（catsoftmax，门：cSplitCount>1 && inner>1 && !resident && !degenerate && blockNum>=S，host 精确镜像）：host 按 192KiB UB 预算取 blockRowsMax，S = max(ceil(C/blockRowsMax), floor(coreNum/(B*tiles))) 并 clamp，blockDim = min(B*tiles*S, coreNum)，tiling 增加 cSplitCount/cSplitRows/wsPitch 三字段并按每 (b,t,cb) 槽 2*wsPitch floats 分配 fp32 workspace（[maxB|sumB]）；kernel 逐 wave 按 group 对齐分派（每 wave floor(blockNum/S) 个 group，所有核以相同轮次各到达一次 SyncAll<true>()），SplitPartial 单读 slab 驻留 UB 后算块内 partial（MaxChunkReg/SumChunkReg）经 VECOUT TQue 写 [maxB|sumB] 槽，SyncAll<true>() 后 SplitNormalize 用 wsInQ 逐槽 CatMergeSlotReg 在线合并（maxRun=max；sumRun=sumRun*exp(oldMax-newMax)+sumB*exp(maxB-newMax)），再以 SoftmaxChunkSplitReg 双 pitch 从驻留 slab 归一化、legacy CopyChunkOut 写出。唯一设计偏离：块内 fp32 e 持久化改为归一化时 exp 复算（块数下限接近核数时 e 无法跨 SyncAll 边界存活；slab-only 驻留使 blockRows 翻倍、merge 流量减半）。

## 2. 性能问题模式

- 优化目标：消除 blockDim = min(outer, coreNum) 造成的核饥饿：外轴（B×tiles 或窗口数 d0）短于核数时长归约轴从不跨核切分，全部工作压在 1-4 个核上串行完成（catsoftmax case 18/19 的 2/4 核、argmaxidentity case 12 的 1 核），其余 60+ 个向量核空闲；把归约轴切成每核一段以补全并行度，同时让切段后的 slab 能 UB 常驻、把该路径的 GM 读由 3x 降为 1x。
- 适用数据流：host 定核公式为 blockDim = min(并行任务数, coreNum)、并行任务数只由外轴（batch×tile 数、窗口数）给出的归约型算子，且归约轴长而从未跨核切分；典型如同 launch 内按 (b,t) 做通道归约的 fused softmax（catsoftmax，channelTotal=2049）与低扇出 launch 的跨窗口选择归约（argmaxidentity Path B，s==1，d1=1000003）。
- Feature signature：`{"bottleneck": ["core-underutilization", "reduction-axis-not-split", "low-fanout-launch"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "reduce-axis-cross-core-split-two-stage-merge", "reduce_mode": "", "structure": ["reduce-axis-cross-core-split", "gm-fp32-workspace-partials", "two-stage-merge", "group-aligned-wave-syncall", "same-stream-second-launch-merge-kernel", "ub-resident-slab-single-read"]}`

## 3. 正确性红线

- SyncAll 悬挂/死锁：AIV-only 硬屏障必须被所有实际 launch 且继续执行的核以相同次数到达，任一核提前 return、wave 轮次不一致或 combine 非终止都会让全部核卡在同一 PC（507034）；本 run 靠 group 对齐 wave 分派规避，(b) 变体首次实证可用（全核等轮次 + PipeBarrier<PIPE_ALL> 写侧可见性 + 未使用 S_MTE3/MTE2_S 原生事件）
- 在线合并的 fp32 舍入：sum 折放 exp(maxB-maxG) 在 case 18 fp32 的 1e-5 容差下有舍入风险（估算 ~1e-6 量级相对误差）；回退方案是用全局 max 重新归约
- 精度首次失败：归一化输出 copy 误用 slabPitch 计算 staging 源 stride（staging 实为 tileInner pitch），case 18 fp32 因 slabPitch==tileInner 侥幸正确、其余 16 行 chunk 仅行 0 正确；性能探测确认显著收益后 1 次修复（复用 legacy CopyChunkOut）
- 门控外回归：catsoftmax 其余 18 case 中 4 个（case 1/11/13/20）六对均值 +2.2%~+3.1%（仅 case 1 逐对一致 ~+0.9us，二进制布局效应；tiling 结构体 +12B 亦有微小贡献），geomean 影响约 -0.3%；argmaxidentity 门控外 19 case 配对比值 0.976~1.050（均值 1.005，噪声带、无系统性回退）——后者是靠 tiling union 恢复 52B 才消除的（68B 形态会给门控外 19 case 每次 launch +0.4~1.1us）
- 标量 merge kernel 编译失败：CCE backend 无法切分标量浮点分支 / GetValue-SetValue / int64 标量写（clang frontend segfault，编译修复 #1），merge kernel 必须全向量队列化
- 尾块 C-block 掩码与空段哨兵：尾块的通道掩码、空段哨兵与归并初值必须同时正确，否则只在部分 shape 上显形

资源与硬件约束：

- 两阶段必须由独立 kernel launch 或 SyncAll<true>() 排序：(a) 走同 stream 顺序两次 launch（跨核可见性由 stream 顺序保证）；(b) 走 KERNEL_TYPE_MIX_AIV_1_0 + SyncAll<true>()，且所有实际 launch 的核必须以相同轮次到达屏障（group 对齐 wave 分派）
- 放大前必须先做最小探针：构造 grSegs=2、单 row、单 dtype 的隔离 case 确认两阶段路径能运行到完成（NEG-GR-SYNCALL-DEADLOCK 在 A5 上曾以 GM workspace + AIV-only SyncAll + combine 的组合确定性死锁 507034，所有已 launch 的核卡在同一 PC）
- 写侧可见性用 SyncAll 内部已含的 PipeBarrier<PIPE_ALL>，不要引入 S_MTE3/MTE2_S 原生事件（NEG-S-MTE3-MIX-SYNCALL：在 MIX_AIV_1_0 + 硬 SyncAll 上下文触发设备 507035）；TQue 管理的核内 V_MTE3/MTE2_V 事件不受影响
- host 门控必须精确镜像 kernel 门与 UB 预算公式，否则出现 ws 未分配而 kernel 走 split 的缺配
- (a) 变体的 tiling 结构体字节数必须保持不变：每核逐字节标量拷贝 tiling 是固定 launch 开销，字段追加（52B→68B）会给门控外全部 case 每次 launch +0.4~1.1us；用 union overlay 到内核从不读取的 totalOutputs/totalLength 槽位可零成本携带新参数
- 归一化写出必须复用 legacy CopyChunkOut（staging 的源 stride 是 tileInner pitch 而非 slabPitch；case 18 fp32 因 slabPitch==tileInner 侥幸正确）

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- host 定核公式为 blockDim = min(并行任务数, coreNum) 且并行任务数只由外轴给出——本 run 两例：catsoftmax workTotal = B×ceil(S/tileInner) = 2/4（pybind blockDim = min(workTotal, coreNum)）；argmaxidentity Path B 的 totalWindows = d0 = 1（blockDim = min(64,d0)）
- 归约轴长且从未被切分：catsoftmax channelTotal=2049、argmaxidentity d1=1000003；核饥饿是结构性证据而非推测（case12 Block Num=1、aiv_vec_time 114.9/117.0us、vec_ratio 0.982、63/64 核闲置）
- 归约具有可结合/可折放的合并规则：max 逐元素 max、argmax 带 tie-break 的全序逐对归并、softmax 的 sum 以 exp(maxB-maxG) 在线重缩放折放
- top wall 落在该路径上并主导 geomean：catsoftmax case 18/19（fp32 [2,1024,511]+[2,1025,511] 与 bf16 [4,1024,255]+[4,1025,255]）单独把 geomean 从 ~26us 拉到 32.5us；argmaxidentity case 12 是 20 case 中唯一 Block Num=1 的 launch
- (b) 变体还需：kernel 可声明 KERNEL_TYPE_MIX_AIV_1_0 使 SyncAll() 硬同步可用，且切段后每核 slab 能装入 UB 预算（192KiB）而顺带把 GM 读 3x 降为 1x

不适用：

- 外轴已足够占满核数（blockDim >= coreNum）时不适用：切段只增加 partial 写入与合并开销，没有核饥饿可补——门控必须与之互斥（argmaxidentity：mode==1 && totalWindows<coreNum && d1>=262144；catsoftmax：cSplitCount>1 && inner>1 && !resident && !degenerate && blockNum>=S）
- 归约轴太短、段负载不足以摊销合并阶段（第二次 launch 或 SyncAll 屏障）时不适用：argmaxidentity 以 d1>=262144 为下限
- 已有 degenerate / resident 快路径覆盖的形状不在本机制域内：split 路径必须与之互斥，不得覆盖已优化的 case
- 要求合并结果与单遍串行逐位一致、且归约是浮点求和的场景须先对账舍入：fp32 sum 折放有舍入风险（本 run case 18 fp32 1e-5 容差）
- 归并阶段不能用标量实现：CCE 不支持 __aicore__ 标量浮点分支 / 标量 GM 读写（GetValue/SetValue）/ int64 标量写，merge kernel 必须全向量队列化

## 5. 实施步骤

1. 先量化核饥饿与并行度结构：算清 host 定核公式（blockDim = min(并行任务数, coreNum)）与并行任务数的来源，确认长归约轴从不跨核切分（catsoftmax workTotal=B×ceil(S/tileInner)=2/4；argmaxidentity totalWindows=d0=1），并用 profiling 坐实核数与瓶颈一一对应（case12 Block Num=1、aiv_vec_time 114.9/117.0us、vec_ratio 0.982）
2. 在放大前先做最小探针：构造 grSegs=2、单 row、单 dtype 的隔离 case 跑通两阶段路径（NEG-GR-SYNCALL-DEADLOCK 红线），确认 SyncAll<true>()（或同 stream 双 launch）在该工程 launch 方式下可用
3. host 侧切段并精确镜像 kernel 门：把归约轴切成 S/segPerWin 段（catsoftmax 按 192KiB UB 预算取 blockRowsMax，S = max(ceil(C/blockRowsMax), floor(coreNum/(B*tiles))) 并 clamp，blockDim = min(B*tiles*S, coreNum)；argmaxidentity segPerWin = coreNum/totalWindows、segLen = alignUp(ceil(d1/segPerWin),64)），新增 tiling 字段并分配 partial workspace（fp32，每 (b,t,cb) 槽 2*wsPitch floats 的 [maxB|sumB] 或 (val, idx) 对）
4. kernel 侧写 partial：每核只读自己那一段（(b) 顺带 slab UB 常驻，GM 读 3x→1x），算出块内 partial 向量/值写 workspace，空段写哨兵（argmaxidentity 为 (-inf, INT32_MAX)、归并初始化 maxRun=-inf 使首槽 exp(-inf-maxB)=0 安全）
5. 合并与写出：(a) 独立归并 kernel 同 stream 第二次 launch，逐窗口把 partial 向量归并后写最终输出；(b) group 对齐 wave 分派（每 wave floor(blockNum/S) 个 group）后 SyncAll<true>()，各核在线合并本 group 全部槽（max 逐元素 / sum 折放 exp(maxB-maxG)），再从驻留 slab 归一化并用 legacy CopyChunkOut 写出

## 6. LLM 前置问题

- 目标实现是否满足：host 定核公式为 blockDim = min(并行任务数, coreNum) 且并行任务数只由外轴给出——本 run 两例：catsoftmax workTotal = B×ceil(S/tileInner) = 2/4（pybind blockDim = min(workTotal, coreNum)）；argmaxidentity Path B 的 totalWindows = d0 = 1（blockDim = min(64,d0)）？
- 目标实现是否满足：归约轴长且从未被切分：catsoftmax channelTotal=2049、argmaxidentity d1=1000003；核饥饿是结构性证据而非推测（case12 Block Num=1、aiv_vec_time 114.9/117.0us、vec_ratio 0.982、63/64 核闲置）？
- 目标实现是否满足：归约具有可结合/可折放的合并规则：max 逐元素 max、argmax 带 tie-break 的全序逐对归并、softmax 的 sum 以 exp(maxB-maxG) 在线重缩放折放？
- 目标实现是否满足：top wall 落在该路径上并主导 geomean：catsoftmax case 18/19（fp32 [2,1024,511]+[2,1025,511] 与 bf16 [4,1024,255]+[4,1025,255]）单独把 geomean 从 ~26us 拉到 32.5us；argmaxidentity case 12 是 20 case 中唯一 Block Num=1 的 launch？
- 目标实现是否满足：(b) 变体还需：kernel 可声明 KERNEL_TYPE_MIX_AIV_1_0 使 SyncAll() 硬同步可用，且切段后每核 slab 能装入 UB 预算（192KiB）而顺带把 GM 读 3x 降为 1x？
- 是否命中排除条件：外轴已足够占满核数（blockDim >= coreNum）时不适用：切段只增加 partial 写入与合并开销，没有核饥饿可补——门控必须与之互斥（argmaxidentity：mode==1 && totalWindows<coreNum && d1>=262144；catsoftmax：cSplitCount>1 && inner>1 && !resident && !degenerate && blockNum>=S）？
- 是否命中排除条件：归约轴太短、段负载不足以摊销合并阶段（第二次 launch 或 SyncAll 屏障）时不适用：argmaxidentity 以 d1>=262144 为下限？
- 是否命中排除条件：已有 degenerate / resident 快路径覆盖的形状不在本机制域内：split 路径必须与之互斥，不得覆盖已优化的 case？
- 是否命中排除条件：要求合并结果与单遍串行逐位一致、且归约是浮点求和的场景须先对账舍入：fp32 sum 折放有舍入风险（本 run case 18 fp32 1e-5 容差）？
- 是否命中排除条件：归并阶段不能用标量实现：CCE 不支持 __aicore__ 标量浮点分支 / 标量 GM 读写（GetValue/SetValue）/ int64 标量写，merge kernel 必须全向量队列化？

## 7. 验收标准

正确性：

- catsoftmax：20/20 PASS（1 次精度修复；最差 case 18 MERE 3.769e-07 < 1e-05）
- argmaxidentity：20/20 PASS，int64 bit-exact vs torch.argmax（段内复用 champion ArgmaxComputeChunkPathB+ArgmaxTreeReduce 逐指令不变，跨段归并与单遍 first-wins / NaN-aware 语义等价，空段 -inf 哨兵不参与归并）
- 未触碰路径原样保留：(b) 的 degenerate / resident 路径与其余 18 case 零语义接触；(a) 的门控外 19 case 逐字段走 champion 路径

性能：

- catsoftmax：形式化 ABBA 6 对（12 runs）全部无歧义（pair ratio 0.8017~0.8098），geomean 32.4653→26.1551us（1.2413x）；case 18 fp32 289.614→29.7188us、case 19 bf16 221.0955→24.0667us（约 9.7x/9.2x，blockNum 2/4→64）
- argmaxidentity：formal ABBA 10/10 paired measurements faster（geomean_ops 41.678→36.6475us，1.1373x）；case 12 [1,1000003] bf16 117.16→15.69us（ratio 0.1339，stage-1 ~12.4us + merge ~3.0us）
- 副作用兑现：(b) 该路径每 block slab UB 常驻，GM 读由 3x 降为 1x
- 门控外扰动已披露：catsoftmax case 1/11/13/20 六对均值 +2.2%~+3.1%（geomean 影响约 -0.3%）；argmaxidentity 门控外 19 case 比例 0.976~1.050（均值 1.005）

回滚信号：

- SyncAll 悬挂或设备报 507034/507035：核未以相同轮次到达屏障，或引入了 S_MTE3/MTE2_S 原生事件
- 门控外任一 case 系统性回退：catsoftmax 有 case 回归 >2% 即回滚；argmaxidentity 门控外 case 超出 0.976~1.050 噪声带即回滚
- workspace 缺配（host 门与 kernel 门不一致，ws 未分配但 kernel 走 split）
- 在线合并舍入使 fp32 case 精度超出 1e-5 容差
- tiling 结构体膨胀导致门控外固定 launch 开销（52B→68B 的 +0.4~1.1us 形态）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：s-mte3-event-mix-syncall-error

- loop_20260916_165309 status=accepted, speedup=1.2413, precision=20/20 PASS（1 次精度修复；最差 case 18 MERE 3.769e-07 < 1e-05））
- loop_20260915_234239 status=accepted, speedup=1.1373, precision=20/20 PASS（int64 bit-exact vs torch.argmax））

## 检索卡（短卡）

动作：把从未切分的长归约轴切成每核一段，各核写 partial 到 GM workspace，再做两级合并。
适用：host 定核 min(并行任务数,coreNum) 且并行任务数只由外轴给出，外轴短于核数；归约具可折放合并规则。
限制：SyncAll 须所有已 launch 核同轮次到达否则 507034 死锁；勿引入 S_MTE3/MTE2_S 原生事件；merge 禁标量实现。
范围：reduction 的通道归约与跨窗口选择归约 launch。
检索词：归约轴切分、GM workspace、SyncAll<true>、group 对齐 wave、flash 在线重缩放、CopyChunkOut
机会：blockDim=min(外轴,coreNum) 使长归约轴留在 1-4 核串行，60+ 向量核空闲。
代价：合并阶段需 workspace 往返与屏障/额外 launch；fp32 sum 折放有舍入风险。
