---
type: Optimization
title: "X9: Deferred Scaling — 反量化仿射结构的代数重排（延迟缩放）"
description: "反量化 decode 中 per-token/per-row 的 Muls/Adds 若只被归约或加权累加消费，可利用分配律把缩放推迟到归约后的低维量上，消掉大量 D-wide 向量指令。"
tags:
  - task.optimization
  - topic.attention
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T15:50:00Z"
platforms:
  - a2
---
# Strategy X9: Deferred Scaling — 反量化仿射结构的代数重排（延迟缩放）

## 核心思路

反量化 decode 类 kernel 的典型结构是：

```
对 nTok*D 个元素逐一施加 per-token 缩放/偏移（D-wide Muls/Adds × nTok）
→ 然后马上被归约（ReduceSum / 加权累加）消费成低维量
```

P94/P95 能把包裹这些向量指令的**标量外壳**向量化，但向量指令本身的数量
（2~3 × nTok 条 D-wide op）并未减少。本策略更进一步：**利用反量化仿射/
乘性结构的分配律，把 per-element 缩放推迟到归约之后的低维量上做**，
在 fp32 等价语义下直接消掉指令：

- **K-fold（乘性）**：`score_t = s_t * sum(q · c_t)` —— K 块全程保持在
  未缩放单位（centroid/idx），per-token 因子 `s_t` 乘到 ReduceSum 之后的
  分数上（1 条 tb-lane Mul），而不是乘到全部 nTok*D 个 K 元素上
  （nTok 条 D-wide Muls）。
- **V-fold（仿射）**：`sum_t p_t*(idx_t*vs_t + vz_t) = sum_t (p_t*vs_t)*idx_t + (sum_t p_t*vz_t)` ——
  V 块保持原始 index 单位，2*nTok 条 per-token D-wide Muls/Adds 折叠为
  复合权重 `w_t = p_t*vs_t` 的 Axpy + 1 条 D-wide Adds（`sumPvz` 修正项）。
- **归约后低维量的派生计算也留在向量域**：如 softmax 权重 `w = p*vs`、
  `lAdd = ReduceSum(p)`、`sumPvz = ReduceSum(p*vz)` 全部走 vector pipe；
  Newton rsqrt 精化在 tb-lane 向量上执行（乘 2^-1 与 fp 舍入可交换，
  bit-exact），消除标量 GetValue/FLOP 链。

## 适用场景

- **算子类型**：量化 KV cache decode attention、dequant+reduce 融合、
  带 per-row scale/zero 的批量反量化。
- **触发条件**（需同时满足）：
  1. profiling 为 scalar-issue-bound/发射受限（`aiv_scalar_ratio` 高、`aiv_mte2_ratio` 低），瓶颈是指令数而非带宽；
  2. 存在 per-token/per-row 的 `Muls(x[t*D], s_t)` / `Adds(x[t*D], z_t)` 循环，
     且其结果**只被归约或加权累加消费**（不被逐元素写出）；
  3. 缩放量与数据量满足仿射/乘性关系（`y = idx*s + z`、`y = s*c`）。

## 改造范式

### 范式 A：乘性缩放延迟（K-fold）

```cpp
// 基线：先缩放全部元素，再归约
for (t) { Muls(kBlk[t*D], kBlk[t*D], sArr[t], D); }   // nTok 条 D-wide
for (t) { Mul(prod[t*D], q, kBlk[t*D], D); ReduceSum(score[t], ...); }

// 改造：先归约（未缩放单位），再缩放低维结果
for (t) { Mul(prod[t*D], q, kBlk[t*D], D); ReduceSum(scoreRaw[t], ...); }
Mul(score, scoreRaw, sVec, tb);                        // 1 条 tb-lane
```

### 范式 B：仿射分解（V-fold）

```cpp
// 基线：逐 token 反量化 + 逐 token 加权
for (t) { Muls(vBlk[t*D], vBlk[t*D], vsArr[t], D);
          Adds(vBlk[t*D], vBlk[t*D], vzArr[t], D); }    // 2*nTok 条 D-wide
for (t) { Axpy(acc, vBlk[t*D], pArr[t], D); }

// 改造：sum_t p_t*(idx*vs+vz) = sum_t (p_t*vs)*idx + sum_t p_t*vz
Mul(wVec, pVec, vsVec, tb);                            // 复合权重（tb-lane）
for (t) { Axpy(acc, vIdxBlk[t*D], w_t, D); }           // V 保持 idx 单位
Adds(acc, acc, sumPvz, D);                             // 1 条修正项
```

### 范式 C：派生量全向量域（消除 V→S 往返）

`FetchSlotScalars` 类函数把 per-token fp16 标量 Gather+Cast 到 UB 后，
**不要** GetValue 回标量数组再喂给向量指令——让数据留在 UB 直接供
vector pipe 消费（配合块级 broadcast 展开）。热路径每 chunk
可消除 3*tb 次 V→S round trip；仅尾 chunk（stale lanes）按需现取。

## 关键前提与陷阱

⚠️ **fp32 等价性必须逐条论证**：分配律在 fp32 下对"缩放-归约"次序交换
通常是安全的（缩放在归约外只改变一次舍入位置），但需实测 rtol/atol +
全 case 验证；Newton rsqrt 类精化需确认每步与舍入可交换（如 ×2^-1）。

⚠️ **stale lanes 不能参与归约**：尾 chunk（nTok < tb）的 stale lanes 经
Exp 后是非零有限值，范式 B/C 的向量化归约只能在**满 chunk** 使用，
尾 chunk 保留标量路径（按 `nTok == tb_` 分派）。

⚠️ **负证据：勿用 Gather/LUT 路线替代本方案**。A2 的 UB Gather 是
（vector pipe 时间膨胀超过省下的发射槽，通常不划算）。本策略保持块算术、只做
代数重排，不引入 gather。（与 P100 的适用边界互补：P100 针对
SetValue/GetValue 解交织，不针对廉价块算术。）

⚠️ **不要动跨 chunk 的 online-softmax 标量状态**（`mPrev`/`lPrev`），
只向量化 chunk 内的派生量。

⚠️ **收益强依赖 splitKv 结构，须逐 case 验证回退条件**：当派生量的机械成本超过 GetValue 消除收益时应回退；应用前按 chunks/unit 评估派生量计算的实际消除率。

## 实现步骤

1. 标记所有 per-token/per-row 缩放点（`Muls/Adds(x[t*D], s_t)`）；
2. 沿数据流确认其唯一消费者是归约/加权累加；
3. 按乘性（A）或仿射（B）写出代数等价式，重排缩放位置；
4. 归约后的低维派生计算（softmax 权重、rsqrt 精化）改 tb-lane 向量 op；
5. 满/尾 chunk 分派：满 chunk 走向量化路径，尾 chunk 保留标量路径；
6. 全 case 精度验证（多轮，关注归约次序改变带来的尾差）。

## 与现有策略的关系

- **P94/P95**：标量归约/逐元素 → 向量 API（指令数不变）；本策略在此基础上
  **减少向量指令本身**。二者串联使用：先本策略代数重排消指令，残余标量
  外壳再按 P94/P95 处理。本策略处理的是"已经是向量 API
  但数量可代数消减"的场景。
- **P100**：Gather 替换逐元素读写；本策略的负证据限定了 P100 类路线在
  "廉价块算术 + scalar-issue-bound"场景下会回退。
- **X4**：Host 预计算常量表；与本策略正交，可叠加。

## 与其它策略的正交性

- 可与 host 常量表预计算、TB 预算化、reduce 融合等策略叠加；叠加时需把新增 buffer 计入 UB 预算，超预算时回退到较小的 TB。

## 代码搜索关键词

```bash
# per-token 缩放后接归约（范式 A/B 候选）
grep -nE "for.*\{[^}]*Muls\s*\([^,]*\[t\s*\*" op_kernel/*.cpp

# 反量化 scale+zero 循环（范式 B 候选）
grep -nE "Muls.*vs|Adds.*vz|scale.*zero" op_kernel/*.cpp

# Gather+Cast 后 GetValue 回读标量数组（范式 C 候选）
grep -nE "GetValue\(t\)|GetValue\(16|GetValue\(32" op_kernel/*.cpp
```

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
