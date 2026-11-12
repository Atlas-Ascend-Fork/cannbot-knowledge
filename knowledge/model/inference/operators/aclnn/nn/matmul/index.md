# 矩阵计算

- [BatchMatmulTranspose A2/A3 ACLNN 算子知识](sgl_batch_matmul_transpose.md)：aclnnSglBatchMatmulTranspose 的8个交错批量矩阵乘实例、72字节POD及Cube双缓冲；L0C成员未绑定与单行A对齐读取限制，draft未做运行验证。
- [SgemmcExpand A2/A3 ACLNN 算子知识](sgl_sgemmc_expand.md)：闭合 aclnnSglSgemmcExpand 在 A2/A3 的MIX1:1、CFG_MDL实例、嵌套POD、L1/L0与GM KFC交接及FP32累加RINT；保留固定尾块、实际copy跨度和条件化SDK索引/系统分区风险。
- [SgemmcExpand 950 ACLNN 算子知识](sgl_sgemmc_expand_950.md)：闭合 aclnnSglSgemmcExpand 在 950 的MIX1:1、CFG_MDL实例、嵌套POD、L1/L0与GM KFC交接及FP32累加RINT；保留固定尾块、实际copy跨度和条件化SDK索引/系统分区风险。
- [SgemmcShrink A2/A3 ACLNN 算子知识](sgl_sgemmc_shrink.md)：闭合 aclnnSglSgemmcShrink 在 A2/A3 的MIX1:1与CFG_MDL、嵌套POD、L1/L0/GM KFC及FP32缩放RINT覆盖写；明确rank0先读scale、三UB、固定尾片与条件化系统分区风险。
- [SgemmcShrink 950 ACLNN 算子知识](sgl_sgemmc_shrink_950.md)：闭合 aclnnSglSgemmcShrink 在 950 的MIX1:1与CFG_MDL、嵌套POD、L1/L0/GM KFC及FP32缩放RINT覆盖写；明确rank0先读scale、三UB、固定尾片与条件化系统分区风险。
- [SgemmvExpand A2/A3 ACLNN 算子知识](sgl_sgemmv_expand.md)：闭合 aclnnSglSgemmvExpand 在 A2/A3 的五rank路线、32B POD、FP32归约与原地累加；明确131584B固定UB、漏slice启动和rank8单槽DMA跨度风险，仅作静态draft。
- [SgemmvExpand 950 ACLNN 算子知识](sgl_sgemmv_expand_950.md)：闭合 aclnnSglSgemmvExpand 在 950 的五rank路线、32B POD、FP32归约与原地累加；明确131584B固定UB、漏slice启动和rank8单槽DMA跨度风险，仅作静态draft。
- [SgemmvShrink A2/A3 ACLNN 算子知识](sgl_sgemmv_shrink.md)：闭合 aclnnSglSgemmvShrink 在 A2/A3 的11776元素驻留/分块两路线、36B POD、FP32点积缩放及固定SDK同址ReduceSum；明确固定UB、漏slice启动与未保护整除/元数据边界。
- [SgemmvShrink 950 ACLNN 算子知识](sgl_sgemmv_shrink_950.md)：闭合 aclnnSglSgemmvShrink 在 950 的11776元素驻留/分块两路线、36B POD、FP32点积缩放及固定SDK同址ReduceSum；明确固定UB、漏slice启动与未保护整除/元数据边界。
