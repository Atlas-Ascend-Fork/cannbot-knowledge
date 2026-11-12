# 批次不变推理接口

- [SGLang Batch Invariant AddRmsNorm：三返回值与残差边界](sgl_batch_invariant_add_rms_norm.md)：定义add_rms_norm_batch_invariant的残差相加、末维RMS归一化、rstd与residual_out形状及输入不修改契约。
- [SGLang Batch Invariant FIA：OpOverloadPacket、v2参数与图捕获缓冲](sgl_batch_invariant_attention.md)：区分返回OpOverloadPacket的FIA入口和直接执行的FIA v2，列出字段改名、TND长度语义及workspace/output辅助接口。
- [SGLang Batch Invariant Linear Online Max/Sum：词表分片与打包掩码](sgl_batch_invariant_linear_online_max_sum.md)：整理词表并行线性层的六项返回值、本地词表区间和uint8位打包target_mask，限定online统计的逐位比较方式。
- [SGLang Batch Invariant MM/Matmul：矩阵维、广播与转置视图](sgl_batch_invariant_matmul.md)：区分mm_batch_invariant的二维矩阵乘与matmul_batch_invariant的batch广播，明确固定K归约顺序下的逐行一致性及外部实现边界。
- [SGLang Batch Invariant ReduceSum/ReduceMean：单维归约与批维边界](sgl_batch_invariant_reductions.md)：给出reduce_sum_batch_invariant与reduce_mean_batch_invariant的单维参数、输出规则和逐位一致性前提，排除把沿batch归约误当批不变的用法。
- [SGLang Batch Invariant Softmax/LogSoftmax：末维限定与逐行一致性](sgl_batch_invariant_softmax.md)：记录softmax_batch_invariant和log_softmax_batch_invariant只支持最后一维的约束、输入dtype及跨batch逐行对比方法。
