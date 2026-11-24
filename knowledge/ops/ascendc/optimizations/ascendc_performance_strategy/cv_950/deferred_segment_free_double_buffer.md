---
type: Optimization
title: 延迟释放等待以重叠相邻归约段
description: 把段级 lock-step 握手中「段已释放」的等待推迟到下一段覆写前，形成深度 2 软件流水，稳态周期由生产+消费降为二者最大值。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/12-deferred-segment-free-double-buffer.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：延迟释放等待以重叠相邻归约段

> 库内状态：`active`。已进入可选择策略库并纳入自动路由；来源方向曾通过编译、全量精度和正式稳定配对验证，收益与正确性红线见下文。

> 单一优化点：当 Vector 生产段与 Cube 消费段被逐段握手强制成 lock-step，而相邻归约段占用互不相交的 staging 窗口时，把“段已释放”的等待推迟到下一段覆写前，形成深度为 2 的软件流水。

---

## 1. 原理

严格的“生产段 t → 等待消费完 t → 生产段 t+1”使生产端和消费端交替空转，稳态周期为两侧耗时之和。若相邻 K 段在权重 staging 中占不同的行窗、在输入 staging 中占不同的列窗，则生产 t+1 与消费 t 不存在 WAR 冲突。

将释放等待延迟一段后，稳态周期可由 `producer + consumer` 接近降为 `max(producer, consumer)`。这只是重排同步等待位置，不改变 set/wait 总数、数值计算或 workspace 布局。

## 2. 性能问题模式

- 每个归约段都执行“写回 drain、set ready、wait free”。
- 消费端每段执行“wait ready、计算、set free”。
- 时间线显示生产与消费从不重叠，双方存在规律性气泡。
- 相邻段写入的 staging 行窗或列窗物理互斥。
- 既有优化缩短生产时间后，逐段 lock-step 仍暴露在总时长中。

## 3. 正确性红线

### 3.1 必须证明相邻段无 WAR

用地址区间证明生产段 t+1 的全部写窗口与消费段 t 的全部读窗口互斥。不能只根据逻辑段号推断；需要包含对齐、padding、跨 Lane 分片和真实 stride。

### 3.2 覆写前必须等待对应释放

延迟的是等待位置，不是删除等待。生产端在复用某一 staging 区域前必须收到其最后一个消费者的 free 信号。

### 3.3 Tile 边界必须 drain

若新 Tile 会从 staging 起点重新写入，必须在边界等待上一 Tile 最后一个段释放，禁止把流水跨越会发生地址复用的边界。

### 3.4 信号计数与 Lane 序列保持不变

逐 Tile 的 ready set 数、free wait 数及两条 Lane 的参与顺序必须与原协议等价，并验证计数器上限不会因 run-ahead 超出。

## 4. 泛化条件

适用：生产者与消费者使用段级握手；相邻段的 staging 窗口互斥；同一缓冲至少允许一段 run-ahead；Tile 边界可明确 drain。

不适用：所有段复用同一物理地址；消费跨段读取；信号是全局栅栏而非段级令牌；计数器容量不足；无法确定最后消费者。

## 5. 实施步骤

1. 记录生产/消费双方每段的 wait、读写、barrier 和 set 顺序。
2. 对相邻段及 Tile 边界做 staging 地址区间证明。
3. 保留 ready 发布前的写回 drain。
4. 将段 t 的 free wait 移到写段 t+1 或复用同一区域之前。
5. 在 Tile 尾显式 drain 最后一个未释放段。
6. 逐 Tile 校验 set/wait 总数、顺序、最大未消费计数和双 Lane 同构性。
7. 跑全量精度、死锁压力与平衡交替配对性能验证。

## 6. LLM 前置问题

1. 当前稳态是否真的是生产与消费相加，而非已存在重叠？
2. 相邻段的每一处读写地址区间是什么，为什么无 WAR？
3. 哪个边界会首次复用旧地址，释放等待应放在哪里？
4. 每个 Tile 的 ready/free 数量是否仍为 1:1？
5. 最大 run-ahead 深度和硬件信号计数上限是多少？
6. 两条 Lane 是否会以相同顺序到达 collective 操作？

## 7. 验收标准

- **构建**：目标硬件编译通过，不改变 workspace 契约。
- **精度**：全量 shape/dtype 通过，覆盖单段、多段、归约尾和多 Tile。
- **同步**：长时间压力运行无死锁、计数溢出、提前覆写或脏读。
- **性能**：同 shape 的平衡交替配对中，生产/消费重叠可见且无稳定 case 回退。
- **归因**：set/wait 总数不变，收益来自等待位置后移而非混入块大小或数值变化。
- **回退**：地址互斥、边界 drain 或计数安全任一无法证明时保持 lock-step。

## 检索卡（短卡）

动作：把段级 lock-step 握手中「段已释放」的等待推迟到下一段覆写前，形成深度 2 软件流水，稳态周期由生产+消费降为二者最大值。
适用：生产/消费段级握手；相邻段 staging 窗口互斥；同一缓冲允许一段 run-ahead；Tile 边界可明确 drain。
限制：须地址区间证明相邻段无 WAR；覆写前等最后消费者 free；Tile 边界 drain 禁跨地址复用；set/wait 计数与 Lane 序不变。
范围：向量生产段与 Cube 消费段逐段握手的融合内核。
检索词：lock-step、free 信号延迟、WAR 冲突、staging 窗口、run-ahead、软件流水、Tile 边界 drain。
机会：每段执行写回 drain、set ready、wait free，生产与消费从不重叠、双方规律性气泡，稳态周期为两侧耗时之和。
