---
type: Optimization
title: 全归约的双 kernel 纯向量归约（partsum + gathersum）
description: 将单输出全归约改为双kernel纯向量归约：先partsum，再gathersum。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/two-phase-vector-reduce.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：全归约的双 kernel 纯向量归约（partsum + gathersum）

单一优化点：当归约目标只有一个输出（`num_segments == 1` 的全归约）时，不逐元素标量累加、也不用桶/原子路径，而是拆成「每核向量累积部分和 → 写临时区 → 单核向量减半归约」两个 kernel，把逐元素标量指令换成 128-lane 向量指令，同时规避 dav_c220 不支持 `ReduceSum`/int64 向量位运算/标量写回 32B 对齐的指令集限制。

## 1. 原理

全归约（所有输入元素求和到一个输出）是最简单的归约形态，却常被通用 scatter-add 路径低效处理：要么逐元素标量累加（scalar bound），要么建 segment 桶再原子写（对单输出是浪费——桶只有一个槽位）。case15（n=104 万 fp32，s=1）旧实现 839us，其 T_HW 仅 4.37us，说明路径开销主导。

改为**纯向量、双 kernel**：
- **partsum**：每核把 `n/usedCoreNum` 个元素按 128-lane fp32 累加器向量 `Add` 累积（一条向量指令替代 128 次标量），结束时把 128-lane 部分和 `DataCopyPad` 写到一个 `usedCoreNum×128` 的临时 GM 区（非原子）。
- **gathersum**（1 核）：读临时区，向量累积进 128-lane 累加器，再做**向量减半归约**（128→64→32→16→8，交替 buffer 避免读写重叠），最后 8 次标量 `GetValue` 求和、一次非原子写 y[0]。

为什么不用 `ReduceSum`：AscendC 的 `ReduceSum` 需要额外 workspace、对 count 对齐敏感，且调试中确认部分 dav_c220 场景有异常风险。向量减半用纯 `Add`（成熟 API），只发 5 次向量指令 + 8 次标量收尾，规避所有限制，实测稳定精确。

## 2. 性能问题模式

- 归约输出为标量/单元素（`num_segments == 1`、`reduce_all` 语义）。
- 当前实现逐元素标量累加，或走了通用桶/原子路径（对单输出是浪费）。
- 症状：墙钟与 n 线性且标量管线饱和，`msprof` 显示 scalar 占用高、向量单元空置。

## 3. 正确性红线

- **尾块 pad**：`n/usedCoreNum` 非 128 倍数时，主循环处理完整 128-lane 块，尾块（1~127 元素）先 `Duplicate` 零填充到 128 再 `Add`。UB→UB `DataCopy` 的 count 是**元素数**（非字节），且按 8 元素（32B）粒度截断——`rem` 非 8 倍数时剩余 0~7 个元素须用标量 `GetValue` 补到累加器 lane 0（加在任意 lane 对最终总和等价）。
- **向量减半无重叠**：`Add(dst, a, a[offset], count)` 的 dst 与源不能重叠，用两个 buffer 交替（acc/red）。
- **每核至少一个完整 128-lane 块**：小 n 用少量核（`usedCoreNum = min(核数, ceil(n/128))`），否则向量 `Add` 读越界。
- **标量写回同步**：标量 `SetValue` 写 y 前需 `pipe_barrier(PIPE_ALL)`（S→MTE3 可见性）。

## 4. 泛化条件

适用：
- 全归约（sum / mean 的分子）到单输出，n 大。
- fp16/bf16/fp32（累加用 fp32）；int32 需换 int32 累加器（本实现未覆盖）。
- 一切「逐元素标量累加改向量累积 + 一次归约」的归约算子，与具体算子无关。

不适用：
- 多输出归约（每 segment 一个输出，走桶路径）；int64 输出（无向量 Add）；n 极小（<128，向量化收益小）。

## 5. 实施步骤

1. Tiling：`usedCoreNum = min(核数, ceil(n/128))`，`perCoreRows = ceil(n/usedCoreNum)`，`baseS` 取 128 的倍数、受 UB 预算约束（tile = x + fp32 cast + 4×512B）。
2. partsum kernel：128-lane 累加器清零 → 循环 tile（完整块向量 Add + 尾块 pad）→ `pipe_barrier` → `DataCopyPad` 写 `tmp[core*128 .. +127]`。
3. gathersum kernel（1 核）：读全部 `usedCoreNum×128` 元素 → 向量累积 → 减半归约（128→64→32→16→8，acc/red 交替）→ 8 次标量求和 → 非原子写 `y[0]`。
4. Plugin 分配 `usedCoreNum×128` fp32 临时区，顺序 launch partsum、gathersum。
5. 精度 + 性能复测。

## 6. LLM 前置问题

- 算子是否全归约到单输出？n 量级？
- 输出 dtype 是否支持 fp32 向量累加（int64 不适用）？
- 指令集是否支持 `ReduceSum`（不支持则用向量减半归约）？

## 7. 验收标准

- 编译通过，精度在阈值内（向量归约与串行累加浮点误差可接受）。
- 全归约 case 墙钟从标量路径的数百 us 降到接近「读一遍」带宽下界（如 case15：839us → 63us，13.3×）。

## 检索卡（短卡）

动作：将单输出全归约改为双kernel纯向量归约：先partsum，再gathersum。
适用：大n的sum或mean分子全归约到单输出；支持fp16/bf16/fp32并以fp32累加。
限制：主循环仅处理完整128-lane块，剩余1~127元素尾块单独处理；int32需int32累加器，当前未覆盖。
范围：num_segments==1、reduce_all语义的标量或单元素输出。
检索词：num_segments==1，reduce_all，partsum，gathersum，scalar bound，scatter-add
机会：单输出全归约仍逐元素标量累加，或经过通用桶/原子路径。
