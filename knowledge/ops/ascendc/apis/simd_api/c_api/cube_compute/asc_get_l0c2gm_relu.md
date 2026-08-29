---
type: API
title: AscGetL0c2gmRelu
description: 数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_get_l0c2gm_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscGetL0c2gmRelu

数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetL0c2gmConfig](asc_set_l0c2gm_config.md)（`related`）：relu_pre(输入): ReLU操作前矢量的起始地址；数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址；前者设置 ReLU 前矢量地址，后者读取同一地址。
<!-- cannbot:related:end -->
