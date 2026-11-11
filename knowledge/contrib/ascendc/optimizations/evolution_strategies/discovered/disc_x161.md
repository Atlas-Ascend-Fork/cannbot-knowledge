---
type: Optimization
title: "X161: 跨 launch L0B 竞态的识别与评测方法"
description: "MIX kernel 在同一进程内多次 launch 时可能间歇报 L0B read/write conflict（507015），而单次 accuracy 口径通过；同一二进制也可能间歇静默污染。单跑精度 PASS 不能证明无竞态。退出排空与简单事件 id 拆分可能无效；评测侧可用自适应二分定位失败 chunk，并对可疑 case 做重复 launch 探针。"
tags:
  - task.debugging
  - topic.precision
  - topic.attention
status: draft
sources: []
created_at: "2026-10-29T03:50:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X161: 跨 launch L0B 竞态的识别与评测方法

## 核心结论
1. **症状分层**：同一内核、同一设备，**单 launch 准**（accuracy 口径）而**多 launch 批**（同一进程内多次 launch）间歇整块崩溃；报错固定为 `L0B read/write conflict in the MTE (same address)`（507015），落在某个 chunk 的某个 case 上，与 chunk 大小无关（二分到 chunk=1 仍可能复现）。
2. **静默污染**：同一二进制在某些 case 上可能约一半 launch 给出大量 op_bound violations（max_abs 明显超出容差），而一分钟前同一 case 却 PASS。⇒ **单次全量精度通过不能证明内核无竞态**；必须用"同一 case 重复多次"的 corruption/crash-rate 探针做门禁。
3. **常见但无效的修法**：
   - kernel 退出补 `MTE2_MTE1`、`M_MTE1`、`MTE1_MTE2`、`M_FIX`、`PIPE_ALL` 全排空；
   - 把与 L0B ping-pong 信用共用 id 的 `FIX_M`/`M_FIX`/`MTE1_MTE2` 拆到新 id。
   两者都可能无改善。竞态不一定在"块退休排空"，也不一定是简单的事件 id 撞车；下一步应证明某组 id 在某一时刻确实空闲，再拆 ping-pong 信用（静态 grep 看到的 id 占用可能少于实际路径）。

## 适用场景
- 任何"MIX_AIC 内核 + 同一进程多次 launch"的 quick-batch 评测；出现 507015/EE9999 且单跑正常时，先判定是否 pre-existing（用未改动种子二进制复现），再决定是否继续评测。
- 交付门禁：不能只跑一次 accuracy；至少对最可疑的 1–2 个 case 做重复 launch 探针。

## 测量侧工程手段：自适应二分
- 把固定 chunk 循环换成**自适应二分**：先按较大的 chunk 跑；失败的 chunk 对半拆（如 10→5→2→1），单 case 仍失败则如实记 `failed_case`。
- 每 case 的数值仍取 `task_time.csv` 的 Task_Duration 之和 / repeats；时间口径保持不变。
- 代价：干净的套件耗时明显上升；带崩溃的窗口可能翻数倍。跨窗口 geomean 漂移可达数个百分比，**只认同窗口同设备 paired 比值**。

## 实现要点
1. 复现优先：先用未改动的种子二进制在同一进程内重复 launch，确认竞态是否 pre-existing；不要一上来就改内核。
2. 记录失败 chunk 的边界与 case 编号，二分时保持 launch 次数/repeats 不变。
3. 静默污染比崩溃更危险：崩溃至少会报错，静默污染会以"偶发精度失败"的形式混入性能数据。对每个可疑 case 做多次重复 launch 并记录 corruption rate。
4. 修复方向：先证明事件 id 的完整占用集合（含运行时分支实际使用的 id），再拆 ping-pong 信用；不要只做退出排空。

## 验证方法
- 同一 case 重复 launch（多次），统计 crash/corruption rate。
- 对失败 chunk 做自适应二分，确认最小复现单元。
- 修复后重新跑重复 launch 探针 + 全量精度；单跑 PASS 不作为结论。

## 关联
- 与 [X171](disc_x171.md)（完成标志/残留 UB 陷阱）同属"单次测试看不见的静默错误"。
- 与 [X162](disc_x162.md)（天花板审计）配合：先确认竞态，再谈性能上限。
