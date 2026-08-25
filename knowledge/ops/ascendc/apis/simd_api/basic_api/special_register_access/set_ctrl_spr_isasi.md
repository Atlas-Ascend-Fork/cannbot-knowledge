---
type: API
title: SetCtrlSpr
description: 对CTRL寄存器的特定比特位进行设置，通过模板参数指定比特位范围并写入对应值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/SetCtrlSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# SetCtrlSpr

头文件路径为："basic_api/kernel_operator_common_intf.h"。

对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。

参数：startBit: 起始比特位索引。；endBit: 终止比特位索引。；value(输入): 起止比特位上新设置的值。；CTRL寄存器比特位: 默认值；CTRL[8:6]: 3'b000；CTRL[10:9]: 2'b00；CTRL[45]: 1'b0；CTRL[48]: 1'b0。

支持数据类型：本接口为寄存器访问接口，不涉及张量数据类型操作。参数value类型固定为int64_t。

约束：- Ascend 950PR/Ascend 950DT仅支持CTRL[8:6]、CTRL[10:9]、CTRL[45]、CTRL[48]、CTRL[50]、CTRL[53]、CTRL[59]、CTRL[60]比特位。

- Atlas A3 训练系列产品/Atlas A3 推理系列产品仅支持CTRL[48]比特位。

- Atlas A2 训练系列产品/Atlas A2 推理系列产品仅支持CTRL[48]比特位。

- Ascend 950PR/Ascend 950DT对于CTRL[8:6]和CTRL[10:9]的设置，已封装原子操作API，建议通过这些原子操作API进行配置。
  - SetAtomicType
  - DisableDmaAtomic
  - SetAtomicAdd
  - SetAtomicMax
  - SetAtomicMin

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetCtrl](../../c_api/sys_var/asc_get_ctrl.md)（`related`）：AscGetCtrl 与《SetCtrlSpr》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
- [AscSetCtrl](../../c_api/sys_var/asc_set_ctrl.md)（`related`）：SetCtrlSpr 以模板位段方式写 CTRL 寄存器，AscSetCtrl 则写入读取并修改后的整体寄存器值，是同一控制寄存器的两种配置入口。
- [SetSaturationFlag](set_saturation_flag_isasi.md)（`related`）：“SetSaturationFlag”定义：设置饱和开关的标志位，控制计算或精度转换时饱和模式的开启与关闭。；“SetCtrlSpr”定义：对CTRL寄存器的特定比特位进行设置，通过模板参数指定比特位范围并写入对应值。。实质衔接：SetSaturationFlag 修改饱和状态，Get 用于验证当前值；通用 CTRL SPR set/reset 提供底层控制位管理和恢复默认值的契约。
- [GetCtrlSpr](get_ctrl_spr_isasi.md)（`same_topic`）：SetCtrlSpr 与 GetCtrlSpr 读写 CTRL 的同一 bit 区间，可形成写后读回验证。
- [GetSpr](get_spr.md)（`same_topic`）：焦点处理特殊寄存器读取与配套清零、CTRL 位设置/复位；SetCtrlSpr正文说明“对CTRL寄存器的特定比特位进行设置，通过模板参数指定比特位范围并写入对应值”。候选操作同一 SPR/CTRL 状态，明确读前设置、读后清理与位域复位。
- [ResetCtrlSpr](reset_ctrl_spr_isasi.md)（`same_topic`）：SetCtrlSpr 临时修改 CTRL 位段，ResetCtrlSpr 是对应的收尾接口。
<!-- cannbot:related:end -->
