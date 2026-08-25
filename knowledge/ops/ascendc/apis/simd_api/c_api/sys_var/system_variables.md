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

<!-- cannbot:related:start -->
## 相关

- [AscGetSqueezeStatus](asc_get_squeeze_status.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《系统变量》说明SIMD C API系统变量类接口汇总，提供架构版本、核编号、循环计数器、CTRL寄存器等系统变量的查询与设置。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [AscGetSubBlockNum](asc_get_sub_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《系统变量》说明SIMD C API系统变量类接口汇总，提供架构版本、核编号、循环计数器、CTRL寄存器等系统变量的查询与设置。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscGetVfLen](asc_get_vf_len.md)（`related`）：系统变量索引明确列出 AscGetVfLen，用于取得当前 VF 的向量长度并支撑分块循环。
- [AscSetCtrl](asc_set_ctrl.md)（`related`）：系统变量入口页把 asc_set_ctrl/get_ctrl 放在运行时状态配置接口中，并列出其与核编号、架构和搬运寄存器的边界。
- [指令发射队列空闲槽位查询](asc_get_pipe_idle_slot_count.md)（`related`）：《指令发射队列空闲槽位查询》说明本接口为试验接口，在后续版本中可能会调整或改进，不保证后续兼容性；《系统变量》说明SIMD C API系统变量类接口汇总，提供架构版本、核编号、循环计数器、CTRL寄存器等系统变量的查询与设置。。二者在该试验接口查询指令发射队列余量，系统变量索引是其能力边界和兼容性入口上存在可执行的直接衔接。
- [AscGetBlockIdx](asc_get_block_idx.md)（`same_topic`）：AscGetBlockIdx 与《系统变量》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [AscGetBlockNum](asc_get_block_num.md)（`same_topic`）：AscGetBlockNum 与《系统变量》的实质衔接是：AscGetBlockNum 与 GetBlockIdx 共同定义多核分片的总数和当前索引；C++ 对应入口及系统变量页给出内置 block_num 迁移上下文。
- [AscGetCtrl](asc_get_ctrl.md)（`same_topic`）：AscGetCtrl 与《系统变量》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
- [AscGetSmmuTagVersion](asc_get_smmu_tag_version.md)（`same_topic`）：AscGetSmmuTagVersion 与《系统变量》的实质衔接是：AscGetSmmuTagVersion 属于系统变量读取；候选中只有系统变量总览提供该硬件状态的使用域，其他共享 Get 前缀不足以构成关系。
<!-- cannbot:related:end -->
