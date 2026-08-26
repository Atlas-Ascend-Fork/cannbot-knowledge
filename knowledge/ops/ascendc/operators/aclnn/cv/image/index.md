# 图像处理 ACLNN 算子

本目录保存图像变换、采样、插值和栅格化相关的 ACLNN 算子知识。

- [Im2colBackward A5](im2col_backward_a5.md)：Im2colBackward 算子在 A5 平台的 ACLNN 实现，用于将列式展开后的梯度还原并累加到输入特征图。
- [Rasterizer A2/A3](rasterizer.md)：Rasterizer 算子在 A2/A3 平台的 ACLNN 实现，用于将三角面片栅格化为像素级覆盖与索引结果。
- [Resize A5](resize_a5.md)：Resize 算子在 A5 平台的 ACLNN 实现，用于按指定尺寸或缩放比例调整图像张量的空间分辨率。
- [ThreeInterpolateBackward A2/A3](three_interpolate_backward.md)：ThreeInterpolateBackward 算子在 A2/A3 平台的 ACLNN 实现，用于计算三点插值过程对输入特征的反向梯度。
- [UpsampleBicubic2d A5](upsample_bicubic_2d_a5.md)：UpsampleBicubic2d 算子在 A5 平台的 ACLNN 实现，用于对二维图像执行双三次插值上采样。
- [UpsampleBicubic2dAA A2/A3](upsample_bicubic_2d_aa.md)：UpsampleBicubic2dAA 算子在 A2/A3 平台的 ACLNN 实现，用于对二维图像执行带抗锯齿处理的双三次缩放。
- [UpsampleBicubic2dAA A5](upsample_bicubic_2d_aa_a5.md)：UpsampleBicubic2dAA 算子在 A5 平台的 ACLNN 实现，用于对二维图像执行带抗锯齿处理的双三次缩放。
- [UpsampleBicubic2dAAGrad A2/A3](upsample_bicubic_2d_aa_grad.md)：UpsampleBicubic2dAAGrad 算子在 A2/A3 平台的 ACLNN 实现，用于计算抗锯齿双三次缩放过程的输入梯度。
- [UpsampleBicubic2dAAGrad A5](upsample_bicubic_2d_aa_grad_a5.md)：UpsampleBicubic2dAAGrad 算子在 A5 平台的 ACLNN 实现，用于计算抗锯齿双三次缩放过程的输入梯度。
- [UpsampleBilinear2dAA A2/A3](upsample_bilinear_2d_aa.md)：UpsampleBilinear2dAA 算子在 A2/A3 平台的 ACLNN 实现，用于对二维图像执行带抗锯齿处理的双线性缩放。
- [UpsampleBilinear2dAA A5](upsample_bilinear_2d_aa_a5.md)：UpsampleBilinear2dAA 算子在 A5 平台的 ACLNN 实现，用于对二维图像执行带抗锯齿处理的双线性缩放。
- [UpsampleBilinear2dAABackward A2/A3](upsample_bilinear_2d_aa_backward.md)：UpsampleBilinear2dAABackward 算子在 A2/A3 平台的 ACLNN 实现，用于计算抗锯齿双线性缩放过程的输入梯度。
- [UpsampleBilinear2dAABackward A5](upsample_bilinear_2d_aa_backward_a5.md)：UpsampleBilinear2dAABackward 算子在 A5 平台的 ACLNN 实现，用于计算抗锯齿双线性缩放过程的输入梯度。
- [UpsampleLinear1dBackward A5](upsample_linear_1d_backward_a5.md)：UpsampleLinear1dBackward 算子在 A5 平台的 ACLNN 实现，用于计算一维线性插值上采样过程的输入梯度。
- [UpsampleNearest2dBackward A5](upsample_nearest_2d_backward_a5.md)：UpsampleNearest2dBackward 算子在 A5 平台的 ACLNN 实现，用于计算二维最近邻上采样过程的输入梯度。
- [UpsampleNearest3d A5](upsample_nearest_3d_a5.md)：UpsampleNearest3d 算子在 A5 平台的 ACLNN 实现，用于对三维体数据执行最近邻上采样。
- [UpsampleNearestExact1d A5](upsample_nearest_exact_1d_a5.md)：UpsampleNearestExact1d 算子在 A5 平台的 ACLNN 实现，用于按精确最近邻坐标规则对一维数据进行上采样。
- [UpsampleNearestExact2dBackward A5](upsample_nearest_exact_2d_backward_a5.md)：UpsampleNearestExact2dBackward 算子在 A5 平台的 ACLNN 实现，用于计算二维精确最近邻上采样过程的输入梯度。
- [UpsampleNearestExact3dBackward A5](upsample_nearest_exact_3d_backward_a5.md)：UpsampleNearestExact3dBackward 算子在 A5 平台的 ACLNN 实现，用于计算三维精确最近邻上采样过程的输入梯度。
- [UpsampleTrilinear3d A5](upsample_trilinear_3d_a5.md)：UpsampleTrilinear3d 算子在 A5 平台的 ACLNN 实现，用于对三维体数据执行三线性插值上采样。
