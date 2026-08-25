---
type: API
title: GetWindowsInAddr
description: 获取卡间通信数据WindowsIn起始地址，可用来直接作为计算的输入输出地址，减少拷贝。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/GetWindowsInAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetWindowsInAddr

获取卡间通信数据WindowsIn起始地址，可用来直接作为计算的输入输出地址，减少拷贝。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline GM_ADDR GetWindowsInAddr(uint32_t rankId)

参数：
- rankId（输入）：待查询的卡的Id。

返回值：返回对应卡的卡间通信数据WindowsIn起始地址。当rankId非法时，返回nullptr。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AlltoAllvWrite](allto_allv_write.md)（`related`）：AlltoAllvWrite 与《GetWindowsInAddr》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [GetRankId](get_rank_id.md)（`related`）：GetRankId 提供本地 rank 身份，而 GetWindowsInAddr 按 rank 定位窗口；两者共同支撑 rank 定位但不能互相替代。
- [GetWindowsOutAddr](get_windows_out_addr.md)（`related`）：GetWindowsInAddr 与 GetWindowsOutAddr 是按 rank 获取通信窗口输入/输出地址的成对接口，rank 范围与空指针语义一致。
- [HCCL Kernel侧接口](hccl_kernel.md)（`related`）：Hccl Kernel 总览说明通信对象生命周期和窗口资源，给出 GetWindowsInAddr 的宿主对象上下文。
- [HCCL使用说明](hccl_usage.md)（`related`）：HCCL 使用流程解释 Prepare/Commit 的服务模型和窗口地址使用时机，使窗口输入地址进入完整通信任务链。
<!-- cannbot:related:end -->
