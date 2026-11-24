---
type: Optimization
title: decode 分支 wsS fp32 高精度回退（双量化误差陷阱）
description: 将 decode 的 S<=16 分支中 wsS staging 从 2B 量化表示回退为 fp32。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/07-decode-wss-fp32-precision.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 精度修复策略：decode 分支 wsS fp32 高精度回退（双量化误差陷阱）

> **单一优化点：** decode 分支（S<=16）把 wsS staging 从 2B（03 号量化）运行时
> 回退到 fp32——通过 TilingData 新增 `wsSHighPrec` 标志，MM1 Fixpipe 跳过
> quantPre 直写 fp32、Vec1 直拷；prefill 分支保持 2B 不动（带宽代价 +35%
> 不可接受）。

> **已验证锚点：** cann-bench gqa_15（fp16 B60 S1 Skv1024 Nq32 Nkv8 D256 decode）
> 小值域错误 7→**0**（3 次复测稳定；修复前评测 20 case 中 1 失败）；全量 20/20
> allclose；bench 子集 0.1631→0.1676ms（decode 流量 +21% 但子集影响 <3%，
> 噪声内）。根因数值仿真精确定位：wsS16+wsP16 双量化→7 错，关任一→0 错。

---

## 1. 问题原理

### 1.1 双量化误差放大链

decode 长序列（S_kv=1024 项求和）+ 输出落在小值域（|y|<2^-11）时：

```
scores(fp32 Mmad) --量化--> wsS(fp16) --softmax fp32--> P --量化--> wsP(fp16)
                                                        ↓
                              MM2: Σ_{j=1..1024} cast16(P_j) × V_j (fp32 累加)
                                                        ↓
                              Vec2: O / sum(Σ e_j, fp32 精确和) → cast16(y)
```

- 分子（O）用**量化后的 P**求和，分母（sum）用**未量化的 e**求和——两级 fp16
  量化（每级相对误差 2^-11）在 1024 项求和中累积，最终 y 的绝对误差可达
  1.5×2^-16，恰超 cann-bench 小值域兜底线（|diff|>2^-16 计错，容错 ≤2 个）。
- **单级量化不超差**：只关 wsS 或只关 wsP 都是 0 错——误差是两级联合效应，
  精度回归若只测均值 allclose 很可能漏检（本例 allclose 一直全过，cann-bench
  小值域口径才抓到）。

### 1.2 修复机制

| 层 | 改动 |
|---|---|
| host | `wsSHighPrec = isDecodeBranch ? 1 : 0`；decode 时 wsSSize 按 4B 算（prefill 仍 2B） |
| kernel 视图 | 同一 wsS 内存绑双视图：`wsSGm_`（WsSElem=QType）+ `wsSFloatGm_`（float），按标志运行时选 |
| MM1 | `if (wsSHighPrec==0) fixParams.quantPre=…` + Fixpipe 目的按标志选 fp32 视图 |
| Vec1 | 高精度分支 DataCopy fp32 直拷（无量化往返）；2B 分支原样 |

## 2. 正确性红线

- **decode 恒 fp32**：S<=16 分支不得因任何带宽优化回 2B（除非重做双量化误差
  仿真证明新链路安全）。
- **sum 与 P 的同源性**：本修复保留 sum=Σe(fp32)（精确）而 P 仍 2B——单级
  量化已证安全；若未来把 P 也升 fp32（p_direct_mm2 顺带），sum 口径不变即可。
- 回归必须含**小值域口径**（|golden|<2^-11 且 |diff|>2^-16 计数 ≤2），
  allclose 均值口径对本类问题不敏感。

## 3. 泛化条件

- **适用（问题模式）**：中间量多级 dtype 压缩 + 长轴求和 + 输出近零（相消）
  的组合——softmax 归一化前的未归一中间量、attention 输出层都常见。
- **修复模式适用**：分支敏感（decode/prefill）时按分支选精度而非全局回退，
  保住大流量分支的带宽收益。
- **不适用**：单级量化即超差的场景（需查 sum 同源或升 DTYPE 计算）。

## 4. 实施步骤

1. 数值仿真定位：CPU 复刻计算链（含每级 cast），枚举量化组合
   {wsS16,wsP16}×on/off，与 NPU 实测错误计数对齐（本例双开=7 错完全吻合）。
2. TilingData 加标志（末尾追加，字段序三处一致）；host 分支算 wsSSize。
3. kernel 双视图 + Fixpipe/Vec1 运行时分支（quantPre 本就是运行时字段）。
4. 全量 allclose + cann-bench 小值域口径 + bench 确认分支带宽代价可承受。

## 5. LLM 前置问题

- 计算链上有几级 dtype 压缩？各级相对误差多少？求和项数（长轴）多大？
- 输出是否会落在小值域（|golden| 接近量化步长）？分母（归一化和）与分子的
  量化是否同源？
- 能否按分支隔离（只回退敏感分支）而非全局升精度？

## 6. 风险与回退

- 回退：`wsSHighPrec` 恒 0（回纯 2B，精度问题复现）或恒 1（全局 fp32，带宽
  回退 ~35%）——两个方向都可用作 A/B 验证。
- 双视图绑定需 host/kernel 的 wsSSize 口径互为倒数（元素数=字节数/元素宽），
  错配表现是 Vec1 读越界（快速失败）。

## 7. 验收标准

- 精度：cann-bench 小值域错误计数 0（或 ≤2 容错）× 3 次复测；全量 allclose。
- 性能：敏感分支带宽增幅 <25%（本例 decode +21% 流量、子集时延影响 <3%）；
  大流量分支零改动。
- 证据：数值仿真组合矩阵与 NPU 实测错误计数一致（根因闭环）。

## 检索卡（短卡）

动作：将 decode 的 S<=16 分支中 wsS staging 从 2B 量化表示回退为 fp32。
适用：中间量多级 dtype 压缩、长轴求和且输出近零相消。
限制：S<=16 的 decode 分支必须保持 fp32，不得为带宽优化退回 2B。
范围：decode 的 S<=16 分支及 wsS staging。
检索词：wsS、fp32、2B、双量化误差、softmax、长轴求和。
机会：长序列求和且输出落入近零小值域。
