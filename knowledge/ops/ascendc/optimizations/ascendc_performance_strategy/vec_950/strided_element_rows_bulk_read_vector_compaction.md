---
type: Optimization
title: 跨步元素行切片：整段连续读入 + 向量 Gather 压实 + 打包写出
description: 当切片的每个输出行只有单个元素宽时，逐块 MTE 描述符搬运使源侧有效带宽落在跨步地板（每描述符数十字节）。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/strided-element-rows-bulk-read-vector-compaction.md
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
      "MTE 写侧 32B 对齐（StoreAlign）约束写布局：GM 侧连续落盘、UB 侧按 32B padded slot 推进，host/kernel 的 alignUnit 必须一致",
      "新增 TilingData 字段后隔离安装流程不自动刷新 op_tiling 宿主库：每次触碰 host tiling 的 build 后必须重同步，否则旧字段布局喂新结构产生全零输出 + 507035 类环境陷阱",
      "正确性红线：纯位置置换、bit-exact 透传（inf/nan 原样）；只允许 host 形状门改变派发，不允许改变任何 route 的数值路径"
    ],
    "excluded_conditions": [
      "span 覆盖率过低（gap 内白读字节超过描述符节省收益）时按覆盖率门控回退原路径",
      "组边界与步长互质（L 与 S 互质）不能整除分块时必须提供头/尾部分块处理，否则不可用",
      "输出行宽 >1 元素的跨步宽行（inner>1）不在本机制覆盖内，走原路径",
      "StoreAlign 32B 存对齐限制下不可表达任意组相位偏移的单一 packed span：须用整组开槽多块读（读放大不变）"
    ],
    "required_conditions": [
      "step>1 且 inner==1（切片维度为末轴、行内宽单元素）：组内源区间连续，可整段读入",
      "压实必须走向量引擎（Reg::Gather 或向量化 strided UB 拷贝），索引用 Arange/Strided 向量化构造，禁止标量循环压实与标量索引生成",
      "span 缓冲 + 压实输出缓冲 + 打包写缓冲落在 ub_bytes（A5 253952B）内；超限按 span 分子块",
      "读放大（span 字节/净输出字节）有界且 MTE2 连续读带宽远高于跨步描述符地板时才净收益",
      "非目标 route（step==1 或 inner>1）保持原 CopyBlock 路径逐字段不变；host 门为纯形状解析，不读数据值，memset-0 语义等价 legacy"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "anti_pattern_evidence": {
        "per-element-mte-descriptor-spray": "baseline op_kernel/slice.h:ProcessRows L120-136 逐 2/4B 块 DataCopyPad（srcGap>0，每调用有效载荷 136-242B）；op_profile aiv_mte2_ratio 0.83-0.95、源侧有效读 30-38GB/s vs 同基线连续块 3.7TB/s；round 后 aiv_mte2 sum5 ~2605->208.6us",
        "scalar-compaction-cost-exceeds-stride-gain": "设计规避（卡片前置约束）：压实实现为 __simd_vf__ 向量核（op_kernel/slice_vf.h），Arange+Muls 向量化索引；本 run 未测试标量压实（先例证伪，按规避记录）",
        "strided-lowword-int64-gather-small-blocklen": "互补边界：CANN 9.1.0 dav-3510 上 lowword gather 小 blockLen 设备崩溃（507035）；本 run CANN 9.2.0 dav-3510 以 __simd_vf__ Reg::Gather b16/b32 实现，20/20 correctness + probe GO，设备稳定"
      },
      "case": "R3-strided-element-rows (cases 3/7/9/12/13, 93.65% 自基线时间份额)",
      "commit": "f319be5a7ecc6168497a6eb4e5db8aee697365e7",
      "comparison": "runs/slice-20260903_054821-826317/final/cumulative_comparison.json (total_speedup 13.0704, ok)",
      "consumed_card": {
        "kind": "run-local extra-candidate (reference-derived), archived as new catalog card",
        "path": "baseline/extra-candidates/C1-r3-bulk-read-vector-compaction.json",
        "sha256": "1c1a406afc946376878a1999ebe350d12359a2cb77411bf6742bda572146737d",
        "slug": "C1-r3-bulk-read-vector-compaction"
      },
      "operator_class": "layout-transform",
      "precision": "20/20 PASS (round + final verify)",
      "round": 1,
      "run_id": "<run-id>",
      "scoring_note": "self_baseline 模式（Ascend950DT_9582 无 slice 官方 t_hw 锚点），无官方分；验收口径=冻结自基线",
      "speedup": "cumulative 13.07x vs 冻结自基线 (self_baseline, 20 cases, 6460.96->494.32us); R3 targets per-case 6.07x-100.70x; 官方路径复测 43-67x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "0778491d150ec7666a547975c11ac523acd77a86de53507c716d318a2d39ef8e",
      "decision_sha256": "7618416d102751ef71e0734e6fdb854ac1b833e941e106853987efda84a57955",
      "operator_class": "layout-transform",
      "performance_sha256": "33dd148a7073bbfc96f812e52e7b62156d8482c2e1dcb519341b8920a3bffa7e",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "b14a86dcd7cb50d15f33e210d082fd17ea38692851958d274bb970da655b6706",
      "verify_sha256": "4c7639d9783df2bc80cd35a18ae50624b113f0ab61dce525410209251cc15e10"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "mte-descriptor-spray",
      "per-block-ub-roundtrip",
      "iterative-ub-roundtrip"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "strided-batch-copy",
    "reduce_mode": "copy",
    "structure": [
      "strided-copy",
      "tiny-row"
    ]
  },
  "generality": "op_class",
  "id": "SLICE-strided-element-rows-bulk-read-vector-compaction",
  "implementation_steps": [
    "case 路由分类确认目标 route（step>1 且 inner==1）与时间份额；核对组连续性算术（start/step/L/S 与组间 gap）",
    "host tiling 增加纯形状门 + span tile 派生（POD 字段，默认 0 = legacy）；kernel 在 ProcessRows 分派新私有函数",
    "实现三段流水：整段/整组开槽多块 GM->UB 读入（TQue depth 2）→ 向量 __simd_vf__ b16/b32 Reg::Gather 压实（Arange+Muls 索引）→ 去垫打包 UB->GM 写出",
    "互质组边界加头/尾部分块；probe 验证 Reg::Gather 对小 stride b16/b32 的吞吐与索引构造成本后再全量化",
    "控制 route 回归核对：非目标 case 逐字段字节等价；全量 correctness + 官方路径 spot check 仲裁绝对刻度"
  ],
  "intent": "消除 mte-descriptor-spray（每 2/4B 块一条 DataCopyPad 描述符 + 逐块 UB 32B 槽位往返）与 per-block-ub-roundtrip；把采集带宽从跨步描述符地板拉回连续读带宽，并把压实计算放到空闲的向量引擎",
  "mechanism": "host tiling 增加纯形状门（pathKind 等 POD 字段，memset-0 即 legacy 语义），命中『step>1 且 inner==1』时派发新 kernel 路径：按 p 组边界把组内源区间 [p*S+st, p*S+st+(L-1)*step] 划为整段 span，多块连续 DataCopyPad GM->UB（源侧单描述符，UB 按 32B 开槽落盘）；向量引擎 __simd_vf__ b16/b32 压实核用 Arange+Muls 向量化构造周期索引做 Reg::Gather UB->UB；压实结果按去垫的打包形式一次写回 GM。span 读入、向量压实、打包写出三段用深度 2 的 TQue 双缓冲重叠。组边界与步长互质时以头/尾部分块保证 bit-exact",
  "name": "跨步元素行切片：整段连续读入 + 向量 Gather 压实 + 打包写出",
  "operator_class": "layout-transform",
  "operator_scope": "步长>1、行内宽为单元素（每块有效载荷仅 1 个 2/4B 元素、源侧按固定 srcGap 跨步采集）的切片/跨步拷贝类布局变换；即任何以固定步长在 GM 上采集微小块、输出按连续行落盘的 dataflow",
  "principle": "微小块跨步访问的成本由描述符条数与槽位垫料决定而非净字节数：把 N 条微块描述符折叠为少量整段连续读（读放大有限且 MTE2 连续带宽高出跨步地板两个数量级），再用向量 Gather 在 UB 内按索引压实，等价于用廉价的向量周期换取昂贵的 MTE 描述符与垫料字节；双缓冲三级流水隐藏 MTE 与向量的串行等待",
  "related_anti_patterns": [
    "per-element-mte-descriptor-spray",
    "scalar-compaction-cost-exceeds-stride-gain",
    "strided-lowword-int64-gather-small-blocklen"
  ],
  "risks": [
    "Reg::Gather 周期索引构造（组内元素数与 span 长度取模周期）与尾窗掩码复杂度；索引必须向量化生成",
    "UB 预算三缓冲竞争；span 过大需分子块，过小则描述符收益回吐",
    "pytest 紧循环与官方 profiler 路径在深流水微核区绝对时长存在 1.25-2.0x 口径差：轮内抽查以相对增益 + control 等价性仲裁，不以绝对值直判",
    "优化后 target case 降至微核地板（launch 开销主导）：后续控制 case 读数受噪声地板支配，回归判定须用样本带宽重叠证据"
  ],
  "slug": "strided-element-rows-bulk-read-vector-compaction",
  "summary": "当切片的每个输出行只有单个元素宽时，逐块 MTE 描述符搬运使源侧有效带宽落在跨步地板（每描述符数十字节）。把每组的源区间整段连续读入 UB（一条大块描述符，接受有限读放大），在向量引擎上用 Reg::Gather 按向量化索引把目标元素压实到连续区，再去垫打包一次写回 GM，三段以深度 2 的 TQue 流水衔接。",
  "verification": {
    "correctness": [
      "全量 case correctness 100%（本 run 20/20，final verify 复验 20/20）",
      "bit-exact 透传（含 inf/nan）；互质组边界头/尾部分块字节精确",
      "非目标 route 字节等价（host 门纯形状，pathKind=0 走原路径）"
    ],
    "performance": [
      "跨步采集 route 加速（本 run 累计 total_speedup 13.07x，目标 route 6.07-100.7x，见 evidence）",
      "管线信号：向量引擎时间从 0 抬升（压实上向量）、MTE2 绝对时间塌缩（描述符喷洒消除）",
      "官方评测路径复测增益成立（target 相对冻结基线 43-67x）"
    ],
    "rollback_signals": [
      "span 覆盖率低的 shape 出现回归（读放大超限）→ 按覆盖率门控回退原路径",
      "向量压实周期超过描述符节省 → 回退或缩小 span",
      "控制 case 回归超阈且样本带宽不重叠 → 回退"
    ]
  }
}
-->

# 性能优化策略：跨步元素行切片：整段连续读入 + 向量 Gather 压实 + 打包写出

单一优化点：当切片的每个输出行只有单个元素宽时，逐块 MTE 描述符搬运使源侧有效带宽落在跨步地板（每描述符数十字节）。把每组的源区间整段连续读入 UB（一条大块描述符，接受有限读放大），在向量引擎上用 Reg::Gather 按向量化索引把目标元素压实到连续区，再去垫打包一次写回 GM，三段以深度 2 的 TQue 流水衔接。

## 1. 原理

微小块跨步访问的成本由描述符条数与槽位垫料决定而非净字节数：把 N 条微块描述符折叠为少量整段连续读（读放大有限且 MTE2 连续带宽高出跨步地板两个数量级），再用向量 Gather 在 UB 内按索引压实，等价于用廉价的向量周期换取昂贵的 MTE 描述符与垫料字节；双缓冲三级流水隐藏 MTE 与向量的串行等待

实现机制：host tiling 增加纯形状门（pathKind 等 POD 字段，memset-0 即 legacy 语义），命中『step>1 且 inner==1』时派发新 kernel 路径：按 p 组边界把组内源区间 [p*S+st, p*S+st+(L-1)*step] 划为整段 span，多块连续 DataCopyPad GM->UB（源侧单描述符，UB 按 32B 开槽落盘）；向量引擎 __simd_vf__ b16/b32 压实核用 Arange+Muls 向量化构造周期索引做 Reg::Gather UB->UB；压实结果按去垫的打包形式一次写回 GM。span 读入、向量压实、打包写出三段用深度 2 的 TQue 双缓冲重叠。组边界与步长互质时以头/尾部分块保证 bit-exact

## 2. 性能问题模式

- 优化目标：消除 mte-descriptor-spray（每 2/4B 块一条 DataCopyPad 描述符 + 逐块 UB 32B 槽位往返）与 per-block-ub-roundtrip；把采集带宽从跨步描述符地板拉回连续读带宽，并把压实计算放到空闲的向量引擎
- 适用数据流：步长>1、行内宽为单元素（每块有效载荷仅 1 个 2/4B 元素、源侧按固定 srcGap 跨步采集）的切片/跨步拷贝类布局变换；即任何以固定步长在 GM 上采集微小块、输出按连续行落盘的 dataflow
- Feature signature：`{"bottleneck": ["mte-descriptor-spray", "per-block-ub-roundtrip", "iterative-ub-roundtrip"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "strided-batch-copy", "reduce_mode": "copy", "structure": ["strided-copy", "tiny-row"]}`

## 3. 正确性红线

- Reg::Gather 周期索引构造（组内元素数与 span 长度取模周期）与尾窗掩码复杂度；索引必须向量化生成
- UB 预算三缓冲竞争；span 过大需分子块，过小则描述符收益回吐
- pytest 紧循环与官方 profiler 路径在深流水微核区绝对时长存在 1.25-2.0x 口径差：轮内抽查以相对增益 + control 等价性仲裁，不以绝对值直判
- 优化后 target case 降至微核地板（launch 开销主导）：后续控制 case 读数受噪声地板支配，回归判定须用样本带宽重叠证据

资源与硬件约束：

- MTE 写侧 32B 对齐（StoreAlign）约束写布局：GM 侧连续落盘、UB 侧按 32B padded slot 推进，host/kernel 的 alignUnit 必须一致
- 新增 TilingData 字段后隔离安装流程不自动刷新 op_tiling 宿主库：每次触碰 host tiling 的 build 后必须重同步，否则旧字段布局喂新结构产生全零输出 + 507035 类环境陷阱
- 正确性红线：纯位置置换、bit-exact 透传（inf/nan 原样）；只允许 host 形状门改变派发，不允许改变任何 route 的数值路径

## 4. 泛化条件

- 策略作用域：op_class：layout-transform

适用：

- step>1 且 inner==1（切片维度为末轴、行内宽单元素）：组内源区间连续，可整段读入
- 压实必须走向量引擎（Reg::Gather 或向量化 strided UB 拷贝），索引用 Arange/Strided 向量化构造，禁止标量循环压实与标量索引生成
- span 缓冲 + 压实输出缓冲 + 打包写缓冲落在 ub_bytes（A5 253952B）内；超限按 span 分子块
- 读放大（span 字节/净输出字节）有界且 MTE2 连续读带宽远高于跨步描述符地板时才净收益
- 非目标 route（step==1 或 inner>1）保持原 CopyBlock 路径逐字段不变；host 门为纯形状解析，不读数据值，memset-0 语义等价 legacy

不适用：

- span 覆盖率过低（gap 内白读字节超过描述符节省收益）时按覆盖率门控回退原路径
- 组边界与步长互质（L 与 S 互质）不能整除分块时必须提供头/尾部分块处理，否则不可用
- 输出行宽 >1 元素的跨步宽行（inner>1）不在本机制覆盖内，走原路径
- StoreAlign 32B 存对齐限制下不可表达任意组相位偏移的单一 packed span：须用整组开槽多块读（读放大不变）

## 5. 实施步骤

1. case 路由分类确认目标 route（step>1 且 inner==1）与时间份额；核对组连续性算术（start/step/L/S 与组间 gap）
2. host tiling 增加纯形状门 + span tile 派生（POD 字段，默认 0 = legacy）；kernel 在 ProcessRows 分派新私有函数
3. 实现三段流水：整段/整组开槽多块 GM->UB 读入（TQue depth 2）→ 向量 __simd_vf__ b16/b32 Reg::Gather 压实（Arange+Muls 索引）→ 去垫打包 UB->GM 写出
4. 互质组边界加头/尾部分块；probe 验证 Reg::Gather 对小 stride b16/b32 的吞吐与索引构造成本后再全量化
5. 控制 route 回归核对：非目标 case 逐字段字节等价；全量 correctness + 官方路径 spot check 仲裁绝对刻度

## 6. LLM 前置问题

- 目标实现是否满足：step>1 且 inner==1（切片维度为末轴、行内宽单元素）：组内源区间连续，可整段读入？
- 目标实现是否满足：压实必须走向量引擎（Reg::Gather 或向量化 strided UB 拷贝），索引用 Arange/Strided 向量化构造，禁止标量循环压实与标量索引生成？
- 目标实现是否满足：span 缓冲 + 压实输出缓冲 + 打包写缓冲落在 ub_bytes（A5 253952B）内；超限按 span 分子块？
- 是否命中排除条件：span 覆盖率过低（gap 内白读字节超过描述符节省收益）时按覆盖率门控回退原路径？

## 7. 验收标准

正确性：

- 全量 case correctness 100%（本 run 20/20，final verify 复验 20/20）
- bit-exact 透传（含 inf/nan）；互质组边界头/尾部分块字节精确
- 非目标 route 字节等价（host 门纯形状，pathKind=0 走原路径）

性能：

- 跨步采集 route 加速（本 run 累计 total_speedup 13.07x，目标 route 6.07-100.7x，见 evidence）
- 管线信号：向量引擎时间从 0 抬升（压实上向量）、MTE2 绝对时间塌缩（描述符喷洒消除）
- 官方评测路径复测增益成立（target 相对冻结基线 43-67x）

回滚信号：

- span 覆盖率低的 shape 出现回归（读放大超限）→ 按覆盖率门控回退原路径
- 向量压实周期超过描述符节省 → 回退或缩小 span
- 控制 case 回归超阈且样本带宽不重叠 → 回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-element-mte-descriptor-spray, scalar-compaction-cost-exceeds-stride-gain, strided-lowword-int64-gather-small-blocklen

- slice-20260903_054821-826317（round=1, status=accepted, case=R3-strided-element-rows (cases 3/7/9/12/13, 93.65% 自基线时间份额), speedup=cumulative 13.07x vs 冻结自基线 (self_baseline, 20 cases, 6460.96->494.32us); R3 targets per-case 6.07x-100.70x; 官方路径复测 43-67x）
- slice-20260903_054821-826317（round=1, status=accepted）

## 检索卡（短卡）

动作：把逐 2/4B 微块 DataCopyPad 改为整段连续读入 UB、向量 Gather 压实后再去垫打包写回。
适用：step>1 且 inner==1（切片维末轴、行内宽单元素）；压实须走向量引擎。
限制：span 覆盖率过低须按覆盖率回退；L 与 S 互质须头/尾部分块；inner>1 走原路径。
范围：切片/跨步拷贝类 layout-transform 的采集与落盘
检索词：DataCopyPad、Reg::Gather、Arange+Muls、__simd_vf__、TQue depth 2、StoreAlign
机会：每描述符仅数十字节有效载荷，源侧有效读远低于连续块带宽
代价：读放大；UB 三缓冲竞争，span 过小则描述符收益回吐
