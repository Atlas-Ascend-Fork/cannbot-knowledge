# kda

- [Chunk Gated Delta Rule Fwd H](chunk_gated_delta_rule_fwd_h.md)：64x64 chunk gated delta rule recurrent FwdH 的 CATLASS DSL 单 launch task-loop mixed kernel，涵盖 task-major host packing、AIC/AIV 片上交接、状态链和负载均衡诊断。
- [Chunk Kda Bwd Intra](chunk_kda_bwd_intra.md)：KDA 块内 Q/K/gate/beta 梯度修正 mixed kernel，包含三角打包、四槽交接、head-window 流水和调优判据。
- [Chunk Kda Fwd](chunk_kda_fwd.md)：KDA 分块前向的五阶段 mixed kernel，包含 A5 融合选择、状态链、workspace 生命周期与分阶段优化方法。
- [Kda Gate Cumsum](kda_gate_cumsum.md)：KDA gate 激活与 chunk 内累计和向量核，包含 dense/varlen 分核、A5 快路径及可执行调优判据。
- [Recompute W U Fwd](recompute_w_u_fwd.md)：KDA recompute_w_u_fwd 的 C310 mixed kernel：每个 64-token chunk 同时重算 w、u、qg 与 kg，并以 AIV UB→AIC L1 交接合并两路 MMAD。
- [Recurrent Kda](recurrent_kda.md)：Decode/MTP KDA 的 AIV-only 递推核，包含状态切片、UB 队列选择、低并发诊断和优化门禁。
