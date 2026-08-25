---
type: API
title: Floor接口
description: 按元素向负无穷取整，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Floor_interface/Floor_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Floor接口

按元素向负无穷取整，并提供临时空间大小获取接口。

获取小于或等于x的最小的整数值，即向负无穷取整操作。计算公式如下： 举例如下： Floor(3.9) = 3.0 Floor(-3.9) = -4.0

本接口组包含 Floor。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetFloorMaxMinTmpSize](get_floor_max_min_tmp_size.md)（`related`）：Floor 调用前用该接口计算 workspace 上下界。
- [GetFloorTmpBufferFactorSize](get_floor_tmp_buffer_factor_size.md)（`related`）：固定空间时 factor-size 决定单次可处理元素数。
- [AscFloor](../../../c_api/reg/data_type_convert/asc_floor.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《Floor接口》提供“按元素向负无穷取整，并提供临时空间大小获取接口。”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [Floor](floor.md)（`same_topic`）：函数页是接口总览对应的实际 LocalTensor Floor 调用。
- [Floorf](../../../../simt_api/math_functions/float_math_functions/floorf.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《Floor接口》明确“按元素向负无穷取整，并提供临时空间大小获取接口。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [Hfloor](../../../../simt_api/math_functions/half_type/half_math_functions/hfloor.md)（`same_topic`）：《Hfloor》处理“获取小于或等于输入half数据的最大整数值。”。《Floor接口》明确“按元素向负无穷取整，并提供临时空间大小获取接口。”，可直接用于核对half floor 与 float/half2、Reg/C API、高阶接口的同一取整语义。
<!-- cannbot:related:end -->
