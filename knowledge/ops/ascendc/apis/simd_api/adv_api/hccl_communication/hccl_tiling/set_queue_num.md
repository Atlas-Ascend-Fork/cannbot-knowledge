---
type: API
title: SetQueueNum
description: 设置每个向服务端下发任务的核上的BatchWrite通信队列数量。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.data_movement.communication.collective_communication
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetQueueNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/hccl/hccl_tiling.h
---

# SetQueueNum

## 功能说明

设置每个向服务端下发任务的核上的BatchWrite通信队列数量。

## 函数原型

```
uint32_t SetQueueNum(uint16_t num)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| num | 输入 | 表示队列的数量。参与通信的核数*队列数量支持设置的取值范围为[0, 40]，参与通信的核数的设置请参考[SetCommBlockNum](set_comm_block_num.md)。 |

## 返回值说明

-   0表示设置成功。
-   非0表示设置失败。

## 约束说明


本接口仅在Atlas A3 训练系列产品/Atlas A3 推理系列产品上通信类型为HCCL\_CMD\_BATCH\_WRITE时生效。


## 调用示例

```
const char* groupName = "testGroup";
uint32_t opType = HCCL_CMD_BATCH_WRITE;
std::string algConfig = "BatchWrite=level0:fullmesh";
uint32_t reduceType = 0; // BatchWrite无归约语义，此处占位
AscendC::Mc2CcTilingConfig mc2CcTilingConfig(groupName, opType, algConfig, reduceType);
mc2CcTilingConfig.SetQueueNum(2U);
```


<!-- cannbot:related:start -->
## 相关

- [BatchWrite](../hccl_kernel/batch_write.md)（`related`）：设置每个向服务端下发任务的核上的BatchWrite通信队列数量；queueID（输入）：指定当前通信所在的队列ID，默认值为0；配置页决定 BatchWrite 调用中 queueID 的可用队列域。
- [GetQueueNum](../hccl_kernel/get_queue_num.md)（`related`）：焦点卡“获取BatchWrite通信任务的通信队列数量。”，候选卡“设置每个向服务端下发任务的核上的BatchWrite通信队列数量。”；Host 设置值与 Kernel 查询值构成同一 BatchWrite 队列数量合同。
- [SetCommBlockNum](set_comm_block_num.md)（`related`）：参与通信的核数*队列数量支持设置的取值范围为［0, 40］；设置参与BatchWrite通信的核数；两接口的乘积共同决定合法 BatchWrite 队列配置。
<!-- cannbot:related:end -->
