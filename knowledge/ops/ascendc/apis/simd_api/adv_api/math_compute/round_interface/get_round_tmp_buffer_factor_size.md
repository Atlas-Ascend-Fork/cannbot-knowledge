---
type: API
title: GetRoundTmpBufferFactorSize
description: 获取Round接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Round_interface/GetRoundTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetRoundTmpBufferFactorSize

获取Round接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetRoundTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Lroundf](../../../../simt_api/math_functions/float_math_functions/lroundf.md)（`related`）：Lroundf 与《GetRoundTmpBufferFactorSize》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [Round](round.md)（`related`）：Round：Round 的 kernel 调用直接依赖同名临时空间接口；AscRound/Roundf提供不同编程模型下相同 ties-to-even 语义的对照。 目标卡《GetRoundTmpBufferFactorSize》补充：获取Round接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
- [GetRoundMaxMinTmpSize](get_round_max_min_tmp_size.md)（`same_topic`）：GetRoundMaxMinTmpSize说明在host侧获取Round接口预留或申请临时空间的最大和最小值，用于Tiling参数传递。
- [Round接口](round_interface.md)（`same_topic`）：Round接口说明按元素四舍五入到最接近的整数，并提供临时空间大小获取接口。
<!-- cannbot:related:end -->
