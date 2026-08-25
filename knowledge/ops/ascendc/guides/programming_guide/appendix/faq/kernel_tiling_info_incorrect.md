---
type: Guide
title: kernel侧获取Tiling信息不正确
description: 通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/faq/kernel_tiling_info_incorrect.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# kernel侧获取Tiling信息不正确

## 现象描述
通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。
比如下文样例，增加的打印代码如下：
打印的Tiling数据如下，全为0：
## 问题根因
kernel侧获取Tiling信息不正确的原因一般有以下两种：
-   host侧计算Tiling的逻辑不正确
-   kernel侧核函数的参数未按照正确顺序填写
## 处理步骤
1.  参考如下示例，打印TilingData的数据，确认host侧序列化保存的TilingData是否正确。如果此时打印值有误，说明Tiling的计算逻辑可能不正确，需要进一步检查host侧Tiling实现代码，排查计算逻辑是否有误。
2.  如果上一步骤中打印的TilingData正确，需要排查kernel侧核函数的参数是否按照正确顺序填写。
使用msOpGen工具创建算子工程，并基于工程进行kernel侧算子开发时，核函数的定义模板已通过msOpGen工具自动生成，样例如下所示。参数按照“输入、输出、workspace、tiling”的顺序排布。请检查是否调整过参数顺序导致和正确顺序不一致。

<!-- cannbot:related:start -->
## 相关

- [Kernel Tiling](../../../../apis/simd_api/basic_api/kernel_tiling/kernel_tiling.md)（`explains`）：kernel侧获取Tiling信息不正确说明通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。
- [RegisterNoneTiling](../../../../apis/simd_api/basic_api/kernel_tiling/register_none_tiling.md)（`explains`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《kernel侧获取Tiling信息不正确》补充：通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。
- [NPU域上板调试（功能调试）](../../debug_and_tuning/functional_debug/npu_board_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《kernel侧获取Tiling信息不正确》提供“通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
<!-- cannbot:related:end -->
