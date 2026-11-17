---
type: Runbook
title: 带数上限撞顶时末带跨度过大，f16 因子直接爆掉
description: 强门控用例需要约 16 个带，带数上限常量撞顶后末带跨 55 log2，2^±28 超出 f16；抬上限并用 ring 槽即可不增 scratch。
tags: [task.debugging, topic.precision, topic.implementation.memory_management]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/Max.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/DeNormMin.md
    role: constraint
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-11-05T03:51:50Z"
platforms: ["310p"]
---

# 带数上限撞顶时末带跨度过大，f16 因子直接爆掉

## 现象

带状 `Mmad` 路线把 chunk 按“门控跨度”切带（每带内衰减的 log2 跨度受限），每带的行因子 `e = 2^(gk−ρ)` 与列因子 `f = 2^(ρ−gk)` 要落进 f16 A/B 操作数。带数有上限常量 `MAXB`：

```cpp
constexpr int32_t MAXB = 12;        // 带数上限（本卡示例值）
```

绝大多数用例只需 4~6 个带，一切正常。**一个强门控用例**（每 token 约 5.15 log2，每 chunk 末行约 −329）需要约 16 个带：带数撞到 12 后，最后一个带被迫囊括剩余全部行，跨度达 55.8 log2 → 因子需要 `2^{±28}` → f16 无法表示（上限 65504（`2^16` 量级）、下限 `2^-24` 量级），精度直接崩（该用例输出误差 ~7e-3、末态 ~0.14，全部用例中唯一不过）。

## 适用场景

- 工程形态：AscendC kernel 直调，带状切分 + f16 操作数因子。
- API 路径：`Maxs`/`Mins`/`Muls`/`Adds`/`Exp`（因子链）、`pushRows`/`pushAt`（槽）、`Mmad`；scratch 槽常量布局。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：operator_family（任何“按跨度切带 + 因子指数化”的设计）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：若门控跨度天然有界（例如 gates 有界于 1 log2/token），不会撞顶，本卡不适用。

## 判别方法

**根因**：带数上限是**正确性参数**，不是性能参数。撞顶后“剩余行并进末带”会放大该带的因子指数，而 f16 操作数的可表示范围是硬限制。ρ 锚定为**带中点**（源码核对，两版内核一致：`rhoR = 0.5f * (gk.GetValue(fb*128) + gk.GetValue((fe-1)*128))`，卡版 `op30_chunk_gdr.cpp:587-588`、现行版 `:600-601`），故因子指数 = |gk−ρ| ≤ 带宽/2——末带跨 55.8 log2 对应 `2^{±27.9}`（卡内 ±28 与 55.8 自洽）。此前的两处“防御性钳位”（`Maxs(e, −30·ln2)` 只护 e 下侧、`Mins(f, 15·ln2)` 只护 f 上侧）在中点锚定 + 阈值 21 正常切带下**两侧都永不触发（死守卫）**，撞顶时真正危险的 e 上侧（指数可达 +27.9，f16 乘积直接 Inf）反而无钳——钳位只能掩盖、不能修正误差，这也是为什么单纯改钳位或改跨度阈值都看不到改善。

判别：把“带数/分块数的上限”当正确性参数，给它加断言或 dump；先算“最坏参数下需要多少带”，再定上限。

## 解决配方

**after（抬上限 + 带槽 ring-2，不增加 scratch，verbatim）**：

```cpp
constexpr int32_t MAXB = 24;        // 带数上限（带槽 ring-2, 不占额外 scratch）
```

```cpp
constexpr int32_t A_KB   = A_QB + 2 * 2 * TILE;
constexpr int32_t B_KGB  = A_KB + 2 * 2 * TILE;
```

所有带的槽索引改为 ring-2（`r & 1`）：

```cpp
                    pushRows(A_QB + ((r & 1) * NKH + kh) * TILE + fb * T64, stg, sz);
                    pushRows(A_KB + ((r & 1) * NKH + kh) * TILE + fb * T64, stg, sz);
                    pushRows(B_KGB + ((r & 1) * NKH + kh) * TILE, stgB, fe);
```

```cpp
                for (int32_t kh = 0; kh < NKH; ++kh) {   // aq 带 r 行
                    mRound(B_KGB + ((r & 1) * NKH + kh) * TILE,
                           A_QB + ((r & 1) * NKH + kh) * TILE, kh == 0);
                }
```

（共 7 处，全部 `(r * NKH + kh)` → `((r & 1) * NKH + kh)`。）

**为什么 ring-2 能白拿上限**：带循环的结构是“每带先构建并推送 A/B，再就地消费（`mRound` 两轮：aq、lf）”，即带 r 的槽在其消费结束时已全部用完，带 r+1 的推送可以覆盖它。因此只需 2 组槽（奇偶交替），槽区从 `2*MAXB*TILE` 降到 `2*2*TILE`，抬 `MAXB` 不增加 scratch。

## 设计决策

- 为什么抬到 24 而不是“按需动态”：`bnd[]` 数组本来就有固定上界；实测最强用例每 chunk 门控跨度约 330 log2（末行 −329.6 = 64×5.15），按 400 log2 设计余量取 24（400/21 ≈ 19 < 24，跨度口径裕量约 1.26x；带数口径 24/15 ≈ 1.6x，见验证信号扫描），且 ring-2 后零成本。全集覆盖性扫描见验证信号。
- 为什么不改“带跨度阈值 21”：本会话先试过把阈值从 26 降到 21（`span > 21.0f || i - bnd[nb-1] >= T64/4`），**误差完全没有变化**（仍是 6.861e-3）——说明当时真正的限制是带数上限，而不是跨度阈值。这是“先改钳位/阈值、后看上限”的教训。
- 为什么不把因子改成 f32 操作数：m200 的 `Mmad` 只吃 f16。
- 路线优先级：recommended_fastpath。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：Ascend310P3（dav-m200 / DAV_2002）。
- f16 上下限数值（65504 / 5.96e-8=2^-24）取自所引 `Max.md`/`DeNormMin.md` 的 half 数值表；两文档的产品支持表标注该接口仅 950PR/DT 支持、310P 不支持——本卡只取其数值表作 f16 表示域约束，不涉及在 310P 调用 `NumericLimits` 接口。
- 常量：`MAXB`、`A_QB`/`A_KB`/`B_KGB`（各 `2*2*TILE`）、`TILE = 4096`。
- 切带规则：`span > 21.0f || i - bnd[nb-1] >= T64/4`，`nb < MAXB`（撞顶即并入末带）。

## 完整代码

after 的完整因果单元（上限常量 + ring-2 槽布局 + 槽索引）：

```cpp
constexpr int32_t MAXB = 24;
constexpr int32_t A_KB   = A_QB + 2 * 2 * TILE;
constexpr int32_t B_KGB  = A_KB + 2 * 2 * TILE;

// 推送
pushRows(A_QB + ((r & 1) * NKH + kh) * TILE + fb * T64, stg, sz);
pushRows(A_KB + ((r & 1) * NKH + kh) * TILE + fb * T64, stg, sz);
pushRows(B_KGB + ((r & 1) * NKH + kh) * TILE, stgB, fe);

// 消费
for (int32_t kh = 0; kh < NKH; ++kh) {
    mRound(B_KGB + ((r & 1) * NKH + kh) * TILE,
           A_QB + ((r & 1) * NKH + kh) * TILE, kh == 0);
}
```

## 性能影响

本卡主要修正确性；性能影响为正：scratch 占用从 `2*MAXB*TILE`（12 带 = 24 tile/槽组）降到 `2*2*TILE`（4 tile），UB 预算回收约 20 tile/组（共三组）。带数增加只影响带循环次数，弱门控用例的带数不变。

## 预防

- 把“带数/分块数的上限”当正确性参数：给它加断言或 dump（本会话就是靠“带数撞顶”的观察定位的）。
- 先算“最坏参数下需要多少带”，再定上限；不要用典型用例的带数定。
- 防溢出的 `Maxs`/`Mins` 钳位只能当最后一道保险，不能靠它“修”超范围；如果误差不随参数调整变化，先怀疑上限/容量类约束。
- 槽复用（ring）是把“上限”变成“零成本”的标准手段：确认消费顺序（先推后用、用完再推）即可。

## 验证信号

来源说明：本卡来自 Ascend310P3 会话内对唯一不过用例的门控跨度分析、带数撞顶观察，以及修复后的精度门结果。

- 修复前：该用例每 chunk 门控末值约 −329（约 5.15 log2/token），带数撞上限（示例 12），末带跨度 55.8 log2，因子需 `2^{±28}`（ρ=带中点，指数=带宽/2）（来源平台：310P；证据等级：tool_observed）。
- 对照实验：仅把跨度阈值 26→21 时误差不变（6.861e-3），证明限制在带数上限（来源平台：310P；证据等级：tool_observed）。
- 修复后（`MAXB=24` + ring-2）：该用例进入全套精度门，最终 `50/50 PASS`（来源平台：310P；证据等级：tool_observed）。
- 终版全套精度通过（来源平台：310P；证据等级：artifact_verified）。
- 复验（2026-11-05）：ρ=带中点，两版内核源码 `op30_chunk_gdr.cpp:587-588`/`:600-601` 同式（来源平台：CANN 9.1.0 源码；证据等级：artifact_verified）。
- 复验（2026-11-05）：MAXB=24 覆盖性扫描——CPU 复刻参考生成器同种子，50 例全部 107,344 个 64 行窗口按卡版切带规则逐窗仿真：最多需带 15（≤24，1.6x 裕量）、最强窗口总跨 355.18 log2 < 504=24×21、`MAXB=24` 下末带跨度峰值 20.88 < 21、需 >24 带的窗口 0；反事实 `MAXB=12` 时末带被迫吞到 83.85 log2（因子指数 ±41.9）——复现"撞顶才出现超大带"机制，并把卡内 55.8 括在 [21, 83.8] 内（来源平台：310P 用例集同种子 CPU 仿真；证据等级：tool_observed，扫描脚本与输出存复验档案）。

## 失效边界

- 只在 Ascend310P3 + CANN 9.1.0 验证；ring-2 的正确性依赖“每带推完即消费完”的循环结构，若改成“先推全部带、再统一 mRound”，ring-2 立即失效（必须回到 `2*MAXB` 槽）。
- `MAXB=24` 仍是一个有限上限：对当前 attrs 下的 50 例全集已证明覆盖（最多 15 带、最强总跨 355 log2 < 504，见验证信号）；若未来放宽 gate 强度（本次扫描最强窗 pertok=5.55，更强门控未测）或门控跨度超过 24×21 log2，仍会撞顶，需重跑覆盖性扫描。
- 钳位侧向（复验确认的潜伏问题）：现行 `Maxs(e, −30·ln2)`/`Mins(f, 15·ln2)` 在覆盖域内是死守卫；一旦撞顶，e 的危险侧（上溢，f16 乘积 Inf）无钳。若放宽 `MAXB`/阈值，需补 e 上侧 `Mins(e, +15·ln2)`（`Mins` 封上界）与 f 下侧 `Maxs(f, −24·ln2)`（`Maxs` 托下界）；正常域内可不加。数值检查（撞顶态 e 指数可达 +27.9·ln2、f 可达 −27.9·ln2）：`Mins(e, +15·ln2)` → 2^15 = 32768 可表示，误用 `Maxs` 则 +27.9·ln2 原样通过 → 2^27.9 超出 f16 上限 65504 → Inf；`Maxs(f, −24·ln2)` → 2^−24 = 5.96e-8 仍可表示，误用 `Mins` 则 −27.9·ln2 原样通过 → 低于 f16 最小非规格化数 → 按 0 处理。注意钳位只防溢出崩坏、会改变因子值，不保证结果正确——超出已验证跨度时应优先重切带（抬 `MAXB`）或回退，不把这两条指令当正确性保险。
- f16 因子可表示范围是本卡的根因约束；若改用其它数据类型（如 bf16），范围变化需重新核算。
- 未决项（收窄）：撞顶后末带的误差传播路径（因子溢出 vs 掩码/三角结构）未逐项分离，只确认“抬上限后消失”；MAXB=24 全集覆盖性已由扫描证明（见验证信号），该未决项关闭。

## 坏实践

- 用典型用例的带数（4~6）定上限 12。
- 改跨度阈值/钳位来“修”精度，而不检查带数是否撞顶。
- 为抬上限直接放大槽区（`2*MAXB*TILE`），吃光 UB 预算；应先确认槽能否 ring 复用。

## 误诊

- 曾把该用例的失败归因为“f16 因子精度不足”，于是去调 `Maxs`/`Mins` 的钳位常数与泰勒项数；实际是带数撞顶导致末带因子超范围，钳位在掩盖它。
