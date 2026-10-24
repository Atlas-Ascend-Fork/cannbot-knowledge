# matmul

- [Batched 与 Grouped Matmul 示例](advanced_matmul.md)：端到端 batched matmul 与按 M 切片 grouped matmul 的动态 GM 和任务映射边界。
- [Basic MMAD 分块、数据类型路由与双缓冲](basic_mmad.md)：GM-L1-L0 分层、动态 tiling、FP/BF16/FP8/INT8/HF32 路由及 K 循环双缓冲模式。
- [FusedMatMul](fused_mat_mul.md)：Ascend 950 FusedMatMul 的矩阵乘后处理融合、调度模型、数据路径与同步语义。
- [MatMul](mat_mul.md)：Ascend 950 MatMul 的调度分派、基本块切分、Stream-K、全载与 Fixpipe 数据路径。
- [Mixed、atomic add 与 mutex 变体](mixed_and_sync_variants.md)：Cube/Vector 混合流水、跨核 flag、atomic add 和 mutex 的源码样例入口。
- [QuantBatchMatmul](quant_batch_matmul.md)：Ascend 950 QuantBatchMatmul 的量化模式分派、AIC/AIV 协同、尺度数据路径与精度约束。
