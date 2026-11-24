---
type: Optimization
title: 占用率驱动的分块与核数分档（人为核数上限与固定块高改为主机侧自适应）
description: 按派发占用率自适应块高 baseM'=Align16(clamp(ceil(M/核数),16,64)) 并重算派发，同时解除沿自上一代硬件的人为核数上限、同步上移守门阈值。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/35-occupancy-adaptive-tile-and-core-cap.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：占用率驱动的分块与核数分档（人为核数上限与固定块高改为主机侧自适应）

> **来源：A5 自由探索实测（lrlrls-softmax 2026-09-14；view_transpose 2026-09-17；matmul_bf16 2026-09-15；ltm 2026-09-14，107 裸机）**
> direction_key: `sub-32-mblock-aic-underfill::adaptive-basem-occupancy-split::host-tiling-dispatch-granularity`（实例一）；`core-utilization::lsts-max-cores-20-to-32::launch-grid-tiling-constant`（实例二）；`cube-core-idle-waste::adaptive-mn-tile-size-tiering::host-tiling-grid`（实例三）；`aic-core-occupancy::shape-adaptive-mn-subtiling::host-tiling-gate`（实例四）
> 证据：<AOA_ROOT>/campaigns/lrlrls-a5-107-20260912-opencode/framework/aoa_out/linear_relu_linear_relu_linear_softmax_custom/loop_<run-id>/explore/direction_004/
>       <AOA_ROOT>/campaigns/linear-sigmoid-view-transpose-kb-a5-107-20260917-opencode/framework/aoa_out/linear_sigmoid_view_transpose_custom/loop_<run-id>/explore/direction_002/
>       <AOA_ROOT>/campaigns/matmul-bf16-bf16-bias-ofp32-a5-107-20260915-opencode/framework/aoa_out/matmul_bf16_bf16_bias_ofp32_custom/loop_<run-id>/explore/direction_002/
>       <AOA_ROOT>/campaigns/linear-transpose-matmul-a5-107-20260912-opencode/framework/aoa_out/linear_transpose_matmul_custom/loop_<run-id>/explore/direction_004/
> 实测：实例一 1.7516 x（113.7502→64.9422us，15 个占用率提升 case 两对一致改善，满块 8 case 恒等）22/22；实例二 1.1509 x（18.7723→16.3116us，大 case 1.546~1.570x）25/25；实例三 1.0556 x（15.6716→14.8461us，14 case 零扰动）22/22；实例四 1.0435 x（9.9132→9.4999us，深饥饿人群 -4.5~-13.9%）22/22。

## 原理

派发占用率 = min(物理核数, 任务数) / 物理核数。核内串行链类策略（01/08/09）贴顶之后，最大的剩余杠杆常常是**让更多核参与**与**让块几何匹配核数**：

- 块高按占用率反推（实例一）：`baseM' = Align16(clamp(ceil(M/核数), 16, 64)) ∈ {16,32,48,64}`，`mBlocks / usedAic / tasksPerCore` 随之重算；满块 case（M 大）保持原 baseM，指令流恒等。
- 解除人为核数上限（实例二）：`LST_MAX_CORES` 被硬编码为 20（注释自证沿自上一代硬件），而实测本机 Aicore Count=32 → launch 占用仅 62.5%；改为 32 后每核任务数 ÷1.6、每核搬运需求 ÷1.6，占用率门控阈值随之 10→16。
- 空闲核形态下按 per-tile 固定成本分档缩块（实例三）：重校准模型（`地板 t/s + 面积 f`）把切换集精确收敛到实测赢面 case。
- 形状自适应子分块（实例四）：仅在「占用 2~12 核 且 tasksPerCore=1 且 k-loop ≥ 4」的深饥饿人群下移档位。

## 性能问题模式（哪些 profiling 信号说明该用）

- `usedAic = min(核数, mBlocks)` 明显小于核数，空闲核不贡献 Task Duration（op_summary 的 Block Num 可逐 case 核对派发算术）。
- 核数常量与目标硬件不符：常量来源是别的架构代次（注释/历史沿革），`npu-smi` 实测核数更大。
- 每核任务数偏大而单任务用时远大于其搬运需求（latency 主导），说明加核能按任务数比例提速。
- 性能门显示「基线比参考慢」的 case 呈现「块数不足」而非「单块太慢」的形态（M/N 小、K 长）。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **per-tile 归约链存在尺寸无关地板**（实测 ~0.42us/iter，64×64 tile 成本 ≈0.95×128×128）→ 分档收益**只能**来自每 tile 固定成本（装载序幕/收尾）随面积收缩，**不可按面积线性外推**；切换集必须用「地板 t/s + 面积 f」的重校准模型筛选，未入选 case 保持原档（实测 14 case 零扰动）。
2. **满块 case 指令流必须恒等**：块高只在小 mBlocks 形态下变（实例一 M≥1537 保持 64），并以「两对 |delta| ≤ 0.30%」为恒等证据面；否则回退面不可控。
3. **核数上限的守门阈值必须同步上移**（本例 `LST_MAX_CORES/2`：10→16），并逐 case 枚举压线 case（实测 4 个 case 恰好压线通过）——只改常量不改门控会让门控形同虚设。
4. **占用已足的人群不要动**：实测「纯占用最大化」在中高占用人群被 screening 证伪（其瓶颈是 B 面重流/并发争用），必须有守门条件（如 ≥16 核或 tpc≥2 时不下移档位）。
5. **带宽必须留余量**：加核会按比例放大聚合 GM 流量，须先用聚合带宽参考值核对该 case 未饱和（实测参考 ≥1.77TB/s，加核后 1.4→2.0+TB/s 仍未饱和）。
6. **主机侧改动不得改动 kernel 数值路径**：本卡全部改动落在 host tiling/launch 常量上（kernel 零改动或仅参数化），逐 tile 数值路径不变。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- shape：M/N 小、K 长、块数 < 核数的 case 收益最大；满块 case 应零变化（作为恒等证据面）。
- dtype：与 dtype 无关（host 侧几何）。
- 流水线：`aic_mac` 贴顶后的第二层杠杆；对任何多核铺核的矩阵/CV 内核适用。
- 与 02 号卡的关系：02 在「访存计算比」约束下放大基本块并设「块数 ≥ 核数一半」的下界门控；本条是同一占用率约束的**反向操作**（块数不足时主动缩块 / 解除核数上限），两者互为对偶，应用前先判断当前 case 落在哪一侧。
- 与 07 号卡的关系：07 按 shape/dtype 分档「行块高、列块宽、归约块深」，其分档锚点是精度边界与容量；本条分档锚点是**派发占用率**与核数上限，两者可叠加但档位表须合并维护。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 对每个 case 算 `任务数 / 物理核数`，把「占用率 < 1 且核内串行链已贴顶」的 case 挑出来。
2. 核对核数常量来源与目标硬件实测核数；若来自其它代次，解除上限并同步上移守门阈值。
3. 按占用率反推块高档位（`Align16(clamp(ceil(M/核数), 下界, 上界))`），重算 `mBlocks/usedAic/tasksPerCore`。
4. 用重校准成本模型（地板 + 面积）筛选切换集，其余 case 保持原档；模型须在**当前 champion** 上重拟合。
5. 逐 case 核对：提升 case 两对一致改善；恒等 case 落在噪声带内。
6. 平衡交替配对测量，报占用率提升 case 与恒等 case 两组数字。

## LLM 前置问题（应用前必须自问）

1. 当前 case 是「块数不足（要缩块/加核）」还是「块数已足（瓶颈在别处）」？判据是 `任务数/核数` 还是占用率以外的证据？
2. 核数常量从哪来？与目标硬件实测核数一致吗？门控阈值是否需要同步改？
3. per-tile 成本模型有没有尺寸无关地板？地板值是多少？切换集是怎么筛出来的？
4. 加核后聚合带宽是否仍有余量？参考带宽从哪来？
5. 满块/高占用 case 的恒等证据是什么（逐 case |delta| 还是跨对符号一致性）？
6. 与 02/07 的档位表是否冲突？叠加时容量账按哪个最坏组合算？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过（host-only 改动应一次通过）；逐 case 核对派发算术（Block Num / usedAic）按预期生效。
- **精度**：全量用例通过、零修复轮（实测四实例分别 22/22、25/25、22/22、22/22）。
- **性能**：平衡交替配对 geomean 超噪声底（实测 1.7516x / 1.1509x / 1.0556x / 1.0435x）；提升集中在目标人群。
- **零劣化判据**：恒等人群逐 case |delta| ≤ 0.30%（实测）；跨对符号不一致者判噪声而非收益。
- **回退**：占用率反推使块数或块高越界、恒等人群出现稳定回退、或带宽饱和时，回退原档位/原核数上限。

## 检索卡（短卡）

动作：按派发占用率自适应块高 baseM'=Align16(clamp(ceil(M/核数),16,64)) 并重算派发，同时解除沿自上一代硬件的人为核数上限、同步上移守门阈值。
适用：核内串行链已贴顶、块数不足使部分核空转（占用率=min(核数,任务数)/核数<1）的矩阵类内核。
限制：per-tile 归约链有尺寸无关地板（~0.42us/iter）不可按面积线性外推；满块 case 指令流须恒等；占用已足人群不得下移档位。
范围：主机侧 tiling 分块几何与派发核数（矩阵类算子）。
检索词：baseM、派发占用率、核数上限、LST_MAX_CORES、核空转、形状自适应子分块、per-tile 地板、守门阈值。
机会：任务数<物理核数、空闲核不计入时长；核内串行链贴顶后剩余杠杆只在占用率；分档收益只来自每 tile 固定成本。
