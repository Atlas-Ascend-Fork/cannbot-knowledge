---
type: Optimization
title: A2 (dav-2201) 前缀扫描向量化实施陷阱集
description: 将标量前缀扫描改为 lane 并行，以 Compare/Select/Min 跨 lane 推进扫描状态。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-a2-scan-vectorization-pitfalls.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-24T01:38:07Z'
platforms:
- a2
---

# 性能优化策略：A2 (dav-2201) 前缀扫描向量化实施陷阱集

> **归档说明**：本卡为 A2（dav-2201）专属策略，因上游 `vec-A3` 源库归置迁入本册；frontmatter `platforms` 为 `a2`，按 A3 平台过滤不会命中，A3 侧未验证，勿直接套用。

> 单一优化点：在 A2/910B 上把标量前缀扫描（cummin/cummax/argmin-scan 类）改为 lane 并行
> 向量化时的 5 个实测硬约束。每条均有 cummin 实测证据（2026-08，910B3 + CANN 9.0.0）。
> 与库内 `prefix-scan-transpose-hillis-steele-vectorization` 配套使用。

## 1. 原理

向量化前缀扫描依赖 Compare/Select/Min 等向量 API 在 lane 间并行推进扫描状态。A2 硬件
对这些 API 有如下实测语义与约束（均为踩坑提炼）：

### 1. CMPMODE::NE 是有序比较，检测 NaN 必须用 LE(x,x)
- 现象：`Compare(m, x, x, CMPMODE::NE)` 在 x=NaN 时返回 false（文档直觉应为 true）。
- 正确写法：`Compare(m, x, x, CMPMODE::LE)`（IEEE 无序：NaN≤NaN=false），再
  `Select(key, m, x, negInf, VSEL_CMPMASK_SPR)` 反源选择：正常值→x，NaN→-inf。
- NaN 语义折叠为 -inf 键后，"NaN 后接真 -inf" 的 tie 与 torch.cummin 有差异（torch 保持
  NaN），用例集混用 NaN 与 -inf 时需评估。

### 2. count 型 VSEL_CMPMASK_SPR 每个 vector repeat 只消费一次 cmpmask
- 现象：count=128（half 域）或 128（float 域）的 Select，lane≥64 的选择结果复用第一
  repeat 的谓词位（bit 周期性错误，values/indices 双输出时表现为两路不一致）。
- 规避：所有 Compare/Select/Min 按向量 repeat 粒度切片执行——half 域 128 lane（256B）、
  float 域 64 lane（256B）；索引载荷若在异宽度域必须再子切片且掩码张量按位打包偏移
  （bit/8）寻址，但 set_cmpmask 要求对齐——最稳妥是让全部载荷与键同域同切片宽度。

### 3. Select 的载荷 dtype 在 A2 仅支持 half/float
- int32/int64/int8/uint8 载荷的 Select 编译可过或直接无匹配；整数 idx 载荷须放入
  half/float 域（dimLen<2048 用 half 精确；更大用 float 精确到 2^24），出口
  Cast(float→int64) 一次完成。
- 附带发现：int32→half / half→int32 直接 Cast 在本芯片产出错误值（经 float 中转正确）。

### 4. Min+EQ 组合替代整数 LE 比较
- A2 Compare 整数仅支持 int32-EQ：`upd = EQ(Min(new, m), new)` ⟺ new<=m，平局取
  new（later 位置），与 torch.cummin 的 `v <= m` 更新规则一致；dst 可与 src1 别名
  （in-place Min 状态保持可用）。

### 5. bisheng kernel 对象的 CMake 依赖必须显式包含头文件
- add_custom_command 只 DEPENDS .cpp 时，kernel 头文件改动不触发重编——所有"改了
  没效果"的迭代都是幻觉构建。`file(GLOB *.h)` 加入 DEPENDS，且每次实验前核对
  build/kernels/*.o 时间戳。

## 2. 性能问题模式

- cummin/cummax/argmin-scan 类算子采用标量逐元素扫描，SCALAR pipe 主导、kernel 时间 ∝ N。
- 试图向量化后出现 bit 周期性错误、NaN 误判、载荷 dtype 无匹配等正确性/编译问题。

## 3. 正确性红线

1. NaN 检测必须用 `CMPMODE::LE(x, x)`（NE 是有序比较，NaN 时返回 false）；NaN 折叠为 -inf 键后与 torch.cummin 的 NaN 保持语义有差异，混用 NaN 与 -inf 的用例需评估。
2. count 型 Select(VSEL_CMPMASK_SPR) 每个 vector repeat 只消费一次 cmpmask——必须按 repeat 粒度切片执行（half 域 128 lane、float 域 64 lane）。
3. Select 载荷仅支持 half/float；int32↔half 直接 Cast 产出错误值，须 float 中转。
4. 整数 LE 比较用 `EQ(Min(new, m), new)` 替代（A2 Compare 整数仅支持 int32-EQ）。
5. CMake 的 kernel 对象 DEPENDS 必须显式包含头文件（file(GLOB *.h)），否则头文件改动不触发重编，产生幻觉构建。

## 4. 泛化条件

- **适用**：A2/910B（dav-2201）+ CANN 9.0.x 上的 cummin/cummax/argmin-scan 类标量前缀扫描向量化；dimLen<2048 载荷可用 half 精确、更大用 float（精确到 2^24）。
- **不适用**：需要 NaN 严格保持（torch.cummin 语义）且用例混用 NaN 与 -inf 的场景（折叠为 -inf 键引入 tie 差异）；其他芯片代号的 API 语义未验证。

## 5. 实施步骤

1. NaN 检测：`Compare(m, x, x, CMPMODE::LE)` + `Select(key, m, x, negInf, VSEL_CMPMASK_SPR)` 反源选择。
2. 所有 Compare/Select/Min 按向量 repeat 粒度切片：half 域 128 lane、float 域 64 lane；载荷与键同域同切片宽度。
3. 整数 idx 载荷放 half/float 域，出口 Cast(float→int64) 一次完成（int32↔half 直 Cast 错误，经 float 中转）。
4. 整数比较用 `EQ(Min(new, m), new)` 替代 LE；dst 可与 src1 别名做 in-place 状态保持。
5. CMake add_custom_command 的 DEPENDS 加 `file(GLOB *.h)`，每次实验前核对 build/kernels/*.o 时间戳。

## 6. LLM 前置问题

- 目标芯片是否为 A2/910B（dav-2201），CANN 版本是否 9.0.x？
- 用例集是否混用 NaN 与 -inf（NaN 折叠为 -inf 键会与 torch.cummin 语义有差异）？
- 扫描维度 dimLen 是否 <2048（决定载荷可用 half 还是必须 float）？
- CMake 的 kernel 构建 DEPENDS 是否包含头文件，build/kernels/*.o 时间戳是否与源码一致？

## 7. 验收标准

- build + 精度全过；cummin（910B3, 20 case）：mode1 路径 self 加速 1.02~7.42x；唯一负加速 case（bf16
  dim=0, 0.29x）修复至 2.12x；20/20 精度 bit-exact。

## 检索卡（短卡）

动作：将标量前缀扫描改为 lane 并行，以 Compare/Select/Min 跨 lane 推进扫描状态。
适用：适用于 A2/910B、CANN 9.0.x 的标量前缀扫描。
限制：NaN检测必须用LE(x,x)，不能用有序比较NE；dimLen<2048时half载荷可精确表达。
范围：cummin、cummax、argmin-scan 类算子。
检索词：前缀扫描、lane 并行、Compare、Select、Min、CMPMODE::LE。
机会：逐元素前缀扫描由 SCALAR pipe 主导。
