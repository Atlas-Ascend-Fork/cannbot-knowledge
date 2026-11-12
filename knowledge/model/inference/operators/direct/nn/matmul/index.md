# 矩阵计算

- [BGMV_EXPAND A3 Direct Invoke 算子知识](sgl_bgmv_expand.md)：说明旧Torch bgmv_expand 的四种rank归约、FP32点积与原地加法、八区UB和直接参数、分核与未校验尾部边界。
- [BGMV_EXPAND 950 Direct Invoke 算子知识](sgl_bgmv_expand_950.md)：说明旧Torch bgmv_expand 的四种rank归约、FP32点积与原地加法、八区UB和直接参数、分核与未校验尾部边界。
- [BGMV_SHRINK A3 Direct Invoke 算子知识](sgl_bgmv_shrink.md)：说明旧Torch bgmv_shrink 的逐适配器FP32缩维、两种X驻留策略、直接参数与UB字节账、分核及元数据与尾部边界。
- [BGMV_SHRINK 950 Direct Invoke 算子知识](sgl_bgmv_shrink_950.md)：说明旧Torch bgmv_shrink 的逐适配器FP32缩维、两种X驻留策略、直接参数与UB字节账、分核及元数据与尾部边界。
- [CATLASS基础矩阵乘 A2/A3 Direct Invoke 算子知识](sgl_matmul_basic.md)：说明 catlass_matmul_basic 的三dtype实例、32B参数、蛇形MN调度、L1/L0双槽与UnitFlag、typed搬运与Fixpipe、真实资源申请和零域边界。
- [SGMV_EXPAND A3 Direct Invoke 算子知识](sgl_sgmv_expand.md)：说明旧Torch sgmv_expand 的四种rank归约、FP32点积与原地加法、八区UB和直接参数、分核与未校验尾部边界。
- [SGMV_EXPAND 950 Direct Invoke 算子知识](sgl_sgmv_expand_950.md)：说明旧Torch sgmv_expand 的四种rank归约、FP32点积与原地加法、八区UB和直接参数、分核与未校验尾部边界。
- [SGMV_SHRINK A3 Direct Invoke 算子知识](sgl_sgmv_shrink.md)：说明旧Torch sgmv_shrink 的逐适配器FP32缩维、两种X驻留策略、直接参数与UB字节账、分核及元数据与尾部边界。
- [SGMV_SHRINK 950 Direct Invoke 算子知识](sgl_sgmv_shrink_950.md)：说明旧Torch sgmv_shrink 的逐适配器FP32缩维、两种X驻留策略、直接参数与UB字节账、分核及元数据与尾部边界。
- [CATLASS softFP8 W8A16分组矩阵乘 A2/A3 Direct Invoke 算子知识](sgl_softfp8_w8a16_grouped_matmul.md)：说明 softfp8_w8a16_grouped_matmul 的128块scale、软件E4M3位解码、BF16 Cube、MIX1:2双槽交接、真实资源和输出/空域边界。
- [CATLASS softFP8 W8A16矩阵乘 A2/A3 Direct Invoke 算子知识](sgl_softfp8_w8a16_matmul.md)：说明 softfp8_w8a16_matmul 的128块scale、软件E4M3位解码、BF16 Cube、MIX1:2双槽交接、真实资源和输出/空域边界。
