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

- [AscSetL0c2gmConfig](asc_set_l0c2gm_config.md)（`related`）：数据搬运过程中进行随路量化时，通过调用该接口获取量化操作前矢量的起始地址。；quant_pre(输入): 量化操作前矢量的起始地址。。左卡取得 L0C→GM 随路量化前矢量地址，右卡把该地址作为 quant_pre 配入搬出量化流程；两端形成地址获取到配置提交的直接调用链。
<!-- cannbot:related:end -->
