---
type: Optimization
title: per-token 标量参数从全局内存直接读取
description: 删除标量的UB缓冲、全局到片上搬运及MTE2屏障，改为逐token从全局内存直接读取
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/per-token-scalar-gm-getvalue.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：per-token 标量参数从全局内存直接读取

单一优化点：当融合算子有 per-token（逐行）的标量参数（如逐 token 的缩放系数），且该标量在每行计算中只参与一次广播运算时，直接从全局内存用标量 GetValue 读取（scalar pipe），而不是把整批标量预先搬入 UB 再逐行取，省去一次 MTE2 搬入 + UB 占用 + 同步屏障。

## 1. 原理
per-token 标量参数（每 token 一个标量）每个 token 一个值。整段搬入 UB 需一次 MTE2 搬运 + UB 占用 + MTE2 同步屏障，且与主流水缓冲争用 UB。直接从全局 GetValue（标量读，走 scalar pipe）每次取当前 token 标量，零 UB 占用、零额外搬入、与 V 流水不争用。

## 2. 性能问题模式
- 把 per-token 标量数组整段从全局搬入 UB（一次 MTE2 搬运），随后逐行从 UB 取标量。
- 引入：一次额外 MTE2 + UB 占用（N 个标量）+ 一个 MTE2 同步屏障（阻塞后续 V），并与主流水输入/输出缓冲争用 UB 空间。

## 3. 正确性红线
- GetValue 读全局标量是 scalar pipe 操作，与 V 的标量广播（如逐元素 Muls）配合时，标量读取须在 V 操作前完成（scalar 读→V 用，自然有序）。
- 索引必须是全局 token 行号（核内起始行 + 块内行偏移）。
- 仅适用 per-token 标量（每行一个标量）；向量参数（每行多元素）不适用，仍须搬入。

## 4. 泛化条件
- 参数是 per-token 标量（每 token 一个标量）。
- 标量在每行计算中参与广播运算（如逐元素乘）。
- 标量数组在全局内存（未驻留 UB）。

## 5. 实施步骤
1. 识别 per-token 标量参数（如逐 token 缩放系数）。
2. 删除该参数的 UB 缓冲分配 + 全局→片上搬运 + MTE2 同步屏障。
3. 逐行计算中，用全局 token 行号从全局直接 GetValue 取标量。
4. 用该标量做逐元素广播运算。

```text
# before: stage scalar array to UB (MTE2 + barrier), then index UB per row
# after:
for each row r:
  scalar = global_scalars.GetValue(global_row_index(r))   # scalar pipe, zero UB
  Muls(buf, buf, scalar, row_len)                          # broadcast
```

## 6. LLM 前置问题
- 参数是否 per-token 标量（每行一个标量）？还是向量（每行多元素）？
- 标量是否在全局内存？每行是否只用一次广播？
- 是否有其他已搬入 UB 的逐行不变量（那些仍可循环外一次搬入长驻）？

## 7. 验收标准
- build 通过；精度全 case 通过。
- 性能：相对"整段搬入 UB"基线延迟下降（省一次 MTE2 + UB + barrier）。
- UB 占用减少。

## 检索卡（短卡）

动作：删除标量的UB缓冲、全局到片上搬运及MTE2屏障，改为逐token从全局内存直接读取
适用：参数是未驻留UB的逐token标量，且每行仅参与一次广播运算
限制：GM GetValue经scalar pipe；须保持标量读取与V广播消费的先后顺序
范围：融合算子的逐token标量广播路径
检索词：per-token标量、GM GetValue、scalar pipe、MTE2屏障、UB缓冲
机会：标量数组先整段搬入UB，再逐行取值
