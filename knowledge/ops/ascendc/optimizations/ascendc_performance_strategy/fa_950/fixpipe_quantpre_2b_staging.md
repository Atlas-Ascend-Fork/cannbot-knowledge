---
type: Optimization
title: MM1 Fixpipe 随路量化 2B staging（wsS fp32→2B）
description: 按 QType 启用 Fixpipe quantPre，将 L0C FP32 随路量化后以 GM 2B 落盘。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/03-fixpipe-quantpre-2b-staging.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：MM1 Fixpipe 随路量化 2B staging（wsS fp32→2B）

> **单一优化点：** MM1 的 Fixpipe 落盘通路启用 `quantPre=F322F16/F322BF16`
> 随路量化，把 GM 中转区 wsS 从 fp32(4B) 降为 QType(2B) staging——量化在
> FIX 通路内完成，**零额外向量指令、零额外搬运**；Vec1 读取端配 2B 队列拷贝 +
> `Cast(CAST_NONE)` bit 精确unpack。

> **已验证锚点：** GQA bench 子集 0.1878→0.1652ms（-12%）；case8（fp16 B4S1024
> long prefill causal）535→398us（-25%）。20/20 allclose（fp16 1e-3/bf16 1e-2）。
> decode 分支的精度回退见 07 号（本策略在 decode 域必须让位于 fp32）。

---

## 1. 优化原理

### 1.1 性能问题模式

AIC→AIV 的 scores 中转区 wsS 以 fp32 落盘：每任务 wsS 写+读 =
`2×mBase×s2Base×4B`（mBase=512/s2Base=512 时达 2MB/任务），占 prefill 任务
总 GM 流量 ~35%；而 softmax 输入只需求 scores 达 fp16/bf16 精度（后续 P 还要
再降 2B），fp32 中转是纯带宽浪费。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| Fixpipe quantPre | `FixpipeParamsV220.quantPre = F322F16/F322BF16`（按 QType）：L0C fp32 → GM 2B 在 FIX 通路内随路量化，无 cbufWorkspace/deqScalar，INF_NAN 支持 |
| MTE 搬运 | wsS 字节减半 → MM1 落盘与 Vec1 取回带宽各 -50% |
| Vector Cast | Vec1 侧 2B 元素进 UB 队列后 `Cast(sUb, sHalfUb, CAST_NONE, n)` —— 低精度→fp32 一律 CAST_NONE（bit 精确扩展，零新增舍入；与 fp32→2B 的 CAST_ROUND 方向严格区分） |

### 1.3 核心改动点

- `op_kernel/gqa_common.h`：`constexpr uint32_t GQA_WS_S_BYTES = 2`（host
  `optiling` 侧同名常量成对镜像，wsSSize 公式同源换算）。
- `op_kernel/gqa_cube.h`（MM1 Fixpipe 位点，prefill 与 decode 折叠块两处）：
  `if constexpr (GQA_WS_S_BYTES==2) fixParams.quantPre = is_same<QType,bfloat16_t>? F322BF16:F322F16;`
- `op_kernel/gqa_vec.h`（Vec1 读取端）：`sInQue_` 2B 队列（`GQA_S_HALF_QUEUE_BUF_SIZE`
  = 8192 元素×2B 恰满单槽）+ CAST_NONE unpack；wsS 视图 `WsSElem = conditional<2,QType,float>`。
- host `gqa_tiling.cpp`：`wsSSize = RING_SLOTS×mBase×s2Base×GQA_WS_S_BYTES`。

## 2. 正确性红线

- **scale 唯一作用点不变**：softmax 的 scale 仍只乘在 Vec1 入口（I9 契约），
  禁止折入 Fixpipe 量化（quantPre 是纯 dtype 转换，非带 scale 量化）。
- 量化饱和域：raw score |s| 必须在 QType 域内（fp16 65504；评测域 |s|≤D≤256
  恒满足——上线前按最大 D×|q||k| 上界核验）。
- **decode 分支禁用**（→07 号）：wsS 2B 与 wsP 2B 双量化误差在长 S_kv 求和 +
  小值域输出场景联合超差（cann-bench gqa_15 实测 7 点 >2^-16）。本策略落位时
  必须与 07 号的 `wsSHighPrec` 运行时标志共存：decode 走 fp32 视图直拷，prefill
  走 2B 量化。

## 3. 泛化条件

- **适用**：AIC(cube)→GM→AIV(vector) 的中间量中转，且下游消费精度 ≤ QType
  （softmax 类、elementwise 类中间量）；prefill/大 S 场景（带宽占比高）。
- **不适用**：中间量需 fp32 精度链路的场景（累加和/归一化分母相关的
  未归一中间量，见 07 号的双量化陷阱）；带宽占比 <10% 的场景收益不显。

## 4. 实施步骤

1. 定义 `GQA_WS_S_BYTES` 常量（host/kernel 成对）+ `WsSElem` conditional 视图。
2. MM1 全部 Fixpipe 位点加 quantPre（quantPre 是运行时字段，可配 `if constexpr`）。
3. Vec1 读取端 2B 队列 + CAST_NONE unpack；UB 预算补 sInQue 双缓冲。
4. host wsSSize 公式同步 + workspace 总量核验。
5. 全量精度 + cann-bench 小值域口径回归（防 07 号问题在 prefill 域复发）。

## 5. LLM 前置问题

- 中间量的 GM 读写占总流量比例（profiler 可估）？下游消费精度是否 ≤QType？
- 中间量绝对值域是否在 QType 表示范围内（防饱和）？
- 是否存在与第二级量化（如 wsP）的**联合量化误差**放大路径（长求和+小值域输出）？

## 6. 风险与回退

- 回退：`GQA_WS_S_BYTES` 翻 4（host/kernel 成对同翻），FIX 无 quantPre 即回
  fp32 现网形态。
- 最大风险是 §2 的双量化陷阱——精度回归必须包含小值域口径（cann-bench 的
  |golden|<2^-11 且 |diff|>2^-16 计数），allclose 均值口径可能漏检。

## 7. 验收标准

- 精度：20 case allclose + cann-bench 小值域兜底计数无恶化（对照 07 号）。
- 性能：prefill 大 case ≥8%（本锚点 case8 -25%）；decode case 噪声内。
- 带宽旁证：profiler MM1 落盘/Vec1 取回字节数减半。

## 检索卡（短卡）

动作：按 QType 启用 Fixpipe quantPre，将 L0C FP32 随路量化后以 GM 2B 落盘。
适用：适用于 AIC→GM→AIV 中转且下游所需精度不高于 QType。
限制：softmax scale 只能在 Vec1 入口作用，不得折入 Fixpipe 量化。
范围：MM1 Fixpipe 的 wsS 落盘通路。
检索词：Fixpipe quantPre、F322F16、F322BF16、wsS、2B staging。
机会：scores 中转区 wsS 仍以 FP32 写入并由下游读取。
代价：主要面向带宽占比较高的 prefill 或大 S 场景。
