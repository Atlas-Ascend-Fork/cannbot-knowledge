# 模型部署指南

准备权重、环境与部署前提，保留历史方案的生命周期边界。

- [已停用：LongCat A3 长序列 KVP 的历史条件与配置](kvp_longseq_decode.md)：保留回退前 LongCat A3 KVP 的分片条件、校验与测试样例；PR501 及 2c45117 按键存在性拒绝 kvp_size，设为 1 也不可用，本 Guide 不再提供当前部署建议。
- [量化权重部署指南：离线转换、原始权重直载与验收](quant_weight_conversion_path_selection.md)：先核对模型版本、权重配置与加载器，再选择离线系数转换、AMCT 或原始量化权重直载；不从 YAML 文件名推断量化格式。
- [启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境）](yuanrong_kv_pool_remote_h2d_ascend_prereqs.md)：依据固定部署文档检查 Yuanrong Remote H2D 的主机 HugeTLB、worker 参数和 NPU/RoCE 环境；关闭开关后仍需验证默认传输，不推导零拷贝次数或设备大页布局。
