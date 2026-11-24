---
type: Optimization
title: direct UB 指针访问（绕过 LocalTensor 标量 GetValue/SetValue，~18ns → ~1-2ns）
description: 将热点标量循环的 LocalTensor GetValue/SetValue 攓为 GetPhyAddr 后的直接 UB 指针访问。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-direct-ub-pointer-scalar-bypass.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：direct UB 指针访问（绕过 LocalTensor 标量 GetValue/SetValue，~18ns → ~1-2ns）

> 单一优化点：把热点标量循环里的 `LocalTensor::GetValue/SetValue`（每 op 含边界检查/类型转换等 API 开销，实测 ~18ns）替换为 `GetPhyAddr()` + `__ubuf__` **直接指针解引用**（~1-2ns），对"命中数很多的标量 RMW"循环获得 10× 常数级加速；配合展开（见 33）可进一步流水化。

本策略适用于任何"标量逐元素读/写 UB"是热点的 kernel（scatter RMW、gather 命中处理、稀疏累加、per-token 标量逻辑等），与具体算子无关。

---

## 1. 原理

`LocalTensor::GetValue/SetValue` 是通用 API：每次调用含下标换算、类型转换、边界/越界检查等；在"每元素都要调几次"的热点循环里，这个 API 开销（实测 ~18ns/op）成为瓶颈，而不是 UB 访问本身。

`GetPhyAddr()` 返回 UB 基址的裸指针，转成 `__ubuf__ T*` 后 `ptr[i]` 就是一次直接 UB 访存（~1-2ns），跳过 API 层。对 scatter 这类"命中数 = 数十万 ~ 百万"的 RMW 循环，10× 常数差就是几十 ms → 几 ms。

与 33（向量化过滤压缩）配合时，压缩后的命中是连续 run，direct 指针按 `relAddr[base+lane]` 顺序解引用，还能让标量 LSU 流水化 8 个背靠背 load（显式 load→op→store 三段），消除 load-after-load 依赖。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. 热点循环每元素调用 ≥2 次 `GetValue/SetValue`（如 `idx=idxLocal.GetValue(j); val=updLocal.GetValue(j); yLocal.SetValue(l, ...)`）。
2. profiling：SCALAR pipe 高，但代码没有复杂标量算术——耗时在 API 调用本身。
3. 由 `GetValue/SetValue` 的耗时反推每 op ~10-20ns（对比：同量级元素数下 direct 指针应快 ~10×）。
4. 命中 RMW 循环体短（每个 op 就几次调用），API 开销占比大。

不适用：标量访问次数很少、非热点；循环本身可全向量化（应先向量化，而不是优化标量）；有符号/越界保护需求强依赖 LocalTensor 语义的调试场景。

## 3. 正确性红线

- **地址与视图类型必须匹配**：`GetPhyAddr()` 返回字节地址，按 `sizeof(T)` 与访问类型解引用；int64/bf16 等视图（如 `ReinterpretCast`）的指针步长必须与视图类型一致，否则越界/错位。
- **同步不变**：direct 指针访问不改变同步语义——UB 数据由 MTE2 搬入后仍需 MTE2→S 同步才能读，V 写后仍需 V→S 同步才能读；只是把"读/写"本身换成了裸指针，同步点不能省。
- **尾/对齐**：遍历 `[base, base+count)` 的 count 必须精确（不越界到其他 buffer）；staging 行有 padding 缝隙时，指针索引按行步长（含 pad）而非元素数。
- **别名与顺序**：裸指针写 `xAddress[rel[i]]` 是随机写，多个 rel 指向同一位置时编译器可能重排（须保持与 LocalTensor 相同的 per-lane 顺序语义——用显式 load/op/store 三段或组内重复探测保证）。
- **可移植性**：`__ubuf__` 是 AscendC 扩展；改回 LocalTensor 语义时功能不变（性能下降），确保代码结构可回退。

## 4. 泛化条件

适用（任一）：
- 热点循环每元素多次 `GetValue/SetValue`，且无法整体向量化（必须标量处理的部分）；
- 命中/目标数大（数十万以上），API 开销 × 次数主导耗时；
- 已用 33 压缩出连续命中 run，需要高效顺序读取。

不适用（任一）：
- 循环可整体向量化（应先向量化，direct 指针是最后的常数优化）；
- 标量访问次数少、非热点；
- 需要 LocalTensor 的边界保护做防御性编程的场景。

## 5. 实施步骤

1. 用 profiling 确认 SCALAR 热点来自 `GetValue/SetValue` 次数多（不是算法本身）。
2. 对热点 buffer：`auto addr = reinterpret_cast<__ubuf__ T*>(tensor.GetPhyAddr());`，用 `addr[i]` 替换 `tensor.GetValue(i)` / `tensor.SetValue(i, v)`。
3. 保持同步点（MTE2→S、V→S 等）不变；遍历 count 精确。
4. 配合展开：8 宽 group 显式 `load(8) → op → store(8)`，让标量 LSU 流水化。
5. 全量编译、精度全过、多次取样性能；对比 GetValue 版本确认 ~10×。

## 6. LLM 前置问题

- 热点循环每元素调几次 `GetValue/SetValue`？这些访问能否整体向量化？
- `GetPhyAddr()` 的视图类型与访问类型、步长（含 padding）是否匹配？
- 同步点（MTE2→S / V→S）是否在替换后保持？随机写别名顺序是否保持？

## 7. 验收标准

- 精度：全量用例通过（含 padding 缝隙、尾精确、int64/bf16 视图路径）。
- 性能：热点标量循环 ~10× 加速（scatter 案例命中 RMW 从 ~15ns/op 降到 ~2ns/op）。
- 结构：热点循环无 `GetValue/SetValue` 调用。

## 检索卡（短卡）

动作：将热点标量循环的 LocalTensor GetValue/SetValue 攓为 GetPhyAddr 后的直接 UB 指针访问。
适用：适用任一：无法整体向量化且每元素多次标量API；或大量命中使API调用开销主导。
限制：GetPhyAddr 返回字节地址，视图类型、sizeof(T) 与解引用访问类型必须匹配。
范围：无法整体向量化的 UB 热点标量循环。
检索词：LocalTensor、GetValue、SetValue、GetPhyAddr、__ubuf__、reinterpret_cast。
机会：热点循环多次标量API调用，API开销可能主导；需profiling确认并排除算法本身。
