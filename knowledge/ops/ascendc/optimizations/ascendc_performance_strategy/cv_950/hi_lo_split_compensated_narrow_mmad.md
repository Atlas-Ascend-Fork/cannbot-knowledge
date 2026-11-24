---
type: Optimization
title: 宽 dtype 操作数 hi/lo 分解 + 多项补偿 Mmad（用窄 dtype 速率替代 fp32 速率）
description: 把 fp32 操作数拆成 hi/lo 两个窄面板，每 K 块发 3 项 Mmad（hi·hi+hi·lo+lo·hi）累加进同一 fp32 L0C、K 序不变。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/33-hi-lo-split-compensated-narrow-mmad.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：宽 dtype 操作数 hi/lo 分解 + 多项补偿 Mmad（用窄 dtype 速率替代 fp32 速率）

> **来源：A5 自由探索实测（linear，2026-09-16；glu_linear，2026-09-15，107 裸机）**
> direction_key: `fp32-native-mmad-throughput::bf16-hi-lo-split-3-term-compensated-mmad::fp32-dtype-cases-c0-k-loop`（实例一）；`aic-mac-fp32-operand-rate::mmad-operand-dtype-narrow::fp16-bf16-cases-c0`（实例二）
> 证据：<AOA_ROOT>/campaigns/task-0195-linear-v2-a5-107-20260916-opencode/framework/aoa_out/linear/loop_<run-id>/explore/direction_004/
>       <AOA_ROOT>/campaigns/glu-linear-a5-107-20260915-opencode/framework/aoa_out/glu_linear_custom/loop_<run-id>/explore/direction_001/
> 实测：实例一 1.1656 x（geomean 24.642→21.142us，5 个 fp32 case 1.92~3.77x，24 个 fp16/bf16 case 逐字节不变）；实例二 1.1071 x（geomean 24.883→22.476us，多 bid fp16 重 case 1.36~1.40x）。两者精度分别 28/28、23/23 通过。

## 原理

目标硬件上「4 字节操作数」的 Mmad 付真实速率罚金：实测 fp32 原生面板 ~50-52 TF/s，而 2 字节原生面板 424-466 TF/s（同 shape 对照差约 9x，而字节/FLOP 只差 2x，故不是带宽问题；用 hi/lo 双遍净数据反推 2 字节倍数 m≈2.5~3）。

机制（Ozaki 式分解）：把 fp32 操作数 x 拆成 hi = narrow(x)、lo = narrow(x - hi)，两个窄 dtype 面板打包；每个 K 块发 **3 条 Mmad**（hi·hi + hi·lo + lo·hi）累加进**同一个 fp32 L0C tile、K 序不变**。被丢弃的 lo·lo 项相对量级 ~2^-18（bf16）/~2^-22（fp16），远低于输出判据；Mmad 地板从「1 × fp32 速率」变为「3 × 窄 dtype 速率」（实例一实测 432ns/k64-eq vs 1278ns）。

实例一还闭合了两个工程事实：(1) **host 侧 aclnn dtype-cast 链在 C0 前运行会触发该平台 arch35 的 MTE 边际故障**，分解必须在核内（in-kernel S 阶段，mode 10 AIV）完成，host 只做 `at::zeros` 预清零；(2) 精度门的「正常值域比值判据」比 MERE 严得多，截断误差经 sqrt(K) 放大后超限——先用 CPU 复刻 checker 做语义仿真再上设备。

## 性能问题模式（哪些 profiling 信号说明该用）

- fp32 case 的每 FLOP 速率约为同 shape 窄 dtype case 的 1/9（实测 3726us vs 419us），而字节/FLOP 只差 2x → 排除带宽解释，定位到 Mmad 速率。
- 串行链类策略（双缓冲、延迟 WAR、CO1 双槽）已把时延重叠吃掉后，fp32 case 仍只 1.06~1.10x——剩余时间是**吞吐地板**不是时延。
- 逐 K 步节拍贴住 fp32 Mmad-only 下界（实测 fp32 ~1278-1437ns/步 vs 窄 dtype 144ns/k64-eq）。
- 该组 case 同时是全套件绝对耗时最大的 case（收益绝对值最大）。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **精度判据按元素级正常值域，不按 MERE/统计量**：单点舍入（任何模式，含设备截断型 CAST_NONE）过不了该判据；机制内唯一可行的精度形态是 hi/lo **补偿**（残差 ~2^-22|g|，fp16 面板）。bf16 hi/lo 残差 ~2^-16|g| 挂小值域绝对判据 → 必须路由 fp16 面板。上设备前先用 CPU 复刻 checker 仿真（实例一/二都靠它提前判死或判活）。
2. **分解必须在核内完成**：host 侧 aclnn cast 链会在 C0 前触发本平台 arch35 MTE 边际故障；host 只保留 `at::zeros` 预清零与打包布局。
3. **累加语义不动**：3 项乘积累加进同一 fp32 L0C、K 序不变、`cmatrixInitVal` 首步语义不变。L0 四面板打包超预算时改 baseK 档位/槽排布，**不得**改累加秩序。
4. **分级回退顺序固定**：精度不足时依次 ①补第 4 项 lo·lo（4×Mmad，地板仍 2.2x，误差 ~2^-19）②重排 L0 打包（baseK 64/32、面板对槽）③退回核内 AIV 拆分阶段；禁止直接放宽阈值或换回 fp32 native。
5. **小 case 门控**：改造引入的 launch/序幕地板会让极小 case 净亏（实测 fp32 case19 +0.79us），须按 case 规模门控走原路径。
6. **面板 dtype 与 32 号卡（HF32）的关系**：本条是「输入确实需要 fp32 精度」时的解法；若操作数取值本就来自窄 dtype cast，应走 32 号卡（更便宜），先判来源再选卡。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- dtype：输入 fp32（4 字节）× fp32 累加；窄 dtype 面板选型按精度判据定（小值域判据下 fp16 优先于 bf16）。
- shape：K 大、Mmad 吞吐受限、绝对耗时大的 case 收益最大（实例一 fp32 5 case 1.92~3.77x）。
- 流水线：`aic_mac` 吞吐地板；对任意 fp32 矩阵乘内核适用。
- 与流水/搬运类策略正交可叠加（实例一是在已含 3 个前序方向的 champion 上再取 1.1656x）。
- 与 `32-hf32-operand-mode-exact-mantissa` 互斥选择（见红线 6），与 `34-native-dtype-panel-direct-read` 同属「面板 dtype 改造」但方向相反（34 把面板降到原生窄 dtype 省搬运，本条把 fp32 拆成窄面板抢速率）。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 用同 shape 跨 dtype 对照测出 fp32 与窄 dtype 的每 FLOP 速率比，确认罚金倍数（并排除带宽解释：字节/FLOP 比 << 速率比）。
2. 选定窄面板 dtype：按精度判据（元素级正常值域）先用 CPU 复刻 checker 仿真 3 项/4 项分解的残差是否过门。
3. 在核内增加拆分阶段（AIV）：产出 hi/lo 打包面板（如 `[rows, 3*kPad]` 形态），host 侧只做 `at::zeros` 预清零；**不要**用 host cast 链。
4. C0 每 K 块发 3 条 Mmad 累加进同一 fp32 L0C，保持 K 序与首步语义；按 L0 预算调 baseK/槽排布。
5. 逐 dtype 分组验收：fp32 case 提速、窄 dtype case 逐字节不变。
6. 平衡交替配对测量；若精度不过，按红线 4 的顺序逐级回退而不是放宽阈值。

## LLM 前置问题（应用前必须自问）

1. fp32 与窄 dtype 的每 FLOP 速率实测比是多少？字节/FLOP 比是多少（能否排除带宽）？
2. 精度判据是哪一种（元素级正常值域 / MERE / 逐位）？残差量级与判据的余量算过吗？CPU 仿真做过吗？
3. 分解放在 host 还是核内？本平台 host cast 链是否有已知故障？
4. 3 项（或 4 项）Mmad 的 L0 面板打包放得下吗？放不下时改的是什么（只能改档位，不能改累加序）？
5. 小 case 的 3-launch/序幕地板是否会让净收益转负？门控阈值定在哪？
6. 本次是「输入确实要 fp32 精度」还是「取值本就来自窄 dtype」？（后者应走 32 号卡）

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；窄 dtype 路径的指令流与产物不发生非预期变化。
- **精度**：全量用例通过（实测实例一 28/28、实例二 23/23），fp32 case 满足元素级正常值域判据（bad_ratio 无新增）；窄 dtype case 逐字节不变。
- **性能**：平衡交替配对 geomean 超噪声底（实测 1.1656x / 1.1071x）；收益集中在原 fp32 大 case（1.92~3.77x）。
- **零劣化判据**：窄 dtype case 无回退；极小 case 走门控原路径，回归 < 启动地板量级（实测 +0.79us 已按门控隔离）。
- **回退**：精度不过按 4 项补偿 → L0 重排 → 核内拆分阶段的顺序回退；仍不过则整体回退 fp32 native 面板。

## 检索卡（短卡）

动作：把 fp32 操作数拆成 hi/lo 两个窄面板，每 K 块发 3 项 Mmad（hi·hi+hi·lo+lo·hi）累加进同一 fp32 L0C、K 序不变。
适用：输入确为 fp32、fp32 累加、Mmad 吞吐受限且绝对耗时大的矩阵乘 case。
限制：精度按元素级正常值域（单点舍入不过、bf16 用 fp16）；分解须核内（host cast 触发 arch35 故障）；回退序 4 项→L0→核内。
范围：fp32 矩阵乘内核的 Mmad 吞吐地板。
检索词：hi/lo 分解、Ozaki、补偿 Mmad、窄面板、fp32 Mmad 速率、L0 打包、CAST_NONE、checker 仿真。
机会：串行链策略吃满后 fp32 仍只 1.06~1.10x；每 FLOP 速率约为窄 dtype 1/9 而字节/FLOP 仅 2x。
代价：L0 四面板打包占用上升；极小 case 付 3-launch 序幕地板。
