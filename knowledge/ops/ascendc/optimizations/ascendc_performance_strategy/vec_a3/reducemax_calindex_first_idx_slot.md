---
type: Optimization
title: ReduceMax/ReduceMin calIndex 打包 (max, 首达 idx) 槽式归约替代手写定位链
description: 用calIndex=true的ReduceMax/ReduceMin一次产出最值与首达索引，替代条件定位链。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-reducemax-calindex-first-idx-slot.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：ReduceMax/ReduceMin calIndex 打包 (max, 首达 idx) 槽式归约替代手写定位链

单一优化点：per-row argmax/argmin 类「归约值 + 首达位置」输出，用
`ReduceMax(dst, src, work, count, calIndex=true)` 一条调用原生得到
(max, 第一个最大值的索引) 对，替代手写「ReduceMax → GetValue →
Compares+Select 64 元素 chunk 链 → ReduceMin → GetValue」链，把每行每
tile 的 2 次标量回读降到每行 1 次、消除 ~192 条向量指令的定位链。

## 1. 原理

AscendC 的 whole-tensor 归约 API（ReduceMax/ReduceMin，count 形态）带
`calIndex` 参数：true 时 dst 写两个元素——dst[0]=最值、dst[1]=首达索引
（按 dst 数据类型的位模式存储）。硬件 vreduce 指令在 repeat 内部与跨
repeat 归并时都保持「多个并列最值取第一个」的语义（文档级保证）。因此
argmax 的首达定位完全不需要软件比较链：

- dst 对 float 只需 **8 字节对齐**（不同于一般向量 dst 的 32B）→ B 行的
  (max, idx) 槽可以 2 元素间距紧凑排列；
- idx 读取：`float raw = dst.GetValue(1); uint32_t idx =
  *reinterpret_cast<uint32_t*>(&raw);`（half 用 uint16_t）；
- 每行只需这一次标量回读（读 idx 槽），归约调用之间零标量同步。

配套的 N%64!=0 处理（count 形态要求 256B 对齐，mask 连续模式会跳过块内
中段，都不能直接用）：**两段合成**——full64=n/64 段用 mask 连续模式
（mask=64, repeatTime=full64, srcRepStride=8）归约；tail 段（rem=n%64）
在偏移 full64*64 处（32B 对齐）mask=rem、repeatTime=1 单独归约；标量
合并 `mB > mA ? iB + full64*64 : iA`（严格大于保首达）。

## 2. 性能问题模式

- 逐行 argmax/argmin/top-1（或任何需要最值+位置的算子），行循环内每
  tile「取最值标量 + 条件执行 Compares/Select 定位链 + 再取标量」。
- profiling：scalar_ratio 30-50%（每 tile 2 次 GetValue 停顿），vec_ratio
  50-70%（其中相当部分是定位链的低效向量工作）。
- 行粒度小（单行 DMA <8KB）时再叠加 MTE 小块发射开销——本策略与多行
  批量搬运（2D DataCopyPad，块数=行数）组合收益最大。

不适用：需要非首达语义（如末达、任意并列位置）；ReduceMax/ReduceMin
不支持的数据类型；跨多输出 segment 的归约（本策略是 per-row/per-tile
独立归约）。

## 3. 正确性红线

- **calIndex 的 idx 是位模式**：必须 reinterpret 读，直接当 float 用会
  得到无意义值。
- **count 形态 256B 对齐**：count×元素大小须 256B 倍数（fp32=64 倍数）；
  **mask 连续模式是「每 repeat 前 mask 个元素」**——n=100 用 mask=36/
  repeat=2 会跳过 [36,64)，跨 repeat 的任意前缀必须走两段合成。
- **两段合成平局取左**：合并判断必须 `mB > mA` 严格大于（相等取左段
  首达），右段 idx 要加 full64*64 偏移。
- **2D 批量搬运后必须走 TQue EnQue/DeQue（或等效 MTE→VEC 同步）再向量
  读**：裸 TBuf + DataCopyPad 后立即 ReduceMax 会读到旧值（实测 max
  读到预填的 -inf）。
- 首 tile/首段比较基线用 -inf；padding 若参与归约必须恒为 -inf（预填
  一次且后续搬运不覆盖）。

## 4. 泛化条件

适用：
- per-row / per-tile 的 argmax、argmin、max-with-index、min-with-index、
  top-1 类输出；行可整段（或分两段）装入 UB。
- 逐行标量回读是瓶颈（scalar_ratio>30%）或定位链向量指令占比高的任何
  归约算子，与具体算子无关。

不适用：
- 需要 top-k（k>1）——配合 topk 类策略；
- 归约跨行/跨 segment 耦合；
- half 输入的 idx > 65535（uint16 上限，见 API 文档）。

## 5. 实施步骤

1. host 端按 (M,N) 算 nPad=align64(N) 与批量行数 B（UB 预算/(nPad×
   elemBytes)），下发 tiling。
2. kernel：TQue 双缓冲 Alloc → 2D DataCopyPad{blockCount=B,
   blockLen=N×es, dstStride=(nPad-N)×es} → EnQue/DeQue。
3. 每行 ReduceMax：N%64==0 或 N≤64 单次调用（mask=64/repeats 或
   mask=N/repeat=1，calIndex=true）；否则两段合成+标量首达合并。
4. 每行 1 次 GetValue 读 idx 槽 → SetValue 到输出缓冲 → Cast int64 →
   DataCopyPad 批量写出。
5. 精度必须覆盖：并列最大（首达）、全 0 行、全负行、±inf、±1e30、
   N%64∈{0,1,63} 的边界用例。

## 6. LLM 前置问题

- 目标硬件的 ReduceMax/ReduceMin 是否支持 calIndex（查产品支持表）？
- 输出语义是否首达？需要 idx 还是只要最值（只要最值则 calIndex=false
  更省）？
- 行长 N 的 64 取整余数分布（决定单次调用 or 两段合成路径占比）？
- 多行批量搬运的行距对齐（nPad 64 倍数）与 UB 预算是否核算？

## 7. 验收标准

- 编译通过；精度全过（首达语义用并列最大用例锁定）。
- per-row 标量回读次数从 2×nTiles 降到 ≤3；scalar pipe 占比显著下降。
- 实测参考（910B3, 40 AIV, fp32）：[2000,512] 49.2→23.7us（0.76→1.2x）、
  [256,4096] 34.2→23.9us（0.90→1.2x）；小 shape 不退化。

## 检索卡（短卡）

动作：用calIndex=true的ReduceMax/ReduceMin一次产出最值与首达索引，替代条件定位链。
适用：适用于逐行或逐tile最值带索引、top-1输出，且一行可整段或分两段装入UB。
限制：calIndex索引是位模式，必须reinterpret读取，不得直接作为float使用。
范围：逐行argmax/argmin的归约值与首达位置输出。
检索词：ReduceMax、ReduceMin、calIndex、首达索引、Compares、Select、reinterpret。
机会：每个行tile先回读最值，再执行Compares/Select定位链并再次回读标量。
