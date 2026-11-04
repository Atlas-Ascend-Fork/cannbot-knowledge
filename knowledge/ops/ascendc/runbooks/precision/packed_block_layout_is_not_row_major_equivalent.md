---
type: Runbook
title: 打包块布局的 [64,64] 块不能用整块线性拷贝接续 GM
description: 四个 [64,64] 块打包在 UB 里并不是 [128,128] 的行主序；初态载入与末态写回都必须逐块（逐行）拷贝。
tags: [task.debugging, topic.data_movement.layout_transform, topic.data_movement.data_copy]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/data_move_concept.md
    role: constraint
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-10-28T09:51:16Z"
platforms: ["310p"]
---

# 打包块布局的 [64,64] 块不能用整块线性拷贝接续 GM

## 现象

递推状态 `S` 在 UB 里按“`[64,64]` 块打包”存放：`sTt2[(vh*NKH + kh)*TILE + r*T64 + c]`，四个块（NV=2 × NK=2）依次排在同一缓冲里。初态从 GM 载入、末态写回 GM，首版都按“整块线性拷贝”写：

```cpp
        // ---- 初态 S_T [NV,KP] ← GM（线性整块）----
        DataCopy(sTt2, gmS0[static_cast<int64_t>(u) * NVw * KPw],
                 DataCopyParams(static_cast<uint16_t>(NVw * KPw * 2 / 32), 1,
                                0, 0));
        SetFlag<HardEvent::MTE2_V>(ev2V);
        WaitFlag<HardEvent::MTE2_V>(ev2V);
```

写回同理：

```cpp
        DataCopy(gmStf[static_cast<int64_t>(u) * NVw * KPw], sTt2,
                 DataCopyParams(static_cast<uint16_t>(NVw * KPw * 2 / 32), 1,
                                0, 0));
```

症状（单 chunk 用例能过，`NV=KP=128` 的用例全错）：

- 初态 dump 出现**行置换**：`kern` 的第 1 行内容等于 `ref` 的第 2 行、`kern` 的第 2 行等于 `ref` 的第 1 行，第 30 行对应到别处；
- 末态误差随 chunk 数累积；
- 同一个 `[64,64]` 块的第 0 行往往精确（线性拷贝的最前一段恰好对齐）。

## 适用场景

- 工程形态：AscendC kernel 直调，UB 里用“块打包”布局（多个 `[64,64]` 块首尾相接）表示一个更大的逻辑矩阵。
- API 路径：`DataCopy` + `DataCopyParams(count, len, srcStride, dstStride)`、`DataCopyParams(T64, 4, ...)`（逐行）。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：platform_wide（所有“打包块 ↔ GM 行主序”的搬运）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：若 UB 侧就是“与 GM 同构的行主序 `[NV,KP]`”，整块线性拷贝才是对的；本卡针对打包块。

## 判别方法

**根因**：`[128,128]` 的逻辑矩阵按块打包成 `[B00][B01][B10][B11]`（每个 4096 个 half 连续），而 GM 侧是行主序 `[128,128]`（每行连续 128 个 half）。两者**只在“单块且 K=64”时恰好一致**；一旦 NV 或 KP > 64，块打包的线性顺序 = “先块 vh，再块 kh”，与 GM 的“先行后列”完全不同。

两个容易踩的中间形态：

1. “整块线性拷贝”：把 `sTt2` 的前 `NVw*KPw*2/32` 个块直接读到 GM——只搬了前两个打包块的行，且顺序错；
2. “一次 strided 拷贝”：`DataCopyParams(T64, 4, 4, 0)`（读 64 行、每行 4 块、源跳 4 块）在 `NV/KP > 64` 时同样实证出现块/行置换。

## 解决配方

**after（初态：逐块 + 块内逐行线性拷，verbatim）**：

```cpp
        // ---- 初态: S_T [NV,KP] ← GM → 打包 [64,64] 块（逐行线性拷;
        //      线性整块与 {64,4,4,0} 跨距形在 NV/KP>64 时均实证块/行置换）----
        for (int32_t vh = 0; vh < NVH; ++vh) {
            for (int32_t kh = 0; kh < NKH; ++kh) {
                const int64_t gBase =
                    static_cast<int64_t>(u) * NVw * KPw +
                    static_cast<int64_t>(vh) * T64 * KPw + kh * T64;
                for (int32_t r = 0; r < T64; ++r) {
                    DataCopy(sTt2[(vh * NKH + kh) * TILE + r * T64],
                             gmS0[gBase + r * KPw],
                             DataCopyParams(4, 1, 0, 0));
                }
            }
        }
        SetFlag<HardEvent::MTE2_V>(ev2V);
        WaitFlag<HardEvent::MTE2_V>(ev2V);
```

**after（末态写回：逐块、块内按行跨距，verbatim）**：

```cpp
        for (int32_t vh = 0; vh < NVH; ++vh) {
            for (int32_t kh = 0; kh < NKH; ++kh) {
                DataCopy(gmStf[static_cast<int64_t>(u) * NVw * KPw +
                               static_cast<int64_t>(vh) * T64 * KPw +
                               kh * T64],
                         sTt2[(vh * NKH + kh) * TILE],
                         DataCopyParams(
                             T64, 4, 0,
                             static_cast<uint16_t>((KPw - T64) * 2 / 32)));
            }
        }
```

写回之所以能“一次 64 行”（`T64, 4, 0, stride`）：源是打包块（连续 64 行 × 4 块），目的行跨距 = `KPw` 的一半块数。载入侧本可以对称地写成 `T64, 4, (KPw-T64)*2/32, 0`，但本会话实测该跨距形在 `NV/KP>64` 时出错，因此载入保留“逐行”这一最保守形态。

## 设计决策

- 为什么载入/写回不对称（逐行 vs 逐块带跨距）：写回的跨距形经实测正确（末态误差从 0.145 量级降到 6.4e-05 量级），载入的跨距形经实测错误；错误来源可能是“源在 GM 的行间距 + 目标打包”组合，未追到机制层，故取最保守实现。
- 为什么不用 `Nd2Nz`/立方辅助搬运：状态张量要按打包块喂给后续 `Mmad`，走 MTE2 直搬最直接。
- 代价：载入每块 64 次 `DataCopy`（4 个块 = 256 次），是本 kernel 的一处 MTE 调用密集点；因只在每 chunk 首尾各一次，未成为瓶颈。
- 路线优先级：recommended_fastpath。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：Ascend310P3（dav-m200 / DAV_2002）。
- 布局：`sTt2` 为 `[NVH*NKH][64][64]` half；GM 侧 `gmS0/gmStf` 为 `[units][NVw][KPw]` half。
- host 侧状态布局：`S -> S_T[v,k]`（host 侧对 v_first 先转一次再统一转置），与 kernel 的 `[v][k]` 约定一致。

## 完整代码

初态载入与末态写回的完整因果单元已在上节内联（两个 after 代码块）。可直接复用的骨架：

```cpp
        for (int32_t vh = 0; vh < NVH; ++vh) {
            for (int32_t kh = 0; kh < NKH; ++kh) {
                const int64_t gBase = static_cast<int64_t>(u) * NVw * KPw +
                    static_cast<int64_t>(vh) * T64 * KPw + kh * T64;
                for (int32_t r = 0; r < T64; ++r) {
                    DataCopy(sTt2[(vh * NKH + kh) * TILE + r * T64],
                             gmS0[gBase + r * KPw], DataCopyParams(4, 1, 0, 0));
                }
            }
        }
        SetFlag<HardEvent::MTE2_V>(ev2V);
        WaitFlag<HardEvent::MTE2_V>(ev2V);
```

## 性能影响

本卡是正确性修复；代价是初态载入从“1 次 `DataCopy`”变成“每块 64 次”（共 256 次）。因为只在每 chunk 首尾执行，会话内未观察到该段成为主口径瓶颈。

## 预防

- 只要 UB 侧是“块打包”，就先把逻辑布局与线性地址的映射画出来，再写 `DataCopyParams`；不要用“单块用例通过”外推。
- 用带 `[1,1,128,128]`（`NV/KP > 64`）的用例做搬运验证，单块用例（`K=64`）不具判别力。
- dump 比对要打印“多行 + 非首行”（本卡的证据就是第 1/2/30 行互换）。

## 验证信号

来源说明：本卡来自 Ascend310P3 会话内对初态/末态张量的 device dump 与参考实现的逐元素比对。

- 修复前初态 dump 呈行置换（`kern` 行 1 = `ref` 行 2、行 2 = `ref` 行 1，行 30 错配）（来源平台：310P；证据等级：tool_observed）。
- 修复前一版“写回逐块”落地后，末态误差从 0.145 量级降到 6.4e-05 量级（来源平台：310P；证据等级：tool_observed）。
- 初态改逐行后该误差项消失；终版全套精度用例 `50/50 PASS`（来源平台：310P；证据等级：artifact_verified）。

## 失效边界

- 只在 Ascend310P3 + CANN 9.1.0 验证；`DataCopyParams` 跨距语义在 `NV/KP>64` 时的异常行为未追到机制层。
- 逐行载入要求 GM 侧每个块的行是 4 块（64 half）连续；若 K 维不是 64 的整数倍，需改 `4` 与跨距。
- 写回的“逐块带跨距”形态在本会话的用例集上正确，但未覆盖 `KPw` 非 128 的情形。
- 未决项（优先）：`{T64, 4, (KPw-T64)*2/32, 0}` 在载入方向出错、在写回方向正确的差异原因未查证；初态逐行载入（256 次 `DataCopy`）在更大 KP（如 256）时的成本未测。

## 坏实践

- 用“整块线性 `DataCopy`”在打包块布局与行主序之间对接。
- 用一次 strided `DataCopy` 假设它等价于“按块取子矩阵”。
- 用单块（K=64）用例验证搬运布局。

## 误诊

- 曾两次“以为已修复”：补丁脚本因 old-string 不匹配静默失败，实际文件仍是旧线性拷贝，于是把残余误差误判为“另有 bug”；后来用行号定位重打才落地。教训：补丁后必须回读文件确认。
