---
type: Runbook
title: "LoadData2D ifTranspose=true 不等于 B 视图=源"
description: "想用 ifTranspose=true 省掉 V 的预转置，全量用例系统性失败；单 tile 穷举八种置换假设均不吻合。该语义在本轨迹未定论，不要按对称性假设使用。"
tags: [task.debugging, topic.data_movement.data_copy, topic.programming_model, topic.architecture]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/examples/01_simd_cpp_api/03_basic_api/03_matrix_compute/load_data_l12l0/scripts/load2d.py
    role: example
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-10-28T09:52:17Z"
platforms: ["310p"]
---

# LoadData2D ifTranspose=true 不等于 B 视图=源

## 现象

Cube 链里第二个乘加需要"左矩阵 × V"。V 的 GM 布局是行主序（行 = 位置，列 = 特征），而 B 操作数进 L0B 需要能表达成 NZ 分形布局。

沿用 K 的装载公式（`Nd2Nz` 搬入 L1、`LoadData` 到 L0B）时，源算子与兄弟算子走的是 `ifTranspose=false`，并依赖 host 侧先把 V 预转置成 `[d, j]` 布局。为了省掉这次 host 预转置，尝试改用 `LoadData2DParams(..., ifTranspose=true, ...)`，期望"B 视图 = 源本身"，从而可以直接读 V 的自然布局。

结果：

- 全量用例**系统性失败**，误差 1e-2~3e-2 级，而参考与金标之间只有 5e-4 级；
- 失败不是"某几个形状"：跨多个 batch/head/tile 用例一致失败；
- 单 tile 对拍时，穷举 8 种"如何解释这个 B 视图"的置换假设（原样、转置、对称、行/列折叠、再转置等），**没有一种**能把误差压到噪声内（全部 2.5e-2~2.9e-2 级）；
- 逐行误差随行下标单调增长（首行接近噪声、末行 1e-2 级），说明不是"整体转置"这种干净的置换错误。

## 适用场景

- 工程形态：kernel 直调；手写 Cube 链，`Nd2Nz` + `LoadData` + `Mmad`。
- API 路径：`LoadData2DParams(startIndex, repeatTimes, srcStride, sid, dstGap, ifTranspose, addrMode)`、`LoadData(l0b, l1b, params)`、`Nd2NzParams`。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / m200）+ CANN 9.1.0。
- 适用粒度：`operator_family`（负知识，适用范围即"想用 ifTranspose 省搬运"的所有场景）。
- 路线优先级：`banned` —— 在语义查清之前，不要用 `ifTranspose=true` 去替代预转置；已知可行路线是 host 预转置 + `ifTranspose=false`。
- 明确不适用 / 未验证场景：`ifTranspose=true` 的正确用法未知；本卡不否认它有用，只否认"它等于 B 视图 = 源"这个假设。

## 根因

**未定论**。可以确定的是：`ifTranspose=true` **不**等价于"B 操作数视图 = 源矩阵本身"，也不等价于任何单一置换（八种候选都不吻合）。

可排除的解释：

- 不是"转置方向搞反"——把结果再转置一次同样不吻合；
- 不是"单个 tile 的边界问题"——单 tile 对拍也同样失败，且误差随行增长。

剩下的可能性（未验证）：`ifTranspose` 作用的是 L1B 内部的分形排布而非逻辑矩阵视图，因此要求 L1B 已经以某种特定形状装入；或者它与 `srcStride`/`dstGap` 的组合有额外约束。

## 判别方法

遇到"换了个加载参数后误差变成 1e-2 级且逐行增长"时：

1. **先做单 tile 对拍**，固定输入，把 B 矩阵的所有廉价置换假设都试一遍（原样/转置/对称/折叠）。若全部落在同一量级，说明问题不在"置换"，而在"这块数据根本没按你以为的形状进入 L0B"。
2. **看误差的行分布**：逐行单调增长通常意味着"每行取到了错位的源行"（行步长错），而不是整体置换。
3. **优先回退到已知可行的装载路线**，把"省一次预转置"当作独立的性能任务再做。

## 完整代码

被尝试的改动（`ifTranspose=true` 的装载参数）：

```cpp
    LoadData2DParams pB64N(0, static_cast<uint8_t>((T64 / 16) * (T64 / 16)), 1,
                           0, 0, false, 0);   // ift=false → B 视图 = srcᵀ
    // PV 直读 v 自然布局: B 视图 = src 本身（与 S 链对称）
    LoadData2DParams pBIFT(0, static_cast<uint8_t>((T64 / 16) * (T64 / 16)), 1,
                           0, 0, true, 0);    // ift=true → B 视图 = src
```

配套的装载（直接读 V 的自然布局，跳过 host 预转置）：

```cpp
            // -- O += W@V（Dv 半片; 跨 kt L0C 累加）--
            for (int32_t dv = 0; dv < ND; ++dv) {
                // v 自然布局直读（同 K 装载公式; ift=true → B=V）
                const int64_t vOff =
                    (kRowE * H + h) * D + kt * T64 * H * D + dv * T64;
                DataCopy(stB, gmV[vOff],
                         DataCopyParams(T64, 4, static_cast<uint8_t>(kBGapBlk),
                                        0));          // 暖读（行距 H·D）
                SetFlag<HardEvent::MTE2_V>(ev2V);
                WaitFlag<HardEvent::MTE2_V>(ev2V);
                ndB.srcDValue = static_cast<uint16_t>(H * D);
                DataCopy(l1b, gmV[vOff], ndB);
                SetFlag<HardEvent::MTE2_MTE1>(ev21);
                WaitFlag<HardEvent::MTE2_MTE1>(ev21);
                PipeBarrier<PIPE_ALL>();
                LoadData(l0b, l1b, pBIFT);                // ift=true → B=V
```

回退后的写法（`ift=false` + 源本身已是 `[d, j]` 转置布局）：

```cpp
                ndB.srcDValue = T64;
                DataCopy(l1b, gmVT[vTOff], ndB);
                SetFlag<HardEvent::MTE2_MTE1>(ev21);
                WaitFlag<HardEvent::MTE2_MTE1>(ev21);
                PipeBarrier<PIPE_ALL>();
                LoadData(l0b, l1b, pB64N);                // ift=false → B=V
```

八种假设的单 tile 对拍结果（同一份读出数据，`|ours − W@B|` 的最大值）：

```
V           2.499e-02
Vt          2.639e-02
S(V)        2.498e-02
S(V).t      2.709e-02
BT(V)       2.549e-02
BT(V).t     2.931e-02
S(BT(V))    2.537e-02
trueT       2.639e-02
```

## 设计决策

- **回退到"host 预转置 + `ift=false`"**：已知可行、可验证；把"省掉预转置"降级为后续独立性能任务。
- **不在语义未明时继续试参数组合**：`ifTranspose` 与 `srcStride`/`dstGap`/`addrMode` 的组合空间大，盲目枚举成本高且无法证伪。
- **先做最小可辨识矩阵观测，再改整链**：若再做一次，会先用"每个元素编码一个不同常数"的 16×16 矩阵单步读出 L0B，直接看实际排布。

## 系统信息

- 目标平台 Ascend310P3（DAV_2002 / m200），CANN 9.1.0；tile 宽 64，`repeatTimes = (64/16)^2 = 16`（16 个 16×16 分形块）。
- 文件：`kernel/<generic>.cpp`（PV 链装载）、`host/<generic>.cpp`（vT 预转置构建）。

## 预防

- 不要按"兄弟链路对称"推断硬件加载参数语义；未查清语义前，默认走已验证的 host 预转置 + `ift=false`。
- 一次只改一处（装载参数不与输出布局、信标迁移等改动同批提），否则失败后要先做回退归因。
- 排查装载类问题时先用"每元素编码不同常数"的 16×16 最小矩阵单步读出 L0B，直接看排布，而不是从整链误差反推。

## 验证信号

- 全量用例系统性失败：`ours ≈ 2.7e-2` 而 `ref ≈ 4.9e-4`（门限 1e-3），跨 batch/head/tile 一致（来源平台：310P；证据等级：tool_observed）。
- 单 tile 穷举八种置换假设，误差全部落在 `2.5e-2`~`2.9e-2`，无一进入噪声级（来源平台：310P；证据等级：tool_observed）。
- 只回退这一处装载（保留同批的其它改动）后精度恢复通过（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- **未决项（优先）**：`LoadData2DParams.ifTranspose` 在 310P/m200 上的真实语义**未定论**。下一个 agent 若要继续，建议从"看 CANN 头文件/doc 对该字段的定义 + 用一个 16×16 的最小可辨识矩阵（每个元素编码一个不同常数）单步读出 L0B 内容"入手，直接观测装载后的实际排布，而不是从整链误差反推。
- 本卡的结论只覆盖"用它替代预转置"这一用法；不否认 `ifTranspose=true` 在别的用法下有效。
- 未验证平台：其它代际未验证。
- 不覆盖"D 维不是 tile 宽整数倍"的情形。
- 与跨代 hand-mmad 的 `ifTranspose` 坑同族但不同代际/不同链路，结论不可直接互推。

## 坏实践

- **按对称性假设推断硬件参数语义**："K 链能这么装，V 链对称所以也能"——这一步在本轨迹里代价是一整轮全量失败。
- **一次改三处**：这次改动与"输出改核内直存""信标迁移"同批提交，导致失败后必须先做"只回退一处"才能归因，白跑了一轮。
- **用整链 e2e 误差反推装载语义**：误差里混着布局、掩码、tile 边界多种因素，单 tile 最小矩阵观测才是有效手段。

## 误诊

- 误诊（agent_reported）：曾认为失败是"转置方向搞反"，于是只把结果再转置一次；误差仍在同一量级，方向判断本身就被推翻。
- 误诊（agent_reported）：也曾归因为"L1B 装入了错误的 stride"，反复调 `srcDValue`；单 tile 八假设实验才把"置换类解释"整体排除。
