---
type: API
title: GetDequantizeTmpBufferFactorSize
description: 获取Dequantize接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetDequantizeTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# GetDequantizeTmpBufferFactorSize

获取Dequantize接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetDequantizeTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [量化操作](quantization.md)（`related`）：《GetDequantizeTmpBufferFactorSize》说明获取Dequantize接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。；《量化操作》说明量化操作接口导航页，涵盖AscendQuant、AscendDequant、AscendAntiQuant及Quantize系列量化与反量化接口。。二者在Dequantize的factor和最大/最小workspace查询为同一Kernel反推单次处理规模上存在可执行的直接衔接。
- [Dequantize](dequantize.md)（`same_topic`）：Dequantize 与《GetDequantizeTmpBufferFactorSize》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
- [GetDequantizeMaxMinTmpSize](get_dequantize_max_min_tmp_size.md)（`same_topic`）：《GetDequantizeTmpBufferFactorSize》说明获取Dequantize接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。；《GetDequantizeMaxMinTmpSize》说明在host侧获取Dequantize接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。。二者在Dequantize的factor和最大/最小workspace查询为同一Kernel反推单次处理规模上存在可执行的直接衔接。
<!-- cannbot:related:end -->
