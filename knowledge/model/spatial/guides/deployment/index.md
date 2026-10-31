# 部署指南

- [VGGT 迁到 950：跳过私有格式转换并检查 Attention 连续性](vggt_950_compatibility.md)：根据具身智能仓已合入实现核对 950 加载、Q/K/V 连续化和无残差 LayerNorm 路径，保留旧 A2 性能与新平台验证的边界。

- [Hunyuan3D A2 部署与验收](hunyuan3d_a2_deployment.md)：固定 Atlas A2 单卡 Hunyuan3D 适配的环境、权重、启动开关、图模式与缓存互斥及验收回退步骤。
