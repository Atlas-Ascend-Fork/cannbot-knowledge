---
type: Runbook
title: 负结果：m200 的向量转置不能替代立方转置取操作数
description: Transpose 只吃连续 16×16 tile、v4dtrans 输出交错、BinaryRepeatParams 行广播被忽略——整块 [64,64] 转置仍应交给立方。
tags: [task.optimization, topic.data_movement.layout_transform, topic.programming_model.execution_unit.vector]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_layout_conversion/Transpose.md
    role: constraint
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-10-28T09:46:50Z"
platforms: ["310p"]
---

# 负结果：m200 的向量转置不能替代立方转置取操作数

## 现象

在分块递推算子里，几乎每一步立方都要两种形态的同一矩阵（`M` 与 `Mᵀ`、`kq` 与 `kqᵀ`、`v_new` 与 `v_newᵀ`）。首版为了省立方轮次，尝试“在 UB 里用向量指令把 `[64,64]` 转置一次，然后直接推 A 槽”——候选手段有三个：

1. `Transpose<half>`（AscendC 的 16×16 转置原语）；
2. 内建 `vtranspose` / `v4dtrans`（`__builtin_cce_v4dtrans`，声明在编译器的 builtin 头里）；
3. `Mul` 配 `BinaryRepeatParams` 的行广播（把 `[64]` 向量按行广播后相乘）。

三个都试过，结论是**都不能可靠地替代“让立方在取 B 操作数时转置”**。探针结果（同批“独立探针”卡的同一探针）：

```
mode 0 [FAIL] BinaryRepeatParams row-bcast Mul first-bad=[(1, 0, 2.0, 4), (1, 1, 2.0, 4), (1, 2, 2.0, 4)]
mode 1 [FAIL] v4dtrans [64,8]->[8,64] first-bad=[(0, 1, 9.0, 2), (0, 2, 17.0, 3), (0, 3, 25.0, 4)]
  mode1 rows0-2 x cols0-7: [[1.0, 9.0, 17.0, 25.0, 33.0, 41.0, 49.0, 57.0], [2.0, 10.0, 18.0, 26.0, 34.0, 42.0, 50.0, 58.0], [3.0, 11.0, 19.0, 27.0, 35.0, 43.0, 51.0, 59.0]]
mode 3 [FAIL] Transpose<half> tile first-bad=[(0, 16, 2.0, 0), (0, 17, 18.0, 0), (0, 18, 34.0, 0)]
```

解读：

- `mode 1`：输入 `[64,8]`（行 i 全为 `i+1`）经 `v4dtrans(dst, src, 64, 8, false)` 后，`dst[0]` 得到 `[1,9,17,25,...]`——即按 8 元素步进取值，输出是**交错**的，而不是普通转置。语义与“nSize/cSize/hSize/wSize”四维的解释强相关，按“二维转置”使用不成立。
- `mode 3`：`Transpose<half>(dst[t*16], tmp[t*256])` 只有在**源是连续的 16×16 tile**时才对；把整块 `[64,64]` 当作四个 tile 直接拼，会得到按 16 行块交错的输出（`(0,16)` 处出现下一段的第 2 个值）——所以正确用法必须先把 tile 排成连续块，再由 MTE 拷贝重排（这就是 `colBcast16` 的做法）。
- `mode 0`：`BinaryRepeatParams(dstRepStride, src0RepStride, src1RepStride, ...)` 的 `src1RepStride` 被忽略，行广播乘法得到的不是“每行乘同一标量向量”，据此不能做行广播。

## 适用场景

- 工程形态：AscendC kernel 直调，Cube+Vector 混合，需要“同一矩阵的转置形态”参与立方。
- API 路径：`Transpose<half>`（Vector）、`vtranspose`/`v4dtrans`（builtin）、`Mul` + `BinaryRepeatParams`、`Mmad`（取 B 操作数时天然转置）。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：platform_wide（310P 上的向量/立方选型负结果）。
- 路线优先级：banned（对本卡的三种替代手段）。
- 明确不适用 / 未验证场景：`[16,16]` 及更小的**单 tile** 转置是可用且高效的（`colBcast16` 就靠它）；本卡否定的是“整块 64×64 一次转置”与“用向量转置替代立方的 B 转置”。

## 根因

**根因**：m200 的向量转置原语是 **tile 级**（16×16、连续地址），且 `v4dtrans` 的语义由四维参数决定，不是二维转置；`BinaryRepeatParams` 的重复步进只对 `src0` 生效，`src1` 的步进被忽略。因此“把 `[64,64]` 一次转成 `[64,64]ᵀ`”没有一条现成的向量路径。

**结论（负结果）**：

- 需要 `Mᵀ` 参与立方时，**不要**在 UB 里做整块转置；改为把 `M` 以紧凑形式推到 GM 槽，再 `Nd2Nz + LoadData2D(ift=false)` 让立方在取 B 时得到转置视图（本 kernel 的 `transPush(T_TMP, B_xxx)` 就是这个模式）。
- 若确实需要 UB 里的整块转置，唯一实测可用的路径是 `colBcast16` 式的“tile 级 `Transpose` + MTE 重排”（4 次 16×16 转置 + 7 次 strided 拷贝），成本约十余条指令，仅适合 `[64]`→`[64,64]` 这类广播构造，不适合每 chunk 多次的矩阵转置。
- `v4dtrans` 在 m200 上可按四维语义工作，但本会话未找到稳定的二维转置用法，**按不可用处理**。

**可用的对照实现（`colBcast16` 的 tile 级用法，verbatim）**：

```cpp
    auto colBcast16 = [&](const LocalTensor<half>& dst,
                          const LocalTensor<half>& src) __aicore__ {
        Brcb<half>(bcT, src, 8, BrcbRepeatParams(1, 8));
        for (int32_t t = 0; t < 4; ++t) {
            Transpose<half>(bcT2[t * 256], bcT[t * 256]);
        }
        PipeBarrier<PIPE_ALL>();            // V 写 → UB 拷贝（双端律）
        for (int32_t t = 0; t < 4; ++t) {   // 段 t → dst 列 [16t,16t+16)
            DataCopy(dst[t * 16], bcT2[t * 256],
                     DataCopyParams(16, 1, 0, 3));
        }
        for (int32_t rr = 1; rr < 4; ++rr) {   // [16,64] → [64,64]
            DataCopy(dst[rr * 16 * T64], dst, DataCopyParams(16, 4, 0, 0));
        }
        PipeBarrier<PIPE_ALL>();
    };
```

## 设计决策

- 为什么最终选“立方取 B 时转置”：`Nd2Nz` 的 `LoadData2D(ift=false)` 已经产出了转置视图，代价是 B 源必须落 GM 槽（一次 `pushAt`）；相比在 UB 里做 4 次 `Transpose` + 多次 MTE 重排，指令数与寄存器压力都更小。
- 为什么不再尝试 `v4dtrans`：探针一次就给出交错输出，且参数语义（四维）无法从文档侧确认；在“立方路径已验证”的前提下继续投入属于负收益。
- 为什么保留 `colBcast16`：列广播（`[64]` → 每行相同）在 m200 上没有 `DataCopy(srcStride=0)` 这种捷径（见精度类卡），tile 级转置是唯一稳定路径。
- 路线优先级：banned（三种替代手段：用向量转置整块替代立方转置）。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：310P（dav-m200 / DAV_2002）。
- builtin 声明位置：`/usr/local/Ascend/cann-9.1.0/.../ccec_compiler` 头内 `__attribute__((clang_builtin_alias(__builtin_cce_v4dtrans)))` / `..._vtranspose`，只有 `(...)` 形式的弱声明，无签名可依。
- 探针：`kernel/<generic>_probe.cpp`（独立 kernel + torch.ops）。

## 性能影响

本卡为负结果，**不提供收益**；它的价值是避免把“UB 整块转置”当成廉价替代而引入错误与返工。会话内采用“立方取 B 转置”路线后，v2 相对旧逐行路线约 1.4x（含其它手段，不可归因到本卡）。

## 预防

- 见到“矩阵转置”需求，先问：这个转置能否由下游的 B 操作数取用方式顺带完成？（`Nd2Nz` + `ift=false`）
- 用 `Transpose` 前确认源是连续 16×16 tile；否则必须先做 tile 排布。
- 不要把 `BinaryRepeatParams` 当作广播原语；行/列广播要走 `Brcb` 或显式张量。
- 对 builtin（`vtranspose`/`v4dtrans`）先写探针确认语义，不要凭名字假设。

## 验证信号

来源说明：本卡来自 310P 会话内的独立探针算子运行（mode 0/1/3 的 first-bad 与输出矩阵）以及主 kernel 的最终路线选择。

- `mode 0` 行广播 `Mul` FAIL，first-bad 显示 `src1` 未按预期推进（来源平台：310P；证据等级：tool_observed）。
- `mode 1` `v4dtrans` 输出交错（`dst[0] = [1,9,17,...]`）（来源平台：310P；证据等级：tool_observed）。
- `mode 3` `Transpose` 整块拼 tile 输出按 16 行交错（来源平台：310P；证据等级：tool_observed）。
- 采用立方转置路线后全套精度 `50/50 PASS`，终版为会话内 v2 提交（来源平台：310P；证据等级：artifact_verified）。

## 失效边界

- 只在 310P + CANN 9.1.0 上验证；910B 有 `Transpose` 的更大粒度原语（未验证）。
- 本卡不否定 `Transpose` 本身：单 tile（16×16）转置是 `colBcast16` 的关键手段。
- `v4dtrans` 的结论是“本会话未能找到可用形式”，不等于“硬件不支持”；四维语义若被正确建模，可能仍有可用路径（未决）。
- 未决项：
  - **复现并追根因到机制层**：`v4dtrans` 的参数语义（`imageSize`/`cSize`/bool 方向）未查证，交错输出的成因未定。
  - `Transpose` 在 `[32,32]`/`[64,16]` 等非 16×16 形状上的排布规则未系统验证。

## 坏实践

- 用 `Transpose<half>` 直接对 `[64,64]` 的四个 tile 连续调用（`dst[t*16] ← tmp[t*256]`）并假设结果就是整块转置：输出按 16 行交错。
- 用 `Mul` + `BinaryRepeatParams(..., src1RepStride=0)` 做行广播：`src1RepStride` 被忽略，得到错误乘积。
- 把 `v4dtrans` 当二维转置用：输出交错且难以反推。

## 误诊

- 一度认为 `Brcb`/`Transpose` “值错了”，实际是探针 dump 的布局假设错（值对、排布不同）；真正的 API 限制是“tile 级 + 连续地址”。
