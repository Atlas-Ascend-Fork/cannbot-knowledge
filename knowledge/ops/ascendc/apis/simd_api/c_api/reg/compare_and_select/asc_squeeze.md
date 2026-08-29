---
type: API
title: AscSqueeze
description: 将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_squeeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscSqueeze

将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。

本接口不会将有效数据大小保存至AR寄存器。如果需要筛选有效元素并将其连续搬出至UB。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、hifloat8_t、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：dst中未被mask筛选的位置被置为0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSqueeze](../../vector_compute/asc_squeeze.md)（`same_topic`）：通过比较掩码src1，将src0中的向量压缩成更短的向量，存储到dst中；将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。两卡都按 mask 压缩有效元素；焦点是 A2/A3 UB 三地址形式，候选是 950 Reg+MaskReg 形式并明确剩余位置清零。
- [AscSqueezeV2](asc_squeeze_deprecated.md)（`same_topic`）：将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。；该接口已废弃，请使用asc_squeeze_and_storeunalign实现筛选并连续搬出有效元素的功能。。两卡都围绕 AscSqueeze 的掩码筛选与连续排列语义，目标卡记录旧接口退役和迁移入口，焦点卡保留当前不写 AR 的筛选契约，因此属于同一核心接口主题的版本演进。
<!-- cannbot:related:end -->
