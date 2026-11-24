---
type: Optimization
title: 每核计划预分区：host 复刻 seg-split 语义下发私有 chunk 子表
description: 把每核重复的全量chunk表扫描、解码与overlap数学移出kernel，改由host按seg-split语义预切成每核私有子表。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/host-per-core-plan-prepartition.md
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
      "host 复刻的设备 seg-split 语义必须逐字节等价：本 run 用共享计划布局 FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 每 chunk 6-u32 的 FlattenPlanEntry（srcLo/srcHi/dstOff/byteLen/isZero/pad），plan 张量按 264+24*E 字节精确上传，host 断言 numChunks<=128",
      "每核计划子表必须自定位：Init 只做 3 次标量 GM 头读 + 一次 MTE2 DataCopyPad 把本核 24*cnt 字节子表搬进 TBuf(3072B)（事件 7 MTE2_S），Process 只对本核 cnt 条 entry 做 cnt*5 次 GetValue 解码后执行 CopyRange/ZeroRange",
      "计划表偏移/宽度的单位必须与 entry 宽度一致：本 run round_01 因 Init 计划子表 GM 偏移漏乘 FLATTEN_PLAN_ENTRY_U32 导致精度 20/20 失败，round_02 一行修复后才通过——这类 off-by-unit 错误只在 20/20 bit-exact 门禁下暴露",
      "CopyRange/ZeroRange 的数据搬运路径必须逐字节不变（DataCopyPad 64KB tile、同步点、zero-chunk 处理），收益归因只能落在被删除的标量扫描、解码、overlap 数学与非命中分支上",
      "删除 useBulkIdxPath 双路径后必须确认没有其它入口仍按旧的全表布局读计划；chunk 列表构建语义本身不变，被替换的只是它的下发形式"
    ],
    "excluded_conditions": [
      "chunk 归属不能由 host 静态决定（依赖运行时数据或需要动态负载均衡）时不适用：本机制的前提是切分规则、chunk 表与核数在 host 侧全部已知",
      "numChunks 很小或核数很少、per-core 全表扫描本身不构成可测成本时没有可消除对象",
      "若节省来自『恒等条件下跳过计算』而非『把扫描搬到 host 并预切成每核子表』，属 host-gated-cheap-path（静态条件门控）的域；若节省来自扁平化 tile 表生成，属 flat-element-full-tile-tiling 的域——本机制特指 per-core 私有 chunk 子表的预切分",
      "若数据搬运路径本身要被改动（tile 大小/同步策略），则收益无法归因到标量扫描的消失，不在本机制口径内"
    ],
    "required_conditions": [
      "host 与设备端的切分语义可逐字节复刻：本 run 的 u32 seg-split/overlap（segBytes=CeilDiv(totalBytes,32)、ovStart=max、ovEnd=min、src 前移 ovStart-cStart）在 host 侧完全重放，因此子表与设备侧自行筛选的结果等价",
      "chunk 表是共享的且每核都要读全量：champion 在 32 核下每核对全部 numChunks（最多 ~24）逐 chunk 做 5 次 UB GetValue（srcAddr lo/hi、dstOff、byteLen、isZero）+ min/max overlap 运算 + 分支，与该 chunk 是否落在本核段无关",
      "标量管是主瓶颈：champion 流水 aiv_scalar_ratio 0.8207（round_002 baseline 230 launches），mte2 0.1930、mte3 0.0391、vec 0.0001；230 次 launch 里 210 次落在 8.1-10us（含 13KB 级小 shape），≥10us 的 launch 仅占设备总时长 16%，指标由 ~8.9us 的每次 launch 固定地板主导",
      "数据搬运路径与 chunk 语义可保持完全不变（DataCopyPad 64KB tile、同步点、zero-chunk 处理），收益因此可纯粹归因到被删除的标量扫描"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "cudnnrnnflattenweight",
      "operator_class": "layout-transform",
      "precision": "20/20 PASS bit-exact（mismatch=0，threshold=0，含 NaN/Inf/±0 与 alias 用例）",
      "run_id": "<run-id>",
      "speedup": 1.3406,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "aiv-scalar",
      "per-core-full-plan-scan",
      "per-chunk-getvalue-scalar-decode",
      "overlap-min-max-math",
      "launch-fixed-floor"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "host-per-core-plan-prepartition",
    "reduce_mode": "",
    "structure": [
      "host-replicated-seg-split-semantics",
      "per-core-private-subtable",
      "plan-header-with-core-offset-and-count",
      "bit-exact-byte-movement",
      "device-side-branch-elimination"
    ]
  },
  "generality": "op_class",
  "id": "HOST-PER-CORE-PLAN-PREPARTITION",
  "implementation_steps": [
    "在 tiling 侧定义共享计划布局：FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 每 chunk 6-u32 的 FlattenPlanEntry（srcLo/srcHi/dstOff/byteLen/isZero/pad）",
    "host（pybind 层）保持原 chunk 列表构建语义不变，新增一次每核计划展开：按与设备端逐字节相同的 u32 seg-split/overlap 语义（segBytes=CeilDiv(totalBytes,32)、ovStart=max、ovEnd=min、src 前移 ovStart-cStart）把共享 chunk 切成每核私有子表，plan 张量按 264+24*E 字节精确上传，并断言 numChunks<=128",
    "kernel Init 改为：3 次标量 GM 头读 + 一次 MTE2 DataCopyPad 搬本核 24*cnt 字节子表进 TBuf(3072B)（事件 7 MTE2_S）",
    "kernel Process 改为只解码执行本核 cnt 条 entry 的 CopyRange/ZeroRange（cnt*5 次 GetValue），删除 32 核全表扫描、逐 chunk min/max overlap 运算、非命中分支与 useBulkIdxPath 双路径；CopyRange/ZeroRange 的 DataCopyPad 64KB tile、同步点与 zero-chunk 处理逐字节不变",
    "以 20/20 bit-exact（含 NaN/Inf/±0 与 alias 用例）+ 配对 ABBA 验收，并核对 aiv_scalar_ratio 是否如实下降（本 run 0.7805→0.6892），而不是只看聚合 duration"
  ],
  "intent": "把每核都要重复执行的『全量 chunk 表扫描 + 解码 + overlap 数学』整体移出 kernel：champion 在 32 核下每核对全部 numChunks（最多 ~24）逐 chunk 做 5 次 GetValue 与 min/max 运算，与该 chunk 是否属于本核无关，这部分固定标量串是 ~8.9us 每次 launch 地板的主要成分。",
  "mechanism": "host-prepartitioned-per-core-chunk-plans：共享计划布局 = FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 每 chunk 6-u32 的 FlattenPlanEntry（srcLo/srcHi/dstOff/byteLen/isZero/pad）。host（pybind 层）在构建 tiling 时保持原 chunk 列表语义不变，但按与设备端逐字节相同的 u32 seg-split/overlap 语义（segBytes=CeilDiv(totalBytes,32)、ovStart=max、ovEnd=min、src 前移 ovStart-cStart）预先把 chunks 切成每核私有的子表，plan 张量按 264+24*E 字节精确上传，host 断言 numChunks<=128。设备侧 Init 只做 3 次标量 GM 头读 + 一次 MTE2 DataCopyPad 把本核 24*cnt 字节子表搬进 TBuf(3072B)（事件 7 MTE2_S）；Process 只对本核 cnt 条 entry 做 cnt*5 次 GetValue 解码并执行 CopyRange/ZeroRange——32 核全表扫描、min/max overlap 运算、非命中分支与 useBulkIdxPath 双路径全部删除。CopyRange/ZeroRange 的 DataCopyPad 64KB tile、同步点与 zero-chunk 处理逐字节不变，因此输出 bit-exact。",
  "name": "每核计划预分区：host 复刻 seg-split 语义下发私有 chunk 子表",
  "operator_class": "layout-transform",
  "operator_scope": "每核的搬运计划可由 host 静态算出的分段拷贝类算子：chunk 列表 + seg-split/overlap 规则确定、核数确定，而 champion 让每核各读一遍全量计划表并自行筛选/解码；典型如权重/索引展平拷贝（cudnnrnnflattenweight，本轮覆盖 20 个 case、每次运行 230 次 launch）、跨核分段搬运的布局转换算子",
  "principle": "当 kernel 的每核固定标量工作与核实际分到的工作量无关时，多核并行反而放大了这笔成本：本 run champion 在 32 核下每核都对全量 chunk 表做 numChunks×(5 GetValue + min/max overlap + 分支)，aiv_scalar_ratio 0.8207 而 vec 只有 0.0001，230 次 launch 里 210 次贴住 ~8.9us 地板（≥10us 的 launch 只占设备总时长 16%）。这类工作的特点是它完全由 host 已经知道的静态信息决定——切分规则（u32 seg-split/overlap）确定、chunk 表确定、核数确定——因此正确的做法不是加速它的执行，而是让 host 直接算出每核的私有计划，设备侧只读自己那一小段。这与 host-gated-cheap-path（静态条件门控以跳过恒等计算）和 flat-element-full-tile-tiling（生成扁平 tile 表）语义都不同：本机制的关键是把设备端的 seg-split 语义在 host 侧逐字节复刻、把共享表预切成每核子表，从而同时删掉解码、overlap 数学与非命中分支三件事。这一方向也解释了为什么『换更有吞吐的读法』行不通：本 loop 的 round_01 已用 index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget 把逐字节标量读换成 MTE2 批量搬入 TBuf（28.8665→9.6155us keep），但所有核仍读全表自筛，问题是『每核都读全量』这个乘数；round_02 删掉 2/3 同步数（batched-sync-amortization）也没有缩短 kernel（0.9689x 回滚，20 个 case 一致 +0.3us），aiv_scalar_ratio 反而由 0.8207 升到 0.8438。",
  "related_anti_patterns": [
    "index-scalar-bulk-mte2-ub-resident-lesson"
  ],
  "risks": [
    "host 与设备的 seg-split 语义不等价会以 bit-exact 失败或错位拷贝显形，但只在部分 shape 上出现：本 run round_01 的计划子表 GM 偏移漏乘 FLATTEN_PLAN_ENTRY_U32 即直接 20/20 失败，round_02 一行修复后通过——必须以 20/20 bit-exact（mismatch=0、含 NaN/Inf/±0）加 alias 用例作为验收门",
    "计划表的偏移/宽度单位（u32 与 entry 宽度）是最易犯且最难自查的一类错误：host 与 kernel 必须共用同一组常量，且断言每核 coreCnt<=128 这类边界要显式写出",
    "收益依赖标量管为主瓶颈：换到 MTE2 带宽主导的 case 收益显著缩小（本 run case20 24MB 的 1.12x 为全 20 case 最小，aiv_mte2_ratio 反而从 0.2165 升到 0.2552）",
    "计划表体积变大（264+24*E 字节）会改变 host 侧上传量与分配行为，需要确认仍在可接受范围；本 run 按精确字节数上传",
    "被推迟的同族方向（按 totalBytes 自适应 blockDim）与本机制在收益上有重叠：本 run 的记录显示两条轨迹先后落地（d001 1.3406x → d002 1.0215x → d003 1.4373x），但机制段互斥（计划预切分 vs grid sizing），实践上必须分开验收、分开归因"
  ],
  "slug": "host-per-core-plan-prepartition",
  "summary": "cudnnrnnflattenweight 的 champion 在 32 核下让每核对全量 chunk 表做 numChunks×(5 GetValue + min/max overlap + 分支) 的固定标量串（aiv_scalar_ratio 0.8207、vec 0.0001，230 次 launch 里 210 次贴 ~8.9us 地板）。host 侧按与设备端逐字节相同的 u32 seg-split/overlap 语义把共享计划预切成每核私有子表（FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 6-u32 FlattenPlanEntry），设备 Init 只 3 次标量头读 + 一次 MTE2 搬本核子表进 TBuf(3072B)，Process 只解码本核 cnt 条 entry 执行 CopyRange/ZeroRange。数据搬运路径、tile 大小、同步点逐字节不变（20/20 bit-exact）。实测地板 8.6→6.3us、聚合 9.6155→7.1726us = 1.3406x，aiv_scalar_ratio 0.78→0.69。",
  "verification": {
    "correctness": [
      "20/20 bit-exact（mismatch=0，threshold=0，逐字节比对含 NaN/Inf/±0）+ alias 用例全部通过（round_02，修复 round_01 偏移 bug 后；round_01 首版因 Init 计划子表 GM 偏移漏乘 FLATTEN_PLAN_ENTRY_U32 而 20/20 失败）",
      "pair_dirs/base 与 pair_dirs/cand 重建后各自复验 20/20 bit-exact；两侧 kernel/cudnnrnnflattenweight_kernel.h、cudnnrnnflattenweight.cpp、tests/、ModelNew.py 逐字节一致，差异仅在 host 侧 kernel/pybind11.cpp 与 cudnnrnnflattenweight_tiling.h",
      "host 每核段展开与设备端 seg-split/overlap 语义逐字节等价，host 断言每核 coreCnt<=128；CopyRange/ZeroRange 的 slot 布局、访问顺序与 zero-chunk 处理均未变"
    ],
    "performance": [
      "形式化 ABBA 2 对（pb1 9.6139 / pa1 7.1875 / pa2 7.1578 / pb2 9.6172，n=230 launches/run），pair ratio 1.3376/1.3436，同侧偏差 base 0.035% / cand 0.414%（阈值 10%，无剔除），两级聚合 9.6155→7.1726us = 1.3406x，与逐对 ratio 交叉一致、方向交替无漂移",
      "全部 20 个 case 改善；小 case 地板 8.5-9.0→6.3-6.5us（-2.2~2.3us，落在预测的 1.5-3us 内），case20（MTE2 带宽主导）1.12x 为最小，geomean(逐 case ratio)=1.3608",
      "aiv_scalar_ratio 0.7805→0.6892、aiv_mte2_ratio 0.2165→0.2552，与『删除 32 核全量 chunk 表标量扫描』的机制预测一致"
    ],
    "rollback_signals": [
      "任何 case 的 bit-exact 比对出现 mismatch（host/设备 seg-split 不再等价，或子表偏移单位错）",
      "aiv_scalar_ratio 未下降：说明删掉的不是 pacing 工作，收益无法归因",
      "计划表上传字节数或 entry 宽度不匹配引发错位拷贝，只在部分 shape 上显形",
      "配对 ABBA（>=2 对）显示 speedup<=1.0 或逐 case 地板未下降，则回滚到 BEST_SNAPSHOT"
    ]
  }
}
-->

# 性能优化策略：每核计划预分区：host 复刻 seg-split 语义下发私有 chunk 子表

cudnnrnnflattenweight 的 champion 在 32 核下让每核对全量 chunk 表做 numChunks×(5 GetValue + min/max overlap + 分支) 的固定标量串（aiv_scalar_ratio 0.8207、vec 0.0001，230 次 launch 里 210 次贴 ~8.9us 地板）。host 侧按与设备端逐字节相同的 u32 seg-split/overlap 语义把共享计划预切成每核私有子表（FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 6-u32 FlattenPlanEntry），设备 Init 只 3 次标量头读 + 一次 MTE2 搬本核子表进 TBuf(3072B)，Process 只解码本核 cnt 条 entry 执行 CopyRange/ZeroRange。数据搬运路径、tile 大小、同步点逐字节不变（20/20 bit-exact）。实测地板 8.6→6.3us、聚合 9.6155→7.1726us = 1.3406x，aiv_scalar_ratio 0.78→0.69。

## 1. 原理

当 kernel 的每核固定标量工作与核实际分到的工作量无关时，多核并行反而放大了这笔成本：本 run champion 在 32 核下每核都对全量 chunk 表做 numChunks×(5 GetValue + min/max overlap + 分支)，aiv_scalar_ratio 0.8207 而 vec 只有 0.0001，230 次 launch 里 210 次贴住 ~8.9us 地板（≥10us 的 launch 只占设备总时长 16%）。这类工作的特点是它完全由 host 已经知道的静态信息决定——切分规则（u32 seg-split/overlap）确定、chunk 表确定、核数确定——因此正确的做法不是加速它的执行，而是让 host 直接算出每核的私有计划，设备侧只读自己那一小段。这与 host-gated-cheap-path（静态条件门控以跳过恒等计算）和 flat-element-full-tile-tiling（生成扁平 tile 表）语义都不同：本机制的关键是把设备端的 seg-split 语义在 host 侧逐字节复刻、把共享表预切成每核子表，从而同时删掉解码、overlap 数学与非命中分支三件事。这一方向也解释了为什么『换更有吞吐的读法』行不通：本 loop 的 round_01 已用 index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget 把逐字节标量读换成 MTE2 批量搬入 TBuf（28.8665→9.6155us keep），但所有核仍读全表自筛，问题是『每核都读全量』这个乘数；round_02 删掉 2/3 同步数（batched-sync-amortization）也没有缩短 kernel（0.9689x 回滚，20 个 case 一致 +0.3us），aiv_scalar_ratio 反而由 0.8207 升到 0.8438。

实现机制：host-prepartitioned-per-core-chunk-plans：共享计划布局 = FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 每 chunk 6-u32 的 FlattenPlanEntry（srcLo/srcHi/dstOff/byteLen/isZero/pad）。host（pybind 层）在构建 tiling 时保持原 chunk 列表语义不变，但按与设备端逐字节相同的 u32 seg-split/overlap 语义（segBytes=CeilDiv(totalBytes,32)、ovStart=max、ovEnd=min、src 前移 ovStart-cStart）预先把 chunks 切成每核私有的子表，plan 张量按 264+24*E 字节精确上传，host 断言 numChunks<=128。设备侧 Init 只做 3 次标量 GM 头读 + 一次 MTE2 DataCopyPad 把本核 24*cnt 字节子表搬进 TBuf(3072B)（事件 7 MTE2_S）；Process 只对本核 cnt 条 entry 做 cnt*5 次 GetValue 解码并执行 CopyRange/ZeroRange——32 核全表扫描、min/max overlap 运算、非命中分支与 useBulkIdxPath 双路径全部删除。CopyRange/ZeroRange 的 DataCopyPad 64KB tile、同步点与 zero-chunk 处理逐字节不变，因此输出 bit-exact。

## 2. 性能问题模式

- 优化目标：把每核都要重复执行的『全量 chunk 表扫描 + 解码 + overlap 数学』整体移出 kernel：champion 在 32 核下每核对全部 numChunks（最多 ~24）逐 chunk 做 5 次 GetValue 与 min/max 运算，与该 chunk 是否属于本核无关，这部分固定标量串是 ~8.9us 每次 launch 地板的主要成分。
- 适用数据流：每核的搬运计划可由 host 静态算出的分段拷贝类算子：chunk 列表 + seg-split/overlap 规则确定、核数确定，而 champion 让每核各读一遍全量计划表并自行筛选/解码；典型如权重/索引展平拷贝（cudnnrnnflattenweight，本轮覆盖 20 个 case、每次运行 230 次 launch）、跨核分段搬运的布局转换算子
- Feature signature：`{"bottleneck": ["aiv-scalar", "per-core-full-plan-scan", "per-chunk-getvalue-scalar-decode", "overlap-min-max-math", "launch-fixed-floor"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "host-per-core-plan-prepartition", "reduce_mode": "", "structure": ["host-replicated-seg-split-semantics", "per-core-private-subtable", "plan-header-with-core-offset-and-count", "bit-exact-byte-movement", "device-side-branch-elimination"]}`

## 3. 正确性红线

- host 与设备的 seg-split 语义不等价会以 bit-exact 失败或错位拷贝显形，但只在部分 shape 上出现：本 run round_01 的计划子表 GM 偏移漏乘 FLATTEN_PLAN_ENTRY_U32 即直接 20/20 失败，round_02 一行修复后通过——必须以 20/20 bit-exact（mismatch=0、含 NaN/Inf/±0）加 alias 用例作为验收门
- 计划表的偏移/宽度单位（u32 与 entry 宽度）是最易犯且最难自查的一类错误：host 与 kernel 必须共用同一组常量，且断言每核 coreCnt<=128 这类边界要显式写出
- 收益依赖标量管为主瓶颈：换到 MTE2 带宽主导的 case 收益显著缩小（本 run case20 24MB 的 1.12x 为全 20 case 最小，aiv_mte2_ratio 反而从 0.2165 升到 0.2552）
- 计划表体积变大（264+24*E 字节）会改变 host 侧上传量与分配行为，需要确认仍在可接受范围；本 run 按精确字节数上传
- 被推迟的同族方向（按 totalBytes 自适应 blockDim）与本机制在收益上有重叠：本 run 的记录显示两条轨迹先后落地（d001 1.3406x → d002 1.0215x → d003 1.4373x），但机制段互斥（计划预切分 vs grid sizing），实践上必须分开验收、分开归因

资源与硬件约束：

- host 复刻的设备 seg-split 语义必须逐字节等价：本 run 用共享计划布局 FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 每 chunk 6-u32 的 FlattenPlanEntry（srcLo/srcHi/dstOff/byteLen/isZero/pad），plan 张量按 264+24*E 字节精确上传，host 断言 numChunks<=128
- 每核计划子表必须自定位：Init 只做 3 次标量 GM 头读 + 一次 MTE2 DataCopyPad 把本核 24*cnt 字节子表搬进 TBuf(3072B)（事件 7 MTE2_S），Process 只对本核 cnt 条 entry 做 cnt*5 次 GetValue 解码后执行 CopyRange/ZeroRange
- 计划表偏移/宽度的单位必须与 entry 宽度一致：本 run round_01 因 Init 计划子表 GM 偏移漏乘 FLATTEN_PLAN_ENTRY_U32 导致精度 20/20 失败，round_02 一行修复后才通过——这类 off-by-unit 错误只在 20/20 bit-exact 门禁下暴露
- CopyRange/ZeroRange 的数据搬运路径必须逐字节不变（DataCopyPad 64KB tile、同步点、zero-chunk 处理），收益归因只能落在被删除的标量扫描、解码、overlap 数学与非命中分支上
- 删除 useBulkIdxPath 双路径后必须确认没有其它入口仍按旧的全表布局读计划；chunk 列表构建语义本身不变，被替换的只是它的下发形式

## 4. 泛化条件

- 策略作用域：op_class：layout-transform

适用：

- host 与设备端的切分语义可逐字节复刻：本 run 的 u32 seg-split/overlap（segBytes=CeilDiv(totalBytes,32)、ovStart=max、ovEnd=min、src 前移 ovStart-cStart）在 host 侧完全重放，因此子表与设备侧自行筛选的结果等价
- chunk 表是共享的且每核都要读全量：champion 在 32 核下每核对全部 numChunks（最多 ~24）逐 chunk 做 5 次 UB GetValue（srcAddr lo/hi、dstOff、byteLen、isZero）+ min/max overlap 运算 + 分支，与该 chunk 是否落在本核段无关
- 标量管是主瓶颈：champion 流水 aiv_scalar_ratio 0.8207（round_002 baseline 230 launches），mte2 0.1930、mte3 0.0391、vec 0.0001；230 次 launch 里 210 次落在 8.1-10us（含 13KB 级小 shape），≥10us 的 launch 仅占设备总时长 16%，指标由 ~8.9us 的每次 launch 固定地板主导
- 数据搬运路径与 chunk 语义可保持完全不变（DataCopyPad 64KB tile、同步点、zero-chunk 处理），收益因此可纯粹归因到被删除的标量扫描

不适用：

- chunk 归属不能由 host 静态决定（依赖运行时数据或需要动态负载均衡）时不适用：本机制的前提是切分规则、chunk 表与核数在 host 侧全部已知
- numChunks 很小或核数很少、per-core 全表扫描本身不构成可测成本时没有可消除对象
- 若节省来自『恒等条件下跳过计算』而非『把扫描搬到 host 并预切成每核子表』，属 host-gated-cheap-path（静态条件门控）的域；若节省来自扁平化 tile 表生成，属 flat-element-full-tile-tiling 的域——本机制特指 per-core 私有 chunk 子表的预切分
- 若数据搬运路径本身要被改动（tile 大小/同步策略），则收益无法归因到标量扫描的消失，不在本机制口径内

## 5. 实施步骤

1. 在 tiling 侧定义共享计划布局：FLATTEN_PLAN_HDR_U32=66 头 {totalBytes, blockDim, coreOff[32], coreCnt[32]} + 每 chunk 6-u32 的 FlattenPlanEntry（srcLo/srcHi/dstOff/byteLen/isZero/pad）
2. host（pybind 层）保持原 chunk 列表构建语义不变，新增一次每核计划展开：按与设备端逐字节相同的 u32 seg-split/overlap 语义（segBytes=CeilDiv(totalBytes,32)、ovStart=max、ovEnd=min、src 前移 ovStart-cStart）把共享 chunk 切成每核私有子表，plan 张量按 264+24*E 字节精确上传，并断言 numChunks<=128
3. kernel Init 改为：3 次标量 GM 头读 + 一次 MTE2 DataCopyPad 搬本核 24*cnt 字节子表进 TBuf(3072B)（事件 7 MTE2_S）
4. kernel Process 改为只解码执行本核 cnt 条 entry 的 CopyRange/ZeroRange（cnt*5 次 GetValue），删除 32 核全表扫描、逐 chunk min/max overlap 运算、非命中分支与 useBulkIdxPath 双路径；CopyRange/ZeroRange 的 DataCopyPad 64KB tile、同步点与 zero-chunk 处理逐字节不变
5. 以 20/20 bit-exact（含 NaN/Inf/±0 与 alias 用例）+ 配对 ABBA 验收，并核对 aiv_scalar_ratio 是否如实下降（本 run 0.7805→0.6892），而不是只看聚合 duration

## 6. LLM 前置问题

- 目标实现是否满足：host 与设备端的切分语义可逐字节复刻：本 run 的 u32 seg-split/overlap（segBytes=CeilDiv(totalBytes,32)、ovStart=max、ovEnd=min、src 前移 ovStart-cStart）在 host 侧完全重放，因此子表与设备侧自行筛选的结果等价？
- 目标实现是否满足：chunk 表是共享的且每核都要读全量：champion 在 32 核下每核对全部 numChunks（最多 ~24）逐 chunk 做 5 次 UB GetValue（srcAddr lo/hi、dstOff、byteLen、isZero）+ min/max overlap 运算 + 分支，与该 chunk 是否落在本核段无关？
- 目标实现是否满足：标量管是主瓶颈：champion 流水 aiv_scalar_ratio 0.8207（round_002 baseline 230 launches），mte2 0.1930、mte3 0.0391、vec 0.0001；230 次 launch 里 210 次落在 8.1-10us（含 13KB 级小 shape），≥10us 的 launch 仅占设备总时长 16%，指标由 ~8.9us 的每次 launch 固定地板主导？
- 目标实现是否满足：数据搬运路径与 chunk 语义可保持完全不变（DataCopyPad 64KB tile、同步点、zero-chunk 处理），收益因此可纯粹归因到被删除的标量扫描？
- 是否命中排除条件：chunk 归属不能由 host 静态决定（依赖运行时数据或需要动态负载均衡）时不适用：本机制的前提是切分规则、chunk 表与核数在 host 侧全部已知？
- 是否命中排除条件：numChunks 很小或核数很少、per-core 全表扫描本身不构成可测成本时没有可消除对象？
- 是否命中排除条件：若节省来自『恒等条件下跳过计算』而非『把扫描搬到 host 并预切成每核子表』，属 host-gated-cheap-path（静态条件门控）的域；若节省来自扁平化 tile 表生成，属 flat-element-full-tile-tiling 的域——本机制特指 per-core 私有 chunk 子表的预切分？
- 是否命中排除条件：若数据搬运路径本身要被改动（tile 大小/同步策略），则收益无法归因到标量扫描的消失，不在本机制口径内？

## 7. 验收标准

正确性：

- 20/20 bit-exact（mismatch=0，threshold=0，逐字节比对含 NaN/Inf/±0）+ alias 用例全部通过（round_02，修复 round_01 偏移 bug 后；round_01 首版因 Init 计划子表 GM 偏移漏乘 FLATTEN_PLAN_ENTRY_U32 而 20/20 失败）
- pair_dirs/base 与 pair_dirs/cand 重建后各自复验 20/20 bit-exact；两侧 kernel/cudnnrnnflattenweight_kernel.h、cudnnrnnflattenweight.cpp、tests/、ModelNew.py 逐字节一致，差异仅在 host 侧 kernel/pybind11.cpp 与 cudnnrnnflattenweight_tiling.h
- host 每核段展开与设备端 seg-split/overlap 语义逐字节等价，host 断言每核 coreCnt<=128；CopyRange/ZeroRange 的 slot 布局、访问顺序与 zero-chunk 处理均未变

性能：

- 形式化 ABBA 2 对（pb1 9.6139 / pa1 7.1875 / pa2 7.1578 / pb2 9.6172，n=230 launches/run），pair ratio 1.3376/1.3436，同侧偏差 base 0.035% / cand 0.414%（阈值 10%，无剔除），两级聚合 9.6155→7.1726us = 1.3406x，与逐对 ratio 交叉一致、方向交替无漂移
- 全部 20 个 case 改善；小 case 地板 8.5-9.0→6.3-6.5us（-2.2~2.3us，落在预测的 1.5-3us 内），case20（MTE2 带宽主导）1.12x 为最小，geomean(逐 case ratio)=1.3608
- aiv_scalar_ratio 0.7805→0.6892、aiv_mte2_ratio 0.2165→0.2552，与『删除 32 核全量 chunk 表标量扫描』的机制预测一致

回滚信号：

- 任何 case 的 bit-exact 比对出现 mismatch（host/设备 seg-split 不再等价，或子表偏移单位错）
- aiv_scalar_ratio 未下降：说明删掉的不是 pacing 工作，收益无法归因
- 计划表上传字节数或 entry 宽度不匹配引发错位拷贝，只在部分 shape 上显形
- 配对 ABBA（>=2 对）显示 speedup<=1.0 或逐 case 地板未下降，则回滚到 BEST_SNAPSHOT

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：index-scalar-bulk-mte2-ub-resident-lesson

- loop_20260916_165309 status=accepted, speedup=1.3406, precision=20/20 PASS bit-exact（mismatch=0，threshold=0，含 NaN/Inf/±0 与 alias 用例））

## 检索卡（短卡）

动作：把每核重复的全量chunk表扫描、解码与overlap数学移出kernel，改由host按seg-split语义预切成每核私有子表
适用：host与设备切分语义可逐字节复刻；chunk表共享且每核都读全量；标量管是主瓶颈；搬运路径可逐字节不变
限制：host/设备seg-split不等价以bit-exact失败或错位拷贝显形；偏移与宽度单位须共用常量
范围：分段拷贝类布局转换算子的每核搬运计划下发环节
检索词：per-core私有子表、FLATTEN_PLAN_HDR_U32、FlattenPlanEntry、seg-split、DataCopyPad
机会：标量管主导：每核重复全量chunk表的GetValue与min/max运算，aiv_scalar_ratio 0.8207
代价：计划表体积增至264+24*E字节改变上传与分配；标量非主导的带宽case收益显著缩小
