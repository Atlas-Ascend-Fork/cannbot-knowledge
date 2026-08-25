---
type: API
title: 随机函数
description: 随机函数接口导航页，包含PhiloxRandom随机数生成接口。
tags: [task.lookup, topic.compute.random_sampling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/random_functions/random_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 随机函数

提供 PhiloxRandom 随机数生成接口。PhiloxRandom 基于 Philox 计数器伪随机算法，输入 128bit 计数器（4×32bit）和两个 32bit key，输出 4 个 32bit 整数。

接口提供连续模式和 stride 模式：连续模式按 `count` 顺序生成；stride 模式通过 PhiloxRandomParams（stride、row、column）支持按列分批生成。模板参数 `Rounds` 支持 7 或 10。目的操作数支持 uint32_t、int32_t（数据类型范围内均匀分布）和 float（0-1 均匀分布），起始地址需 32Byte 对齐。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Philox offset 须放 counter[2:3] 而非 [0:1]](../../../../runbooks/precision/philox_offset_counter_2_3_0_1.md)（`exemplifies`）：该运行卡确认 PhiloxRandom 的 offset 应写入 counter[2:3]、counter[0:1] 保留给 block/group 计数，补充随机 API 总览未展开的 counter 布局契约。
- [PhiloxRandom 默认 7 rounds 与原生 10 不匹配](../../../../runbooks/precision/philoxrandom_7_rounds_10.md)（`exemplifies`）：该运行卡用逐位对照证明原生 PhiloxRandom 要以 Rounds=10 才能复现目标 7-round 路径的预期位流，具体化 rounds 参数边界。
- [philox offset 推进量须固定 12 而非元素数](../../../../runbooks/precision/philox_offset_12.md)（`exemplifies`）：随机函数总览的 PhiloxRandom 以固定 group 消耗 counter；该运行卡验证每轮 offset 必须按实现固定推进 12，而不能按输出元素数推进，否则后续随机序列错位。
- [多核 numPerCore 须对齐 Philox group 4](../../../../runbooks/precision/numpercore_philox_group_4.md)（`exemplifies`）：Philox 每个 counter 生成 4 个值，运行卡说明多核 numPerCore 必须按该 group=4 对齐才能保持 counter 分区连续。
- [PhiloxRandom](philox_random.md)（`related`）：随机函数总览当前唯一展开的生成接口是 PhiloxRandom，目标卡给出其计数器、key、rounds 与输出契约。
<!-- cannbot:related:end -->
