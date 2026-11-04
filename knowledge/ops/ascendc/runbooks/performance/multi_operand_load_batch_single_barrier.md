---
type: Runbook
title: 多操作数装载合并成一次全屏障
description: visit 内 3-4 张 B 操作数改为两相批装载，每次 visit 只留一次 MTE2_MTE1+PIPE_ALL；官方口径几何平均由 0.88 升到 1.08，逐例 −9% ~ −58%。
tags: [task.optimization, topic.implementation.pipeline, topic.implementation.synchronization, topic.data_movement.data_copy]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/PipeBarrier_ISASI.md
    role: constraint
created_at: "2026-10-28T10:00:08Z"
updated_at: "2026-10-28T10:00:08Z"
platforms: ["310p"]
---

# 多操作数装载合并成一次全屏障

## 现象

310P（Ascend310P3，DAV_2002 / dav-m200）上一个裸 Mmad 的多段 GEMM kernel（选块稀疏注意力反向），每个 visit 要装 3 张（A 域）或 4 张（B 域）B 操作数到 L1、再 `LoadData` 到 L0B。原实现每张操作数各自带一套完整同步：

```cpp
DataCopy(l1d, gm[base], nd);                    // GM→L1
SetFlag<HardEvent::MTE2_MTE1>(ev21);
WaitFlag<HardEvent::MTE2_MTE1>(ev21);
PipeBarrier<PIPE_ALL>();                        // 上一 Mmad 的 M→MTE1 WAR
LoadData(l0b[l0Off], l1d, pB64);
SetFlag<HardEvent::MTE1_M>(ev1M);
WaitFlag<HardEvent::MTE1_M>(ev1M);
```

即每次 visit 有 3–4 次 `PIPE_ALL` 全排空 + 3–4 对 `MTE2_MTE1` + 3–4 对 `MTE1_M`，GM→L1 的并发被逐个串行化。改前该实现在官方口径（msprof `quick` / `Task_Duration`，warmup=3，device 4）下相对同一参照实现的几何平均比值为 0.88（14/14 valid）。

改成“两相批装载”后，同一口径的几何平均比值 1.0842（14/14 valid），算子侧总时长 −20.4%，逐例 −9% ~ −58%，精度门禁保持 50/50 PASS。

## 适用场景

- 工程形态：kernel 直调（AscendC raw-launch，裸 `Mmad` + `LoadData`/`LoadData2D`/`LoadData3D` + L1/L0 手工管理），非 matmul 高阶 API。
- API 路径：`DataCopy`(GM→L1, `Nd2NzParams`)、`LoadData`(L1→L0B, `LoadData2DParams`)、`SetFlag/WaitFlag<HardEvent::MTE2_MTE1|MTE1_M>`、`PipeBarrier<PIPE_ALL>()`、`Mmad`。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.1.0，device 4。
- 适用粒度：`operator_family` —— 任何“单次迭代要装多张 B 操作数、且 L1/L0B 槽位互不相同”的裸 Mmad kernel。
- 路线优先级：`recommended_fastpath`（本卡的两相写法）；“每张操作数各自一套同步”是被替换的基线，不是错，只是慢。
- 明确不适用 / 未验证：多缓冲/双缓冲流水（`TQue`/`TPipe` 自动流水）不在本卡范围；槽位复用（同一 L1/L0 槽装两张不同操作数）会破坏“批内无冲突”前提；A2/A3/950 未验证。

## 根因

visit 级开销的主项不是数据量，而是**同步次数**：每张操作数一套 `MTE2_MTE1` + `PIPE_ALL` + `MTE1_M`，把本可并发的 GM→L1 逐个串行化，并且每次全屏障都要把整条流水排空一次。3–4 张操作数就意味着每个 visit 3–4 次全排空，而 visit 在一个 kernel 里要跑很多轮。

两相写法把“发”和“收”拆开：先把所有 GM→L1 发出去（MTE2 并发），用一次 `MTE2_MTE1` 等它们全部落地，同时用一次 `PIPE_ALL` 排空上一轮 Mmad 对 L0 槽的 M→MTE1 WAR，再逐张 `LoadData2D`，末尾单次 `MTE1_M` 收尾。相序等价的前提是批内槽位互不相同。

## 解决配方

**before：每张 B 操作数各自一套事件对 + 全屏障（A visit 3 次、B visit 4 次）**

```cpp
// ---- B 操作数装载: （可选暖读）+ Nd2Nz + LoadData2D（ift=false→B=srcᵀ）
auto loadB = [&](LocalTensor<half>& l1d, int32_t l0Off,
                 const GlobalTensor<half>& gm, int64_t base,
                 const Nd2NzParams& nd, bool warm, int32_t warmStrideBlk)
    __aicore__ {
    // [律 ndQK] 连续 src(warmStrideBlk==0)免暖读; strided 暖读
    // lean(3): 按律执行——砍掉连续 src 的串行 GM→UB 全等(WAR 暖读双跳)
    if (warm && (warmStrideBlk != 0 || !lean)) {
        DataCopy(staging, gm[base],
                 DataCopyParams(M64, 4,
                                static_cast<uint16_t>(warmStrideBlk), 0));
        SetFlag<HardEvent::MTE2_V>(ev2V);
        WaitFlag<HardEvent::MTE2_V>(ev2V);
    }
    DataCopy(l1d, gm[base], nd);
    SetFlag<HardEvent::MTE2_MTE1>(ev21);
    WaitFlag<HardEvent::MTE2_MTE1>(ev21);
    PipeBarrier<PIPE_ALL>();   // [M→MTE1] 上一 Mmad 读 l0 槽排空
    LoadData(l0b[l0Off], l1d, pB64);
    SetFlag<HardEvent::MTE1_M>(ev1M);
    WaitFlag<HardEvent::MTE1_M>(ev1M);
};
```

```cpp
// A visit：0=Kᵀ(S 用, ←kP2ᵀ), 1=Vᵀ(dp 用, ←vP2ᵀ), 2=K 自然(dq 用, ←kT2ᵀ)
const int64_t ktUnit =
    (static_cast<int64_t>(b) * Hk + kh) * nKT + kt;
loadB(l1b0, 0, gKP2, ktUnit * M64 * Deff, ndCont, true, 0);
loadB(l1b1, M64 * C64, gVP2, ktUnit * M64 * Deff, ndCont, true, 0);
loadB(l1b2, 2 * M64 * C64, gKT, ktUnit * M64 * Deff, ndCont, true, 0);
mmad64(0, 0, 0, true);                    // S = Q@Kᵀ
mmad64(M64 * C64, M64 * C64, M64 * C64, true);  // dp = DO@Vᵀ
SetFlag<HardEvent::V_MTE3>(evZa);   // z/dpR WAR 护栏
WaitFlag<HardEvent::V_MTE3>(evZa);
readout64(l0c[0], z, -1, false, true);
```

```cpp
// B visit：0=Qᵀ(←qTile), 1=DOᵀ(←doTile), 2=Q(←qT), 3=DO(←doT)
loadB(l1b0, 0, gQT, qBase, ndCont, true, 0);
loadB(l1b1, M64 * C64, gDOT, qBase, ndCont, true, 0);
loadB(l1b2, 2 * M64 * C64, gQTt, qBase, ndCont, true, 0);
loadB(l1b3, 3 * M64 * C64, gDOTt, qBase, ndCont, true, 0);
// 逐 visit 的 lse/δ（列参数）→ 行广播矩阵（Adds 拷贝, 行广播）
DataCopy(lseL, gLse[uA * C64], C64);
DataCopy(dltL, gDlt[uA * C64], C64);
SetFlag<HardEvent::MTE2_V>(ev2V);
WaitFlag<HardEvent::MTE2_V>(ev2V);
PipeBarrier<PIPE_ALL>();
```

**after：两相批装载，每次 visit 一次全屏障**

```cpp
// ---- [性能·批装载] B 操作数两相装载(单 visit 多张操作数共用一次同步) ----
// 原 loadB 每张操作数各带 MTE2_MTE1 对 + PIPE_ALL 全排空 + MTE1_M 对
// (A visit 3 次 / B visit 4 次); 全屏障是本算子 visit 的主开销, 合并后
// 每 visit 仅 1 次全屏障。相序等价: 全部 GM→L1 先发(MTE2 并发), 一次
// MTE2_MTE1 + 全屏障(同时排空上一 Mmad 的 M→MTE1 WAR), 再逐张 LoadData2D,
// 单次 MTE1_M 收尾。l1b/l0b 槽位互不相同, 批内无冲突(实证骨架不变)。
auto loadBprep = [&](LocalTensor<half>& l1d,
                     const GlobalTensor<half>& gm, int64_t base,
                     const Nd2NzParams& nd) __aicore__ {
    DataCopy(l1d, gm[base], nd);
};
auto loadBfin = [&](LocalTensor<half>& l1d, int32_t l0Off) __aicore__ {
    LoadData(l0b[l0Off], l1d, pB64);
};
```

```cpp
// A visit
loadBprep(l1b0, gKP2, ktUnit * M64 * Deff, ndCont);
loadBprep(l1b1, gVP2, ktUnit * M64 * Deff, ndCont);
loadBprep(l1b2, gKT, ktUnit * M64 * Deff, ndCont);
SetFlag<HardEvent::MTE2_MTE1>(ev21);
WaitFlag<HardEvent::MTE2_MTE1>(ev21);
PipeBarrier<PIPE_ALL>();
loadBfin(l1b0, 0);
loadBfin(l1b1, M64 * C64);
loadBfin(l1b2, 2 * M64 * C64);
SetFlag<HardEvent::MTE1_M>(ev1M);
WaitFlag<HardEvent::MTE1_M>(ev1M);
mmad64(0, 0, 0, true);                    // S = Q@Kᵀ
mmad64(M64 * C64, M64 * C64, M64 * C64, true);  // dp = DO@Vᵀ
readout64(l0c[0], z, -1, false, true);
readout64(l0c[M64 * C64], dpR, -1, true, false);
```

```cpp
// B visit：4 张 B 操作数 + lse/δ 一次发 + 单次全屏障
loadBprep(l1b0, gQT, qBase, ndCont);
loadBprep(l1b1, gDOT, qBase, ndCont);
loadBprep(l1b2, gQTt, qBase, ndCont);
loadBprep(l1b3, gDOTt, qBase, ndCont);
// 逐 visit 的 lse/δ（列参数）→ 行广播矩阵（Adds 拷贝, 行广播）
DataCopy(lseL, gLse[uA * C64], C64);
DataCopy(dltL, gDlt[uA * C64], C64);
SetFlag<HardEvent::MTE2_MTE1>(ev21);
WaitFlag<HardEvent::MTE2_MTE1>(ev21);
SetFlag<HardEvent::MTE2_V>(ev2V);
WaitFlag<HardEvent::MTE2_V>(ev2V);
PipeBarrier<PIPE_ALL>();
loadBfin(l1b0, 0);
loadBfin(l1b1, M64 * C64);
loadBfin(l1b2, 2 * M64 * C64);
loadBfin(l1b3, 3 * M64 * C64);
SetFlag<HardEvent::MTE1_M>(ev1M);
WaitFlag<HardEvent::MTE1_M>(ev1M);
```

同一轮里还删掉了读出前多余的一对 `V_MTE3`（A/B 两处都删）：

```cpp
// before
SetFlag<HardEvent::V_MTE3>(evZa);   // z/dpR WAR 护栏
WaitFlag<HardEvent::V_MTE3>(evZa);
readout64(l0c[0], z, -1, false, true);

// after（批装载全屏障已覆盖该 WAR，直接读出）
readout64(l0c[0], z, -1, false, true);
```

## 设计决策

- **为什么一次 `PIPE_ALL` 够**：批内所有 GM→L1 都在同一次 `MTE2_MTE1` 事件对之前发出（MTE2 并发执行），该事件保证它们全部落地后才开始 `LoadData`；`PIPE_ALL` 同时排空上一轮 Mmad 对 L0 槽的 M→MTE1 WAR；末尾单次 `MTE1_M` 保证所有 `LoadData` 完成后再发 Mmad。槽位（`l1b0..l1b3` / L0B 偏移 0、64×64、2×64×64、3×64×64）互不相同，批内无依赖。
- **为什么把 lse/δ 的 `DataCopy` 也并进批里**：它同样是 MTE2 通路，单独发会多一对事件；并入后 B visit 只有一次全屏障。但它消费在向量侧，所以额外保留 `MTE2_V` 事件对。
- **为什么敢删 `V_MTE3` 事件对**：它是读出前对 z/dpR 的 WAR 护栏，而批装载的全屏障在同一位置已把向量队列排空；删后 50/50 精度通过（这是必要但不充分的验证，见失效边界）。
- **放弃的候选**：把每张操作数改成“发完就走、最后统一等待”但保留多次 `PIPE_ALL`——收益几乎为零（全屏障就是主开销）。
- **路线分级**：`recommended_fastpath`。

## 系统信息

- 工具链：CANN 9.1.0，torch + torch_npu，Python `/usr/local/python3.11.10/bin/python3`，单 device 4。
- 工程布局：`/home/<user>/<workdir>/<op>/`，含 `kernel/<generic>.cpp`、`host/<generic>_host.cpp`、`tests/<generic>_test.py`、`perf/`；kernel 724 行（含 `dbgStage` 诊断分支，默认 0）。
- 构建：`cd /home/<user>/<workdir>/<op> && bash build.sh` → `BUILD_OK: build/lib<generic>_ops.so`。
- 精度：`ASCEND_RT_VISIBLE_DEVICES=4 /usr/local/python3.11.10/bin/python3 <op>/tests/<generic>_test.py`（50 例全量）。
- 性能：官方 harness `--quick --warm-up=3 --device=4`，产物 `perf/{performance.json, performance.log, perf_report.md}`；310P 禁 `--compare`（深度对比组含 310P 非法的 L2Cache 采集项，实测全灭）。

## 性能影响

- **相对代价（成对；参照路线 = 官方 harness 的参照实现，同一 `Task_Duration` 口径；来源平台 310p）**：同一口径下，改前几何平均比值 0.88（14/14 valid），改后 1.0842（14/14 valid）；算子侧总时长 −20.4%；逐例变化 −9% ~ −58%。
  其中小/中例（暂存与固定开销占比高）降幅最大（−58% / −45% / −35%），大例 −16% ~ −19%——与本卡“减少 visit 内同步次数”的机制一致，但该轮同时改动了 host staging，故不能把全部降幅归因于本卡。
- 同轮的 host staging 缩减另见同族卡；本条是本轮 kernel 侧的主要改动。
- **精度未退化**：改动后全量 50/50 PASS，最大 `|ours-gold|` dq 9.533e-04、dk 4.410e-03、dv 8.152e-03，最差 `ours/ref` 误差比 dq 1.0000、dk 1.0007、dv 1.0047。

## 预防

- 改批装载前先列出每个槽位（L1 与 L0 偏移），确认批内无槽位复用；有复用就必须拆批。
- 全屏障放到“批内所有 MTE2 已发出”之后、“第一张 LoadData”之前；顺序错了就变成竞态。
- 删同步事件前必须找到“覆盖它的那个屏障”并写在注释里；不要凭“看起来没用”删。
- 改完先单例门禁（3 例覆盖 A/B 两域），再全量 50 例，再重新构建后复验。
- 逐例同口径对比（改前/改后都用官方 `Task_Duration`），不要拿 kernel-only 数字和官方数字比。

## 验证信号

来源说明：以下信号取自本算子在 310P 上那一轮性能收官的实测输出——官方 harness 采集表与 `performance.json` 复算、全量/子集精度门禁输出；均为本轨迹内的工具输出，无外部转述。

- 改后全量精度门禁 50/50 PASS（来源平台：310P；证据等级：tool_observed）。
- 改后官方口径 14/14 valid，几何平均比值 1.0842（工具输出 `geomean_speedup` 与按 `per_case` 逐例复算一致）（来源平台：310P；证据等级：tool_observed）。
- 同口径改前/改后逐例对比：算子侧总时长 −20.4%，逐例 −9%/−10%/−10%/−58%/−45%/−13%/−9%/−10%/−35%/−19%/−17%/−16%/−27%/−16%（来源平台：310P；证据等级：tool_observed）。
- 重新构建后 8 例复验 8/8 PASS，随后全量报告恢复为 50/50（来源平台：310P；证据等级：tool_observed）。
- 最大误差量级：dq 9.533e-04、dk 4.410e-03、dv 8.152e-03；最差 `ours/ref` 1.0000/1.0007/1.0047（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 只在 Ascend310P3（DAV_2002 / dav-m200, CANN 9.1.0）实测；其它平台未验证。
- 前提是“批内 L1/L0B 槽位互不相同”；改成共享缓冲（例如双缓冲里复用同一槽）会破坏正确性。
- 本卡不改 tiling 与 Mmad 形状（仍是 64×64×64 分块）；tile 常量变化需重算 L0B 偏移与 `pB64`。
- 未决项：同骨架内把 B 操作数装载**单独**回退为逐操作数（对照）时，dk/dv 同时崩到 1.024e+02 / 2.572e+02（dq 8.986e+00），根因未定位。说明本卡的“可独立回退”不成立，回退试验会污染其它域的判定；需要单独隔离后再说。
- 未决项：删除 `V_MTE3` 事件对的正确性只由 50/50 全量与 8/8 复验支撑，未做竞态压力（多次运行/不同形状交错）验证；对时序更敏感的 kernel 不要照删。
- 未决项：`warm`（暖读）路径在本轮 A/B visit 中均传 `true, 0`（连续源免暖读），strided 暖读路径未在本轮验证。

## 坏实践

- **每张操作数各配一套 `PIPE_ALL`**：把本可并发的 GM→L1 串行化，是 visit 级主要开销。
- **只删屏障不补等价同步**：例如直接删 `PIPE_ALL` 而不保留 `MTE2_MTE1`/`MTE1_M`，会变成竞态（且可能只在部分形状暴露）。
- **用 kernel-only 数字自我验证官方收益**：两个口径差约 1.8 倍，混用会得出错误结论（见同族卡“Task_Duration 含 kernel 间间隙”）。
- **为省一次同步而放松精度门禁**：本卡所有改动都保持 50/50，不接受“先过再修”。

## 误诊

- 会话内一度把 dq 的确定性大错归因于本卡引入的批装载（因为两者同一轮改动）；用单变量对照排除——批装载路径下 dk/dv 与参照逐位相同，且把 lse/δ 改回 host 物化后 dq 立即正确（对照实验见同族行广播卡）。
