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

<!-- cannbot:related:start -->
## 相关

- [kernel 源码改动未生效因 binary 缓存](../../../runbooks/compilation/kernel_binary_cache_printf_hash_toggle.md)（`exemplifies`）：当源码修改未进入 device binary hash 时，加入 PRINTF 会改变 binary 并可判别运行时仍加载旧缓存，展示 Printf 的另一诊断用途。
- [双 VF 融合输出非预期 先排 CopyOut slot 勿用 PRINTF](../../../runbooks/precision/vf_fusion_output_unexpected_check_copyout_slot_not_printf.md)（`exemplifies`）：该 runbook 明确说明 VF 融合异常时 device PRINTF 不稳定，先用 host copyout/slot 映射核对数据链，给出 Printf 的调试边界。
- [NPU域上板调试（功能调试）](../../../guides/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《Printf》提供“SIMD和SIMT编程调试场景下提供格式化输出功能，在算子Kernel侧打印日志信息。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [核函数运行验证时算子存在精度问题](../../../guides/programming_guide/appendix/faq/kernel_precision_issue.md)（`explains`）：FAQ 明确把 printf 数值打印作为定位 tileLength、LocalTensor 大小和中间值的手段；目标卡给出可调用接口。
- [printf（AI CPU API）](../../ai_cpu_api/printf.md)（`related`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；Printf正文界定“SIMD和SIMT编程调试场景下提供格式化输出功能，在算子Kernel侧打印日志信息”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
<!-- cannbot:related:end -->
