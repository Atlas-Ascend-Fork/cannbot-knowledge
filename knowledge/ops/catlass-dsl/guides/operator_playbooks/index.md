# operator playbooks

原插件 `operator/` 目录整体迁入，收录 CATLASS DSL 各算子实现任务的知识卡。

- [convolution](convolution/index.md)：共 2 张知识卡（如 Causal Conv1d、Causal Conv1d Bwd）。
- [flash attention](flash_attention/index.md)：共 2 张知识卡（如 Flash Attention Backward (FAG / flash_attn_grad)、Flash Attention Inference）。
- [linear attention](linear_attention/index.md)：共 20 张知识卡，分布在 2 个子目录（gdn、kda）。
- [matmul](matmul/index.md)：共 6 张知识卡（如 Batched 与 Grouped Matmul 示例、Basic MMAD 分块、数据类型路由与双缓冲、FusedMatMul 等）。
- [sparse attention](sparse_attention/index.md)：共 6 张知识卡（如 Block Sparse Attention (BSA)、BSA Select Block Mask、Lightning Indexer 等）。
- [vector](vector/index.md)：共 2 张知识卡（如 Basic VADD 数据流、Vector 算子代码模式）。
