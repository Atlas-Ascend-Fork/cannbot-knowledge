---
type: API
title: 系统变量
description: SIMD C API系统变量类接口汇总，提供架构版本、核编号、循环计数器、CTRL寄存器等系统变量的查询与设置。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/system_variables.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 系统变量

C API系统变量接口提供运行时系统状态查询与配置。核信息查询含asc_get_block_idx/block_num/core_id/sub_block_id/sub_block_num，架构查询含asc_get_arch_ver和asc_get_smmu_tag_version。
资源查询含asc_get_vf_len（矢量长度）、asc_get_system_cycle（系统周期）、asc_get_program_counter（程序计数器）、asc_get_phy_buf_addr/phy_stack_base/ffts_base_addr（物理地址）、asc_get_status（状态寄存器）。
配置接口含asc_set_ctrl/get_ctrl（CTRL寄存器）、asc_set_l0c2gm_quant_post/relu_alpha/channel_para（L0C到GM随路计算）、asc_set_gm2l1_nz_para/l12l0_padding_val/l3d_rpt_b等搬运参数。asc_get_pipe_idle_slot_count查询指令发射队列空闲槽位。
