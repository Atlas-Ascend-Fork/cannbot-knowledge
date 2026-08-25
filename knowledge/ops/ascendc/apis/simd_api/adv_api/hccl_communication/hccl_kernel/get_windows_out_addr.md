---
type: API
title: GetWindowsOutAddr
description: 获取卡间通信数据WindowsOut起始地址，可用来直接作为计算的输入输出地址，减少拷贝。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/GetWindowsOutAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetWindowsOutAddr

获取卡间通信数据WindowsOut起始地址，可用来直接作为计算的输入输出地址，减少拷贝。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline GM_ADDR GetWindowsOutAddr(uint32_t rankId)

参数：
- rankId（输入）：待查询的卡的Id。

返回值：返回对应卡的卡间通信数据WindowsOut起始地址。当rankId非法时，返回nullptr。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AlltoAllvWrite](allto_allv_write.md)（`related`）：AlltoAllvWrite 与《GetWindowsOutAddr》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [GetWindowsInAddr](get_windows_in_addr.md)（`related`）：GetWindowsInAddr 与 GetWindowsOutAddr 是按 rank 获取通信窗口输入/输出地址的成对接口，rank 范围与空指针语义一致。
- [HCCL Kernel侧接口](hccl_kernel.md)（`related`）：HCCL Kernel 接口页给出初始化、提交、等待和集合通信流程，是直接使用 WindowsOut 地址时所属的通信客户端生命周期。
- [HCCL使用说明](hccl_usage.md)（`related`）：HCCL 使用说明解释 AI Core 仅准备通信任务、由 AI CPU/CCU 服务端执行的模型，补足 WindowsOut 作为计算输入输出地址以减少拷贝的使用目的。
<!-- cannbot:related:end -->
