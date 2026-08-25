---
type: API
title: Transpose
description: 对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Transpose.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Transpose

对输入数据进行数据排布及Reshape操作。支持多种场景：NZ2ND（1/2轴互换）、NZ2NZ（1/2轴互换）、NZ2NZ（尾轴切分）等。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过Transpose Tiling获取。接口参数：dstTensor输出转置结果；srcTensor输入数据；sharedTmpBuffer临时缓存；transposeInfo含源/目标shape和格式信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《ACLNN 561000 非连续张量需 AutoContiguous》明确提供“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 errno 226808025 并升级为 561000。判别：grep plog 取 226808025/561000，核查 op_host *_def.cpp 的 Input 链是否声明连续性策略；AutoContiguous 是 OpParamDef 方法而非 OpDef 方法。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [Gather 非 last-dim 转置+索引换算预处理占比高](../../../../runbooks/performance/gather_last_dim.md)（`exemplifies`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《Gather 非 last-dim 转置+索引换算预处理占比高》明确提供“Ascend950 上 Gather 算子当 dim != last 时，plugin 端 permute+contiguous 转置与 Cast/Mul/Cast 三段索引 byte-offset 换算合计占 case 总耗时的 58-83%，kernel 本身仅占 17-41%。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../../../../runbooks/compilation/nddma_nddmaconfig_datacopypad.md)（`exemplifies`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》明确提供“Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《noTrans extract 与 NDExtLayoutPtn 方向不匹配》明确提供“aclblasStrsm blocked 路径 noTrans misaligned 尝试 extract A/B 到对齐 workspace 再走 GEMM(transA=0)，extract 行主序存储与 blocked GEMM 的 NDExtLayoutPtn 读取方向不一致致精度大错（outliers 占比 48%~69%）；trans path 靠 transA=1 转置存储恰好匹配而工作；noTrans misaligned 一律回退 SIMT，extract+GEMM 路线 banned。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [NZ2ND](../../basic_api/cube_compute/cube_store_key_features/nz2_nd.md)（`related`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《NZ2ND》明确提供“矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [NZ2NZ](../../basic_api/cube_compute/cube_store_key_features/nz2_nz.md)（`related`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《NZ2NZ》明确提供“矩阵计算的搬出过程中NZ2NZ的核心功能体现为，矩阵计算结果搬出前后保持NZ数据排布不变。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [数据排布转换](../../basic_api/memory_vector_compute/data_layout_conversion/data_layout_conversion.md)（`related`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《数据排布转换》明确提供“矢量数据排布转换接口集，包含 Transpose、TransDataTo5HD 等数据布局转换接口。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [AscTranspose](../../c_api/vector_compute/asc_transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《AscTranspose》明确提供“用于实现16*16的二维矩阵数据块转置。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [LoadDataWithTranspose](../../basic_api/cube_compute/cube_compute_load/load_data_with_transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《LoadDataWithTranspose》明确提供“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [TransData](trans_data.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《TransData》明确提供“将输入数据的排布格式转换为目标排布格式，支持NCDHW与NDC1HWC0、FRACTAL_Z_3D之间的转换。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [Transpose](../../basic_api/memory_vector_compute/data_layout_conversion/transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《Transpose》明确提供“实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [Transpose Tiling](transpose_tiling.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《Transpose Tiling》明确提供“用于获取Transpose Tiling参数。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
<!-- cannbot:related:end -->
