---
type: Runbook
title: Kernel 侧 assert 与 __trap 选型及失败诊断
description: 在 AscendC Kernel 中选择 assert/ascendc_assert 或 __trap；先核对失败是否归属目标断言，再区分标准上下文和可选消息缺失，以确定失败输入验证断言链路并保留 Trap 前的证据。
tags:
- task.debugging
- topic.implementation.debugging
- topic.programming_model.execution_model.simt
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/assert_and_trap.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/platform_matrix.md
  role: constraint
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/diagnosis_workflow.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/debug_api_quickref.md
  role: supporting
created_at: '2026-10-23T01:40:00Z'
updated_at: '2026-10-23T10:20:04Z'
platforms:
- '950'
- a3
- a2
---

# Kernel 侧 assert 与 __trap 选型及失败诊断

`assert` / `ascendc_assert` 与 `__trap` 常被当成同一类"让算子停下来"的手段混用，但两者的
能力边界不同：断言**带条件表达式、源码位置和可选的自定义消息（受模式限制）**，条件为假时输出断言上下文并触发
异常，算子执行失败；`__trap` **无参数、无返回值**，只负责在 SIMT 代码中立即中断 Kernel，
不携带任何原因信息。选错会直接导致两类典型症状——该响的断言不响，或者算子被中断却查不出
为什么。

## 触发条件

- 想在 Kernel 里对非法索引、越界长度、不可恢复状态做防护，不确定该用哪个接口；
- 断言写了但从未触发，算子继续跑出错误结果；
- 断言或 `__trap` 触发后算子失败，但失败现场缺少可用信息；
- 断言消息该带参数的地方没带出来，或编译期报宏定义冲突。

## 第 1 步：先按能力选型

1. **想让错误状态立即可见并中止算子** → 用 `assert` / `ascendc_assert`（头文件
   `"utils/debug/asc_assert.h"`）。二者在 AscendC 内提供相同的断言能力，条件为真时继续执行，
   条件为假时输出断言上下文并触发异常。
2. **只在 SIMT 线程发现不可恢复数据（NaN、非法索引、不可恢复状态）时停止** → 用条件判断 +
   `__trap()`。它适合"条件已经由你自己判好、只需要立刻掐断"的场合。
3. **需要条件表达式、源码位置或自定义消息** → 用断言，不要用 `__trap`。`__trap` 没有这些能力，
   事后无法从它本身读出触发原因。
4. **不要用"打印一句然后继续执行"替代断言**：需要中止语义时，应使用当前平台与模式支持的断言或 Trap，而不是仅打印后继续执行。

### 平台红线（选型前必须先过这一条）

- `__trap` 的**公开支持面仅 Ascend 950PR & 950DT**（SIMT / SIMT VF 场景）。A2、A3 在当前公开
  文档中**不支持** `__trap`，310P/310B 与 910/Kirin 同样不支持；不能用它向 A2/A3 或通用 SIMD
  无条件承诺可用。
- 即使编译头文件里存在其他条件编译分支，也必须**以目标版本的公开文档为准**。
- `assert` / `ascendc_assert` 的支持面宽得多：Ascend 950 为 SIMD 以及 SIMT/VF 相关变体，
  A3、A2 为 SIMD（310P SIMD 文档支持，310B 不支持，910/Kirin 不支持）。因此在 A2/A3 上应规划
  SIMD 形式的断言，而不是 `__trap`。
- "API 支持"不等于"当前调用场景可运行"：还要确认 CPU 调试 / 仿真 / 上板、直接调用 / 算子入图、
  编译模式与版本。

## 第 2 步：先分算子失败、标准上下文与自定义消息

先不要把“没有看到预期消息”直接判成断言未生效。按下面三种观测分流：

1. **算子失败**：先保留返回码、失败日志和执行状态，再核对失败是否发生在目标断言的条件和执行路径上；其他原因也能使算子失败，失败本身不能证明目标断言触发。
2. **标准断言上下文出现**：核对条件和源码位置是否属于目标断言。归属明确时断言链路已触发；即使自定义 `fmt`/`args` 没有出现，也不能判定断言未生效。
3. **仅自定义消息缺失**：CPU 调试、SIMT VF 和 SIMD VF 等场景可能只输出标准断言上下文，`fmt`/`args` 不生效。这是消息模式限制；先核对标准上下文与失败归属，不归类为断言未触发。

未能确认失败或标准上下文归属目标断言时，先检查目标条件和执行路径；确认目标断言未触发后再走第 3 步。算子因其他原因失败也不跳过这一步。

## 第 3 步：断言未触发时，区分条件、执行路径与调试配置

断言"没有失败"不等于条件正确。逐类排除：

1. **条件确实为真**：先把条件和实际输入值对一遍，不要因为"不可能成立"就跳过。
2. **当前代码路径没有执行**：语句所在分支根本没走到，或被 Block / 线程条件过滤掉，
   或 Kernel 在到达该语句前已经失败。
3. **`NDEBUG`**：Release 工程通常定义 `NDEBUG`，此时断言不生效。确认当前构建是调试配置。
4. **`ASCENDC_DUMP=0`**：该开关会使这类调试接口不生效，断言与 dump、`printf` 一起被关掉。
5. **宏定义被覆盖（附带检查项）**：需要包含 `<cassert>` 时，必须**先包含 `<cassert>`，再包含
   `kernel_operator.h` 或 `utils/debug/asc_assert.h`**，否则标准库会覆盖 AscendC 的宏定义，
   表现为断言行为异常。

## 第 4 步：用确定失败的最小输入验证宏生效

在排查第 3 步之前（或之中），先做一次**链路自证**：构造一个**确定失败**的最小输入，让断言条件
在该输入下必然为假，确认输出中出现断言上下文且算子执行失败。链路成立后，再恢复真实条件。

- 链路自证成功 + 真实条件不触发 → 回到第 3 步的第 1、2 类（条件为真 / 路径未执行）。
- 链路自证没有归属于该断言的失败或标准上下文 → 先确认测试路径确实执行，再查第 3 步的第 3、4、5 类（`NDEBUG`、`ASCENDC_DUMP`、宏覆盖）；
  如果只是自定义消息缺失而标准上下文已归属该断言，先检查第 2 步的模式限制，不把它当成断言未生效。
- 自证用的临时条件不要留在代码里，验证完立即恢复。

## 第 5 步：Trap 路径必须在触发前留可观测上下文

`__trap` 只负责中断，不输出条件、源码位置或消息，因此**触发前**就要把上下文写出去：

- 用少量输出或写回可观测位置的方式，记录判据取值、索引、阶段标识等最必要的信息；
- 判据本身（如 `isnan(x[idx])`）要能在事后复核，不要用无法复现的中间量做判据；
- 如果需要条件表达式、源码位置或自定义消息，说明这里应该用断言而不是 `__trap`。

## 第 6 步：断言或 Trap 导致算子失败时，保留失败证据

- **保留失败日志与返回码**，不要只记录"算子失败了"。
- 断言通常自带源码位置和条件，可直接作为定位起点；`__trap` 没有这些信息，只能依赖第 5 步的留痕。
- 若失败同时伴随错误码、plog、卡死或崩溃，说明已经超出本卡范围，应继续走 runtime / crash 类的
  日志与错误码排查路线。

## 验证方式

按"接口能编译 → 语句确实执行 → 输出或异常符合预期 → 扩大到真实数据与多核 → 关闭或删除调试代码"
逐级验证，每一步只增加一个变量。**不要为了让输出出现而放宽真实的边界检查**——把越界条件改宽
以"看到断言触发"，得到的是无效证据。

断言会影响性能，且可被 `NDEBUG` 或 `ASCENDC_DUMP=0` 禁用，不能作为生产路径唯一的输入校验或安全防护。调试完成后按工程约定清理临时断言与留痕代码；关闭调试接口前确认必要的错误处理并不依赖它们。

## 失效边界

- 本卡结论来自 asc-devkit 内核调试 Skill 的参考资料（固定到 40 位 commit）；最终以目标 CANN 版本的
  公开 API 文档、公开头文件和实际编译验证为准，公开文档与内部资料不一致时以公开文档为准。
- **`__trap` 的公开支持面仅为 Ascend 950PR & 950DT（SIMT / SIMT VF）**；本卡不提供 A2/A3 上的
  `__trap` 用法，也不把"头文件里能编过"当作可用证据。
- 断言支持面为 950（SIMD、SIMT/VF 变体）、A3 SIMD、A2 SIMD；`platforms` 只登记 950/A3/A2。
  310P 的 SIMD 断言在文档中有支持面，但**不在本卡登记范围**，在 310P 上使用前需按目标版本文档复核。
- A2/A3 的"主要为 SIMD"表示公开文档没有为它们承诺 SIMT 或 VF 变体，不能由产品名称推断所有
  断言形式都可用。
- 不覆盖：崩溃 / 卡死 / plog 错误码的根因分析；AI CPU 侧 assert 的调用与链接约束；CPU 侧调试手段；
  算子入图框架自身的日志通道。

## 与相邻卡的分工

- [Assert / ascendc_assert（镜像 API 卡）](../../../../ops/ascendc/apis/utils_api/tuning_interface/assert.md)：
  函数原型、`fmt` / `args` 能力矩阵、头文件与 `ASCENDC_DUMP` 等 API 事实归它；本卡只做**选型判定**
  与失败诊断流程。
- [\_\_trap（镜像 API 卡）](../../../../ops/ascendc/apis/utils_api/tuning_interface/_trap.md)：
  `__trap` 的原型、头文件与调用示例归它；本卡只强调它的平台红线与"中断无上下文"这一后果。
- [assert（AI CPU API）：固定 reference 调用约束](../../../../ops/ascendc/guides/diagnostics/aicpu_assert_reference_contract.md)：
  覆盖 **AI CPU 侧**（`<<<...>>>` 启动的 AI CPU Kernel、异构编译与 `libaicpu_api` 链接、每核 dump
  数据量上限）的 reference 约束；本卡覆盖 **Device 侧 AscendC Kernel** 调试路径，两者不可互相套用。
- [Kernel printf 无输出诊断](kernel_printf_no_output_diagnosis.md)：若现象是"printf 什么输出都没有"，
  先走它的开关 / FIFO / 执行路径排查；本卡处理的是"断言该响不响"与"断言或 Trap 把算子打挂"。
