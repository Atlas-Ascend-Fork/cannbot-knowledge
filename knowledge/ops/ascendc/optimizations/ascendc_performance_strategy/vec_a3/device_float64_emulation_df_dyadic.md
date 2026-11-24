---
type: Optimization
title: device 端 float64 bit-exact 仿真（double-float + 整数 dyadic 长除法）
description: 以 device 端 bit-exact float64 仿真把 host 标量数学下沉到 kernel。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-device-float64-emulation-df-dyadic.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：device 端 float64 bit-exact 仿真（double-float + 整数 dyadic 长除法）

> 单一优化点：当算子的性能瓶颈是「device 归约 → **host float64 标量数学** → device 逐元素」三段式中的强制同步时，把 host 数学**下沉 kernel** 的唯一拦路虎是 NPU 无 float64 硬件。用 double-float（df，~66bit）承担所有「输出为 float32 比较值」的运算、用**整数 dyadic 长除法**承担所有「float64 舍入敏感决策」（half-even tie、边界比较），即可在 device 上 bit-exact 复刻 float64 语义，从而消除同步、实现双 kernel 背靠背异步提交。

---

## 1. 原理

ATen/CPU 参考实现的动态参数计算（量化 scale/zero_point、动态阈值等）通常用 float64。AIV 无 float64 单元，naive 的 float32 复刻会在**舍入敏感点**（rint 半数边界、阈值比较的 1ulp 分界）产生 ±1 偏差，破坏 bit-exact。

两层仿真：
- **df（double-float）**：`{hi, lo}` 两个 float32，无误差变换（two-sum / Dekker two-prod）+ 三级除法迭代，有效精度 ~66bit。对**最终输出是 float32** 的量（scale 截断、invScale、宏观比较）精度富余。
- **整数 dyadic**：float32 是 dyadic 有理数（`mant×2^e`，|mant|<2^25）。float64 除法的 53bit 舍入决策用**移位-比较-减法整数长除法**逐位生成（含 guard/sticky 位的 round-half-even），结果尾数 ∈ [2^52,2^53) 精确。用于 df 分辨率不够的场景：df 有效分辨率 48bit < float64 的 53bit——当后续决策依赖「商的第 49~53 位」（典型：zpFromMax = qmax − fl64(rmax/scale) 恰落在 x.5±1e-14 的 tie 带）时必须走整数路径。
- zp 的 rint half-even：df 的 hi 恰落 half 边界时，由 **lo 的符号**判向（lo>0 真值在 half 之上、lo<0 在下、lo==0 精确 half 取偶）。

## 2. 性能问题模式

适用信号（同时满足）：
- profiling 分解显示 `端到端 wall ≫ device kernel 总时间`，差值来自 host 归约读回（`.to(kCPU)`/`.item()` 强制同步）+ 参数计算后二次 launch；
- 被下沉的 host 数学是**有限分支的初等运算**（min/max → 除法/比较 → rint/clamp 链），无超越函数；
- 精度要求 bit-exact（golden 为 float64 链条）。

不适用：
- host 数学含 float64 超越函数（exp/log/pow，整数法不可穷举）；
- 参数只依赖 shape/attr（编译期已知，直接常量下沉即可，无需仿真）；
- host 数学本身可改为 float32 而不破坏精度（先验证 float32 直算，不行再上仿真）。

## 3. 正确性红线（实测踩坑）

1. **编译器破坏无误差变换**：bisheng -xasc 会重排/收缩标量浮点表达式，two-sum 的 `(a-s)+b` 被优化后不再无误差 → 所有关键运算经 `volatile float` 屏障中转（`__asm__` 的 float 寄存器约束在 Ascend 后端不受支持，会编译失败）。
2. **整数长除法的定标**：商 ∈ [1/2, 2) 时若首个生成位是 0（商 <1），53 位生成后的指数记账差 1 → 商翻倍。用「是否生成了整数位」分别定标，或循环左移 renormalize 到 [2^52,2^53)。
3. **df 除法必须用完整 df 除数**（hi+lo），用 `scale.hi` 单独除会在 tie 带引入 2^-25 相对误差 → zp 差 1。
4. **rint 感知 lo 位**：只对 hi 做 half-even 会在「真值 63.49999999999999 但 hi 舍入为 63.5」时输出 64（应为 63）。
5. **inf/NaN 保留 df 链条**：golden 的 NaN 传播语义（NaN 比较为 false 的链条）用 df 的 NaN 传播自然复刻；整数 dyadic 无法表示 inf/NaN，有限值路径才走 dyadic。
6. **float32×float32 的 float64 精确积**：两个 float32 的积在 float64 内精确 → 直接 float32 乘法（单次舍入）等价于 `ToF32(f64 精确积)`，无需 df。
7. **CMake custom_command 的 DEPENDS 必须包含头文件**：只列 .cpp 时改 .h 不触发重编，调试出现「改动无效」的幽灵行为。

## 4. 泛化条件

适用：量化/反量化参数计算、动态 loss scale、动态阈值/裁剪范围、任何「全量 reduce → host float64 标量数学 → 逐元素 map」且要求 bit-exact 的算子。
不适用：见 §2「不适用」。

## 5. 实施步骤

1. 用 profiler 分解确认 host 同步开销占比（wall − device 总时间）。
2. 在 python/numpy 上用 float32 严格模拟（`np.float32` 逐步舍入）复刻 device 算法，与 float64 golden 全用例比对——先定位**哪些决策点 float32 不够**（tie 带比较）。
3. 决策点分类：输出为 float32 的量 → df；float64 舍入敏感决策 → 整数 dyadic 长除法；inf/NaN → df 链条。
4. df 层：two-sum/two-prod/三级除法 + volatile 屏障；在 host（g++）单元测试同源代码先验证正确。
5. dyadic 层：F32ToDyad（位操作）/DyadAdd（指数对齐 ≤38 位移）/DyadDivF64（归一化到 [2^62,2^63) 后长除 53 位 + guard/sticky half-even）；rint 用「M>>sh 的整数 half-even」。
6. device kernel 开头：DataCopyPad 读回 per-core 归约对 + GetValue 归约 + 仿真计算 + 走原逐元素路径。
7. host：launch 参数化（把原 host 数学所需输入如 reduceRange/usedCoreNum 放进 tiling）、tiling/workspace tensor 按 key 缓存、双 launch 背靠背零同步。
8. 全量 bit-exact 验证（特殊值 case 必须覆盖：零张量、inf、阈值截断、half 边界构造值）。

## 6. LLM 前置问题

- host 数学的每一步在 float64 里的舍入点在哪？哪些决策依赖 <2^-48 的差异？
- 是否存在 x.5±1e-14 的 tie 构造 case（值域端点精确命中、对称值域）？
- inf/NaN 的传播链条是否依赖「NaN 比较为 false」？
- volatile 屏障是否覆盖了所有无误差变换？host g++ 单测过了吗？
- 长除法的指数记账在商 <1 与 ≥1 两种情形是否都验证过？

## 7. 验收标准

- 全量用例 bit-exact（含零张量/inf/阈值截断/端点命中 case）。
- wall 时间接近 device kernel 总时间 + n×launch（n=kernel 数）。
- 实测（910B3, 20 case）：mean 338→117us（2.89x），小 case 200→27-40us（5-7.5x，同步消除），大 case ~2x；bit-exact 20/20。

## 检索卡（短卡）

动作：以 device 端 bit-exact float64 仿真把 host 标量数学下沉到 kernel。
适用：适用于要求 bit-exact 的 reduce→host float64 标量数学→逐元素 map。
限制：AIV 无 float64 单元；不能以普通 float32 复刻舍入敏感计算。
范围：全量归约、标量参数计算及逐元素映射链路。
检索词：float64 仿真、bit-exact、rint 半数边界、1ulp、强制同步。
机会：端到端耗时远大于 device kernel 总时，存在归约读回同步和二次 launch。
