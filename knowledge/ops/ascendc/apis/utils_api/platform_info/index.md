# 平台信息获取

- [PlatformAscendC](platform_ascend_c/index.md)：针对Cube与Vector分离模式，计算融合算子启动的numBlocks值，即AIV与AIC组合数量，结果通过SetSimdNumBlocks设置。
- [PlatformAscendCManager](platform_ascend_c_manager.md)：Kernel直调场景下获取硬件平台信息的单例管理类，通过GetInstance获取PlatformAscendC指针以访问核数等平台信息。
