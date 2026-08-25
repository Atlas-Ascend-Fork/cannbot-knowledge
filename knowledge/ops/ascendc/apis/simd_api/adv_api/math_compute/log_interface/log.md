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

<!-- cannbot:related:start -->
## 相关

- [exponential_ 0% 匹配须改 -log(1-u) 路径](../../../../../runbooks/precision/exponential_0_log_1_u.md)（`exemplifies`）：Exponential inverse-CDF 最终调用 Log；输入应是 (0,1] 而非含 0 的 u。
- [AscLog](../../../c_api/vector_compute/asc_log.md)（`related`）：高阶 Log 同样覆盖自然对数，并扩展到 base 2/10 和临时空间管理；AscLog 是 UB 上 half 自然对数的 C API 入口。
- [GetLogMaxMinTmpSize](get_log_max_min_tmp_size.md)（`related`）：GetLogMaxMinTmpSize 返回的区间正用于为 Log/Log2/Log10 执行分配 sharedTmpBuffer；Log 是其直接消费者。
- [Log](../../../basic_api/reg_vector_compute/basic_arithmetic/log.md)（`related`）：两者计算同一自然对数，但分别面向 LocalTensor 高阶接口和 RegTensor VF 接口；Reg 版为无需高阶临时空间的不同实现路径。
- [GetLogTmpBufferFactorSize](get_log_tmp_buffer_factor_size.md)（`same_topic`）：GetLogTmpBufferFactorSize 与《Log》的实质衔接是：Log 的 factor/max-min 查询服务 Log kernel，log2/log10 和 UB 步长故障补充实现与空间约束。
- [Log接口](log_interface.md)（`same_topic`）：总览中的 e/2/10 底数选择、LocalTensor 与 sharedTmpBuffer 约束由 Log 具体接口实现。
<!-- cannbot:related:end -->
