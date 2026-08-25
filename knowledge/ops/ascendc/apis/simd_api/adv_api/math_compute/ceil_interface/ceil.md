---
type: API
title: Ceil
description: 获取大于或等于输入值的最小整数，即向正无穷方向取整
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Ceil_interface/Ceil.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Ceil

获取大于或等于x的最小的整数值，即向正无穷取整操作。计算公式如下： 举例如下： Ceil(3.9) = 4.0

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Ceil(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Ceil内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetCeilMaxMinTmpSize。

约束：
- 针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [多核 ceil 尾块为负 — 每核按 remaining 截断](../../../../../runbooks/precision/ceil_partition_each_core_must_clamp_remaining.md)（`exemplifies`）：Ceil 与《多核 ceil 尾块为负 — 每核按 remaining 截断》的实质衔接是：Ceil kernel 依赖两种临时空间查询，C API 是对应入口，Floor 提供相反取整边界；多核尾块卡直接验证 remaining 计数错误。
- [AscCeil](../../../c_api/reg/data_type_convert/asc_ceil.md)（`related`）：Ceil 与《AscCeil》的实质衔接是：Ceil kernel 依赖两种临时空间查询，C API 是对应入口，Floor 提供相反取整边界；多核尾块卡直接验证 remaining 计数错误。
- [AscFloat2Int32](../../../c_api/scalar_compute/asc_float2int32.md)（`related`）：AscFloat2Int32 与《Ceil》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [Floor](../floor_interface/floor.md)（`related`）：Ceil 与《Floor》的实质衔接是：Ceil kernel 依赖两种临时空间查询，C API 是对应入口，Floor 提供相反取整边界；多核尾块卡直接验证 remaining 计数错误。
- [AscFloat2float](../../../c_api/vector_compute/asc_float2float.md)（`same_topic`）：AscFloat2float 与《Ceil》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [Ceil接口](ceil_interface.md)（`same_topic`）：《Ceil接口》说明提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。；《Ceil》说明获取大于或等于输入值的最小整数，即向正无穷方向取整。二者在Ceil计算、临时空间估算与多核尾段切分共同决定向上取整算子的正确执行上存在可执行的直接衔接。
- [GetCeilMaxMinTmpSize](get_ceil_max_min_tmp_size.md)（`same_topic`）：Ceil 与《GetCeilMaxMinTmpSize》的实质衔接是：Ceil kernel 依赖两种临时空间查询，C API 是对应入口，Floor 提供相反取整边界；多核尾块卡直接验证 remaining 计数错误。
- [GetCeilTmpBufferFactorSize](get_ceil_tmp_buffer_factor_size.md)（`same_topic`）：GetCeilTmpBufferFactorSize 与《Ceil》的实质衔接是：factor 查询与 GetCeilMaxMinTmpSize 共同换算 Ceil 单次元素数，Ceil/C API 是消费端；tmpBuffer 步长故障直接验证空间公式错误会造成 UB 越界。
<!-- cannbot:related:end -->
