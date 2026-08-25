---
type: API
title: GetFmodTmpBufferFactorSize
description: 获取Fmod接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fmod_interface/GetFmodTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetFmodTmpBufferFactorSize

获取Fmod接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetFmodTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Fmod](fmod.md)（`related`）：GetFmodTmpBufferFactorSize 与《Fmod》的实质衔接是：Fmod 的 factor-size、max/min 临时空间、kernel 接口和标量实现共同决定固定 UB 下单次元素数及除零保护。
- [Fmodf](../../../../simt_api/math_functions/float_math_functions/fmodf.md)（`related`）：GetFmodTmpBufferFactorSize 与《Fmodf》的实质衔接是：Fmod 的 factor-size、max/min 临时空间、kernel 接口和标量实现共同决定固定 UB 下单次元素数及除零保护。
- [Fmod接口](fmod_interface.md)（`related`）：GetFmodTmpBufferFactorSize 与《Fmod接口》的实质衔接是：Fmod 的 factor-size、max/min 临时空间、kernel 接口和标量实现共同决定固定 UB 下单次元素数及除零保护。
- [GetFmodMaxMinTmpSize](get_fmod_max_min_tmp_size.md)（`same_topic`）：GetFmodMaxMinTmpSize 的核心契约是“在host侧获取Fmod接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；GetFmodTmpBufferFactorSize 补充“获取Fmod接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。
<!-- cannbot:related:end -->
