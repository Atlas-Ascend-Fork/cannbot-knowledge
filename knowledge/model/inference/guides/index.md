# 模型推理指南

按任务选择实施、验收与回退流程。

- [模型跑通指南](bringup/index.md)：当前Sana导入兼容补丁、必传quant_type的方法注入时序、加载后权重同步与量化替换。
- [模型部署指南](deployment/index.md)：共 3 张知识卡（如 已停用：LongCat A3 长序列 KVP 的历史条件与配置、量化部署：先检查权重格式，再选转换或直载、启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境））。
- [模型集成指南](integration/index.md)：共 4 张知识卡（如 块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）、把 decode 逻辑塞进图前消除 graph break：host 同步 / host 构造张量 / 图后端不支持算子的图安全改写、MTP 接入：共享权重、隐状态与惰性注册 等）。
- [模型优化指南](optimization/index.md)：共 4 张知识卡（如 LLM Decode 图编译指南（当前 GE 与 npugraph_ex）、多流优化流程：拆解依赖、选择后端并验收真实收益、R1 Prefill 微批双流：按请求切分并对齐通信轮次 等）。
- [模型专用指南](models/index.md)：共 23 张知识卡（如 DeepSeek-R1 A3 分阶段部署与优化验收流程、DeepSeek-V3.2-Exp A3 长序列部署与验收流程、DeepSeek V4.1 Flash：950 单卡的 Engram 与专家卸载 等）。
