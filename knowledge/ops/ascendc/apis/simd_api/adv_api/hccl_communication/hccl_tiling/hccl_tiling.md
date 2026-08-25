---
type: API
title: HCCL Tiling侧接口
description: 提供HCCL集合通信的Host侧Tiling接口，包含TilingData结构体、GetTiling及通信类型、分组、队列等参数设置方法。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/HCCL_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Tiling侧接口

提供 HCCL 集合通信的 Host 侧 Tiling 接口，通过 TilingData 结构体承载通信切分参数。
核心方法 GetTiling 获取最终 Tiling 数据；SetOpType 设置通信算子类型，SetGroupName 设置通信组名，SetReduceType 设置归约操作类型，SetAlgConfig 配置算法参数。
另提供 SetCommBlockNum/SetQueueNum/SetCommEngine 控制通信引擎与队列分配，SetSkipLocalRankCopy/SetSkipBufferWindowCopy 跳过特定拷贝路径以优化性能，SetDebugMode 支持调试模式。
v1/v2 版本 TilingData 已废弃，新代码应使用当前版本结构体。

<!-- cannbot:related:start -->
## 相关

- [HCCL Context简介](../hccl_context/hccl_context_intro.md)（`related`）：HCCL Context简介 与《HCCL Tiling侧接口》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL通信类](../hccl_communication.md)（`related`）：HCCL通信类 与《HCCL Tiling侧接口》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [GetTiling](get_tiling.md)（`same_topic`）：GetTiling说明获取Mc2InitTiling参数和Mc2CcTiling参数。
- [HCCL Kernel侧接口](../hccl_kernel/hccl_kernel.md)（`same_topic`）：HCCL Kernel侧接口说明提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`same_topic`）：HCCL Tiling使用说明说明说明 HCCL 通信任务的 TilingData、Mc2InitTiling、Mc2CcTiling 及临时空间配置方式。
- [HCCL使用说明](../hccl_kernel/hccl_usage.md)（`same_topic`）：HCCL使用说明说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [HcclTilingData](tiling_data_struct.md)（`same_topic`）：HcclTilingData说明HCCL通信Tiling配置结构体，包含Mc2InitTiling和Mc2CcTiling，通过GetTiling接口返回，最多支持8个通信任务。
- [InitV2](../hccl_kernel/init_v2.md)（`same_topic`）：InitV2说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
- [SetReduceType](set_reduce_type.md)（`same_topic`）：SetReduceType 与《HCCL Tiling侧接口》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《HCCL Tiling侧接口》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [v2版本TilingData（废弃）](v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《HCCL Tiling侧接口》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
