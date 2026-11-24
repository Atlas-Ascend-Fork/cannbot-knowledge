---
type: Optimization
title: HF32 操作数模式（尾数可精确表示时用半精度 MAC 速率跑 fp32 累加）
description: 把窄 dtype 实例化路径的 Cube 操作数模式切到 HF32：操作数全部来自 ≤11 位尾数 cast 时乘积与 fp32 累加序不变、L0C 逐位不变，MAC 走半精度档。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/32-hf32-operand-mode-exact-mantissa.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：HF32 操作数模式（尾数可精确表示时用半精度 MAC 速率跑 fp32 累加）

> **来源：A5 自由探索实测（matmul_bf16_bf16_bias_ofp32，2026-09-15；linear，2026-09-16，107 裸机）**
> direction_key: `cube-mac-throughput::hf32-operand-mode-bias-tile-isolation::k-main-loop`（实例一）；`cube-mad-throughput::hf32-exact-mantissa-mmad::c0-half-precision-paths`（实例二）
> 证据：<AOA_ROOT>/campaigns/matmul-bf16-bf16-bias-ofp32-a5-107-20260915-opencode/framework/aoa_out/matmul_bf16_bf16_bias_ofp32_custom/loop_<run-id>/explore/direction_001/
>       <AOA_ROOT>/campaigns/task-0195-linear-a5-107-20260916-opencode/framework/aoa_out/linear/loop_<run-id>/explore/direction_001/
> 实测：实例一 2.1266 x（geomean 33.3250→15.6705us，大 K case 最高 2.73x）；实例二 1.5840 x（geomean 25.1383→15.8698us，18 个 fp16/bf16 case-run 1.02~2.96x，5 个 fp32 case-run 零变化）。两者精度 22/22 首过、零修复轮；实例一另裁决三个未知量（速率 ~2x / 宽累加器语义保持 / 核内多次模式切换合法零代价）全部正面。

## 原理

矩阵乘单元对「fp32-regular 操作数」与「HF32 操作数」提供两档 MAC 速率（实测 ~2x）。FP32 累加器与输出语义不变，差异只出现在乘加通路：HF32 操作数（1 符号 + 8 指数 + 10 尾数）在 MAC 内以半精度速率运算。

在 fp16/bf16 算子上，操作数的**全部取值都来自窄 dtype cast**（host 预 cast 的权重、V0 阶段 cast 的激活），因此最坏情况尾数位数 ≤ 11（fp16 1s+5e+10m、bf16 1s+8e+7m），HF32 的 10 位尾数能**精确表示**它们——开启 HF32 后乘积与累加序不变，L0C 结果逐位不变，唯一变化是 MAC 速率从「强制全 fp32」档切到半精度档。

实例一把该模式与 bias tile 隔离一起裁决：bias 追加位由既有 `kPad = AlignUp(K+1, 32)` 布局结构性隔离（kPad-32 <= K 恒成立），无需额外重排。

## 性能问题模式（哪些 profiling 信号说明该用）

- cube MAC 流水（aic_mac 类）占比贴顶，搬运/发射/标量侧仍有余量，且 case 为 fp16/bf16 大 K 形态。
- 同一 kernel 内 fp16/bf16 与 fp32 实例的每 FLOP 速率差接近 2x，而两者的字节/FLOP 差远小于 2x（速率差来自 MAC 档位而非带宽）。
- 平台文档或实测给出两档 Cube 速率（实例一实测 ~2x），且当前内核从未显式设置过操作数模式。
- 其它维度（tiling、搬运、流水、尾块）策略已用尽或收益已贴顶。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **精确尾数前提必须逐操作数证明**：每个操作数的全部可能取值都须来自 ≤11 位尾数的来源（窄 dtype cast 链）。原始 fp32 数据（24 位尾数）直接上 HF32 会丢精度——那种输入要走 `33-hi-lo-split-compensated-narrow-mmad`，不是本条。
2. **逐路径门控**：只对窄 dtype 实例化路径启用，fp32 路径必须零接触；门控是否生效要以「fp32 case 逐条零变化」为证据面（实例二实测 5 个 fp32 case-run 零变化）。
3. **核内模式切换须实证合法**：若同一核在多次 Mmad 之间切换模式，须实测零代价且语义正确（实例一裁决：合法、零代价）。
4. **bias/kPad 追加位的隔离必须成立**：确认追加位落在独立分形/独立 tile 上、不参与 MAC 通路的缩放；隔离靠布局常量时要写明该常量恒等式（本例 kPad-32 <= K），布局改版须复核。
5. **累加语义不动**：乘积集合、fp32 累加顺序、L0C 布局与 Fixpipe 形态均不变；本条只改 MAC 档位，任何需要改累加秩序的实现都不属于本条。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- dtype：操作数来自 fp16/bf16（或其它 ≤11 位尾数的窄类型）；fp32 原始输入不适用。
- shape：K 大、MAC 受限的 case 收益最大；小块/搬运受限 case 中性。
- 流水线：`aic_mac` 贴顶；对任意「fp32 累加 + 窄 dtype 操作数」的矩阵乘内核适用。
- 与 tiling（02/07）、K 块粗化（01）、搬运合并（29）、双缓冲流水（08/09）等正交可叠加——实例二是在已含 01/07/08 家族改动的 champion 上再取 1.5840x。
- 与 `33-hi-lo-split-compensated-narrow-mmad` 的关系：33 处理「操作数确实是 fp32」的场景（拆成 hi/lo 窄面板），本条处理「操作数虽是 fp32 语义但取值本就来自窄 dtype」的场景；先判定来源链，再选卡，二者不叠加。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 列出该 kernel 的全部 dtype 实例化路径与每条路径的操作数来源链，逐条判定「最坏尾数位数 ≤ 11」是否成立。
2. 在窄 dtype 路径的 cube 初始化处启用 HF32 操作数模式；fp32 路径保持原状；门控写在实例化/编译期分支，避免运行期分支引入标量开销。
3. 若核内需多次切换，实测切换次数与耗时关系，确认零代价。
4. 复核 bias/kPad 追加位的布局隔离恒等式，写成注释固化。
5. 全量精度用例（含尾块、非整除、bias 追加位）一次过门。
6. 平衡交替配对测量，逐 case 核对「窄 dtype 提升 / fp32 零变化」两组证据面。

## LLM 前置问题（应用前必须自问）

1. 每个操作数的最坏尾数位数是多少？来源是 cast 链还是原始 fp32？
2. fp32 路径是否完全不受门控影响？靠什么 case 级证据证明？
3. bias/kPad 追加位落在哪里？隔离靠什么布局常量，该常量是否恒成立？
4. 核内模式切换发生几次？零代价有实测吗？
5. MAC 是否真是 top1 流水（不是的话本条收益会被搬运/发射封顶）？
6. 与已叠加的 K 块粗化/双缓冲组合后，L0 预算与模式设置的作用域是否仍然正确？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：两条路径均编译通过；fp32 实例的代码生成与基线等价（逐字节或指令流核对）。
- **精度**：全量用例一次通过、零修复轮（实测两实例均 22/22 首过）；窄 dtype case 与基线逐位一致或满足阈值判据。
- **性能**：平衡交替配对 geomean 超噪声底（实测实例一 2.1266x、实例二 1.5840x），大 K case 为收益主体。
- **零劣化判据**：fp32 case 逐条零变化（|delta| 落在同二进制离散带内），窄 dtype 小 case 无稳定回退。
- **回退**：尾数位数无法证明、fp32 路径出现任何非零变化、模式切换有代价、或 bias 隔离恒定式不成立时，关闭 HF32 回退原路径。

## 检索卡（短卡）

动作：把窄 dtype 实例化路径的 Cube 操作数模式切到 HF32：操作数全部来自 ≤11 位尾数 cast 时乘积与 fp32 累加序不变、L0C 逐位不变，MAC 走半精度档。
适用：操作数取值全部来自 fp16/bf16 cast（最坏尾数 ≤11 位）、fp32 累加、MAC 贴顶的矩阵乘内核。
限制：fp32 路径零接触并以逐条零变化为证据面；核内多次模式切换须实测零代价；bias/kPad 追加位隔离恒等式须成立；原始 fp32 输入禁用。
范围：矩阵乘内核的 Cube MAC 档位选择（fp32 累加 + 窄 dtype 操作数）。
检索词：HF32、操作数模式、SetHF32Mode、窄 dtype cast、精确尾数、fp32 累加、L0C 逐位、bias 隔离。
机会：aic_mac 贴顶而搬运/发射有余量；窄 dtype 与 fp32 每 FLOP 速率差近 2x，字节/FLOP 差小得多。
