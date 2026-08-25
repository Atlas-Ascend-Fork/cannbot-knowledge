---
type: API
title: AscSetL0c2gmChannelPara
description: 设置通道步长寄存器比特位，配合L0C搬运接口使用。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l0c2gm_channel_para.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL0c2gmChannelPara

对通道步长参数的专用寄存器的比特位进行设置。需要配合接口asc_copy_l0c2l1或asc_copy_l0c2gm使用。 仅当调用接口时开启NZ2DN模式时，此功能才有效。
函数原型：void asc_set_l0c2gm_channel_para(uint64_t config)
约束：需要在对应的数据搬运接口之前调用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](../cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：AscSetL0c2gmChannelPara说明设置通道步长寄存器比特位，配合L0C搬运接口使用。
- [AscCopyL0c2Gm](../cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0c2gmChannelPara》补充：设置通道步长寄存器比特位，配合L0C搬运接口使用。
- [AscCopyL0c2Gm](../cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm_arch_3510.md)（`related`）：AscCopyL0c2Gm说明将矩阵计算结果从L0C Buffer搬运至GM，搬运过程中支持随路量化、ReLU、格式转换、通道拆分等能力；对AscSetL0c2gmChannelPara而言，ChannelPara 只在 NZ2DN 的 L0C 搬运前生效；Channel Split 的格式限制和 AscCopyL0c2Gm 的参数共同界定有效调用。
- [F32 Channel Split](../../basic_api/cube_compute/cube_store_key_features/f32_channel_split.md)（`related`）：F32 Channel Split说明矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵；对AscSetL0c2gmChannelPara而言，ChannelPara 只在 NZ2DN 的 L0C 搬运前生效；Channel Split 的格式限制和 AscCopyL0c2Gm 的参数共同界定有效调用。
- [Int8 Channel Merge](../../basic_api/cube_compute/cube_store_key_features/int8_channel_merge.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；AscSetL0c2gmChannelPara正文说明“设置通道步长寄存器比特位，配合L0C搬运接口使用”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
<!-- cannbot:related:end -->
