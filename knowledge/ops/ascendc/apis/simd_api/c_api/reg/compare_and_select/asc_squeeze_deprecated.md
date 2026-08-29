---
type: API
title: AscSqueezeV2
description: 已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，搭配asc_storeunalign_postupdate可将有效数据大小保存至AR寄存器。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_squeeze_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSqueezeV2

该接口已废弃，请使用asc_squeeze_and_storeunalign实现筛选并连续搬出有效元素的功能。

将src中被mask选择的有效元素依次复制到dst，有效元素在dst上连续排列。dst中剩余位置元素置为0。

asc_squeeze_v2接口搭配asc_storeunalign_postupdate接口使用时，会将有效数据大小保存至AR寄存器，搬出时使用该值作为存储偏移量。AR寄存器中的数值可以通过asc_get_squeeze_status接口获取。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、hifloat8_t、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalign](../reg_store/asc_squeeze_and_storeunalign.md)（`related`）：该接口已废弃，请使用asc_squeeze_and_storeunalign实现筛选并连续搬出有效元素的功能。；reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的场景。 本接口将输入矢量数据寄存器src1中被掩码squeeze_mask选择的有效元素依次复制到矢量数据寄存器dst，有效元素在dst上连续排列，dst中后续非有效元素置0。若AR寄存器（用于累加已搬出的有效数据量）中累加了前序asc_squeeze_and_storeunalign指令的有效元素总数据量，则将dst中有效数据写入dst_addr + AR寄存器数据量的地址，并将本次执行的有效数据量大小（以字节为单位）累加进AR寄存器。如调用示例所示，多次连续调用本接口时，若不清空AR寄存器，可以实现自动地址偏移，不需要手动管理地址。。废弃卡明确指定 asc_squeeze_and_storeunalign 为迁移目标，目标卡给出筛选、连续非对齐搬出和 AR 自动偏移的替代合同，因此该边直接推进旧调用迁移。
- [AscSqueeze](asc_squeeze.md)（`same_topic`）：将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。；该接口已废弃，请使用asc_squeeze_and_storeunalign实现筛选并连续搬出有效元素的功能。。两卡都围绕 AscSqueeze 的掩码筛选与连续排列语义，目标卡记录旧接口退役和迁移入口，焦点卡保留当前不写 AR 的筛选契约，因此属于同一核心接口主题的版本演进。
<!-- cannbot:related:end -->
