---
type: Optimization
title: D=2 配对反交错行-通道向量化快路径
description: 将D=2数据配对反交错为每lane一行；dst0承接偶索引列0，dst1承接奇索引列1，保持合并交错顺序，再单次向量加求行和。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/d2-pair-dintlv-row-per-lane.md
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
      "尾组安全阀：行数非 64 倍数的尾批整批回落逐行路径，残余时间中尾批占比可观；进一步压榨需 part-group 掩码化尾批（须独立数值验证轮，源码级等价论证不可轻信）或选取能整除每核行数的批因子",
      "工具链前提：dav_m510 双目的 LoadAlign<float,DIST_DINTLV_B32>、Cast<DX,float,{ZERO/ONE}>+Or(uint16) 合并、双源 StoreAlign<float,DIST_INTLV_B32>、DIST_BRC_B32 列广播在 ascend950 编译通过、数值逐位等价且实测带来向量化塌缩——此前对该原语家族的『死路判定』已被本证据翻转"
    ],
    "excluded_conditions": [
      "D≠2：meanRcp=0.5 的『先和后乘』逐位等价论证依赖 2 的幂，明确不得推广到其它行宽",
      "存在行距填充放大的整批经典张量 API 组织（见 small-d-flat-tensor-reorg-padding-regression 负边界）不适用本机制的替代关系",
      "每核行数少或已进入微核噪声区（几十微秒量级）的任务：进一步压榨须按微核噪声语义解读测量"
    ],
    "required_conditions": [
      "末轴 dDim == 2（host tiling 一次判定 + kernel 镜像门控；D=2 时行宽必然非 32B 对齐，属 pad 搬运路径，不引入新路由维度）",
      "每核行数 ≥128（组循环守卫 ≥64），批因子为 64 的倍数且扁平布局峰值 ≤ ubSize − reserve",
      "gamma 以 V 引擎列广播寄存器常驻，组循环外一次装载"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "0d7d7bf809489c9393cc6635a3e719a4a5ce4dad425cbba8615aa6f545331a18",
      "decision_sha256": "6487e96f62fa375a03154f2d55e6f29752d2833c6d7d912892efb6f274b4b773",
      "operator_class": "normalization",
      "performance_sha256": "b13bea972ec40ef2a3c85859254e89fc2b5b83e8b468389310d3f9bb69cb493d",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "8eefa838f2cf483dce87bab73752d618799c39a74cf3c644fad82477b6e5fc64",
      "verify_sha256": "bd1b9823ffc28e53cc05a97e84637e13de0a07971229db7d712f604a5fa4e4be"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-row-vector-instruction-floor",
      "lane-underutilization"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "gating": [
      "dDim==2",
      "rows-per-core>=128"
    ],
    "pattern": "d2-pair-deinterleave-row-per-lane",
    "reduce_mode": "row-reduce",
    "structure": [
      "flat-batch-copy",
      "dual-destination-dintlv-load",
      "row-per-lane",
      "interleaved-store",
      "brc-column-broadcast"
    ]
  },
  "generality": "op_class",
  "id": "NORM-D2-PAIR-DINTLV",
  "implementation_steps": [
    "host 在 tiling 阶段判定 dDim==2，下发门控字段并按扁平布局重算 UB 预算（保留 reserve、每核批数 ≥2 守卫）",
    "搬入/写回换为单条扁平 DataCopyPad（blockCount=1、blockLen=行数×2×sizeof(dtype) 字节，字节粒度参数纪律）",
    "pass A：x 上转 fp32 落交错影像暂存；pass B：双目的 DINTLV load 分离偶/奇列 → 行和 → rstd → 归一化 → cast·Or 合并或双源交错 store 写回；两 pass 间每批一次 LocalMemBar",
    "接线前先做编译探针 + D=2 小张量 A/B 逐位差分（0/±0/±inf/nan/subnormal/epsilon，含尾批回落形态）确认 dst0/dst1 lane 映射与合并交错顺序，探针未过不得接线",
    "尾组/尾批回落既有逐行路径；correctness 按共享模板代码全量 case 验证"
  ],
  "intent": "消除行批化后残余的逐行向量指令地板（每行固定条数的掩码向量指令 × 低 lane 利用率）——小行宽、大批数下它是向量管 critical path。",
  "mechanism": "host 仅当 dDim==2 时置 TilingData 门控字段（kernel Init 镜像判定，非每批分支）；批布局换型为扁平 [B·2] 连续元素（搬入/写回各一条 DataCopyPad，字节粒度参数）；pass A 将 x 上转 fp32 落交错影像暂存，pass B 用双目的 LoadAlign<float,DIST_DINTLV_B32> 分离偶/奇列（一行一 lane）→ 行和 → rstd → 列广播 gamma 常驻寄存器 → RegLayout ZERO/ONE cast·Or（或双源 StoreAlign<DX,DIST_INTLV_B16>）重交错写回；两 pass 间每批一次 LocalMemBar。UB 预算按扁平布局重算（约 16B/行）并保留 reserve 与每核批数 ≥2 守卫；不足 64 行的尾组与不足批行数的尾批回落既有逐行路径（安全阀，零新增尾部掩码/未对齐 store 语义面）。",
  "name": "D=2 配对反交错行-通道向量化快路径",
  "operator_class": "normalization",
  "operator_scope": "末轴 D==2 的行独立归约归一化（RmsNorm/LayerNorm 类 [N,2] 输入，任意 rank 展平为行）",
  "principle": "当每行只有 2 个有用元素时，逐行掩码指令的固定发射与空闲 lane 浪费主导向量管；把数据重排为一条 lane 承载一行（配对反交错），行和退化为跨 lane 的单次向量加法，每 64 行的规约+归一化仅需常数条向量指令。双目的反交错加载（dst0=偶索引列、dst1=奇索引列）在 UB 内完成分离、交错写回在寄存器内合并：无填充放大、无逐行发射。",
  "related_anti_patterns": [],
  "risks": [
    "lane 映射（dst0=偶索引列0 / dst1=奇索引列1）与合并交错顺序是首要数值风险，必须以 A/B 逐位探针证实而非假设",
    "『先和后乘』的 meanRcp 重排只对 2 的幂逐位等价",
    "影像暂存复用与两 pass 屏障缺失会产生批间覆盖竞态（表现为样本离散增大或双峰）"
  ],
  "slug": "d2-pair-dintlv-row-per-lane",
  "summary": "对 D==2 的行批改用扁平无填充 [B·2] 布局 + 双目的 LoadAlign<float,DIST_DINTLV_B32> 偶/奇列分离（一行一 lane，行和退化为每 64 行常数条向量指令）+ RegLayout ZERO/ONE cast·Or（或双源 DIST_INTLV_B16 store）重交错写回，整段消除逐行掩码组织的向量地板。",
  "verification": {
    "correctness": [
      "全量 case 含极值（[-inf,inf] / nan / 全零 / 极小 epsilon）",
      "A/B 逐位差分探针覆盖 lane 映射、交错合并顺序与尾批回落形态"
    ],
    "performance": [
      "以向量管绝对时间塌缩与总时延中位改善为准；同 route 门控为假的哨兵 case 必须 unchanged，Block Num 不变（核间均衡不受门控影响）"
    ],
    "rollback_signals": [
      "中位时延或 aiv_vec_time 高于证伪线即回退到上一个 accepted kernel",
      "任一控制 case 回归 ⇒ 门控泄漏或共享文件污染，回退",
      "任一 precision_mismatch ⇒ 先按逐行行因子差分定位损坏行集合，区分 lane 映射实现 bug 与机制性损坏，不得部分接受",
      "双目的 DINTLV/交错 store 编译期 static_assert 或链接失败 ⇒ 该原语在本工具链不可达，如实报告方向 exhausted 而非静默替换",
      "样本离散超阈或双峰 ⇒ 影像暂存复用/屏障竞态，先复测并核对屏障位置，仍异常即回退"
    ]
  }
}
-->

# 性能优化策略：D=2 配对反交错行-通道向量化快路径

单一优化点：对 D==2 的行批改用扁平无填充 [B·2] 布局 + 双目的 LoadAlign<float,DIST_DINTLV_B32> 偶/奇列分离（一行一 lane，行和退化为每 64 行常数条向量指令）+ RegLayout ZERO/ONE cast·Or（或双源 DIST_INTLV_B16 store）重交错写回，整段消除逐行掩码组织的向量地板。

## 1. 原理

当每行只有 2 个有用元素时，逐行掩码指令的固定发射与空闲 lane 浪费主导向量管；把数据重排为一条 lane 承载一行（配对反交错），行和退化为跨 lane 的单次向量加法，每 64 行的规约+归一化仅需常数条向量指令。双目的反交错加载（dst0=偶索引列、dst1=奇索引列）在 UB 内完成分离、交错写回在寄存器内合并：无填充放大、无逐行发射。

实现机制：host 仅当 dDim==2 时置 TilingData 门控字段（kernel Init 镜像判定，非每批分支）；批布局换型为扁平 [B·2] 连续元素（搬入/写回各一条 DataCopyPad，字节粒度参数）；pass A 将 x 上转 fp32 落交错影像暂存，pass B 用双目的 LoadAlign<float,DIST_DINTLV_B32> 分离偶/奇列（一行一 lane）→ 行和 → rstd → 列广播 gamma 常驻寄存器 → RegLayout ZERO/ONE cast·Or（或双源 StoreAlign<DX,DIST_INTLV_B16>）重交错写回；两 pass 间每批一次 LocalMemBar。UB 预算按扁平布局重算（约 16B/行）并保留 reserve 与每核批数 ≥2 守卫；不足 64 行的尾组与不足批行数的尾批回落既有逐行路径（安全阀，零新增尾部掩码/未对齐 store 语义面）。

## 2. 性能问题模式

- 优化目标：消除行批化后残余的逐行向量指令地板（每行固定条数的掩码向量指令 × 低 lane 利用率）——小行宽、大批数下它是向量管 critical path。
- 适用数据流：末轴 D==2 的行独立归约归一化（RmsNorm/LayerNorm 类 [N,2] 输入，任意 rank 展平为行）
- Feature signature：`{"bottleneck": ["per-row-vector-instruction-floor", "lane-underutilization"], "dtypes": ["fp16", "bf16", "fp32"], "gating": ["dDim==2", "rows-per-core>=128"], "pattern": "d2-pair-deinterleave-row-per-lane", "reduce_mode": "row-reduce", "structure": ["flat-batch-copy", "dual-destination-dintlv-load", "row-per-lane", "interleaved-store", "brc-column-broadcast"]}`

## 3. 正确性红线

- lane 映射（dst0=偶索引列0 / dst1=奇索引列1）与合并交错顺序是首要数值风险，必须以 A/B 逐位探针证实而非假设
- 『先和后乘』的 meanRcp 重排只对 2 的幂逐位等价
- 影像暂存复用与两 pass 屏障缺失会产生批间覆盖竞态（表现为样本离散增大或双峰）

资源与硬件约束：

- 尾组安全阀：行数非 64 倍数的尾批整批回落逐行路径，残余时间中尾批占比可观；进一步压榨需 part-group 掩码化尾批（须独立数值验证轮，源码级等价论证不可轻信）或选取能整除每核行数的批因子
- 工具链前提：dav_m510 双目的 LoadAlign<float,DIST_DINTLV_B32>、Cast<DX,float,{ZERO/ONE}>+Or(uint16) 合并、双源 StoreAlign<float,DIST_INTLV_B32>、DIST_BRC_B32 列广播在 ascend950 编译通过、数值逐位等价且实测带来向量化塌缩——此前对该原语家族的『死路判定』已被本证据翻转

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- 末轴 dDim == 2（host tiling 一次判定 + kernel 镜像门控；D=2 时行宽必然非 32B 对齐，属 pad 搬运路径，不引入新路由维度）
- 每核行数 ≥128（组循环守卫 ≥64），批因子为 64 的倍数且扁平布局峰值 ≤ ubSize − reserve
- gamma 以 V 引擎列广播寄存器常驻，组循环外一次装载

不适用：

- D≠2：meanRcp=0.5 的『先和后乘』逐位等价论证依赖 2 的幂，明确不得推广到其它行宽
- 存在行距填充放大的整批经典张量 API 组织（见 small-d-flat-tensor-reorg-padding-regression 负边界）不适用本机制的替代关系
- 每核行数少或已进入微核噪声区（几十微秒量级）的任务：进一步压榨须按微核噪声语义解读测量

## 5. 实施步骤

1. host 在 tiling 阶段判定 dDim==2，下发门控字段并按扁平布局重算 UB 预算（保留 reserve、每核批数 ≥2 守卫）
2. 搬入/写回换为单条扁平 DataCopyPad（blockCount=1、blockLen=行数×2×sizeof(dtype) 字节，字节粒度参数纪律）
3. pass A：x 上转 fp32 落交错影像暂存；pass B：双目的 DINTLV load 分离偶/奇列 → 行和 → rstd → 归一化 → cast·Or 合并或双源交错 store 写回；两 pass 间每批一次 LocalMemBar
4. 接线前先做编译探针 + D=2 小张量 A/B 逐位差分（0/±0/±inf/nan/subnormal/epsilon，含尾批回落形态）确认 dst0/dst1 lane 映射与合并交错顺序，探针未过不得接线
5. 尾组/尾批回落既有逐行路径；correctness 按共享模板代码全量 case 验证

## 6. LLM 前置问题

- 目标实现是否满足：末轴 dDim == 2（host tiling 一次判定 + kernel 镜像门控；D=2 时行宽必然非 32B 对齐，属 pad 搬运路径，不引入新路由维度）？
- 目标实现是否满足：每核行数 ≥128（组循环守卫 ≥64），批因子为 64 的倍数且扁平布局峰值 ≤ ubSize − reserve？
- 目标实现是否满足：gamma 以 V 引擎列广播寄存器常驻，组循环外一次装载？
- 是否命中排除条件：D≠2：meanRcp=0.5 的『先和后乘』逐位等价论证依赖 2 的幂，明确不得推广到其它行宽？

## 7. 验收标准

正确性：

- 全量 case 含极值（[-inf,inf] / nan / 全零 / 极小 epsilon）
- A/B 逐位差分探针覆盖 lane 映射、交错合并顺序与尾批回落形态

性能：

- 以向量管绝对时间塌缩与总时延中位改善为准；同 route 门控为假的哨兵 case 必须 unchanged，Block Num 不变（核间均衡不受门控影响）

回滚信号：

- 中位时延或 aiv_vec_time 高于证伪线即回退到上一个 accepted kernel
- 任一控制 case 回归 ⇒ 门控泄漏或共享文件污染，回退
- 任一 precision_mismatch ⇒ 先按逐行行因子差分定位损坏行集合，区分 lane 映射实现 bug 与机制性损坏，不得部分接受
- 双目的 DINTLV/交错 store 编译期 static_assert 或链接失败 ⇒ 该原语在本工具链不可达，如实报告方向 exhausted 而非静默替换
- 样本离散超阈或双峰 ⇒ 影像暂存复用/屏障竞态，先复测并核对屏障位置，仍异常即回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- rms_norm-20260825_084147-d55800（round=4, status=accepted）

## 检索卡（短卡）

动作：将D=2数据配对反交错为每lane一行；dst0承接偶索引列0，dst1承接奇索引列1，保持合并交错顺序，再单次向量加求行和。
适用：末轴 dDim==2，并由 host tiling 判定、kernel 镜像门控。
限制：非64行倍数的尾批须整批回退逐行路径；保留 reserve 与每核批数≥2守卫。
范围：normalization 的末轴 D=2 路径。
检索词：D=2、配对反交错、row-per-lane、跨-lane向量加
机会：行批化后仍有逐行掩码向量指令，且 lane 利用率低。
