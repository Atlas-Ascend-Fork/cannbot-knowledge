---
type: API
title: AscCopyGm2l1Dn2nz
description: 将矩阵数据从GM搬运到L1 Buffer，过程中执行DN到NZ格式转换并在最内层维度补0。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1_dn2nz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCopyGm2l1Dn2nz

将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行DN->NZ/NCHW->NC1HWC0/NCHW->C1HWNC0操作。若D未对齐C0的大小，将会在L1 Buffer的最内层维度填充0值。GM中的数据以DN类型存储；L1中的数据以NZ形式存储。

DN->NZ的搬运形式如下图

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；loop1_src_stride(输入): 搬运过程中最内层循环相邻迭代源操作数的数据块间的间隔，单位为字节。；l2_cache_ctl(输入): 配置数据在L2 Cache中的管理策略。取值说明请参见表2。；n_value(输入): 源操作数中DN排布中的N值。；d_value(输入): 源操作数中DN排布中的D值。；loop4_src_stride(输入): 搬运过程中最外层循环相邻迭代源操作数的数据块间的间隔，单位为字节。；smallc0_en(输入): SmallC0模式开关：   &bull; true：C0_SIZE会被pad至32个字节。  &bull; false：C0_SIZE会被pad为4个c。

约束：- 各存储单元的空间大小和对齐要求
- 注意当且仅当D <= 4时，smallc0_en才可以被启用，否则它会失效。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetGm2l1NzPara](../sys_var/asc_set_gm2l1_nz_para.md)（`related`）：“对MTE2_NZ_PARA寄存器中的值进行设置，可以在调用asc_copy_gm2l1_dn2nz和asc_copy_gm2l1_nd2nz前设置相关参数。”；“将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行DN->NZ/NCHW->NC1HWC0/NCHW->C1HWNC0操作。”。焦点接口在 DN→NZ 搬运前写入该指令消费的 MTE2_NZ_PARA 参数。
- [DataCopy](../../basic_api/cube_compute/cube_compute_load/data_copy_gm_to_l1_dn2_nz.md)（`same_topic`）：将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行DN->NZ/NCHW->NC1HWC0/NCHW->C1HWNC0操作。若D未对齐C0的大小，将会在L1 Buffer的最内层维度填充0值。GM中的数据以DN类型存储；L1中的数据以NZ形式存储。；将Global Memory中的DN格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。。两卡描述同一 GM 到 L1 的 DN→NZ 搬运，在 C API 与 Basic API 中提供不同调用表面。
<!-- cannbot:related:end -->
