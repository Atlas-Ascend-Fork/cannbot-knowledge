---
type: Optimization
title: 累加器与 filter 寄存器驻留的 tap 折叠
description: 把 max(acc, span+f) 的 classic 两步折进一次 VF 调用：acc 与 filter 具名寄存器常驻，每 tap 只 LoadAlign 一次
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/vec-acc-register-resident-tap-fold.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：累加器与 filter 寄存器驻留的 tap 折叠

把 `max(acc, span+f)` 的 classic 两步（每 tap 6 次 UB 往返）折叠成一次 `__simd_vf__` 调用内的 acc 寄存器驻留链：filter 具名寄存器常驻，每个 tap 只 `LoadAlign` 一次窗口列 + `Add` + `Max`，输出与 classic 路径位级一致。

## 1. 原理

`y = max(acc, span + f)` 在 classic LocalTensor 形态下是两条独立的向量调用：

- `Add(partial, span, f, C)`：读 span、读 f、写 partial —— 3 次 UB 访问；
- `Max(acc, acc, partial, C)`：读 acc、读 partial、写 acc —— 3 次 UB 访问。

每个 tap 6 次（Add 3 + Max 3），N 个 tap 就是 6N 次 UB 访问，而真正不可省的只有「每个 tap 读一次输入窗口」这 N 次。矢量单元因此大部分时间在等 UB 端口，表现为「V 管很忙、但每条 op 的平均周期偏高」——不是算力不够，是流量形态不对。

把整条归约链折进寄存器后：`tmp` 与 `acc` 都是 RegTensor，filter 也在寄存器，唯一的 UB 流量是每个 tap 一次的 `LoadAlign`。指令数从「每 tap 2 条带隐式 load/store 的调用」变成「1 条显式 load + 2 条寄存器运算」，V 侧吞吐随之提升。

## 2. 性能问题模式

- 优化目标：消除 max 归约链在 UB 里的 read-modify-write 往返（每 tap 6 次），把 V 管从「UB 带宽受限」变成「发射数受限」
- 适用数据流：逐输出点做 tap 集合 `max(值+权重)` 归约的窗口类算子；tap 数有编译期特化；UB 能同时驻留被折的 tap 集合
- 判定入口（先量后改）：`aiv_vec_time / Device Duration ≥ 0.9` 且 `aiv_scalar_time / Device Duration ≥ 0.4`，同时 `aiv_mte2_time / Device Duration ≤ 0.2` —— 说明瓶颈在 V 侧且伴随大量地址/发射开销，换 VF 形态最有效

## 3. 正确性红线

- 累加器必须在一个 VF 调用内跨越全部 tap 存活：一旦 acc 落 UB，每个 tap 重新变成 6 次往返，收益归零
- filter 必须整组常驻寄存器且**具名展开**——`RegTensor freg[TAPS]` 数组 + `#pragma unroll` 在部分 bisheng 版本上会触发后端 ICE（`Unsupported Inst must be hoisted`），必须改成具名变量
- tap 体必须按 `(fh,fw)` 编译期特化；动态 tap 循环的通用 VF 在较大 tap 数上比 classic 更慢（见 `tap-loop-invariant-vector-hoisting`）
- 数值路径必须保持 fp16 add-then-max 的舍入次序（先出 tap 和再取 max），否则与 golden 的位级一致不成立
- 被折的 tap 集合的地址必须能在同一份 UB 驻留数据上一次算清（见 `span-window-full-fh-residency`）

资源与硬件约束：

- 具名 filter 寄存器数量随 tap 数线性增长，tap 较多时超出寄存器文件，须分组或回退 classic
- 每 128 lane 一次 VF 调用；lane 数取真实 C 而非 Cp 对齐值

## 4. 泛化条件

- 策略作用域：op_class：morphology-window（max-plus 窗口归约）

适用：

- 算子主体是逐输出元素的 `max(tap 和)` 归约，tap 之间可结合（max 可交换/结合），因此可以折叠进同一寄存器
- V 管是绑定管（`aiv_vec_time / Duration` 接近 1）
- classic 体在同一位置的 UB 往返是每 tap 6 次，VF 形态只需 1 次 load + Add + Max
- fp16/bf16 直算链：低精度下 `Reg::Add` / `Reg::Max` 与 classic 同名接口位级一致

不适用：

- tap 数没有编译期特化：只能回退 classic
- 与 `tap-loop-invariant-vector-hoisting` 的分工：那张卡的主变量是“把 tap 循环里的不变量外提 + 编译期特化”，tap 体收缩为 Load+Add+Max；本卡的主变量是“把 classic 每 tap 的 UB 往返消成一次 load + 两条寄存器运算”，即累加器与 filter 全程寄存器驻留。两张卡常常一起用，但收益来源不同（前者削标量发射，后者削 UB 往返）。
- 与 `register-resident-compute` 的分工：那张卡讲“lane-local 计算链换载体”的一般结论（含长链在寄存器里反而变慢的边界）；本卡给出窗口归约这一类链的具体折叠形态与寄存器具名展开的工程约束。
- V 管不是绑定管：本机制只削 V 侧 UB 往返，对纯 MTE2 绑定形状无收益

## 5. 实施步骤

1. 把「每 tap 一次 classic Add + 一次 classic Max」改写成一个 `__simd_vf__` 调用：`acc` / `tmp` 两个 RegTensor + taps 个**具名** filter RegTensor
2. filter 具名寄存器在 VF 入口一次 `LoadAlign(t*filtStride + kOff)`，全列复用；禁止 `RegTensor` 数组
3. 列循环里每个 tap 只做 `LoadAlign(tmp, p + dy*rowStep + dx*dxStep)` → `Add(tmp,tmp,f)` → `Max(acc,acc,tmp)`；**第一个 tap 直接 Add 进 acc**，省掉一次 Max
4. 列末一次 `StoreAlign(out + i*cp + kOff, acc)`；acc 全程不落 UB
5. 按 128 lane 切通道 chunk，每 chunk 一次 VF 调用；lane 数取真实 C
6. 外层保留 TPipe/TQue/DataCopyPad 与工作分解不变，只替换计算体；逐例守住位级一致

## 6. LLM 前置问题

- 目标实现是否满足：逐输出元素的 `max(tap 和)` 归约、tap 可结合？
- 目标实现是否满足：V 管是绑定管（`aiv_vec_time / Duration ≥ 0.9`）？
- 目标实现是否满足：classic 体的 UB 往返是每 tap 6 次（Add 3 + Max 3）？
- tap 数是否小到能具名展开（具名寄存器数加上 acc/tmp 不溢出寄存器文件）？
- 是否命中排除条件：tap 数无编译期特化（须回退 classic）？
- 是否命中排除条件：V 管不是绑定管（收益归零）？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`op_class`
- 相关策略：`span-window-full-fh-residency`（前置条件）、`tap-loop-invariant-vector-hoisting`（同族，削标量发射）、`register-resident-compute`（载体切换的一般结论）

## 检索卡（短卡）

动作：把 max(acc, span+f) 的 classic 两步折进一次 VF 调用：acc 与 filter 具名寄存器常驻，每 tap 只 LoadAlign 一次
适用：逐输出点做 max(tap 和) 归约、tap 可结合；V 管绑定；tap 数可编译期特化
限制：acc 须在一个 VF 调用内跨全部 tap 存活；filter 须具名展开（数组+unroll 触发 ICE）；保持先 Add 后 Max 的次序
范围：形态学/滑窗/max-plus 归约类算子的逐 tap 归约环节
检索词：acc 寄存器驻留、具名 filter 寄存器、UB 往返消除、编译期 tap 特化、Reg::Add、__simd_vf__
机会：classic 每 tap 6 次 UB 往返（Add 2读1写、Max 2读1写），V 管被 UB 端口钉死
代价：寄存器压力上升；动态 tap 循环的通用 VF 更慢，必须门控回退
