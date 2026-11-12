---
type: Concept
title: GE 图编译执行进程崩溃的归属判定与 coredump 诊断入口
description: "判定 coredump 是否归 GE（libge_common/libge_compiler/libge_runner/libge_executor/libgert/libgraph*/tf_adapter 或 ge::/domi:: 帧）：从栈顶向下只忽略 libc/libstdc++/libpthread 等标准库帧，最近的非标准库帧属于 GE 才纳入；coredump 诊断以崩溃现场和匹配的二进制/源码为主，日志只作辅助，归属不明标记 undetermined 并指路。"
tags: [task.debugging, topic.compilation, topic.graph_execution]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/graph/ge-coredump-diagnose/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/graph/ge-coredump-diagnose/references/gdb_collection.md
    role: supporting
created_at: "2026-11-05T02:10:00Z"
updated_at: "2026-11-05T02:10:00Z"
platforms: [a2, a3, "950"]
aliases: [GE coredump, libge, backtrace 归属, gdb]
---

# GE 图编译执行进程崩溃的归属判定与 coredump 诊断入口

GE（Graph Engine，含 ge / metadef / tf_adapter 库）图编译/图执行相关进程崩溃时，先判定崩溃归属，再进入 GE 源码定位。

## 归属判定（先于一切诊断）

**coredump 纳入标准**（满足任一即进入 GE 诊断）：

1. 崩溃线程栈顶帧属于 GE 库（libge_common、libge_compiler、libge_runner、libge_executor、libgert、libgraph*、libparser*、tf_adapter）；
2. 从栈顶向下**只忽略标准库帧**（libc、libstdc++、libpthread、libm、libdl、动态加载器等）后，最近的非标准库帧属于 GE 库。

判断时从 frame #0 向下逐帧扫描，只跳过标准库；**不能越过其他业务库继续寻找更下方的 GE 帧**。满足条件后，backtrace 同时出现 runtime、驱动、算子实现或用户代码帧也不排除——这些帧只作上下文，默认不展开其源码。

库归属以 backtrace 或 `info sharedlibrary` 中的 `.so` 名称/路径为准；只有函数名相似而无法确认库归属时标记 `undetermined`，不武断判定 GE 或非 GE。

**判定不纳入时必须指路**：最近非标准库帧属于 runtime（libruntime/librts/libascendcl）→ runtime 侧诊断；属于 AscendC 算子 kernel → 算子崩溃诊断；属于驱动/HCCL/用户应用代码 → 判定责任边界并说明对应处理渠道；归属不明 → 提示补充 backtrace 后重新判断。

## 诊断纪律

- **以崩溃现场和匹配的二进制/源码为主，日志只作辅助**：需要采集崩溃现场时按 gdb 采集清单执行（core 文件、匹配版本的带符号二进制、`bt full`、`info sharedlibrary`、`info registers` 等）；
- 证据不足时降低结论级别，不把候选原因写成确定根因；不确定时先搜 GE 责任田；
- 涉及源码位置与调用链的报告遵守统一源码引用格式（仓库/文件/行号）。

## 失效边界

- GE 库源码位置在诊断会话内确认，不预设固定路径；
- 栈顶与最近非标准库帧都无法确认归属时保持 `undetermined`；
- 图模式不崩溃但报错/断图/精度差异的问题走 npugraph_ex 分诊流程（见[npugraph_ex 五步分层卡](npugraph_ex_dfx_five_step_triage.md)），不在本入口范围。
