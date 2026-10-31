# 模型

- [Hunyuan3D 2.0 — 图生 3D 资产生成（NPU 推理适配）](hunyuan3d.md)：Hunyuan3D 2.0 通过 DiT 与 VAE 从图像生成形状，再由 Paint 为 mesh 生成纹理；本页说明两阶段输入输出和固定 Atlas A2 适配边界。
- [VGGT 昇腾 Atlas A2 推理适配与优化](vggt.md)：VGGT（Visual Geometry Grounded Transformer，CVPR 2025）是一个前馈式 3D 视觉基础模型：给定一组无序图像，单次前向即可联合预测相机位姿、点云、深度图等几何属性。cann-recipes-spatial-intelligence 提供 Atlas A2（Atlas 800I A2 推理产品）上的推理适配、性能优化与三任务精度评测。模型本体来自上游开源仓 facebookresearch/vggt；实现与测量证据限于昇腾适配文件，不覆盖上游完整实现。三任务精度评测指标为 AUC@30（位姿误差≤30°累积准确率）、Acc（预测→真值点云最近邻均距）、Comp（真值→预测最近邻均距）、Overall（(Acc+Comp)/2）。
