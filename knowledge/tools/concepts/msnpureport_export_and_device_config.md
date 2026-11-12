---
type: Concept
title: msnpureport Device 侧维测信息导出与配置命令
description: msnpureport（驱动内置，driver/tools 下）单次或常驻连续导出 Device 侧系统日志、黑匣子、stackcore、coretrace、Host 驱动内核日志等维测信息；config --get/--set 查询与设置日志级别、加速器自动复位、singlecommit（AI Core 内部多指令串行化控制，影响性能观测）、坏核屏蔽（aic_switch/aiv_switch）、icache 检验范围；仅 root 可执行，建议并发不超过 4 进程。
tags: [task.debugging, topic.implementation.debugging, topic.architecture]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msnpureport-toolkit/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msnpureport-toolkit/references/export-one-time.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msnpureport-toolkit/references/config-query.md
    role: constraint
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msnpureport-toolkit/references/config-set-log.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msnpureport-toolkit/references/output-layout.md
    role: supporting
created_at: "2026-11-05T02:40:00Z"
updated_at: "2026-11-10T02:00:00Z"
platforms: [a2, a3, "950"]
aliases: [msnpureport, 黑匣子, stackcore, slog, 坏核屏蔽]
---

# msnpureport Device 侧维测信息导出与配置命令

msnpureport 部署在驱动软件包中（驱动安装目录 `driver/tools/` 下，容器场景需配置 PATH 并加 `--docker`），用于导出与配置 Device 侧维测信息。导出内容存储在执行命令的当前目录（或 `-o` 指定路径）下以时间戳命名的文件夹中。

## 导出能力

**单次导出**：Device 侧系统类日志（Control CPU 内核态/用户态系统日志、非 Control CPU 的低功耗/Task Scheduler/ISP 日志）、黑匣子日志、Device 进程 coredump 调用栈（stackcore）、coretrace、Host 侧驱动内核日志等维测信息。

```sh
msnpureport report [options]     # 方式一（推荐）
msnpureport [options]            # 方式二
```

- **仅 root 用户可执行**，且须确保当前路径对普通用户无访问权限（防日志被恶意删除或泄露系统信息）；
- 支持多进程运行，**建议不超过 4 个**，不建议同路径同时刻并发（时间戳目录名冲突）；
- 容器场景仅支持导出 Host 侧驱动内核日志（特权容器除外）。

**常驻连续导出**：脚本方式连续导出，适合长时间监控；**工具自身维测日志**也可配置展示位置与级别；问题偶发难复现时用配置命令调大 Device 日志级别辅助捕获。

## 导出目录结构解读

```
├── hisi_logs/device-id/          # 设备异常信息
│   ├── <时间戳>/bin/vmcore       # vmcore，仅 Device OS 心跳丢失时产生
│   ├── ub/                       # Unified Bus 维测信息
│   └── history.log               # 各文件夹生成的异常场景信息
├── slog/dev-os-id/
│   ├── debug/{device-id, device-app-pid, device-os}/   # Device 侧调试日志
│   ├── run/                                            # Device 侧运行日志
│   └── ...
```

路径中的 `id`/`pid` 为 Device ID 与进程 ID，文件名中的 `*` 为创建时间戳；`device-app-pid.log` 仅在回传 Host 失败时生成。

## 维测配置查询与设置

```sh
msnpureport config --get [--device <id>]      # 一键查询当前 Device 维测配置
msnpureport config --set --log ...           # 设置 Device 侧系统日志级别
```

| 配置项 | 命令 | 用途 |
| --- | --- | --- |
| 日志级别 | `--set --log ...` | 问题偶发难复现时调大级别辅助捕获 |
| 加速器自动复位 | `--accelerator_recover` | 设置 TaskSchedule 是否自动复位加速器 |
| 指令串行化控制 | `--singlecommit` | AI Core **内部多条指令**的串行化/并行执行控制（不是多个任务或算子间的串行/并行保证）；开启串行化会改变指令调度、影响性能观测结果，仅诊断需要时使用，观测完毕记得还原 |
| 坏核屏蔽 | `--aic_switch` / `--aiv_switch --coreid <id>` | 屏蔽指定 AI Core/Vector Core 上的任务执行（怀疑坏核导致反复报错时可屏蔽验证） |
| icache 检验 | `--icachecheck` | 设置 icache bit 翻转检验范围 |

与导出命令不同，**查询命令不指定 `-d` 时默认只查 Device 0**，而非所有 Device；SMP 工作模式下指定一个 OS 内任意 Device ID 会导出该 OS 下所有 Device 日志。

## 失效边界

- 本卡为命令能力与目录结构的蒸馏；配置参数取值域以当前驱动版本 `msnpureport` 帮助输出为准；
- 黑匣子/stackcore/coretrace 文件的解析用 asys analyze（见[asys 工具卡](asys_command_routing_and_constraints.md)）；Device 日志级别语义的判读见诊断向导既有卡。
