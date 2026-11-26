---
type: Runbook
title: "同ID重复set单wait致MTE1定序失效或EE9999挂死"
description: "原始修复注释将同 ID SetFlag 记为非计数信号量；每轮 SetFlag/WaitFlag 必须一一配对，重复 set 后仅一次 wait 不能提供逐份 L1 定序——表型为静默错值或 EE9999 aicpu exception 挂死，含逐轮配对的 K2 重写版通过 48/50，后续复合版本通过 50/50。"
tags: [task.debugging, topic.implementation.synchronization, topic.architecture]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
    role: supporting
created_at: "2026-11-16T14:03:25Z"
updated_at: "2026-11-25T10:00:57Z"
platforms: ["310p"]
---

# 同ID重复set单wait致MTE1定序失效或EE9999挂死

## 现象

FlashAttention 反向内核在 ND=2（双头/双份收缩循环）形态下随机挂/崩：一种表现为静默错值（`.dq ERR=3.040e-01`，R=2 C=2 ND=2，slot0 `s_raw` 行峰值 2e+00..2e+01 混杂，bad=64/64 全错），另一种表现为 `EE9999: rtDeviceSynchronizeWithTimeout execution failed, reason=aicpu exception`（挂死后 aicpu 异常超时）。ND=1 形态正常。

## 适用场景

- 工程形态：AscendC 内核内按维度循环下发片上搬运 + `SetFlag/WaitFlag<HardEvent::MTE2_MTE1 / MTE3_MTE1>` 令牌握手的流水线：GM→L1 由 MTE2 经 DataCopy 搬入，L1→L0A/L0B 由 MTE1 经 LoadData 搬入，`MTE2_MTE1` 用于通知 L1 数据就绪；重写示例实际展示 MTE2_MTE1 路径，MTE3_MTE1 属其它搬入路径。
- 触发几何：循环次数 ND≥2（同一事件通道在一轮内核里走多遍）。
- 验证过的平台与版本：Ascend 310P3（dav-m200 / `__NPU_ARCH__`=2002），CANN 9.1.0，aarch64。
- 适用粒度（transfer_scope）：`pattern`——AscendC 事件令牌流水线内核（跨算子同构模式）。
- 路线优先级：`recommended_fastpath`（同一事件通道每次 set 均配对一个顺序在其后的 wait（允许同实例内多次握手），且不聚合 wait 的配对纪律是正确写法本身；其强制意图落为「## 坏实践」的 banned 条目：跨轮聚合 set/wait 或双 set 单 wait 形态——令牌配对违例不报编译错，运行期随机挂/静默错）。
- 明确不适用/未验证场景：ND=1 单份形态测不出配对缺失；ND≥3、多 AIV 并行同通道跨核语义未验证。

## 根因

原始修复注释明确写着 `SetFlag 非计数信号量`，因此不能把同 ID 的重复 `SetFlag` 解释成可累计的令牌余额。可观测病灶是循环内每轮 set、循环外只有一次 wait：该形态没有为每份 L1 数据建立一一对应的等待，MTE1 搬运失去逐份定序，可能读到未就绪或已被覆写的数据而静默错值，也可能表现为 `rtDeviceSynchronizeWithTimeout` aicpu exception 挂死。K2 重写把每个 ID 落实为逐轮配对握手；实际验证见「## 验证信号」，未做仅改变事件配对的隔离对照。

“非计数”来自真实修复注释；本轨迹没有寄存器或计数器直测，因此本卡不进一步断言覆盖电路或硬件计数器实现。可复用且已验证的纪律是：**同一 ID 的每个 set 必须被恰好一个顺序在其后的 wait 消费；允许同一循环实例内多次一握一清，也允许 wait 承接前序实例的 set 作流水线式消费，全程收支平衡。不得无配对 wait 连续重复 set，也不得把多个 set 聚合成一次 wait。**

与 [ec_294（MTE2_S 标量消费者死锁）](../compilation/ec_294_dav_m200_setflag_waitflag_hardevent_mte2_s_deadl.md)同属 HardEvent 族但不同 nugget：本例是**同 ID 跨轮 set/wait 配对缺失**，彼例是同通道标量等待无生产者。

## 判别方法

1. ND（循环份数）分层：ND=1 过、ND=2 随机挂/静默错 → 循环内事件配对嫌疑。
2. 错值表型双态：确定性 slot 级垃圾（bad=64/64）与 aicpu exception 挂死交替出现 → 管道定序类而非数值类。
3. 静态审查：展开循环后逐通道检查 `SetFlag<ch>` 与 `WaitFlag<ch>`——每次 set 均配对一个顺序在其后的 wait；允许同实例内多次一握一清，也允许 wait 承接前序实例的 set；全程收支平衡，不能只看整个函数的总数。

## 解决配方

修前形态（诊断事件中 Edit 的 `old_string` 逐字病灶段——每轮循环两次 `SetFlag`、循环内无任何 `WaitFlag`）：

```cpp
        // ---- 单元常驻: q/dy tile + 统计量行（紧凑分块 [wh][c][SqP,64]）----
        for (int32_t c = 0; c < ND; ++c) {
            DataCopy(l1q[c * T64 * T64],
                     gmQ[(static_cast<int64_t>(wh) * ND + c) * SqP * T64 +
                         rb * T64], ndQ);
            SetFlag<HardEvent::MTE2_MTE1>(e21Q);
            DataCopy(l1dy[c * T64 * T64],
                     gmDY[(static_cast<int64_t>(wh) * ND + c) * SqP * T64 +
                          rb * T64], ndQ);
            SetFlag<HardEvent::MTE2_MTE1>(e21DY);
        }
```

要点是**同通道双 set 零 wait 跨轮叠加**。

修后形态（重写版内核 K2 的完整函数，作为逐轮配对写法的独立示例，逐字恢复自完整 Write 并应用跟进 Edit；事件声明、四通道装载与配对、Mmad 生产端及 `rb > 0` / `db > 0` 守卫全部保留。注意 K2 相对修前片段新增 dS/PT/QN/DN 搬运与 dK/dV 的 Mmad 写回，并非同一数据路径的事件级改动）：

```cpp
extern "C" __global__ __aicore__ void op70_fabwd2_310p(
    GM_ADDR dstc, GM_ADDR ptc, GM_ADDR qnat, GM_ADDR dynat,
    GM_ADDR dkF, GM_ADDR dvF,
    int32_t Bf, int32_t nh, int32_t Sq, int32_t Skv, int32_t Dp,
    int32_t units, int32_t R, int32_t C) {
    const int32_t blockDim = GetBlockNum();
    const int32_t core = GetBlockIdx();
    if (core >= blockDim) {
        return;
    }
    const int32_t ND = Dp / T64;
    const int64_t hdCnt = static_cast<int64_t>(Bf) * nh;

    GlobalTensor<half> gmDS, gmPT, gmQN, gmDN;
    gmDS.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(dstc),
                         hdCnt * C * T64 * R * T64);
    gmPT.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(ptc),
                         hdCnt * C * T64 * R * T64);
    gmQN.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(qnat),
                         hdCnt * R * T64 * Dp);
    gmDN.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(dynat),
                         hdCnt * R * T64 * Dp);
    GlobalTensor<float> gmDK, gmDV;
    gmDK.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(dkF), hdCnt * Skv * Dp);
    gmDV.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(dvF), hdCnt * Skv * Dp);

    TPipe pipe;
    TBuf<TPosition::A1> l1dsBuf, l1ptBuf, l1qnBuf, l1dnBuf;
    pipe.InitBuffer(l1dsBuf, T64 * T64 * sizeof(half));
    pipe.InitBuffer(l1ptBuf, T64 * T64 * sizeof(half));
    pipe.InitBuffer(l1qnBuf, T64 * Dp * sizeof(half));
    pipe.InitBuffer(l1dnBuf, T64 * Dp * sizeof(half));
    TBuf<TPosition::A2> l0aABuf, l0aPBuf;
    TBuf<TPosition::B2> l0bQBuf, l0bDBuf;
    pipe.InitBuffer(l0aABuf, T64 * T64 * sizeof(half));
    pipe.InitBuffer(l0aPBuf, T64 * T64 * sizeof(half));
    pipe.InitBuffer(l0bQBuf, T64 * T64 * sizeof(half));
    pipe.InitBuffer(l0bDBuf, T64 * T64 * sizeof(half));
    TBuf<TPosition::CO1> l0cKBuf, l0cVBuf;
    pipe.InitBuffer(l0cKBuf, ND * T64 * T64 * sizeof(float));
    pipe.InitBuffer(l0cVBuf, ND * T64 * T64 * sizeof(float));
    TBuf<TPosition::VECCALC> ubDBuf, oBBuf;
    pipe.InitBuffer(ubDBuf, T64 * T64 * sizeof(float));
    pipe.InitBuffer(oBBuf, T64 * T64 * sizeof(float));

    LocalTensor<half> l1ds = l1dsBuf.Get<half>();
    LocalTensor<half> l1pt = l1ptBuf.Get<half>();
    LocalTensor<half> l1qn = l1qnBuf.Get<half>();
    LocalTensor<half> l1dn = l1dnBuf.Get<half>();
    LocalTensor<half> l0aA = l0aABuf.Get<half>();
    LocalTensor<half> l0aP = l0aPBuf.Get<half>();
    LocalTensor<half> l0bQ = l0bQBuf.Get<half>();
    LocalTensor<half> l0bD = l0bDBuf.Get<half>();
    LocalTensor<float> l0cK = l0cKBuf.Get<float>();
    LocalTensor<float> l0cV = l0cVBuf.Get<float>();
    LocalTensor<float> ubD = ubDBuf.Get<float>();
    LocalTensor<float> oBlk = oBBuf.Get<float>();

    Nd2NzParams ndA;
    ndA.ndNum = 1; ndA.nValue = T64; ndA.dValue = T64;
    ndA.srcNdMatrixStride = 0; ndA.srcDValue = T64;
    ndA.dstNzC0Stride = T64; ndA.dstNzNStride = 1; ndA.dstNzMatrixStride = 0;
    const DataCopyParams cpKz(T64 * Dp * 2 / 32, 1, 0, 0);
    LoadData3DParamsV2Pro pA64;
    pA64.channelSize = T64;
    pA64.extConfig = (static_cast<uint64_t>(T64) << 16) | static_cast<uint64_t>(T64);
    LoadData2DParams pB64T(0, static_cast<uint8_t>((T64 / 16) * (T64 / 16)), 1, 0, 0, true, 0);
    MmadParams mp;
    mp.m = T64; mp.n = T64; mp.k = T64;
    mp.cmatrixInitVal = true; mp.cmatrixSource = false;
    DataCopyEnhancedParams epM;
    epM.blockMode = BlockMode::BLOCK_MODE_MATRIX;
    const uint8_t pad0[4] = {0, 0, 0, 0};

    event_t e21DS = static_cast<event_t>(0);   // MTE2_MTE1: l1ds
    event_t e21PT = static_cast<event_t>(1);   // MTE2_MTE1: l1pt
    event_t e21QN = static_cast<event_t>(2);   // MTE2_MTE1: l1qn
    event_t e21DN = static_cast<event_t>(3);   // MTE2_MTE1: l1dn
    event_t e1M = static_cast<event_t>(0);     // MTE1_M
    event_t eMsK = static_cast<event_t>(0);    // M_S: dk Mmad
    event_t eMsV = static_cast<event_t>(1);    // M_S: dv Mmad
    event_t e3S = static_cast<event_t>(0);     // MTE3_S
    event_t e3M = static_cast<event_t>(0);     // MTE3_M
    event_t eV3 = static_cast<event_t>(0);     // V_MTE3
    event_t e3V = static_cast<event_t>(0);     // MTE3_V
    Load3DSetFMatrixCal(1, static_cast<uint16_t>(T64), pad0);

    for (int32_t u = core; u < units; u += blockDim) {
        const int32_t wh = u / C;
        const int32_t mb = u - wh * C;
        const int32_t validRows =
            (Skv - mb * T64 < T64) ? (Skv - mb * T64) : T64;
        for (int32_t rb = 0; rb < R; ++rb) {
            const int64_t tOff =
                ((static_cast<int64_t>(wh) * C + mb) * R + rb) * T64 * T64;
            DataCopy(l1ds, gmDS[tOff], ndA);
            SetFlag<HardEvent::MTE2_MTE1>(e21DS);
            DataCopy(l1pt, gmPT[tOff], ndA);
            SetFlag<HardEvent::MTE2_MTE1>(e21PT);
            DataCopy(l1qn, gmQN[(static_cast<int64_t>(wh) * R + rb) * T64 * Dp],
                     cpKz);
            SetFlag<HardEvent::MTE2_MTE1>(e21QN);
            DataCopy(l1dn, gmDN[(static_cast<int64_t>(wh) * R + rb) * T64 * Dp],
                     cpKz);
            SetFlag<HardEvent::MTE2_MTE1>(e21DN);
            WaitFlag<HardEvent::MTE2_MTE1>(e21DS);
            WaitFlag<HardEvent::MTE2_MTE1>(e21PT);
            WaitFlag<HardEvent::MTE2_MTE1>(e21QN);
            WaitFlag<HardEvent::MTE2_MTE1>(e21DN);
            if (rb > 0) {
                WaitFlag<HardEvent::M_S>(eMsK);   // 上 rb 末 Mmad 完成
                WaitFlag<HardEvent::M_S>(eMsV);
            }
            LoadData(l0aA, l1ds, pA64);
            LoadData(l0aP, l1pt, pA64);
            SetFlag<HardEvent::MTE1_M>(e1M);
            WaitFlag<HardEvent::MTE1_M>(e1M);
            for (int32_t db = 0; db < ND; ++db) {
                if (db > 0) {
                    WaitFlag<HardEvent::M_S>(eMsK);
                    WaitFlag<HardEvent::M_S>(eMsV);
                }
                LoadData(l0bQ, l1qn[db * T64 * T64], pB64T);
                SetFlag<HardEvent::MTE1_M>(e1M);
                WaitFlag<HardEvent::MTE1_M>(e1M);
                mp.cmatrixInitVal = (rb == 0);
                Mmad(l0cK[db * T64 * T64], l0aA, l0bQ, mp);
                SetFlag<HardEvent::M_S>(eMsK);
                LoadData(l0bD, l1dn[db * T64 * T64], pB64T);
                SetFlag<HardEvent::MTE1_M>(e1M);
                WaitFlag<HardEvent::MTE1_M>(e1M);
                mp.cmatrixInitVal = (rb == 0);
                Mmad(l0cV[db * T64 * T64], l0aP, l0bD, mp);
                SetFlag<HardEvent::M_S>(eMsV);
            }
        }
        // ---- epilogue: dk/dv 写出（f32, validRows 行）----
        WaitFlag<HardEvent::M_S>(eMsK);
        WaitFlag<HardEvent::M_S>(eMsV);
        SetFlag<HardEvent::MTE3_M>(e3M);
        WaitFlag<HardEvent::MTE3_M>(e3M);
        for (int32_t db = 0; db < ND; ++db) {
            DataCopy(ubD, l0cK[db * T64 * T64], DataCopyParams(4, 8, 0, 0), epM);
            SetFlag<HardEvent::MTE3_S>(e3S);
            WaitFlag<HardEvent::MTE3_S>(e3S);
            for (int32_t nb = 0; nb < T64 / 16; ++nb) {
                DataCopy(oBlk[nb * 16], ubD[1024 * nb], DataCopyParams(T64, 2, 0, 6));
            }
            SetFlag<HardEvent::V_MTE3>(eV3);
            WaitFlag<HardEvent::V_MTE3>(eV3);
            DataCopy(gmDK[(static_cast<int64_t>(wh) * Skv + mb * T64) * Dp +
                          db * T64],
                     oBlk,
                     DataCopyParams(static_cast<uint16_t>(validRows), 8, 0,
                                    static_cast<uint8_t>((Dp - T64) / 8)));
            SetFlag<HardEvent::MTE3_V>(e3V);
            WaitFlag<HardEvent::MTE3_V>(e3V);
            DataCopy(ubD, l0cV[db * T64 * T64], DataCopyParams(4, 8, 0, 0), epM);
            SetFlag<HardEvent::MTE3_S>(e3S);
            WaitFlag<HardEvent::MTE3_S>(e3S);
            for (int32_t nb = 0; nb < T64 / 16; ++nb) {
                DataCopy(oBlk[nb * 16], ubD[1024 * nb], DataCopyParams(T64, 2, 0, 6));
            }
            SetFlag<HardEvent::V_MTE3>(eV3);
            WaitFlag<HardEvent::V_MTE3>(eV3);
            DataCopy(gmDV[(static_cast<int64_t>(wh) * Skv + mb * T64) * Dp +
                          db * T64],
                     oBlk,
                     DataCopyParams(static_cast<uint16_t>(validRows), 8, 0,
                                    static_cast<uint8_t>((Dp - T64) / 8)));
            SetFlag<HardEvent::MTE3_V>(e3V);
            WaitFlag<HardEvent::MTE3_V>(e3V);
        }
    }
    PipeBarrier<PIPE_ALL>();
}
```

四个 L1 就绪通知通道（e21DS/e21PT/e21QN/e21DN = MTE2_MTE1）为同实例 set×1 ↔ wait×1 紧邻配对；`eMsK/eMsV`（M_S）为流水线式跨实例消费——每实例 set×1、wait 排在其后首个消费点（下一个 db / rb / epilogue），全循环收支平衡。两类形态共同满足「每 set 恰一 wait、无未消费的重复 set」。

## 设计决策

- 选逐轮配对而非循环外聚合 wait：聚合形态正是 bug 本体；逐轮事件让每份 L1 数据的可见性独立定序。
- K2 是含逐轮配对的独立重写示例，非同一数据路径的事件级改动：修前病灶片段与 K2 不构成单因素对照，配对纪律的成立不依赖「纯事件改动」这一归因。

## 系统信息

- Ascend 310P3（6 卡机），DAV_2002/dav-m200，CANN 9.1.0，aarch64（EulerOS）。

## 验证信号

- 修前：`.dq ERR=3.040e-01 (R=2 C=2 ND=2)`，slot0 `s_raw` 行峰值 2e+00/2e+01 混杂，bad=64/64（来源平台：310p；证据等级：tool_observed）。
- 修前挂死表型：`EE9999: rtDeviceSynchronizeWithTimeout execution failed, reason=aicpu exception`（来源平台：310p；证据等级：tool_observed）。
- 修复实现：Write + 跟进 Edit 落地四组 WaitFlag/SetFlag 通道逐轮配对及 `rb > 0` 守卫（来源平台：310p；证据等级：artifact_verified）。
- K2 重写版（含逐轮配对）：ND=2 形态并入全电池，GATE-4 48/50——残余 2 案均与本缺陷无关（commit 正文实录）：case 32 = 累加序结构地板 2.003x（NPU f32 matmul f16 内部逐位实证）、case 49 = ref 臂 GE 3.42GB OOM（hugepages 0/0）（来源平台：310p；证据等级：artifact_verified，commit 证据）。
- 后续轮 GATE-4 50/50 收口（来源平台：310p；证据等级：artifact_verified，Git history；属后续复合形态，不是本轮原始测量，也不是本缺陷的隔离验证）。

## 预防

- AscendC 内核评审固定项：逐 `HardEvent` 通道画“循环展开后”的 set/wait 配对表——每次 set 恰一 wait、顺序在其后、收支平衡；允许同实例内多次握手，区分紧邻配对与跨实例流水线消费两种合法形态。
- ND/循环维参数化的内核，测试矩阵必须含循环份数 ≥2 的形态（单份形态测不出配对缺失）。

## 失效边界

- “同 ID SetFlag 非计数信号量”来自修复注释，`artifact_verified`；没有寄存器/计数器直测，不断言硬件采用覆盖电路或某种计数器实现。`tool_observed` 闭包只支持：ND=2 失败、同 ID 重复 set 后仅一次 wait 的病灶、逐轮一 set 一 wait 修复及后续验证。
- 本卡不覆盖同内核另两处独立竞态（mid-buffer trans LoadData2D 窗口竞态、MTE2 warm-write staging 危害），另有记载。
- 未验证：ND≥3、多 AIV 并行下同一通道跨核语义。

## 坏实践

- 把 `SetFlag` 提出循环外/合并写，或用“多 set 单 wait 兜底”——原始修复注释明确否定计数信号量语义，重复 set 不构成可累计保险；本例该写法已实测失效。
- 用重跑碰运气通过当验证：本缺陷表型之一就是偶发挂死，偶过即漏。

## 误诊

ND≥2 出现错值或超时，优先检查事件配对；当前记录不足以将两种故障的消失单独归因于此改动。
