---
type: API
title: Histograms
description: 对直方图数据进行统计，在目的寄存器原始数据上累加源寄存器数据的频率统计或累计统计结果。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/histogram_compute/Histograms.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Histograms

头文件路径为："basic_api/reg_compute/kernel_reg_compute_histograms_intf.h"。

对直方图数据进行统计，在目的操作数dstReg的基础数据上加上源操作数srcReg数据的统计结果，包括数据的频率统计和累计统计。

- 频率统计
    如下图所示，在低位模式下，dstReg用于统计srcReg中index为[0-127]范围内（前半部分）各个值的出现频率；而在高位模式下，dstReg则统计[128-255]范围内（后半部分）的频率。dstReg中的第n位（bit）表示srcReg中数值n的出现次数，并在原始dstReg数据的基础上进行累加。

- 累计统计
    如下图所示，在低位模式下，目的寄存器dstReg会统计源寄存器srcReg中值落在低位区间[0-127]的数据分布情况；在高位模式下，目的寄存器dstReg则会统计srcReg中值落在高位区间[128-255]的数据分布情况。dstReg中的第n个元素表示srcReg中从0到n的所有数值在对应区间中出现的总频率。最终，统计结果会在目的寄存器原始数据的基础上进行累加。

参数：T: 源操作数的数据类型。；U: 目的操作数的数据类型。；mode: HistogramsBinType枚举类型，用于选择统计srcReg的低位区间或高位区间。Histograms将uint8_t类型srcReg的[0, 255]取值范围划分为低位、高位两个区间；每个区间包含128个取值，对应uint16_t类型dstReg在一个VL（256Byte）内可保存的128个统计结果。单次调用只统计其中一个区间，并将该区间的统计结果写入传入的dstReg。若需要获得完整[0, 255]范围的统计结果，需要分别以BIN0和BIN1调用两次接口，并使用两个目的寄存器保存结果，例如dst0保存低位区间结果，dst1保存高位区间结果。 • BIN0：统计srcReg中[0, 127]范围内的数据，结果写入传入的dstReg。 • BIN1：统计srcReg中[128, 255]范围内的数据，结果写入传入的dstReg。；type: HistogramsType 枚举类型，表示统计模式。 • FREQUENCY：频率统计模式，统计srcReg中[0, 255]每个数的数量。每个dst有128个元素，其中低位模式dstReg中每个元素对应src中[0, 127]每个元素的累加个数，高位模式dstReg中每个元素对应src中[128,255]每个元素的累加个数。 • ACCUMULATE：累计统计模式，统计srcReg中[0, 255]每个数及其之前出现数的数量总和。每个dst有128个元素，其中低位模式dstReg中每个元素对应src中[0, 127]每个元素区间累加个数，高位模式dstReg中每个元素对应src中[128,255]每个元素区间累加个数。；S: 源操作数RegTensor类型，由编译器自动推导，用户不需要填写。；V: 目的操作数RegTensor类型，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。

约束：- 当mask位数为0时，对应位置的src源操作数的数值被忽略，dst对应位置数值为忽略该位置src后计算得到的值。
- dst的数据类型为uint16_t，最大值为65535，使用时需注意累加溢出问题。

仅 Ascend 950PR/Ascend 950DT 支持。
