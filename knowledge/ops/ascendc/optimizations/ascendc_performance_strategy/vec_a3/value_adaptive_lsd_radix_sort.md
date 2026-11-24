---
type: Optimization
title: 值域自适应 LSD 基数排序替换 O(N²) 标量排序（排序键类算子）
description: 用值域自适应LSD基数排序替换O(N²)标量插入或选择排序，并由umin与umax确定pass数。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-value-adaptive-lsd-radix-sort.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：值域自适应 LSD 基数排序替换 O(N²) 标量排序（排序键类算子）

> 单一优化点：小规模（全量驻 UB）排序/去重/分位类算子若用**标量插入/选择排序**（O(N²) 次标量
> UB 访问），替换为**保序位变换 + 值域自适应 LSD 基数排序**（byte 直方图 counting sort，
> 按 (max^min) 的非零字节决定 pass 数），标量工作量从 N²/4 次比较降到 passes×N 次 RMW，
> N=4096 实测 148ms → ~1ms（135×）。

适用于任何"整段数据驻 UB、需要有序或分组"的算子（unique/sort/argsort/分桶/topk 预处理），
与具体算子无关。

---

## 1. 原理

- **保序位变换**把任意 dtype 统一成无符号序，byte 直方图才能正确分桶：
  int64: `k = x ^ (1<<63)`；int32: `k = x ^ (1<<31)`；
  float: `bits>=0 ? bits|0x80000000 : ~bits`（全序、NaN 按位模式有序、**-0.0 需规范化到
  +0.0 的 key**——torch 语义的 unique 用 IEEE == 判等，±0.0 必须合并）。
- **pass 数自适应**：pass p 需要跑 ⟺ `((umax^umin) >> (8p)) != 0`。值域 [0,8) 的 int64 只跑
  1 pass（不是 8）；(max^min) 而非 max 本身——符号位翻转后高位字节恒非零但可能全相同。
- LSD counting pass：hist[256] 清零 → 统计 → exclusive 前缀和 → 稳定 scatter (key, index)
  双数组 ping-pong。稳定性免费（LSD 天然稳定），inverse 只依赖"等值同 run"但稳定无害。

## 2. 性能问题模式

- profiling 显示 SCALAR pipe 占比 ~100%、kernel 时间随 N² 增长（N 翻倍时间×4）。
- 扫描体积乘子（实际比较次数 / 理论 N·log₂N）>10×（插入排序 N²/4，N=4096 时 85×）。
- 全量数据驻 UB（N ≤ UB预算/元素占用），单核即可，无需多核。

## 3. 正确性红线（实战踩坑，全部实际发生过）

1. **maxKey 必须无符号比较**：key 域是"无符号序"，有符号 `>` 把翻转符号位后的正数判为负 →
   maxKey 恒 0 → passes=0 → **根本没排序**（现象：已有序/全不同的 case 巧合 PASS，有重复
   无序 case 全 FAIL）。
2. run-boundary 从 p=1 起循环时**别漏写 p=0 的 inverse**。
3. values 若"in-place 逆变换"只改写 run-start 位置，run 中间位置还是 key 域垃圾——host 按
   [:K] 切片会取到。values 必须密集写入独立区域（排序 ping-pong 的空闲面恰好可用）。
4. **buffer 复用禁止与在飞 MTE3 竞争**：DataCopyPad(UB→GM) 异步，紧随其后标量覆写源
   buffer 会竞争（r1 实测 inverse 被 counts 覆盖）。各输出独立 buffer 或程序序保证。
5. 改 kernel 头（.h）不触发 CMake 重编——调试"改了没生效"先 touch .cpp。

## 4. 泛化条件

- **适用**：单核 N≤~4096（受 UB 预算：key×2 + idx×2 + 输出缓冲）全量驻 UB 的排序/分组。
- **不适用**：N 超出 UB（需多核分片 + 归并）；已部分有序的极端数据（radix 收益仍在但不显著）。

## 5. 实施步骤

1. 数据搬入 UB 后做保序变换（标量 O(n) 或向量 Xor）。
2. 一遍标量求 umin/umax（uint64 比较），算 range=umax^umin 定 pass 数。
3. 每 pass：hist 清零/统计/前缀和/稳定 scatter（(key,idx) ping-pong）。
4. run-boundary 扫描产出 values（逆变换，写 ping-pong 空闲面）/counts/inverse（经 idx
   payload scatter）。
5. 输出 DataCopyPad，num(K) 写回。

## 6. LLM 前置问题

- 输入规模 N 是否能全量驻 UB（key×2 + idx×2 + 输出缓冲的 UB 预算是否够）？
- 现有实现的 kernel 时间是否随 N² 增长、SCALAR pipe 是否接近 100%？
- 数据 dtype 是什么，是否包含 -0.0、NaN 或极值对需要保序位变换特殊处理？
- 输出 buffer 是否可能与在飞 MTE3 DataCopyPad 竞争，需要独立 buffer 吗？

## 7. 验收标准

- build + 精度全过；N=4096 int64 近全不同：148ms → ~1ms；值域 <256 的输入 1 pass 即完成。精度需覆盖负数、
  ±0.0、NaN 位模式、极值对（±2^62）。

## 检索卡（短卡）

动作：用值域自适应LSD基数排序替换O(N²)标量插入或选择排序，并由umin与umax确定pass数。
适用：单核数据可全量驻留UB，且N不超过约4096的排序或分组。
限制：key域必须按无符号序比较，maxKey不得使用有符号比较。
范围：单核全量驻UB的小规模排序、分组、去重或分位路径。
检索词：LSD基数排序、保序位变换、byte直方图、umin/umax、range、pass数、无符号序
机会：排序由SCALAR管主导，耗时随N呈二次增长。
代价：规模受key双缓冲、idx双缓冲及输出缓冲的UB预算限制。
