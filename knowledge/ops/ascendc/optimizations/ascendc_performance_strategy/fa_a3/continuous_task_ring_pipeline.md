---
type: Optimization
title: 全核连续任务环形流水，减少短流水反复启停
description: 将按外层 block 反复启动并排空的局部流水改为全核连续任务环形流水。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/08-continuous-task-ring-pipeline.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：全核连续任务环形流水，减少短流水反复启停

> **单一优化点：** 将 attention 类 AscendC kernel 中“按外层 block 启动、排空、再启动”的局部流水，改为以 reduce-axis tile 或逻辑子任务为原子单元的全核连续任务流。任务描述符使用 3 槽环形缓存，使矩阵阶段、向量阶段和后续矩阵/输出阶段跨相邻任务稳定重叠，只在每个 core 的任务流首尾各经历一次启动和排空。

本策略适用于各类 attention-like 算子（含 GQA/MQA 变体与稀疏/反向变体），只要求存在可线性排序的 per-core 任务流，以及相邻任务之间可用固定距离表达的生产消费关系。本文使用 `MatA / VecB / MatC / VecD` 作为通用阶段名：

- `MatA`：不依赖当前向量结果的矩阵或搬入计算阶段，例如 QK、dO*V、局部 score 生成。
- `VecB`：消费 `MatA` 结果并生成中间概率、归一化状态、梯度中间量或缩放系数的向量阶段。
- `MatC`：消费 `VecB` 结果的后续矩阵阶段，例如 P*V、P*dO、dP*K。
- `VecD`：消费 `MatC` 结果并更新最终输出、累计状态或写回梯度的向量阶段。

---

## 0. Preflight and staged adoption gate

本策略不能作为一次性大重写直接实施。agent 必须先在设计/执行计划中给出下面的 preflight evidence table；任一项缺失时，不允许进入三槽 ring scheduler 改写，只能落地下一步可验证的 preparatory slice，或明确报告缺失证据。

| Preflight 项 | 必须证明 | 不能用什么替代 |
|---|---|---|
| Source inventory | 当前源码中真实存在的 stage 函数、kernel 入口、workspace/queue/signal 字段、qHead/kvHead 地址映射位置 | 不能凭 FA 参考实现或策略模板猜函数名 |
| Stage DAG | `MatA -> VecB -> MatC -> VecD` 或目标算子的等价生产消费关系，列出每条边的数据和 producer/consumer | 不能只写“按模板改成流水” |
| Reduce group continuity | 同一 `(batch, qHead, kvHead, qRowStart)` 的所有 reduce-axis tiles 在同一 core 内连续 | 不能改变跨核划分来满足本策略 |
| Slot ownership | task descriptor slot、workspace data slot、queue slot、signal/event slot 的生命周期和最晚消费者 | 不能把 `taskSlot` 当成 `workspaceSlot`；taskSlot is not workspaceSlot |
| Baseline reproducibility | 修改前 build、accuracy、benchmark 命令和结果可复现；benchmark 输入文件已存在 | 不能通过修改 benchmark case 文件伪造可测性 |

### Staged implementation slices

按以下 slice 顺序推进。每个 candidate 只能推进一个 slice，除非前一个 slice 已在历史 attempt 中通过 build/accuracy，且本次 diff 清楚复用其证据。

1. **descriptor-only slice**：新增 `AttentionTask`/`GqaTask` 或等价 descriptor、cursor 类型和只读构造 helper；不改变原计算顺序，不改变 workspace 槽数，不删除同步。
2. **stage-interface slice**：把现有阶段函数改成显式接收 `const Task&` 或调用前 `SetTaskContext(task)`；仍保持原 loop 顺序，验证 qHead/kvHead、tail、mask、state 地址都来自 task。
3. **ring-scheduler slice**：在 descriptor 和 stage interface 已通过后，才引入 `current/previous/older` 三槽 loop；保持原 workspace slot 选择和原同步协议。
4. **sync-slot validation slice**：只补齐按 `seq/workspaceSlot` 映射的 wait/ready/free 证明；不做冗余同步删减。
5. **performance slice**：accuracy 通过后再分析 wait/scalar/task duration；若性能回退，定位 ring drain、slot 覆盖或上下文重设，不混入 L0/L1/tile shape 优化。

如果模型无法完成当前 slice，必须提交 **smallest legal diff**：例如 descriptor-only source diff、stage signature source diff、或清晰的 source-proven D1 deviation。禁止产生 no-op/no candidate source diff 后继续把失败归类为普通策略失败。

### Hard redlines for this strategy

- No lambda/local callable defined or called inside an `__aicore__` function. AscendC device-side helper 必须是 `__aicore__ inline` 成员函数、自由函数或 device-safe struct/helper；不要在 kernel 函数内部定义 host lambda 再调用。
- Do not edit `basic_case.csv`、benchmark CSV、性能 case 文件或外部 harness 输入作为本策略的修复。缺 benchmark 输入是 harness blocker，不是 candidate source diff。
- 不允许把 qHead/kvHead 合并成一个隐式 head 字段；GQA/MQA 场景必须在 task descriptor 或纯函数映射中同时保留 qHead/kvHead。
- 不允许把 `taskSlot` 绑定为 `workspaceSlot`，除非独立证明数据 slot 的最晚消费者已经完成。
- 不允许在本策略中顺手删除同步、减少 workspace 槽、改 L0/L1 缓存、改 tile shape、加 fast path 或改变跨核分配。

---

## 1. 性能问题模式

低效实现通常在每个外层 query block、head block 或 row block 内独立流水：

```text
block 0: prologue -> short steady -> epilogue
block 1: prologue -> short steady -> epilogue
block 2: prologue -> short steady -> epilogue
...
```

当每个 block 内 reduce-axis tile 数量很少时，steady 阶段过短，AIC/AIV 反复等待对方首个结果或尾部 drain，导致：

- Cube 等待 Vec 产物的时间增加。
- Vec 等待 Cube 产物的时间增加。
- 标量调度、信号等待和任务切换成本被放大。
- 每个 core 的真实并行重叠时间远小于理论流水深度。

优化目标是把同一 core 可执行的所有子任务展平为一个连续任务流：

```text
task 0, task 1, task 2, ..., task N-1
```

然后在一个统一 loop 内执行固定距离的流水：

```text
tick i:
  MatA(current task i)
  VecB(previous task i-1)
  MatC(previous task i-1)
  VecD(older task i-2)
```

也可按算子依赖拆成 AIC/AIV 两侧：

```text
AIC: MatA(current) -> MatC(previous)
AIV: VecB(previous) -> VecD(older)
```

这样每个 core 只在任务流开头启动一次，在任务流结尾排空一次。

---

## 2. 适用条件

必须同时满足：

| 条件 | 要求 |
|---|---|
| 任务可展平 | per-core 工作可以拆成有确定顺序的原子任务，每个任务包含完整的 batch/head/row/reduce tile 坐标 |
| 固定依赖距离 | `VecB` 消费当前或前一任务的 `MatA` 结果，`MatC` 消费同一任务的 `VecB` 结果，`VecD` 消费更早任务的 `MatC` 结果，依赖距离可由 3 槽描述 |
| 状态边界明确 | online softmax、dropout、mask、累加器、梯度状态等跨 reduce tile 状态能用 `isFirstTile/isLastTile` 或等价字段表达 |
| 同一归约组连续 | 未实现跨核归约时，同一 query row block 的 reduce-axis tiles 必须在同一 core 内连续生成和执行 |
| slot 生命周期清楚 | 每个任务的 workspace、queue slot、signal slot 和片上缓存 slot 不会在消费者完成前被覆盖 |
| 基线稳定 | 修改前能稳定通过全量精度测试，并有可重复性能命令 |

优先适用：

- 每个外层 block 只有 2 到 4 个 reduce-axis tiles，局部流水 steady 很短。
- profiling 显示 AIC/AIV 存在大量 wait、signal、scalar 调度或 pipeline drain 开销。
- 算子已经有阶段化结构，如 `compute_score -> softmax/state -> compute_output -> normalize/writeback`。
- 多 head、多 batch、多 row block 在每个 core 上可串成较长任务流。

不适用或需先重构：

- 同一归约组的不同 reduce tiles 被分配到不同 core，且没有正确的跨分片 softmax/梯度归约。
- 任务间存在非固定距离依赖，不能用小环形缓存表达。
- 阶段函数依赖大量隐式全局上下文，且无法可靠改为按任务上下文执行。
- baseline 已有随机 hang、精度不稳定、workspace 覆盖或信号协议问题。

---

## 3. 必须保持的语义约束

1. 不改变数学公式、浮点精度、归一化顺序、mask/dropout 语义、输出布局和梯度累加公式。
2. 不改变跨核任务划分，除非同时实现并验证对应的跨核归约协议。
3. 不把同一 query row block 的 reduce-axis tiles 打散到不同 core，除非已有正确的分片合并公式。
4. 不在本策略中顺手缩减 workspace 槽数、改 L0/L1 缓冲、删除同步或提前释放信号；这些属于独立优化点。
5. 不复用原来的隐式当前上下文给不同流水年龄的任务。
6. 不允许 `VecB(previous)` 和 `VecD(older)` 共享同一套 mutable task fields，除非每次调用前完整设置上下文且没有异步延迟读取。
7. 不允许 task slot 被新任务覆盖后，旧任务的任一消费者仍可能读取该 slot。

---

## 4. 原子任务描述符

新增或重构一个显式任务描述符。字段名可按项目风格调整，但语义必须完整。

```cpp
struct AttentionTask {
    bool valid;
    uint64_t seq;
    uint32_t taskSlot;       // 任务描述符环形槽，通常 seq % 3
    uint32_t workspaceSlot;  // 首轮建议仍使用原数据槽数，不与 taskSlot 强绑定

    uint32_t batch;
    uint32_t qHead;
    uint32_t kvHead;
    uint32_t groupHead;      // GQA/MQA 可选；不用时置 0

    uint32_t qRowStart;
    uint32_t qRows;
    uint32_t kvStart;        // reduce-axis tile start，如 S/K/V block start
    uint32_t kvRows;

    bool isFirstReduceTile;
    bool isLastReduceTile;
    bool isFirstQueryTile;   // 可选，用于初始化输出或梯度状态
    bool isLastQueryTile;    // 可选，用于最终写回
};
```

要求：

- `seq` 单调递增，不因 batch/head/block 切换而重置。
- `taskSlot` 至少 3 槽，用于 `current / previous / older` 描述符。
- 首次落地时，workspace 数据槽保持原数量；不要同时实施 workspace 3 槽到 2 槽的优化。
- `isFirstReduceTile` 必须只在同一归约组的第一个 reduce tile 为真。
- `isLastReduceTile` 必须只在同一归约组的最后一个 reduce tile 为真。
- GQA/MQA 中多个 qHead 共享 kvHead 时，任务描述符必须同时携带 qHead 和 kvHead，不能只用其中一个隐式推导。
- 若算子存在 latent/head 维度映射（部分多头注意力变体），必须把影响地址和状态归属的维度放入任务描述符或可纯函数推导。

---

## 5. 任务生成顺序

任务生成必须保证同一归约组连续：

```text
(batch, qHead, kvHead, qBlock A, reduce tile 0)
(batch, qHead, kvHead, qBlock A, reduce tile 1)
...
(batch, qHead, kvHead, qBlock A, reduce tile last)
(batch, qHead, kvHead, qBlock B, reduce tile 0)
...
```

对不同算子的归约组定义：

| 算子类型 | 归约组必须保持连续的键 |
|---|---|
| FA/GQA/MQA/SFA forward | `batch, qHead, kvHead, qRowStart` 的所有 K/V tiles |
| 注意力 forward | `batch, qHead（或 latent-head group）, qRowStart` 的全部 KV tiles |
| FAGrad/SFAGrad | 同一输出梯度累加目标或同一 softmax 反传归约目标的所有 reduce tiles |

禁止生成顺序：

```text
qBlock A, reduce 0
qBlock B, reduce 0
qBlock A, reduce 1
qBlock B, reduce 1
```

除非已经实现跨 task 状态重排，并证明 online state、dropout/mask、累加器和最终输出仍等价。

---

## 6. 连续流水执行模板

推荐最小结构：

```cpp
constexpr uint32_t TASK_CACHE_SIZE = 3;
AttentionTask taskRing[TASK_CACHE_SIZE] = {};
TaskCursor cursor = BuildCoreStartCursor();
uint64_t tick = 0;
uint64_t seq = 0;
bool hasTask = HasTask(cursor);

while (hasTask || AnyValid(taskRing)) {
    AttentionTask &current = taskRing[tick % TASK_CACHE_SIZE];
    AttentionTask &previous = taskRing[(tick + TASK_CACHE_SIZE - 1) % TASK_CACHE_SIZE];
    AttentionTask &older = taskRing[(tick + TASK_CACHE_SIZE - 2) % TASK_CACHE_SIZE];

    current.valid = false;

    if (hasTask) {
        current = BuildTask(cursor);
        current.valid = true;
        current.seq = seq;
        current.taskSlot = seq % TASK_CACHE_SIZE;
        current.workspaceSlot = SelectWorkspaceSlot(seq, current);
        AdvanceCursor(cursor);
        ++seq;
        hasTask = HasTask(cursor);
    }

    if ASCEND_IS_AIC {
        if (current.valid) {
            PrepareMatAInputs(current);
            ComputeMatA(current);
        }
        if (previous.valid) {
            ComputeMatC(previous);
        }
    }

    if ASCEND_IS_AIV {
        if (previous.valid) {
            SetTaskContext(previous);
            ComputeVecB(previous);
        }
        if (older.valid) {
            SetTaskContext(older);
            ComputeVecD(older);
        }
    }

    older.valid = false;
    ++tick;
}
```

实现时必须按实际依赖调整同一 tick 内阶段顺序。若 `MatC(previous)` 必须等待 `VecB(previous)` 的结果，则 AIC 侧应在 `ComputeMatA(current)` 后等待 `previous` 的 ready 信号，再执行 `ComputeMatC(previous)`。不要把上述模板理解为省略同步。

---

## 7. 隐式状态重构要求

连续流水后，同一 tick 内不同阶段可能处理不同任务：

```text
VecB: previous task
VecD: older task
MatA: current task
MatC: previous task
```

因此必须消除或隔离以下隐式状态：

- 当前 batch/head/query row/reduce tile。
- 当前有效行数、有效列数、tail 标志。
- 当前 workspace base、slot id、GM offset。
- 当前 softmax/normalization/dropout/gradient state 指针。
- 当前 mask、scale、alibi、rope、causal 边界。

允许两种实现方式：

1. 阶段函数直接接收 `const AttentionTask &task`。
2. 每次调用阶段函数前执行 `SetTaskContext(task)`，且该上下文只在同步调用期间被读取。

禁止：

- `VecB(previous)` 设置上下文后，`VecD(older)` 继续使用 previous 的上下文。
- AIC 和 AIV 共用一份会被异步覆盖的 mutable task context。
- 依赖 `curTask++`、`curHead++` 等隐式推进来推导另一个流水年龄的任务。

---

## 8. 同步与生命周期要求

必须为每类跨阶段数据建立明确 happens-before：

| 数据 | 生产者 | 消费者 | 要求 |
|---|---|---|---|
| score 或中间矩阵 S | `MatA(task)` | `VecB(task)` | task slot 不得覆盖；ready 信号或 queue handoff 必须对应同一 task |
| probability/weight 或梯度中间量 P | `VecB(task)` | `MatC(task)` | AIC 等待的是同一 `seq/workspaceSlot` 的 P-ready |
| output/accumulator 中间量 O | `MatC(task)` | `VecD(task)` | VecD 读取前必须等待 MatC 完成 |
| online state 或梯度 state | `VecB/VecD` | 后续 reduce tile 或最终写回 | 按 `isFirstReduceTile/isLastReduceTile` 初始化、更新和释放 |

约束：

- 每个 signal/event/queue slot 必须能映射到 `task.seq` 或 `workspaceSlot`。
- 释放 slot 必须发生在该 slot 最晚消费者完成之后。
- 如果使用 `SetFlag/WaitFlag`，event ID 必须按项目和 AscendC 规则申请、配对和释放。
- 如果使用 `TQue`，必须保持 `AllocTensor -> EnQue -> DeQue -> FreeTensor` 生命周期完整。
- 如果使用 `TBuf`，必须额外补齐必要 `SetFlag/WaitFlag`，因为 `TBuf` 不提供 queue 同步语义。
- 不要用精度通过来证明同步安全；必须能说明每个冲突访问的 happens-before 路径。

本策略不要求删除任何同步。若发现冗余同步，应作为独立“同步删减”策略单独提交和验证。

---

## 9. 实施步骤

LLM/agent 必须按以下顺序实施：

1. **建立阶段 DAG**：列出当前算子的阶段、输入输出、生产消费关系和跨阶段数据。
2. **识别原子任务**：确定最小可流水任务，一般是一个 query row block 加一个 reduce-axis tile。
3. **证明任务顺序**：写出 per-core 任务生成顺序，证明同一归约组 reduce tiles 连续。
4. **新增任务描述符**：加入显式 `AttentionTask` 或等价结构，不改变计算逻辑。
5. **改造阶段接口**：让每个阶段接收 task 或在调用前设置独立 task context。
6. **实现 3 槽调度 loop**：先保持原 workspace 槽数、原同步协议和原 tile 大小。
7. **处理 prologue/epilogue**：用 `valid` 位自然启动和排空，禁止写多个特殊 case 分支覆盖主逻辑。
8. **编译验证**：修复所有接口、类型和条件编译问题。
9. **精度验证**：先跑基础 case，再跑全量 case。
10. **性能验证**：对比 task duration、AIC/AIV wait、scalar time、cube/vector time。

首轮提交只允许包含连续任务流水所必需的改动。禁止同时改 workspace 槽数、L0/L1/TBuf/TQue、tile shape、fast path、同步删减或信号提前释放。

---

## 10. 验收标准

正确性：

- 每个任务的 `MatA / VecB / MatC / VecD` 或对应阶段均执行一次，不能漏算或重复。
- 同一归约组的 reduce tiles 顺序与原数学语义一致。
- 所有基础、泛化、tail、head mapping、mask/dropout/causal、梯度累加 case 精度通过。
- 无 hang、随机失败、workspace overwrite、event ID 泄漏或队列生命周期错误。

性能：

- 每个 core 的流水启动和排空次数从“每外层 block 一次”下降为“每连续任务流一次”。
- AIC 等待 Vec 中间量的时间下降，或 AIV 等待 Cube 中间量的时间下降。
- task duration 下降；Cube FOPs 和 Vector FOPs 不应因本策略增加。
- 若端到端性能回退超过测量噪声，必须回滚或定位到具体等待、slot 覆盖、上下文重设或同步问题。

建议记录：

```text
task_count_per_core
pipeline_ticks
matA_count / vecB_count / matC_count / vecD_count
AIC wait by signal id
AIV wait by signal id
Cube time / Vector time
Task Duration
workspace bytes
```

---

## 11. 常见错误

1. **只改循环顺序，不改隐藏上下文**：VecB 和 VecD 实际读到同一 task context，导致跨 block 污染。
2. **任务顺序打散归约组**：online softmax 或梯度归约状态被错误复用。
3. **task slot 与 workspace slot 混用**：3 槽描述符覆盖安全，但数据 slot 过早覆盖。
4. **排空不足**：最后两个任务的 VecB/MatC/VecD 没有执行。
5. **同步信号按 tick 等待而非按 seq/slot 等待**：AIC/AIV 等到错误任务的 ready。
6. **同时合并其他优化**：性能变化无法归因，精度失败难以定位。
7. **把 GQA/MQA 的 kvHead 当 qHead**：共享 KV 场景下地址和状态归属错误。
8. **FAGrad/SFAGrad 忽略累加目标**：不同 reduce tile 对同一梯度输出的累加顺序被破坏。

---

## 12. 最小回滚边界

本策略应当能被一个提交完整回滚。回滚后必须恢复：

- 原阶段调用顺序。
- 原任务生成循环。
- 原 workspace slot 选择。
- 原同步信号位置和 event 生命周期。
- 原阶段函数上下文方式。

若实现需要修改公共 helper，必须保证 helper 的旧行为仍可由旧调用路径覆盖，避免回滚时牵连无关优化。

## 检索卡（短卡）

动作：将按外层 block 反复启动并排空的局部流水改为全核连续任务环形流水。
适用：每核工作可拆成有确定顺序且坐标完整的原子任务。
限制：不得改变公式、精度、归一化顺序、mask/dropout、输出布局或梯度累加。
范围：attention 类 AscendC kernel 的 per-core 任务流水。
检索词：连续任务、环形流水、reduce-axis tile、逻辑子任务、任务坐标。
机会：每个外层 block 都重复 prologue、短 steady 与 epilogue。
