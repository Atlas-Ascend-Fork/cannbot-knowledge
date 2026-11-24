---
type: Optimization
title: 微型元数据标量 GM 直读：删除 GM->UB MTE2 暂存与 tile TBuf
description: 把微型元数据张量的GM→UB MTE2暂存与tile TBuf整段删除，改为在标量check循环里逐元素直读GM。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/tiny-tensor-direct-scalar-gm-read.md
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
      "改动限定在 kernel/usecudnnctcloss_kernel.h（implementation_summary 只列出该文件）；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）保持不变",
      "标量 GM 直读的可见性必须由精度门（20 case 位精确 bool）裁决，不得仅凭源码注释里的顾虑否决该机制",
      "谓词边界必须与 golden/ATen 对齐：0 < input_lengths[i] <= T、0 <= target_lengths[i] < 256、target_lengths[i] <= input_lengths[i]",
      "冻结基线的精度状态必须如实记录：本 run 的冻结基线本身 15/20 失败（pre-existing champion il==T 缺陷），且在只读原工程上独立复现同集合同形态失败；不得把继承的失败当作新机制引入，也不得把过期世系的 20/20 报告当作基线证据"
    ],
    "excluded_conditions": [
      "元素数大到逐元素标量 GM 直读本身成为 Scalar 瓶颈时不适用：那是 index-scalar-bulk-mte2-* 家族的域（每行 O(K) 次标量 GM GetValue），其正确载体是 host 流量门控 + UB 批量搬运；本机制是它的逆——流量小到暂存路径的固定成本大于直读成本",
      "被读的元数据需要参与向量/归约计算而非仅做标量判定时不适用：直读只对逐元素标量消费成立（本 run 的消费点是 check 循环里的比较）",
      "输入来源无法保证与 kernel 同流序、或存在标量 GM 可见性竞态风险时不适用",
      "暂存路径还承担别的语义（对齐、广播、类型转换）而不只是搬运时删不掉"
    ],
    "required_conditions": [
      "被暂存的张量是微型元数据（元素数 <= 数次）：全部 20 个测试 case 的 N ∈ {1,2}（log_probs shape [T,N,C]），CheckTile 循环 <=2 次、tileCount 恒为 1；实际输入载荷 <=8 字节/张量，而 champion Init() 每次 launch 用 TPipe::InitBuffer 分配两个 8192 元素（32KB）int32 tile 缓冲 + 32B out 缓冲",
      "瓶颈是 per-launch 固定成本而非循环体：稳态 aiv_scalar 0.738-0.901us（ratio 0.60-0.66）、aiv_mte2 0.368-0.412us（ratio 0.28-0.33）、aiv_mte3 ~0.08us、aiv_vec 0.0us；strategy router 判定全局瓶颈 AIV Scalar 63.6%（1/1 分组）",
      "被删路径的固定成本可逐项枚举：两个 32KB 输入 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S SetFlag/WaitFlag 事件对、以及 UCTC_TILE_ELEMS tiling；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）是唯一保留项",
      "标量 GM 直读的可见性可由精度门裁决：输入由 stream 序 H2D（.npu()）产生，本 SoC 上标量 GM 读能否看见同流上游写入未经验证（源码注释曾以可见性顾虑为由刻意选择 DataCopyPad，repo 内无 profiling 证据支持实际竞态），本 run 用 20 case 位精确 bool 精度门裁决"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "task_0387_aten__use_cudnn_ctc_loss",
      "operator_class": "mask-predicate",
      "precision": "20/20 PASS bit-exact（round-02 谓词修复后；round-01 与冻结基线同为 15/20 且失败集合/形态相同，标量 GM 读返回与暂存路径逐值相同）",
      "run_id": "<run-id>",
      "speedup": 1.0728,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "aiv-scalar-fixed-overhead",
      "per-call-initbuffer-descriptor",
      "mte2-staging-fixed-cost",
      "tiny-tensor-ub-staging-roundtrip"
    ],
    "dtypes": [
      "int32"
    ],
    "pattern": "tiny-tensor-direct-scalar-gm-read",
    "reduce_mode": "",
    "structure": [
      "gm-scalar-direct-load",
      "staging-path-deletion",
      "two-tile-tbuf-removal",
      "output-path-unchanged",
      "golden-conformant-predicate-bounds"
    ]
  },
  "generality": "op_class",
  "id": "SCALAR-GM-DIRECT-LOAD-TINY-TENSOR",
  "implementation_steps": [
    "确认元数据张量的元素数上界（本 run 全部 20 case 的 N ∈ {1,2}、CheckTile 循环 <=2 次、tileCount 恒为 1）与暂存路径的全部固定成本项（两个 32KB 输入 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S 事件对、UCTC_TILE_ELEMS tiling）",
    "round_01 在 kernel/usecudnnctcloss_kernel.h 做单次编辑：check 循环里改用 inLenGM_.GetValue(i)/tgtLenGM_.GetValue(i) 直接标量 GM 读，删除上述暂存路径；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）保持原样",
    "先决条件检验：用 20 case 位精确 bool 精度门裁决标量 GM 直读的可见性（本 run round-01 的失败集合与冻结基线完全相同且取值逐值相同，证明直读与暂存路径等价）",
    "round_02 精度修复（1/3 预算）：把谓词边界对齐 golden/ATen 语义（0 < input_lengths[i] <= T、0 <= target_lengths[i] < 256、target_lengths[i] <= input_lengths[i]），恢复 20/20 bit-exact",
    "以形式化配对 ABBA（同 shape、provenance clean、平衡交替、逐 case 无回退）验收，并核对 aiv_mte2 的塌缩与 aiv_scalar 的转移是否净赚；任一精度失败或未补偿回退即回滚"
  ],
  "intent": "消除微型元数据张量（长度/计数类，元素数 <= 数次）走 GM->UB MTE2 暂存带来的 per-launch 固定开销：两个 32KB tile TBuf 的 InitBuffer、DataCopyPad pair、每 tile 的 MTE2_S 事件对，以及 MTE2 引入的 ~0.37us 延迟；改为在标量 check 循环里直接 GM 直读。",
  "mechanism": "gm-scalar-direct-load：round_01 对 kernel/usecudnnctcloss_kernel.h 做单次编辑——在 check 循环里直接调 inLenGM_.GetValue(i)/tgtLenGM_.GetValue(i)，删除两个 32KB tile 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S 事件对与 UCTC_TILE_ELEMS tiling；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）保持不变。round_02 是同方向的一次精度修复（1/3 预算）：把谓词边界对齐到 golden/ATen 语义（0 < input_lengths[i] <= T、0 <= target_lengths[i] < 256、target_lengths[i] <= input_lengths[i]）。",
  "name": "微型元数据标量 GM 直读：删除 GM->UB MTE2 暂存与 tile TBuf",
  "operator_class": "mask-predicate",
  "operator_scope": "读入极少量标量元数据（长度/计数/标志类微型张量）做判定并输出、kernel 属固定开销微内核（Block Num 小、aiv_vec 为 0、非带宽/计算受限）的场景；典型如 _use_cudnn_ctc_loss 的输入长度校验（Block Num=1、N<=2、32KB 输入 tile 却只承载 <=8 字节）",
  "principle": "在 microkernel 量级，wall 由 per-launch 固定成本决定而不是由载荷决定：本 run 稳态 aiv_scalar 0.738-0.901us（ratio 0.60-0.66）与 aiv_mte2 0.368-0.412us（ratio 0.28-0.33）构成全部时间，aiv_vec 为 0、aiv_mte3 约 0.08us，实测 Task Duration 均值 1.568us（min 1.173us），而两个长度张量的实际载荷 <=8 字节/张量。为 <=8 字节的数据付一条完整的 MTE2 暂存路径（两个 8192 元素/32KB int32 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S SetFlag/WaitFlag 事件对）在固定成本项上是纯亏损：这些描述符与事件开销与载荷大小无关，而标量管本来就要为校验循环取数。当元数据张量元素数少到可以逐元素标量直读时，把 GM->UB 暂存整段删掉、改在 check 循环里用 GlobalTensor::GetValue 直接读，既省掉暂存侧的一次性固定开销，又省掉 MTE2 的 ~0.37us 延迟。这条机制的判据是流量量级：暂存路径的固定成本（InitBuffer 描述符 + 事件对 + DataCopyPad 发射 + tiling 常量）对 O(几次) 的元素是常数、对 O(K) 的元素才是可摊销项——因此它与 index-scalar-bulk-mte2-* 家族的结论方向相反（那里逐元素标量 GM 读本身成为 Scalar 瓶颈，正确载体是把标量索引数组批量搬进 UB），而 index-scalar-bulk-mte2-traffic-gated-boundary 只把『小流量保持原路径』写成流量门控的边界结论，从未把 direct-scalar-read-over-staging 立成正向机制。源码注释里曾以可见性顾虑为由刻意选择 DataCopyPad，本 run 用精度门把它证伪：标量 GM 直读返回与暂存路径完全相同的值。",
  "related_anti_patterns": [
    "index-scalar-bulk-mte2-traffic-gated-boundary",
    "index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget",
    "index-scalar-bulk-mte2-ub-resident-lesson",
    "launch-arg-by-value-tiling-fetch-elimination"
  ],
  "risks": [
    "可见性是机制的隐含前提：源码注释记录的顾虑是『标量 GM 读可能看不见上游/同流写入』；本 run 的实证是 round-01 单次编辑后继承了冻结基线的 15/20 同集合同形态失败，而标量 GM 读返回与暂存路径完全相同的值（可见性顾虑被反驳），但该结论只对本 run 的 ascend950 + 同流 H2D 输入成立，换输入生产路径需重验",
    "精度门必须先与被测基线对齐：本 run 的冻结基线自带 15/20 的 champion 既有谓词缺陷（il==T vs golden/ATen il<=T），若直接以 20/20 为目标会把『修复既有缺陷』与『机制回归』混为一谈；round-02 的谓词修复消耗了 1/3 修复预算",
    "microkernel 量级的收益绝对值小：geomean 1.2371->1.1531us 的总差 ~0.084us，必须在同 shape/provenance clean/平衡交替的 ABBA 配对下才可归因（本 run 16/16 case 在两对中均更快，相关性无歧义）",
    "staging 删除后要确认没有别的消费者：两个 tile TBuf 与 CopyLengths() 一旦被其它分支（如更宽 N 的路径）复用，删除会破坏那些路径；本 run 的 N<=2 使 CheckTile 循环与 tileCount 都退化",
    "GM 标量装载延迟会转移成本：直读把 ~0.32us 加到 aiv_scalar 上（0.395us 的 mte2 塌缩到 0.006us 仍净赚），若某个算子的标量管已饱和，这笔转移可能吃掉收益"
  ],
  "slug": "tiny-tensor-direct-scalar-gm-read",
  "summary": "_use_cudnn_ctc_loss 是固定开销微内核：Block Num=1、aiv_vec 为 0，稳态 aiv_scalar 0.738-0.901us 与 aiv_mte2 0.368-0.412us 就是全部时间，而两个 int32 长度张量（input_lengths/target_lengths，全部 case N ∈ {1,2}）的载荷 <=8 字节/张量，却每次 launch 都要走一遍 GM->UB MTE2 暂存：两个 8192 元素（32KB）int32 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S 事件对。把暂存整段删掉、改在 check 循环里标量 GM 直读（inLenGM_.GetValue(i)/tgtLenGM_.GetValue(i)），输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）不变：aiv_mte2 由 0.395us 塌缩到 0.006us，形式化配对 ABBA 2 对 16/16 case 均更快，geomean 1.2371->1.1531us = 1.0728x，代价是 GM 标量装载延迟给 aiv_scalar 加 ~0.32us。方向与 index-scalar-bulk-mte2-* 家族相反（那里是把标量索引数组批量搬进 UB）。精度侧另附一次谓词修复：冻结基线本身带 champion 既有的 il==T 缺陷（15/20），修复为 golden/ATen 语义后 20/20 bit-exact。",
  "verification": {
    "correctness": [
      "round-01 单次编辑后继承了冻结基线的 15/20 失败，失败集合与形态完全相同——标量 GM 读返回值与暂存路径逐值相同，可见性顾虑被实证反驳",
      "冻结基线本身在只读原工程上独立复现同样 15/20（champion 既有谓词缺陷 il==T，golden/ATen 语义为 il<=T）；归档的 20/20 报告是来自另一世系（2026-08-17）的过期证据，已在 baseline/profiling/summary.yaml 的 accuracy 段落记录",
      "round-02 谓词修复（1/3 预算，边界 0<il<=T、0<=tl<256、tl<=il）恢复 20/20 bit-exact PASS"
    ],
    "performance": [
      "形式化配对 ABBA 2 对（B C C B，4 次独立 msprof，双 workspace 各自不同 .so，同 shape）：geomean 1.2371->1.1531us = 1.0728x，16/16 case 在两对中均更快（pair geomean ratio 0.938 与 0.9263），provenance clean、相关性无歧义",
      "aiv_mte2 由 0.395us 塌缩到 0.006us；GM 标量装载延迟使 aiv_scalar 增加约 0.32us，仍净赚；16 个 case 的 candidate 均值 1.1212-1.2006us vs baseline 1.2029-1.2855us",
      "全测试脚本 screening 口径 baseline 1.489us -> candidate 1.413us；形式化配对口径 1.2371 -> 1.1531us——两个口径的数值均照录，不用前者替换后者"
    ],
    "rollback_signals": [
      "任何 case 的精度不再是 20/20 bit-exact，尤其标量 GM 直读与暂存路径取值不一致（可见性竞态）",
      "形式化 ABBA 配对未达采纳门（geomean 未改善）或出现未补偿的 per-case 回退",
      "aiv_mte2 已塌缩而 wall 不变：说明省下的不是 pacing 工作，收益无法归因",
      "删除 staging 后其它分支（更宽 N / 其它 shape）失去其依赖的 tile TBuf 或 CopyLengths() 语义"
    ]
  }
}
-->

# 性能优化策略：微型元数据标量 GM 直读：删除 GM->UB MTE2 暂存与 tile TBuf

_use_cudnn_ctc_loss 是固定开销微内核：Block Num=1、aiv_vec 为 0，稳态 aiv_scalar 0.738-0.901us 与 aiv_mte2 0.368-0.412us 就是全部时间，而两个 int32 长度张量（input_lengths/target_lengths，全部 case N ∈ {1,2}）的载荷 <=8 字节/张量，却每次 launch 都要走一遍 GM->UB MTE2 暂存：两个 8192 元素（32KB）int32 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S 事件对。把暂存整段删掉、改在 check 循环里标量 GM 直读（inLenGM_.GetValue(i)/tgtLenGM_.GetValue(i)），输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）不变：aiv_mte2 由 0.395us 塌缩到 0.006us，形式化配对 ABBA 2 对 16/16 case 均更快，geomean 1.2371->1.1531us = 1.0728x，代价是 GM 标量装载延迟给 aiv_scalar 加 ~0.32us。方向与 index-scalar-bulk-mte2-* 家族相反（那里是把标量索引数组批量搬进 UB）。精度侧另附一次谓词修复：冻结基线本身带 champion 既有的 il==T 缺陷（15/20），修复为 golden/ATen 语义后 20/20 bit-exact。

## 1. 原理

在 microkernel 量级，wall 由 per-launch 固定成本决定而不是由载荷决定：本 run 稳态 aiv_scalar 0.738-0.901us（ratio 0.60-0.66）与 aiv_mte2 0.368-0.412us（ratio 0.28-0.33）构成全部时间，aiv_vec 为 0、aiv_mte3 约 0.08us，实测 Task Duration 均值 1.568us（min 1.173us），而两个长度张量的实际载荷 <=8 字节/张量。为 <=8 字节的数据付一条完整的 MTE2 暂存路径（两个 8192 元素/32KB int32 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S SetFlag/WaitFlag 事件对）在固定成本项上是纯亏损：这些描述符与事件开销与载荷大小无关，而标量管本来就要为校验循环取数。当元数据张量元素数少到可以逐元素标量直读时，把 GM->UB 暂存整段删掉、改在 check 循环里用 GlobalTensor::GetValue 直接读，既省掉暂存侧的一次性固定开销，又省掉 MTE2 的 ~0.37us 延迟。这条机制的判据是流量量级：暂存路径的固定成本（InitBuffer 描述符 + 事件对 + DataCopyPad 发射 + tiling 常量）对 O(几次) 的元素是常数、对 O(K) 的元素才是可摊销项——因此它与 index-scalar-bulk-mte2-* 家族的结论方向相反（那里逐元素标量 GM 读本身成为 Scalar 瓶颈，正确载体是把标量索引数组批量搬进 UB），而 index-scalar-bulk-mte2-traffic-gated-boundary 只把『小流量保持原路径』写成流量门控的边界结论，从未把 direct-scalar-read-over-staging 立成正向机制。源码注释里曾以可见性顾虑为由刻意选择 DataCopyPad，本 run 用精度门把它证伪：标量 GM 直读返回与暂存路径完全相同的值。

实现机制：gm-scalar-direct-load：round_01 对 kernel/usecudnnctcloss_kernel.h 做单次编辑——在 check 循环里直接调 inLenGM_.GetValue(i)/tgtLenGM_.GetValue(i)，删除两个 32KB tile 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S 事件对与 UCTC_TILE_ELEMS tiling；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）保持不变。round_02 是同方向的一次精度修复（1/3 预算）：把谓词边界对齐到 golden/ATen 语义（0 < input_lengths[i] <= T、0 <= target_lengths[i] < 256、target_lengths[i] <= input_lengths[i]）。

## 2. 性能问题模式

- 优化目标：消除微型元数据张量（长度/计数类，元素数 <= 数次）走 GM->UB MTE2 暂存带来的 per-launch 固定开销：两个 32KB tile TBuf 的 InitBuffer、DataCopyPad pair、每 tile 的 MTE2_S 事件对，以及 MTE2 引入的 ~0.37us 延迟；改为在标量 check 循环里直接 GM 直读。
- 适用数据流：读入极少量标量元数据（长度/计数/标志类微型张量）做判定并输出、kernel 属固定开销微内核（Block Num 小、aiv_vec 为 0、非带宽/计算受限）的场景；典型如 _use_cudnn_ctc_loss 的输入长度校验（Block Num=1、N<=2、32KB 输入 tile 却只承载 <=8 字节）
- Feature signature：`{"bottleneck": ["aiv-scalar-fixed-overhead", "per-call-initbuffer-descriptor", "mte2-staging-fixed-cost", "tiny-tensor-ub-staging-roundtrip"], "dtypes": ["int32"], "pattern": "tiny-tensor-direct-scalar-gm-read", "reduce_mode": "", "structure": ["gm-scalar-direct-load", "staging-path-deletion", "two-tile-tbuf-removal", "output-path-unchanged", "golden-conformant-predicate-bounds"]}`

## 3. 正确性红线

- 可见性是机制的隐含前提：源码注释记录的顾虑是『标量 GM 读可能看不见上游/同流写入』；本 run 的实证是 round-01 单次编辑后继承了冻结基线的 15/20 同集合同形态失败，而标量 GM 读返回与暂存路径完全相同的值（可见性顾虑被反驳），但该结论只对本 run 的 ascend950 + 同流 H2D 输入成立，换输入生产路径需重验
- 精度门必须先与被测基线对齐：本 run 的冻结基线自带 15/20 的 champion 既有谓词缺陷（il==T vs golden/ATen il<=T），若直接以 20/20 为目标会把『修复既有缺陷』与『机制回归』混为一谈；round-02 的谓词修复消耗了 1/3 修复预算
- microkernel 量级的收益绝对值小：geomean 1.2371->1.1531us 的总差 ~0.084us，必须在同 shape/provenance clean/平衡交替的 ABBA 配对下才可归因（本 run 16/16 case 在两对中均更快，相关性无歧义）
- staging 删除后要确认没有别的消费者：两个 tile TBuf 与 CopyLengths() 一旦被其它分支（如更宽 N 的路径）复用，删除会破坏那些路径；本 run 的 N<=2 使 CheckTile 循环与 tileCount 都退化
- GM 标量装载延迟会转移成本：直读把 ~0.32us 加到 aiv_scalar 上（0.395us 的 mte2 塌缩到 0.006us 仍净赚），若某个算子的标量管已饱和，这笔转移可能吃掉收益

资源与硬件约束：

- 改动限定在 kernel/usecudnnctcloss_kernel.h（implementation_summary 只列出该文件）；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）保持不变
- 标量 GM 直读的可见性必须由精度门（20 case 位精确 bool）裁决，不得仅凭源码注释里的顾虑否决该机制
- 谓词边界必须与 golden/ATen 对齐：0 < input_lengths[i] <= T、0 <= target_lengths[i] < 256、target_lengths[i] <= input_lengths[i]
- 冻结基线的精度状态必须如实记录：本 run 的冻结基线本身 15/20 失败（pre-existing champion il==T 缺陷），且在只读原工程上独立复现同集合同形态失败；不得把继承的失败当作新机制引入，也不得把过期世系的 20/20 报告当作基线证据

## 4. 泛化条件

- 策略作用域：op_class：mask-predicate

适用：

- 被暂存的张量是微型元数据（元素数 <= 数次）：全部 20 个测试 case 的 N ∈ {1,2}（log_probs shape [T,N,C]），CheckTile 循环 <=2 次、tileCount 恒为 1；实际输入载荷 <=8 字节/张量，而 champion Init() 每次 launch 用 TPipe::InitBuffer 分配两个 8192 元素（32KB）int32 tile 缓冲 + 32B out 缓冲
- 瓶颈是 per-launch 固定成本而非循环体：稳态 aiv_scalar 0.738-0.901us（ratio 0.60-0.66）、aiv_mte2 0.368-0.412us（ratio 0.28-0.33）、aiv_mte3 ~0.08us、aiv_vec 0.0us；strategy router 判定全局瓶颈 AIV Scalar 63.6%（1/1 分组）
- 被删路径的固定成本可逐项枚举：两个 32KB 输入 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S SetFlag/WaitFlag 事件对、以及 UCTC_TILE_ELEMS tiling；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）是唯一保留项
- 标量 GM 直读的可见性可由精度门裁决：输入由 stream 序 H2D（.npu()）产生，本 SoC 上标量 GM 读能否看见同流上游写入未经验证（源码注释曾以可见性顾虑为由刻意选择 DataCopyPad，repo 内无 profiling 证据支持实际竞态），本 run 用 20 case 位精确 bool 精度门裁决

不适用：

- 元素数大到逐元素标量 GM 直读本身成为 Scalar 瓶颈时不适用：那是 index-scalar-bulk-mte2-* 家族的域（每行 O(K) 次标量 GM GetValue），其正确载体是 host 流量门控 + UB 批量搬运；本机制是它的逆——流量小到暂存路径的固定成本大于直读成本
- 被读的元数据需要参与向量/归约计算而非仅做标量判定时不适用：直读只对逐元素标量消费成立（本 run 的消费点是 check 循环里的比较）
- 输入来源无法保证与 kernel 同流序、或存在标量 GM 可见性竞态风险时不适用
- 暂存路径还承担别的语义（对齐、广播、类型转换）而不只是搬运时删不掉

## 5. 实施步骤

1. 确认元数据张量的元素数上界（本 run 全部 20 case 的 N ∈ {1,2}、CheckTile 循环 <=2 次、tileCount 恒为 1）与暂存路径的全部固定成本项（两个 32KB 输入 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S 事件对、UCTC_TILE_ELEMS tiling）
2. round_01 在 kernel/usecudnnctcloss_kernel.h 做单次编辑：check 循环里改用 inLenGM_.GetValue(i)/tgtLenGM_.GetValue(i) 直接标量 GM 读，删除上述暂存路径；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）保持原样
3. 先决条件检验：用 20 case 位精确 bool 精度门裁决标量 GM 直读的可见性（本 run round-01 的失败集合与冻结基线完全相同且取值逐值相同，证明直读与暂存路径等价）
4. round_02 精度修复（1/3 预算）：把谓词边界对齐 golden/ATen 语义（0 < input_lengths[i] <= T、0 <= target_lengths[i] < 256、target_lengths[i] <= input_lengths[i]），恢复 20/20 bit-exact
5. 以形式化配对 ABBA（同 shape、provenance clean、平衡交替、逐 case 无回退）验收，并核对 aiv_mte2 的塌缩与 aiv_scalar 的转移是否净赚；任一精度失败或未补偿回退即回滚

## 6. LLM 前置问题

- 目标实现是否满足：被暂存的张量是微型元数据（元素数 <= 数次）：全部 20 个测试 case 的 N ∈ {1,2}（log_probs shape [T,N,C]），CheckTile 循环 <=2 次、tileCount 恒为 1；实际输入载荷 <=8 字节/张量，而 champion Init() 每次 launch 用 TPipe::InitBuffer 分配两个 8192 元素（32KB）int32 tile 缓冲 + 32B out 缓冲？
- 目标实现是否满足：瓶颈是 per-launch 固定成本而非循环体：稳态 aiv_scalar 0.738-0.901us（ratio 0.60-0.66）、aiv_mte2 0.368-0.412us（ratio 0.28-0.33）、aiv_mte3 ~0.08us、aiv_vec 0.0us；strategy router 判定全局瓶颈 AIV Scalar 63.6%（1/1 分组）？
- 目标实现是否满足：被删路径的固定成本可逐项枚举：两个 32KB 输入 tile TBuf 的 InitBuffer、CopyLengths() 的 DataCopyPad pair、每 tile 的 MTE2_S SetFlag/WaitFlag 事件对、以及 UCTC_TILE_ELEMS tiling；输出路径（outBuf + S_MTE2 同步 + 4B DataCopyPad）是唯一保留项？
- 目标实现是否满足：标量 GM 直读的可见性可由精度门裁决：输入由 stream 序 H2D（.npu()）产生，本 SoC 上标量 GM 读能否看见同流上游写入未经验证（源码注释曾以可见性顾虑为由刻意选择 DataCopyPad，repo 内无 profiling 证据支持实际竞态），本 run 用 20 case 位精确 bool 精度门裁决？
- 是否命中排除条件：元素数大到逐元素标量 GM 直读本身成为 Scalar 瓶颈时不适用：那是 index-scalar-bulk-mte2-* 家族的域（每行 O(K) 次标量 GM GetValue），其正确载体是 host 流量门控 + UB 批量搬运；本机制是它的逆——流量小到暂存路径的固定成本大于直读成本？
- 是否命中排除条件：被读的元数据需要参与向量/归约计算而非仅做标量判定时不适用：直读只对逐元素标量消费成立（本 run 的消费点是 check 循环里的比较）？
- 是否命中排除条件：输入来源无法保证与 kernel 同流序、或存在标量 GM 可见性竞态风险时不适用？
- 是否命中排除条件：暂存路径还承担别的语义（对齐、广播、类型转换）而不只是搬运时删不掉？

## 7. 验收标准

正确性：

- round-01 单次编辑后继承了冻结基线的 15/20 失败，失败集合与形态完全相同——标量 GM 读返回值与暂存路径逐值相同，可见性顾虑被实证反驳
- 冻结基线本身在只读原工程上独立复现同样 15/20（champion 既有谓词缺陷 il==T，golden/ATen 语义为 il<=T）；归档的 20/20 报告是来自另一世系（2026-08-17）的过期证据，已在 baseline/profiling/summary.yaml 的 accuracy 段落记录
- round-02 谓词修复（1/3 预算，边界 0<il<=T、0<=tl<256、tl<=il）恢复 20/20 bit-exact PASS

性能：

- 形式化配对 ABBA 2 对（B C C B，4 次独立 msprof，双 workspace 各自不同 .so，同 shape）：geomean 1.2371->1.1531us = 1.0728x，16/16 case 在两对中均更快（pair geomean ratio 0.938 与 0.9263），provenance clean、相关性无歧义
- aiv_mte2 由 0.395us 塌缩到 0.006us；GM 标量装载延迟使 aiv_scalar 增加约 0.32us，仍净赚；16 个 case 的 candidate 均值 1.1212-1.2006us vs baseline 1.2029-1.2855us
- 全测试脚本 screening 口径 baseline 1.489us -> candidate 1.413us；形式化配对口径 1.2371 -> 1.1531us——两个口径的数值均照录，不用前者替换后者

回滚信号：

- 任何 case 的精度不再是 20/20 bit-exact，尤其标量 GM 直读与暂存路径取值不一致（可见性竞态）
- 形式化 ABBA 配对未达采纳门（geomean 未改善）或出现未补偿的 per-case 回退
- aiv_mte2 已塌缩而 wall 不变：说明省下的不是 pacing 工作，收益无法归因
- 删除 staging 后其它分支（更宽 N / 其它 shape）失去其依赖的 tile TBuf 或 CopyLengths() 语义

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：index-scalar-bulk-mte2-traffic-gated-boundary, index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget, index-scalar-bulk-mte2-ub-resident-lesson, launch-arg-by-value-tiling-fetch-elimination

- loop_20260915_161957（round=2, status=accepted, speedup=1.0728, precision=20/20 PASS bit-exact（round-02 谓词修复后；round-01 与冻结基线同为 15/20 且失败集合/形态相同，标量 GM 读返回与暂存路径逐值相同））

## 检索卡（短卡）

动作：把微型元数据张量的GM→UB MTE2暂存与tile TBuf整段删除，改为在标量check循环里逐元素直读GM
适用：被暂存张量是微型元数据（CheckTile<=2 次、载荷<=8 字节/张量）；瓶颈是per-launch固定成本而非循环体
限制：可见性仅在ascend950+同流H2D输入下经精度门证伪，换输入生产路径须重验；TBuf被其它分支复用则不可删
范围：读入极少量标量元数据做判定并输出的固定开销微内核取数路径
检索词：GlobalTensor::GetValue、DataCopyPad、InitBuffer、TBuf、MTE2_S、UCTC_TILE_ELEMS
机会：为<=8字节载荷付MTE2暂存：aiv_mte2 0.37-0.41us、aiv_scalar 0.74-0.90us即全部时间
代价：GM标量装载延迟给aiv_scalar加约0.32us，标量管已饱和时可能吃掉收益
