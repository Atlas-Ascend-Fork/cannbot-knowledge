---
type: Runbook
title: Kernel 调试接口路由矩阵：症状 × 目标平台与编程模式
description: 把"症状 → 该用哪个 Kernel 调试接口 → 在目标平台/编程模式是否可用"做成一张可执行的路由表，覆盖 printf、assert/ascendc_assert、__trap、asc_dump、clock、asc_time_stamp，并给出"主要为 SIMD 不等于所有形式可用""API 支持不等于当前调用场景可运行"两条判定规则。
tags:
- task.debugging
- task.lookup
- topic.architecture
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/platform_matrix.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/SKILL.md
  role: supporting
created_at: '2026-10-23T01:36:00Z'
updated_at: '2026-10-23T01:36:00Z'
platforms:
- '950'
- a3
- a2
- '310p'
---

# Kernel 调试接口路由矩阵：症状 × 目标平台与编程模式

Kernel 侧调试接口（`printf`、`assert`/`ascendc_assert`、`__trap`、`asc_dump`、`clock`、`asc_time_stamp`）的可用性同时受**目标产品/编程模式**和**调用场景**两层约束。本卡只做**路由**：给定症状与目标平台，先决定选哪个接口、再判断它在当前平台和模式下是否可用。接口的签名、头文件、参数与容量细节归各自的 API 卡。

## 触发条件

- 想加调试输出/断言/打点，但不确定目标平台和编程模式下哪个接口可用；
- 某个调试接口"写了没用"，需要先排除"该形式在当前平台/模式下本就不被支持"；
- 目标产品与编译架构不明确，需要先确定取哪一组 API。

## 处置步骤

### 1. 先固定背景上下文

在选接口之前至少确认这六项，它们直接决定后续分支：SoC/产品与 `__NPU_ARCH__` 或编译架构；当前是 SIMD、SIMT、SIMT VF 还是 SIMD VF；跑在 CPU 调试还是 NPU 上板；走直接调用还是算子入图；CANN/AscendC 版本与相关编译选项；期望观察的是文本、张量内容、异常还是周期数据。

### 2. 按目标选接口

| 用户目标 | 首选接口 | 关键区别 |
| --- | --- | --- |
| 打印标量、索引、地址或字符串 | [printf](../../../../ops/ascendc/apis/utils_api/tuning_interface/printf.md) | 格式字符串 + 变参；需要控制线程数和数据量 |
| 检查不变量并让算子失败 | [assert / ascendc_assert](../../../../ops/ascendc/apis/utils_api/tuning_interface/assert.md) | 条件失败时输出并触发异常 |
| 条件满足时立即中断 SIMT | [__trap](../../../../ops/ascendc/apis/utils_api/tuning_interface/_trap.md) | 无参数、无返回值，只用于 SIMT 代码 |
| 查看 GM/UB/L1/L0C/寄存器数据 | [asc_dump 系列](../../../../ops/ascendc/apis/utils_api/tuning_interface/asc_dump.md) | 按地址空间选择重载，检查元素数和对齐 |
| 计算局部执行周期 | [clock](../../../../ops/ascendc/apis/utils_api/tuning_interface/clock.md) | 返回 `uint64_t`，通常取 `end - start` |
| 写出结构化时间戳记录 | [asc_time_stamp](../../../../ops/ascendc/apis/utils_api/tuning_interface/asc_time_stamp.md) | SIMD/NPU 调试，默认需显式编译开启 |

### 3. 查目标平台/编程模式的可用性

| 接口 | Ascend 950 | A3 | A2 | 310P/310B | 910/Kirin |
| --- | --- | --- | --- | --- | --- |
| `printf` | SIMD、SIMT、SIMT VF、SIMD VF | 主要为 SIMD | 主要为 SIMD | 当前 `printf` 文档不支持 | 不支持 |
| `assert`/`ascendc_assert` | SIMD、SIMT/VF 变体 | SIMD | SIMD | 310P SIMD 文档支持；310B 不支持 | 不支持 |
| `__trap` | SIMT/SIMT VF | 当前文档不支持 | 当前文档不支持 | 当前文档不支持 | 不支持 |
| `asc_dump` | SIMD，另有受限 VF/Buffer 变体 | SIMD | SIMD | 当前文档不支持 | 不支持 |
| `clock` | SIMD、SIMT | SIMD | SIMD | 当前文档不支持 | 不支持 |
| `asc_time_stamp` | SIMD、NPU 上板 | SIMD、NPU 上板 | SIMD、NPU 上板 | 当前文档不支持 | 不支持 |

使用这张矩阵时必须同时遵守四条规则：

1. **"主要为 SIMD"不等于所有形式可用。** 它表示当前公开 tuning 文档没有为 A2/A3 承诺 SIMT 或 VF 变体，**不代表**所有其他开发路径都没有相关能力。反过来也不能由"产品支持这个接口"推断它的每种编程模式形式都能用。
2. **目标架构未知时先取 `__NPU_ARCH__`/SoC 信息，再选 API**，不要用产品名称推断每个接口都支持。
3. **`__trap` 以目标版本公开文档为准。** 最新公开文档只列出 Ascend 950PR&950DT 系列产品；即使头文件里存在其他条件编译分支，也不能据此认为在其他平台可用。
4. **SIMD VF 的 reserved UBUF、FIFO 和编译选项限制要单独检查**，不能套用普通 SIMD 的容量结论。

### 4. 再判"API 支持"是否等于"当前调用场景可运行"

平台矩阵只回答"这个接口在该产品上被不被支持"，不回答"你这次的调用能不能跑出来"。落到具体问题还要检查：跑在 CPU 调试还是 NPU 上板、是直接调用还是算子入图、编译模式与编译选项、以及 CANN/AscendC 版本。任一维度不满足，表现都会是"接口支持但就是没输出/不生效"。

### 5. 按症状继续收敛

| 症状 | 先检查 | 继续动作 |
| --- | --- | --- |
| `printf` 完全没有输出 | 平台/模式、头文件、`ASCENDC_DUMP`、线程条件 | 走 [Kernel printf 无输出诊断](kernel_printf_no_output_diagnosis.md) 的五类原因排查及短字符串复验 |
| 输出不全 | SIMD/SIMT FIFO、每核上限、单条记录大小、打印线程数 | 减小输出量，或按文档调大对应配置 |
| 断言没有失败 | 条件是否为真、`NDEBUG`、`ASCENDC_DUMP=0` | 用确定失败的最小用例验证开关与模式；细分走 [assert 与 Trap 失败诊断](kernel_assert_and_trap_failure_diagnosis.md) |
| 断言失败但没有自定义消息 | CPU/VF 模式限制、FIFO、单条消息大小 | 保留标准断言上下文，缩短自定义消息；细分同 [assert 与 Trap 失败诊断](kernel_assert_and_trap_failure_diagnosis.md) |
| `asc_dump` 数据不可信 | 地址空间重载、模板类型 `T`、`dump_size`、32B 补齐 | 先用小范围且已知长度的数据验证；细分走 [asc_dump 数据不可信诊断](kernel_asc_dump_data_untrusted_diagnosis.md) |
| `asc_time_stamp` 没有输出 | `ASCENDC_TIME_STAMP_ON`、NPU 上板、算子入图限制 | 重新编译并检查每核累计 dump 量 |
| Kernel 失败或中断 | 先区分 assert 与 `__trap` | 保留 plog 与返回码；诊断走 [assert 与 Trap 失败诊断](kernel_assert_and_trap_failure_diagnosis.md)，运行时/崩溃问题继续外转 |

### 6. 记住四条口径

- `assert` 与 `ascendc_assert` 提供相同的 AscendC 断言能力；`__trap` 不是通用 SIMD 异常 API，要先判断条件、再在 SIMT 代码中调用。
- `clock` 只返回数值、不自动产生结构化 dump；`asc_time_stamp` 由编译开关控制并输出时间戳记录。
- `ASCENDC_DUMP=0` 会关闭依赖 Dump 的调试输出；`NDEBUG` 会使断言不生效；`asc_dump` 的 `dump_size` 不得超过实际元素数，非 32 字节对齐时还要算上系统补齐带来的容量消耗。
- 调试接口会改变性能，带大量 `printf`/`asc_dump` 的测量结果不能代表原始 Kernel 性能。

## 验证方式

1. 先给最小补丁：只补正确头文件、调用和必要的编译/运行配置，保持算子计算逻辑不变。
2. 再按所选接口检查输出链路：先确认平台/模式与执行路径；`printf`/`asc_dump` 检查 `ASCENDC_DUMP` 和各自容量，断言另查 `NDEBUG` 与标准上下文，`asc_time_stamp` 另查 `ASCENDC_TIME_STAMP_ON` 与上板/入图限制。只调整命中的环节，不把这些开关当作所有接口的共同条件。
3. 确认日志、dump 数据或异常符合预期后，移除调试调用或关闭调试开关，避免性能与产物污染。
4. 平台或版本不明确时，先查当前版本的公开 API 文档、公开头文件和示例，不凭旧经验下结论。

## 失效边界

- 本矩阵来自固定 commit 的 asc-devkit 内部参考资料，用于**初步路由**，不替代目标 CANN 版本的 API 文档、公开头文件和实际编译验证；版本或平台不明确时先查当前 API 文档、头文件和示例，不凭旧经验下结论。
- 本卡只覆盖上表六个接口的**路由**。`DumpTensor`、`DumpAccChkPoint`、`PrintTimeStamp` 仅作为相邻能力，不走本卡的路由结论。
- `asc_prof_start`、`asc_prof_stop`、`asc_mark_stamp`、`TRACE_START`、`TRACE_STOP` 不在范围内，需要采集/时间线能力时按 [asc_prof_start（API 卡）](../../../../ops/ascendc/apis/utils_api/tuning_interface/asc_prof_start.md) 一类的 profiling 能力处理。
- 不把未提交的 Super Tensor/FIFO 内部协议、`ASCENDC_DUMP_SUPER_TENSOR` 或 type 11/12 当作公开调用契约。
- 不支持平台列在矩阵中仅用于排除；本卡的平台声明只覆盖 950/A3/A2/310P。

## 与相邻卡的分工

- [printf（API 卡）](../../../../ops/ascendc/apis/utils_api/tuning_interface/printf.md) 与同目录的 `assert`、`__trap`、`asc_dump`、`clock`、`asc_time_stamp` 卡：**接口事实归它们**（头文件、原型、参数、FIFO/容量、开关语义）。本卡只回答"遇到这个症状该找哪个接口、它在目标平台与模式下可不可以用"。
- [Kernel printf 无输出诊断](kernel_printf_no_output_diagnosis.md)：printf 单个接口的五类原因排查与最小复验；本卡是跨接口的路由入口，只有命中"printf 完全没有输出"时才把细节交给它。
- [Kernel 侧 assert 与 \_\_trap 选型及失败诊断](kernel_assert_and_trap_failure_diagnosis.md) 与 [asc_dump 数据不可信诊断](kernel_asc_dump_data_untrusted_diagnosis.md)：分别是断言/Trap、`asc_dump` 两个症状的单接口深度排查；本卡只负责把它们路由进正确的候选集，不重复其判定步骤。
- [PRINTF 扰动时序：去 PRINTF 复验再定论](../../../../ops/ascendc/runbooks/runtime/printf_perturbs_timing_verify_without_printf.md)：打印本身改变时序的证伪方法，作为本卡"调试接口会改变性能"这条口径的展开。
- [Kernel 周期与时间戳测量：clock 与 asc_time_stamp](../performance/kernel_clock_and_time_stamp_measurement.md)：`clock`/`asc_time_stamp` 的测量口径与无输出排查细节；本卡只负责把它们路由进正确的候选集。
- [assert（AI CPU API）：固定 reference 调用约束](../../../../ops/ascendc/guides/diagnostics/aicpu_assert_reference_contract.md)：AI CPU 侧的断言调用约束，**不在本卡范围**；本卡的 `assert` 路由只针对 AscendC Kernel 侧调试接口。
