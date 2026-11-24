---
type: Optimization
title: 免排序值域直方图（unique/计数类算子跳过排序本身）
description: 将先排序再查找 run 边界，改为按值建立直方图并遍历非零桶。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-sort-free-value-histogram-unique.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：免排序值域直方图（unique/计数类算子跳过排序本身）

> 单一优化点：**输出不需要有序数组**的排序类算子（unique 的 values/counts/inverse、按值
> 计数、值压缩），当值域跨度 (max-min) 小于阈值时**完全跳过排序**：一遍 O(n) 直方图计数 +
> 一遍 O(R) 桶压缩（非零桶天然升序 = sorted values，rank 表）+ 一遍 O(n) 顺序写 inverse。
> N=4096 实测比 1-pass radix 再快 ~40%，比 O(N²) 标量排序快 ~300×。

适用于 unique / bincount / 值域内分组统计类算子。

---

## 1. 原理

- 直方图按值分桶，**非零桶的遍历顺序天然是升序**——不需要先排序再找 run 边界。
- inverse[i] = rank[x[i]]：position i 就是原始索引 i（顺序写，无需 permutation payload）。
- rank 表原地覆写直方图（读 hist[b] 后写 rank[b]，b 递增顺序安全），且 R+1 可以远大于
  n（如 n=512 散布 2000 个值），**不能**放在按 n 分配的 idx buffer（越界踩相邻 UB）。
- float 输入：整数值 f32（randint().to(f32) 类）经**标量逐元素检测**
  `v == (float)(int64)v`（对任意 integral float 精确，含 |v|≥2^24）后 Cast 到 int32 复用
  整数直方图；分数值回退 radix。

## 2. 性能问题模式

- 排序只为拿"分组+计数"，从不消费有序数组本身。
- 值域跨度小（类别数 ≤ 数千）但 n 大（重复多）。
- 算子语义等价于 groupby-value + 每组计数 + 元素→组号映射。

## 3. 正确性红线（实战踩坑）

1. **值域门槛必须无符号**：`(uint64)mx - (uint64)mn` 在 ±2^62 极值对下达 2^63，转 int64
   变负数 → `diff > threshold` 判 false → 不退出直方图 → 垃圾桶号越界读 → **vector core
   exception**。全程 uint64 比较；float 路用 int64 差 + `diff < 0` 守卫（aicore 禁止
   float↔unsigned 直接 cast）。
2. **f32 的 Cast 必须在 range 预检之后**：Cast 覆盖 key0 的 float bits，预检失败回退 radix
   时需要原始 bits（否则 values 输出为 bit 错位垃圾，如 7.0f → 5e-44）。
3. ±0.0 处理跟随框架语义（torch 的 unique 用 IEEE ==：合并；bit-exact 比较则区分）。
4. 向量 round-trip 检测不可行替代标量检测：Compare 的 mask 是 bit-packed，GetValue 按字节
   读出 8 结果打包，无法逐元素探测。

## 4. 泛化条件

- **适用**：整数 dtype 或整数值浮点 + 值域跨度 ≤ 阈值（受 hist UB 预算，4096 桶=16KB）。
- **不适用**：值域跨度大（均匀随机 int64）→ 回退基数排序；需要有序数组的算子（sort 本体）。

## 5. 实施步骤

1. 标量 min/max（一遍）→ 无符号差判定走/不走。
2.（f32）标量整数值检测 + range 预检 → 向量 Cast 到 int32。
3. hist 计数（n 次）→ 桶压缩（R 次，rank 原地覆写 hist，vals/counts 紧凑写）→ inverse
   顺序写（n 次查 rank）。
4. 输出同原路径。

## 6. LLM 前置问题

- 算子输出是否真正不需要有序数组（只消费分组+计数+映射）？
- 输入值域跨度 (max-min) 是否小于直方图 UB 预算允许的阈值？
- 输入是整数 dtype 还是浮点？若是浮点，是否全部为整数值（可安全 Cast 到 int32）？
- 框架对 ±0.0 的语义是 IEEE == 合并还是 bit-exact 区分？

## 7. 验收标准

- build + 精度全过；N=4096 值域 [0,4096)：radix 2-pass ~900us → 直方图 ~200us；值域 16：再降至 ~60us（向量化
  版见策略 03）。精度必须覆盖：负数、极值对（±2^62/±2^31）、±0.0、分数值回退、N=1/2。

## 检索卡（短卡）

动作：将先排序再查找 run 边界，改为按值建立直方图并遍历非零桶。
适用：整数 dtype 或取整数值的浮点，且值域跨度不超过阈值。
限制：大值域须回退；值域门槛计算必须采用无符号差。
范围：unique values/counts/inverse、按值计数、值压缩。
检索词：值域直方图、groupby-value、非零桶、inverse、rank、run 边界
机会：排序仅用于分组计数、不消费有序数组，且值域小、输入大、重复多。
代价：桶数受 hist 的 UB 预算限制，4096 桶占 16KB。
