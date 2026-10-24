# sparse attention

- [Block Sparse Attention (BSA)](block_sparse_attention.md)：Ascend 950 BSA 从零生成时强制采用 mixed Cube/Vector 流水，逐阶段对照 AscendC regular 实现，并审计批准接口与骨架 ABI。
- [Block Sparse Attention Grad (BSAG)](block_sparse_attention_grad/index.md)：Ascend 950 Arc35 Block Sparse Attention 反向主路径：以 blockSparseMask 为唯一稀疏元数据， 重算被选稀疏块的 score 与概率，五路 MMAD 产出 dQ/dK/dV。dQ 每个 task 原子加到 FP32 workspace；dK/dV 在同一 KV 块内跨 task 在 L0C 累加、换块时一次原子写出。统合 BSND、BNSD、 TND 三种 layout 的 stride 寻址与 TND 累计长度，覆盖 GQA/MQA 的 Q-head 到 KV-head 映射和 共享 dK/dV 所有权。非确定性路径由 host NonZero 预 kernel 生成有效块下标列表、kernel 按 列表取块并把 Q/K/V/dY 做三槽轮转预取；确定性路径用 latin-square 顺序直接读 mask。同一 kernel 的 constexpr 分支覆盖 FP16/BF16 与 1000..1005/1008..1013 两族 tiling key。文末 「扩展层」记录细 token mask 与 head_dim 32/64 两个实现侧变体的出处与边界。（共 2 张知识卡：Block Sparse Attention Grad Sink）
- [BSA Select Block Mask](bsa_select_block_mask.md)：Ascend 950 BSA 稀疏掩码选择的池化、QK、两遍 Online Softmax、Radix TopK 与 AIC/AIV 同步。
- [Lightning Indexer](lightning_indexer.md)：Ascend 950 Lightning Indexer 的 QK 分块、ReLU 加权归约、流式 TopK、PagedAttention 寻址和 C/V 流水。
- [Sparse Flash Attention Grad Arc35](sparse_flash_attention_grad.md)：topk 稀疏注意力反向（SFAG）：逐行 gather 选中 KV、五路加两路 rope MMAD、一轮延迟的 AIC/AIV 流水、位置序 scratch 加 token 行原子散写。
