---
type: Runbook
title: Cube 操作数 GM 中转按半片粒度使 MTE2 成首瓶颈
description: 核内算出的 cube 操作数按“每操作数半片”各自往返 GM，MTE2 占掉 kernel 三成时间；把带因子打包成单张交错 tile、单次线性推 + 单次 Nd2Nz 读，kernel 自身加速约 2.15x。
tags: [task.optimization, topic.implementation.pipeline, topic.data_movement.data_copy, topic.programming_model.execution_unit.cube]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_UBToL1_continuous.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_3D.md
    role: constraint
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-10-28T09:46:50Z"
platforms: ["310p"]
---

# Cube 操作数 GM 中转按半片粒度使 MTE2 成首瓶颈

## 现象

在 310P（dav-m200）上优化分块门控前向 kernel（分块 KDA 门控 delta rule 前向：每 64 行一个 chunk，chunk 内做 `qg/kq/kgq/kg` 四组带因子、若干 64×64 矩阵乘与状态递推）。主 caliber（msprof kernel 级 `Task_Duration`）显示主 kernel 单次耗时是参考实现的约 2 倍，即加速比 ~0.50x。

对这个 case 做单例 profile，按 pipe 拆开主 kernel：

```
                     vec      mac       m1       m2       m3 blk name
 chunk_kda_310p       40.0%    0.9%    1.3%    33.3%    5.8%   8 chunk_kda_310p
 Cast10                0        0       0       0       0     2 Cast10
```

（按 5 次迭代求和的占比折算；`m1`=MTE1、`m2`=MTE2、`m3`=MTE3、`mac`=cube）

即：vec ≈ 40%、**mte2 ≈ 33%**、mte3 ≈ 6%，cube 只有约 1%。**首瓶颈不是 cube 也不是纯向量计算，而是 MTE2（UB↔GM↔L1 的搬运）**。

根因在结构上：核内算出来的 cube 操作数（带因子 tile、`S_T` 镜像、转置片…）不能直接给 cube 用，必须先 `UB→(MTE3)→GM scratch→(MTE2 Nd2Nz)→L1→(MTE1 LoadData)→L0A/L0B`。原实现的粒度是**“每个操作数的每个 k=64 半片”**各占一个 GM 槽、各自推一次、各自装一次，并且每对 set/wait 都单独发事件；带因子一张 [64,128] 要推 8 个半片槽。

## 适用场景

- 工程形态：Kernel 直调（AscendC 手写 kernel，cube + UB 中转，GM scratch 每核独立一段）。
- API 路径：`DataCopy`（V→GM 推 / GM→UB 暖读）+ `Nd2NzParams`（UB/GM→L1 的 nd→nz）+ `LoadData`/`LoadData3DParamsV2Pro`（L1→L0）+ `Mmad`；事件 `SetFlag/WaitFlag<HardEvent::V_MTE3|MTE3_MTE2|MTE2_MTE1|MTE1_M>`。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0，UB 240KB / 8 核 / cube 仅 fp16。
- 适用粒度：operator_family（凡是“核内造操作数 + GM 中转喂 cube”的分块递推类 kernel）。
- 路线优先级：recommended_fastpath。
- 明确不适用或未验证场景：K=128 且 64×64 分块的形态（本例结构）；A2/A3 上 Nd2Nz/`LoadData3D` 的几何约束不同（未验证，推断可迁移的是“打包粒度”思路，不是具体分形）。

## 根因

`mte2` 占 33%，且它搬的是**本可以少搬的数据**：

1. **打包粒度按操作数切**：带因子 `qgB/kqB` 各 8 个 k=64 半片、`kgqB` 4 个整带槽，每片一次 `DataCopy` 推 + 一次 `Nd2Nz` 装。搬运字节数不是问题，**每次搬运的固定成本（事件对 + 指令开销）**才是问题。
2. **事件按对发**：每个 set/wait 事件对都带流水线气泡，Mmad 之间反复排空。
3. **为规避 m200 的装载律而加的“暖读”**（Nd2Nz 直读新推槽会命中旧线）又额外读一遍源数据，进一步抬高 MTE2。
4. 由此 MTE2 与 vec 相互挤压：vec 侧每 Mmad 后要等装载，装载又要等 push 排空。

**与 950 侧同类现象的边界**：950 侧有“MTE2 发射开销 vs 带宽受限”与“整 tile 合并 DMA 消除 MTE2 发射开销”两条卡（见下方交叉引用），讲的是**同一台 AI Core 上 DMA 指令发射开销主导**；本卡是 310P（dav-m200）上**cube 操作数必须经 GM 中转**这一子系统约束下、按操作数半片切分导致的中转次数膨胀。两者结论形状相同（都要“减少搬运次数而不是字节数”），但平台、约束来源与可用手段不同，不可互相照搬参数。

## 解决配方（结构重排，逐项对应“减少搬运次数”）

**① 带因子打包成单张交错 tile，行内就地写本带因子。** 4 个带共用一张 `[64,128]` 交错槽（行距 128），每个带只写自己那 16 行；Mmad 时只收割本带的 C 行，其余行是别带因子（丢弃）。

```cpp
constexpr int32_t A_QGB  = 12288;    // [64,128] 打包 q 带因子（交错）
constexpr int32_t A_KQB  = 20480;    // [64,128] 打包 k 带因子（交错）
constexpr int32_t B_KGQB = 28672;    // 4×[64,128] k·2^(ρ_r-gk)（交错, B=srcᵀ）
```

**② 推送聚合：一次线性 push 整 tile，每推尾只加一个全屏障。**

```cpp
    // ---- 推送（V→MTE3 发射; 每推尾栅栏）----
    auto pushAt = [&](int32_t off, const LocalTensor<half>& src,
                      int32_t nBlk) __aicore__ {
        SetFlag<HardEvent::V_MTE3>(evV3);
        WaitFlag<HardEvent::V_MTE3>(evV3);
        DataCopy(gmScr[scr + off], src,
                 DataCopyParams(static_cast<uint16_t>(nBlk), 1, 0, 0));
        PipeBarrier<PIPE_ALL>();   // 每推排水（staging 复用对价）
    };
    // 相位排水
    auto drain32 = [&]() __aicore__ {
        SetFlag<HardEvent::MTE3_MTE2>(ev32);
        WaitFlag<HardEvent::MTE3_MTE2>(ev32);
    };
    auto drain3V = [&]() __aicore__ {
        SetFlag<HardEvent::MTE3_V>(ev3V);
        WaitFlag<HardEvent::MTE3_V>(ev3V);
    };
```

**③ 装载：暖读落专用缓冲 + 单次 Nd2Nz，交错槽用 `srcDValue=128` 半读。**

```cpp
    // ---- 装载（两段式: N = 暖读+Nd2Nz[MTE2]; Fin = LoadData[MTE1]）----
    //   暖读落 warm 专用缓冲（免 staging 竞态）; MTE2 管内保序 → 暖读免等待
    //   iv=true: 交错槽 [64,128] 半读（srcDValue=128）
    auto ldAN = [&](int32_t slot, int32_t off, bool iv) __aicore__ {
        Nd2NzParams ndA = nd64;   // 局部参数（勿跨装载点共享）
        if (iv) {
            ndA.srcDValue = static_cast<uint16_t>(K128);
        }
        DataCopy(warm, gmScr[scr + off],
                 DataCopyParams(T64 * T64 * 2 / 32, 1, 0, 0));
        DataCopy(l1aS[slot], gmScr[scr + off], ndA);
    };
    auto ldBN = [&](int32_t slot, int32_t off, bool iv) __aicore__ {
        Nd2NzParams ndB = nd64;
        if (iv) {
            ndB.srcDValue = static_cast<uint16_t>(K128);
        }
        DataCopy(warm, gmScr[scr + off],
                 DataCopyParams(T64 * T64 * 2 / 32, 1, 0, 0));
        DataCopy(l1bS[slot], gmScr[scr + off], ndB);
    };
    auto commit21 = [&]() __aicore__ {
        SetFlag<HardEvent::MTE2_MTE1>(ev21);
        WaitFlag<HardEvent::MTE2_MTE1>(ev21);
    };
    auto ldAFin = [&](int32_t slot) __aicore__ {
        LoadData3DParamsV2Pro pC;
        pC.channelSize = T64;
        pC.extConfig =
            (static_cast<uint64_t>(T64) << 16) | static_cast<uint64_t>(T64);
        LoadData(l0aS[slot], l1aS[slot], pC);
    };
    auto ldBFin = [&](int32_t slot) __aicore__ {
        LoadData(l0bS[slot], l1bS[slot], pB64N);
    };
    auto commit1M = [&]() __aicore__ {
        SetFlag<HardEvent::MTE1_M>(ev1M);
        WaitFlag<HardEvent::MTE1_M>(ev1M);
    };
```

**④ 紧凑 [64,64] 操作数：单 Nd2Nz + 单 `LoadData3D` + 单 Mmad**（原来是“半片对：2 装载 + 2 Mmad + 累加”），L0C 读出用 D 布局一次搬 + 每 16 行重排：

```cpp
    // L0C D 布局 → 行主序（全 64 行有效: A tile 全行打包）
    auto readout = [&]() __aicore__ {
        DataCopy(tD, l0c, DataCopyParams(4, 8, 0, 0), epM);
        SetFlag<HardEvent::MTE3_V>(evV3);
        WaitFlag<HardEvent::MTE3_V>(evV3);
        for (int32_t nb = 0; nb < T64 / 16; ++nb) {   // D 布局 → 行主序
            DataCopy(t2[nb * 16], tD[1024 * nb], DataCopyParams(T64, 2, 0, 6));
        }
        SetFlag<HardEvent::MTE3_V>(evV3);
        WaitFlag<HardEvent::MTE3_V>(evV3);
    };
```

**⑤ 常驻/复用降低往返次数**：`S_T` 单槽 32KB（每核串行 unit 链，同时只有一个 unit 活跃）；`B_ST` 两行块交错推、o 相位 4 半批量常驻（`w@S` 与 `qg@S` 共享一次装载）；单位阵 eye 常驻 L0A（转置 `eye@Xᵀ=Xᵀ` 不再走 GM）；`kgᵀ/kqᵀ` 用 GM 侧转置对（`transR` 系列）一次成型。

## 设计决策

- **为什么选“交错槽 + srcDValue=128”而不是继续用紧凑半片**：交错槽一次线性 push 就能推整 tile（1 次 `DataCopy` 代替 2 次半片推），读回时用 `Nd2NzParams.srcDValue=128` 直接按行跨 128 取半，省掉“半片对”的第二次装载与第二次 Mmad。
- **为什么把“暖读”独立成 `warm` 缓冲**：m200 的实证律是“Nd2Nz 直读新推槽会命中旧线”，必须同址线性读一遍再 Nd2Nz；暖读若落回 `staging` 会与后续构建抢同一缓冲，落专用 `warm` 后 MTE2 管内保序、无需等待。
- **为什么每推尾加全屏障而不是只发事件**：staging 缓冲被多次 push 复用，“每推排水”是复用前提；代价是每次 push 一次排空，但换来的是可以安全复用单份 staging（UB 预算换到位）。
- **被放弃的候选**：① 按 k=64 半片保持紧凑布局、只是把事件合并——试过，MTE2 仍是瓶颈（字节数没变，装载次数只减了事件开销）；② 完全不落 GM（用 L1 直接接收 UB 数据）——310P 上没有 UB→L1 的通路，只能经 GM。
- 当前方案属 recommended_fastpath。

## 系统信息

- 平台：310P（dav-m200 / DAV_2002），CANN 9.1.0，UB 240KB，8 核，cube fp16-only。
- 相关文件：`kernel/<generic>_chunk_kda.cpp`（整条流水：GM 槽常量、push/装载/读出 helper、chunk 主体）；`host/<generic>_host.cpp`（GM scratch 分配、每核独立段）。
- GM scratch：每核独立一段、槽位以 `constexpr int32_t` 别名给出（槽表见上文“解决配方”的 verbatim 代码块；具体偏移值属该内核实现细节，迁移时按自己的 tile 尺寸重算）。交错槽行距 = tile 宽，紧凑槽为 `[64,64]`。
- 测量：单例 `msprof --output=... --ai-core=on --task-time=on --ascendcl=on python3 _wrapper.py` → `op_summary*.csv` 按 `Task Duration/Pipe` 汇总；主 caliber 用 `--compare --warm-up=3`。

## 性能影响

参照路线：**同一个 kernel 重写前的版本（按半片/逐操作数中转的 v0）**，来源平台 310p，主 caliber = msprof kernel 级 `Task_Duration`。

- 主 kernel 单次耗时降到 v0 的 **0.465x（即约 2.15x 加速）**；
- 其中 mte2 pipe 降到 **0.30x**、vec pipe 降到 **0.59x**、mte3 降到 **0.27x**；
- 整轮每迭代总时长降到 v0 的 0.51x（该数字**含**另一项 host 侧修复，不能单独归给本卡；本卡可单独归因的是 kernel 自身 2.15x）；
- 精度未退化：改写在同一次 profile 输出里附带的抽样精度为 `abs(o-r)=9.537e-07`、最终全量 40/40 通过（见验证信号）。
- 该路线属 recommended_fastpath，无精度/功能取舍。

## 完整代码

本卡的核心可复用单元是上文 ②③④ 三段 helper（`pushAt`/`drain32`/`drain3V`/`ldAN`/`ldBN`/`commit21`/`ldAFin`/`ldBFin`/`commit1M`/`readout`）与 ① 的槽常量，均已在“解决配方”中 verbatim 内联。整条 kernel 的 chunk 主体（约 700 行）不在本卡内联：它与具体算子语义强绑定，复用价值在 helper 与槽布局，不在主体。

## 预防

- 优化 cube+中转类 kernel 前先看 pipe 占比：**mte2 超过 30% 就先动中转粒度**，别先去抠 vec 指令数。
- 迁移这套结构时必须连着三条装载律一起搬：① 暖读先行；② A/B 不共用同一个 `Nd2NzParams` 实例（每装载点用局部变量）；③ Nd2Nz 参数全 `uint16`。
- 交错槽的“半读”靠 `srcDValue`，改 tile 宽/行距时必须同步改它，否则读到的行错位（症状是“数值像但整体错行”）。

## 验证信号

来源：分块门控前向 kernel（310P）kernel 架构重写（上游流水线架构移植）。以下均为本轨迹内的工具输出。

- 重写前同一 case 的主 kernel pipe breakdown：vec ≈ 40%、mte2 ≈ 33%（5 次迭代求和口径）（来源平台：310P；证据等级：tool_observed）。
- 重写后同一 case：主 kernel 单次耗时降到 0.465x（2.15x 加速），vec 0.59x、**mte2 0.30x**（来源平台：310P；证据等级：tool_observed）。
- 同一次 profile 输出附带的抽样精度：`abs(o-r)=9.537e-07`、`matched=1.0000`（来源平台：310P；证据等级：tool_observed）。
- 终态全量精度 40/40 通过，主 caliber 逐例 10/10 有效（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 结构强绑定 K=128、chunk=64、cube fp16-only 的形态；换 tile 尺寸需重算 `srcDValue`、`LoadData3DParamsV2Pro.extConfig` 的打包参数与 D 布局重排步长（`DataCopyParams(T64, 2, 0, 6)`）。
- 交错槽吃 UB 预算：`warm` 缓冲翻倍（16KB）与补充 tile 会让 240KB 吃紧，本例为此把 staging 从双缓冲降为单缓冲；**UB 超预算时这套结构不能直接照搬**。
- 本次重写同时**引入了新的精度缺陷**（带因子块构建 + ρ 参照），由另外的卡记录；即“性能重排”不能与“数值等价”分开验证，必须每步跑同构 emulation 比对。
- 未验证场景：A2/A3 上 `LoadData3D` 的分形约束（未验证，推断“打包粒度”思路可迁移、“分形参数”不可迁移）。
- 未决项：`B_ST` 的“两行块交错 + o 相位 4 半批量常驻”能否进一步减到一次装载（当前仍需两次）；需要确认 `w@S` 与 `qg@S` 的 B 视图能否共享同一 L1B 落点。

## 坏实践

- 只合并事件、不合并搬运粒度——MTE2 时间几乎不动（字节数与装载次数才是主项）。
- 为省一次 push 而复用同一份 staging 却不加推尾屏障——会把 UB 内容在 push 未完成时改写（本例用 `PipeBarrier<PIPE_ALL>()` 明确买这份保险）。
- 把 A、B 两个视图共用一个 `Nd2NzParams` 实例（“省一个变量”）——m200 上是明令禁止的实证律，症状是 B 侧读到的几何参数来自 A。

## 误诊

- 起初判断瓶颈在 vec（占比最大 40%），于是先去做向量调用数削减；实测那一轮只把 kernel 压到 0.911x（约 −9%），确认 vec 不是唯一主项，最终两条线并行。
- 曾认为 MTE2 高是“搬运字节数多”，想靠减少冗余读（暖读）解决；暖读是正确性必需，减不掉，真正的减法是减少装载**次数**。

## 相关（平台对照）

- 950（同代另一平台）侧的同类现象：[mte2_issue_overhead_vs_bandwidth_bound](mte2_issue_overhead_vs_bandwidth_bound.md)（DMA 发射开销与带宽受限的区分）。
- 950 侧的整 tile 合并手段：[tile_merged_dma_eliminate_mte2_issue_bound](tile_merged_dma_eliminate_mte2_issue_bound.md)（合并搬运消除发射开销）。
- 对向引用：上述两卡的“平台=950”结论不应被本卡的 310P 参数覆盖；本卡的“交错槽 + `srcDValue` 半读 + 暖读”等手段是在 310P 的 GM 中转路径上验证的，能否迁移到 950 未验证（推断只可迁移“减少搬运次数”的思路）。
