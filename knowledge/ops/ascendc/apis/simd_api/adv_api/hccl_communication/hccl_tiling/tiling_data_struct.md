---
type: API
title: HcclTilingData
description: HCCL通信Tiling配置结构体，包含Mc2InitTiling和Mc2CcTiling，通过GetTiling接口返回，最多支持8个通信任务。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/TilingData_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# HcclTilingData

在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。本节TilingData结构体包括[Mc2InitTiling](#table4835205712588)和[Mc2CcTiling](#table678914014562)，这两个结构体均通过调用GetTiling接口返回。其中，[Mc2CcTiling](#table678914014562)为具体每个通信任务的参数配置，当算子中有多个通信任务时，可定义多个[Mc2CcTiling](#table678914014562)参数：（最多支持定义8个）。

参数：
- reserved（初始化通信任务配置。uint8_t*类型，支持最大长度64字节，该结构体仅支持通过接口GetTiling获取。
- reserved：各通信域中每个通信任务的参数配置。uint8_t*类型，支持最大长度280字节，该结构体仅支持通过接口GetTiling获取。注意，最多支持配置8个通信任务。

<!-- cannbot:related:start -->
## 相关

- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：HCCL Tiling构造函数 与《HcclTilingData》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [HCCL通信类](../hccl_communication.md)（`related`）：HCCL通信类 与《HcclTilingData》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [InitV2](../hccl_kernel/init_v2.md)（`related`）：InitV2 消费 HcclTilingData 起始处的 Mc2InitTiling 栈地址来初始化客户端，并要求标准 C++ 结构定义；这与 focal 给出的结构布局直接衔接。
- [SetAlgConfig](set_alg_config.md)（`related`）：TilingData 结构承载 SetAlgConfig 等 setter 生成的固定通信参数，是 Host 配置传入 Kernel 的接口边界。
- [SetCcTilingV2](../hccl_kernel/set_cc_tiling_v2.md)（`related`）：SetCcTilingV2 以 Mc2CcTiling 相对 Mc2InitTiling 的 offset 绑定通信算法配置；HcclTilingData 的连续布局和最多八组配置决定 offset 的含义。
- [SetDebugMode](set_debug_mode.md)（`related`）：TilingData 结构是 debug mode 等通信配置跨 Host/Kernel 的承载契约。
- [SetGroupName](set_group_name.md)（`related`）：SetGroupName 与《HcclTilingData》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [v1版本TilingData（废弃）](v1_tiling_data_deprecated.md)（`related`）：当前结构化 TilingData 替代固定字段顺序，减少版本耦合。
- [GetTiling](get_tiling.md)（`same_topic`）：GetTiling 直接返回由 Mc2InitTiling 与最多 8 个 Mc2CcTiling 任务组成的 HcclTilingData。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`same_topic`）：两卡描述同一 HcclTilingData 契约：Mc2InitTiling 加最多八个 Mc2CcTiling 任务，并由 GetTiling 生成后传给 Kernel。
- [HCCL Tiling侧接口](hccl_tiling.md)（`same_topic`）：HcclTilingData说明HCCL通信Tiling配置结构体，包含Mc2InitTiling和Mc2CcTiling，通过GetTiling接口返回，最多支持8个通信任务。
- [SetCommBlockNum](set_comm_block_num.md)（`same_topic`）：SetCommBlockNum 与《HcclTilingData》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [SetReduceType](set_reduce_type.md)（`same_topic`）：SetReduceType 与《HcclTilingData》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《HcclTilingData》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [v2版本TilingData（废弃）](v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《HcclTilingData》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
