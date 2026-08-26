# 网络模块

- [Action Chunking（动作分块 / ACT Transformer）](action_chunking.md)：VLA 模仿学习策略的核心结构思想：一次性预测一段连续动作序列（动作块，action chunk），而不是逐步预测，从而缓解逐步预测带来的误差累积。cann-recipes-embodied-ai 中由 ACT（Action Chunking with Transformers，act）模型直接体现，Pi0/Pi0.5 的 flow-matching 动作专家也以 chunk 形式整段输出动作，因此本页作为 canonical 概念页被多模型复用。
- [Flow-Matching Action Expert（流匹配动作专家）](flow_matching_action_expert.md)：Pi0 / Pi0.5 系 VLA（Vision-Language-Action）模型的核心架构模块：VLM 主干 + flow-matching 动作专家双流结构。这是 cann-recipes-embodied-ai 操作类模型 pi0 与 pi05 共享的网络范式，由本页 canonical 描述，模型页只链接。
