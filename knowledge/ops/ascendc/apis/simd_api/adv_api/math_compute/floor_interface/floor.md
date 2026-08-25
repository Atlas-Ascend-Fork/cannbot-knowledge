---
type: API
title: Floor
description: 获取小于或等于x的最小整数值，即向负无穷取整
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Floor_interface/Floor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Floor

获取小于或等于x的最小整数值，即向负无穷取整操作（Floor(3.9)=3.0, Floor(-3.9)=-4.0）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetFloorMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int32](../../../c_api/scalar_compute/asc_float2int32.md)（`related`）：AscFloat2Int32 与《Floor》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [Ceil](../ceil_interface/ceil.md)（`related`）：Ceil 与《Floor》的实质衔接是：Ceil kernel 依赖两种临时空间查询，C API 是对应入口，Floor 提供相反取整边界；多核尾块卡直接验证 remaining 计数错误。
- [GetFloorTmpBufferFactorSize](get_floor_tmp_buffer_factor_size.md)（`related`）：Floor 的显式 sharedTmpBuffer 重载直接消费 Host 侧预算；FactorSize 用于在 UB 已知时反推可处理规模，最终仍需满足 Floor 的不重叠和输入值域约束。
- [AscFloat2float](../../../c_api/vector_compute/asc_float2float.md)（`same_topic`）：AscFloat2float 与《Floor》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [AscFloor](../../../c_api/reg/data_type_convert/asc_floor.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《Floor》提供“获取小于或等于x的最小整数值，即向负无穷取整”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [Floorf](../../../../simt_api/math_functions/float_math_functions/floorf.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《Floor》明确“获取小于或等于x的最小整数值，即向负无穷取整”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [Floor接口](floor_interface.md)（`same_topic`）：函数页是接口总览对应的实际 LocalTensor Floor 调用。
- [GetFloorMaxMinTmpSize](get_floor_max_min_tmp_size.md)（`same_topic`）：GetFloorMaxMinTmpSize 与《Floor》的实质衔接是：该 host 查询给 Floor 高阶接口分配最大/最小临时空间，factor 查询再把选定空间换算为 kernel 单次处理量。
- [H2Floor](../../../../simt_api/math_functions/bfloat16_type/bfloat16x2_math_functions/h2floor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《Floor》提供“获取小于或等于x的最小整数值，即向负无穷取整”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [Hfloor](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hfloor.md)（`same_topic`）：Hfloor 与《Floor》的实质衔接是：Hfloor 对 bfloat16 向负无穷取整；half/packed/float、Hceil/Hrint/Htrunc 和 Tensor/Reg Floor 入口直接对照类型及舍入方向。
- [Hfloor](../../../../simt_api/math_functions/half_type/half_math_functions/hfloor.md)（`same_topic`）：《Hfloor》处理“获取小于或等于输入half数据的最大整数值。”。《Floor》明确“获取小于或等于x的最小整数值，即向负无穷取整”，可直接用于核对half floor 与 float/half2、Reg/C API、高阶接口的同一取整语义。
<!-- cannbot:related:end -->
