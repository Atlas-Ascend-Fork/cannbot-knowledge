# 算法

- [3D Gaussian Splatting 昇腾 Atlas A2 训推优化实践](3d_gaussian_splatting.md)：3D Gaussian Splatting（3DGS）是 2023 年由 Kerbl 等人提出的可微渲染算法，以 3D 高斯椭球为核心图元，通过可微光栅化完成三维场景的重建与渲染（Kerbl et al., ACM TOG 2023）。cann-recipes-spatial-intelligence 提供了基于 gsplat 框架的昇腾适配版本，在 Atlas A2 上支持单卡训练与推理，并通过一组 AscendC 自研融合算子重写了 GPU 实现中的关键流程；实现与测量证据限于该昇腾适配版本，不覆盖 gsplat 完整实现。
