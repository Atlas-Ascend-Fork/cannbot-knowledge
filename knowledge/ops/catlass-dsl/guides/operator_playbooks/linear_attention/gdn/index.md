# gdn

- [Chunk Bwd Dqkwg](chunk_bwd_dqkwg.md)：Gated Delta Rule 的 DQ/DK/DW/DG 混合反向核，包含四阶段信用流水、workspace 环和可证伪优化路径。
- [Chunk Bwd Dv Local](chunk_bwd_dv_local.md)：分块门控 Delta Rule 反向的块内 Value 梯度核。
- [Chunk Fwd O](chunk_fwd_o.md)：分块门控 Delta Rule 前向输出阶段的矩阵乘与融合后处理核。
- [Chunk Gated Delta Rule](chunk_gated_delta_rule.md)：Ascend 950 Chunk Gated Delta Rule 的三阶段分块算法、workspace 数据路径、Cube/Vector 协同和精度边界。
- [Chunk Gated Delta Rule Bwd Dhu](chunk_gated_delta_rule_bwd_dhu.md)：门控 Delta Rule 的反向状态链 mixed kernel，覆盖四 head window、八槽 workspace、A5 直达 UB 和当前接口漂移。
- [Chunk Gated Delta Rule Fwd H](chunk_gated_delta_rule_fwd_h.md)：分块门控 Delta Rule 的跨 chunk 隐藏状态传播核。
- [Chunk Local Cumsum](chunk_local_cumsum.md)：按 chunk 重置的局部门控前缀和向量核。
- [Chunk Scaled Dot Kkt](chunk_scaled_dot_kkt.md)：按 chunk 计算缩放 Key-Key 转置乘积的矩阵核。
- [Prepare Wy Repr Bwd](prepare_wy_repr_bwd.md)：Gated Delta Rule 的融合 WY 表示反向核，覆盖 dA 构造、四个输出、head 复用、四槽 workspace 和 mixed 流水。
- [Prepare Wy Repr Bwd Da](prepare_wy_repr_bwd_da.md)：WY 表示反向中计算块内 A 矩阵梯度的混合核。
- [Prepare Wy Repr Bwd Full](prepare_wy_repr_bwd_full.md)：WY 表示反向中联合生成 K、V、beta 与中间分支梯度的混合核。
- [Recompute W U Fwd](recompute_w_u_fwd.md)：门控 Delta Rule 前向重计算 W/U 表示的混合核。
- [Recurrent Gated Delta Rule](recurrent_gated_delta_rule.md)：Ascend 950 Recurrent Gated Delta Rule 的逐 token 状态更新、变长分核、UB 数据路径和 VF 数值策略。
- [Solve Tri](solve_tri.md)：分块线性注意力中下三角矩阵求逆核。
