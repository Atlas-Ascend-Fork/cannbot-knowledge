---
type: Concept
title: SIMD 核内自动同步与手动同步的决策边界
description: 对照硬件、TPipe-TQue 与 cce-auto-sync 的覆盖边界，说明 A2/A3 与 950 的差异、原子和缓存约束，以及静态 Tensor、同步定位与验证的限制。
tags: [task.implementation, task.debugging, topic.implementation.synchronization, topic.compilation]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/key_features.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/PipeBarrier_ISASI.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/TQueSync.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/Lock.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/Unlock.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/impl/basic_api/kernel_reg.h
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/atomic_operations/AtomicAdd.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/cache_control/DataCacheCleanAndInvalid.md
    role: constraint
created_at: "2026-11-02T01:33:19Z"
updated_at: "2026-11-03T07:39:15Z"
platforms: [a2, a3, "950"]
aliases: [自动同步, 手动同步, cce-auto-sync, TPipe-TQue 自动同步]
---

# SIMD 核内自动同步与手动同步的决策边界

## 适用范围与核心结论

本卡面向 Atlas A2/A3（NPU 架构 2201）与 Ascend 950PR/950DT（NPU 架构 3510）的 Ascend C SIMD 核内同步。它不覆盖核间、任务间同步，也不将这些流水级保证推广到 SIMT 线程同步或 VF 内部寄存器级同步。

**自动同步不是一个覆盖所有依赖的开关。** 硬件保证、TPipe-TQue 框架和毕昇编译器各负责不同范围；框架与 `--cce-auto-sync=on` 可以同时生效。判断一对访问是否需要手动同步，必须同时核对数据依赖、源/目的流水、编程范式、接口类型和目标架构。

## 三种同步责任如何划分

| 责任方 | 可以依赖的保证 | 不能据此推断的保证 |
| --- | --- | --- |
| 硬件 | 950 的 `PIPE_V → PIPE_V`；A2/A3 文档列出的掩码、搬运随路原子配置及 CTRL 寄存器相关 `PIPE_S` 接口与其他流水间的同步 | 不能扩大为所有 Scalar 接口、所有架构或所有流水都有硬件同步 |
| TPipe-TQue 框架 | 正确使用队列生命周期时，为支持的跨流水组合处理 RAW（先写后读）与 WAR（先读后写）依赖 | 不插入单流水同步；仅分配 Tensor 或仅使用 TBuf 不等于完成队列同步 |
| 毕昇编译器 | 满足接口约束时，在 AIV 中处理 `PIPE_S` 与 `PIPE_V/MTE2/MTE3` 的双向跨流水同步；2201 上还处理 `PIPE_V → PIPE_V` | 不处理 AIC/Cube 中任何类型的自动同步；不兜底所有跨流水或地址重叠的 DMA 依赖 |

### 框架自动同步与 cce-auto-sync 覆盖对照

下表中的框架支持项以来源给出的 **2201 AIV** 为边界，均要求正确队列流转；编译器支持项均要求选项开启且满足下文的接口约束。“不覆盖”不代表一定要手动插入，还应检查另一责任方或硬件是否已覆盖。

| 依赖方向或场景 | TPipe-TQue（2201 AIV） | cce-auto-sync | 架构边界与决策 |
| --- | --- | --- | --- |
| `V → V` | 不覆盖同流水 | 2201 支持；3510 由硬件保证 | 950 不需要手动 V barrier；不能推广到其他流水 |
| `V ↔ MTE2`、`V ↔ MTE3` | 支持 | 不覆盖 | 静态 Tensor 或未正确经过队列的依赖需显式处理 |
| `MTE2 ↔ MTE3` | 支持 | 不覆盖 | 3510 的框架组合须另核对，不能照搬本表 |
| `S ↔ V/MTE2/MTE3` | 不覆盖 | AIV 中对限定的 Scalar 接口支持 | 原始指针与未列入集合的 Scalar 原子接口不能据此省略同步 |
| 同流水 MTE2/MTE3 的重叠目的地址搬运 | 不覆盖同流水 | 不覆盖 | 按实际流水手动加入单流水 barrier |
| AIC/Cube 内部依赖 | 不属于本表；见下方有向组合 | 不覆盖任何类型 | 检查合法队列组合或架构支持的显式同步 |

针对 950/3510，固定来源提交的 `impl/basic_api/kernel_reg.h` 中，`PipeBarrierImpl<PIPE_V>()` 不调用 `pipe_barrier`，属于空操作；保留该写法可用于迁移兼容，新写 950 代码不应把它作为有效同步手段。这是具体 API 实现的结论，不应表述为“所有 Vector 相关依赖都不存在”。

### TPipe-TQue 的生效条件

必须使用该框架，并正确配对、组织 `EnQue/DeQue` 与 `AllocTensor/FreeTensor`。缺少消费端 `DeQue`，即使已经 `DataCopy` 和 `EnQue`，也不能认为 `MTE2_V` 已完整建立。静态 Tensor 编程不因使用 `LocalTensor` 就获得队列框架的同步。

2201 的 AIV 支持框架管理 `V ↔ MTE2`、`V ↔ MTE3`、`MTE2 ↔ MTE3`；涉及 `PIPE_S` 的组合和同流水不由队列框架补齐。AIC 支持的有向组合如下，不能将其推广为任意 Cube 流水组合：

| 源流水 | 框架支持的目的流水（2201 AIC） |
| --- | --- |
| `PIPE_M` | `PIPE_MTE1`、`PIPE_MTE2`、`PIPE_FIX` |
| `PIPE_MTE1` | `PIPE_M`、`PIPE_MTE2`、`PIPE_MTE3`、`PIPE_FIX` |
| `PIPE_MTE2` | `PIPE_M`、`PIPE_MTE1`、`PIPE_MTE3` |
| `PIPE_MTE3` | `PIPE_MTE1`、`PIPE_MTE2` |
| `PIPE_FIX` | `PIPE_M`、`PIPE_MTE1` |

这些框架覆盖表来自 2201，不作为 3510 的完整覆盖表使用；其他架构上的具体组合仍需核对对应文档。

### cce-auto-sync 的生效条件

- 来源所述的异构编译直调、Kernel 直调工程及自定义算子工程默认开启 `--cce-auto-sync=on`；仍需核对实际编译命令，显式设为 `off` 会关闭编译器自动插入。
- `PIPE_V/MTE2/MTE3` 接口必须操作基础 Tensor，即 `LocalTensor/GlobalTensor`；不能把此保证直接套用于原始指针访问或带 Layout 的扩展 Tensor。
- `PIPE_S` 只覆盖文档明确列出的集合：`LocalTensor::GetValue/SetValue/operator()`、`GlobalTensor::GetValue/operator()`、`GetReduceRepeatMaxMinSpr`、`GetReduceRepeatSumSpr`、`GetMrgSortResult`。
- 950 的标量原子 `AtomicAdd/AtomicCas/AtomicExch/AtomicMax/AtomicMin` 不在该集合内；它们与 MTE2/MTE3 读写 GM 有依赖时，需要开发者手动处理。这与硬件保证的搬运随路原子**配置**接口不是同一类操作。

### 原子操作：平台、流水同步与缓存一致性分别判断

| 操作类别 | 本卡来源确认的边界 | 不能混淆的保证 |
| --- | --- | --- |
| `SetAtomicAdd/Max/Min`、`DisableDmaAtomic`、`SetAtomicType` 等搬运随路原子配置 | A2/A3 的这些 `PIPE_S` 配置接口与其他流水间同步由硬件保证 | 配置生效不等于搬运已完成，也不等于缓冲区可安全复用；不能据此推断 950 的同类保证 |
| 950 的 Scalar 原子 `AtomicAdd/Cas/Exch/Max/Min` | 不在编译器自动同步的 Scalar 接口集合中；与 MTE2/MTE3 存在 GM 数据依赖时手动处理 | 原子读改写不等于跨流水顺序；例如来源中的 AtomicAdd 后搬入使用 `S_MTE2` 事件配对 |
| 950 的 `AtomicAdd` 与 DCache 交互 | 来源说明 Scalar 原子绕过 DCache，需按 `DataCacheCleanAndInvalid` 接口约束维护 GM/DCache 一致性 | 缓存维护与流水同步是两个独立问题，不能用 barrier 或事件替代缓存维护 |

这些结论绑定 frontmatter 中的官方固定提交，不表示所有 CANN/编译器版本都相同。复现或迁移时同时记录产品、NPU 架构、CANN/编译器版本及原子接口类别，再核对该版本的接口约束；本卡没有跨软件版本实验，不给出未经验证的兼容性结论，也不将 950 Scalar 原子能力推广到 A2/A3。

## 何时必须手动补同步

先列出真实的数据访问依赖及方向，再依次排查硬件保证、框架覆盖和编译器覆盖；任何一层都未覆盖时，不能凭“开了自动同步”删掉同步。

| 场景 | 决策 |
| --- | --- |
| 2201 上相邻 Vector 操作有依赖，且满足编译器自动同步约束 | 可由编译器插入 V 单流水同步；关闭选项后不能沿用该保证 |
| 950 上 `PIPE_V → PIPE_V` | 由硬件保证，不照搬 2201 的手动 V barrier 需求 |
| 两条 MTE2 搬运的 UB 目的区域重叠 | 两次搬运间手动加入 `PipeBarrier<PIPE_MTE2>()` |
| 两条 MTE3 搬运的 GM 目的区域重叠 | 两次搬运间手动加入 `PipeBarrier<PIPE_MTE3>()` |
| 静态 Tensor、未经过正确队列流转的 `MTE2 → V` 或 `V → MTE3` 依赖 | 不能由编译器的 Scalar 相关自动同步代替，需要显式跨流水同步 |
| 原始指针标量访问与搬运存在依赖 | 不满足基础 Tensor/Scalar 接口集合约束，需要按实际流水手动同步 |
| Cube 中的依赖未由合法队列组合管理 | 编译器不会补齐，需要选择架构支持的显式同步 |
| 对缓冲区进行循环复用 | 同时检查 RAW 和 WAR；只等“搬入完成”不能代替“上一次计算/搬出读完后才能覆盖” |

### 手动接口与事件管理

- **同流水**使用 `PipeBarrier<pipe>()`，等待该流水前序读写完成；不支持 `PIPE_S`。`PipeBarrier<PIPE_ALL>()` 会等待所有流水的先前操作，不应替代可以精确表达的单流水同步而无谓串行化。
- **跨流水**使用 `SetFlag/WaitFlag` 或 `TQueSync`。事件名按“源流水_目的流水”解释，例如 `MTE2_V` 表示 Vector 等待 MTE2；`SetFlag` 不阻塞源流水的后继指令，`WaitFlag` 才阻塞目的流水并消费标志。
- `SetFlag` 与 `WaitFlag` 的事件类型和 ID 必须一致并成对使用；相同事件、相同 ID 连续发送未消费的 `SetFlag` 属于未定义行为，不能用全流水 barrier 修复配对错误。
- TPipe-TQue 范式下，ISASI `SetFlag/WaitFlag` 的事件 ID 应由 `AllocEventID/FetchEventID` 获取。静态 Tensor 范式自行管理时，来源建议使用 0–5，不直接占用系统规划的 6 和自动同步使用的 7。
- `SetFlag/WaitFlag(ISASI)` 不保证跨硬件版本兼容；需要跨硬件版本接口时可查看 `TQueSync`，但仍需确认其流水参数和产品支持范围。
- 950 还支持 `Lock/Unlock` 管理流水依赖；A2/A3 不支持这组接口，不能把这一方案直接移植到 2201。每对调用必须使用相同的 `pipe` 和 MutexID，先 `Lock` 后 `Unlock`；相同 MutexID 的组合无论 `pipe` 是否相同，都不得嵌套。
- TPipe-TQue 范式下，`Lock/Unlock` 的 MutexID 必须通过 `AllocMutexID/ReleaseMutexID` 申请、释放；与 Lock 文档列出的可能申请、取得或操作 MutexID 的资源管理接口混用时，同样必须采用该方式。自管 ID 不登记到框架分配记录中，可能与 `TQue/TQueBind` 等接口使用的 ID 冲突，导致同步行为未定义；调用成对不能消除这一风险。
- 静态 Tensor 范式自行管理 MutexID 时，不得同时使用上述资源管理接口；来源建议使用 0–27，28–31 为系统内部规划预留，不建议使用。选择建议范围内的 ID 不代表可以绕过资源管理接口的混用限制，完整接口清单见下方 Lock API 卡。

## 同步检查、定位与验证边界

### 两种编程范式分别检查

| 编程范式 | 检查路径 | 共同检查项 |
| --- | --- | --- |
| TPipe-TQue | 核对 `AllocTensor/EnQue/DeQue/FreeTensor` 生命周期、队列对应的源/目的流水及复用顺序 | 硬件保证、编译器覆盖、RAW/WAR 依赖及地址重叠 |
| 静态 Tensor | 不依赖队列隐式同步；逐条核对数据依赖、显式 barrier/事件及缓冲区复用顺序，同时检查仍适用的编译器自动同步 | 同上；使用 `LocalTensor` 本身不代表已经建立跨流水顺序 |

静态 Tensor 是独立的编程选择，不必为了检查同步而改成 TPipe-TQue；两种范式都需要检查实际依赖，而不是只检查接口名称或事件数量。

### 从编译日志到目标平台实验

1. **确认前提**：记录目标产品/架构、CANN/编译器版本、实际 `cce-auto-sync` 选项、接口所属流水、Tensor 类型，以及对应范式下的同步和内存复用完整路径。
2. **检查编译器插入**：添加 `--cce-auto-sync-log=<file>` 和 `-g`。直接编译时写入编译命令；Kernel 直调工程通过 `ascendc_compile_options`，自定义算子工程通过 `add_ops_compile_options` 传入。日志中的 `line before` 表示紧接该源码行之前插入。
3. **检查框架和编译器的最终指令**：使用 `-DCMAKE_ASC_RUN_MODE=sim` 启用来源样例的 NPU 仿真构建，检查如 `core0.veccore0.instr_log.dump` 的指令日志。TPipe-TQue 没有独立同步日志；编译器日志未列出某事件，不代表框架一定没有插入它。来源展示的 `SET_FLAG/WAIT_FLAG/BAR` 日志解析示例仅针对 2201。
4. **检查顺序与实验结果**：对照依赖图检查生产者完成、消费者开始和缓冲区可复用的顺序；按实际编程范式，对重叠搬运、缺失 `DeQue`、静态 Tensor 显式事件和循环复用等边界做仿真或目标设备测试。事件配对与功能结果正确都不足以单独证明同步充分；编译成功、单次或多次精度通过也不能覆盖所有时序。精度异常、结果不稳定或卡死是定位线索，还需排除越界、未初始化和事件错误等其他原因。

### 受控串行化对照，不机械删除全部同步

以下是基于接口约束整理的定位方法，不是本次已执行的实验：

1. 保留可复现的基线，在同一产品和软件版本下固定输入、编译选项及精度判据；记录差异与原始日志。
2. 在已确认的单流水边界，可临时加对应 `PipeBarrier<pipe>()`；在接口支持且语义适合的边界，可用 `PipeBarrier<PIPE_ALL>()` 等待此前已提交操作，构造保守串行化对照。它会影响性能，不应保留为未经分析的最终方案。
3. 不将“删除全部同步后统一替换为全同步”作为通用方案。保留队列生命周期、事件配对以及 `Lock/Unlock` 的配对约束；全流水等待不能修复事件协议错误，也不能代替缓存一致性或核间同步。具体流水和架构必须仍满足接口支持范围。
4. 每次只改变一个依赖边界，比较精度、稳定性与指令顺序，再逐步缩小范围。加屏障后恢复正确只支持“该时序变化可能相关”的定位假设，不证明已找到唯一根因；应回到准确的 RAW/WAR 依赖和最小同步方案重新验证。

本卡未执行算子编译、NPU 仿真、真机精度或性能实验；以上是来源给出的验证入口及据其边界整理的检查方法，不是本次实测结果。

## 相关知识

- [自动同步原始说明](../apis/simd_api/basic_api/sync_control/intra_core_sync/key_features.md)：完整决策图、编程范式反例和日志样例。
- [核内同步能力概述](../apis/simd_api/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md)：硬件流水及合法事件组合。
- [PipeBarrier 接口](../apis/simd_api/basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md)：同流水屏障、重叠搬运与全流水等待的约束。
- [SetFlag/WaitFlag 接口](../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)：事件方向、配对和 ID 分配。
- [TQueSync 接口](../apis/simd_api/basic_api/sync_control/intra_core_sync/t_que_sync.md)：跨硬件版本的核内跨流水同步接口。
- [Lock 接口](../apis/simd_api/basic_api/sync_control/intra_core_sync/lock.md)：MutexID 分配与资源管理接口混用限制、配对顺序及禁止嵌套的完整约束。
- [Unlock 接口](../apis/simd_api/basic_api/sync_control/intra_core_sync/unlock.md)：指定流水前序指令完成后的 Mutex 释放语义及配套约束。
- [AtomicAdd 接口与官方样例入口](../apis/simd_api/basic_api/atomic_operations/atomic_add.md)：950 Scalar 原子的显式同步、DCache 约束及固定版本完整样例。
- [DataCacheCleanAndInvalid 接口](../apis/simd_api/basic_api/cache_control/data_cache_clean_and_invalid.md)：缓存维护语义、参数及产品支持范围。
