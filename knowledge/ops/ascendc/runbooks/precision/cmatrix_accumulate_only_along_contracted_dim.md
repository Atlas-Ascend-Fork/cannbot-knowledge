---
type: Runbook
title: K 维分半时 W 的两半要各出一块 l0c，不能累加进同一块
description: 对 w = A @ kq（kq 的列按 K 分半）连续两次 Mmad 且 cmatrixInitVal=false，会把两半加进同一 n 块。
tags: [task.debugging, topic.programming_model.execution_unit.cube, topic.implementation.pipeline]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Mmad.md
    role: primary
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-10-28T09:51:16Z"
platforms: ["310p"]
---

# K 维分半时 W 的两半要各出一块 l0c，不能累加进同一块

## 现象

算子支持 K 维 64/128 两种宽度（`NKH = 1` 或 `2`）。`w = A @ (kqᵀ)` 的 B 操作数按 K 分半（`kq` 的列 `[0,64)` 与 `[64,128)` 各推成一个 B 槽）。首版为了“一次算完”，对两半连续两次 `mRound`，第二半用 `cmatrixInitVal=false` 继续累加：

```cpp
            // ---- w = A' @ kq（kh 累加）→ lf（M 已消费）----
            mRound(B_KQT, A_AKK, true);
            if (NKH > 1) {
                mRound(B_KQT + TILE, A_AKK, false);
            }
            readout();
            reapTo(lf);
            packPush(A_W, lf);
```

症状：`NKH=1` 的用例正常；`NKH=2`（K=128）的用例 `w`（进而 `w@S`、`v_new`、`o`）错误，误差不随其它修复收敛（改完因子折叠方向后仍剩 ~7e-3，末态更差）。

## 适用场景

- 工程形态：AscendC kernel 直调，`Mmad` + `cmatrixInitVal` 累加。
- API 路径：`MmadParams.cmatrixInitVal`、`mRound`/`readout`/`l0c`。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：operator_family（K 维分块 + 一次 `Mmad` 聚合）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：累加维是**真实的收缩维**时（例如输出第一项对 K 求和、`w@S` 对 K 求和），连续累加才是正确的。

## 判别方法

**根因**：`cmatrixInitVal=false` 的含义是“在已有 l0c 上继续累加”。这里两半 B 槽的差别在 **n（输出列）方向**（`kq` 的 K 列分半 → 输出的 w 列分半），不在收缩维 `k`。所以第二次 `Mmad` 把“w 的右半”加进了“w 的左半”的同一块 l0c，等于 `w_left + w_right`；而随后的 `packPush(A_W, lf)` 也只推了一块，右半从未单独存在。

判据：**看 B 槽切换的是哪个维**——切换的是收缩维（`k`）→ 应累加；切换的是输出维（`m`/`n`）→ 必须各自独立的 l0c。

## 解决配方

**before（错误，verbatim）**：

```cpp
            mRound(B_KQT, A_AKK, true);
            if (NKH > 1) {
                mRound(B_KQT + TILE, A_AKK, false);
            }
            readout();
            reapTo(lf);
            packPush(A_W, lf);
```

**after（每半独立一次 Mmad + 读出 + 推槽，verbatim）**：

```cpp
            // ---- w = A' @ kq（n 半各自独立 l0c, 勿跨半累加）----
            for (int32_t kh = 0; kh < NKH; ++kh) {
                mRound(B_KQT + kh * TILE, A_AKK, true);
                readout();
                reapTo(lf);
                packPush(A_W + kh * TILE, lf);
            }
```

对照：同一 kernel 里的输出第一项与 `w@S` 用的是**累加**形式，因为它们的 B 槽切换的是 K（收缩维）：

```cpp
                mRound(B_ST + vh * NKH * TILE, A_QG, true);
                mRound(B_ST + (vh * NKH + 1) * TILE, A_QG + TILE, false);
```

（`B_ST` 的槽按 K 分半、`A_QG` 也按 K 分半 → 正确的跨半累加。）

## 设计决策

- 为什么不做“把两半拼成一个 `[64,128]` B 槽再一次 Mmad”：B 槽的 `Nd2Nz` 形状与 L1 预算按 `[64,64]` 设计，拼接会破坏既有的推送/装载节奏。
- 为什么要两次 `readout`：两半的结果必须分别落到独立的 UB 区（`A_W`、`A_W+TILE`），否则只有一块能进后续的 `w@S` A 操作数。
- 为什么把判据写成“收缩维 vs 输出维”：这是唯一稳定的判断方式；靠“维度名称”或“看起来对称”极易出错（本卡就是把 n 当成了 k）。
- 路线优先级：recommended_fastpath。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：Ascend310P3（dav-m200 / DAV_2002）。
- 槽位：`A_W` 为 2 tile 区（两半各一）、`B_KQT` 为 2 tile 区、`B_ST` 为 4 tile 区（K 半 × V 半）。
- 尺寸：`TILE = 4096` 元素。

## 完整代码

after 的完整因果单元：

```cpp
            for (int32_t kh = 0; kh < NKH; ++kh) {
                mRound(B_KQT + kh * TILE, A_AKK, true);
                readout();
                reapTo(lf);
                packPush(A_W + kh * TILE, lf);
            }
```

## 性能影响

本卡是正确性修复；代价是 `NKH=2` 时 `w` 多一次 `readout` + 一次 `pushAt`（约多两条 MTE/V 调用），可忽略。

## 预防

- 每次写 `cmatrixInitVal=false` 前，明确写下“这次 Mmad 的 B 槽与上一次差在哪个维”，并在注释里标注该维。
- 同一 kernel 里同时存在“累加对”与“独立对”时，在代码里相邻注释区分（本例两处相隔不过百行）。
- K 维分半的支持（`NKH=2`）必须单独做用例；`NKH=1` 的用例永远不触发这类错误。

## 验证信号

来源说明：本卡来自 Ascend310P3 会话内 K=128 用例的逐轮误差收敛观察与修复后的复测。

- 修复前：`NKH=2` 用例误差在改正因子折叠后仍停在 ~7e-3（末态 0.145 量级），不随其它修复收敛（来源平台：310P；证据等级：tool_observed）。
- 修复后：该误差项消失（该用例当时仍受其它独立 bug 影响，最终随全套修复过门）（来源平台：310P；证据等级：tool_observed）。
- 终版全套精度用例 `50/50 PASS`（来源平台：310P；证据等级：artifact_verified）。

## 失效边界

- 只在 Ascend310P3 + CANN 9.1.0 验证；`cmatrixInitVal` 语义在各代一致，但累加精度（f32 l0c）在不同 tile 尺寸下的行为未验证。
- 本卡依赖“`B_KQT` 的槽按 n 分半”这一实现事实；若改为按 k 分半，判据与结论都会反转。
- `NKH > 2` 的分半未验证。
- 未决项（优先）：修复前的误差为何没有更大（两半相加而非覆盖）——因为 w 两半量级接近，相加后误差被下游 `w@S` 部分抵消，未定量分析。

## 坏实践

- 用 `cmatrixInitVal=false` 做“批量”累加而不确认 B 槽切换的维。
- 只在 K=64 的用例上验证 K 维分块逻辑。
- 把“两半相加”的误差当成数值精度问题继续调因子。

## 误诊

- 一度认为 `A_W + TILE` 槽位与 `A_AQK` 槽重叠（槽布局确实相邻），去改常量表；实际槽没重叠，问题是只推了半块。
