---
type: API
title: Log
description: 对输入张量按元素以e、2或10为底进行对数运算，支持half和float数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Log_interface/Log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Log

按元素做对数运算，提供以e为底（Log）、以2为底（Log2）、以10为底（Log10）三种接口。模板参数T支持half/float。

Log（以e为底）和Log10仅支持接口框架申请临时空间方式，每种区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。Log2额外支持通过sharedTmpBuffer传入临时空间。临时空间大小通过GetLogMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer（仅Log2）为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。
