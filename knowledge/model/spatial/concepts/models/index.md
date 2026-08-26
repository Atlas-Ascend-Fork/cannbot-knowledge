# 模型

- [Hunyuan3D 2.0 — 图生 3D 资产生成（NPU 推理适配）](hunyuan3d.md)：Hunyuan3D 是腾讯混元系列在 2025 年推出的图生 3D 资产创作模型，生成带高分辨率纹理贴图的高保真 3D mesh。本样例提供其昇腾 Atlas A2 单机单卡推理适配版，依赖上游开源仓 Tencent-Hunyuan/Hunyuan3D-2 的网络结构代码（外部未克隆未核验），通过非覆盖方式将本仓优化模块（替换文件 + module/dit_cache）叠加进去。环境为 CANN 8.2.RC1 + torch/torch_npu 2.6。推理通过 python minimal_demo_npu.py 入口启动（source set_env.sh 后），优化后 texgen 在 2 万平面 mesh 输入下推理时间降至约 26 秒。
- [VGGT 昇腾 Atlas A2 推理适配与优化](vggt.md)：VGGT（Visual Geometry Grounded Transformer，CVPR 2025）是一个前馈式 3D 视觉基础模型：给定一组无序图像，单次前向即可联合预测相机位姿、点云、深度图等几何属性。本页记录 cann-recipes-spatial-intelligence 在 Atlas A2（Atlas 800I A2 推理产品）上对 VGGT 的推理适配、性能优化与三任务精度评测。模型本体来自上游开源仓 facebookresearch/vggt（外部未克隆未核验，本页只引本仓内重写/覆盖的优化文件）。 补充：三任务精度评测指标语义（AUC@30=位姿误差≤30°累积准确率、Acc=预测→真值点云最近邻均距、Comp=真值→预测最近邻均距、Overall=(Acc+Comp)/2）。
