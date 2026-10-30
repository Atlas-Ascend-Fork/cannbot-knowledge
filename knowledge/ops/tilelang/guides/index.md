# TileLang 开发指南

- [Chunk GDN/KDA 的任务切分](chunk_gdn_kda_task_partition.md)：说明准备与输出按 chunk 并行、状态更新按 head 分核且核内顺序遍历 chunk。
- [Chunk 下三角矩阵的分块求逆](chunk_triangular_block_inverse.md)：讲解 32 阶 Vector 行递推及 64/128 阶 Cube 块间组合。
- [KDA 的门控分解与数值稳定性](kda_gate_factorization_and_numerical_stability.md)：说明逐通道门控的矩阵乘法分解、子块中点参考及精度安排。
- [Flash Attention 的任务切分与流水排布](flash_attention_task_partition_and_pipeline.md)：说明按 Q 块分核、核内遍历 KV，以及四阶段的三槽连续流水。
