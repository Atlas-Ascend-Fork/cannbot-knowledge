---
type: Optimization
title: bit-mask popcount 向量计数 + Gather 逆索引（标量直方图路径向量化）
description: 将标量计数改为Duplicate→Compare位掩码→字节popcount累加直方图，并向量化查表scatter。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-bitmask-popcount-gather-vectorized-histogram.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：bit-mask popcount 向量计数 + Gather 逆索引（标量直方图路径向量化）

> 单一优化点：值域直方图/查表类 kernel 的 **O(n) 标量循环三件套**（min/max、计数、查表
> scatter）中，后两者可向量化：per-value 计数用「Duplicate 广播值 + Compare 产 bit-packed
> mask + 标量 popcount(字节)」（(R+1)×n/8 次字节读代替 n×3 次标量 UB 访问），查表逆索引
> 用「Adds 产桶号 + Muls×4 产字节偏移 + Gather 查 rank 表 + Cast 宽化」。N=4096、R=15
> 实测净 kernel 300→180us。

适用于"少量桶 × 大量元素"的计数/映射类 kernel（直方图 unique、bincount、小值域编码）。

---

## 1. 原理

- 每次标量 UB 访问实测 ~15 cycles（依赖链 + 地址计算），O(n) 标量循环是主要成本。
- **Compare 的 bit-packed mask 是特性不是缺陷**：8 个比较结果打包 1 字节，popcount(字节)
   直接得到桶计数——读 n/8 字节代替 n 次标量读。
- Gather（A2 支持 int32）按字节偏移查 rank 表一次产出全部逆索引，Cast int32→int64 宽化。

## 2. 性能问题模式

- SCALAR pipe ~100%、kernel 时间 ∝ n、每迭代 2-3 次标量 UB 访问。
- 桶数少（R≤16）、n 大、桶内重复高。

## 3. 正确性红线（dav_c220 实战陷阱清单，全部实际踩过）

1. **Compares 的标量操作数只支持 half**——int32 值必须先 Duplicate 广播成 tensor 再
   Compare(tensor, tensor)。
2. **原地向量运算触发 vector core exception**（MTE bus error）——Adds/Muls 的 dst 必须
   ≠ src，用三数组接力（桶号→idx1、偏移→key0、结果→key1，各自等源用完）。
3. **Vector 写 → MTE3 读必须显式 `TQueSync<PIPE_V, PIPE_MTE3>`**（SetFlag/WaitFlag）——
   否则 DataCopyPad 抢先读未写完的 UB，输出全垃圾。枚举名是全局 `PIPE_V`/`PIPE_MTE3`
   （不在 AscendC:: 内）。
4. **Compare/Duplicate 的 count 版要求 n 为 64 元素(256B)整数倍**——n%64!=0 时尾部
   mask/计数错（n=264/288 实测 counts 错），门控必须含 `(n%64)==0`。
5. Gather 的 srcOffset 单位是**字节**（桶号要 Muls×4）；读出的值就是表值（表存 rank
   本身，不要再缩放）；Gather 的 dst/src/off 三者不能与任何在飞访问重叠。
6. int64 无 Subs（3510 专属）——用 `Adds(dst, src, -scalar, n)`；dst/src 必须同类型。

## 4. 泛化条件

- **适用**：桶数 R≤~16（(R+1)×n/8 次读 < n×3 次标量访问的盈亏平衡点附近）、int32、n≥256 且
  n%64==0。
- **不适用**：桶数多（popcount 侧成本 ∝ R）、int64（Gather 偏移 32bit、Adds 同型约束，可先
  Cast 降宽但增加一遍）；min/max 仍需标量（A2 的 ReduceMax 不支持 int32，f32 中转破坏
  >2^24 值域）。

## 5. 实施步骤

1. 标量 min/max → range 判定（无符号！）。
2. 计数循环：Duplicate(cmpVal) → Compare(mask) → popcount(字节) 累加 → hist[v]。
3. 压缩：非零桶写 vals/counts，rank 原地覆写 hist。
4. 逆索引：Adds(b=x-mn) → Muls(off=b*4) → Gather(inv32, rank, off) → Cast(inv64)。
5. 输出前插 TQueSync<PIPE_V, PIPE_MTE3>。

## 6. LLM 前置问题

- 桶数 R 是否 ≤16（处于 popcount 侧成本盈亏平衡点内）？
- n 是否 ≥256 且为 64 的整数倍？非 64 倍数的尾部是否有标量回退路径？
- 数据 dtype 是否 int32（int64 受 Gather 偏移与 Adds 同型约束）？
- 向量写与 MTE3 读之间是否插入了显式 TQueSync<PIPE_V, PIPE_MTE3> 同步？

## 7. 验收标准

- build + 精度全过；N=4096/i32/R=15：300→180us 净 kernel。精度必须覆盖非 64 倍数的 n（255/264/288/300/4095
  走标量回退）与负值域。

## 检索卡（短卡）

动作：将标量计数改为Duplicate→Compare位掩码→字节popcount累加直方图，并向量化查表scatter。
适用：适用于 R≤约16、int32、n≥256 且 n%64=0。
限制：Compares 标量操作数仅支持 half；int32 比较值须先 Duplicate 广播。
范围：值域直方图/查表类kernel的计数与查表scatter环节。
检索词：bit-packed mask、popcount、Duplicate、Compare、hist。
机会：桶少、n 大、重复高，循环每次含多次标量 UB 访问。
代价：桶数增大会增加按桶读取；盈亏取决于 (R+1)×n/8 与 3n。
