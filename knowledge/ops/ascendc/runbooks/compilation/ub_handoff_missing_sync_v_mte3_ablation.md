---
type: Runbook
title: "310P UB 数据交接缺同步：V→MTE3 消融与历史重排观察"
description: "UB 数据跨管道交接缺生产者→消费者同步时静默读旧值：310P 消融实证 V 写→MTE3 读缺 V_MTE3 握手即坏、仅补握手 8/8 恢复（Adds 恒等物化单独 0/4 不必要）；UB→UB DataCopy 直搬重排损坏为历史观察（16 列成组出自 310P 历史轨迹；220x PB-9 为同现象早期记录，均未独立复验）——交接前按实际生产者/消费者补依赖，勿当作 DataCopy 固有行为。"
tags: [task.debugging, topic.data_movement.data_copy]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/programming_guide/advanced_programming/memory_model/memory_consistency.md
    role: constraint
created_at: "2026-09-15T16:00:00Z"
updated_at: '2026-11-16T11:43:18Z'
platforms: ["310p"]
aliases: ["PB-180", "PB-9", "DataCopy"]
---

# 310P UB 数据交接缺同步：V→MTE3 消融与历史重排观察

## 现象

AscendC kernel 内 UB 缓冲跨管道交接后直接消费，编译与调用均无报错，但输出被静默改数。实证形态（f32 出口）：MTE3 直接从刚被 strided copy 写过的 UB 缓冲（`t2`）取源写 GM，按 **16 列（f32 下 64B）的整数倍**成组读到陈旧数据，坏值高比例为写前残留零（消融与逐列 dump 实证）。

历史形态（未独立复验）：UB→UB `DataCopy` 在两个 `LocalTensor` 之间做重排/搬移（例如 L0C 批量读出后再重排）按 16 列（fp16 下 32B）成组出错，坏块表现为列错位/上一 tile 残留；早期 pad 类 kernel 另有单次证伪（pass_a 21/51、max_diff 3–5，去掉 UB→UB 直搬；agent_reported）。

## 适用场景

- 工程形态：AscendC kernel 直调；UB 缓冲跨管道交接后由 `DataCopy` 消费（本卡实证形态：MTE3 从刚被 strided copy 写过的 UB 缓冲取源写 GM，即 UB→GM 出口）。
- API 路径：`DataCopy`（UB 源）＋按实际生产者→消费者方向选跨管事件握手（本例 V 写→MTE3 读补 `V_MTE3`；`Adds` 恒等物化为历史实现选择，非必要条件）；历史观察另含 UB→UB `DataCopy` 直搬重排。
- 验证过的平台与 CANN 版本：实测 Ascend310P3（dav-m200 / arch 200）+ CANN 9.1.0；历史记录另含 220x 的 PB-9 结论。
- 适用粒度：`operator_family`——UB 缓冲跨管道交接，按实际生产者/消费者补依赖（本卡消融实证的是 V 写→MTE3 读缺 `V_MTE3` 握手）。
- 路线优先级：`recommended_fastpath`（默认按“可能损坏”处理：按实际生产者、消费者选择同步方向，不默认 `V_MTE3`——本例恰好是 V 写→MTE3 读）。
- 明确不适用 / 未验证场景：搬运方向本身不是失效条件（本例出口即 UB→GM；GM→UB 载入后 MTE2 写→他管读的组合未实证，机制同理按生产者/消费者补依赖）；UB→UB 直搬损坏未独立复验（历史观察）；其它代际未逐一复验。

## 根因

UB 缓冲在写入者与读取者之间直接转手时，若缺跨管事件握手（按生产者→消费者方向选事件对，本卡实证的是 V 写→MTE3 读补 `V_MTE3`；通用规则——各方向如何选事件对与独立 eventId、多平台案例——见 [shared_ub_cross_pipeline_per_direction_sync](../precision/shared_ub_cross_pipeline_per_direction_sync.md)，本卡为其在 310P 搬运域的诊断案例卡，两卡结论一致、分工互补），读取侧可能看到按 16 列（fp16 下 32B、f32 下 64B）粒度的陈旧/错位数据（消融实测：仅握手即充分，物化并非必要条件）。实证形态：MTE3 直接从刚被 strided copy 写过的 UB 缓冲取源写 GM（f32 直写出口）。历史形态（未独立复验）：UB→UB `DataCopy` 在两个 `LocalTensor` 视图之间直接搬移——同源机制（交接缺依赖）为外推解释，未经独立验证。

解释性假设（未独立复验）：fp16 路径因为要做 `Cast` 而天然多出一块独立 UB 缓冲，等于免费物化，历史 fp16 用例因此未见损坏——不要据此判定交接安全。物化生效的解释框架是把“同一块 UB 被两个视图读写（别名）”变成“两块 UB 之间的单向流”；消融已表明物化并非恢复的必要条件。

## 解决配方

f32 出口的成对改动（inv 分支，before/after 逐字引自轨迹；`w`/`u` 两个出口用同一配方。最小充分改动 = 仅 `V_MTE3` 握手、直读源不动，见验证信号消融；下方为实际采用的形态）。注意：before 仅示意「直读源缺握手 → 补 `V_MTE3`」的**改动形态**——其直读的 `iv` 由 V 管生产，复验中直读未见 16 列指纹，实测指纹属 `t2` 链（`t2` 的实测形态见「现象」首段与「实测」条目，逐字注见代码块后），勿把「直读 `iv`」当作失效复现路径照抄：

```cpp
// before：MTE3 直接从刚被 strided copy 写过的 iv 取源
        if (outF32) {
            DataCopy(gmInvF[invRowBase(bh, m)], iv,
                     DataCopyParams(static_cast<uint16_t>(vr),
                                    static_cast<uint16_t>(Ceff * 4 / 32),
                                    static_cast<uint16_t>((T64 - Ceff) * 4 / 32),
                                    static_cast<uint16_t>(
                                        (HVX * Ceff - Ceff) * 4 / 32)));
        } else {

// after：V 物化到 pf + V_MTE3 握手后再写 GM
        if (outF32) {
            // f32 直写源必须先经 V_MTE3 握手（消融：仅握手即充分）；Adds
            // 物化非必要，为现行实现保留——直读 MTE3 串排产物的 t2 实测
            // 取到 16 列粒度陈旧
            Adds(pf, iv, 0.0f, T64 * T64);
            SetFlag<HardEvent::V_MTE3>(evV3);
            WaitFlag<HardEvent::V_MTE3>(evV3);
            DataCopy(gmInvF[invRowBase(bh, m)], pf,
                     DataCopyParams(static_cast<uint16_t>(vr),
                                    static_cast<uint16_t>(Ceff * 4 / 32),
                                    static_cast<uint16_t>((T64 - Ceff) * 4 / 32),
                                    static_cast<uint16_t>(
                                        (HVX * Ceff - Ceff) * 4 / 32)));
        } else {
```

（注：before 代码及其注释为原始轨迹记录；源码核对 `iv` 实由 V 管（`Cast`/`Sub`/`Add`）生产，直读 `iv` 的出口未见 16 列指纹——16 列指纹属于 `t2` 链，以失效边界为准。）

## 实测、历史观察与解释性假设（16 列粒度指纹与 f32 出口）

310P + CANN 9.1.0 的一次批量归一化类反向算子上命中实证形态：

- **实测（消融与逐列 dump）**：f32 出口 MTE3 直读刚被 strided copy 写过的 UB 缓冲（`t2`）写 GM，按 **16 列（f32 下 64B）的整数倍**成组读到陈旧数据，坏值高比例为写前残留零；仅补 `V_MTE3` 握手即 8/8 恢复。看到"整列整列地错、错列数总是 16 的倍数"时，优先怀疑交接缺同步。
- **历史观察（未独立复验）**：310P 历史轨迹（fp16 用例）记录 UB→UB `DataCopy` 直搬重排按 16 列（fp16 下 32B）成组损坏，坏块表现为"列错位 / 上一 tile 残留"；`Fixpipe` / L0C 批量读出后的 UB→UB 重排曾被记为来源之一——即使重排索引本身是对的，数值也已错；220x 的 PB-9 为同现象早期记录（损坏粒度未记录）。
- **解释性假设（未独立复验）**：fp16 路径因 `Cast`（`half → float`）多生成一块独立 UB 缓冲、等价于一次物化，故历史 fp16 用例未见该损坏——**不要用 fp16 例的通过去证明交接安全**。
- **f32 出口的现行形态（实际采用）**：写出前插一次恒等 `Adds` 物化到独立缓冲 + 显式 `V → MTE3` 握手；消融表明仅握手即充分、物化非必要（见验证信号），逐字 before/after 见上节 `## 解决配方`（inv / w / u 三个出口同形）。

## 验证信号

- 310P/CANN 9.1.0（原会话轨迹记录，未经本卡复验重跑）：保留 UB→UB 直搬时，精度用例出现按 16 列成组的错误；改用恒等 `Adds` 物化 + `V_MTE3` 后，同批用例全部回到该精度门的通过范围（误差绝对值未单列；来源平台：310P；证据等级：tool_observed）。
- 同一版本上（原会话轨迹记录），fp16 路径（中间有 `Cast` 物化）未出现该错误，而 f32 路径复现——排除"数据源错"（来源平台：310P；证据等级：tool_observed）。
- 消融矩阵（2026-11-05 复验，f32 8 例）：全直读无同步 0/8；仅 `V_MTE3` 握手 **8/8 PASS**；仅 `Adds` 物化 0/4（前 4 例）；仅同管 `PipeBarrier<PIPE_MTE3>` 0/4（前 4 例）——必要条件是跨管握手，不是物化（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 损坏粒度：f32 出口的 16 列（64B）粒度经逐列 dump 实测确认（翻转边界恰在 16 列倍数、坏值高比例为写前残留零，日志存档案）；历史 fp16 形态为 16 列（32B）。
- 恒等 `Adds` 的物化成本是整块一次向量 op；大 tile 上会增加 V 管道压力（未量化）。
- 实证只在 310P + CANN 9.1.0；其它代际未验证（历史记录含 220x，未独立复验）。
- 与"无 `DataCopyPad`"的平台限制叠加时，非 32B 对齐的尾部仍需另行处理。

## 坏实践

- 把“交接缺依赖”当成 `DataCopy` 的固有损坏——先按实际生产者/消费者管道核对依赖（本卡实证的失效模式是 V→MTE3 缺握手），再怀疑 API 本身。
- 在未核对生产者→消费者同步前，用 UB→UB `DataCopy` 做纯视图重排（"只搬不改值"）并假设它等价于 `memcpy`（历史轨迹有按 16 列成组损坏的记录）。
- 用 fp16 用例通过去证明交接安全（fp16 未见损坏的解释是 `Cast` 物化——解释性假设，未独立复验）。
- 只检查首地址对齐，不检查"列粒度是否为 16 的倍数"。

## 误诊

- 误诊：看到错误按列出现，先怀疑列索引算错或数据源错（agent_reported）。判据是坏列固定落在 16 的倍数边界、且坏块外数值全对——优先按交接缺同步排查（补生产者→消费者事件握手；本卡实证补 `V_MTE3` 后即恢复），搬运本身不是已实证的失效原因。
- 误诊：把 fp16 例的通过当成"UB→UB 没问题"的证据（agent_reported）；fp16 未见损坏的物化解释是假设（见根因），不能作安全证明。
