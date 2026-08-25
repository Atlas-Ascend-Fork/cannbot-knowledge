---
type: API
title: LogSoftMax接口
description: 提供LogSoftMax激活函数接口及其Tiling接口，用于在Kernel侧完成LogSoftMax计算。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/LogSoftMax_interface/LogSoftMax_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LogSoftMax接口

提供 LogSoftMax 激活函数及其 Tiling 接口，在 Kernel 侧对输入 Tensor 按 last 轴做 LogSoftmax 计算，输出 dst、sum、max 三个结果。计算过程包含 reducemax、broadcast sub、exp、reducesum、broadcast div、log10 等步骤，均在 Vector 上执行。

LogSoftMax 为模板函数，模板参数 `isReuseSource` 预留（传 false），`isDataFormatNZ` 指示源操作数是否为 NZ 格式；支持 half、float 数据类型，last 轴长度需 32Byte 对齐。接口内部需要临时空间，可通过 `sharedTmpBuffer` 传入或由框架申请，空间大小通过 LogSoftMax Tiling 接口获取。

<!-- cannbot:related:start -->
## 相关

- [LogSoftMaxTiling](log_soft_max_tiling.md)（`same_topic`）：LogSoftMaxTiling 的核心契约是“用于在host侧获取LogSoftMax接口所需的最大最小临时空间大小，并计算Tiling参数传递到kernel侧使用”；LogSoftMax接口 补充“提供LogSoftMax激活函数接口及其Tiling接口，用于在Kernel侧完成LogSoftMax计算”。
<!-- cannbot:related:end -->
