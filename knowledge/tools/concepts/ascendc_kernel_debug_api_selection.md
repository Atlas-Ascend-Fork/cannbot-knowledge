---
type: Concept
title: AscendC 核函数调试接口的选型与调用约束（printf/assert/__trap/asc_dump/clock/时间戳）
description: AscendC Kernel 侧调测接口按观测目标选型：printf 格式化输出标量、assert/ascendc_assert 条件断言（NDEBUG 与 ASCENDC_DUMP=0 会关闭）、__trap 显式中断（SIMT）、asc_dump 按地址空间转储（dump_size 单位是元素、32 字节补齐、单核输出约 30KB 上限）、clock 周期计数、asc_time_stamp 结构化时间戳；接口支持取决于 CANN 版本、SoC 与编程模式，以目标版本 asc-devkit 文档与公开头文件为准。
tags: [task.debugging, topic.implementation.debugging, topic.precision]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/tools-npu-debug-api/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/tools-npu-debug-api/references/debug_api_quickref.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/tools-npu-debug-api/references/asc_dump.md
    role: constraint
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/tools-npu-debug-api/references/assert_and_trap.md
    role: supporting
created_at: "2026-11-05T02:40:00Z"
updated_at: "2026-11-05T02:40:00Z"
platforms: [a2, a3, "950"]
aliases: [asc_dump, AscendC printf, ascendc_assert, __trap, asc_time_stamp, clock]
---

# AscendC 核函数调试接口的选型与调用约束（printf/assert/__trap/asc_dump/clock/时间戳）

Ascend C Kernel 侧调试接口的选型、调用与配置：用于精度偏差观察（中间张量）、执行路径确认（标量/分支）、异常条件暴露（断言/中断）与时间观测。

## 选型速查

| 观测目标 | 接口 | 主要功能与限制 |
| --- | --- | --- |
| 确认分支是否执行、查看少量标量 | `printf` / `AscendC::printf` | 输出格式化文本；不自动遍历张量或校验结果 |
| 错误状态立即可见并中止 | `assert` / `ascendc_assert` | `NDEBUG` 使断言失效；`ASCENDC_DUMP=0` 关闭依赖 Dump 的输出 |
| SIMT 线程不可恢复状态时中断核函数 | `__trap`（条件判断 + 调用） | 不是通用 SIMD 异常接口，平台需核对 |
| 查看中间张量/片上缓冲区内容 | `asc_dump_*` / `asc_dump` | 按地址空间选择；不推断内存长度、不比较参考结果 |
| 返回值参与计算或写回 GM | `clock` | 返回 `uint64_t` 周期计数；不自动计算耗时 |
| 统一可解析的 SIMD 时间点 | `asc_time_stamp` | 结构化时间戳（带 `desc_id`）；不自动配对或计算区间 |

不要把 `printf` 后继续执行当作错误处理；不能依赖可被关闭的断言防止越界。

## asc_dump 调用约束（高频陷阱）

- `dump_size` 单位是**元素**不是字节；超出实际元素数产生未定义行为——先确认地址与长度；
- 地址空间必须匹配：GM 用 `asc_dump_gm`（`__gm__` 指针）、UB 用 `asc_dump_ubuf`（`__ubuf__`）、L1 用 `asc_dump_l1buf`（`__cbuf__`）、L0C 用 `asc_dump_cbuf`（`__cc__`）；不能靠强制类型转换伪装地址空间；950 上另有 BiasTable/Fixpipe 变体与 SIMD VF 寄存器变体 `asc_dump_reg`（Fixpipe 保存的可能是硬件参数位域，输出不一定等于上游原始数据）；
- 非 32 字节对齐的 dump 末尾 padding 占容量；SIMD 场景单核调试输出默认约 30 KB，超限可能没有输出；
- SIMD VF 中 `asc_dump`、`printf` 与断言共享预留 UB 空间，单条记录过大或关闭预留空间时接口可能不可用；
- `ASCENDC_DUMP=0` 关闭 dump；调试接口不应保留在生产性能路径；
- 多核同时 dump 时用 `desc` 区分阶段、过滤线程/Block，避免输出不可读或超限。

## 观测有效性纪律

- 插桩只添加观测所需的调试代码，保持算法、tiling 与同步逻辑不变；控制核、线程与输出量；
- dump 不证明被观测数据已由生产者写完——调用者仍需满足原有同步与生命周期要求；
- dump 前确认指针有效性、实际元素数与线程索引范围；`dump_size` 不得超过实际元素数，不得用于试探未知内存长度；
- 时间观测注意线程局部性、同步、冷启动与调试扰动；`asc_time_stamp` 需 `-DASCENDC_TIME_STAMP_ON` 且有 1 MB/核上限、入图受限。

## 失效边界

- 接口支持取决于 CANN/devkit 版本、SoC/编译架构、SIMD/SIMT/VF 模式与执行方式（CPU/仿真/NPU、直调/入图）——声明、重载与参数范围以目标版本 `asc-devkit/docs/zh/api/Utils-API/tuning_interface/` 与公开头文件为准；编译通过不等于运行支持；
- 配置模板是片段，不能覆盖现有 `acl.json` 其他字段；
- 调试输出的解析工具用法与插桩扰动控制，见[Ascend C 诊断向导](../../ops/ascendc/guides/diagnostics/index.md)（插桩与观测边界既有卡）。
