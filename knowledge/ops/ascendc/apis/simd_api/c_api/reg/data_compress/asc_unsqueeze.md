---
type: API
title: AscUnsqueeze
description: 根据掩码对矢量数据进行解压缩，dst各元素值取决于mask中前序元素为1的数量
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_unsqueeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscUnsqueeze

将dst中数据根据mask进行解压缩。解压缩方式：dst中第0个元素置为0，dst中的第i个元素等于mask中从第0个到第(i-1)个元素中1的数量。mask最高位被忽略不参与统计。
具体算法如图1所示，dst的首位为0，后续mask[i]对应mask值为1时，dst[i]的值为dst[i-1] + 1；mask[i]对应mask值为0时，dst[i]的值为dst[i-1]。

参数：dst(输入/输出): 源操作数和目的操作数（矢量数据寄存器）。；mask(输入): 源操作数（掩码寄存器），用于提供dst解压缩信息。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscPackToHigh](asc_pack_to_high.md)（`same_topic`）：AscUnsqueeze 与《AscPackToHigh》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [AscPackToLow](asc_pack_to_low.md)（`same_topic`）：AscUnsqueeze 与《AscPackToLow》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [AscSqueeze](../compare_and_select/asc_squeeze.md)（`same_topic`）：AscUnsqueeze 与《AscSqueeze》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [AscUnpack](asc_unpack.md)（`same_topic`）：AscUnsqueeze 与《AscUnpack》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [Squeeze](../../../basic_api/data_structure_tensor_api/layout_structure/squeeze.md)（`same_topic`）：AscUnsqueeze 与《Squeeze》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [Unsqueeze](../../../basic_api/reg_vector_compute/data_compression/unsqueeze.md)（`same_topic`）：AscUnsqueeze 与《Unsqueeze》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
<!-- cannbot:related:end -->
