# MHC ACLNN 算子

本目录保存 MHC 类 ACLNN 算子知识。

- [MhcPost A2/A3](mhc_post.md)：MhcPost 算子在 A2/A3 平台的 ACLNN 实现，用于融合 MHC 多头隐状态与残差后处理。
- [MhcPost A5](mhc_post_a5.md)：MhcPost 算子在 A5 平台的 ACLNN 实现，用于融合 MHC 多头隐状态与残差后处理。
- [MhcPostBackward A2/A3](mhc_post_backward.md)：MhcPostBackward 算子在 A2/A3 平台的 ACLNN 实现，用于计算 MHC 后处理的输入与参数梯度。
- [MhcPostBackward A5](mhc_post_backward_a5.md)：MhcPostBackward 算子在 A5 平台的 ACLNN 实现，用于计算 MHC 后处理的输入与参数梯度。
- [MhcPreBackward A5](mhc_pre_backward_a5.md)：MhcPreBackward 算子在 A5 平台的 ACLNN 实现，用于计算 MHC 前处理的输入与参数梯度。
- [MhcPreSinkhorn A2/A3](mhc_pre_sinkhorn.md)：MhcPreSinkhorn 算子在 A2/A3 平台的 ACLNN 实现，用于生成 Sinkhorn 路由所需的打分与中间量。
- [MhcSinkhorn A5](mhc_sinkhorn_a5.md)：MhcSinkhorn 算子在 A5 平台的 ACLNN 实现，用于对路由得分执行迭代行列归一化。
- [MhcSinkhornBackward A5](mhc_sinkhorn_backward_a5.md)：MhcSinkhornBackward 算子在 A5 平台的 ACLNN 实现，用于计算 Sinkhorn 迭代归一化的反向梯度。
