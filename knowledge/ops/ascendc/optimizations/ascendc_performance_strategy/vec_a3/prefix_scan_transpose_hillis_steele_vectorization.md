---
type: Optimization
title: 串行前缀扫描改转置 + Hillis-Steele 向量化 block-scan
description: 将逐元素串行前缀扫描改为tile转置与Hillis-Steele扫描。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-prefix-scan-transpose-hillis-steele-vectorization.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：串行前缀扫描改转置 + Hillis-Steele 向量化 block-scan

> 单一优化点：把逐元素标量前缀扫描（S pipe 每元素 GetValue/SetValue 串行比较链）
> 改成 R×C tile 转置到列主序（TransDataTo5HD）+ log2(C) 步 Hillis-Steele 全宽
> 向量前缀（Min/Compare/Select），cross-tile carry 折叠进 column 0。向量单元
> 利用率从 ~0 提到全宽，扫描串行深度从 N 降到 (N/tile)·log2(C)。

本策略适用于任何"前缀扫描/累积类（cummin/cummax/cumsum/cumprod 类）"kernel，
与具体算子无关。

---

## 1. 原理

标量扫描的每元素成本 = 2 次 UB 标量读写（S pipe）+ 1 次串行比较，比较链是
严格顺序依赖（后一个元素依赖前一个的 running 状态），S pipe 标量访存延迟
无法被流水掩盖，V pipe 全程空转。实测这类实现比框架基线慢 10-20 倍。

向量化 block-scan 把 [R 行][C 列] tile 转置成列主序 W[C][R]（每列的 R 个
running 状态在向量 lane 上并排），于是：
- 前缀依赖被拆成 R 条独立 lane 链 → 每条链只在 tile 边界交换 carry；
- tile 内 C 步前缀用 Hillis-Steele：log2(C) 步、每步一次全宽 Min +
  Compare + Select（严格 LT 保 tie 语义：后者胜）；
- 计算全部 fp32（值只被 Select 选择、不被算术组合 → fp16/bf16/int32(＜2^24)
  精确 round-trip），消掉逐元素 Cast。

开销模型：改前 per-element ~S-pipe 标量访存×2；改后 per-tile =
2 次 TransDataTo5HD + log2(C)×3 向量指令 + carry 折叠，摊到 R×C 个元素上
低 1-2 个数量级。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. 代码形态：kernel 内出现逐元素 `GetValue(i)` → 比较 → `SetValue(i)` 的
   串行循环，循环变量间存在 running-min/max/sum 寄存器依赖链；
2. 代码形态：多行数据按行均分到各核，每核逐行逐元素扫描；
3. profiling 特征：所有含该维的 case 一致慢 10 倍以上，耗时与元素数线性，
   pipe 占比 S pipe 主导（V pipe 空）；
4. 特殊 case：行数 < 核数时只有少数核干活（单行 case 差百倍）。

不适用：扫描维极短（如 ≤64）且行数巨大——tile 转置固定开销摊不平，
保持标量或走其他路径；值需要被算术组合且 dtype 无法 fp32 精确表示的
累积（如 int64 cumsum）。

## 3. 正确性红线

- **tie 语义**：torch.cummin 用 `<=`（相等取后者 index）。Hillis-Steele 里必须
  用严格 `<`（shifted < current 才取 shifted 的 index），等值时保留 current
  （更晚的位置），否则 index 全错但 values 仍对（极难排查）。
- **carry 折叠顺序**：cross-tile carry 并入 column 0 必须发生在 HS 之前且
  carry 与 column 0 tie 时 column 0 胜（carry 是更早的位置）。
- **NaN 语义**：HS 快路径不保 NaN 传播；必须旁路检测（EQ(x,x) 向量掩码
  AND 累积，无 per-tile barrier）+ 检出后 NaN-aware 路径整行重算。
- **fp32 index 精确性**：index 以 fp32 表示时 scan_len 必须 < 2^24，超限走
  标量路径。
- **转置地址列表**：TransDataTo5HD 的 src/dst 16 地址列表须 32B 对齐；
  固定 TBuf 布局下可一次预计算。

## 4. 泛化条件

适用（任一）：
- 任何前缀扫描算子（cummin/cummax/cumsum/cumprod/argmin-scan）在
  contiguous 扫描维上的实现；
- 标量扫描链已确认是瓶颈（profiling S pipe 主导 / 全 case 一致慢 10 倍+）。

不适用（任一）：
- 扫描算子本身可结合且无 index 输出——用树形折叠归约策略（库内 08/30）更优；
- 扫描维 < ~128 的短扫描（转置固定开销主导）；
- 累积值超出 fp32 精确表示范围。

## 5. 实施步骤

1. 定位逐元素扫描循环，确认 running 状态依赖链 + S pipe 主导的 profiling 特征；
2. 核验正确性红线（tie 语义 / NaN / index 精度）对应的 golden 行为；
3. 设计 R×C tile（R·C=2048 适配 192KB UB 的多缓冲布局），写 Fwd/Back
   TransDataTo5HD + Hillis-Steele 步进 + carry 折叠；
4. 按行数分派：单行→1D scan（lane=同行连续 chunk）；少行→1D/小 tile；
   多行→block tile；行数<核数且长扫描→扫描维跨核两阶段（Phase1 段 carry →
   核间同步 → Phase2 前缀播种重扫）；
5. 全量编译 + 精度（含 NaN/±inf/tie 用例）+ 多次取样性能；
6. 验收：逐 case 加速比提升超噪声且精度全过则采纳。

## 6. LLM 前置问题

- 扫描的 tie 语义是 `<=` 还是 `<`？NaN 如何传播？
- 扫描维最长多少？是否 < 2^24（fp32 index 精确）？
- 输入是否 contiguous？非 contiguous 扫描维是否可转成 (outer, scan, inner)
  分解由 kernel 原生 strided 处理（避免宿主 permute）？
- 行数与 AIV 核数的关系？是否需要扫描维切分？

---

## 验收标准（实测数据）

以 cummin（910B3，20 case 全量）为例：标量实现平均加速比 0.073x（14 case
可用、6 case 因宿主 permute 失败）；本策略（含分派结构）平均 0.486x，
20/20 精度全过，达到高性能参照水平（0.49x）。case13（1D 100 万元素单行）
从 0.003x → 0.356x（118 倍，扫描维跨核两阶段）。

## 7. 验收标准

- build + 精度全过（含 NaN/±inf/tie 用例：Hillis-Steele 用严格 `<` 保 `<=` 取后 index 语义；carry 与 column 0 tie 时 column 0 胜；scan_len ≥ 2^24 时回退标量路径保 fp32 index 精确）。
- 性能验收（卡内实测，cummin 910B3 20 case 全量）：标量实现平均加速比 0.073x（且 6 case 因宿主 permute 失败）；本策略平均 0.486x，20/20 精度全过，达到高性能参照水平（0.49x）；case13（1D 100 万元素单行）从 0.003x → 0.356x（118 倍）。
- 非适用场景（扫描维 < ~128 的短扫描、超 fp32 精确表示的累积、可结合无 index 输出的树形折叠更优形态）回退原路径且无精度/性能退化。

## 检索卡（短卡）

动作：将逐元素串行前缀扫描改为tile转置与Hillis-Steele扫描。
适用：适用于cummin、cummax、cumsum、cumprod或argmin-scan的连续扫描维实现。
限制：torch.cummin相等取后者index；Hillis-Steele内部必须使用严格<比较。
范围：前缀扫描算子的contiguous扫描维。
检索词：R×C tile、转置、Hillis-Steele、running-min/max/sum、S pipe、V pipe。
机会：内核存在GetValue→比较→SetValue串行循环及running状态依赖链。
