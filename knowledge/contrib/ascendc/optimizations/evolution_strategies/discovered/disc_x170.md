---
type: Optimization
title: "X170: 精度 gate 单元素污染的排查：先确认 host 是否读错地址"
description: "当精度 gate 稳定出现单个元素污染，而其余元素逐位一致时，先判断错值是否是另一个输出的合法值，再用 device PRINTF 对比 UB/写后 GM 回读与 host 读到值；若设备侧正确而 host 错，检查 ref→cand 之间是否缺少 torch.npu.synchronize()。换内核写法无效而 host 时序 A/B 可稳定复现，即可判定为分配器/流竞态而非数值缺陷。"
tags:
  - task.debugging
  - topic.precision
  - topic.attention
status: draft
sources: []
created_at: "2026-10-29T06:00:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X170: 精度 gate 单元素污染的排查：先确认 host 是否读错地址

## 判据（先做这一步，通常很快能结案）
1. **看错值是不是「另一个输出的合法值」**：把 host 读到的错值拿去和本 case 的其它输出（lse / 中间量 / 上一次迭代的结果）比。若错值恰好等于某个本应存在但该路径并不写出的量，则一定是读错了地址，不是算错了数。
2. **在 kernel 侧现场取证**：对失败 case 打 `PRINTF`，同时打印 (a) UB 里的结果、(b) 写完 GM 后立即回读的值。若两者都正确而 host 仍读错 → 内核无罪。
3. **做 host 时序 A/B**：把官方 harness 的执行流程逐行镜像，只删/加 ref→cand 之间的 `torch.npu.synchronize()`。若去掉 sync 就稳定复现、加回就逐位通过 → 是分配器/流竞态，不是数值问题。
4. **反证**：换三种内核侧写法（`DataCopyPad` / 严格 32B `DataCopy` / `SetValue` 标量直写），若现象完全不变，就是内核对这个字没有控制权。

## 后果与处置
- 这条「缺陷」在官方精度 gate 下**不可交付**（gate 用的正是该 harness），即使内核是对的。要交付只能从 host/运行时侧绕（例如让另一个输出的分配不与 out 相邻，或在自己的 wrapper 里补一次 sync），且必须写明理由与风险。
- 反面教训：连续多轮把「换 softmax 写法 / Fill 目的缓冲 / 加 PipeBarrier」当作修复手段，都是在扰动调度；这类尝试若只在子集上通过、全量仍败，应立即转做上面的第 1、2 步。
- 这类问题不是内核数值缺陷，不要尝试用更高精度或改算法来"修"。

## 适用场景
- 精度 gate 出现单元素/少量元素污染，且污染位置固定（例如 flat index 0），其余元素逐位一致。
- 使用多流或异步执行的 host harness；ref 与 cand 之间是否同步是重点怀疑对象。

## 验证方法
- 打印错值的十六进制与浮点表示，和同 case 的其它输出逐项比对。
- device PRINTF 覆盖"计算完成 → 写 GM → host 读回"三个点。
- host A/B：只加/删 sync，重复多次，统计复现率。
- 修 host 后跑全量精度 + 重复 launch 稳定性。

## 关联
- 与 [X171](disc_x171.md)（首 launch 残留 UB / 完成标志陷阱）同属"设备侧正确、主机侧读错"的静默错误。
- 与 [X161](disc_x161.md)（跨 launch 竞态）共享"单跑 PASS 不足以证明正确"的门禁思想。
