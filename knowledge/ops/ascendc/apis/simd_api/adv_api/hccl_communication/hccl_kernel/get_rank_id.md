---
type: API
title: GetRankId
description: 获取本卡RankId。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/GetRankId.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetRankId

获取本卡RankId。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline uint32_t GetRankId()

返回值：返回本卡RankId。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AlltoAllvWrite](allto_allv_write.md)（`related`）：AlltoAllvWrite 与《GetRankId》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [GetWindowsInAddr](get_windows_in_addr.md)（`related`）：GetRankId 提供本地 rank 身份，而 GetWindowsInAddr 按 rank 定位窗口；两者共同支撑 rank 定位但不能互相替代。
- [GetRankDim](get_rank_dim.md)（`same_topic`）：“GetRankId”处理获取本卡RankId。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。；“GetRankDim”明确获取通信域内卡的数量。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。实质衔接：GetRankId 与 GetRankDim 在同一 HCCL 通信域分别给出当前卡编号和域内卡数，二者共同定义 rank 的有效范围。
<!-- cannbot:related:end -->
