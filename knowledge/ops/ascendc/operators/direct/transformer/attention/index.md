# 注意力直调算子

本目录保存注意力类 Direct Invoke 算子知识。

- [EngramGateFusion A5](engram_gate_fusion_a5.md)：说明状态门控、RMSNorm 与 causal timeline 派生路线。
- [GQA A5](gqa_a5.md)：说明分组查询注意力的 Cube、在线 Softmax 和混合核路线。
- [MHA A5](mha_a5.md)：说明多头注意力的矩阵乘、在线 Softmax 与混合核流水。
- [MLA A5](mla_a5.md)：说明 A5 MLA 的 mask、Cube 矩阵乘、在线 Softmax 与归一化图。
- [MlaProlog A5](mla_prolog_a5.md)：说明 A5 MLA Prolog 的 MIX_CV、Matmul、RMSNorm 与 RoPE 融合路线。
- [SparseFlashAttention A5](sparse_flash_attention_a5.md)：说明稀疏块选择、Cube 矩阵乘与在线 Softmax 路线。
