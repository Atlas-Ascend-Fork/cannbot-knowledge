---
type: API
title: Round
description: 将输入元素四舍五入到最接近的整数，小数部分为0.5时向偶数舍入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Round_interface/Round.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Round

将输入元素四舍五入到最接近的整数（Round(3.5)=4.0, Round(-3.4)=-3.0），若恰好在两个整数中间（小数部分为0.5）则向偶数舍入。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRoundMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；srcTensor为输入操作数，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：只支持四舍五入到整数，不支持到小数，小数部分为0.5时向偶数舍入；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int32](../../../c_api/scalar_compute/asc_float2int32.md)（`related`）：AscFloat2Int32 与《Round》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [GetRoundTmpBufferFactorSize](get_round_tmp_buffer_factor_size.md)（`related`）：Round：Round 的 kernel 调用直接依赖同名临时空间接口；AscRound/Roundf提供不同编程模型下相同 ties-to-even 语义的对照。 目标卡《GetRoundTmpBufferFactorSize》补充：获取Round接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
- [Lroundf](../../../../simt_api/math_functions/float_math_functions/lroundf.md)（`related`）：Lroundf 与《Round》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [Roundf](../../../../simt_api/math_functions/float_math_functions/roundf.md)（`related`）：Round：Round 的 kernel 调用直接依赖同名临时空间接口；AscRound/Roundf提供不同编程模型下相同 ties-to-even 语义的对照。 目标卡《Roundf》补充：获取对输入数据四舍五入后的整数。
- [AscFloat2float](../../../c_api/vector_compute/asc_float2float.md)（`same_topic`）：AscFloat2float 与《Round》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [AscRound](../../../c_api/reg/data_type_convert/asc_round.md)（`same_topic`）：AscRound 与《Round》的实质衔接是：AscRound 采用 ties-away 的 ROUND 语义，舍入模式页与 AscRint 的 ties-to-even 形成直接对照；高阶 Round 和 SIMT roundf 是同一取整任务在 Tensor 与线程标量层的入口。
- [GetRoundMaxMinTmpSize](get_round_max_min_tmp_size.md)（`same_topic`）：Round 的临时空间需在 Host 侧用 GetRoundMaxMinTmpSize 计算并随 tiling 传入。
- [Round接口](round_interface.md)（`same_topic`）：Round：Round 的 kernel 调用直接依赖同名临时空间接口；AscRound/Roundf提供不同编程模型下相同 ties-to-even 语义的对照。 目标卡《Round接口》补充：按元素四舍五入到最接近的整数，并提供临时空间大小获取接口。
<!-- cannbot:related:end -->
