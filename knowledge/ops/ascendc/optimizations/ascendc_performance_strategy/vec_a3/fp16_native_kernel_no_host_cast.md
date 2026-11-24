---
type: Optimization
title: fp16 host 双 cast 下沉 kernel（native half 进出 + 类型系统陷阱清单）
description: 取消 fp16 的 host 双 cast，改由 kernel 接收 half、内部转 f32 后复用 f32 主路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-fp16-native-kernel-no-host-cast.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：fp16 host 双 cast 下沉 kernel（native half 进出 + 类型系统陷阱清单）

> 单一优化点：fp16/bf16 输入的算子若在 host 上 `.to(float)` 进 kernel、结果再
> `.to(half)`，两次全量 elementwise kernel launch（各 ~40-50us）主导小 N 端到端耗时。
> 给 kernel 加 native half 实例（half 直进直出，kernel 内转 f32 复用现有路径），
> P7 (n=48) 端到端 310→156us。

适用于任何 fp16/bf16 输入、内部以 f32 逻辑计算的直 launch 算子。

---

## 1. 原理

- 两次 host cast = 2 次全量 GM 往返 + 2 次 launch 开销；小 N 时 launch 开销占比 ~60%。
- kernel 内 half→f32 标量转换（n 次循环）对小/中 n 的成本 ≪ 两次 launch；转换后完全
  复用 f32 主路径（检测/直方图/radix 不变）。

## 2. 性能问题模式

- pybind/plugin 层出现 `xIn.to(at::kFloat)` 与 `result[0].to(at::kHalf)` 成对调用。
- 小 N case 端到端 ≫ 净 kernel 时间，差值固定 ~80-100us。

## 3. 正确性红线（CANN 9.0 / dav_c220 的 half 类型系统陷阱，全部实际踩过）

1. **类型名是全局 `half`**（`struct half`，kernel_fp16.h，有 float 构造/转换）——本环境
   **没有 `AscendC::half_t`**；`__fp16`（编译器内建）能编译但与向量 API 模板特化不匹配，
   产生**位宽错位数据**（f32 bits 被按 half 读）。
2. **向量 Cast 没有 half 数值语义**（编译通过但不做数值转换）；正确的 half↔float 向量
   转换在 DataCopy 的 dtype-conversion 特化里，但带 8 元素对齐约束（通用 n 尾部难处理）。
   **标量 `static_cast<float>(half)` / `static_cast<half>(float)` 最稳**。
3. half staging 目标与 f32 转换目标**不能同 buffer 原地扩张**（dst[i] 覆盖未读的
   src[j>i]）——half 落 idx1 空闲区再转 key0。
4. radix 路径的 vals 若是 int32 buffer 里的 **f32 bits**：float 视图即真实值（bit 重解释），
   **不能**对 int32 做数值 Cast（0x40E00000 会转成 1192755200.0f）。
5. pybind 的 static 辅助函数前向声明若落在 namespace 外，产生未定义符号——把函数定义
   放在被调用位置之后。

## 4. 泛化条件

- **适用**：小/中 N（n 次标量转换 ~15c/元素可忽略）的 half/bf16 输入直 launch 算子。
- **不适用**：超大 N（应改用 DataCopy 转换特化并处理 8 元素对齐尾部）；bf16 未验证（同构）。

## 5. 实施步骤

1. kernel 模板加 `kIsHalf` 标记：staging 用 `Get<half>()`（落空闲 idx buffer）。
2. 标量循环 `f32[i] = float(half[i])` 后复用 f32 全路径。
3. 输出 vals：直方图路径 int32 数值 → float → half 两级标量；radix 路径 f32 bits 视图
   → half 一级标量。
4. pybind：kHalf 直传直出，删除两次 .to()。

## 6. LLM 前置问题

- host 侧是否存在成对的 `.to(at::kFloat)` / `.to(at::kHalf)` 调用，小 N 端到端与净 kernel 差值是否 ~80-100us？
- 目标环境是否有全局 `half` 类型（而非 `AscendC::half_t` 或 `__fp16`）？
- N 规模是否属于小/中段（n 次标量转换成本可忽略）？
- 输出 vals 走直方图（int32 数值）还是 radix（f32 bits 视图）路径？

## 7. 验收标准

- build + 精度全过；P7 (n=48 fp16)：310→156us（1.02x→1.65x）。精度覆盖 fp16 随机值/负数/分数/all-same/N=1。

## 检索卡（短卡）

动作：取消 fp16 的 host 双 cast，改由 kernel 接收 half、内部转 f32 后复用 f32 主路径。
适用：适用于小或中等 N 的 half/bf16 输入直 launch 算子。
限制：超大 N 不适用；应采用 DataCopy 转换特化，并处理 8 元素对齐尾部。
范围：half/bf16 输入直 launch 算子的类型转换路径。
检索词：host 双 cast、half→f32、kIsHalf、DataCopy、直 launch
机会：pybind/plugin 层成对出现输入转 float 与结果转 half。
代价：小中规模下 kernel 标量转换成本低于两次 launch；超大规模不适用。
