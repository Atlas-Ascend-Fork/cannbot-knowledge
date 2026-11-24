---
type: Optimization
title: 非末轴归约：沿连续维条带并行
description: 把非末轴归约前的全量转置/逐元素组装改为各class连续inner条带搬运，SIMD lane对应独立inner位置，沿C累积。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/non-last-axis-contiguous-stripe-reduction.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "NONLAST-AXIS-CONTIGUOUS-STRIPE-REDUCTION",
  "slug": "non-last-axis-contiguous-stripe-reduction",
  "created": "2026-10-14",
  "classification": "validated_strategy",
  "generality": "op_class",
  "operator_class": "reduction-normalization",
  "phase": [
    "design",
    "tuning"
  ],
  "feature_signature": {
    "pattern": "non-last-axis-contiguous-stripe-reduction",
    "bottleneck": [
      "full-tensor-transpose-before-row-reduce",
      "serial-strided-element-gather",
      "underused-contiguous-inner-lanes"
    ],
    "structure": [
      "original-layout-class-major-stripes",
      "SIMD-lane-per-inner-position",
      "C-loop-per-lane-statistics",
      "liveness-based-UB-budget",
      "metadata-guarded-fallback"
    ]
  },
  "related_strategy_ids": [
    "row-resident-single-gm-read-cross-pass-reuse",
    "row-batch-normalize",
    "mte-row-pad-strided-staging",
    "scan-inner-lane-axis-core-distribution",
    "register-resident-accumulator-arg-reduce",
    "simd-simt-gather-to-vector-math",
    "host-gated-cheap-path",
    "vector-api-unaligned-overread"
  ],
  "name": "非末轴归约：沿连续维条带并行",
  "mechanism": "For x[outer,C,inner], map SIMD lanes to contiguous inner positions, load each class stripe by MTE2 and accumulate independently along the strided C axis; avoid full-tensor transpose when the original contract and resource guards permit.",
  "operator_scope": "非末轴归约 / 归一（连续 ND，如 softmax(dim=1)+cross_entropy 复合损失）；普通 max/sum 与其它 normalize 为可迁移候选",
  "intent": "单一优化点：把为复用末轴行 kernel 而做的全量转置或逐元素跨步组装，改为原布局中的连续 inner 条带搬运；SIMD lane 对应独立 inner 位置、沿归约轴 C 累计每个 lane 的状态。",
  "implementation_steps": [
    "以连续 x[outer,C,inner] 为例，取宽度 B 的 inner tile，元素地址 (outer_id*C+c)*inner+r0+lane；每个 SIMD lane 代表不同 r 位置",
    "原 GM 指针→逐 class 连续 R 条带 MTE2→对齐 UB 类主序 tile / 流式槽；沿 c 循环向量 Max/Add 更新各 lane 自身 max/sum（C 不是 SIMD lane 轴）",
    "多遍参考变体将一个 C×B tile 驻留：max_c→exp(x−m1)/sum_c→除法得 z→后继统计；保留第二次 log-softmax 的 max/exp/sum/log 及 target 概率",
    "以实际 InitBuffer / 队列槽 / 消费者活跃范围建预算，逐对象取整后向下选合法 B；最小合法 tile 超预算即回退",
    "有 target 时在 z 被原位覆盖前保存 z[target[r]][r]，p* 由已归一 z 初始化；每核 partial 完整发布后 finalize 同流按 launch 顺序读取"
  ],
  "risks": [
    "布局必须由 shape/stride 证明，仅连续 ND 输入与 target 可套连续条带公式；非连续/广播/别名/不同 stride 须另证寻址否则回退",
    "尾条带只读写合法 GM 元素；完整寄存器 load 可能触及 mask 以外物理字节，需真实 guard 并验证头/body/tail",
    "多遍 softmax 必须保留第二次 log-softmax 与 target 概率，不能偷换成普通 cross_entropy；不同遍 exp 输入不同，不能跨遍错误复用",
    "高 C 挤压 B、小 inner 不足以填 lane/活动核、原路径已有高效局部转置、额外多遍重读或 target 标量开销主导时可能无收益",
    "已验证阈值为该实现资源/回退配置，不是通用推荐阈值；C≤64 的 VF 目标提取须重新核验索引编码/计数/repeat/guard"
  ],
  "verification": {
    "correctness": [
      "覆盖 NaN/Inf、长链、尾、空域、分派边界；原容差验证，容差通过不等于逐位精确；空核按契约初始化有效 partial",
      "FP16/BF16 升 FP32、FP32 保留原链、最终一次降回并保持规定舍入；逐步低精度舍入契约不能照搬",
      "有 target 时先存 z[target[r]][r]；跨 R Compare/Select 提取需索引域、读取范围/UB guard、条带 stride 与尾 mask 全部证明"
    ],
    "performance": [
      "已验证参考为 Ascend950/DAV_3510 FP16/BF16/FP32 连续 ND 复合归一化/标量损失链；直接条带分派含连续输入+target、C≤1024（实现资源/回退配置，非通用阈值）",
      "同条件比较原路径、直接条带与必要 fallback 的完整调用至完成同步、真实主/辅助 device 工作、逐输入组及波动",
      "布局/并行轴替换连同计算链变化属组合干预，无消融不拆收益；单槽/冗余 buffer、smallC target VF、负载平衡各自须独立对照或明确组合归因"
    ],
    "rollback_signals": [
      "未知/非连续布局、不安全 offset、UB 不足、inner 并行过少或稳定全调用回退且无安全收缩域即回退",
      "转置或重复搬入因修复重新出现时重测受影响布局域；边界两侧都测，不按用例编号特化",
      "更换 SDK/布局/dtype/并行轴后重验，同步与资源结论限于已证明范围"
    ]
  },
  "principle": "把“非末轴归约前的全量转置/逐元素组装”改为“原布局中各 class 连续 inner 条带搬运 + SIMD lane 对应独立 inner 位置、沿 C 累积”；既不要求全量转置，也不要求整 tensor 驻留 UB。",
  "validation_scope": "Ascend950/DAV_3510 reference variant: contiguous ND FP16/BF16/FP32 softmax followed by cross_entropy of its probabilities, including tail and special-value checks. Continuous-input-and-target C<=1024 dispatch and C<=64 vector target selection are implementation-specific guards. Ordinary max/sum and other normalizations are transfer candidates requiring independent validation.",
  "applicability": {
    "required_conditions": [
      "Original strides prove contiguous inner stripes and independent outputs along inner",
      "Aligned tile, live buffers, queues, index widths and asynchronous lifetimes fit the actual hardware/API budget",
      "Original reduction, numerical chain and special-value contract are preserved"
    ],
    "excluded_conditions": [
      "Unknown/noncontiguous layout, unsafe offsets or insufficient UB allocation",
      "Too little inner parallelism, excessive class working set or stable full-call regression without a safe restricted domain"
    ],
    "constraints": [
      "Tile-only residency is sufficient; whole-tensor UB residency is neither required nor permitted beyond the budget",
      "Reduction order and NaN/Inf behavior require original-tolerance validation; no blanket bit-exact guarantee"
    ]
  },
  "attribution": "The layout/axis replacement was measured as a combined implementation change. Queue/buffer budget, target selection and load balance are associated refinements, not independently additive gains of this mechanism."
}
-->
# 性能优化策略：非末轴归约：沿连续维条带并行

> 单一优化点：把为复用末轴行kernel而做的全量转置或逐元素跨步组装，改为原布局中的连续inner条带搬运；SIMD lane对应独立inner位置，沿归约轴C累计每个lane的状态。选择并行轴与数据流，既不要求全量转置，也不要求整个tensor驻留UB。

## 1. 原理与数据流

以连续布局 `x[outer,C,inner]`（示意亦可写作 `[N,C,R]`）为例，沿C归约的同一输出在GM中间隔inner元素，而固定outer/c的inner条带连续。取宽度B的inner tile，元素地址为 `(outer_id*C+c)*inner+r0+lane`；每个SIMD lane代表不同r位置，沿c循环以向量Max/Add等更新各lane自己的max/sum。C不是这里的SIMD lane轴，归约不是对同一向量内的不同r做横向归约。后续若要全局loss，再对有效r归并，须另遵守其求和契约。

数据流是原GM指针→逐class的连续R条带MTE2→对齐UB类主序tile或流式槽→跨R SIMD计算→原布局输出/每核partial→必要finalize。无需先写出全量 `[outer*inner,C]` 再重读。单遍max/sum可在少量class槽上流式累积；多遍softmax等须在“驻留一个C×B tile并复用”“按class分块”“重读GM/重算”之间选择，不能假定所有中间值可丢弃或C总能完整驻留。类分块的全局max/sum合并与归一次序要单独证明、验证。

多遍参考变体将一个C×B tile驻留：max_c x→exp(x−m1)及sum_c→除法得到z→后继所需统计量/数学。原链若明确要求先softmax(x)，再cross_entropy(z,target)，必须保留第二次log-softmax的max/exp/sum/log及target概率，不能偷换成普通cross_entropy(x,target)；这只是已验证的复合归一化变体，不是所有归约的数学定义。不同遍的exp输入不同，不能错误跨遍复用。

## 2. tile、预算和生命周期

以实际InitBuffer、队列槽数和消费者活跃范围建立预算：原dtype class tile `depth_x*C*B_alloc*sizeof(T)`；需要加宽时另有 `C*B_alloc*4`；统计量为 `k*B_alloc*acc_bytes`；有target时计入其队列、原索引宽度与guard；再计reduce临时、标量槽、输出/partial、对齐及编译器/SDK保留区。逐对象取整，预算后向下选合法B；若最小合法tile也超预算就回退，不能先求B再向上padding而遗漏增量。

FP32输入如可直接消费队列槽且寿命覆盖所有遍，可省未消费的加宽buffer；低精度加宽槽不能照删。只在最后一次消费完成后复用/覆盖，不能把两个同时活跃的统计量设为同址。队列depth=2只描述容量，不证明预取或重叠；顺序alloc/copy/enqueue/dequeue/compute/free路径可比较单槽和相应预算，但真正预取时保留在途槽及依赖。预算/队列优化与本机制关联，不将组合收益重复归给免转置。

B应兼顾C、inner、outer、dtype、真实UB/AIV、最坏每核tile循环、向量repeat、target提取成本和尾浪费。最大UB tile不一定最短关键路径；减小B可能增加任务数与活动核，也可能多发描述符。按 `(outer_id, stripe_id)` 独占分区，宽整数计算总任务及偏移；空域先守卫，不能除零。某些二维末轴行或连续行批量归约仍更合适，无需强制整个kernel只有一个并行轴。

## 3. 正确性与依赖红线

- 布局必须由shape/stride证明。仅连续ND输入和target才可套用连续条带公式；非连续、广播/别名或不同stride须有另证寻址，否则保留正确的归一/转置/行路径或MTE局部转换。契约本身不强制 `[outer*inner,C]`。源offset、乘积、任务计数、target索引和输出位置分别核验位宽，乘加前提升，不能凭某个offset宽就认为全部计数安全。
- 尾条带只读写合法GM元素。UB槽基址/行距满足目标API对齐；padding lane对应不存在的独立r，不参与最终loss归约或输出。完整寄存器load可能触及mask以外物理字节，需分配真实guard并验证头/body/tail，不把逻辑mask当越界保护。
- MTE2写→V/Scalar读、V写→MTE3读及槽复用WAR按目标SDK的队列/事件保证；V中原位运算也保持必要顺序。每核partial完整发布后，finalize同流按launch顺序读取；其它跨核合并方案另证可见性与同步。空核仍按契约初始化有效partial，不能让empty workspace进入最终归约；空归约返回值按原接口。异步返回时tensor/workspace寿命覆盖全部在途任务，完成语义由约定同步界定，不能盲加全核barrier。
- 数学、统计量归约次序、累加dtype和最终转换按原契约。参考浮点变体FP16/BF16升FP32，FP32保留原链，最终一次降回原dtype并保持规定舍入；其它接口若要求逐步低精度舍入不能照搬。NaN/Inf/零/次正规及长链累加需原容差验证，容差通过不等于逐位精确。
- 有target时，在z被原位覆盖为后继exp等数据之前保存 `z[target[r]][r]`；p*必须由已经归一的z初始化。宽C可保留合法标量target捕获，本机制不意味着全部步骤向量化。跨R Compare/Select提取是可选子变体：需索引域合法、读取范围与UB guard、条带stride和尾mask全部证明。

## 4. 已验证参考范围与迁移边界

已验证参考是Ascend950/DAV_3510的FP16/BF16/FP32连续ND复合归一化/标量损失链，按原容差验证尾块、特殊值和正确fallback。其直接条带分派条件包含连续输入与target、C≤1024；这是该实现资源与回退配置，**不是通用推荐阈值，也不证明阈值内每个shape均已穷举**。其它C、inner、outer、布局及工具链需预算证明和实测。

其小C目标提取仅在C≤64启用跨64个r的VF，条带槽按64个FP32元素补齐；int64索引拆成两个int32字并DeInterleave低32位，前提是非负合法类别值 `<C`，已验证的字序/表示和完整寄存器载入空间成立。它不是把任意int64索引窄化为int32；高C继续标量提取。迁移需重新核验索引编码、计数/repeat字段与guard，不能把64或1024当硬件通用门限。

普通max/sum、其它normalize和不同非末轴算子是可迁移候选，数学顺序、特殊值、输出布局和性能必须独立验证。高C挤压B、小inner不足以填lane/活动核、原路径已有高效局部转置、额外多遍重读或target标量开销主导时可能无收益。可按shape/dtype/layout/资源收缩快速域，回到正确转置/行路径/MTE局部转换；边界两侧都测，不按用例编号特化。

## 5. 实施与验收

1. 先确认原数学链、归约轴与真实stride，定位全量转置或标量组装的实际设备工作；分别计算可省的中间GM写读、额外class描述符/UB占用和多遍重读代价。逻辑字节估算不是硬件流量实测。
2. 以合法B建tile及活跃期预算，证明独占任务、尾条带、offset/index宽度、队列与partial/finalize依赖；保持fallback。保留原容差并覆盖NaN/Inf、长链、尾、空域及分派边界。
3. 同条件比较原路径、直接条带和必要fallback的完整调用至完成同步、真实主/辅助device工作、逐输入组及波动。转置或重复搬入因修复重新出现时，重新测受影响布局域；这属于策略验收，不规定额外运行时工作流。
4. 布局/并行轴替换连同计算链变化属于组合干预；无消融不拆收益。单槽/冗余buffer、smallC target VF和负载平衡是相关优化，各自须有独立对照或明确组合归因，不把最终累计效果全归于本卡。

## 6. 与相邻机制的区别

- [末轴整行常驻/跨pass复用](row_resident_single_gm_read_cross_pass_reuse.md)以类别连续的行驻留为前提；此处SIMD沿原连续inner维，类别仍跨stride。
- [独立行批归一](row_batch_normalize.md)及连续行布局上的批量归约在已有连续行布局中摊销行归约，不自动消除非末轴全量转置。
- [行padding搬运](mte_row_pad_strided_staging.md)改善UB行基对齐；strided DataCopy只是搬运描述，不等于重选计算轴，也不能用单个burst表示任意元素转置。
- [扫描lane分核](scan_inner_lane_axis_core_distribution.md)扩展已经存在的独立lane任务；[arg-reduce寄存器驻留](register_resident_accumulator_arg_reduce.md)削已有strided计算的UB往返，可组合但不是这里的布局/并行轴重构。
- [SIMT取数接SIMD数学](simd_simt_gather_to_vector_math.md)解决不规则索引取数交接，此处依赖规则连续条带，不要求SIMT。预算调整可关联[host守卫与实际队列预算](host_gated_cheap_path.md)，完整载入安全关联[向量读取guard](vector_api_unaligned_overread.md)。

## 检索卡（短卡）

动作：把非末轴归约前的全量转置/逐元素组装改为各class连续inner条带搬运，SIMD lane对应独立inner位置，沿C累积。
适用：原stride可证明连续inner且输出独立；合法tile、索引宽度与活跃缓冲满足真实UB预算。
限制：尾mask须配实际guard；保原数学/NaN/Inf，target先于z覆盖保存；不适合布局/资源域回退。
范围：非末轴归约/归一；复合softmax损失已有受限验证，其它用途另验。
检索词：ND、非末轴、strided reduction、连续R条带、跨R SIMD、免全量转置、MTE2
机会：布局修复把原连续维拆成标量访问，先整张转置再读行kernel。
代价：C×tile驻留/多遍重读、class描述符与target提取成本；高C小R可无收益。
