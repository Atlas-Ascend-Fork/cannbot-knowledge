---
type: Optimization
title: 按行窗拆分 AIV 双 Lane 数据面
description: 把一核双 Vector Lane 中仅 Lane0 执行的数据面工作按互斥行窗均分给两条 Lane，保持跨核协议与数值路径不变。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/11-aiv-dual-lane-datapath-split.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：按行窗拆分 AIV 双 Lane 数据面

> 库内状态：`active`。已进入可选择策略库并纳入自动路由；来源方向曾通过编译、全量精度和正式稳定配对验证，收益与正确性红线见下文。

> 单一优化点：在一核双 Vector Lane 的拓扑中，若第二条 Lane 只参与同步而没有数据面工作，则把彼此不重叠的行窗均分给两条 Lane，并保持原跨核协议与数值路径不变。

---

## 1. 原理

当两条 AIV Lane 已参加同一套 collective 同步，但只有 Lane 0 执行反量化、类型转换或尾处理时，数据面吞吐被单 Lane 限制。若处理接口天然支持行起点和行数，按行窗将权重面板、输入转换和输出尾处理拆给两条 Lane，可在不改变逐元素计算的前提下并行生产。

收益来自消除 Lane 1 的结构性空转；不是改变计算精度或 AIC 侧算法。

## 2. 性能问题模式

- 硬件拓扑为一组 AIC 对应两条 AIV Lane，两条 Lane 均进入同步协议。
- 初始化或主循环以 Lane ID 门控，只有一条 Lane 构造或调用数据面内核。
- 数据面工作可按 K 行、M 行或其他不重叠行窗独立切分。
- 小 M、长 K 或宽 N 形状中，Vector 生产时间成为跨核握手的关键路径。
- 第二条 Lane 当前只镜像信号，设备时间随面板元素量近似增长。

## 3. 正确性红线

### 3.1 两条 Lane 的写窗口必须严格互斥

明确计算每条 Lane 的起点、有效行数、尾行和 GM/Workspace 偏移。奇数行、空窗口和非整除尾块不得重写或漏写。

### 3.2 Collective 协议必须保持同构

每条 Lane 的 set/wait 次数和顺序必须与协议要求一致。不得让仅有数据的一条 Lane额外发信号，也不得让空窗口 Lane 提前退出而破坏 collective 语义。

### 3.3 发信号前必须完成写回

每条 Lane 必须在其 MTE3 写回完全 drain 后才发布“数据就绪”。AIC 不得在任一 Lane 尚未完成时读取完整面板。

### 3.4 容量按每 Lane 独立核算

取消初始化门控后，两条 Lane 都会实例化队列和临时缓冲。必须按目标硬件的单 Lane UB 上限核算峰值，而不能用双 Lane 总量替代单 Lane 上限。

## 4. 泛化条件

适用：双 Lane 已同步但数据面单 Lane 执行；工作可按互斥行窗切分；每 Lane 容量足够；下游在完整数据就绪后消费。

不适用：两条 Lane 已有有效分工；数据存在跨行依赖；输出需原子归并；协议不允许两条 Lane 对等发信号；切分后单 Lane 工作过小而同步开销占主导。

## 5. 实施步骤

1. 画出两条 Lane 的数据面与 set/wait 序列，确认空转位置。
2. 为每个 Vector 阶段定义互斥的行窗切分和尾块规则。
3. 取消仅 Lane 0 初始化/执行的门控，让两条 Lane 使用相同内核、不同窗口。
4. 保持 AIC 侧、逐元素指令、workspace 布局及 collective 计数不变。
5. 在每条 Lane 写回 drain 后发布原有就绪信号。
6. 核算单 Lane UB 峰值，验证空窗口、奇数行和最大面板。
7. 通过全量精度后做平衡交替的同 shape 配对测量。

## 6. LLM 前置问题

1. 第二条 Lane 是否真的只有同步、没有数据面工作？
2. 哪些阶段能按行窗切分，两个窗口是否严格无交叠？
3. 尾行和空窗口如何处理？
4. 两条 Lane 的 set/wait 次数、顺序和参与条件是否完全同构？
5. 每条 Lane 发信号前的最后一个异步写在哪里完成？
6. 双 Lane 实例化后单 Lane UB 峰值和余量是多少？

## 7. 验收标准

- **构建与容量**：目标硬件编译通过，单 Lane UB 不超限。
- **精度**：全量 shape/dtype 通过，重点覆盖奇数行、尾块和空窗口。
- **同步**：无死锁、漏信号、重复消费或半面板读取。
- **性能**：稳定配对测量显示 Vector 主导形状改善，所有聚合用例无稳定回退。
- **归因**：AIC 和数值路径不变，收益能对应 Lane 1 数据面利用率提升。
- **回退**：无法证明窗口互斥、协议同构或容量合法时保留单 Lane 路径。

## 检索卡（短卡）

动作：把一核双 Vector Lane 中仅 Lane0 执行的数据面工作按互斥行窗均分给两条 Lane，保持跨核协议与数值路径不变。
适用：双 Lane 已同步但数据面单 Lane 执行；工作可按互斥行窗切分；每 Lane 容量足够；下游完整数据就绪后消费。
限制：写窗口须严格互斥，奇数行/空窗不得漏写重写；set/wait 次序与协议同构；发信号前写回须 drain；容量按单 Lane UB 上限核算。
范围：一核双 AIV Lane 拓扑算子的向量数据面阶段。
检索词：AIV Lane、行窗切分、Lane 门控、collective 同步、MTE3 写回 drain、单 Lane UB。
机会：Lane1 仅镜像信号空转，数据面吞吐被单 Lane 限制，Vector 生产时间成为跨核握手关键路径。
