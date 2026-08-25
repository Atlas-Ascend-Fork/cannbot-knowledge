---
type: API
title: DumpTensor
description: 打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/onboard_print/DumpTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DumpTensor

打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。

该接口可以打印Tensor的内容，同时支持打印自定义的标签（仅支持uint32_t数据类型的信息），比如打印当前行号等。 在算子kernel侧实现代码中需要打印Tensor数据的地方，调用DumpTensor接口打印相关内容。样例如下： > [!CAUTION]注意 > 该接口主要用于调试分析，开启后会对算子性能产生一定影响，通常在调试阶段使用，生产环境建议关闭。 > 默认情况下，调用该接口就会打印相关内容，开发者可以参考关闭ASCENDC_DUMP说明，按需关闭该接口功能。 打印示例如下：

参数说明：T：需要dump的Tensor的数据类型。；tensor：输入 需要dump的Tensor。 •待dump的tensor位于Unified Buffer/L1 Buffer/L0C Buffer时使用LocalTensor类型的tensor参数输入。 •待dump的tensor位于Global Memory时使用GlobalTensor类型的tensor参数输入。；desc：输入 用户自定义附加信息（行号或其他自定义数字）。 在使用DumpTensor功能时，用户可通过desc参数附加自定义信息，以便在不同场景下区分Dump内容的来源。此功能有助于精准定位具体DumpTensor的输出，提升调试与分析效率。；dumpSize：输入 需要dump的元素个数。；shapeInfo：输入 传入Tensor的shape信息，可按照shape信息进行打印。 •当Shape尺寸大于dumpSize元素个数时，按照ShapeInfo打印元素，不足的Dump数据用"-"展示。 •当Shape尺寸小于等于dumpSize元素个数时，按照ShapeInfo打印元素，多出的Dump数据不展示。

约束：当前支持打印存储位置为Unified Buffer/L1 Buffer/L0C Buffer/Global Memory的Tensor信息。；在Ascend 950PR/Ascend 950DT下新增BiasTable Buffer和Fixpipe Buffer的Tensor数据打印。；针对Ascend 950PR/Ascend 950DT，使用该接口打印L1 Buffer、BiasTable Buffer或Fixpipe Buffer数据时，HDK版本需要至少升级到25.7.0以上。；针对Ascend 950PR/Ascend 950DT，打印Fixpipe Buffer中的Tensor信息场景：
