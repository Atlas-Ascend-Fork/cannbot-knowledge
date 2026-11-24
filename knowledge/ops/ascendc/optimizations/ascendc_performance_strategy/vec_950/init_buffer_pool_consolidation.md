---
type: Optimization
title: 缓冲池化：InitBuffer 14→4、GetPhyAddr 11→1
description: batch_norm_group_norm_slow_thinking 的 aiv_scalar 占 aiv_time 的 84.5-85.2% 且与数据量反向相关（每核数据最少的 blk=12 标量时间反而最高），属固定开销主导。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/init-buffer-pool-consolidation.md
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
      "池内各子缓冲的字节偏移必须按 InitBuffer 内部同样的 32B 上取整规则手工构造，且偏移不得重叠；容量按 11 个子缓冲 size 之和（各自上取整到 32B）预留",
      "队列缓冲（tileIn/tileOut/paramRaw）必须保留自身的 InitBuffer 与队列语义，池化只覆盖普通的 VECCALC TBuf",
      "只允许改 Init 期的描述符结构（InitBuffer / Init 期 GetPhyAddr）；缓冲内容、对齐语义、stats 数学、数据搬运与 tiling 读取必须逐字节不变（本 run 以位相同构造保证）",
      "收益量级小且单次成本未直测：本 run 在 ~4.2us 的算子上每核削掉约 0.36us 标量固定成本，而单次 InitBuffer/GetPhyAddr 的绝对成本在证据中标注为 UNKNOWN（仅 HYPOTHESIS 为 50-150 scalar cycles），归因必须靠 aiv_scalar 的实测 delta",
      "SetGlobalBuffer 与 param chunk 本轮保持不变，以便把收益隔离到 InitBuffer + GetPhyAddr 这一份份额上"
    ],
    "excluded_conditions": [
      "队列缓冲不适用池化：其 InitBuffer 与队列语义必须保留（本 run tileIn/tileOut/paramRaw 未动）",
      "kernel Init 不在每核每 launch 的关键路径上（blockDim 远小于物理核数、或 Init 被其它工作遮蔽）时收益被摊薄",
      "Init 固定成本已被其它方向定位并消掉时不适用：本 run 已证伪 tiling GM 读粒度（byte-loop -> word-loop 仅 aiv_scalar 3.452 -> 3.392us，wall +1.48% < 5% 门槛）与 stats-chain scope 融合（aiv_scalar +0.060us 符号相反，wall +2.37% < 5% 门槛）是标量墙的主因"
    ],
    "required_conditions": [
      "kernel Init 在每个 launch 上被完整付出且 per-core 固定成本占比高：本 run 9 个测试 shape 全部 blockDim = totalGroups（8 或 12）、每核恰好 1 组走 ProcessGroupResident，Init 全程外露在关键路径上，被每核每 launch 付 8-12 次",
      "标量管道占 aiv_time 的绝对多数且与数据量无关：本 run aiv_scalar 3.650/3.711/3.659us = 84.5-85.2%（aiv_vec 0.57-0.59us、aiv_mte2 0.69-0.73us）；blk=12（L=63，每核数据最少）的标量时间 3.936-4.010us 反而高于 blk=8 的 3.481-3.561us，说明标量墙是固定开销主导而非数据量驱动",
      "存在一批同构的普通 VECCALC TBuf，其 Init 期动作只有 InitBuffer 与 GetPhyAddr 两类，且彼此无别名依赖（本 run 11 个：workBufA/B、max/scale/total/mean/rstd slots、gnW/gnB/bnScale/bnShift）",
      "有未触碰的管道分量用于收益归因（本 run vec/mte 保持不变）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "batch_norm_group_norm_slow_thinking",
      "operator_class": "fused-composite",
      "pairs": 4,
      "precision": "9/9 PASS",
      "run_id": "<run-id>",
      "speedup": 1.086,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "kernel-init-fixed-cost",
      "per-call-initbuffer-descriptor",
      "init-time-getphyaddr",
      "scalar-pipe-wall"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "init-buffer-pool-consolidation",
    "structure": [
      "single-pool-initbuffer",
      "fixed-byte-offset-carving",
      "queue-buffers-unchanged",
      "bit-identical-buffer-contents"
    ]
  },
  "generality": "op_class",
  "id": "INIT-BUFFER-POOL-CONSOLIDATION",
  "implementation_steps": [
    "清点 Init 期的普通 VECCALC TBuf 集合与其 size 来源（本 run 11 个：workBufA/B、max/scale/total/mean/rstd slots、gnW/gnB/bnScale/bnShift），确认彼此无别名依赖、队列缓冲不在集合内",
    "用一个 scalarPool_ TBuf 的 1 次 InitBuffer 取代这 11 次 InitBuffer，容量取 11 个子 size 之和，每个子 size 按 InitBuffer 内部同样的 32B 规则上取整",
    "把 11 次 Init 期 GetPhyAddr 抽取替换为 1 次池 GetPhyAddr + 11 个 32B 对齐的固定字节偏移派生（偏移由 tiling 字段算出：workLen 来自 maxPartials_、slotLen=256B、affineLen 来自 numChannels_）",
    "members 从 11 个普通 TBuf 收敛为 scalarPool_；queue buffers（tileIn/tileOut/paramRaw）保留各自的 InitBuffer 与语义不动",
    "对 Init 面做对账（本 run 14 -> 4 InitBuffer、11 -> 1 次 Init 期 GetPhyAddr），并以 aiv_scalar 的 delta 与精度门验收（本 run -0.359us、9/9 PASS）"
  ],
  "intent": "削减每核每次 launch 都要付的 kernel-Init 描述符/记账固定成本：14 次 pipe_->InitBuffer（3 个队列缓冲 + 11 个普通 VECCALC TBuf）与 11 次 Init 期 TBuf GetPhyAddr 抽取，把普通缓冲折叠成一个按固定偏移切分的池，只保留一次池级 InitBuffer 与一次池级 GetPhyAddr。",
  "mechanism": "init-buffer-pool-consolidation：把 11 个普通 VECCALC TBuf 的 InitBuffer 合并成一个 raw InitBuffer 的 VECCALC 区域，各子缓冲按手工计算的固定 32B 对齐字节偏移切分（偏移由 tiling 字段推出，与原先各自的 size 同源），Init 期由一次池 GetPhyAddr + 偏移派生取代 11 次 TBuf GetPhyAddr 抽取；3 个队列缓冲（tileIn/tileOut/paramRaw）保留原 InitBuffer 与队列语义。所有队列操作、per-group 常驻路径代码、stats 数学、数据搬运、tiling 读取与缓冲内容都不变，仅 Init 期缓冲描述符的组织方式改变，故数值位相同。无运行期门控：Init 面（14 -> 4 InitBuffer、11 -> 1 GetPhyAddr）对全部 shape 与 dtype 生效。",
  "name": "缓冲池化：InitBuffer 14→4、GetPhyAddr 11→1",
  "operator_class": "fused-composite",
  "operator_scope": "kernel Init 在每核每 launch 的关键路径上全程外露、且 Init 期存在一批只做 InitBuffer + GetPhyAddr 的普通 VECCALC TBuf、标量管道为节拍源的算子",
  "principle": "当 kernel Init 每核每 launch 都被完整付出时，Init 面的每一次 InitBuffer（对齐算术 + TPipe UB 池切分 + 描述符落存储）和 Init 期 GetPhyAddr 都是标量管道的固定成本；当标量管道占 aiv_time 的 84.5-85.2% 且其时间随每核数据量反向变化（blk=12 的 L=63 比 blk=8 更慢）时，削减的对象应是固定开销而非数据量。把 N 个同构描述符合并为 1 个池 + N 个常量偏移，把 N 次逐调用成本换成 1 次，是纯 Init 面的结构收益，与数据路径无关。",
  "related_anti_patterns": [
    "aggregate-buffer-alias-scalar-war"
  ],
  "risks": [
    "收益量级小，且单次成本未直测：本 run 在 ~4.2us 的算子上每核削掉约 0.36us（aiv_scalar -0.359us），而单次 InitBuffer/GetPhyAddr 的绝对成本在证据中标注为 UNKNOWN；效果只能以 aiv_scalar 实测 delta 判定（预注册门槛为 5% 或 aiv_scalar >= 0.1us）",
    "偏移手工构造必须与 InitBuffer 的 32B 上取整规则逐字一致：任一处漏掉上取整或偏移重叠，会静默改写相邻子缓冲（本池化前的失败模式见 aggregate-buffer-alias-scalar-war：同一区域被两个用途共用导致标量 WAR 覆盖）",
    "池化后相邻子缓冲共享同一 UB 页，越界写不再被独立 TBuf 边界拦下，只能靠对齐/容量静态对账（本 run 以位相同构造 + 9/9 精度兜底）",
    "改的是 Init 面结构而非数据路径，若把队列缓冲一并池化会破坏队列语义（TQue 的 slot 切分与同步依赖），队列缓冲必须排除在集合外",
    "跨会话漂移会淹没小收益：同一二进制实测 dev0 4.0369us vs dev1 4.5549us（约 13%），故采用预注册 5%/0.1us 门槛与 ABBA 配对（本 run 4/4 对有效、12/12 case 全胜）"
  ],
  "slug": "init-buffer-pool-consolidation",
  "summary": "batch_norm_group_norm_slow_thinking 的 aiv_scalar 占 aiv_time 的 84.5-85.2% 且与数据量反向相关（每核数据最少的 blk=12 标量时间反而最高），属固定开销主导。把 Init 期 11 个普通 VECCALC TBuf（workBufA/B、max/scale/total/mean/rstd slots、gnW/gnB/bnScale/bnShift）的 InitBuffer 折叠成一个按 32B 固定偏移切分的池，并用 1 次池 GetPhyAddr + 11 个偏移派生取代 11 次 Init 期 GetPhyAddr：Init 面 14 -> 4 InitBuffer、11 -> 1 GetPhyAddr，队列缓冲保留自身 InitBuffer 与语义，缓冲内容/偏移按构造位相同。形式化 ABBA 配对 4/4 对有效、12/12 case 全胜，wall geomean 4.5680 -> 4.2062us（+8.60%，1.086x），aiv_scalar -0.359us 而 vec/mte 不变，精度 9/9 PASS。",
  "verification": {
    "correctness": [
      "精度 9/9 PASS，首次尝试即通过，并在用于配对运行的确切候选二进制上复验；未消耗修复预算",
      "缓冲内容、对齐语义、stats 数学、数据搬运与 tiling 读取均未变（位相同构造），任何精度失败都指向实现 bug 而非机制边界"
    ],
    "performance": [
      "形式化 ABBA 配对：4/4 对有效，12/12 case 胜，wall geomean 4.5680 -> 4.2062us（+8.60%，1.086x，dev1）",
      "aiv_scalar -0.359us 而 aiv_vec / aiv_mte2 不变，满足预注册的 5% / 0.1us 门槛，并验证了 InitBuffer 每调用固定成本假设",
      "方向性证据：blk=12（每核数据最少）标量时间高于 blk=8；d001（tiling 读粒度）与 d002（stats scope 融合）两项对照均未过 5% 门槛，说明本方向的收益不可由它们解释"
    ],
    "rollback_signals": [
      "aiv_scalar delta < 0.1us 或配对 wall 改善 < 5%：InitBuffer 每调用固定成本假设被证伪（本 run 已越过该门槛，故门槛同时是后续复现的判定线）",
      "aiv_vec / aiv_mte2 出现超出噪声带的变化：说明改动溢出 Init 面，收益归因不成立",
      "任何精度 case 失败：位相同构造被破坏（偏移错位/重叠）",
      "偏移与 InitBuffer 的 32B 上取整不一致导致相邻缓冲被改写"
    ]
  }
}
-->

# 性能优化策略：缓冲池化：InitBuffer 14→4、GetPhyAddr 11→1

batch_norm_group_norm_slow_thinking 的 aiv_scalar 占 aiv_time 的 84.5-85.2% 且与数据量反向相关（每核数据最少的 blk=12 标量时间反而最高），属固定开销主导。把 Init 期 11 个普通 VECCALC TBuf（workBufA/B、max/scale/total/mean/rstd slots、gnW/gnB/bnScale/bnShift）的 InitBuffer 折叠成一个按 32B 固定偏移切分的池，并用 1 次池 GetPhyAddr + 11 个偏移派生取代 11 次 Init 期 GetPhyAddr：Init 面 14 -> 4 InitBuffer、11 -> 1 GetPhyAddr，队列缓冲保留自身 InitBuffer 与语义，缓冲内容/偏移按构造位相同。形式化 ABBA 配对 4/4 对有效、12/12 case 全胜，wall geomean 4.5680 -> 4.2062us（+8.60%，1.086x），aiv_scalar -0.359us 而 vec/mte 不变，精度 9/9 PASS。

## 1. 原理

当 kernel Init 每核每 launch 都被完整付出时，Init 面的每一次 InitBuffer（对齐算术 + TPipe UB 池切分 + 描述符落存储）和 Init 期 GetPhyAddr 都是标量管道的固定成本；当标量管道占 aiv_time 的 84.5-85.2% 且其时间随每核数据量反向变化（blk=12 的 L=63 比 blk=8 更慢）时，削减的对象应是固定开销而非数据量。把 N 个同构描述符合并为 1 个池 + N 个常量偏移，把 N 次逐调用成本换成 1 次，是纯 Init 面的结构收益，与数据路径无关。

实现机制：init-buffer-pool-consolidation：把 11 个普通 VECCALC TBuf 的 InitBuffer 合并成一个 raw InitBuffer 的 VECCALC 区域，各子缓冲按手工计算的固定 32B 对齐字节偏移切分（偏移由 tiling 字段推出，与原先各自的 size 同源），Init 期由一次池 GetPhyAddr + 偏移派生取代 11 次 TBuf GetPhyAddr 抽取；3 个队列缓冲（tileIn/tileOut/paramRaw）保留原 InitBuffer 与队列语义。所有队列操作、per-group 常驻路径代码、stats 数学、数据搬运、tiling 读取与缓冲内容都不变，仅 Init 期缓冲描述符的组织方式改变，故数值位相同。无运行期门控：Init 面（14 -> 4 InitBuffer、11 -> 1 GetPhyAddr）对全部 shape 与 dtype 生效。

## 2. 性能问题模式

- 优化目标：削减每核每次 launch 都要付的 kernel-Init 描述符/记账固定成本：14 次 pipe_->InitBuffer（3 个队列缓冲 + 11 个普通 VECCALC TBuf）与 11 次 Init 期 TBuf GetPhyAddr 抽取，把普通缓冲折叠成一个按固定偏移切分的池，只保留一次池级 InitBuffer 与一次池级 GetPhyAddr。
- 适用数据流：kernel Init 在每核每 launch 的关键路径上全程外露、且 Init 期存在一批只做 InitBuffer + GetPhyAddr 的普通 VECCALC TBuf、标量管道为节拍源的算子
- Feature signature：`{"bottleneck": ["kernel-init-fixed-cost", "per-call-initbuffer-descriptor", "init-time-getphyaddr", "scalar-pipe-wall"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "init-buffer-pool-consolidation", "structure": ["single-pool-initbuffer", "fixed-byte-offset-carving", "queue-buffers-unchanged", "bit-identical-buffer-contents"]}`

## 3. 正确性红线

- 收益量级小，且单次成本未直测：本 run 在 ~4.2us 的算子上每核削掉约 0.36us（aiv_scalar -0.359us），而单次 InitBuffer/GetPhyAddr 的绝对成本在证据中标注为 UNKNOWN；效果只能以 aiv_scalar 实测 delta 判定（预注册门槛为 5% 或 aiv_scalar >= 0.1us）
- 偏移手工构造必须与 InitBuffer 的 32B 上取整规则逐字一致：任一处漏掉上取整或偏移重叠，会静默改写相邻子缓冲（本池化前的失败模式见 aggregate-buffer-alias-scalar-war：同一区域被两个用途共用导致标量 WAR 覆盖）
- 池化后相邻子缓冲共享同一 UB 页，越界写不再被独立 TBuf 边界拦下，只能靠对齐/容量静态对账（本 run 以位相同构造 + 9/9 精度兜底）
- 改的是 Init 面结构而非数据路径，若把队列缓冲一并池化会破坏队列语义（TQue 的 slot 切分与同步依赖），队列缓冲必须排除在集合外
- 跨会话漂移会淹没小收益：同一二进制实测 dev0 4.0369us vs dev1 4.5549us（约 13%），故采用预注册 5%/0.1us 门槛与 ABBA 配对（本 run 4/4 对有效、12/12 case 全胜）

资源与硬件约束：

- 池内各子缓冲的字节偏移必须按 InitBuffer 内部同样的 32B 上取整规则手工构造，且偏移不得重叠；容量按 11 个子缓冲 size 之和（各自上取整到 32B）预留
- 队列缓冲（tileIn/tileOut/paramRaw）必须保留自身的 InitBuffer 与队列语义，池化只覆盖普通的 VECCALC TBuf
- 只允许改 Init 期的描述符结构（InitBuffer / Init 期 GetPhyAddr）；缓冲内容、对齐语义、stats 数学、数据搬运与 tiling 读取必须逐字节不变（本 run 以位相同构造保证）
- 收益量级小且单次成本未直测：本 run 在 ~4.2us 的算子上每核削掉约 0.36us 标量固定成本，而单次 InitBuffer/GetPhyAddr 的绝对成本在证据中标注为 UNKNOWN（仅 HYPOTHESIS 为 50-150 scalar cycles），归因必须靠 aiv_scalar 的实测 delta
- SetGlobalBuffer 与 param chunk 本轮保持不变，以便把收益隔离到 InitBuffer + GetPhyAddr 这一份份额上

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- kernel Init 在每个 launch 上被完整付出且 per-core 固定成本占比高：本 run 9 个测试 shape 全部 blockDim = totalGroups（8 或 12）、每核恰好 1 组走 ProcessGroupResident，Init 全程外露在关键路径上，被每核每 launch 付 8-12 次
- 标量管道占 aiv_time 的绝对多数且与数据量无关：本 run aiv_scalar 3.650/3.711/3.659us = 84.5-85.2%（aiv_vec 0.57-0.59us、aiv_mte2 0.69-0.73us）；blk=12（L=63，每核数据最少）的标量时间 3.936-4.010us 反而高于 blk=8 的 3.481-3.561us，说明标量墙是固定开销主导而非数据量驱动
- 存在一批同构的普通 VECCALC TBuf，其 Init 期动作只有 InitBuffer 与 GetPhyAddr 两类，且彼此无别名依赖（本 run 11 个：workBufA/B、max/scale/total/mean/rstd slots、gnW/gnB/bnScale/bnShift）
- 有未触碰的管道分量用于收益归因（本 run vec/mte 保持不变）

不适用：

- 队列缓冲不适用池化：其 InitBuffer 与队列语义必须保留（本 run tileIn/tileOut/paramRaw 未动）
- kernel Init 不在每核每 launch 的关键路径上（blockDim 远小于物理核数、或 Init 被其它工作遮蔽）时收益被摊薄
- Init 固定成本已被其它方向定位并消掉时不适用：本 run 已证伪 tiling GM 读粒度（byte-loop -> word-loop 仅 aiv_scalar 3.452 -> 3.392us，wall +1.48% < 5% 门槛）与 stats-chain scope 融合（aiv_scalar +0.060us 符号相反，wall +2.37% < 5% 门槛）是标量墙的主因

## 5. 实施步骤

1. 清点 Init 期的普通 VECCALC TBuf 集合与其 size 来源（本 run 11 个：workBufA/B、max/scale/total/mean/rstd slots、gnW/gnB/bnScale/bnShift），确认彼此无别名依赖、队列缓冲不在集合内
2. 用一个 scalarPool_ TBuf 的 1 次 InitBuffer 取代这 11 次 InitBuffer，容量取 11 个子 size 之和，每个子 size 按 InitBuffer 内部同样的 32B 规则上取整
3. 把 11 次 Init 期 GetPhyAddr 抽取替换为 1 次池 GetPhyAddr + 11 个 32B 对齐的固定字节偏移派生（偏移由 tiling 字段算出：workLen 来自 maxPartials_、slotLen=256B、affineLen 来自 numChannels_）
4. members 从 11 个普通 TBuf 收敛为 scalarPool_；queue buffers（tileIn/tileOut/paramRaw）保留各自的 InitBuffer 与语义不动
5. 对 Init 面做对账（本 run 14 -> 4 InitBuffer、11 -> 1 次 Init 期 GetPhyAddr），并以 aiv_scalar 的 delta 与精度门验收（本 run -0.359us、9/9 PASS）

## 6. LLM 前置问题

- 目标实现是否满足：kernel Init 在每个 launch 上被完整付出且 per-core 固定成本占比高（本 run 9 个 shape 全部 blockDim = totalGroups = 8/12、每核 1 组，Init 全程外露）？
- 目标实现是否满足：标量管道占 aiv_time 的绝对多数且与数据量无关（本 run aiv_scalar 84.5-85.2%，blk=12 标量时间反高于 blk=8）？
- 目标实现是否满足：存在一批同构的普通 VECCALC TBuf，其 Init 期动作只有 InitBuffer 与 GetPhyAddr 两类且彼此无别名依赖（本 run 11 个）？
- 目标实现是否满足：有未触碰的管道分量用于收益归因（本 run vec/mte 保持不变）？
- 是否命中排除条件：队列缓冲（tileIn/tileOut/paramRaw）必须保留自身 InitBuffer 与队列语义？
- 是否命中排除条件：kernel Init 不在每核每 launch 关键路径上（blockDim 远小于核数或 Init 被遮蔽）时收益被摊薄？
- 是否命中排除条件：Init 固定成本已被其它方向定位并消掉（本 run 的 tiling 读粒度与 stats scope 融合两项均未过 5% 门槛，不构成主因）？

## 7. 验收标准

正确性：

- 精度 9/9 PASS，首次尝试即通过，并在用于配对运行的确切候选二进制上复验；未消耗修复预算
- 缓冲内容、对齐语义、stats 数学、数据搬运与 tiling 读取均未变（位相同构造），任何精度失败都指向实现 bug 而非机制边界

性能：

- 形式化 ABBA 配对：4/4 对有效，12/12 case 胜，wall geomean 4.5680 -> 4.2062us（+8.60%，1.086x，dev1）
- aiv_scalar -0.359us 而 aiv_vec / aiv_mte2 不变，满足预注册的 5% / 0.1us 门槛，并验证了 InitBuffer 每调用固定成本假设
- 方向性证据：blk=12（每核数据最少）标量时间高于 blk=8；d001（tiling 读粒度）与 d002（stats scope 融合）两项对照均未过 5% 门槛，说明本方向的收益不可由它们解释

回滚信号：

- aiv_scalar delta < 0.1us 或配对 wall 改善 < 5%：InitBuffer 每调用固定成本假设被证伪（本 run 已越过该门槛，故门槛同时是后续复现的判定线）
- aiv_vec / aiv_mte2 出现超出噪声带的变化：说明改动溢出 Init 面，收益归因不成立
- 任何精度 case 失败：位相同构造被破坏（偏移错位/重叠）
- 偏移与 InitBuffer 的 32B 上取整不一致导致相邻缓冲被改写

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：aggregate-buffer-alias-scalar-war

- loop_20260913_154221（pairs=4, status=accepted, speedup=1.086, precision=9/9 PASS）

## 检索卡（短卡）

动作：把 Init 期一批同构普通 VECCALC TBuf 的 InitBuffer 折叠成一个按 32B 固定偏移切分的池，用一次池级 GetPhyAddr 取代逐缓冲抽取。
适用：kernel Init 每核每 launch 全程外露、标量占 aiv_time 绝对多数。
限制：偏移须按 InitBuffer 同样的 32B 上取整规则构造且不重叠；队列缓冲须保留自身语义。
范围：fused-composite kernel 的 Init 期普通 TBuf 描述符。
检索词：InitBuffer、GetPhyAddr、TPipe、VECCALC TBuf、标量管道、aiv_scalar
机会：每核每 launch 付 InitBuffer/GetPhyAddr 固定成本，aiv_scalar 占 84.5-85.2%。
代价：收益小（每核约 0.36us）且单次成本未直测；池化后越界写不再被独立 TBuf 拦下。
