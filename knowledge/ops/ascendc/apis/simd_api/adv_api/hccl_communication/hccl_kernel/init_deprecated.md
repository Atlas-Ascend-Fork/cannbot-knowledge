---
type: API
title: Init（废弃）
description: HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/Init_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Init（废弃）

HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline void Init(GM_ADDR context, __gm__ void* initTiling = nullptr)

参数：
- context（输入）：通信上下文，包含rankDim，rankID等相关信息。
- initTiling（输入）：可选参数，通信域初始化Mc2InitTiling的地址。Mc2InitTiling在Host侧计算得出，具体请参考表1 Mc2InitTiling参数说明，由框架传递到Kernel函数中使用，完整示例请参考8.13.1.2-调用示例。

约束：
- 若调用本接口时传入initTiling参数，则必须与SetCcTiling接口配合使用。
- 同一个程序中不能同时调用传入可选参数initTiling的接口和不传入可选参数initTiling的接口，推荐使用传入initTiling参数的调用方式。
- 若调用本接口时传入initTiling参数，必须使用标准C++语法定义TilingData结构体的开发方式。
- 本接口不支持使用相同的context初始化多个HCCL对象。每个HCCL对象都应获取其自身的通信上下文。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Finalize（HCCL集合通信）](finalize.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；Finalize（HCCL集合通信）正文说明“通知服务端后续无通信任务，执行结束后退出”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [HCCL使用说明](hccl_usage.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；HCCL使用说明正文说明“Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [InitV2](init_v2.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；InitV2正文说明“HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；SetCcTilingV2正文说明“用于设置HCCL客户端中某个通信算法配置的TilingData地址”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [SetCcTiling（废弃）](set_cc_tiling_deprecated.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；SetCcTiling（废弃）正文说明“用于设置HCCL客户端通信算法的Tiling地址”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [v2版本TilingData（废弃）](../hccl_tiling/v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《Init（废弃）》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
