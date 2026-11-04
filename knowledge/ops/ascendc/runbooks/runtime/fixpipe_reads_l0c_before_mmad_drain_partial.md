---
type: Runbook
title: "Mmad 后立刻 fixpipe 读 L0C 只得部分快照"
description: "Mmad 与 L0C bulk 读出之间只靠向量事件对不够，读出会缺末尾列且随 M 队列积压加重；bulk 前加 PipeBarrier<PIPE_ALL> 才根治。"
tags: [task.debugging, topic.implementation.synchronization, topic.programming_model.execution_unit.cube]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/PipeBarrier_ISASI.md
    role: constraint
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-10-28T09:52:17Z"
platforms: ["310p"]
---

# Mmad 后立刻 fixpipe 读 L0C 只得部分快照

## 现象

310P 上 cube 段每次 `Mmad` 后立即用 fixpipe bulk 把 `[64,64]` f32 的 L0C 结果读到 UB（`DataCopy(tD, src, DataCopyParams(4, 8, 0, 0), epM)`），再做分形重排。探针按列统计"与 golden 精确相符的列区间"，得到非常规整的形状：

```
kt=0（本 unit 第一次 Mmad，M 队列空）: 精确列 0..47，列 48..63 = NaN（从未被写）
kt=1（上一 visit 的 dq Mmad 仍在队列）: 精确列 0..31，列 32..63 = 垃圾
某域 u=3 kt=0: S firstbad=-1（全 64 列精确）、dp firstbad=-1
某域 u=3 kt=1: S firstbad=32、dp firstbad=32
```

规律：**M 队列越"忙"，读出剩下的列越少**；坏区永远在列方向尾部（最后若干 n 分形），行方向不一定坏。同一个 bug 在另一路（转置输出）同样出现（firstbad-col=32），只是那一路输出对少数列不敏感、靠成员掩码"运气"没暴露。

当时代码在 Mmad 与 bulk 之间只有：

```cpp
// ✗ 只有队列内事件对，管不到 fixpipe 读 L0C
Mmad(...);
SetFlag<HardEvent::M_S>(evMm3);
WaitFlag<HardEvent::M_S>(evMm3);
DataCopy(tD, src, DataCopyParams(4, 8, 0, 0), epM);
```

## 适用场景

- 工程形态：Kernel 直调，单 kernel 内 cube（Mmad/fixpipe）与 vector 混排。
- API 路径：`Mmad` → `DataCopy(L0C 视图, UB, DataCopyParams(4, 8, 0, 0), epM)`；同步原语 `PipeBarrier<PIPE_ALL>()` 与 `HardEvent` 事件对。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / dav_m200）+ CANN 9.1.0。
- 适用粒度：`platform_wide`（m200 的 Mmad/fixpipe 完成度语义）。
- 路线优先级：`recommended_fastpath`（Mmad 后一律全屏障；相对"只用事件对"的代价是每次 Mmad 增加一个全局排空点）。
- 明确不适用 / 未验证场景：只在 310P 实测；其它代际是否同样需要全屏障未验证。

## 根因

`Mmad` 的分形写入由 M 队列完成，而 L0C→UB 的 bulk 读出由 fixpipe/MTE3 侧发起。两者之间**没有可用的定点事件对**：

- `HardEvent::M_MTE3` 在本工具链枚举里不存在：写出来直接编译失败
  `error: no member named 'M_MTE3' in 'AscendC::HardEvent'`。
- `HardEvent::M_S` 可以编译（M→S 等待），但实测**不改变任何数值**：插入后目标算子的 dq 误差逐位不变，S 读出仍缺列。
- 裸 `set_flag(PIPE_M, PIPE_MTE3, id)` 只在内建 intrinsic 层存在，C++ API 侧没有对应封装。

因此"等 Mmad 完成"只能落在**全局排空点** `PipeBarrier<PIPE_ALL>()` 上：它同时排空 M 与 MTE3，bulk 读出才拿到完整分形。

## 解决配方

```cpp
// ✓ 终版 readout64：bulk 前全屏障
auto readout64 = [&](const LocalTensor<float>& src,
                     LocalTensor<float>& dst,
                     int64_t probeOff) __aicore__ {
    tDAlt = !tDAlt;
    LocalTensor<float> tX = tDAlt ? tD2 : tD;
    // Mmad 分形完成前 fixpipe 读 L0C 得部分快照
    // (实证: 列 48-63 行 2+ 恒为零 = L0C 该区从未被写) — M_S 对只约束
    // S 队列、管不到 MTE3 (实证 no-op); PipeBarrier<PIPE_ALL> 为全局排空点
    PipeBarrier<PIPE_ALL>();
    DataCopy(tX, src, DataCopyParams(4, 8, 0, 0), epM);
    SetFlag<HardEvent::MTE3_S>(evRs);
    WaitFlag<HardEvent::MTE3_S>(evRs);
    for (int32_t nb = 0; nb < 4; ++nb) {   // 实证 4 连拷
        DataCopy(dst[nb * 16], tX[1024 * nb], DataCopyParams(64, 2, 0, 6));
    }
    SetFlag<HardEvent::MTE3_V>(ev3V);
    WaitFlag<HardEvent::MTE3_V>(ev3V);
    PipeBarrier<PIPE_ALL>();
};
```

同一纪律也用在操作数装载上（`loadA`/`loadB` 里 `DataCopy` 之后、`LoadData` 之前加 `PipeBarrier<PIPE_ALL>()`，注释 `[M→MTE1] 上一 Mmad 读 l0 槽排空`），否则新一次 Mmad 的 B 操作数会覆盖仍在被上一次 Mmad 读取的 L0 槽。

## 设计决策

- 先试了事件对（`M_MTE3` 不存在 → 退到 `M_S`），失败后才用全屏障；最终选择"每个 Mmad 后一律全屏障"，理由是行为确定、代价可控，而事件对在本代际没有可靠封装。
- 没有退到"双 L0C 槽 + 隔一轮读"：那只是把问题推后一轮，队列积压时仍会读到半成品。

## 系统信息

- 平台 310P（dav_m200），CANN 9.1.0（枚举定义编译进 bisheng 编译器，不在文本头里，故 `grep HardEvent` 找不到定义）。
- 文件：`kernel/<generic>.cpp`（`readout64`、`loadA`、`loadB`、`mmad64`）。

## 完整代码

改前（只有 M→S 事件对）：

```cpp
// ✗ 队列内事件对管不到 fixpipe 读 L0C
Mmad(l0c, l0a, l0b, ...);
SetFlag<HardEvent::M_S>(evMm3);
WaitFlag<HardEvent::M_S>(evMm3);
DataCopy(tD, src, DataCopyParams(4, 8, 0, 0), epM);
SetFlag<HardEvent::MTE3_V>(ev3V);
WaitFlag<HardEvent::MTE3_V>(ev3V);
```

改后（bulk 前后各一个全屏障，中间按 4 连带重排）：

```cpp
auto readout64 = [&](const LocalTensor<float>& src,
                     LocalTensor<float>& dst,
                     int64_t probeOff) __aicore__ {
    tDAlt = !tDAlt;
    LocalTensor<float> tX = tDAlt ? tD2 : tD;
    PipeBarrier<PIPE_ALL>();
    DataCopy(tX, src, DataCopyParams(4, 8, 0, 0), epM);
    SetFlag<HardEvent::MTE3_S>(evRs);
    WaitFlag<HardEvent::MTE3_S>(evRs);
    for (int32_t nb = 0; nb < 4; ++nb) {
        DataCopy(dst[nb * 16], tX[1024 * nb], DataCopyParams(64, 2, 0, 6));
    }
    SetFlag<HardEvent::MTE3_V>(ev3V);
    WaitFlag<HardEvent::MTE3_V>(ev3V);
    PipeBarrier<PIPE_ALL>();
};
```

操作数装载侧的对应写法：

```cpp
DataCopy(l1a, gmQ[qOff], ndA);
SetFlag<HardEvent::MTE2_MTE1>(ev21);
WaitFlag<HardEvent::MTE2_MTE1>(ev21);
PipeBarrier<PIPE_ALL>();      // [M→MTE1] 上一 Mmad 读 l0 槽排空
LoadData(l0a, l1a, pA);
```

## 预防

- 把"`Mmad` → L0C bulk 读出"封装成单一 `readout64` 函数，`PipeBarrier<PIPE_ALL>()` 写死在函数里，禁止调用点各自省屏障。
- 操作数装载段（`loadA`/`loadB`）同样在 `LoadData` 前加全屏障，防新 Mmad 覆写仍被读取的 L0 槽。
- 探针统计按列区间输出（`firstbad`），而不是只看整体 max，才能看到"随队列积压缩短"的形态。

## 验证信号

来源：一次 310P attention 类反向算子迁移会话的列区间探针（dump 每块 Mmad 结果与 python golden 逐列对拍）。

- 修复前：kt=0 精确列止于 48（其余 NaN），kt=1 精确列止于 32；另一路同现象（来源平台：310P；证据等级：tool_observed）。
- `HardEvent::M_MTE3` 写法编译报 `no member named 'M_MTE3' in 'AscendC::HardEvent'`；改用 `M_S` 后目标算子 dq 误差逐位不变（来源平台：310P；证据等级：tool_observed）。
- bulk 前加 `PipeBarrier<PIPE_ALL>()` 后同一探针输出 `exact cols=64, maxdiff=1e-05`（来源平台：310P；证据等级：tool_observed）。
- 终版 kernel 保留该形态，最终 50 例精度全 PASS（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 全屏障代价是流水线气泡；对 Mmad 密集的小 tile 循环，性能可能受影响（本算子后续改用更省时的掩码路径才把整体性能拉起来，屏障本身未做微基准拆分）。
- "缺尾部列"是本平台本形态下的表现；其它芯片的部分快照形态（缺行/缺分形）未验证。
- 探针本身有坑：读 L0C 的 dump 若与跨单元重载的 lse/dlt 缓冲共用 GM 区，会读到别的 unit 的数据，误判为"读出坏了"——判读列区间前先确认 dump 源是本次 Mmad 的目标槽。
- 与"同一 UB 暂存被连续两次 bulk 覆写"（WAR）是两种故障：本卡判据是"精确列随 M 队列积压而缩短"，WAR 的判据是"坏块固定在第二次读出、与源偏移无关"。

## 坏实践

- 看到"列 48-63 为 0/NaN"就去改 L0C 布局公式或 bulk 参数——本轨迹中 raw 影像与文档布局完全一致（`max≈9.5e-6`），问题在完成度不在布局。
- 用 `M_S` 事件对当"通用 fixpipe 护栏"——它编译得过，但没有可观测效果，会让人误以为问题在别处。

## 误诊

- 误诊（agent_reported）：曾把该现象解释为"上一轮 bulk 的 WAR"，并用双缓冲去修；两症状相似但判据不同（见失效边界最后一条），双缓冲对本卡无效。
