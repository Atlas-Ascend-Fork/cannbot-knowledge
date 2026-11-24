---
type: Optimization
title: 稀疏权重表 Axpy 累积（gather-free 一维加权混合向量化）
description: 将逐元素标量 gather 与 FMA，改为使用稀疏权重表进行 Axpy 累积。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-sparse-weight-table-axpy-gatherfree-vectorization.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：稀疏权重表 Axpy 累积（gather-free 一维加权混合向量化）

> 单一优化点：kernel 里"按预计算索引表从 UB 行中取 2 个邻点做加权混合"的**逐元素标量循环**（GetValue/SetValue 主导、SCALAR pipe >90%），且向量 Gather API 不可用/不可靠时，把混合改写为**稀疏权重矩阵形式**：host 按 (输入长度, 输出长度) 预计算 W[in][outPad]（每列 ≤2 个非零权重，退化列自然和为 1），kernel 侧对每个输出向量做 `out = Σ_x Axpy(W[x], v[x])` 的向量累积，尾部用 Sub/Muls/Add 完成标量权重维度的混合——完全消除内层标量循环。

---

## 1. 原理

一维加权插值/混合 `out(o) = (1-w)·v[x0(o)] + w·v[x1(o)]` 的本质是对输入向量的**稀疏线性变换**。逐元素做（标量 gather 4 邻点 + 标量 FMA）时每输出元素付 4 次 S-pipe UB 标量读 + 1 次写；把变换矩阵显式化为 W[in][outPad]（x0 列存 1-w、x1 列存 w）后：

- 每个输入分量只贡献一个**标量广播系数**：`Axpy(dst, W[x], v[x], count)` 一条向量指令完成 `dst += W[x]·v[x]`；
- 内层从 `4×out` 次标量访存降为 `2×in` 次标量读 + `in` 次向量指令（in 通常 ≪ 4×out，上采样时差距更大）；
- 与逐元素方案相比 SCALAR pipe 让出主体，VEC pipe 接管（实测 SCALAR 93.9%→60.1%，VEC 0.1%→62.2%，kernel -38%）；
- W 表只依赖 (in_len, out_len) 与映射函数，host 一次生成、按 key 缓存到 NPU（与 tiling 同机制），kernel 每核 DataCopy 一次常驻 UB。

浮点求和顺序改变引入 ~1e-7 量级重排误差（fp32 容差内）；fp16 输入经 `Cast` 进 fp32 域计算再 `Cast` 出，中间精度与标量路径一致。

## 2. 性能问题模式

1. kernel 内层循环按输出元素逐个：索引整数运算（乘/除/取余）+ `GetValue`×2~4 + `SetValue`；msprof `aiv_scalar_ratio > 60%`（本例 93.9%）、VEC ≈ 0。
2. 索引表只依赖**静态维度对**（如 (in_len, out_len)），跨行/跨样本重复计算同一映射。
3. 向量 `Gather` API 缺失、或在当前工具链上验证不可靠（输出 UB 残留地址）。
4. 权重矩阵大小 `in_len × RoundUp32(out_len×4)B` 能装入 UB 预算（如 ≤96KB），超限需回退标量路径保正确性。

**不适用**：索引/权重依赖运行时数据（无法 host 预计算）；in_len 很大而 out_len 很小（W 表稀疏度低、向量短，Axpy 次数 = in 反而多）；输出通道本身已连续可整块向量计算（直接向量化更优）。

## 3. 正确性红线

本例踩坑实录（跨队列同步纪律）：`--cce-auto-sync=off`（或依赖手工事件）时，以下五组事件缺一即出现**非确定性数值错误**（小行数不触发、行多必现，极具迷惑性）：

1. **MTE2 → V**：DataCopy/DataCopyPad 搬入后，V 队列（Cast/Axpy/Add）读 UB 前。
2. **V → S**：`GetValue` 走 Scalar 队列。**`MTE2_S` 事件在本环境（AIV）未生效**——数据必须先"过水"成 V 队列产物（fp16 用 `Cast`、fp32 用 `Adds(dst, src, 0.0f)` 复制）再用 **V_S** 保证 S 读可见。
3. **V → MTE3**：向量写完输出行后，DataCopyPad 搬出前。
4. **V → MTE2（行尾）**：行循环复用输入行缓冲时，下一行 MTE2 写入必须等上一行 V 读 retire。
5. **MTE3 → V（行尾）**：下一行 V 写输出缓冲必须等上一行 MTE3 store 读 retire。

其他红线：
- W 表生成端的整数映射必须与被替换的标量路径**逐位一致**（同分子/分母/取整），否则边界列错位；
- W 表 pad 列全零，向量指令按 pad 长度全量发射是安全的（0×垃圾=0，但 NaN×0=NaN——pad 区只允许 0 权重，不允许读入未初始化数据参与**非零**权重）；
- dtype 模板分支必须 `if constexpr`（half/float 实例化交叉类型编译失败）。

## 4. 泛化条件

- 适用：一维 gather/加权混合类（resize/插值/重排/散射混合/任意"静态索引表 + 少量权重"变换），SCALAR 主导且 Gather 不可用。
- 前提：索引与权重是**静态维度**的纯函数，可 host 预计算并按维度对缓存；W 表 ≤ UB 预算（超限自动回退原路径，用 tiling.mode 之类开关）。
- fp16 算子需经 fp32 中间域（Cast in/out）保持精度。

## 5. 实施步骤

1. msprof 确认 SCALAR 主导 + 索引映射静态可预计算。
2. host 生成 W 表（整数映射与标量路径逐位一致），按 (in, out) key 缓存 NPU；kernel 签名加 W 表 GM 指针；tiling 加 mode 字段与 UB 预算门控（超限回退标量路径）。
3. kernel：每核一次 DataCopy W 表到 UB（行 32B 对齐 → 行 stride = RoundUp32(out×4)/4 元素）；每行 Duplicate 清零 → `for x in in_len: Axpy(accum, W[x], v[x])` → Sub/Muls/Add 完成标量维混合 →（fp16）Cast out。
4. 按红线补齐五组跨队列事件；dtype 分支 `if constexpr`。
5. 验证：与标量路径/参考实现逐位比对（多 shape × 多轮重复，抓非确定性竞争）+ pipe 前后对比 + 官方 bench。

## 6. LLM 前置问题

- SCALAR 占比多少？索引映射是否只依赖静态维度对？
- W 表尺寸 in×outPad×4B 是否 ≤ UB 预算？超限的回退路径是什么？
- 行循环是否复用输入/输出缓冲（决定行尾 V_MTE2/MTE3_V 是否必需）？
- GetValue 读的数据是否为 V 队列产物（决定 V_S 过水是否必需）？
- 精度容差是否容纳求和重排误差（~1e-7）？

## 7. 验收标准

- build + 精度全过；resize_bilinear（910B3，官方 bench + msprof）：kernel 15.24µs → 9.50µs（-38%），SCALAR 93.9%→60.1%，VEC 0.1%→62.2%；device-bound case（10 行/核）E2E 27.8µs → 17.8µs；geo_speedup 2.94x → 3.03x；精度 9/9 全过 + 5×8 重复数值验证零竞争。

## 检索卡（短卡）

动作：将逐元素标量 gather 与 FMA，改为使用稀疏权重表进行 Axpy 累积。
适用：SCALAR 路径主导、Gather 不可用，且索引映射可静态预计算。
限制：host 生成的 W 表中，整数映射须与标量路径逐位一致。
范围：一维 gather、resize、插值、重排及散射混合路径。
检索词：稀疏权重表、Axpy、标量 gather、FMA、静态索引表、W 表
机会：内层逐输出执行索引乘除取余，并多次 GetValue、SetValue。
