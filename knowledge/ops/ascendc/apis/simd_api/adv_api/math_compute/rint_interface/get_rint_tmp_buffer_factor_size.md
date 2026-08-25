---
type: API
title: GetRintTmpBufferFactorSize
description: 获取Rint接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Rint_interface/GetRintTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetRintTmpBufferFactorSize

获取Rint接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetRintTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Hrint](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hrint.md)（`related`）：Hrint 与《GetRintTmpBufferFactorSize》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Rint接口](rint_interface.md)（`related`）：“Rint接口”定义：按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。；“GetRintTmpBufferFactorSize”定义：获取Rint接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。实质衔接：Rint 接口页汇总 kernel 操作与两种临时空间估算；AscRint 提供寄存器 C API 的同一 ties-to-even 数值语义用于实现路径对照。
- [GetRintMaxMinTmpSize](get_rint_max_min_tmp_size.md)（`same_topic`）：焦点处理Rint 临时空间上下界与 factor 的配套 Tiling 契约；GetRintTmpBufferFactorSize正文说明“获取Rint接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。候选把 host 侧 max/min 查询、factor 推算与 Rint kernel 调用连成同一 Tiling 参数链。
- [Rint](rint.md)（`same_topic`）：GetRintTmpBufferFactorSize说明获取Rint接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。
<!-- cannbot:related:end -->
