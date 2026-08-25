---
type: API
title: v2版本TilingData（废弃）
description: AI CPU启动下发通信任务前，需获取固定的通信配置，如表1所示。在算子实现中，由Tiling组装通信配置项，通过配置固定参数和固定参数顺序的Tiling
  Data，将通信配置信息在调用AI CPU通信接口时传递给AI CPU。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/v2_TilingData_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# v2版本TilingData（废弃）

AI CPU启动下发通信任务前，需获取固定的通信配置，如[表1](#table4835205712588)所示。在算子实现中，由Tiling组装通信配置项，通过配置固定参数和固定参数顺序的Tiling Data，将通信配置信息在调用AI CPU通信接口时传递给AI CPU。

参数：
- version：uint32_t类型。用于区分TilingData版本。 v2版本的TilingData结构体中，version字段仅支持取值为2。 注意：该字段在v2版本TilingData中的位置，同v1版本的preparePosition字段。当该字段取值为2时，为v2版本的结构体，当取值为1时，为v1版本的结构体，请使用Mc2Msg结构体。
- mc2HcommCnt：uint32_t类型。表示各通信域中通信任务总个数。当前该参数支持的最大取值为3。
- serverCfg：[Mc2ServerCfg](#table96371578575)类型。集合通信server端通用参数配置。
- hcom：[Mc2HcommCfg](#table13131010011)类型。各通信域中每个通信任务的参数配置。在通信算子TilingData的定义中，根据各通信域中通信任务总个数，共需要定义mc2HcommCnt个Mc2HcommCfg结构体。例如：mc2HcommCnt=2，则需要依次定义2个[Mc2HcommCfg](#table13131010011)类型的参数，自定义参数名，比如hcom1、hcom2。
- version：预留字段，不需要配置。
约束：
- 如果需要使用v2版本的Tiling结构体，必须设置Tiling结构体的第一个参数version=2。
- 算子的Tiling Data结构需要完整包含v2版本HCCL TilingData参数，其中各参数需要严格按照对应参数的结构来定义。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`same_topic`）：v2版本TilingData（废弃） 与《GetTiling》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`same_topic`）：v2版本TilingData（废弃） 与《HCCL Tiling使用说明》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [HCCL Tiling侧接口](hccl_tiling.md)（`same_topic`）：v2版本TilingData（废弃） 与《HCCL Tiling侧接口》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`same_topic`）：v2版本TilingData（废弃） 与《HCCL Tiling构造函数》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [HcclTilingData](tiling_data_struct.md)（`same_topic`）：v2版本TilingData（废弃） 与《HcclTilingData》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [Init（废弃）](../hccl_kernel/init_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《Init（废弃）》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [SetCcTilingV2](../hccl_kernel/set_cc_tiling_v2.md)（`same_topic`）：v2版本TilingData（废弃） 与《SetCcTilingV2》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [SetCcTiling（废弃）](../hccl_kernel/set_cc_tiling_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《SetCcTiling（废弃）》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
- [v1版本TilingData（废弃）](v1_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《v1版本TilingData（废弃）》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
