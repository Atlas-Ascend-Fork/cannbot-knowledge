---
type: Runbook
title: AI CPU 侧调试接口边界（assert / printf / DataStoreBarrier）
description: 区分 AI CPU 的 assert、printf、DataStoreBarrier 与 AI Core 同名接口；核对异构调用域、每核单次 Dump 预算和写可见性，并用来源中的读侧同步示例排查问题。
tags:
- task.debugging
- task.lookup
- topic.architecture
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/printf.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/assert.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/DataStoreBarrier.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/ai_cpu_api_list.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_cpu_programming.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/printf.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/assert.md
  role: supporting
created_at: '2026-10-23T02:30:00Z'
updated_at: '2026-10-23T02:30:00Z'
platforms:
- '950'
- a2
- a3
---

# AI CPU 侧调试接口边界（assert / printf / DataStoreBarrier）

## 触发条件

- 要在 AI CPU 算子（`.aicpu` 文件中的 `__global__ __aicpu__` 核函数）里打印日志、做断言，或让本核写的数据对 AI Core 可见，需要先确认这三条接口各自能用到什么程度。
- 典型症状：断言条件不成立却没有断言输出；printf 无输出或输出不全；AI Core 读到旧的 tiling 值；把 AscendC Kernel 侧的 printf/assert 写法照搬进 `.aicpu` 后编不过或行为不符。

## 适用平台与接口面

- 三条接口的产品支持面在来源里逐条一致：Ascend 950PR&950DT 支持、Atlas A3 支持、Atlas A2 支持；Atlas 200I/500 A2 推理产品、Atlas 推理系列产品 AI Core、Atlas 推理系列产品 Vector Core、Atlas 训练系列产品均不支持。
- AI CPU 编程自身的支持面相同（950 / A3 / A2）。
- **所引 AI CPU API 列表只列出这三条**；这限定了本卡的证据范围，不能由列表缺项推导 AI CPU 不存在其他调测能力。AI Core 侧接口见相邻路由卡，不可直接套用于 AI CPU。

## 选哪条接口（先分清目标）

| 目标 | 用哪条 | 依据与配套边界 |
|---|---|---|
| 打印标量、地址或字符串 | printf | 默认把内容解析并打印到屏幕；格式支持面见边界 2，输出量受共享 Dump 预算限制 |
| 检查不变量并让算子停下来 | assert | 条件为假时输出条件、触发文件、行号并终止程序；来源未给出自定义消息形式 |
| 让本核算出的数据对 AI Core 可见 | DataStoreBarrier | 保证先前写操作完成且可见；读侧与同步方式依具体协议确定（边界 4） |

## 边界 1：能出现在哪里（调用域）

- 三条接口的共同约束：**仅支持通过 `<<<...>>>` 调用，并在异构编译场景使用**。这里的 `<<<...>>>` 描述的是 AI CPU Kernel 的启动方式，不是修饰 assert/printf 调用本身的语法。
- AI CPU Kernel 定义规范：必须 `__global__ __aicpu__` 联合声明；返回类型不能是 void、入参只能是一个指针；不能是类的成员函数、不能位于匿名空间；返回值用于 Runtime 报告状态，用户无需基于返回值编写处理逻辑，也不能把调用当右值使用；来源示例允许 `return 0;`。
- Host 侧：`.asc` 文件中只能 `extern` 声明 `__global__ __aicpu__` 函数（不能在 `.asc` 里定义），并用 `<<<numBlocks, nullptr, stream>>>(ptr, sizeof(...))` 启动；大小是 Host 启动调用参数，不是 Kernel 的第二个形参。numBlocks 建议 1（AI CPU 不支持分核，Host 侧多核无意义）；**同一条 stream 不能同时用于 AI Core 与 AI CPU 算子调用**。
- 文件形态：AI CPU 实现文件用 `.aicpu` 后缀（或 `.cpp` 加 `-x aicpu`）；Host 调用代码在 `.asc` 里，两者分别编译后链接成可执行文件。
- 库链接：bisheng 命令行编 `.aicpu` 时需 `--cce-aicpu-laicpu_api` 链接 `libaicpu_api.a`、`--cce-aicpu-L` 指定库路径；CMake 构建时框架自动处理，开发者无需额外关注。
- 判读：调试接口"写了没反应"时，先确认它写在 `.aicpu` 的 AI CPU Kernel 路径上，且该 Kernel 确实通过 `<<<...>>>` 启动。

## 边界 2：与 AI Core 侧同名接口的差别（不能互抄）

| 维度 | AI CPU 侧（本卡） | AI Core（AscendC Kernel）侧 |
|---|---|---|
| 头文件 | `aicpu_api.h` | `utils/debug/asc_printf.h`、`utils/debug/asc_assert.h`；用 `AscendC::printf` 形式还须额外包含 `kernel_operator.h` |
| assert 调用形式 | `assert(expr)`，与 C 语言一致，**不需要** AscendC 命名空间 | `assert` / `ascendc_assert`，含 `(expr, fmt, args...)` 重载 |
| 断言失败行为 | 输出断言条件、触发文件名、行号，并**终止程序** | 打印断言失败信息并**触发异常**，算子执行失败 |
| 系统 `<cassert>` | Kernel 开发不要包含系统的 `assert.h`，会导致宏定义冲突 | 需要标准库 `<cassert>` 时，必须先包含 `<cassert>` 再包含 `kernel_operator.h` / `asc_assert.h`，避免覆盖 Ascend C 的 `assert` 定义 |
| Release / NDEBUG | 来源未声明 NDEBUG 规则 | CMake Release 默认使能 `NDEBUG`，断言接口不生效 |
| 自定义错误信息 | 原型只有 `assert(expr)`，来源未给出 fmt 形式 | `assert(expr, fmt, args...)` / `ascendc_assert(...)` 支持自定义消息 |
| printf 转换说明 | `%d`/`%i`、`%f`（float/half）、`%x`、`%s`、`%u`、`%p` | 另有 `%ld`/`%lld`/`%lx`/`%llx`/`%lu`/`%llu`、`%F`，并支持 bfloat16_t 等 |
| printf 转义字符 | **不支持**打印除换行符以外的其他转义字符 | 来源未给出同类限制说明 |
| 产品面 | Atlas 推理系列产品不支持 | assert 在 Atlas 推理系列产品 AI Core / Vector Core 支持；printf 在该系列不支持 |

判读：两侧的调测合同不同——把 Kernel 侧的格式串、数据类型假设或头文件习惯直接搬进 `.aicpu` 是错误方向，反之亦然。

## 边界 3：输出可见性与共享 Dump 预算

- 输出形态：printf 默认把内容解析并打印在屏幕上；assert 失败时输出断言条件、触发文件名与行号，来源示例输出为：

    ```text
    [ASSERT]` assertFlag == 12 ' at /home/.../test.cpp:36
    ```
- 预算：来源写明"该接口使用 Dump 功能，所有使用 Dump 功能的接口在每个核上单次 Dump 的数据量不可超过 1M"，**超出则不会打印**（不是报错）。这条约束同时写在 assert 与 printf 下，即口径是"所有使用 Dump 功能的接口"共同适用——assert 与 printf 不是各自拿 1M。
- 判读：断言或日志缺失时，**不能由"没看到文字"推出条件为真或 Kernel 没执行**；先排除超预算、编译/调用域未生效、执行路径未跑到三类原因。超预算时来源只说明不打印，不能据此推断会截断并保留前半段。
- 与 AI Core 侧口径不同：AI Core 侧 SIMD 单次调用（默认 30KB）与 SIMT（2MB Global Memory 缓存）各有自己的限制与配置字段；AI CPU 侧来源没有给出可配置的缓冲字段，不能拿 Kernel 侧的容量结论外推。

## 边界 4：DataStoreBarrier 只解决"写可见"，不解决"同步语义"

- 语义：数据同步屏障指令，阻塞当前线程，确保所有先前的写内存操作完成并对其它硬件单元可见后，才继续执行后续指令；用于 AI CPU 与 AI Core 多核之间的数据一致性。
- 位置：在 AI CPU Kernel 里写完与 AI Core 共享的 tiling 数据后调用 `AscendC::DataStoreBarrier()`，使 AI Core 能正确读到 tiling 数据。
- 配套示例：来源的 tiling 交接样例中，AI Core 侧用 `volatile` 读锁变量 + `DataCacheCleanAndInvalid<uint64_t, CacheLine::SINGLE_CACHE_LINE, DcciDst::CACHELINE_OUT>` 直接访问 Global Memory 取最新数据，再用 `SyncAll<false>()` 做核间同步、用 lock 值做握手。这是该样例的一组动作，不是所有协议必须采用的固定 API 组合。
- 判读：只加 `DataStoreBarrier` 不能替代核间同步协议；读侧缓存维护和同步须按实际数据流与协议核对，否则可能读到旧值。它也不是 AI Core 侧 `PipeBarrier`/`SyncAll` 的对应物；本卡未核对其他 AI CPU 屏障接口。

## 症状处置表

| 症状 | 先查 | 动作 |
|---|---|---|
| assert 条件不成立但没有断言输出 | 是否满足调用域（`.aicpu` + `<<<...>>>`）；Dump 预算 | 确认断言在 AI CPU Kernel 内、启动语法正确；减少同核单次输出量；仍无输出按"接口支持 ≠ 当前场景能跑出来"排查编译与执行路径 |
| printf 无输出或输出不全 | 每核单次 Dump ≤1M 的共享预算、执行路径与格式 | 缩减单次输出量并复查输出是否恢复；不把超预算直接判作前半段截断 |
| printf 打的类型/格式不对 | 转换说明是否在 AI CPU 支持集合内 | 只用 `%d`/`%i`、`%f`、`%x`、`%s`、`%u`、`%p`；需要其他格式时先核对目标版本文档；不得为了打印将 AI CPU 数据处理直接改成 AI Core 调用 |
| AI Core 读到旧 tiling | 写侧是否调用 `DataStoreBarrier`；读侧缓存与同步协议 | 若采用来源的 tiling 交接样例，核对 `DataCacheCleanAndInvalid`、`SyncAll`/lock；其他协议按自身读侧与同步要求验证 |
| `.aicpu` 编译或链接失败 | 文件形态与库链接 | `.aicpu`（或 `-x aicpu`）编译时带 `--cce-aicpu-laicpu_api` 与 `--cce-aicpu-L`；CMake 工程交给框架链接 |

## 验证方式

1. **编译级**：`.aicpu` + `.asc` 两个文件能编成可执行文件（bisheng 命令行带 `--cce-aicpu-*`，或 CMake 走 AI CPU 语言支持）。
2. **行为级**：构造必然失败的 assert，确认打印条件、文件、行号；对每种转换说明各打印一次，确认支持面与边界 2 一致。
3. **一致性级**：按来源样例做"AI CPU 写 tiling → `DataStoreBarrier` → AI Core 侧读"，确认 AI Core 读到新值而不是旧值。
4. **反向确认**：接口"没输出"时先区分超预算不打印、调用域/编译未生效、执行路径未跑到，再动代码。

## 失效边界

- 本卡只覆盖 AI CPU 侧这三条接口。AI Core（AscendC Kernel）侧调测接口的选型与诊断不在本卡范围，见下方相邻卡。
- 平台面：950 / A3 / A2 支持，Atlas 200I/500 A2 推理产品、Atlas 推理系列产品、Atlas 训练系列产品不支持。Kernel 侧 assert 在 Atlas 推理系列产品另有支持，**不能与 AI CPU 的支持面互推**。
- 来源未声明的内容按"未声明"处理：AI CPU 调测输出的落盘路径与日志文件字段、可配置的 Dump 缓冲上限、assert 的自定义消息形式，本卡都不做推断。
- 本卡为来源蒸馏，未在 950 上执行编译、打印或一致性验证；"验证方式"是要做的动作，不是已完成证据。

## 与相邻卡的分工

- 接口事实（原型、参数、格式表、支持矩阵、逐接口约束）归镜像卡 [assert（AI CPU API）](../../../ops/ascendc/apis/ai_cpu_api/assert.md)、[printf（AI CPU API）](../../../ops/ascendc/apis/ai_cpu_api/printf.md)、[DataStoreBarrier](../../../ops/ascendc/apis/ai_cpu_api/data_store_barrier.md)；本卡不重复它们的参数表，只给三条接口作为**一个集合**的使用边界。
- 固定 reference 的调用合同与版本边界归 [assert（AI CPU API）：固定 reference 调用约束](../../../ops/ascendc/guides/diagnostics/aicpu_assert_reference_contract.md) 与 [printf（AI CPU API）：固定 reference 调用约束](../../../ops/ascendc/guides/diagnostics/aicpu_printf_reference_contract.md)；本卡在其上补调用域、Dump 预算、与 AI Core 侧的对照以及 DataStoreBarrier 的配对要求。
- AI Core 侧的调测接口路由归 [Kernel 调试接口路由矩阵：症状 × 目标平台与编程模式](../../../contrib/ascendc/runbooks/runtime/kernel_debug_api_platform_mode_matrix.md)——它明确把 AI CPU 侧排除在外，本卡正是它的 AI CPU 补集；Kernel 侧同名接口的事实见 [printf（tuning interface）](../../../ops/ascendc/apis/utils_api/tuning_interface/printf.md) 与 [assert（tuning interface）](../../../ops/ascendc/apis/utils_api/tuning_interface/assert.md)。
