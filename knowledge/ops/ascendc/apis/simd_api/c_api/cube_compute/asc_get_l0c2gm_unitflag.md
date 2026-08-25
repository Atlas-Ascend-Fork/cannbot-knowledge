---
type: API
title: AscGetL0c2gmUnitflag
description: 数据搬运过程中进行随路量化时，通过调用该接口获取unit_flag设置。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_get_l0c2gm_unitflag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscGetL0c2gmUnitflag

数据搬运过程中进行随路量化时，通过调用该接口获取unit_flag设置。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetL0c2gmPrequant](asc_get_l0c2gm_prequant.md)（`related`）：Prequant 地址与 unit_flag 都用于观察同一随路量化搬出流程，一个定位量化前数据、一个读取同步标志。
- [AscSetL0c2gmConfig](asc_set_l0c2gm_config.md)（`related`）：AscSetL0c2gmConfig 写入随路量化及 unit_flag 等配置，AscGetL0c2gmUnitflag 从同一 L0C→GM 状态读取该标志。
- [UnitFlag](../../basic_api/cube_compute/mmad_compute_key_features/unit_flag.md)（`related`）：C API getter 读取 L0C→GM 搬运的 unit flag 状态，连接特性概念与底层控制。
- [AscGetL0c2gmRelu](asc_get_l0c2gm_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscGetL0c2gmUnitflag》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [UnitFlag](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscGetL0c2gmUnitflag》提供“数据搬运过程中进行随路量化时，通过调用该接口获取unit_flag设置。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
