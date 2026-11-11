---
type: Guide
title: "Host Runtime 专题：Event 零超时语义、MemcpyAsync 返回边界与资源生命周期"
description: 三个高频 Host Runtime 专题的实测边界：① Event（ExWithFlag 创建的 Event 完成后 timeout=0 仍返回 107000 不代表任务未完成；首次 record 前可报 COMPLETE；计时+跨流等待需 TIME_LINE|SYNC 组合；复用错轮读到旧数据时先查 wait 是否成功再查 record 对应哪轮生产）② MemcpyAsync 返回边界按 Host 内存分配族二分（锁页=提交即返回须等流；非锁页=复制完成才返回；分配不明先查族）③ 资源生命周期（部分初始化失败只清理已取得所有权的对象；临时 Context 切换后须恢复调用者）。
tags: [task.debugging, topic.implementation.resource_lifecycle, topic.implementation.synchronization, topic.memory]
status: stable
sources:
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/749c3c88283397b28472e91c36a402e598121622/skills/tool-runtime-debug/references/event-timeout-zero.md
    role: primary
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/749c3c88283397b28472e91c36a402e598121622/skills/tool-runtime-debug/references/memcpy-async-host-memory.md
    role: primary
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/749c3c88283397b28472e91c36a402e598121622/skills/tool-runtime-debug/references/resource-lifecycle.md
    role: primary
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/749c3c88283397b28472e91c36a402e598121622/skills/tool-runtime-debug/references/output-and-ownership.md
    role: supporting
created_at: "2026-11-05T05:50:00Z"
updated_at: "2026-11-10T03:25:00Z"
platforms: [a2, "950"]
aliases: ["107000", aclrtSynchronizeEventWithTimeout, aclrtCreateEventExWithFlag, aclrtMemcpyAsync, 锁页内存, "107002"]
---

# Host Runtime 专题：Event 零超时语义、MemcpyAsync 返回边界与资源生命周期

排查流程与错误码分流见[证据纪律卡](evidence_discipline_and_error_routing.md)；本卡保存三个专题的实测边界与判定方法。实测标注均为 910B1/CANN 9.0.0 的有限记录，不外推其他版本、芯片或全部创建方式。

## Event：零超时、创建方式与复用错轮

**零超时与目标运行库**：目标安装头文件把 timeout=0 注释为「立即检查」，但官方页面只定义 -1 为永久等待、正数为毫秒。910B1/CANN 9.0.0 实测：同一 Event **已完成后传入 0 仍返回 107000**——不能据此判断任务未完成，也不能只凭头文件注释认定运行库支持零超时。必须在截止时间内取得结果时使用已确认的正超时并检查实际返回值。

**创建方式决定可用操作**：`aclrtCreateEventExWithFlag` 创建的 Event 不能使用 `aclrtQueryEvent` / `aclrtQueryEventWaitStatus` / `aclrtResetEvent`——记录状态查询用 `aclrtQueryEventStatus`（检查返回值 + `aclrtEventRecordedStatus` 具名常量）。该接口的 Event 在**首次 record 前可报告 COMPLETE**（尚无捕获任务，不证明计划提交的工作已完成）；重复 record 会覆盖捕获的任务集，但已提交的 StreamWaitEvent 仍等待它提交时选中的任务集——复用语义限定 ExWithFlag，不能套用到 `aclrtCreateEvent` / `CreateEventWithFlag`。

**计时 + 跨流等待的组合**：同时需要计时和 StreamWaitEvent 时保留 `ACL_EVENT_TIME_LINE` 按位或 `ACL_EVENT_SYNC`（9.0 头文件 TIME_LINE=8、SYNC=1，组合值 9，用具名常量）；仅传 TIME_LINE 不能用于 StreamWaitEvent，直接替换成 SYNC 又删掉计时需求。计时还需 record 起止 Event、同步其生产 Stream 再查 `aclrtEventGetTimestamp` / `aclrtEventElapsedTime`——**等待成功不证明计时有效**（实测：仅等待消费 Stream 时数据正确但耗时查询返回 107006；查询前等待结束 Event 或生产 Stream 后取得有效耗时）。

**复用错轮读到旧数据的成对检查**：先查 wait 是否成功，再查它等待的 record 是否位于本轮生产之后——两个条件分别成立才可消费本轮结果；只有 TIME_LINE 时 wait 返回非零、增加 SYNC 后 wait 成功但数据仍旧，说明创建用途与生产顺序是两个需分别检查的条件；后补同步不会重新执行已经结束的复制；本轮生产完成后重新复制得到正确数据只证明设备结果正确，不证明原流程正确。不能用 sleep、设备复位或忽略返回值替代同步关系。

## MemcpyAsync：Host 分配方式决定返回边界

CANN 9.0 `aclrtMemcpyAsync` 成功返回的含义按 Host 内存分配族二分：

| Host 内存 | 成功返回的含义 | 消费数据前 |
| --- | --- | --- |
| `aclrtMallocHost` 等锁页内存 | 任务已提交，尚不能证明复制完成 | 等待执行复制的 Stream 完成再读取或释放 |
| `malloc` 等非锁页内存 | **此复制任务完成后才返回** | 检查返回值、完整输出和本轮生产关系；仅凭 Async 名称不能认定仍未完成 |
| 分配来源不明 | 缺少判定依据 | 先查分配族，不同时套用前两种语义 |

跨 Stream 生产与复制的顺序：先提交本轮生产 → 生产 Stream record 支持 `ACL_EVENT_SYNC` 的 Event → 复制 Stream 先 wait 再复制，各步检查实际返回值。EP 形态下该接口不支持 Host 到 Host 异步复制；RC 形态部分涉及 Host 的方向按 D2D 处理（须同时核对产品型号与运行形态）。目标是计算与复制重叠时，非锁页内存的完成返回不能证明获得异步性能。

## 资源生命周期：部分初始化失败与所有权

- **正常返回与失败退出分别检查**：正常返回成功不证明失败退出没有遗漏；发生失败时保留首个错误，只清理**创建成功、由当前代码负责且使用已结束**的资源——不使用创建失败的输出，不顺手销毁调用者借来的对象；
- **部分初始化失败矩阵**：输入申请成功输出失败→保存输出首错、回收输入等自有资源；部分异步任务已提交后失败→先取得对应任务完成证据，不能直接按创建顺序倒序释放；释放本身失败→保留原始首错与清理错误，不无条件再释放一次；
- **临时 Context 切换与调用者恢复**：工具函数内 Create/DestroyContext 后出现 107002、当前句柄为空或调用者 Stream 失效时，恢复调用者原 Context 再继续；
- 最小检查顺序：列出创建点/使用点/释放点 → 分配 API 与目标版本释放族配对 → 确认排队使用均越过完成边界 → 检查失败分支的重复/提前释放 → 只修第一个被证据确认的配对或顺序错误。

## 输出参数与非连续 Tensor

输出参数需指向类型匹配的可写存储，读取前先检查调用成功条件——仅凭指针非空不能判断容量、生命周期或数据正确。非连续 Tensor 的 `viewDims`（逻辑形状）/`storageDims`（物理形状）/`stride`/`offset` 共同决定实际读写位置：stride 写错时地址合法也会读错业务数据；已带 offset 的视图不能再移动 `tensorData` 起点（重复偏移）。最大访问位置检查式：`offset + sum((viewDims[i]-1) × stride[i])`——适用条件为**非空、非负步长的普通 ND 视图**（另查溢出与分配范围）。空 Tensor（任一维为 0，如 shape [2,0]、stride [100,1]、offset 0——直接套式会得 99，误判不存在的访问为越界）无元素访问，单独处理、不走该式；该式结果是**元素位置**，判断字节容量越界还需结合元素大小换算。

## 失效边界

- 实测条目（107000/107006/组合标志值）均为 910B1/CANN 9.0.0 有限记录，标签只约束各自条目；
- 回调与报告订阅线程（`aclrtSubscribeReport`/`aclrtProcessReport`）的收尾、Blaze Launcher 清理顺序等更窄专题按原文档分流，不在本卡展开；
- Runtime API 完整语义见 `runtime/apis/`；本卡为排查专题的判定方法蒸馏。
