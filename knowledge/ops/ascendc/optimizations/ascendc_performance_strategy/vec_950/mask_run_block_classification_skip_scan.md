---
type: Optimization
title: 掩码分块分类跳过扫描：打包位图 + 空桶 O(1) 跳过
description: 把逐字节掩码扫描改为按块/按字的一致性分类跳过：掩码 UB 常驻、Compares(uint8,EQ 0) 生成 packed 位图、空桶 O(1) 跳过。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/mask-run-block-classification-skip-scan.md
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
      "向量分类的正确性必须在目标 SoC 上逐位验证：idx26 计划中的向量 Compares 分类（u8 标志）在 dav_3510 上因 VcmpvsImpl 的 StoreUnAlign 多 repeat 标志错位（flags 漂移到字上）失败并回退为标量 u32 字分类；idx28 路径的 Compares(uint8, EQ 0) -> packed 位图形态通过 20/20，但同一类标志存储语义仍须在落地 SoC 上验证",
      "emit 顺序与 u/m/numInt 语义必须与 champion 逐字节扫描严格一致，精度以 bit-exact 验收；delInfo 契约与 copy kernel 不得改动",
      "分桶（按 index 32KB chunk 两遍计数）只在 chunks >= 4 时启用，否则保持每 chunk 单遍扫描——idx28 v1 的阈值 chunks >= 1 在单 chunk case 上回退，v2 改为阈值 4 + u64 扫描才成立",
      "多核门控放宽后必须保留回退：prepBlockSize > 32768 仍回退串行路径",
      "掩码改为 UB 常驻后不再有 keepGM 往返，需确认下游只消费 delInfo/intervals 契约（本 run delInfo 契约未动）"
    ],
    "excluded_conditions": [
      "copy kernel 不适用：本机制只作用于 delete_prep 的掩码扫描，copy 路径保持零改动",
      "掩码近似随机（混合块/混合字比例极高）时快路径失效：收益退化为原逐字节扫描的常数倍折减，本 run 混合字比例高的 mid case 即被 1+4 迭代混合路径摊薄",
      "chunks < 4 的输入不启用分桶，退化为每 chunk 单遍扫描",
      "目标 SoC 的向量 Compare 标志存储路径不可靠时（StoreUnAlign 多 repeat 错位）向量位图形态不可用，只能走标量 word 分类形式"
    ],
    "required_conditions": [
      "prep 在单核上运行且标量主导：idx28 记录 delete_prep n=100 mean=792.247us 约占 matched device time 的 58%（delete_copy_fp32 28%、fp16 10%、bf16 4%）；DeletePrepKernel::Process 在 GetBlockIdx()!=0 时直接返回，整个 prep 跑在一个核上；idx26 记录 prep case 均值为第二大分量",
      "keep/delete 掩码是逐字节常量，可按块分类为「全保留/全删除/混合」——256B 块（idx28）与 4B word（idx26）两种粒度都可分类",
      "扫描成本与标量迭代量同量级（idx26 记录约 8-15ns/迭代，[1000003]1D 266us、S=4096 full 126us、mid case 20-85us、下限 2.5us），故降低迭代粒度可直接折减时间",
      "存在可 O(1) 跳过的空桶 chunk（大 index 张量下 interval 分布稀疏，本 run 以 32KB chunk 分桶后空桶可整块跳过）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "delete__v2",
      "operator_class": "scan",
      "pairs": 4,
      "precision": "20/20 PASS（首次通过，未消耗精度修复）",
      "run_id": "<run-id>",
      "speedup": 1.4652,
      "status": "accepted"
    },
    {
      "operator": "delete",
      "operator_class": "scan",
      "pairs": 2,
      "precision": "20/20 PASS（bit-exact，向量比较分类失败后改标量 u32 字分类，耗 1 轮修复）",
      "run_id": "<run-id>",
      "speedup": 1.1065,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "prep-scalar-byte-scan",
      "mask-gm-roundtrip",
      "per-chunk-pipe-all",
      "single-core-prep"
    ],
    "pattern": "mask-run-block-classification-skip-scan",
    "structure": [
      "ub-resident-mask",
      "word-level-mask-classification",
      "packed-delete-bitmap",
      "empty-bucket-o1-skip",
      "barrier-reduction"
    ]
  },
  "generality": "op_class",
  "id": "MASK-RUN-BLOCK-CLASSIFICATION-SKIP",
  "implementation_steps": [
    "掩码全程驻留 UB：Duplicate(1) 初始化 + 桶内标量置零，不再写 keepGM/读回，删掉 keep 掩码的 GM 往返（idx28 粒度）",
    "用 Compares(uint8, EQ 0) 向量生成 packed 删除位图（32KB 掩码 -> 4KB 位图），u64 字扫位图：w==0 全保留 / w==~0 全删走快路径，仅混合字按位处理，run 状态跨 chunk 连续（idx28 粒度）",
    "索引按 32KB chunk 两遍计数分桶（仅 chunks>=4 启用，否则每 chunk 单遍扫描），空桶 chunk 以 O(1) 跳过（不发向量段、不设 barrier），每 chunk 的 PIPE_ALL 由 5 次降为 3 次；header+intervals 保持单次融合 DataCopyPad 下发（idx28 粒度）",
    "标量回退形式：keep-mask 按 4B word 分类（0x01010101 全留 / 0x00000000 全删 / 混合），一次 u32 读 + 两比较替代 4 次字节读，标量只走 S/4 个 word，混合字与尾字节逐字节检查；emit 顺序与 u/m/numInt 与 champion 逐字节扫描严格一致，串行 ScanAndBuildIntervals 与并行 ProcessParallel 共用（idx26 粒度）",
    "index 载入改固定 32KB 分块（indexBuf 固定 32KB）去除整表 UB 上限，每 fill-chunk 单趟散播；host 门控由 scanBlocks>=4 && idxBytes<=32KB 放宽为 scanBlocks>=2 && intervalBytes=8*(L+1)<=48KB，prepBlockSize>32768 仍回退串行（idx26 粒度）",
    "以 bit-exact 精度（emit 顺序、u/m/numInt 不变）与 prep 分量时长、copy 路径持平作为验收，copy kernel 与 delInfo 契约零改动"
  ],
  "intent": "消除 delete_prep 的 O(S) 标量逐字节 run 扫描、keep 掩码的 GM 往返、以及每 32KB 掩码 chunk 的多次 PIPE_ALL：把掩码扫描的迭代粒度从逐字节提升到逐块/逐字，并让可跳过的块整块跳过，从而在单核 prep 上折减标量迭代量。",
  "mechanism": "mask-run-block-classification-skip-scan 的两种粒度，均为掩码的层次化一致性分类：(a) idx28（delete__v2）粒度——索引按 32KB chunk 两遍计数分桶；掩码全程驻留 UB（Duplicate(1) + 桶内标量置零）不再走 keepGM 往返；用 Compares(uint8, EQ 0) 生成 packed 删除位图（32KB 掩码 -> 4KB 位图），u64 字扫位图时 w==0 / w==~0 走「全保留/全删除」快路径、只对混合字逐 bit 处理；空桶 chunk 以 O(1) 跳过（不发向量段、不设 barrier），每 chunk 的 PIPE_ALL 由 5 次降为 3 次，header+intervals 保持单次融合下发；(b) idx26（delete）粒度——同一分类思想落到标量形式：keep-mask 按 4B word 分类（0x01010101 全留 / 0x00000000 全删 / 混合），一次 u32 读 + 两比较替代每字 4 次字节读，标量只走 S/4 个 word，混合字与尾字节逐字节检查；index 载入改固定 32KB 分块，host 多核门控放宽为 scanBlocks>=2 且 intervalBytes<=48KB，prepBlockSize>32768 仍回退串行。两种粒度的 emit 顺序与 u/m/numInt 语义都与 champion 逐字节扫描严格一致（bit-exact），copy kernel 与 delInfo 契约均未改动。边界：idx26 路径上计划中的向量 Compares 分类在 dav_3510 上失败（VcmpvsImpl 的 StoreUnAlign 多 repeat 标志错位，flags 漂移到字上，case1 m=775/786），最终落地的是标量 u32 字分类回退形式。",
  "name": "掩码分块分类跳过扫描：打包位图 + 空桶 O(1) 跳过",
  "operator_class": "scan",
  "operator_scope": "单核、标量主导、以逐字节扫描 keep 掩码来生成 run/interval 的 prep 类算子（掩码为逐字节 0/1 常量，可按 256B 块或 4B word 分类为全保留/全删除/混合）",
  "principle": "当 prep 在单核上标量主导、且扫描成本与标量迭代量同量级（本 run 约 8-15ns/迭代）时，时间正比于迭代次数而非数据语义复杂度。掩码只有两种取值，因此任意对齐块只有三种状态：全保留（无需产出 interval）、全删除（整块一个 interval）、混合（才需要逐元素处理）。把逐字节扫描换成按块/按字的分类扫描，均匀块退化为常数次比较，同时把向量产生的分类信息压成 packed 位图进一步把迭代数再降 8 倍（32KB 掩码 -> 4KB 位图，8 bit/字节）；配合分桶后空桶整块 O(1) 跳过与 barrier 次数下降，单核 prep 的标量工作量被直接折减。约束是分类信息的正确性依赖向量 Compare 的标志存储语义（本 run 在 dav_3510 上实证过该路径不可靠，故保留标量 word 分类作为回退）。",
  "related_anti_patterns": [
    "vector-api-unaligned-overread"
  ],
  "risks": [
    "向量 compare 分类的边界是实测出来的：idx26 计划中的向量 Compares 分类在 dav_3510 上失败（VcmpvsImpl 的 StoreUnAlign 多 repeat 标志错位，flags 漂移到字上，case1 结果 m=775/786），最终落地的是标量 u32 字分类回退形式；idx28 路径的 Compares(uint8, EQ 0) -> packed 位图形态 20/20 首次通过，但同类标志存储语义在换 SoC 时必须重新逐位验证",
    "混合字/混合块比例决定收益上限：本 run 模型预估 prep 52->约31us，实测 ABBA 34.86us（模型略乐观），混合字比例高的 mid case 被「1 次均匀字快路径 + 4 次混合字处理」的混合路径摊薄",
    "分桶阈值是负向边界：idx28 v1 用 chunks>=1 在单 chunk case 上回退，v2 改为阈值 4 并叠加 u64 扫描才成立；阈值下调会重新引入回退",
    "bit-exact 是硬契约：emit 顺序与 u/m/numInt 语义必须与 champion 逐字节扫描严格一致，否则精度门拒绝（idx26 消耗 1 轮精度修复、idx28 消耗编译 2 轮 + 性能 1 轮）",
    "单核 prep 本身未被并行化：本机制削减的是单核内的工作量，非门控 case（scanBlocks 不足或 prepBlockSize>32768）仍走串行原样路径，收益不覆盖全部形状"
  ],
  "slug": "mask-run-block-classification-skip-scan",
  "summary": "delete_prep 在单核上标量主导（idx28：n=100 mean=792.247us 约占 matched device time 的 58%，vec≈0；每 32KB 掩码 chunk 3 次 PIPE_ALL、掩码走 keepGM 完整往返，ScanAndBuildIntervals 为 O(S) 逐字节读，case12 S=1000003 约 100 万次标量读）。改为掩码的层次化一致性分类：掩码 UB 常驻（省 GM 往返）、Compares(uint8, EQ 0) 生成 packed 删除位图（32KB->4KB）、u64 字扫位图走 w==0 / w==~0 快路径只对混合字逐 bit 处理、空桶 chunk O(1) 跳过、每 chunk PIPE_ALL 5->3，header+intervals 单次融合下发：kernel_geomean 54.407 -> 37.134us（1.465x），prep 全部 20 case 改善 1.05-23.9x，ABBA x4 全胜、36 组无 >2% 回退，精度 20/20。同一机制的标量粒度（4B word 分类，全留/全删/混合）在 delete 上把 prep 52.140 -> 34.864us（1.496x）、两级聚合 geomean 41.866 -> 37.839us（1.1065x），精度 20/20 bit-exact——该路径的向量 Compares 分类在 dav_3510 上因标志错位失败，落地为标量回退形式。copy kernel 与 delInfo 契约均未改动。",
  "verification": {
    "correctness": [
      "idx28：精度 20/20 PASS，首次通过、未消耗精度修复（修复记录为编译 x2 __ubuf__ 指针类型、性能 x1 分桶阈值）",
      "idx26：精度 20/20 bit-exact，耗 1 轮修复（attempt1 向量分类失败：case1 m=775/786，class 标志与 word 错位；改标量 u32 word 分类后通过）",
      "两路均保持 emit 顺序与 u/m/numInt 语义与 champion 逐字节扫描一致；copy kernel 与 delInfo 契约未动"
    ],
    "performance": [
      "idx28：形式化配对（ABBA x4、双目录交替、同 shape、溯源干净）4/4 对候选更快，36 组 (Op,case) 无 >2% 回退，kernel_geomean 54.407 -> 37.134us（1.465x），prep 全部 20 case 改善 1.05-23.9x",
      "idx26：ABBA 两对平衡配对 geomean 41.866 -> 37.839us（1.1065x），prep 分量 52.140 -> 34.864us（1.496x），copy 三 case 持平且对间偏差 <=0.4% 远小于效应量",
      "机制级证据：idx28 掩码 GM 往返与 per-chunk barrier 被移除（PIPE_ALL 5->3）、空桶 chunk 不再发向量段；idx26 扫描迭代量由 S 降为 S/4（word 级），冻结基线两级聚合 geomean 40.656us、prep case 均值 52.103us（n=100）"
    ],
    "rollback_signals": [
      "目标 SoC 上向量 Compare 的标志/位图存储语义不可靠（StoreUnAlign 多 repeat 错位），打包位图结果与掩码不一致",
      "非门控 case（chunks<4、scanBlocks 不足、prepBlockSize>32768）出现回退或不再走原串行路径",
      "任何 case 的 emit 顺序或 u/m/numInt 与 champion 不再 bit-exact",
      "copy kernel 时长或 delInfo 契约发生变化（收益归因被污染）"
    ]
  }
}
-->

# 性能优化策略：掩码分块分类跳过扫描：打包位图 + 空桶 O(1) 跳过

delete_prep 在单核上标量主导（idx28：n=100 mean=792.247us 约占 matched device time 的 58%，vec≈0；每 32KB 掩码 chunk 3 次 PIPE_ALL、掩码走 keepGM 完整往返，ScanAndBuildIntervals 为 O(S) 逐字节读，case12 S=1000003 约 100 万次标量读）。改为掩码的层次化一致性分类：掩码 UB 常驻（省 GM 往返）、Compares(uint8, EQ 0) 生成 packed 删除位图（32KB->4KB）、u64 字扫位图走 w==0 / w==~0 快路径只对混合字逐 bit 处理、空桶 chunk O(1) 跳过、每 chunk PIPE_ALL 5->3，header+intervals 单次融合下发：kernel_geomean 54.407 -> 37.134us（1.465x），prep 全部 20 case 改善 1.05-23.9x，ABBA x4 全胜、36 组无 >2% 回退，精度 20/20。同一机制的标量粒度（4B word 分类，全留/全删/混合）在 delete 上把 prep 52.140 -> 34.864us（1.496x）、两级聚合 geomean 41.866 -> 37.839us（1.1065x），精度 20/20 bit-exact——该路径的向量 Compares 分类在 dav_3510 上因标志错位失败，落地为标量回退形式。copy kernel 与 delInfo 契约均未改动。

## 1. 原理

当 prep 在单核上标量主导、且扫描成本与标量迭代量同量级（本 run 约 8-15ns/迭代）时，时间正比于迭代次数而非数据语义复杂度。掩码只有两种取值，因此任意对齐块只有三种状态：全保留（无需产出 interval）、全删除（整块一个 interval）、混合（才需要逐元素处理）。把逐字节扫描换成按块/按字的分类扫描，均匀块退化为常数次比较，同时把向量产生的分类信息压成 packed 位图进一步把迭代数再降 8 倍（32KB 掩码 -> 4KB 位图，8 bit/字节）；配合分桶后空桶整块 O(1) 跳过与 barrier 次数下降，单核 prep 的标量工作量被直接折减。约束是分类信息的正确性依赖向量 Compare 的标志存储语义（本 run 在 dav_3510 上实证过该路径不可靠，故保留标量 word 分类作为回退）。

实现机制：mask-run-block-classification-skip-scan 的两种粒度，均为掩码的层次化一致性分类：(a) idx28（delete__v2）粒度——索引按 32KB chunk 两遍计数分桶；掩码全程驻留 UB（Duplicate(1) + 桶内标量置零）不再走 keepGM 往返；用 Compares(uint8, EQ 0) 生成 packed 删除位图（32KB 掩码 -> 4KB 位图），u64 字扫位图时 w==0 / w==~0 走「全保留/全删除」快路径、只对混合字逐 bit 处理；空桶 chunk 以 O(1) 跳过（不发向量段、不设 barrier），每 chunk 的 PIPE_ALL 由 5 次降为 3 次，header+intervals 保持单次融合下发；(b) idx26（delete）粒度——同一分类思想落到标量形式：keep-mask 按 4B word 分类（0x01010101 全留 / 0x00000000 全删 / 混合），一次 u32 读 + 两比较替代每字 4 次字节读，标量只走 S/4 个 word，混合字与尾字节逐字节检查；index 载入改固定 32KB 分块，host 多核门控放宽为 scanBlocks>=2 且 intervalBytes<=48KB，prepBlockSize>32768 仍回退串行。两种粒度的 emit 顺序与 u/m/numInt 语义都与 champion 逐字节扫描严格一致（bit-exact），copy kernel 与 delInfo 契约均未改动。边界：idx26 路径上计划中的向量 Compares 分类在 dav_3510 上失败（VcmpvsImpl 的 StoreUnAlign 多 repeat 标志错位，flags 漂移到字上，case1 m=775/786），最终落地的是标量 u32 字分类回退形式。

## 2. 性能问题模式

- 优化目标：消除 delete_prep 的 O(S) 标量逐字节 run 扫描、keep 掩码的 GM 往返、以及每 32KB 掩码 chunk 的多次 PIPE_ALL：把掩码扫描的迭代粒度从逐字节提升到逐块/逐字，并让可跳过的块整块跳过，从而在单核 prep 上折减标量迭代量。
- 适用数据流：单核、标量主导、以逐字节扫描 keep 掩码来生成 run/interval 的 prep 类算子（掩码为逐字节 0/1 常量，可按 256B 块或 4B word 分类为全保留/全删除/混合）
- Feature signature：`{"bottleneck": ["prep-scalar-byte-scan", "mask-gm-roundtrip", "per-chunk-pipe-all", "single-core-prep"], "pattern": "mask-run-block-classification-skip-scan", "structure": ["ub-resident-mask", "word-level-mask-classification", "packed-delete-bitmap", "empty-bucket-o1-skip", "barrier-reduction"]}`

## 3. 正确性红线

- 向量 compare 分类的边界是实测出来的：idx26 计划中的向量 Compares 分类在 dav_3510 上失败（VcmpvsImpl 的 StoreUnAlign 多 repeat 标志错位，flags 漂移到字上，case1 结果 m=775/786），最终落地的是标量 u32 字分类回退形式；idx28 路径的 Compares(uint8, EQ 0) -> packed 位图形态 20/20 首次通过，但同类标志存储语义在换 SoC 时必须重新逐位验证
- 混合字/混合块比例决定收益上限：本 run 模型预估 prep 52->约31us，实测 ABBA 34.86us（模型略乐观），混合字比例高的 mid case 被「1 次均匀字快路径 + 4 次混合字处理」的混合路径摊薄
- 分桶阈值是负向边界：idx28 v1 用 chunks>=1 在单 chunk case 上回退，v2 改为阈值 4 并叠加 u64 扫描才成立；阈值下调会重新引入回退
- bit-exact 是硬契约：emit 顺序与 u/m/numInt 语义必须与 champion 逐字节扫描严格一致，否则精度门拒绝（idx26 消耗 1 轮精度修复、idx28 消耗编译 2 轮 + 性能 1 轮）
- 单核 prep 本身未被并行化：本机制削减的是单核内的工作量，非门控 case（scanBlocks 不足或 prepBlockSize>32768）仍走串行原样路径，收益不覆盖全部形状

资源与硬件约束：

- 向量分类的正确性必须在目标 SoC 上逐位验证：idx26 计划中的向量 Compares 分类（u8 标志）在 dav_3510 上因 VcmpvsImpl 的 StoreUnAlign 多 repeat 标志错位（flags 漂移到字上）失败并回退为标量 u32 字分类；idx28 路径的 Compares(uint8, EQ 0) -> packed 位图形态通过 20/20，但同一类标志存储语义仍须在落地 SoC 上验证
- emit 顺序与 u/m/numInt 语义必须与 champion 逐字节扫描严格一致，精度以 bit-exact 验收；delInfo 契约与 copy kernel 不得改动
- 分桶（按 index 32KB chunk 两遍计数）只在 chunks >= 4 时启用，否则保持每 chunk 单遍扫描——idx28 v1 的阈值 chunks >= 1 在单 chunk case 上回退，v2 改为阈值 4 + u64 扫描才成立
- 多核门控放宽后必须保留回退：prepBlockSize > 32768 仍回退串行路径
- 掩码改为 UB 常驻后不再有 keepGM 往返，需确认下游只消费 delInfo/intervals 契约（本 run delInfo 契约未动）

## 4. 泛化条件

- 策略作用域：op_class：scan

适用：

- prep 在单核上运行且标量主导：idx28 记录 delete_prep n=100 mean=792.247us 约占 matched device time 的 58%（delete_copy_fp32 28%、fp16 10%、bf16 4%）；DeletePrepKernel::Process 在 GetBlockIdx()!=0 时直接返回，整个 prep 跑在一个核上；idx26 记录 prep case 均值为第二大分量
- keep/delete 掩码是逐字节常量，可按块分类为「全保留/全删除/混合」——256B 块（idx28）与 4B word（idx26）两种粒度都可分类
- 扫描成本与标量迭代量同量级（idx26 记录约 8-15ns/迭代，[1000003]1D 266us、S=4096 full 126us、mid case 20-85us、下限 2.5us），故降低迭代粒度可直接折减时间
- 存在可 O(1) 跳过的空桶 chunk（大 index 张量下 interval 分布稀疏，本 run 以 32KB chunk 分桶后空桶可整块跳过）

不适用：

- copy kernel 不适用：本机制只作用于 delete_prep 的掩码扫描，copy 路径保持零改动
- 掩码近似随机（混合块/混合字比例极高）时快路径失效：收益退化为原逐字节扫描的常数倍折减，本 run 混合字比例高的 mid case 即被 1+4 迭代混合路径摊薄
- chunks < 4 的输入不启用分桶，退化为每 chunk 单遍扫描
- 目标 SoC 的向量 Compare 标志存储路径不可靠时（StoreUnAlign 多 repeat 错位）向量位图形态不可用，只能走标量 word 分类形式

## 5. 实施步骤

1. 掩码全程驻留 UB：Duplicate(1) 初始化 + 桶内标量置零，不再写 keepGM/读回，删掉 keep 掩码的 GM 往返（idx28 粒度）
2. 用 Compares(uint8, EQ 0) 向量生成 packed 删除位图（32KB 掩码 -> 4KB 位图），u64 字扫位图：w==0 全保留 / w==~0 全删走快路径，仅混合字按位处理，run 状态跨 chunk 连续（idx28 粒度）
3. 索引按 32KB chunk 两遍计数分桶（仅 chunks>=4 启用，否则每 chunk 单遍扫描），空桶 chunk 以 O(1) 跳过（不发向量段、不设 barrier），每 chunk 的 PIPE_ALL 由 5 次降为 3 次；header+intervals 保持单次融合 DataCopyPad 下发（idx28 粒度）
4. 标量回退形式：keep-mask 按 4B word 分类（0x01010101 全留 / 0x00000000 全删 / 混合），一次 u32 读 + 两比较替代 4 次字节读，标量只走 S/4 个 word，混合字与尾字节逐字节检查；emit 顺序与 u/m/numInt 与 champion 逐字节扫描严格一致，串行 ScanAndBuildIntervals 与并行 ProcessParallel 共用（idx26 粒度）
5. index 载入改固定 32KB 分块（indexBuf 固定 32KB）去除整表 UB 上限，每 fill-chunk 单趟散播；host 门控由 scanBlocks>=4 && idxBytes<=32KB 放宽为 scanBlocks>=2 && intervalBytes=8*(L+1)<=48KB，prepBlockSize>32768 仍回退串行（idx26 粒度）
6. 以 bit-exact 精度（emit 顺序、u/m/numInt 不变）与 prep 分量时长、copy 路径持平作为验收，copy kernel 与 delInfo 契约零改动

## 6. LLM 前置问题

- 目标实现是否满足：prep 单核运行且标量主导（本 run idx28 prep mean=792.247us 约占 matched device time 的 58%，idx26 prep case 均值为第二大分量）？
- 目标实现是否满足：keep/delete 掩码是逐字节常量，可按 256B 块或 4B word 分类为全保留/全删除/混合？
- 目标实现是否满足：扫描成本与标量迭代量同量级（本 run 约 8-15ns/迭代），降低迭代粒度可直接折减时间？
- 目标实现是否满足：存在可 O(1) 跳过的空桶 chunk（大 index 张量下 interval 分布稀疏）？
- 是否命中排除条件：改动波及 copy kernel？（本机制只作用于 delete_prep）
- 是否命中排除条件：掩码近似随机（混合块/混合字比例极高）使快路径失效？
- 是否命中排除条件：chunks < 4 不启用分桶，退化为每 chunk 单遍扫描？
- 是否命中排除条件：目标 SoC 的向量 Compare 标志存储路径不可靠（StoreUnAlign 多 repeat 错位）？

## 7. 验收标准

正确性：

- idx28：精度 20/20 PASS，首次通过、未消耗精度修复（修复记录为编译 x2 __ubuf__ 指针类型、性能 x1 分桶阈值）
- idx26：精度 20/20 bit-exact，耗 1 轮修复（attempt1 向量分类失败：case1 m=775/786，class 标志与 word 错位；改标量 u32 word 分类后通过）
- 两路均保持 emit 顺序与 u/m/numInt 语义与 champion 逐字节扫描一致；copy kernel 与 delInfo 契约未动

性能：

- idx28：形式化配对（ABBA x4、双目录交替、同 shape、溯源干净）4/4 对候选更快，36 组 (Op,case) 无 >2% 回退，kernel_geomean 54.407 -> 37.134us（1.465x），prep 全部 20 case 改善 1.05-23.9x
- idx26：ABBA 两对平衡配对 geomean 41.866 -> 37.839us（1.1065x），prep 分量 52.140 -> 34.864us（1.496x），copy 三 case 持平且对间偏差 <=0.4% 远小于效应量
- 机制级证据：idx28 掩码 GM 往返与 per-chunk barrier 被移除（PIPE_ALL 5->3）、空桶 chunk 不再发向量段；idx26 扫描迭代量由 S 降为 S/4（word 级），冻结基线两级聚合 geomean 40.656us、prep case 均值 52.103us（n=100）

回滚信号：

- 目标 SoC 上向量 Compare 的标志/位图存储语义不可靠（StoreUnAlign 多 repeat 错位），打包位图结果与掩码不一致
- 非门控 case（chunks<4、scanBlocks 不足、prepBlockSize>32768）出现回退或不再走原串行路径
- 任何 case 的 emit 顺序或 u/m/numInt 与 champion 不再 bit-exact
- copy kernel 时长或 delInfo 契约发生变化（收益归因被污染）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：vector-api-unaligned-overread

- loop_20260913_154221（operator=delete__v2, pairs=4, status=accepted, speedup=1.4652, precision=20/20 PASS 首次通过）
- loop_20260913_154221（operator=delete, pairs=2, status=accepted, speedup=1.1065, precision=20/20 PASS bit-exact，向量分类失败后改标量 word 分类，1 轮修复）

## 检索卡（短卡）

动作：把逐字节掩码扫描改为按块/按字的一致性分类跳过：掩码 UB 常驻、Compares(uint8,EQ 0) 生成 packed 位图、空桶 O(1) 跳过。
适用：prep 单核运行且标量主导、掩码为逐字节常量可按 256B 块或 4B word 分类、扫描成本与标量迭代量同量级。
限制：向量 Compares 标志语义须在目标 SoC 逐位验证；emit 顺序与 u/m/numInt 须 bit-exact。
范围：scan 类单核 prep 的掩码 run/interval 扫描。
检索词：Compares、StoreUnAlign、packed 位图、PIPE_ALL、Duplicate、ScanAndBuildIntervals
机会：O(S) 逐字节标量扫描 + keepGM 往返 + 每 32KB chunk 多次 PIPE_ALL。
代价：混合字/块比例高时被 1+4 迭代摊薄；非门控形状收益不覆盖。
