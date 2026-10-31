# 模型部署指南

准备权重、环境与部署前提，保留历史方案的生命周期边界。

- [已停用：LongCat A3 长序列 KVP 的历史条件与配置](kvp_longseq_decode.md)：当前版本不提供 LongCat KVP 配置或部署入口；撤下旧代码、旧 YAML 和多提交历史配方。
- [量化部署：先检查权重格式，再选转换或直载](quant_weight_conversion_path_selection.md)：昇腾量化权重制备与部署路径：离线系数配合 convert_model.py、原始 compressed-tensors 权重直载、amct 重新标定；按模型、格式与平台选择并验收精度。
- [启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境）](yuanrong_kv_pool_remote_h2d_ascend_prereqs.md)：依据固定部署文档检查 Yuanrong Remote H2D 的主机 HugeTLB、worker 参数和 NPU/RoCE 环境；关闭开关后仍需验证默认传输，不推导零拷贝次数或设备大页布局。
