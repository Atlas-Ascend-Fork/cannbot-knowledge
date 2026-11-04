---
type: Runbook
title: 用独立探针算子验证 m200 上的 K16 立方几何
description: 在改主 kernel 之前，用 torch.ops 探针逐模式验证 [64,16] B 槽 Nd2Nz + k=16 Mmad 是否可用，避免在形状假设上返工。
tags: [task.optimization, topic.implementation.debugging, topic.programming_model.execution_unit.cube]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_ND2NZ.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Mmad.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/include/basic_api/kernel_struct_mm.h
    role: header
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-10-28T09:46:50Z"
platforms: ["310p"]
---

# 用独立探针算子验证 m200 上的 K16 立方几何

## 现象

要改造一个 `Mmad` 为中心的 kernel，把“每轮都把 K 维补齐到 64 再乘”改成“按真实带宽用 K=16 的薄片”，但 m200 的 `Nd2Nz`/`LoadData`/`Mmad` 几何组合很多（`nValue`/`dValue`/`dstNzC0Stride`/`dstNzNStride`、`LoadData2DParams` 的 `ift`、`MmadParams.k`），**在真 kernel 里试错一次要几分钟编译 + 精度门**，而且失败时无法判断是几何不支持还是自己写错。

会话里的做法是先写一个**独立探针算子**（同工程、独立 `.cpp`、独立 torch.ops schema），一次编好，用 `mode` 参数在同一进程里跑十种几何组合，每种把 `l0c` 读回 UB、`Cast` 成 f32、与 Python 侧期望逐元素比对，只打“PASS/FAIL + 前三处 first-bad”。其中关键结果：

```
mode 0 [FAIL] BinaryRepeatParams row-bcast Mul first-bad=[(1, 0, 2.0, 4), (1, 1, 2.0, 4), (1, 2, 2.0, 4)]
mode 1 [FAIL] v4dtrans [64,8]->[8,64] first-bad=[(0, 1, 9.0, 2), (0, 2, 17.0, 3), (0, 3, 25.0, 4)]
mode 2 [FAIL] Brcb<half> [64]->[64,16] first-bad=[(0, 16, 2.0, 0.0), (0, 17, 2.0, 0.0), (0, 18, 2.0, 0.0)]
mode 3 [FAIL] Transpose<half> tile first-bad=[(0, 16, 2.0, 0), (0, 17, 18.0, 0), (0, 18, 34.0, 0)]
mode 4 [FAIL] colBcast16 chain [64,64] all-rows=vec first-bad=[(1, 0, 49.0, 1), (1, 1, 50.0, 2), (1, 2, 51.0, 3)]
mode 5 [PASS] [64,16] Nd2Nz B + Mmad k=16
```

（多数 FAIL 是“探针自己的期望布局写错”，值本身是对的——见同批负结果卡的结论；`mode 5` 是真 PASS。）

## 适用场景

- 工程形态：AscendC kernel 直调工程（可加一个探针 kernel + torch.ops 绑定）；设备可用。
- API 路径：`Nd2NzParams`/`Nd2Nz`（MTE2）、`LoadData2DParams`/`LoadData`（MTE1）、`MmadParams`/`Mmad`（Cube）、`DataCopyEnhancedParams`/`DataCopy`（读出）、`Cast`（读回）。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：platform_wide（310P 上立方几何选型）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：910B 的 `Nd2Nz`/`LoadData` 语义与 m200 不同，本探针结论不可直接迁移；A 核非 16 对齐形状需另行扩展探针。

## 根因 / 解决配方

**结论（本卡要传达的可复用事实）**：m200 上 **`[64,16]` B 源 + `Nd2Nz(dValue=16, dstNzC0Stride=16)` + `LoadData2DParams(..., ift=false)` + `Mmad(k=16)` 可用**，`l0c[i][j] = Σ_d eye[i][d]·src[j][d]` 与期望逐元素一致（mode 5 PASS）。因此“K16-native 薄片”路线在几何上成立，不必把所有带都补齐到 64。

**宿主侧两个必备条件**（本会话实证）：

1. torch.ops 的 schema 必须有至少一个 Tensor 参数才能被 dispatcher 路由到 PrivateUse1；纯标量签名（`op_probe(int mode) -> Tensor`）无法调用。改成 `op_probe(Tensor dummy, int mode) -> Tensor`，Python 侧传一个 `torch.zeros(1, device="npu")` 即可。
2. 探针要落独立 kernel（如 `kernel/<generic>_probe.cpp`）+ 独立 schema，不要在主 kernel 里加分支：主 kernel 的 UB/L1 预算与事件序列都会被 `dbg` 分支污染。

**期望值必须在 Python 侧按“物理布局”构造，而不是按直觉的数学转置**：探针里 `A` 用单位阵、`B` 用 `[64,16]` 行主序，则期望 `out[i][j] = src[j][:16]·eye_row_i`——这种“用一个已知矩阵当 A，只观察 B 侧被怎么解释”的设计，使 FAIL 的 first-bad 直接读出布局。

## 完整代码

探针的最小可复用骨架（verbatim，mode 5 分支，含参数）：

```cpp
    if (mode == 5) {
        // [64,16] B 源 Nd2Nz + eye A → l0c[i][j] = Σ_d eye[i][d]·src[j][d]
        TBuf<TPosition::A1> l1aBuf;
        TBuf<TPosition::B1> l1bBuf;
        pipe.InitBuffer(l1aBuf, TILE * sizeof(half));
        pipe.InitBuffer(l1bBuf, TILE * sizeof(half));
        TBuf<TPosition::A2> l0aBuf;
        TBuf<TPosition::B2> l0bBuf;
        TBuf<TPosition::CO1> l0cBuf;
        pipe.InitBuffer(l0aBuf, TILE * sizeof(half));
        pipe.InitBuffer(l0bBuf, TILE * sizeof(half));
        pipe.InitBuffer(l0cBuf, TILE * sizeof(float));
        LocalTensor<half> l1a = l1aBuf.Get<half>();
        LocalTensor<half> l1b = l1bBuf.Get<half>();
        LocalTensor<half> l0a = l0aBuf.Get<half>();
        LocalTensor<half> l0b = l0bBuf.Get<half>();
        LocalTensor<float> l0c = l0cBuf.Get<float>();
        Nd2NzParams ndB;
        ndB.ndNum = 1; ndB.nValue = T64; ndB.dValue = 16;
        ndB.srcNdMatrixStride = 0; ndB.srcDValue = 16;
        ndB.dstNzC0Stride = 16; ndB.dstNzNStride = 1; ndB.dstNzMatrixStride = 0;
        Nd2NzParams ndA;
        ndA.ndNum = 1; ndA.nValue = T64; ndA.dValue = T64;
        ndA.srcNdMatrixStride = 0; ndA.srcDValue = T64;
        ndA.dstNzC0Stride = T64; ndA.dstNzNStride = 1;
        ndA.dstNzMatrixStride = 0;
        LoadData2DParams pB16(0, 4, 1, 0, 0, false, 0);   // (64/16)·(16/16)=4
        LoadData3DParamsV2Pro pC;
        pC.channelSize = T64;
        pC.extConfig = (static_cast<uint64_t>(T64) << 16) |
                       static_cast<uint64_t>(T64);
        MmadParams mp;
        mp.m = T64; mp.n = T64; mp.k = 16;
        mp.cmatrixInitVal = true; mp.cmatrixSource = false;
        DataCopy(l1b, gmSrc, ndB);
        DataCopy(l1a, gmEye, ndA);
        SetFlag<HardEvent::MTE2_MTE1>(ev21);
        WaitFlag<HardEvent::MTE2_MTE1>(ev21);
        LoadData(l0b, l1b, pB16);
        LoadData(l0a, l1a, pC);
        SetFlag<HardEvent::MTE1_M>(ev1M);
        WaitFlag<HardEvent::MTE1_M>(ev1M);
        Mmad(l0c, l0a, l0b, mp);
        PipeBarrier<PIPE_ALL>();
        // readout: D → 行主序（[64,64] 标准形）
        DataCopyEnhancedParams epM;
        epM.blockMode = BlockMode::BLOCK_MODE_MATRIX;
        DataCopy(ta, l0c, DataCopyParams(4, 8, 0, 0), epM);
        SetFlag<HardEvent::MTE3_V>(ev3V);
        WaitFlag<HardEvent::MTE3_V>(ev3V);
        for (int32_t nb = 0; nb < T64 / 16; ++nb) {
            DataCopy(tb[nb * 16], ta[1024 * nb], DataCopyParams(T64, 2, 0, 6));
        }
        SetFlag<HardEvent::MTE3_V>(ev3V);
        WaitFlag<HardEvent::MTE3_V>(ev3V);
        dumpF(tb);
        return;
    }
}
```

（`gmSrc`/`gmEye` 为 host 侧传入的 [64,16] 源与 [64,64] 单位阵；`dumpF(tb)` 把 L0C 读出结果按 [64,64] 行主序写回 GM，由 host 侧逐元素与期望比对——mode 5 的 PASS 输出即由此得到。）

## 设计决策

- 为什么探针而不是在主 kernel 里试：主 kernel 单次迭代 = 编译（分钟级）+ 精度门（分钟级），且任何异常都可能被其他未定 bug 掩盖；探针把一个几何问题压缩成一次编译 + 秒级运行。
- 为什么一个 mode 只测一件事：多变量同测时 FAIL 无法定位；本会话六个模式的 first-bad 分别指向“`src1RepStride` 被忽略”“`v4dtrans` 输出交错”“`Brcb` 输出是 `[16,64]` 不是 `[64,16]`”“`Transpose` 只吃连续 16×16 tile”。
- 为什么保留 `[64,64]` eye 当 A：单位阵让 `l0c` 直接暴露 B 侧的布局，无需反推乘加。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：310P（dav-m200 / DAV_2002）。
- 目录：`kernel/<generic>_probe.cpp`（探针 kernel）、`host/<generic>_probe_host.cpp`（schema + 绑定）、`tests/probe_check.py`（期望值比对脚本）。
- 设备选择：`ASCEND_RT_VISIBLE_DEVICES` 指定卡；探针单 block 单核。

## 性能影响

本卡是**选型前置验证**，本身不产生性能收益；它决定的是后续实现能否走 K16-native 薄片路线（避免把 K 维 padding 到 64 带来的立方空转）。本会话最终 v2（含 K64-native 带环 + 因子折进操作数）相对旧逐行路线约 1.4x，但该相对值不可归因到本探针。

## 预防

- 任何“我猜硬件这样解释布局”的假设，先写探针；探针的期望值要用能直接读出布局的输入（单位阵、递增序列）。
- 探针必须落独立文件/schema，不要在主 kernel 里加 `dbg` 分支做实验。
- 纯标量 schema 无法路由到 PrivateUse1，探针签名要带 Tensor。

## 验证信号

来源说明：本卡来自 310P 会话内独立探针算子的一次运行（同一进程十个模式），结果由 device 侧 dump 与 Python 侧逐元素比对产生。

- `mode 5 [PASS]`：`[64,16]` B + `Mmad k=16` 输出与期望逐元素一致（来源平台：310P；证据等级：tool_observed）。
- `mode 0/1/2/3/4` 的 FAIL 及 first-bad 值与本卡“失效边界/坏实践”一致（来源平台：310P；证据等级：tool_observed）。
- 探针的用法（改主 kernel 前先隔离几何假设、每个模式一条 dump）在本会话后续排查中反复使用；但**该 K16 几何本身未进入终版**——终版是 K64-native 带环，故本卡的价值是“探针方法论 + 已证伪的几何边界”，不是“K16 路线已验证落地”（来源平台：310P；证据等级：artifact_verified）。

## 失效边界

- 只在 310P + CANN 9.1.0 上验证；`LoadData2DParams` 的第二个参数（本卡取 4 = `(64/16)·(16/16)`）与 `nValue/dValue` 的整数关系是硬约束，换形状必须重算。
- `pC.extConfig` 的打包方式（`channelSize << 16 | n`）按本会话实测反推，未查文档确认通用形式。
- 探针只验证了 `m=64, n=64, k=16` 与 `m=64, n=64, k=64`；其它 m/n 未验证。
- 未决项：
  - **复现并追根因到机制层**：`ift=false` 在此几何下的精确语义（是否等价于“B 取转置视图”）本会话只按输出反推，未查证。
  - K16-native 在完整 kernel 中的收益未单独消融（最终实现走的是 K64-native 带环）。

## 坏实践

- 在主 kernel 里加 `if (mode == N)` 做几何实验：编译一次几分钟、事件与缓冲预算全被分支污染。
- 探针期望值按“数学上应该的转置”写：本会话前五个模式因此全部误报 FAIL，白读一轮结果。
- 用纯标量 schema 暴露探针：dispatcher 无法路由，报错信息与几何问题无关，容易误判。

## 误诊

- 把 `mode 2/3/4`（`Brcb`/`Transpose`/列广播链）判成“API 损坏”：实际是探针 dump 的落点布局假设错（`Brcb` 输出按 16 段排布、`Transpose` 只处理连续 16×16 tile），值本身正确，后由主 kernel 的 `colBcast16` 修正。相反，`mode 0`（`BinaryRepeatParams` 行广播乘）与 `mode 1`（`v4dtrans` 输出交错）的 FAIL 是**真实语义**，不是期望值写错。
