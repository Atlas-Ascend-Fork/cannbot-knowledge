---
type: API
title: AscSetL0c2gmConfig
description: 数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_l0c2gm_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL0c2gmConfig

数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。

参数：relu_pre(输入): ReLU操作前矢量的起始地址。；quant_pre(输入): 量化操作前矢量的起始地址。；enable_unit_flag(输入): 是否启用unit_flag。unit_flag是一种矩阵计算指令和矩阵搬运指令细粒度的并行，开启该功能后，硬件每计算完一个分形，计算结果就会被搬出，该功能。

约束：支持以下三种传参形式
- 同时设置relu_pre和quant_pre。
- 仅传入relu_pre，quant_pre传入0。
- 仅传入quant_pre，relu_pre传入0。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetL0c2gmPrequant](asc_get_l0c2gm_prequant.md)（`related`）：数据搬运过程中进行随路量化时，通过调用该接口获取量化操作前矢量的起始地址。；quant_pre(输入): 量化操作前矢量的起始地址。。左卡取得 L0C→GM 随路量化前矢量地址，右卡把该地址作为 quant_pre 配入搬出量化流程；两端形成地址获取到配置提交的直接调用链。
- [AscGetL0c2gmRelu](asc_get_l0c2gm_relu.md)（`related`）：relu_pre(输入): ReLU操作前矢量的起始地址；数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址；前者设置 ReLU 前矢量地址，后者读取同一地址。
- [AscGetL0c2gmUnitflag](asc_get_l0c2gm_unitflag.md)（`related`）：enable_unit_flag(输入): 是否启用unit_flag。unit_flag是一种矩阵计算指令和矩阵搬运指令细粒度的并行；数据搬运过程中进行随路量化时，通过调用该接口获取unit_flag设置；前者写入组合配置，后者读取其中的 unit_flag 字段。
<!-- cannbot:related:end -->
