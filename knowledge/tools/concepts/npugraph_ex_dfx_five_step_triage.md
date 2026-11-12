---
type: Concept
title: npugraph_ex 图模式问题的五步分层采集与分诊路由
description: npugraph_ex（aclgraph）DFX 问题统一分诊入口：按 eager→compile eager→aot_eager→npugraph_ex force_eager→npugraph_ex 五步顺序执行，每步只跑当前形态并记录合并日志与 plog，遇到第一个失败的 step 立即停止——失败 step 即问题所在层；按首败层路由到编译错误/运行时错误/精度/性能四个专科。
tags: [task.debugging, topic.graph_execution, topic.implementation.debugging]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/graph/torch-npugraph-ex-dfx-triage/SKILL.md
    role: primary
created_at: "2026-11-05T02:10:00Z"
updated_at: "2026-11-05T02:10:00Z"
platforms: [a2, a3, "950"]
aliases: [npugraph_ex, aclgraph, DFX 分诊, force_eager, TORCH_COMPILE_DEBUG]
---

# npugraph_ex 图模式问题的五步分层采集与分诊路由

npugraph_ex（aclgraph）模式的问题（报错、断图、精度差异、性能回退）不要直接拿一份报错猜根因，先做五步分层采集：从最简形态到完整图模式逐层验证，**遇到第一个失败的 step 立即停止**，失败 step 的日志即为分诊主证据——哪一步首次失败，问题就出现在那一层。

## 五步分层与日志开关

| step | 形式 | 调试日志开关 |
| --- | --- | --- |
| 1 | 不带 `torch.compile`，纯 eager | `TORCH_LOGS="+all"` |
| 2 | `torch.compile(backend="eager")` | `TORCH_LOGS="+all"` |
| 3 | `torch.compile(backend="aot_eager")` | `TORCH_LOGS="+all"` |
| 4 | `torch.compile(backend="npugraph_ex", options={"force_eager": True})` | `TORCH_COMPILE_DEBUG=1` + `TORCH_COMPILE_DEBUG_DIR` |
| 5 | `torch.compile(backend="npugraph_ex")` | `TORCH_COMPILE_DEBUG=1` + `TORCH_COMPILE_DEBUG_DIR` |

step 1-3 的 `TORCH_LOGS` 输出进 stderr，被合并打屏文件捕获；step 4-5 是 npugraph_ex 自家链路，`TORCH_COMPILE_DEBUG=1` 把 FX/AOT graph 等结构化产物落到 `torch_compile_debug/` 目录。

**首败层 → 专科路由**：step 1-2 失败（eager/编译前端）转编译错误诊断；step 4-5 失败且为运行时报错转运行时诊断；step 5 通过但结果不一致转精度诊断；step 5 通过但性能不达预期转性能诊断。

## 采集纪律

- **目录结构**：所有产物落统一根目录，下一层子目录带时间戳 + shell PID 避免多次分诊互相覆盖；每个 step 目录保留 `stdout_stderr.log`（合并打屏）与 `ascend_plog/`（`ASCEND_PROCESS_LOG_PATH` 直接落盘），step 4-5 另有 `torch_compile_debug/`；
- **失败标记**：失败时在根目录写 `first_failure.txt`（首个失败 step + exit code），成功 step 落 `SUCCESS` 标记——不要只靠目录是否存在反推首个失败 step；任一 step 缺日志产物视为信息不全，必须补跑；
- **最小化改造**：基于用户现有复现脚本做最小化修改生成各 step 副本——只改复现路径上的 `torch.compile(...)` 调用及其紧邻赋值，不改模型定义、输入构造、数据路径、随机种子、训练循环；多个 `torch.compile` 调用时只改与当前复现路径直接相关的那一个；封装在 helper 里的优先在 helper 内改；
- **compile 参数继承**：step1 去掉外层 `torch.compile(...)` 直接运行其第一个位置参数，其余业务逻辑不变；后续 step 逐步收紧 backend。

## 失效边界

- 信息不足（缺最小复现、版本、shape、日志）时先补齐再判断，不给根因结论；
- 分诊只完成「采集 + 分类」；各专科（编译错误/运行时错误/精度/性能）的深入诊断由对应专科知识承接；
- GE 图编译/图执行进程崩溃（backtrace 出现 libge_* / ge:: 帧）不在本流程内，走 GE coredump 诊断。
