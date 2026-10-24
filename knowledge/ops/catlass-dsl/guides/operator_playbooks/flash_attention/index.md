# flash attention

- [Flash Attention Backward (FAG / flash_attn_grad)](flash_attention_grad.md)：Ascend950 Flash Attention 反向（FAG）在 CATLASS DSL 下的算法、分核、数据路径、流水同步与优化地图，以及重做这个算子时的方向与判据（预算先行、先判绑定管道、flag 台账先行、单轴候选与回退信号；不含逐 case 观测值）；来源只引用 catlass 仓库 catlass-dsl 自身的 kernel/example 与 API，以及固定提交的 ops-transformer 上游实现与设计文档。
- [Flash Attention Inference](flash_attention_infer.md)：Ascend950 Prefill Flash Attention 的 Online Softmax、GQA、tiling、流水和验证边界；含无源码重写骨架、变体派生图谱与实测硬约束。
