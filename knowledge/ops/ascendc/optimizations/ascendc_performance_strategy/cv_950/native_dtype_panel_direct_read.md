---
type: Optimization
title: 原生 dtype 面板直读（折叠 V0 cast 阶段与 fp32 环槽 GM 往返）
description: 删掉只做 cast/重排的 V0 阶段：C0 以 Nd2Nz 直读 GM padded 输入并改用原生 dtype 面板，环槽与 host 预 cast 一并消失，主路径 3→2 launch。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/34-native-dtype-panel-direct-read.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：原生 dtype 面板直读（折叠 V0 cast 阶段与 fp32 环槽 GM 往返）

> **来源：A5 自由探索实测（linear，2026-09-16，107 裸机）**
> direction_key: `v0-fp32-ring-roundtrip::fold-cast-into-native-dtype-cube-mmad::three-kernel-main-path`
> 证据：<AOA_ROOT>/campaigns/task-0195-linear-v2-a5-107-20260916-opencode/framework/aoa_out/linear/loop_<run-id>/explore/direction_001/
> 实测：1.3861 x（launch 均值口径 geomean 69.421→50.082us；逐 iter 设备总时长 2.079x（208.3→100.2us）；窄 dtype 大 case 最高 3.37x；fp32 case 时间比 0.87，与「V0 纯拷贝消除 12.6%」的预测一致）；**29/29 case 真机时间全部下降**，精度 28/28 一次通过。

## 原理

三段式主路径里存在一个「V0 cast 阶段」：把 fp32 输入 cast 成窄 dtype 写进片上/全局的环槽（A-ring），C0 再从那里以 fp32 面板读回消费。该阶段的数据流是一次 **GM 往返 + 一次多余 launch**，而它存在的唯一理由是「C0 只能吃 fp32 面板」。

机制：让 C0 直接以 Nd2Nz 从 GM 读 padded 输入（行步距 = paddedK，窗口为满 512 列），窄 dtype 路径改用**原生 dtype 面板**（L0A/L0B 原生 dtype、`Mmad` 原生×原生、fp32 L0C 累加）；fp32 dtype 保留 fp32 面板，但仍吃掉「V0 只是纯拷贝」那部分收益。随之删除：V0 阶段本身、A-ring staging、host 权重预 cast、`aRingBytes` workspace，主路径由 3 launch 收缩为 2 launch（C0+V1）。

## 性能问题模式（哪些 profiling 信号说明该用）

- 主路径存在一个只做 dtype 转换/布局重排、不做数学的阶段，其输出被下一个矩阵阶段原样读回（GM→GM 往返）。
- 该阶段耗时占比与纯拷贝带宽模型吻合（实测 fp32 case 12.6%），且它的存在使 launch 数 +1（小 case 受 launch 地板影响）。
- 矩阵阶段的 MTE2 字节数里，有约一半是 fp32 面板字节，而计算侧只需要窄 dtype 精度（fp32 面板把搬运量翻倍）。
- 环槽/staging 缓冲的容量账（`aRingBytes` 等）在片上预算里占着一块，删掉它能解开后续 K 块粗化/双缓冲的容量。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **面板 dtype 语义必须逐 dtype 分流**：窄 dtype 走原生面板（Mmad 原生×原生），fp32 走 fp32 面板；不得用统一改写把 fp32 也降到窄面板——那是 33 号卡（hi/lo 补偿）的地盘，需要精度论证。
2. **HF32/累加语义不得被顺带改动**：若本 kernel 同时使用 HF32 操作数模式（32 号卡），须单独论证两者叠加后的精确尾数前提仍然成立。
3. **padded 布局的 K 边界与零填充语义必须与原环槽完全一致**：改的是「谁来 cast、写到哪」，不是「填充多少、按什么步距读」；行步距 = paddedK 的窗口数必须逐 case 对齐。
4. **L0 预算重算**：面板 dtype 变化会改变 L0A/L0B 占用（本例窄 dtype 释放约 2x），后续 K 块粗化/双缓冲档位必须按新预算重新分档，不得沿用旧档。
5. **删除的 host 预 cast 与 workspace 必须留证**：逐 case 确认无残留引用（编译期一处、运行期一处），否则会以「读到未初始化缓冲」的形式在尾块 case 上偶发。
6. **fp32 case 的收益预期不得按窄 dtype 外推**：fp32 只能兑现「纯拷贝消除」那一部分（实测时间比 0.87），按 2x 预期会误判为失败而错杀。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- dtype：窄 dtype（fp16/bf16）收益最大（面板字节减半 + 原生速率）；fp32 也有纯拷贝消除的固定收益。
- shape：面板大、K 长、launch 地板敏感的 case 收益最大；极小 case 因 launch 数减少同样受益（本例 29/29 全部下降）。
- 流水线：`aic_mte2` + 启动地板；对任何「cast/重排阶段 → 矩阵阶段」的三段式主路径适用。
- 与 29 号卡（面板宽搬运合并）叠加：本条决定「搬什么 dtype」，29 决定「一次搬多大」，31/01 决定「缓存怎么摆」，三者容量账要合起来算。
- 与 `33-hi-lo-split-compensated-narrow-mmad` 的分界：本条是「把面板降到原生窄 dtype」的搬运侧改造，33 是「fp32 输入靠分解换速率」的数学侧改造；输入确实是 fp32 且精度判据严时走 33，不冲突但需分别论证。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 画出主路径的 launch 与数据流，标出「只做 cast/重排」的阶段及其输出消费者。
2. 确认 C0 侧装载原语支持以 GM 行步距直接读 padded 布局（Nd2Nz 窗口覆盖满列），并确定 fp32/窄 dtype 两条面板通路的开关位置。
3. 改写 C0 装载源：从环槽地址改为 GM padded 地址；窄 dtype 面板改原生 dtype 的 L0 布局与 Mmad 入参；fp32 面板保持不变。
4. 删除 V0 阶段、host 预 cast、环槽 workspace，同步清理同步标志与 launch 配置。
5. 按新 L0 预算重算 K 块/双缓冲档位（与 01/08/09 的容量账合并）。
6. 全量精度用例（含尾块、非整除、两种 dtype 家族）一次过门，再走平衡交替配对测量，并分别报「窄 dtype 收益」与「fp32 纯拷贝收益」两组数字。

## LLM 前置问题（应用前必须自问）

1. 主路径里有几个阶段是纯粹的 cast/重排？它的输出有没有其它消费者？
2. C0 能不能直接吃 GM 上的 padded 布局（行步距、满列窗口、对齐）？
3. fp32 与窄 dtype 两条面板通路分别怎么走？会不会顺带改动 HF32/累加语义？
4. 删除环槽后 L0/UB 预算变化多少？后续哪些卡（01/08/09）的档位要跟着重算？
5. fp32 case 的预期收益是多少（只算拷贝消除），拿什么证据确认没有按窄 dtype 外推？
6. host 预 cast 与 workspace 的引用是否彻底清除（编译期 + 运行期各一处）？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；主路径 launch 数减少可核实（本例 3→2）。
- **精度**：全量用例一次通过、零修复轮（实测 28/28）；窄 dtype case 与基线一致，fp32 case 满足原判据。
- **性能**：launch 均值口径 geomean 与逐 iter 设备总时长两个口径都要报（实测 1.3861x / 2.079x），且**逐 case 真机时间无一上升**（实测 29/29 下降）。
- **零劣化判据**：单 case 最大回退 < 噪声底；fp32 case 时间比应落在拷贝消除预测带内（实测 0.87）。
- **回退**：padded 布局对不齐、窄 dtype 面板精度不过、或 fp32 case 出现非预期回退时，恢复 V0 阶段与环槽路径。

## 检索卡（短卡）

动作：删掉只做 cast/重排的 V0 阶段：C0 以 Nd2Nz 直读 GM padded 输入并改用原生 dtype 面板，环槽与 host 预 cast 一并消失，主路径 3→2 launch。
适用：主路径存在只做 cast/布局重排的中间阶段、cube 吃宽 dtype 面板的矩阵乘内核。
限制：面板 dtype 逐 dtype 分流（fp32 不得顺带降窄面板）；padded K 边界与零填充语义不动；L0 预算按新面板重算。
范围：矩阵乘主路径中只做 cast/重排的中间阶段与其 GM 环槽往返。
检索词：Nd2Nz 直读、原生 dtype 面板、阶段消除、V0 cast 阶段、环槽 workspace、launch 数、L0A/L0B。
机会：主路径多一次 GM 往返与一次 launch；V0 阶段占比高却只做纯拷贝；窄 dtype cube 速率被 fp32 面板压住。
