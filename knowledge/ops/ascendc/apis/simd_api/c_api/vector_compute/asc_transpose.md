---
type: API
title: AscTranspose
description: 用于实现16*16的二维矩阵数据块转置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_transpose.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscTranspose

用于实现16*16的二维矩阵数据块转置。
函数原型：void asc_transpose(__ubuf__ int16_t* dst, __ubuf__ int16_t* src)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：AscTranspose 与《noTrans extract 与 NDExtLayoutPtn 方向不匹配》的衔接是：AscTranspose 与基础/高阶 Transpose 共享转置数据布局；LoadDataWithTranspose 可作为上游搬运转置，tiling 与 noTrans 布局案例说明方向参数必须一致。
- [AscSetVaReg](asc_set_va_reg.md)（`related`）：“AscSetVaReg”定义：用于设置transpose的16个DataBlock地址，将操作数地址序列与地址寄存器关联，接口要求前8个和后8个地址序列与地址寄存器分别关联。；“AscTranspose”定义：用于实现16*16的二维矩阵数据块转置。。实质衔接：AscSetVaReg 先把 16 个 DataBlock 地址写入 VA 寄存器，随后 C/基础 Transpose 消费这些地址完成 16×16 转置。
- [LoadDataWithTranspose](../../basic_api/cube_compute/cube_compute_load/load_data_with_transpose.md)（`related`）：AscTranspose 与《LoadDataWithTranspose》的衔接是：AscTranspose 与基础/高阶 Transpose 共享转置数据布局；LoadDataWithTranspose 可作为上游搬运转置，tiling 与 noTrans 布局案例说明方向参数必须一致。
- [Transpose](../../adv_api/tensor_transform/transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《AscTranspose》明确提供“用于实现16*16的二维矩阵数据块转置。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [Transpose](../../basic_api/memory_vector_compute/data_layout_conversion/transpose.md)（`same_topic`）：AscTranspose 与《Transpose》的衔接是：AscTranspose 与基础/高阶 Transpose 共享转置数据布局；LoadDataWithTranspose 可作为上游搬运转置，tiling 与 noTrans 布局案例说明方向参数必须一致。
- [Transpose Tiling](../../adv_api/tensor_transform/transpose_tiling.md)（`same_topic`）：AscTranspose 与《Transpose Tiling》的衔接是：AscTranspose 与基础/高阶 Transpose 共享转置数据布局；LoadDataWithTranspose 可作为上游搬运转置，tiling 与 noTrans 布局案例说明方向参数必须一致。
<!-- cannbot:related:end -->
