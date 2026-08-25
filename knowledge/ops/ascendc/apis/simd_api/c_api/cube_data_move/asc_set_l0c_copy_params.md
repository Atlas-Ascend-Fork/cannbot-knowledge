---
type: API
title: AscSetL0cCopyParams
description: 设置L0C搬运随路格式转换（NZ转ND）的相关配置。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l0c_copy_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscSetL0cCopyParams

DataCopy从L0C Buffer搬运到Global Memory或L1 Buffer过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。

参数：nd_num(输入): ND矩阵的数量，取值范围：nd_num∈[1, 65535]。；src_nd_stride(输入): 以分形大小为单位的源步长，源相邻nz矩阵的起始地址间的偏移。  src_nd_stride∈[1, 512]，单位：fractal_size 1024B。；dst_nd_stride(输入): 目的相邻ND矩阵的起始地址间的偏移。单位为元素。   dst_nd_stride∈[1, 65535]。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0cCopyParams》补充：设置L0C搬运随路格式转换（NZ转ND）的相关配置。
- [AscCopyL0c2L1](asc_copy_l0c2l1/asc_copy_l0c2l1_arch_2201.md)（`related`）：AscCopyL0c2L1：AscCopyL0c2L1的2201/3510卡核对同一搬运原型，DataCopyL0CToL1提供C++对应语义，AscSetL0cCopyParams配置该L0C搬出的通用参数。 目标卡《AscSetL0cCopyParams》补充：设置L0C搬运随路格式转换（NZ转ND）的相关配置。
- [AscSetL0cCopyPrequant](asc_set_l0c_copy_prequant.md)（`related`）：《AscSetL0cCopyParams》明确“设置L0C搬运随路格式转换（NZ转ND）的相关配置。”；它与《AscSetL0cCopyPrequant》的“设置数据搬运随路量化流程中的标量量化参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscCopyL0c2ub](asc_copy_l0c2ub.md)（`same_topic`）：AscSetL0cCopyParams说明设置L0C搬运随路格式转换（NZ转ND）的相关配置。
- [AscSetL0c2gmNz2nd](../cube_compute/asc_set_l0c2gm_nz2nd.md)（`same_topic`）：AscSetL0c2gmNz2nd 与《AscSetL0cCopyParams》的实质衔接是：AscSetL0c2gmNz2nd 为 L0C 搬出配置 NZ→ND，AscSetL0cCopyParams 与 C++ SetFixpipeNz2ndFlag 是同一配置的相邻 API 层表达；NZ2ND 概念和 MmadDirectionN 说明格式转换与搬出方向的配合。
- [AscSetL0c2gmQuantPost](../sys_var/asc_set_l0c2gm_quant_post.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscSetL0cCopyParams正文说明“设置L0C搬运随路格式转换（NZ转ND）的相关配置”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
<!-- cannbot:related:end -->
