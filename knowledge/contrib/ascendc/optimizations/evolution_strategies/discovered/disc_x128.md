---
type: Optimization
title: "X128: decode KV gather 的槽信用时序诊断"
description: "预取 chunk t+1 写入槽 (t+1)%k_slots，该槽的上一读者是 C2(t+1-k_slots)（在迭代 t+1-k_slots+PRELAUNCH 执行）；当 k_slots=3、PRELAUNCH=2 时，上一读者就是本迭代刚执行的 C2(t-2)，gather 必须等同迭代 C2 归还信用，发车点被钉在迭代尾。该关系可把「MTE2 空转」拆成请求率不足与消费者等待两个变量，但扩大槽数受 L1 容量约束。"
tags:
  - task.optimization
  - topic.attention
  - topic.data_movement
status: draft
sources: []
created_at: "2026-10-27T16:00:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X128: decode KV gather 的槽信用时序诊断

## 核心思路
在"slot 持久块 + K 多槽轮转"的 paged-decode 中，预取 chunk t+1 写入槽 `(t+1) % k_slots`，该槽的**上一读者**是 chunk `t+1-k_slots` 的 C2（PV 读 V，V 复用 K tile）。C2(tc) 在迭代 `tc+PRELAUNCH` 执行，于是：

- `k_slots=3, PRELAUNCH=2` → 上一读者是 `C2(t-2)`，恰好排在本迭代 C1 之前刚跑完 → gather 的 MTE2 必须等同迭代 C2 归还信用，**发车点被钉在迭代尾部**，与 C1 的 mma 重叠窗口接近零。
- `k_slots=4, PRELAUNCH=2` → 上一读者退到 `C2(t-3)`（上一迭代）→ 信用在迭代头即归还，gather 可以整迭代提前。

因此，"MTE2 空转"至少有两个可分别验证的来源：请求率不足，以及**消费者信用等待**。先算清上一读者所在的迭代，再决定是加槽、改 chunk 宽，还是改预取位置。

## 适用场景
- paged / gather 型 KV 读 + 多槽 L1 轮转 + CV 环的 decode attention。
- 判据：per-chunk 时间呈两档，且与 KV 总量或页表规模相关；同时理论字节/带宽算出的下限明显低于实测。
- 扩大槽数受 L1 容量约束：`槽数 * tokens_per_chunk * dqk * sizeof(dtype) <= L1 预算`。必要时缩小 chunk 宽（tokens_per_chunk）来换槽数。

## 实现要点
1. **先算 slot 字节数，再决定 chunk 宽**：`slot_bytes = tok * dqk * sizeof(dtype)`；用 `floor(L1_budget / slot_bytes)` 得到可行槽数。缩小 chunk 宽会改变 K/V 的 DMA 形状，需同步检查 burst 效率。
2. **tok 运行期化的成本可控但站点多**：若把 `TOK` 从编译期常量改为运行期取值，需要同步 cube/vec/kernel 三侧的所有使用点，并处理少数不能运行期化的常量（例如显式传参、`constexpr` 改 `const`、固定大小数组、局部 `#undef`）。
3. **K 槽寻址数组化**：把 `if (s==0)/if (s==1)/else` 改成 `k_l1[s * tok * dim_align]`；事件 id 也要随槽数扩展，并避开 P 载入等已有 id。每个 id 的 Set/Wait 必须严格交替。
4. **fast-path 判据不要绑定固定 tok**：若 gather 快路径用 `page_size == TOK/8` 之类的判据，tok 变化后所有 case 会退化到慢路径。应改成与 tok 无关的页大小判据（例如"每 16-token 组恰一页"），并为不满足该判据的页大小准备慢路径单测。
5. **慢路径的地址计算要单独验证**：槽视图偏移 + `DataCopyPad` 的 2D 目标地址在非标准页大小下可能越界。先用合成微基准覆盖 `page_size` 的各个取值，再上真实 shape。

## 边界与风险
- 本卡首先是一个**诊断关系**，不是"加槽一定更快"的结论。加槽可能被 L1 容量、DMA burst、P 环深度等其它约束抵消。
- 若无法为所有 `page_size` 提供正确慢路径，应保留原 chunk 宽，不要为了加槽牺牲正确性。

## 验证方法
- 用 per-chunk 时间表确认两档现象，并用理论字节/带宽计算排除"请求率不足"。
- 对每个 `page_size` 构造微基准；对 tok 运行期化的每个使用点做编译期检查。
- 同设备同窗口 A/B，观察 gather 发车点是否从迭代尾移到迭代头（可用 msprof 或轻量时间戳）。

## 关联
- 与 [X127](disc_x127.md)（RING/PRELAUNCH 约束）和 [X172](disc_x172.md)（MLA decode 分档）配合使用。
