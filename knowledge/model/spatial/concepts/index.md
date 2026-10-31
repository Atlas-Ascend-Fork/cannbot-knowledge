# 概念

- [算法](algorithms/index.md)：3D Gaussian Splatting（3DGS）是 2023 年由 Kerbl 等人提出的可微渲染算法，以 3D 高斯椭球为核心图元，通过可微光栅化完成三维场景的重建与渲染（Kerbl et al., ACM TOG 2023）。cann-recipes-spatial-intelligence 提供了基于 gsplat 框架的昇腾适配版本，在 Atlas A2 上支持单卡训练与推理，并通过一组 AscendC 自研融合算子重写了 GPU 实现中的关键流程；实现与测量证据限于该昇腾适配版本，不覆盖 gsplat 完整实现。
- [融合 Kernel](kernels/index.md)：共 6 张知识卡（如 CalcRender —— 3DGS Alpha-blending 渲染融合算子（前向/反向）、GaussianFilter —— 3DGS 视锥剔除融合算子（前向/反向 Scatter）、GaussianSort —— 3DGS tile 内高斯球深度排序算子 等）。
- [模型](models/index.md)：共 2 张知识卡（如 Hunyuan3D 2.0 — 图生 3D 资产生成（NPU 推理适配）、VGGT 昇腾 Atlas A2 推理适配与优化）。
- [平台](platforms/index.md)：华为昇腾 Atlas A2 系列训练/推理服务器，是 cann-recipes-spatial-intelligence 仓所有样例（VGGT、Hunyuan3D、3D Gaussian Splatting）的目标部署平台。各样例 README 明确以 Atlas A2 为运行环境（3DGS 为单卡 Atlas A2 训推）。
