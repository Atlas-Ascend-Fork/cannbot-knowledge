---
type: Guide
title: Flash Attention 的任务切分与流水排布
description: 说明按 Q 块分核、核内遍历 KV，以及 QK、softmax、PV、输出累加的三槽连续流水。
tags:
- task.design
- task.implementation
- topic.tiling
- topic.memory
status: stable
sources:
- resource: https://github.com/tile-ai/tilelang-ascend/blob/bb4d4de55fde9830a70b3e9001a65fb6bf7a4381/examples/flash_attention/fa_opt/expert_v3/kernel.py
  role: primary
- resource: https://github.com/tile-ai/tilelang-ascend/blob/bb4d4de55fde9830a70b3e9001a65fb6bf7a4381/examples/flash_attention/fa_opt/expert_v3/kernel.tl
  role: implementation
- resource: https://github.com/tile-ai/tilelang-ascend/blob/bb4d4de55fde9830a70b3e9001a65fb6bf7a4381/examples/flash_attention/fa_opt/expert_v3/README.md
  role: supporting
created_at: '2026-10-20T07:44:06Z'
updated_at: '2026-10-30T03:11:40Z'
platforms:
- a3
aliases:
- flash_attention
- expert_v3
---

# Flash Attention 的任务切分与流水排布

## 任务切分

每个 batch、每个 Q head 下的一个 Q 块对应一个独立任务，负责这些 Q 行的完整输出。不同 Q 块之间没有依赖，可以分核并行；一个任务内顺序遍历所有 KV 块，更新 online softmax 的最大值、指数和与输出累加值。

`expert_v3` 使用 Q256、KV512、D128，将任务均衡分配给 24 个核，每核领取一段连续任务。

以下骨架仅适用于非因果 MHA/GQA，FP16 输入输出、D=128，Q/KV 长度分别为 256/512 的整数倍，Q head 数能被 KV head 数整除。骨架未展示 causal mask、尾块 mask 或 padding，不能仅改为 ceil-div 就用于任意长度。

```python
assert batch > 0 and heads_kv > 0 and heads_q % heads_kv == 0
assert dim == 128 and nq > 0 and nk > 0
assert nq % 256 == 0 and nk % 512 == 0
query_tasks = nq // 256
all_tasks = batch * heads_q * query_tasks
task_base, task_remainder = divmod(all_tasks, 24)

with T.Kernel(24, is_npu=True) as (cid, vid):
    my_start = cid * task_base + T.min(cid, task_remainder)
    my_tasks = task_base + T.if_then_else(cid < task_remainder, 1, 0)
    # 本核依次处理 my_start 开始的 my_tasks 个 Q 块
```

一个 Cube 与两个 Vector 子块协作处理一个 Q 块，两个 Vector 各负责 128 行。Q 留在 L1 供各轮 QK 复用；FP32 输出累加值留在 UB，直到最后一个 KV 块处理完才归一化并写出。

来源记录的验证环境为 Atlas A3 `Ascend910_9392`、CANN 9.1、TileLang-Ascend 提交 `4c7267018af02284ff28f1cd090a1492c7985bed`；本指南未另行执行设备验证，不扩展到其他工具链或硬件。

## 四个阶段

每个 KV 块依次经过四个阶段：

| 阶段 | TileLang 函数 | 工作 |
|---|---|---|
| C1 | `cube_qk` | 计算 QK，将 score 写到 GM 工作区 |
| V1 | `vec_softmax_strip` | 更新最大值，计算未归一化的 P、行和及重缩放系数；外层用 `vec_store_packet` 写出 P |
| C2 | `cube_pv` | 计算 PV，将本轮输出贡献写到 GM 工作区 |
| V2 | `vec_merge_o_tile` | 重缩放旧累加值，合入本轮贡献，更新归一化分母 |

同一块遵守 `C1 → V1 → C2 → V2`；不同块的阶段可以交错。V1 与 V2 分开执行，因此每一块的行和与重缩放系数也要保存到对应槽位，不能被后续 V1 提前覆盖。

## Prelaunch 与三槽流水

各 KV 块的 QK 只依赖 Q/K 输入，不依赖前一块的 softmax 或输出累加，因此可以提前计算后续块的 QK。这样 Vector 处理前一块 softmax 时，Cube 可以计算后续块 QK；P 就绪后再穿插 PV，减少 Cube 与 Vector 相互等待。三槽保存不同轮次的中间结果，让生产与消费错开，而不必每块都串行做完四个阶段后才开始下一块。

源码用 `NUM_STAGES=3` 同时表示固定调度延迟和工作区槽数。将本核所有任务的 KV 轮次展平后，`packets = my_tasks * kv_blocks`；启动阶段最多生产 `min(3, packets)` 个有效 QK/softmax packet，再延迟消费对应的 PV/输出贡献。主体骨架为：

```python
NUM_STAGES = 3
with T.Scope("C"):
    cube_init()
    for step in T.serial(packets + NUM_STAGES):
        stage = step % NUM_STAGES
        if step >= NUM_STAGES:
            old = step - NUM_STAGES
            cube_prepare_v(...)             # 提前搬 old 对应的 V
            T.wait_cross_flag(P_READY)
            cube_pv(...)                    # C2(old)，使用 stage 槽
            T.set_cross_flag("FIX", O_READY)
        if step < packets:
            kv = step % kv_blocks
            if kv == 0:
                cube_begin_q(...)           # 新 Q 任务，加载 Q
            cube_qk(...)                    # C1(step)，使用 stage 槽
            T.set_cross_flag("FIX", S_READY)
    cube_finish()
    T.wait_cross_flag(VECTOR_DONE)

with T.Scope("V"):
    ...
    for step in T.serial(packets + NUM_STAGES):
        stage = step % NUM_STAGES
        if step >= NUM_STAGES:
            old = step - NUM_STAGES
            T.wait_cross_flag(O_READY)
            for half in T.unroll(2):
                vec_load_packet(...)
                vec_merge_o_tile(...)       # V2(old)，每次处理 64 行
                if old % kv_blocks + 1 == kv_blocks:
                    vec_store_packet(...)   # 最后一个 KV 块，写最终 O
        if step < packets:
            T.wait_cross_flag(S_READY)
            for strip in T.serial(8):
                vec_load_packet(...)
                vec_softmax_strip(...)      # V1(step)，每次处理 16 行
                vec_store_packet(...)
            T.set_cross_flag("MTE3", P_READY)
    ...
    T.set_cross_flag("MTE3", VECTOR_DONE)
```

前 3 个调度步不消费，末尾 3 个调度步不生产；两者重叠时存在空步，不能视为各有 3 轮有效计算。生产、消费分别受 `step < packets` 和 `step >= NUM_STAGES` 保护，不得删除；`packets=0` 的核不执行有效计算。两者同时满足时，Cube 做 `C2(step-3) → C1(step)`，Vector 做 `V2(step-3) → V1(step)`。实际调用按 `step` 或 `old` 计算任务、KV 地址与行偏移；这里保留调度和跨核交接，省略函数参数。

`S_READY` 由 FIX 在 score 写完后发出，Vector 等待后读取；`P_READY` 由 MTE3 在 P 写完后发出，Cube 等待后读取；`O_READY` 由 FIX 在 PV 结果写完后发出，Vector 等待后合入输出。结束时 Vector 发出 `VECTOR_DONE`，Cube 等待完成。

流水跨 Q 任务连续推进，不在每个 Q 块末尾整体排空。下一个 Q 块的 QK、softmax 可以先行，前一个 Q 块延迟的 PV、输出累加随后完成；V2 仍按原任务顺序消费，前一任务最后一次输出写出后，才复用 UB 累加区。
