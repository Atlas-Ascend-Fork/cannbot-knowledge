---
type: API
title: GetCtrlSpr
description: 读取CTRL寄存器特定比特位上的值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/GetCtrlSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetCtrlSpr

头文件路径为："basic_api/kernel_operator_common_intf.h"。

读取CTRL寄存器（控制寄存器）特定比特位上的值。

参数：startBit: 起始比特位索引。；endBit: 终止比特位索引。

支持数据类型：本接口为寄存器访问接口，不涉及张量数据类型操作。返回值类型固定为int64_t。

约束：- startBit和endBit的取值范围为[0, 63]。
- startBit小于等于endBit。
- 各比特位的说明

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [ResetCtrlSpr](reset_ctrl_spr_isasi.md)（`related`）：“读取CTRL寄存器（控制寄存器）特定比特位上的值。”；“对CTRL寄存器（控制寄存器）的特定比特位做重置。由模板参数［startBit, endBit］指定的比特位重置为默认值，默认值参考表 常用CTRL寄存器比特位说明。”。Reset 后可用 GetCtrlSpr 对同一 bit range 回读默认值，闭合临时控制位的恢复验证。
- [SetCtrlSpr](set_ctrl_spr_isasi.md)（`related`）：“读取CTRL寄存器（控制寄存器）特定比特位上的值。”；“对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。”。两接口以相同 bit range 形成 CTRL 配置写入与回读核验链。
<!-- cannbot:related:end -->
