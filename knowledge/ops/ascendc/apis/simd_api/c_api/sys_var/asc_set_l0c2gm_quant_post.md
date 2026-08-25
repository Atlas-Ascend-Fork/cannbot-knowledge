---
type: API
title: AscSetL0c2gmQuantPost
description: 设置QUANT_POST寄存器值，存储Fixpipe后处理阶段量化信息。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l0c2gm_quant_post.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL0c2gmQuantPost

对QUANT_POST寄存器中的值进行设置, QUANT_POST是一个64bit的寄存器，存储Fixpipe后处理阶段量化信息。 其中各bit含义如下，其中各种量化模式的说明可见asc_copy_l0c2l1中对各种量化模式的说明： 表1 QUANT_POST寄存器比特位说明
函数原型：void asc_set_l0c2gm_quant_post(uint64_t config)
参数：config（输入）：待设置的寄存器值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2L1](../cube_data_move/asc_copy_l0c2l1/asc_copy_l0c2l1.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscCopyL0c2L1正文说明“将数据从L0C搬运到L1 Buffer的接口，包含不同架构版本的具体实现”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [AscCopyL0c2L1](../cube_data_move/asc_copy_l0c2l1/asc_copy_l0c2l1_arch_2201.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscCopyL0c2L1正文说明“矩阵计算完成后对结果进行量化处理，并将处理结果搬运到L1 Buffer中，支持9种量化模式”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [AscCopyL0c2L1](../cube_data_move/asc_copy_l0c2l1/asc_copy_l0c2l1_arch_3510.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscCopyL0c2L1正文说明“将矩阵计算结果从L0C Buffer搬运至L1 Buffer，搬运过程中支持随路量化、ReLU、格式转换等能力”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [AscGetL0c2gmPrequant](../cube_compute/asc_get_l0c2gm_prequant.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscGetL0c2gmPrequant正文说明“数据搬运过程中进行随路量化时，通过调用该接口获取量化操作前矢量的起始地址”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [AscSetL0c2gmConfig](../cube_compute/asc_set_l0c2gm_config.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscSetL0c2gmConfig正文说明“数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [AscSetL0cCopyParams](../cube_data_move/asc_set_l0c_copy_params.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscSetL0cCopyParams正文说明“设置L0C搬运随路格式转换（NZ转ND）的相关配置”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [AscSetL0cCopyPrequant](../cube_data_move/asc_set_l0c_copy_prequant.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscSetL0cCopyPrequant正文说明“设置数据搬运随路量化流程中的标量量化参数”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
<!-- cannbot:related:end -->
