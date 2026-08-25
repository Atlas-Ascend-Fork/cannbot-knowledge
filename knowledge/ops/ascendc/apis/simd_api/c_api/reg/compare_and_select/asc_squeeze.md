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

- [AscSqueezeAndStoreunalign](../reg_store/asc_squeeze_and_storeunalign.md)（`related`）：AscSqueeze 只在 Reg 中压紧且不保存有效数，Storeunalign 变体同时用 AR 累计长度并连续写 UB，适合需要跨调用非对齐搬出的路径。
- [AscSqueeze](../../vector_compute/asc_squeeze.md)（`same_topic`）：AscSqueeze说明将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
- [AscSqueezeV2](asc_squeeze_deprecated.md)（`same_topic`）：AscSqueeze说明将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
- [AscSqueezeWithStatus](asc_squeeze_with_status_deprecated.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueeze》补充：将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
- [AscUnsqueeze](../data_compress/asc_unsqueeze.md)（`same_topic`）：AscUnsqueeze 与《AscSqueeze》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [Squeeze](../../../basic_api/reg_vector_compute/compare_and_select/squeeze.md)（`same_topic`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《AscSqueeze》补充：将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
<!-- cannbot:related:end -->
