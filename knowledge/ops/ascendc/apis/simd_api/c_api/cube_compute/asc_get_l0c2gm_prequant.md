---
type: API
title: AscGetL0c2gmPrequant
description: 数据搬运过程中进行随路量化时，通过调用该接口获取量化操作前矢量的起始地址。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_get_l0c2gm_prequant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscGetL0c2gmPrequant

数据搬运过程中进行随路量化时，通过调用该接口获取量化操作前矢量的起始地址。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetL0c2gmUnitflag](asc_get_l0c2gm_unitflag.md)（`related`）：Prequant 地址与 unit_flag 都用于观察同一随路量化搬出流程，一个定位量化前数据、一个读取同步标志。
- [SetFixpipePreQuantFlag](../../basic_api/cube_compute/cube_store_aux_config/set_fixpipe_pre_quant_flag.md)（`related`）：AscGetL0c2gmPrequant 与《SetFixpipePreQuantFlag》的实质衔接是：AscGetL0c2gmPrequant 读取随路量化前矢量地址，AscSetL0cCopyPrequant、总配置和 C++ prequant flag 是写入并启用同一状态的控制端。
- [AscGetL0c2gmRelu](asc_get_l0c2gm_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscGetL0c2gmPrequant》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [AscSetL0c2gmConfig](asc_set_l0c2gm_config.md)（`same_topic`）：AscGetL0c2gmPrequant 与《AscSetL0c2gmConfig》的实质衔接是：AscGetL0c2gmPrequant 读取随路量化前矢量地址，AscSetL0cCopyPrequant、总配置和 C++ prequant flag 是写入并启用同一状态的控制端。
- [AscSetL0c2gmQuantPost](../sys_var/asc_set_l0c2gm_quant_post.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscGetL0c2gmPrequant正文说明“数据搬运过程中进行随路量化时，通过调用该接口获取量化操作前矢量的起始地址”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [AscSetL0cCopyPrequant](../cube_data_move/asc_set_l0c_copy_prequant.md)（`same_topic`）：AscGetL0c2gmPrequant 与《AscSetL0cCopyPrequant》的实质衔接是：AscGetL0c2gmPrequant 读取随路量化前矢量地址，AscSetL0cCopyPrequant、总配置和 C++ prequant flag 是写入并启用同一状态的控制端。
<!-- cannbot:related:end -->
