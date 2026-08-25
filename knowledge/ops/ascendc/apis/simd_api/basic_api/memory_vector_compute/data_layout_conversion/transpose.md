---
type: API
title: Transpose
description: 实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_layout_conversion/Transpose.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Transpose

实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。

Transpose接口用于实现16*16的二维矩阵数据块转置或者[N,C,H,W]与[N,H,W,C]数据格式互相转换。 16*16的普通转置接口计算原理和参考伪代码如下： [N,C,H,W]与[N,H,W,C]数据格式互相转换的增强转置计算原理和参考伪代码如下：

本接口属于 UB 矢量计算数据排布转换接口。

参数说明：T：操作数的数据类型。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。 数据类型需要与dst保持一致。；sharedTmpBuffer：输入 共享的临时Buffer，sharedTmpBuffer的大小参考[表sharedTmpBuffer所需的内存](#table4)。；transposeParams：输入 控制Transpose的数据结构。结构体内包含：输入的shape信息和transposeType参数。该数据结构的定义请参考[表TransposeParamsExt结构体内参数说明](#table3)。 struct TransposeParamsExt {     __aicore__ TransposeParamsExt() {}     __aicore__ TransposeParamsExt(const uint16_t nSizeIn, const uint16_t cSizeIn, const uint16_t hSizeIn,         const uint16_t wSizeIn, const TransposeType transposeTypeIn)         : nSize(nSizeIn),           cSize(cSizeIn),           hSize(hSizeIn),           wSize(wSizeIn),           transposeType(transposeTypeIn)     {}     uint16_t nSize = 0;     uint16_t cSize = 0;     uint16_t hSize = 0;     uint16_t wSize = 0;     TransposeType transposeType = TransposeType::TRANSPOSE_ND2ND_B16; };

返回值：无。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《Transpose》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [AscSetVaReg](../../../c_api/vector_compute/asc_set_va_reg.md)（`related`）：“AscSetVaReg”定义：用于设置transpose的16个DataBlock地址，将操作数地址序列与地址寄存器关联，接口要求前8个和后8个地址序列与地址寄存器分别关联。；“Transpose”定义：实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。。实质衔接：AscSetVaReg 先把 16 个 DataBlock 地址写入 VA 寄存器，随后 C/基础 Transpose 消费这些地址完成 16×16 转置。
- [AscTranspose](../../../c_api/vector_compute/asc_transpose.md)（`same_topic`）：AscTranspose 与《Transpose》的衔接是：AscTranspose 与基础/高阶 Transpose 共享转置数据布局；LoadDataWithTranspose 可作为上游搬运转置，tiling 与 noTrans 布局案例说明方向参数必须一致。
- [Transpose](../../../adv_api/tensor_transform/transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《Transpose》明确提供“实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [数据排布转换](data_layout_conversion.md)（`same_topic`）：数据排布转换 与《Transpose》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
<!-- cannbot:related:end -->
