---
type: Runbook
title: Kernel 周期与时间戳测量：clock 与 asc_time_stamp
description: 在 Kernel 内用 clock 测同线程局部代码的相对周期差、用 asc_time_stamp 输出结构化时间戳时，如何摆正测量区、排除同步/冷启动/编译优化/测量次数的干扰，并定位"时间戳没有输出"；同时划清 clock 不是 profiling 采集器这一边界。
tags:
- task.debugging
- task.optimization
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/clock_and_timestamp.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/diagnosis_workflow.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/platform_matrix.md
  role: constraint
created_at: '2026-10-23T01:35:00Z'
updated_at: '2026-10-23T01:35:00Z'
platforms:
- '950'
- a3
- a2
---

# Kernel 周期与时间戳测量：clock 与 asc_time_stamp

## 触发条件

- 要判断 Kernel 内某段局部代码慢在哪里，准备用 `clock()` 取周期差；
- 要按阶段记录多个打点、并保留"哪条记录来自哪一步"的来源关系，准备用 `asc_time_stamp`；
- 已经拿到周期数字，但怀疑它不代表真实耗时——打印夹在测量区内、`start`/`end` 不在同一线程，或多核数值被当成一条时间线；
- `asc_time_stamp` 编译通过，却没有任何时间戳输出。

## 处置步骤

### 1. 先按"要不要结构化记录"选接口

两个接口回答的是不同问题，不要混用：

- `clock()` 返回 `uint64_t`，即从程序开始到调用时刻经历的时钟周期数。它**只适合测量同一线程中一段局部代码的相对周期差**：`start = clock(); RunTheCode(); end = clock();`，再看 `end - start`。
- 需要**跨阶段结构化记录**时用 `asc_time_stamp`；不要自行把 `clock` 的输出拼成 timestamp dump 的格式去冒充它是打点接口。

### 2. 摆正测量区（决定结果可不可信）

1. **把 `printf`/`asc_dump` 移出测量区域。** 调试输出本身会污染周期结果，落在 `start` 与 `end` 之间就不可信。
2. **确认 `start` 与 `end` 位于同一线程、同一逻辑阶段。** `clock()` 的数值不要跨线程或跨核直接比较、相加；不同线程或不同核的值不能当作一条全局同步时间线。
3. **只让一个代表线程打印结果**，或把结果写回 GM 后由 Host 汇总。多核都要看时，先固定来源关系（Block/线程 ID、阶段标签），不要假设多核输出天然有序。

### 3. 归因剩余偏差

即使测量区已经干净，下面五类因素仍会进入数字，结论里要显式说明，而不是当成噪声忽略：

- **同步**：测量区间内包含等待/同步时，测到的是"等待 + 执行"，不是纯计算时间；
- **冷启动**：首次执行的路径包含未预热的部分，与稳态不可比；
- **编译优化**：优化会改写甚至消除被测代码，同一份源码的测量结果随构建配置变化；
- **线程调度**：调度会改变执行顺序与等待，周期数随之变化；
- **测量次数**：单次测量抖动大，必须说明测了几次、取的是哪个统计量。

`clock` **不是 profiling 采集器**：它只返回一个计数，不产生结构化采集记录，也不携带阶段语义。要时间线、要采集器、要做阶段统计，就换到对应能力，不要拿 `clock` 硬凑。

### 4. 用 asc_time_stamp 时必须额外做的三件事

1. **重新编译并显式开启**：该能力默认关闭，编译时需要传入 `-DASCENDC_TIME_STAMP_ON`。只改开关却没重新编译，应作为"没有输出"的排查项。
2. **自定义 ID 取大于 `0xffff` 的值**：`[0, 0xffff]` 预留给 AscendC 内部各模块使用。
3. **控制每核累计 dump 数据量**，并检查 `ASCENDC_DUMP` 设置。

`asc_time_stamp` 在 SIMD Kernel 中按用户描述符输出结构化时间戳信息（含当前 cycle、PC、Kernel 入口等字段），主要用于 NPU 上板调试；当前公开文档声明**不支持算子入图场景**。

### 5. "时间戳没有输出"的排查顺序

1. 检查调用是否位于 SIMD 支持的 Kernel 路径；
2. 确认重新编译时确实传入了 `-DASCENDC_TIME_STAMP_ON`；
3. 确认不是 CPU 调试或算子入图场景；
4. 检查每核累计 dump 数据量与 `ASCENDC_DUMP` 设置；
5. 检查 Kernel 是否在执行到打点位置前就失败或提前返回。

### 6. 平台与编程模式可用性

| 接口 | Ascend 950 | A3 | A2 | 310P/310B | 910/Kirin |
| --- | --- | --- | --- | --- | --- |
| `clock` | SIMD、SIMT | SIMD | SIMD | 当前文档不支持 | 不支持 |
| `asc_time_stamp` | SIMD、NPU 上板 | SIMD、NPU 上板 | SIMD、NPU 上板 | 当前文档不支持 | 不支持 |

A2/A3 栏写 SIMD，表示当前公开 tuning 文档没有为它们承诺 SIMT 或 VF 变体，**不代表**所有其他开发路径都没有相关能力。目标架构未知时先取 `__NPU_ARCH__`/SoC 信息再选接口，不要用产品名称推断每个接口都支持。不支持的平台列在此仅用于排除，本卡的平台声明只覆盖 950/A3/A2。

## 验证方式

1. 按"接口能编译 → 语句确实执行 → 输出/周期数值符合预期 → 扩大到真实数据与多核 → 关闭或删除调试代码"逐级验证，每一步只增加一个变量。
2. 最小验证：先只保留两次 `clock()` 调用、把输出放到测量区之外，记录 `end - start` 与重复测量的分布；差值为零或波动时先核对计数精度、优化和调度，不以非零或稳定作为通路成立的必要条件，再加回真实代码与阶段打点。
3. `asc_time_stamp` 先用一个大于 `0xffff` 的 ID 做单点验证，确认有记录输出后再铺开到多阶段。
4. 结论落笔前去掉调试输出，在可比输入与构建配置下重建无输出干扰的测量基线，记录差异；不要求有无调试代码时的周期趋势一致。

## 失效边界

- 平台支持面以来源矩阵中"当前公开 tuning 文档"的声明为准，最终需要目标 CANN 版本的公开 API 文档、公开头文件和实际编译验证；目标版本与来源不一致时以目标版本文档为准。
- 本卡只覆盖 `clock` 与 `asc_time_stamp`。`asc_prof_start`/`asc_prof_stop`/`asc_mark_stamp`/`TRACE_START`/`TRACE_STOP` 属于 profiling 能力，不能由本卡来源推导它们的签名或行为，也不在本卡范围内。
- 周期数是相对量而非绝对时间：跨核、跨线程、跨次运行之间只比较差值与趋势，不做绝对时间换算。
- `printf`/`asc_dump` 落在测量区域内时会污染周期结果，这类数字不能当作被测代码的真实耗时；跨构建比较时还要保证测量区内的代码与编译配置可比。

## 与相邻卡的分工

- [clock（API 卡）](../../../../ops/ascendc/apis/utils_api/tuning_interface/clock.md) 与 [asc_time_stamp（API 卡）](../../../../ops/ascendc/apis/utils_api/tuning_interface/asc_time_stamp.md)：接口原型、返回值、头文件与参数约束等**接口事实归它们**；本卡只回答"怎么测、为什么数字不可信、没有输出怎么查"。
- [PRINTF 扰动时序：去 PRINTF 复验再定论](../../../../ops/ascendc/runbooks/runtime/printf_perturbs_timing_verify_without_printf.md)：那卡讲打印如何掩盖真实竞态、制造幽灵异常；本卡讲打印落在测量区内如何污染周期数，两者的证伪手段一致——去掉打印再复验。
- [Kernel printf 无输出诊断](../runtime/kernel_printf_no_output_diagnosis.md)：printf 无输出的五步定位；本卡第 5 节只处理 `asc_time_stamp` 无输出，printf 的输出链路问题走该卡。
- [PrintTimeStamp（API 卡）](../../../../ops/ascendc/apis/simd_api/basic_api/debug_interface/onboard_print/print_time_stamp.md)：另一个时间戳打点接口的事实卡，需要时按该卡使用，本卡不替它推导行为。
- [MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报](../../../../model/inference/optimizations/rules/mtp_decode_timing_two_metric_split.md)：推理侧的**计时口径拆分**（框架层，解决"一个数糊了两件事"）；本卡是 Kernel 内**单段测量的口径与可信度**，一个在框架层、一个在核内，互不替代，可组合使用。
- [昇腾性能测量失真陷阱：不代表真实访存的测量输入·折算前被截断的度量口径](../../../../model/inference/optimizations/anti_patterns/perf_measurement_distortion_input_and_metric.md)：讲测量输入与折算口径造成的系统性失真；本卡补充"测量区内部被调试输出污染"这一类。
