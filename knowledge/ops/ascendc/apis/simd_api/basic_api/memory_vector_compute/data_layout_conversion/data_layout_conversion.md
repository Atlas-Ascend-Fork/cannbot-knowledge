---
type: API
title: 数据排布转换
description: 矢量数据排布转换接口集，包含 Transpose、TransDataTo5HD 等数据布局转换接口。
tags: [task.lookup, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_layout_conversion/data_layout_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 数据排布转换

提供 Transpose 和 TransDataTo5HD 两个数据布局转换接口。

Transpose 用于实现 16×16 二维矩阵数据块转置，增强模式还支持 NCHW 与 NHWC 格式互转。TransDataTo5HD 用于将 NCHW 格式转换为 NC1HWC0 格式，也可用于二维矩阵转置；相比 Transpose 仅支持 16×16，TransDataTo5HD 单次 repeat 可处理 512Byte 数据（16 个 DataBlock），支持不同 shape 的矩阵转置和多次 repeat 操作。操作数起始地址需 32Byte 对齐。

<!-- cannbot:related:start -->
## 相关

- [B16 交错 DINTLV 成对归零 — 转 fp32 后重排](../../../../../runbooks/precision/b16_interleave_compute_should_promote_to_b32_layout.md)（`exemplifies`）：数据排布转换 与《B16 交错 DINTLV 成对归零 — 转 fp32 后重排》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：数据排布转换 与《noTrans extract 与 NDExtLayoutPtn 方向不匹配》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：数据排布转换 与《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
- [AIV核上的ND2NZ格式转换](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/aiv_nd2nz_conversion.md)（`explains`）：数据排布转换 与《AIV核上的ND2NZ格式转换》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
- [数据排布格式](../../../../../guides/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md)（`explains`）：数据排布转换 与《数据排布格式》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
- [Transpose](../../../adv_api/tensor_transform/transpose.md)（`related`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《数据排布转换》明确提供“矢量数据排布转换接口集，包含 Transpose、TransDataTo5HD 等数据布局转换接口。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [TransDataTo5HD](trans_data_to5_hd.md)（`same_topic`）：TransDataTo5HD 与《数据排布转换》的实质衔接是：TransDataTo5HD 将张量转为 NC1HWC0；布局转换/格式说明、TransData 与 C API AscTransto5hd共同确定源目格式和对应入口。
- [Transpose](transpose.md)（`same_topic`）：数据排布转换 与《Transpose》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
<!-- cannbot:related:end -->
