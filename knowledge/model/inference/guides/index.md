# 模型推理指南

按任务选择实施、验收与回退流程。

- [模型跑通指南](bringup/index.md)：当前Sana导入兼容补丁、必传quant_type的方法注入时序、加载后权重同步与量化替换。
- [模型部署指南](deployment/index.md)：共 40 张知识卡（如 已停用：LongCat A3 长序列 KVP 的历史条件与配置、推理并行配置选型：按 Prefill、Decode 和模型结构找参考 YAML、量化部署：先检查权重格式，再选转换或直载 等）。
- [模型集成指南](integration/index.md)：共 321 张知识卡（如 Attention 融合链选型：GQA、MLA Absorb 与 Indexer 稀疏路径、块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）、compressed-tensors 接入：产物契约、targets/ignore 与运行加载链 等）。
- [模型优化指南](optimization/index.md)：共 40 张知识卡（如 LLM Decode 图模式：编译配置、backend 定界与精度排查、kernel_details 字段解读：流水指标、控核与多流真实重叠、多流优化流程：拆解依赖、选择后端并验收真实收益 等）。
- [模型专用指南](models/index.md)：共 44 张知识卡（如 DeepSeek-R1 A3 分阶段部署与优化验收流程、DeepSeek-V3.2-Exp A3 长序列部署与验收流程、DeepSeek V4.1 Flash：950 单卡的 Engram 与专家卸载 等）。

- [SGLang 昇腾模型、量化与适配指南](sglang_ascend/index.md)：共 38 张知识卡（如 SGLang 昇腾 LoRA 的驻留槽、逐 rank 一致性与安全清零、SGLang 昇腾 LoRA 的 SGEMV、批次元数据与图边界、SGLang 昇腾模型默认后端与量化配置守卫 等）。
- [模型推理验证与测试](testing/index.md)：共 22 张知识卡，分布在 1 个子目录（sglang_ascend）。
