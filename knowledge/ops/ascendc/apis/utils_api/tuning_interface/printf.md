---
type: API
title: Printf
description: SIMD和SIMT编程调试场景下提供格式化输出功能，在算子Kernel侧打印日志信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/printf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# printf

头文件路径为："utils/debug/asc_printf.h"。

本接口提供SIMD和SIMT编程调试场景下的格式化输出功能。

在算子Kernel侧的实现代码中，需要输出日志信息时，调用printf接口打印相关内容。

> [!CAUTION]注意
>printf接口打印功能会对算子实际运行的性能带来一定影响，通常在调测阶段使用。开发者可以按需通过设置ASCENDC_DUMP=0的方式关闭打印功能。

函数原型：template <class... Args>；__aicore__ static __attribute__((noinline)) void printf( const __gm__ char* fmt, Args&&... args)；template <class... Args> 等6种重载

参数：fmt（输入）：格式控制字符串，包含两种类型的对象：普通字符和转换说明。<br><br>普通字符将原样不动地打印输出。<br>转换说明并不直接输出而是用于控制printf中参数的转换和打印。每个转换说明都由一个百分号字符（%）开始，以转换说明结束，从而说明输出数据的类型。<br>支持的转换类型包括：<br>%d、%ld、%lld、%i、%li、%lli：输出十进制数，支持打印的数据类型：int8_t、int16_t、int32_t、int64_t<br>%f、%F：输出浮点数，支持打印的数据类型：float、half、bfloat16_t<br>%x、%lx、%llx：输出十六进制整数，支持打印的数据类型：int8_t、int16_t、int32_t、int64_t、uint8_t、uint16_t、uint32_t、uint64_t<br>%s：输出字符串<br>%u、%lu、%llu：输出unsigned类型数据，支持打印的数据类型：uint8_t、uint16_t、uint32_t、uint64_t<br>%p：输出指针地址<br><br>注意：上文列出的数据类型是NPU域调试支持的数据类型，CPU域调试时，支持的数据类型和C/C++规范保持一致。；args（输入）：附加参数，个数和类型可变的参数列表：根据不同的fmt字符串，函数可能需要一系列的附加参数，每个参数包含了一个要被插入的值，替换了fmt参数中指定的每个%标签。参数的个数应与%标签的个数相同。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   本接口不支持打印除换行符之外的其他转义字符。

-   SIMT场景的支持情况如下：

    - Ascend 950PR/Ascend 950DT：支持。


    - Atlas A3 训练系列产品/Atlas A3 推理系列产品：不支持。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
