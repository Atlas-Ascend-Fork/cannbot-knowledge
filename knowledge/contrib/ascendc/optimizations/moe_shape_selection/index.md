# MoE Shape 选择

MoE 算子的 shape/负载参数（tok/expert、填充率等）与性能关系的实测经验。

## 知识卡

- [MoE 分组 GEMM：L1 读带宽利用率由【每专家 token 数】驱动，不由填充率驱动](tokens_per_expert_drives_l1_bandwidth.md)：arch22 融合 MoE 实测，aic_l1_read_bw 单调于 tok/expert 而非填充率。
