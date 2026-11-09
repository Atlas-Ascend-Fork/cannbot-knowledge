---
type: Concept
title: npu-check 运行时正确性检查工具的使用与结论边界
description: 通过 npu-check 启动应用以执行 memcheck（数据搬运指令 GM 访问越界/释放后访问）与 synccheck（SET_FLAG/WAIT_FLAG、GET_BUF/RLS_BUF 配对）检查；覆盖 GM 越界判定以 aclrtMalloc 成功分配为基准、检测数据在流同步时导出等关键边界。当前已验证配置仅 Ascend 950。
tags: [task.debugging, topic.implementation.debugging, topic.memory]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-check/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-check/references/check-capabilities.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-check/references/capability-boundaries.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-check/references/execution.md
    role: supporting
created_at: "2026-11-05T01:20:00Z"
updated_at: "2026-11-05T01:20:00Z"
platforms: ["950"]
aliases: [memcheck, synccheck, npu check]
---

# npu-check 运行时正确性检查工具的使用与结论边界

npu-check 是面向 Ascend C 算子开发场景的 NPU 运行时正确性检查工具：通过它启动目标应用，在应用运行过程中检查数据搬运指令对设备全局内存（GM）的访问与核内同步操作的配对。本卡说明命令契约、检查能力与结论边界；报告字段判读的 Ascend C 实战经验另见[诊断向导](../../ops/ascendc/guides/diagnostics/index.md)。

## 工具定位与适用场景

典型场景：怀疑算子实现存在越界访问或同步错误；新写或修改算子后做正确性验证；结果偶发错误想排查算子问题。

```bash
npu-check --tool memcheck --tool synccheck -- ./my_app <args>
```

两种检查能力可同一次命令启用：

| 命令行选项 | 启用的检查能力 |
| --- | --- |
| `--tool memcheck` | 检查数据搬运指令产生的 GM 访问 |
| `--tool synccheck` | 检查 `SET_FLAG/WAIT_FLAG`、`GET_BUF/RLS_BUF` 配对 |
| 未提供任何 `--tool` | 默认启用 memcheck |

## 已验证运行配置与限制

以下为来源声明的已验证配置，超出时应将对应能力标记为不支持或未知，不把运行结果解释为有效检查结论：

- 目标设备为 Ascend 950（芯片架构 `dav-3510`），使用与目标 NPU 和驱动匹配、且包含 npu-check 的 CANN 包；
- 目标程序为可执行文件，脱离 npu-check 后也能成功执行核函数；
- 应用通过 `<<<>>>` 核函数直调语法调用算子，一次运行只下发一次；单进程、单线程运行；
- 应用在核函数下发后调用 `aclrtSynchronizeStream` 或 `aclrtSynchronizeStreamWithTimeout`（检测数据在流同步时导出并处理，应用不调用任一接口时不能依据没有诊断判断检查通过）；
- PyTorch 场景暂不支持。

## memcheck 能力与判定基准

memcheck 仅检查数据搬运指令对 GM 的访问，不支持标量直接访问检测。报告可提供：`read`/`write` 访问方向及字节数、源码文件和行号或核函数名与指令地址（PC）、执行核类型（AIC/AIV）与核编号、任务块、搬运流水、下发批次、异常地址，以及 NPU 侧调用栈（报告原文为 `Device Frames`）。

GM 越界判定基准（不是张量逻辑形状）：

1. 工具根据 `aclrtMalloc`、`aclrtFree` 的成功返回结果记录有效 NPU 内存分配范围；检查边界使用 `aclrtMalloc` 请求大小向上按 32 字节对齐后的值；
2. 访问范围必须完整落入一个当前有效的分配范围，否则可能形成越界、释放后访问或未知地址诊断；
3. CPU 侧为 NPU 申请了额外预留空间（padding、内存池）时，访问超出逻辑数据范围但仍在同一有效分配范围内，不一定会被报告——报告 `size N bytes` 是完整访问长度，不是越界字节数。

## synccheck 能力与判定基准

synccheck 检查核内 `SET_FLAG -> WAIT_FLAG`、`GET_BUF -> RLS_BUF` 的实际执行记录，按指令参数（src/dst pipe、event ID、buffer ID）和实际执行次数判断配对；未实际执行的控制流不在本次结论范围内。报告汇总字段：

- `duplicate_opens`：同一组配对参数的 SET_FLAG/GET_BUF 未被消费就再次执行；
- `unmatched_closes`：执行了 WAIT_FLAG/RLS_BUF 但没有相同配对参数的前置操作；
- `unconsumed_opens`：应用执行流同步时前置操作仍未被消费。

判断匹配应读取配对参数，不是只比较操作名称。

## 执行与结果判定纪律

- 保留应用原有的工作目录、环境、NPU 设备选择与参数；复用项目已有的 CANN 环境加载命令；
- 原始捕获日志可能同时包含检查报告与应用自身输出，不是独立报告文件；`--log-file <path>` 指定后检查报告只写入该文件，终端仍显示应用输出并重复写入该文件——不得重新拼接两路输出；
- 应用被外部超时或信号终止而未正常退出时，工具可能收不到完整报告，本次检查判定为未完成；
- 「本次未发现明确问题」不能证明未执行的分支、未启用的检查类型、数值精度、性能或 CPU 侧逻辑没有问题。

## 失效边界

- 来源为技能文档蒸馏，命令与字段以当前安装的 npu-check `--help` 输出为权威；
- 官方资料未明确说明的检查对象，统一标记为「覆盖范围未知」；
- 本卡未在本地执行工具验证；Ascend C 场景的 memcheck 报告判读实战经验见[诊断向导索引](../../ops/ascendc/guides/diagnostics/index.md)。
