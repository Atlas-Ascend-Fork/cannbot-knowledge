---
type: API
title: AdjustSoftMaxRes
description: 调整SoftMax计算结果为指定值，当maxTensor中存在指定值时，按行将对应softMaxRes结果替换为自定义值，用于SoftMax后处理。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/AdjustSoftMaxRes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# AdjustSoftMaxRes

本接口用于调整SoftMax的计算结果为指定的值。主要用于对SoftMax相关计算结果做后处理。当输入的max中存在指定的值的时候，会调整对应的softmaxres中的结果为输入的自定义的值。以上调整方式为按行进行，即当max某一行的值为某个值时，调整当前softmaxres对应一行的值都为输入的值。 为方便理解，通过Python脚本实现的方式，表达其计算公式如下，其中res是输入也是输出，，max\\from\\to\\res_shape都为输入。

函数原型：template <typename T1, typename T2, bool isDataFormatNZ = false, uint8_t stepSizeMode = 0>

参数：
- T1：softMaxRes的数据类型。支持的数据类型为：half、float。
- T2：maxTensor的数据类型。支持的数据类型为：half、float。
- isDataFormatNZ：当前输入输出的数据格式是否为NZ格式，默认数据格式为ND，即默认取值为false。
约束：
- 操作数地址对齐要求请参见通用地址对齐约束。
- 当参数softmaxShapeInfo中srcM != oriSrcM或者srcK != oriSrcK时，开发者需要对GM上的原始输入(oriSrcM, oriSrcK\)在M或K方向补齐数据到\(srcM, srcK\)，补齐的数据会参与部分运算，在输入输出复用的场景下，API的计算结果会覆盖srcTensor中补齐的原始数据，在输入输出不复用的场景下，API的计算结果会覆盖dstTensor中对应srcTensor补齐位置的数据。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。
