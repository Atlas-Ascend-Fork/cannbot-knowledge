---
type: API
title: L0C Buffer内存结构介绍
description: 为提升数据访问效率和吞吐量，L0C Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank
  Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/L0C_memory_structure_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L0C Buffer内存结构介绍

L0C Buffer 采用 Bank 结构设计，内存空间划分为多个 Bank 并分组为 Bank Group（BG），每个 Bank 为可独立操作的存储单元子模块。

Atlas A2/A3 训练推理系列产品：L0C Buffer 总容量 128KB，由 16 个 Bank 组成，每个 Bank 8KB（128 行 × 64B），16 个 Bank Group 各含 1 个 Bank。地址编码 17 位：L0C_ADDR[16:0] = {BANK_DEPTH[6:0] (行数[0,127]), BANK[3:0] (Bank编号[0,15]), BANK_WIDTH[5:0] (行内偏移[0,63])}。

Ascend 950PR/950DT：L0C Buffer 总容量 256KB，由 16 个 Bank 组成，每个 Bank 16KB（256 行 × 64B），16 个 Bank Group 各含 1 个 Bank。地址编码 18 位：L0C_ADDR[17:0] = {BANK_DEPTH[7:0] (行数[0,255]), BANK[3:0] (Bank编号[0,15]), BANK_WIDTH[5:0] (行内偏移[0,63])}。

<!-- cannbot:related:start -->
## 相关

- [DataCopyL0CToGM](data_copy_l0_c_to_gm.md)（`related`）：L0C 的 bank/行宽和地址编码决定 DataCopyL0CToGM 的源布局、对齐和 stride 解释。
- [DataCopy（L0C Buffer到UB数据搬运）](data_copy_l0_c_to_ub.md)（`related`）：DataCopy（L0C Buffer到UB数据搬运） 与《L0C Buffer内存结构介绍》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
- [FixpipeL0CToGM](fixpipe_l0_c_to_gm.md)（`related`）：Fixpipe 从 L0C 读取 NZ/Bank 布局并转换后写 GM，理解 bank 行宽是配置 m/n/stride 的前提。
- [FixpipeL0CToUB](fixpipe_l0_c_to_ub.md)（`same_topic`）：FixpipeL0CToUB 与《L0C Buffer内存结构介绍》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [矩阵计算的搬出](cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《L0C Buffer内存结构介绍》明确“为提升数据访问效率和吞吐量，L0C Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
<!-- cannbot:related:end -->
