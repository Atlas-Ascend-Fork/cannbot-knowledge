# 950 卷积算子策略

> 目录划分：conv_950 收卷积/反向传播类（Dn2Nz/Load3D/im2col 等）；cv_950 收 Cube-Vector 融合类（MatMul/GEMM/BMM 及后处理融合），两者不是同一类，不能合并。平台 ID 为 950；正文中的 A5 为产品代际别名。

- [成本模型铺核 + 单内核 SyncAll 归约 + tile-B 解耦](cost_model_core_fill_single_kernel_reduce.md)：小 shape 归约/聚合内核用实测成本模型铺核，并以单内核 SyncAll 收口归约、tile-B 解耦降低 halo。
- [fullWidth 整行组 L1 分段 + wsAtomic 单写者协议 + 标量流瘦身（Dn2Nz 事务粒度重组织）](fullwidth_rowgroup_dn2nz_wsatomic_scalar_diet.md)：用 fullWidth 整行组 staging 让 Dn2Nz 恒走单矩阵快路径，配合 wsAtomic 单写者协议与标量流瘦身降低固定税。
- [原语可用性探针 + 零置换代数恒等式 + 反 flop 折半（FFT/复杂数学类算子的工程收敛）](primitive_probe_permutation_free_fft.md)：设计期对候选硬件原语（SinCos/Gather/专用指令）写 20 行级 probe kernel 实测可用性与精度再定禁令；数学结构先 numpy 全形状验证零置换/免转置恒等式（如 Forward=DIF 与 Inverse=镜像共轭 DIT 互为精确逆、转置态跨正逆消费）再写 kernel。
