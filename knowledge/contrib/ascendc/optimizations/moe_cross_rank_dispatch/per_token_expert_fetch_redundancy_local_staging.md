---
type: Optimization
title: "MegaMoE 跨卡 dispatch：按 (token, expert) 取数产生 topk×(LOCAL_E/E) 冗余，首用本地暂存可消除"
description: "arch35 (Ascend950DT) 融合 MegaMoE 上实测：跨卡 dispatch 按 (token,expert) 粒度取数，一个 token 路由到本卡 N 个专家就跨卡取 N 次，冗余倍数 = topk×(LOCAL_E/E)（topk=8,E=16,W=2 时为 4.0×）。首次取后本地暂存、其后本地读，五个 shape 全部 ratio>1.0，几何平均 1.1325，输出逐位相同。附不适用边界：大 FFN 下 dispatch 被 GMM1 完全遮蔽，该优化结构性无收益。"
tags: [task.optimization, topic.mixture_of_experts, topic.data_movement.communication.collective_communication, topic.performance.optimization.optimization_overview]
status: stable
platforms: ["950"]
created_at: "2026-10-08T09:30:00Z"
updated_at: "2026-10-08T09:30:00Z"
sources:
  - resource: https://gitcode.com/cann/ops-transformer/blob/6f0d3ec620b338cab4f2d00322ff2e0d141419d2/mc2/mega_moe/op_kernel/arch35/mega_moe.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/6f0d3ec620b338cab4f2d00322ff2e0d141419d2/mc2/mega_moe/op_host/op_tiling/mega_moe_tiling.cpp
    role: supporting
---

# MegaMoE 跨卡 dispatch 去重：(token,expert) 取数冗余与本地暂存

## 结论

**在 arch35 融合 MegaMoE（BF16、CANN 9.1.0、EP=2）上**，跨卡 dispatch 的取数粒度是
**(token, expert)**：一个 token 若被路由到本卡的 N 个本地专家，它的 hidden 行就**跨卡被取 N 次**。

```
冗余倍数 = topk × (LOCAL_E / E)
         = 8 × (8/16) = 4.0×        # topk=8, E=16 全局专家, W=2, 每卡 8 专家
```

**消除方式**：该 token 行**首次**被取时在本地暂存一份，其后本地读。暂存区按与对端 window
**完全相同的行布局**镜像（H=7168 时两者均为 7392 B/行），因此它可直接替换
`remoteRankGlobalTensor`，而 `tokenRev` 的写入、以及 GEMM 的稠密 `MakeLayoutA` 都不受影响。

```
stageRowBytes = CeilAlign(CeilAlign(H,256) + CeilDiv(H,32), 32)     # H=7168 -> 7392 B
staging       = (W-1) × bs × stageRowBytes                          # W=2,bs=512 -> 3,784,704 B
```

## 实测证据

同窗口回文轮转、按 half-block 配对，每个 shape 自带阳性对照：

```
shape  H     2*FFN  topk   ctrl ms   cand ms   ratio
S1     7168   2048    8    1.41745   1.17865   1.2026
S2     7168   1024    8    1.44242   1.12208   1.2855
S3     7168   7168    8    1.58088   1.53690   1.0286
S4     4096   2048    6    0.67326   0.58397   1.1529
S5     4096   7168    6    0.76391   0.75180   1.0161
                           ratio>1.0: 5/5      几何平均 1.1325
```

- **输出逐位相同**：23 次运行 × 3 个 binary，同一 digest；非容差比较。
- **分母对齐**：算子外还有 router（gate GEMM+softmax+topk，约 71–77 us 的**固定绝对**开销）。
  把它计入分母后 S2 1.2846→1.2689、S1 1.2020→1.1902、S4 1.1603→1.1445，
  **稀释 1~1.4%，通过/不通过集合不变**。
- **存储代价**：3.78 MB（上式 W=2,bs=512,H=7168），占 96 GiB 卡的 **0.0037%**。

## ⚠ 不适用边界（负知识，与结论同等重要）

**dispatch 跑在 AIV 的兄弟 sub-block 上，与 GMM1 并发**（dispatch 在 `subBlockIdx_==1`，
GMM1 在 `subBlockIdx_==0`，循环体内无逐专家 barrier，另有 6 级 dispatch buffer 软流水）。
因此：

```
FFN 越大 -> GMM1 越长 -> dispatch 被遮蔽得越彻底 -> 去掉它的跨卡流量也省不出时间
```

**绝对节省量**（不是比值）直接显示这一点——若只是 Amdahl 摊薄，绝对节省应当不变：

```
H=7168:  2FFN=1024 -> 320.3us    2048 -> 238.8us    7168 -> 44.0us
H=4096:  2FFN=2048 ->  89.3us    7168 -> 12.1us
```

**节省量本身在塌缩，不是被摊薄**，这是"被遮蔽"的签名。排序 `S3 < S1 < S2` 在测量前即已
预注册并应验。

⇒ **在 2FFN ≥ 7168 一类的大 FFN shape 上，这条路径结构性无收益（S3 1.0286 / S5 1.0161），
不是没调好。** 要在那里取得收益必须换机制，而不是继续调这一条。

## 适用条件

- 跨卡 dispatch 按 (token, expert) 取数，且 `topk × LOCAL_E/E > 1`（冗余存在）
- 允许 `(W-1) × bs × stageRowBytes` 的额外 device 内存（实测量级为 MB）
- 暂存区能与对端 window 行布局**逐字节一致**，否则下游稠密 layout 假设会被破坏
