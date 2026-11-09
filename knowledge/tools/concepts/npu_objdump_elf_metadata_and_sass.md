---
type: Concept
title: npu-objdump 算子编译产物分析与 AI Core 指令反汇编
description: 用 npu-objdump（兼容命令 msobjdump）查看算子编译产物的 kernel 元数据（KERNEL_TYPE/TilingKey/CROSS_CORE_SYNC 等）、verbose ELF 信息、列出与提取内嵌 device ELF，并用 --sass 反汇编 AIC/AIV 指令；结合报错日志异常 PC 截取精确指令窗口定位出错指令。
tags: [task.debugging, topic.compilation, topic.implementation.debugging]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-objdump/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/npu-objdump-toolkit/references/metadata.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/npu-objdump-toolkit/references/fault-pc-disassembly.md
    role: supporting
created_at: "2026-11-05T01:20:00Z"
updated_at: "2026-11-05T01:20:00Z"
platforms: ["950", a2, a3]
aliases: [msobjdump, npu-objdump, dump-elf, sass]
---

# npu-objdump 算子编译产物分析与 AI Core 指令反汇编

npu-objdump（兼容命令 `msobjdump`，参数与行为一致）用于分析 Ascend C 算子编译产物：查看 kernel 元数据、列出/提取内嵌 device ELF、反汇编 device 侧 AI Core 指令。host 侧（x86/AArch64）普通 ELF 反汇编与性能采集使用 GNU/LLVM objdump，不在本工具范围。

## 命令契约

| 用户目标 | 调用方式 |
| --- | --- |
| kernel 名称、核类型、TilingKey 等元数据 | `msobjdump --dump-elf <input_file>` |
| ELF header、section、symbol 完整信息 | `msobjdump --dump-elf <input_file> --verbose` |
| 列出内嵌 device ELF | `msobjdump --list-elf <input_file>` |
| 提取 device ELF | `msobjdump --extract-elf <input_file> --out-dir <dir>` |
| 反汇编 device 侧 AI Core 指令 | `msobjdump --sass <input_file>` |

依赖按操作条件启用：`readelf`（ELF 读取）、`llvm-objcopy`（`.aicore_binary` 融合产物）、`ar`（静态库）、`llvm-objdump`（仅 `--sass`，须来自带 Ascend device 架构反汇编后端的 CANN 环境；系统 GNU objdump 缺少 Ascend 后端）。分析已有文件不需要 NPU 设备与驱动。

没有扩展名的可执行文件也可能含 device ELF，不能仅凭 `.o`/`.so`/`.a` 后缀判断支持；输入格式识别是线索而非扩展名白名单，无法识别时保留实际输出，不统一归因为文件损坏。

## 元数据字段判读要点

`.ascend.meta META INFO` 与 `.ascend.meta. [索引]: 名称` 输出按 kernel 归组，保留字段原名：

- `KERNEL_TYPE`：产物声明的 core 类型（AIC、AIV、MIX_AIC_MAIN、MIX_AIV_MAIN 等）；`mix_aic`/`mix_aiv` 两个符号可以是同一混合算子的两部分，不能当作两个独立算子；
- `FUNCTION_ENTRY`：工具文档定义为 TilingKey——保留完整整数，不与符号地址、入口地址或真实执行过的分支混淆；
- `CROSS_CORE_SYNC`：硬同步配置（USE_SYNC / NO_USE_SYNC）；适用平台需结合当前 CANN 文档；
- `MIX_TASK_RATION`：Cube/Vector 任务配比（如 `[1:2]`），不解读为耗时或利用率比例；
- `BLOCK_NUM`：当前源码打印固定占位值 `0xFFFFFFFF`，不能转换成实际核数；
- `DYNAMIC_PARAM`/`OPTIONAL_PARAM`：0/1 开关语义按版本定义解释；
- `DEBUG` 的 `debugOptions` 按版本位定义（0 关闭、1 DumpTensor/printf、2 assert、4 时间戳打点、8 内存越界检测），遇到其他值先核对当前版本，不能自行猜测；不能从 debugBufSize 判断本次运行已产生调试数据。

## --sass 反汇编与异常 PC 定位

`--sass` 调用所选 CANN 的 llvm-objdump 反汇编 device ELF，每行为「地址、十六进制编码、指令助记符与操作数」，按符号划分函数块（不等于 kernel 边界）；`file format` 行指明反汇编对象架构。`<not available>` 表示当前 llvm-objdump 没有该架构的反汇编后端，不是文件损坏。指令语义、调度与性能不能凭静态反汇编直接推断。

把运行时异常 PC 映射到具体指令的完整流程（OPP 对象筛选、MIX AIC/AIV 物理符号选择、窄指令窗口截取）见来源故障 PC 精确反汇编参考；CANN 9.2.0 安装中可能只有 `msobjdump` 且该版本没有 `--sass`，以接口自检探测结果为准。

## 失效边界

- 安装的 msobjdump 可能比文档记载更旧或更新；首次分析、切换 CANN 包或输出与文档冲突时先做接口自检（`skills/tool-npu-objdump/scripts/check_interface.py --json`），按 ok / newer-install / missing-options / unavailable 四态处理；
- `--dump-elf` 等元数据输出是结构信息而非指令反汇编；分析融合编译产物时详细信息可能来自提取后的 device ELF 而非外层 host ELF，解释架构和入口时须标明对象；
- 元数据表示编译产物配置（如 DETERMINISTIC_INFO），不代替运行测试。
