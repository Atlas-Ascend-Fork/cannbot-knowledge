---
type: API
title: Rint接口
description: 按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Rint_interface/Rint_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Rint接口

按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。

获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。计算公式如下： 举例如下： Rint(3.9) = 4 Rint(3.3) = 3 Rint(3.5) = 4

本接口组包含 Rint。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscRint](../../../c_api/reg/data_type_convert/asc_rint.md)（`related`）：“Rint接口”定义：按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。；“AscRint”定义：将浮点数按RINT（四舍六入五成双）舍入为整数值，结果保持原浮点类型。。实质衔接：Rint 接口页汇总 kernel 操作与两种临时空间估算；AscRint 提供寄存器 C API 的同一 ties-to-even 数值语义用于实现路径对照。
- [GetRintTmpBufferFactorSize](get_rint_tmp_buffer_factor_size.md)（`related`）：“Rint接口”定义：按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。；“GetRintTmpBufferFactorSize”定义：获取Rint接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。实质衔接：Rint 接口页汇总 kernel 操作与两种临时空间估算；AscRint 提供寄存器 C API 的同一 ties-to-even 数值语义用于实现路径对照。
- [Hrint](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hrint.md)（`related`）：Hrint 与《Rint接口》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Rintf](../../../../simt_api/math_functions/float_math_functions/rintf.md)（`related`）：Rint接口说明按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。
- [GetRintMaxMinTmpSize](get_rint_max_min_tmp_size.md)（`same_topic`）：焦点处理Rint 临时空间上下界与 factor 的配套 Tiling 契约；Rint接口正文说明“按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口”。候选把 host 侧 max/min 查询、factor 推算与 Rint kernel 调用连成同一 Tiling 参数链。
- [Rint](rint.md)（`same_topic`）：“Rint接口”定义：按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。；“Rint”定义：获取与输入数据最接近的整数，等距时取偶数。实质衔接：Rint 接口页汇总 kernel 操作与两种临时空间估算；AscRint 提供寄存器 C API 的同一 ties-to-even 数值语义用于实现路径对照。
<!-- cannbot:related:end -->
