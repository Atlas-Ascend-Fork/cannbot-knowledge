---
type: Optimization
title: 小 xDim 索引 gather 列窗 slab 整块 MTE2 + SIMD 向量 Gather 替换逐元素 SIMT 散射读
description: 把逐元素 GM 散射读改为按 chunk 列窗整块 MTE2 搬入双缓冲 slab，SIMT 构偏移后由 SIMD Gather 收集。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/t2-small-xdim-slab-bulk-mte2-simd-gather.md
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
      "2D 多块 DataCopyPad 的 srcStride 字段在大 stride（实测 ~579KB）溢出产生错数据；小 xDim 下用逐行单块拷贝规避（描述符成本可忽略），见 common 卡 2d-datacopy-ext-stride-field-limit",
      "同一 Compute 内 SIMT 偏移构建与 SIMD 消费之间必须显式 PipeBarrier<PIPE_V>（V→V 顺序非隐式），见 common 卡 vf-simd-simt-sequential-ordering-barrier",
      "slab 必须经 TQue EnQue/DeQue 承载 MTE2→V 同步；不得用 TBuf 裸窗口跨流水读取",
      "host 门为纯形状解析（不读张量数据值），非目标 case 必须逐字段一致"
    ],
    "excluded_conditions": [
      "xDim 大到 slab 超出 UB 预算或 MTE2 聚合带宽饱和成为新瓶颈（兑现后被 MTE2 包络锁死，继续提速需攻击 MTE2 侧）",
      "索引 gather 语义无法表达为 y[p]=x[rowBase+idx[p]·inner+m0+p] 的列窗恒等式（跨行 trail 不匹配等）",
      "瓶颈为字节带宽或每 chunk 固定开销（加大 C 或提升线程宽的天花板 ~1.1x，本机制不适用）"
    ],
    "required_conditions": [
      "索引前缀维 xDim 足够小，使 xDim·C·dtype 的 slab 窗在 UB 预算内且块对齐可满足",
      "每个输出元素的 x 读取当前为逐元素离散 GM 访问（散射请求主导而非字节带宽主导）",
      "逻辑行长 inner ≥ C，chunk 循环次数足够多以摊销 slab 装载",
      "SIMT 偏移构建的 UB 触碰面满足单 8KB 对齐页约束（见 common 卡 simt-ub-8kb-page-and-thread-cliffs）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "12/14/15（xDim=7/13/7，bf16/fp16/fp32；control 8 例含 r1-r3 已优化 case）",
      "commit": "9fc54d68bc3b83437c7b7ece6d259d5f1b28d8cc",
      "decision_sha256_ref": "7ecd376a68b8fe5220df0e9e8d4d39bc25dca8e29370ca5b7adfce7e4c86190c",
      "note": "probe 4 次迭代发现 4 个工具链硬事实（线程悬崖/8KB 对齐页/srcStride 字段上限/V→V barrier），均已内化为卡内 constraints 与 common 卡",
      "operator_class": "index-gather",
      "precision": "20/20 PASS（verify --cases all）",
      "round": 4,
      "run_id": "<run-id>",
      "speedup": "2.78x / 3.07x / 2.49x（incremental total 1.0569，control 最差 0.9685）",
      "status": "accepted"
    },
    {
      "comparison_sha256": "80f324f7158633737e05f8708844af41a35d45ac5b2be2b4f94df9f37dcb7fbd",
      "decision_sha256": "7ecd376a68b8fe5220df0e9e8d4d39bc25dca8e29370ca5b7adfce7e4c86190c",
      "operator_class": "index-gather",
      "performance_sha256": "07e8d6f6985e87d3dd67aef99fe002f1f543ba71b9393f9a1faba1cd9e0c75c7",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "e8fd106c50bc0e04e1fc5a1ef3c90fed87d852236d00cd22814ad0971e3d553d",
      "verify_sha256": "586ab13f70749a00a5f2c1df68342fd05131f248c4ebcbbf2b244a34c219fdd0"
    }
  ],
  "feature_signature": {
    "bottleneck": "per-element scattered GM request rate (not byte bandwidth)",
    "primitives": [
      "DataCopyPad per-row single-block slab load",
      "TQue<VECIN,2> double buffer",
      "__simt_vf__ offset build",
      "PipeBarrier<PIPE_V>",
      "__simd_vf__ Reg::Gather slices"
    ],
    "route": "vector-index-gather-per-element-scatter"
  },
  "generality": "op_class",
  "id": "GATHER-t2-small-xdim-slab-bulk-mte2-simd-gather",
  "implementation_steps": [
    "由 op_summary 中位判别瓶颈：每元素/核成本对 C 作图无趋势 + 少核每核速率高于满核 + 聚合吞吐窄带 ⇒ 散射请求主导",
    "host 向量分支内解析求解 C：自 dtype 对齐上界向下取首个满足（C·dtype)%32==0、SIMT 偏移足迹 off+2·idx+2·y≤8192 且全在首个 8KB 对齐页、slab 双缓冲+既有队列 ≤ UB、xDim·C·dtype≤预算、xDim·C<偏移类型上限",
    "命中时以 C 作为 chunk 宽重算 chunk 数/切分（公式不变），追加运行时 tiling 标志字段（不动 tiling key）",
    "kernel 新增 slab TQue<VECIN,2> 与偏移 TBuf（条件 InitBuffer）；chunk 循环内增量 m0 派生列窗，逐行单块拷贝装载 slab",
    "SIMT 构建偏移 → PipeBarrier<PIPE_V> → SIMD 切片 Reg::Gather → 输出队列；跨 inner 边界拆子块，失对齐子块回退原路径",
    "全 case 精度验证 + 命中/非命中 case 的管线形态与多核数不变性核验"
  ],
  "intent": "消除 SIMT 逐元素 GM 散射读的请求率/共享通路瓶颈（判别特征：每元素成本与 chunk 宽 C 无关；少核时每核速率更高；聚合吞吐窄带远低于字节带宽包络）。",
  "mechanism": "host 在向量路由分支用纯形状解析门求解列窗宽 C（对齐/足迹/UB 预算/xDim·C·dtype 上限），命中时把该值作为 chunk 宽下发（chunk 数与切分公式同式重算，多核切分机制不动）；kernel 每 chunk 以增量 m0 派生列窗，逐行单块 DataCopyPad 装载 slab 进 TQue<VECIN,2>，SIMT 偏移构建后 PipeBarrier<PIPE_V>，SIMD 切片 Reg::Gather 收集并 CopyOut；跨 inner 边界 chunk 拆 ≤2 子块，失 32B 对齐子块回退原逐元素路径；门 false 的 case tiling 逐字段一致。",
  "name": "小 xDim 索引 gather 列窗 slab 整块 MTE2 + SIMD 向量 Gather 替换逐元素 SIMT 散射读",
  "operator_class": "index-gather",
  "operator_scope": "索引 gather 类（T2 向量路由、x 源逐元素散射读为瓶颈、索引前缀维 xDim 小、逻辑行长 inner 远大于单 chunk 宽）",
  "principle": "每输出元素一次离散 GM 请求的代价由请求率与共享通路延迟主导，与搬运字节数无关；把 N 个离散请求合并为 xDim 个连续块搬运后，每元素字节成本降到 dtype×xDim^-1 量级，且消费端用已验证的 UB 内 SIMD Gather 速率完成收集。",
  "related_anti_patterns": [],
  "risks": [
    "MTE2 聚合饱和：满核并发 slab 搬运逼近带宽包络后兑现被锁死在包络之上（非回归，是天花板形态）",
    "优化后 case 深入微核噪声区（<50us）：收益按物理量级记录，采集协议见 microkernel-noise-floor-measurement-gate",
    "共享 host tiling 代码：门写错即全局回归，非目标 case 必须逐字段一致 + 全量精度兜底",
    "VF 新代码非既有逐字移植时，限定为已验证原语组合（LoadAlign/Gather/StoreAlign + 切片循环）"
  ],
  "slug": "t2-small-xdim-slab-bulk-mte2-simd-gather",
  "summary": "当索引 gather 的每输出元素一次 GM 散射请求是成本中心时，把 x 源的读取改为按 chunk 列窗整块搬运：每 chunk 将 xDim 个源行在当前列窗 [m0,m0+C) 的窗口 bulk MTE2 进双缓冲 TQue（slab），SIMT 构建偏移 off[p]=idx[p]·C+p（不取模），SIMD Reg::Gather 从 UB slab 向量收集输出，逐元素 GM 散射请求归零。",
  "verification": {
    "correctness": [
      "全 case（含全部非命中 case）accuracy pass；命中 case 的正确性按构造与 idx 数据值无关（slab 无条件装载全部源行窗）"
    ],
    "performance": [
      "命中 case op_summary 由 V 散射主导转为 MTE2 主导、Block Num 与切分机制不变；非命中 control 中位带内（±5%）且结构逐位一致"
    ],
    "rollback_signals": [
      "任一 case MISMATCH/507035/设备错误；命中 case 中位改善 <1.1x（MTE2 饱和或顺序假设失败）；control 回归超门且不满足噪声地板判据"
    ]
  }
}
-->

# 性能优化策略：小 xDim 索引 gather 列窗 slab 整块 MTE2 + SIMD 向量 Gather 替换逐元素 SIMT 散射读

单一优化点：当索引 gather 的每输出元素一次 GM 散射请求是成本中心时，把 x 源的读取改为按 chunk 列窗整块搬运：每 chunk 将 xDim 个源行在当前列窗 [m0,m0+C) 的窗口 bulk MTE2 进双缓冲 TQue（slab），SIMT 构建偏移 off[p]=idx[p]·C+p（不取模），SIMD Reg::Gather 从 UB slab 向量收集输出，逐元素 GM 散射请求归零。

## 1. 原理

每输出元素一次离散 GM 请求的代价由请求率与共享通路延迟主导，与搬运字节数无关；把 N 个离散请求合并为 xDim 个连续块搬运后，每元素字节成本降到 dtype×xDim^-1 量级，且消费端用已验证的 UB 内 SIMD Gather 速率完成收集。

实现机制：host 在向量路由分支用纯形状解析门求解列窗宽 C（对齐/足迹/UB 预算/xDim·C·dtype 上限），命中时把该值作为 chunk 宽下发（chunk 数与切分公式同式重算，多核切分机制不动）；kernel 每 chunk 以增量 m0 派生列窗，逐行单块 DataCopyPad 装载 slab 进 TQue<VECIN,2>，SIMT 偏移构建后 PipeBarrier<PIPE_V>，SIMD 切片 Reg::Gather 收集并 CopyOut；跨 inner 边界 chunk 拆 ≤2 子块，失 32B 对齐子块回退原逐元素路径；门 false 的 case tiling 逐字段一致。

## 2. 性能问题模式

- 优化目标：消除 SIMT 逐元素 GM 散射读的请求率/共享通路瓶颈（判别特征：每元素成本与 chunk 宽 C 无关；少核时每核速率更高；聚合吞吐窄带远低于字节带宽包络）。
- 适用数据流：索引 gather 类（T2 向量路由、x 源逐元素散射读为瓶颈、索引前缀维 xDim 小、逻辑行长 inner 远大于单 chunk 宽）
- Feature signature：`{"bottleneck": "per-element scattered GM request rate (not byte bandwidth)", "primitives": ["DataCopyPad per-row single-block slab load", "TQue<VECIN,2> double buffer", "__simt_vf__ offset build", "PipeBarrier<PIPE_V>", "__simd_vf__ Reg::Gather slices"], "route": "vector-index-gather-per-element-scatter"}`

## 3. 正确性红线

- MTE2 聚合饱和：满核并发 slab 搬运逼近带宽包络后兑现被锁死在包络之上（非回归，是天花板形态）
- 优化后 case 深入微核噪声区（<50us）：收益按物理量级记录，采集协议见 microkernel-noise-floor-measurement-gate
- 共享 host tiling 代码：门写错即全局回归，非目标 case 必须逐字段一致 + 全量精度兜底
- VF 新代码非既有逐字移植时，限定为已验证原语组合（LoadAlign/Gather/StoreAlign + 切片循环）

资源与硬件约束：

- 2D 多块 DataCopyPad 的 srcStride 字段在大 stride（实测 ~579KB）溢出产生错数据；小 xDim 下用逐行单块拷贝规避（描述符成本可忽略），见 common 卡 2d-datacopy-ext-stride-field-limit
- 同一 Compute 内 SIMT 偏移构建与 SIMD 消费之间必须显式 PipeBarrier<PIPE_V>（V→V 顺序非隐式），见 common 卡 vf-simd-simt-sequential-ordering-barrier
- slab 必须经 TQue EnQue/DeQue 承载 MTE2→V 同步；不得用 TBuf 裸窗口跨流水读取
- host 门为纯形状解析（不读张量数据值），非目标 case 必须逐字段一致

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- 索引前缀维 xDim 足够小，使 xDim·C·dtype 的 slab 窗在 UB 预算内且块对齐可满足
- 每个输出元素的 x 读取当前为逐元素离散 GM 访问（散射请求主导而非字节带宽主导）
- 逻辑行长 inner ≥ C，chunk 循环次数足够多以摊销 slab 装载
- SIMT 偏移构建的 UB 触碰面满足单 8KB 对齐页约束（见 common 卡 simt-ub-8kb-page-and-thread-cliffs）

不适用：

- xDim 大到 slab 超出 UB 预算或 MTE2 聚合带宽饱和成为新瓶颈（兑现后被 MTE2 包络锁死，继续提速需攻击 MTE2 侧）
- 索引 gather 语义无法表达为 y[p]=x[rowBase+idx[p]·inner+m0+p] 的列窗恒等式（跨行 trail 不匹配等）
- 瓶颈为字节带宽或每 chunk 固定开销（加大 C 或提升线程宽的天花板 ~1.1x，本机制不适用）

## 5. 实施步骤

1. 由 op_summary 中位判别瓶颈：每元素/核成本对 C 作图无趋势 + 少核每核速率高于满核 + 聚合吞吐窄带 ⇒ 散射请求主导
2. host 向量分支内解析求解 C：自 dtype 对齐上界向下取首个满足（C·dtype)%32==0、SIMT 偏移足迹 off+2·idx+2·y≤8192 且全在首个 8KB 对齐页、slab 双缓冲+既有队列 ≤ UB、xDim·C·dtype≤预算、xDim·C<偏移类型上限
3. 命中时以 C 作为 chunk 宽重算 chunk 数/切分（公式不变），追加运行时 tiling 标志字段（不动 tiling key）
4. kernel 新增 slab TQue<VECIN,2> 与偏移 TBuf（条件 InitBuffer）；chunk 循环内增量 m0 派生列窗，逐行单块拷贝装载 slab
5. SIMT 构建偏移 → PipeBarrier<PIPE_V> → SIMD 切片 Reg::Gather → 输出队列；跨 inner 边界拆子块，失对齐子块回退原路径
6. 全 case 精度验证 + 命中/非命中 case 的管线形态与多核数不变性核验

## 6. LLM 前置问题

- 目标实现是否满足：索引前缀维 xDim 足够小，使 xDim·C·dtype 的 slab 窗在 UB 预算内且块对齐可满足？
- 目标实现是否满足：每个输出元素的 x 读取当前为逐元素离散 GM 访问（散射请求主导而非字节带宽主导）？
- 目标实现是否满足：逻辑行长 inner ≥ C，chunk 循环次数足够多以摊销 slab 装载？
- 是否命中排除条件：xDim 大到 slab 超出 UB 预算或 MTE2 聚合带宽饱和成为新瓶颈（兑现后被 MTE2 包络锁死，继续提速需攻击 MTE2 侧）？

## 7. 验收标准

正确性：

- 全 case（含全部非命中 case）accuracy pass；命中 case 的正确性按构造与 idx 数据值无关（slab 无条件装载全部源行窗）

性能：

- 命中 case op_summary 由 V 散射主导转为 MTE2 主导、Block Num 与切分机制不变；非命中 control 中位带内（±5%）且结构逐位一致

回滚信号：

- 任一 case MISMATCH/507035/设备错误；命中 case 中位改善 <1.1x（MTE2 饱和或顺序假设失败）；control 回归超门且不满足噪声地板判据

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gather-20260831_113139-a1e0e0（round=4, status=accepted, case=12/14/15（xDim=7/13/7，bf16/fp16/fp32；control 8 例含 r1-r3 已优化 case）, speedup=2.78x / 3.07x / 2.49x（incremental total 1.0569，control 最差 0.9685））
- gather-20260831_113139-a1e0e0（round=4, status=accepted）

## 检索卡（短卡）

动作：把逐元素 GM 散射读改为按 chunk 列窗整块 MTE2 搬入双缓冲 slab，SIMT 构偏移后由 SIMD Gather 收集。
适用：xDim 足够小使 xDim·C·dtype 在 UB 预算内；散射请求主导；inner>=C。
限制：srcStride（~579KB）溢出须逐行单块拷贝；须显式 PipeBarrier<PIPE_V>；slab 须经 TQue 承载同步。
范围：T2 向量路由索引 gather 的列窗读入与收集
检索词：DataCopyPad、TQue<VECIN,2>、__simt_vf__、PipeBarrier<PIPE_V>、Reg::Gather
机会：每元素一次离散 GM 请求，瓶颈在请求率而非搬运字节数
代价：满核并发 slab 搬运逼近 MTE2 包络后兑现被锁死
