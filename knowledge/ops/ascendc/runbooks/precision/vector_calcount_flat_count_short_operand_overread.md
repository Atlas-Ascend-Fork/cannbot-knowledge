---
type: Runbook
title: 向量算子 calCount 是平铺元素数，短操作数切片被越读
description: AscendC 向量 API 的 calCount 是对基址的平铺元素计数，128 元素的 LocalTensor 切片配 cnt=2048 会静默越读相邻 UB；判别方法=逐参数核对 cnt 与物理长度。
tags: [task.debugging, topic.programming_model.execution_unit.vector, topic.implementation.memory_management]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/continuous_compute.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/operator.md
    role: constraint
created_at: "2026-10-28T09:51:47Z"
updated_at: "2026-10-28T09:51:47Z"
platforms: ["310p"]
---

# 向量算子 calCount 是平铺元素数，短操作数切片被越读

## 现象

在 310P（dav-m200）上把分块扫描 kernel 的"行带因子"构建从**逐行**改成**多行块**（一次处理 16 行，`cnt = 16 * K128 = 2048`）以削减向量调用次数。因子式是 `q·2^(gk_i − ρ_r)`，其中带参照 ρ_r 是"每 K 通道一个标量"的一行，即长为 128 的切片 `rho[r * K128]`：

```cpp
                Sub(t2, gk[fb * K128], rho[r * K128], 16 * K128);   // cnt=2048, 但 ρ 只有 128
```

改完精度崩坏，症状随版本漂移：有时整例输出饱和到 f16 上限（`6.554e+04`，即 65504），有时 `A_QGB` tile 与同构 emulation 差 0.16% 相对、bar 值恰好落在某些行带上；同一份代码逐行形式（`cnt = K128`）却是干净的：

```
aq: max 3.661e+04 bad 183    lf: max 3.216e+03 bad 84      ← 块形式
aq: max 3.389e-05 bad 0      lf: max 9.133e-06 bad 0       ← 逐行形式（同一诊断脚本、同一轮）
```

## 适用场景

- 工程形态：Kernel 直调（AscendC 手写 kernel，向量指令级）。
- API 路径：`Cast` / `Sub` / `Maxs` / `Mins` / `Muls` / `Exp` / `Mul` 等向量指令的 `calCount` 参数；`LocalTensor<T> t = buf.Get<T>()[offset]` 形式的偏移切片。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / m200）+ CANN 9.1.0。
- 适用粒度：`platform_wide`（calCount 语义是 API 层性质）。
- 路线优先级：`recommended_fastpath`（把 `cnt` 压到等于所有操作数中最短者的物理长度；需要长操作数时另行物理补齐）。
- 不适用 / 未验证场景：未在 A2/A3 验证同一越读行为（未验证，推断可迁移）；未验证越读在越界后才 32B 对齐边界上的裁剪行为。

## 根因

AscendC 向量指令的 `calCount` 是**对该指令每个操作数基址的平铺元素计数**：编译器/运行时按"起始地址 + calCount 个元素"生成访问区间。`LocalTensor` 的偏移切片 `rho[r * K128]` 只改变**基址**，不携带"这个视图只有 128 个元素"的长度信息，也不会在任何环节做长度校验。

因此 `Sub(t2, gk[fb*K128], rho[r*K128], 16*K128)` 会从 `rho` 的起点连续读 2048 个 float：**前 128 个是真正的 ρ_r，其后 1920 个是紧邻 UB 的内容**（本例是同 TBuf 里的其他向量暂存：`gl`/`betaF`/`eV`/… 的残留值和别带的中间结果）。被参照 ρ 一旦取到垃圾值，因子 `2^(gk−ρ)` 整体乘上 `2^(Δρ)`，误差按 `Δρ` 指数放大——这解释了"有时只是 1e-2 级相对误差、有时直接饱和到 f16 上限"的漂移谱。

判别要点三条：
1. 同一段逻辑，**逐行（cnt=128）正确、多行块（cnt=2048）错误** → 先怀疑操作数长度不匹配，而不是算式；
2. 误差量级随 `cnt`/行带边界跳变（不是随 shape 平滑变化）→ 指向"读到了邻居数据"；
3. 代码审计：把一条向量指令的 `cnt` 与该指令**每个**操作数的物理元素数并列写出来，任何一个 `< cnt` 就是缺陷。

## 判别方法

1. 在 kernel 里对可疑因子 tile 做定点 dump（见"核内 dump 探针"相关经验：MTE2→MTE3 之间必须有全屏障），把 tile 的若干行与 host 侧同构 emulation 逐值比对。
2. 把该段构建**退回逐行**（`for i in 0..15: 各指令 cnt=K128`）再跑同一诊断脚本。若误差从 1e+04 量级掉到 1e-05 量级，即确认是块形式的操作数长度问题。
3. 逐参数核对：本段每条向量指令的操作数分别是 `t2`(2048)、`gk[fb*K128]`(至少 2048)、`rho[r*K128]`(**128**)——第三个不满足 `≥ cnt`，缺陷即在此。

## 解决配方

`before`（块形式，`cnt` 与最短操作数不匹配；q 带因子打包段）：

```cpp
            for (int32_t r = 0; r < 4; ++r) {      // 打包 qgB: 行 i 就地本带因子
                const int32_t fb = 16 * r;
                Cast<float, half>(tD, qk[fb * K128], RoundMode::CAST_NONE, 16 * K128);
                Sub(t2, gk[fb * K128], rho[r * K128], 16 * K128);
                Maxs(t2, t2, -30.0f, 16 * K128);
                Mins(t2, t2, 15.0f, 16 * K128);
                Muls(t2, t2, LN2, 16 * K128);
                Exp(t2, t2, 16 * K128);
                Mul(tD, tD, t2, 16 * K128);
                Cast<half, float>(staging[fb * K128], tD,
                                  RoundMode::CAST_NONE, 16 * K128);
            }
```

同一模式还出现在 k 带因子（`kqB`）与反号形式（`kgqB`，`Sub(t2, rho[r * K128], gk[jb * K128], cnt)`）。

`after`（逐行形式，每条指令的 `cnt` 都等于 128，与最短操作数一致）：

```cpp
            Duplicate(staging, static_cast<half>(0.0f), T64 * K128);
            for (int32_t r = 0; r < 4; ++r) {            // 打包 kqB: 行 i 就地
                for (int32_t i = 0; i < 16; ++i) {
                    Cast<float, half>(rV, qk[(16 * r + i) * K128],
                                      RoundMode::CAST_NONE, K128);
                    Sub(eV, gk[(16 * r + i) * K128], rho[r * K128], K128);
                    Maxs(eV, eV, -30.0f, K128);
                    Mins(eV, eV, 15.0f, K128);
                    Muls(eV, eV, LN2, K128);
                    Exp(e2V, eV, K128);
                    Mul(rV, rV, e2V, K128);
                    Cast<half, float>(staging[(16 * r + i) * K128], rV,
                                      RoundMode::CAST_NONE, K128);
                }
            }
```

两条可选解：
- **A（本轨迹最终采用）**：退回逐行，`cnt` 恒为 128，与 128 元素切片物理等长；代价是向量调用次数回升（本段 4×16 次）。
- **B（可行但需另配容量）**：把 ρ 物理补齐成与 `cnt` 等长的 tile（每行重复同一个 ρ_r），再让块形式用这个补齐后的操作数。本轨迹试过 B，但补齐 tile 落到了容量不足的缓冲上，引出另一类越界（见另一张 UB 容量越界卡）。

## 设计决策

- 起初选"多行块"的动机是削减向量调用数（逐行 64 次 → 块形式 4 次），这是性能驱动的取舍；但块形式引入了"操作数长度不对齐"的隐式前提，收益被排查成本抵消。
- 最终决策：**只对操作数长度天然一致的链做块化**（`qg/kq/kg` 这类纯逐元素链，所有操作数都是整 tile），**凡含 128 元素参照/标量广播的链一律逐行**。这条边界在后续调优中被固定为纪律。
- 被放弃的候选：给向量切片套一层"带长度断言的封装"。被放弃原因是 `LocalTensor` 视图没有长度语义，封装只能在编译期常量层面做，无法覆盖运行期偏移。

## 系统信息

- 平台：Ascend310P3（DAV_2002 / m200），CANN 9.1.0，UB 240KB / 8 核。
- 相关文件：`kernel/chunk_scan.cpp`（带因子构建段）；诊断脚本 `<diag-dir>/chunk_scan/ringd2.py`、`emu_core.py`（host 侧同构 emulation + ring 通路误差统计）。
- 构建：`bash build.sh` → `build/lib<generic>_ops.so`。

## 完整代码

见 `## 解决配方` 的块形式 before 与逐行 after；改动是把"多行块"循环展开成逐行，`cnt` 恒为 `K128`。

## 预防

- 写任何向量指令前，把 `(cnt, 每个操作数的物理长度)` 五个数并列写在纸上；`min(操作数长度) < cnt` 即禁止提交。
- 带"每通道一个标量"的广播语义时，优先用"显式物理补齐的 tile"或"逐行"，不要指望切片视图能表达长度。
- 改"逐行 → 块"这类纯性能重构时，先用同构 emulation 跑一轮 ring 级误差（不是只看最终精度门），把 1e-05 级基线钉住；误差跳到 1e+03 就说明读到了邻居。

## 验证信号

来源：分块扫描 kernel（310P）重写期间对"行带因子构建"的性能重构。以下均为本轨迹内的工具输出。

- 块形式（含 `cnt=16*K128` 配 128 元素 ρ 切片）：同一诊断脚本下 `aq max 3.661e+04 bad 183 / lf max 3.216e+03 bad 84`（来源平台：310P；证据等级：tool_observed）。
- 逐行形式（同一脚本、同一构建流程）：`aq max 3.389e-05 bad 0 / lf max 9.133e-06 bad 0`，且随后整条通路 6/6 迭代通过（来源平台：310P；证据等级：tool_observed）。
- 早前一轮块形式的产物还出现过整例饱和到 f16 上限（`abs(o-r)=6.554e+04`，65504 = f16 上限）（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 本卡的判别结论（`cnt` ≤ 最短操作数物理长度）在所有 AscendC 向量指令上成立；但"越读会踩到哪个邻居"取决于 TBuf 布局，**症状位置会随布局漂移**，不要指望用"错误行号"当稳定判据。
- 若操作数是 `GlobalTensor`，越读会读写到 GM 的相邻区域，可能静默成功而不报错——同样适用本条判据。
- 未验证场景：`cnt` 同时大于多个操作数长度时的优先级/裁剪行为（未验证）。
- **未决项（优先）**：本轨迹把 `cnt` 压回 128 后精度恢复，但**块形式自身的残留错坏未被单独隔离**——退回逐行时同时移除了另一处"补齐 tile 越界"，两者在证据上互相混淆。下一个接续点：在容量充足的独立缓冲上重做一次"仅块化、不含越界"的对照组，验证"只修 `cnt` 是否足以让块形式正确"。
- 未决项：`cnt` 越读是否在 32B 边界被裁剪（本例未观察到裁剪迹象，未验证）。

## 坏实践

- 认为"`LocalTensor` 切片有形状、所以指令只会动这个形状内的元素"——向量指令只认基址 + `calCount`，这是最典型的隐式假设。
- 用"块形式 + 短切片"做性能重构而不先跑 ring 级误差基线，导致误差放大后无法判断是新重构还是既有缺陷。
- 看到饱和到 f16 上限就先去查 clamp 上下界（`Maxs/Mins`），而饱和往往只是"读到了垃圾 → 指数爆掉"的下游表现。

## 误诊

- 曾按"factor 的 clamp 上下界写错"排查（`agent_reported`），因为饱和值 65504 很像 clamp 边界问题；实际 clamp 值 `[-30, 15]` 与设计一致。
- 曾把块形式的错坏一次性归因给"NDDMA/Nd2Nz 陈旧线"（`agent_reported`）；逐行形式在同一装载路径下干净，排除了装载路径。
- **推断（非实测）**："越读的是相邻 msBuf 里的其他暂存"这一步是代码审计推断：内核 dump 只证明块形式下因子值错、逐行下对，未单独 dump 出被越读到的具体内容。
