---
type: Guide
title: SGLang 昇腾模型支持矩阵的使用与新旧差异
description: 按具体 checkpoint 读取 A2/A3 支持声明，区分模型接入、优化组合和950证据缺口。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/support_models.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Support%20Models%20on%20Ascend%20NPU.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms:
- a2
- a3
---

# SGLang 昇腾模型支持矩阵的使用与新旧差异

## 怎样解释支持声明

两份固定快照的模型矩阵是框架接入声明，不是每个checkpoint的容量、精度、PD/CP/graph兼容、性能或设备实测证明。新矩阵只有A2/A3列，没有950列；不能从安装页支持950推导本表所有模型已适配950。GLM-OCR是新表明确的例外：A3支持，A2未声明。其余下列新表条目两列均勾选。具体教程常只有A3配方，不能以模型支持行扩展某个优化组合。

## 当前矩阵的具体模型

下列按来源模型家族聚合，同一行保留了具体checkpoint身份；供应方前缀或量化后缀不同不自动等价。

- **DeepSeek**：Eco-Tech/DeepSeek-V4-Pro-w4a8-mtp；Eco-Tech/DeepSeek-V4-Flash-w8a8-mtp；sgl-npu/DeepSeek-V3.1-w8a8；sgl-npu/DeepSeek-V3.2-W8A8；sgl-npu/DeepSeek-R1-0528-W8A8；sgl-npu/DeepSeek-V2-Lite-W8A8。
- **Qwen3.8**：Qwen/Qwen3.8-2.4T-A95B。
- **Qwen3.6**：Qwen/Qwen3.6-35B-A3B；Eco-Tech/Qwen3.6-27B-w8a8。
- **Qwen3.5**：Eco-Tech/Qwen3.5-397B-A17B-w4a8-mtp；Eco-Tech/Qwen3.5-122B-A10B-w8a8-mtp；Eco-Tech/Qwen3.5-35B-A3B-w8a8-mtp；Eco-Tech/Qwen3.5-27B-w8a8-mtp；Qwen/Qwen3.5-9B；Qwen/Qwen3.5-4B；Qwen/Qwen3.5-0.8B。
- **Qwen3**：Qwen/Qwen3-30B-A3B-Instruct-2507；Qwen/Qwen3-32B；Qwen/Qwen3-0.6B；sgl-npu/Qwen3-235B-A22B-W8A8；Qwen/Qwen3-Next-80B-A3B-Instruct；Eco-Tech/Qwen3-Coder-480B-A35B-Instruct-w8a8-QuaRot。
- **Qwen2.5**：Qwen/Qwen2.5-7B-Instruct。
- **QWQ**：sgl-npu/QwQ-32B-W8A8。
- **Llama**：LLM-Research/Llama-4-Scout-17B-16E-Instruct；AI-ModelScope/Llama-3.1-8B-Instruct；LLM-Research/llama-2-7b；LLM-Research/Llama-3.2-1B-Instruct。
- **Mistral**：mistralai/Mistral-7B-Instruct-v0.2。
- **Gemma**：google/gemma-3-4b-it。
- **Phi**：microsoft/Phi-4-multimodal-instruct。
- **OLMoE**：allenai/OLMoE-1B-7B-0924。
- **StableLM**：stabilityai/stablelm-2-1_6b。
- **Command-R**：CohereForAI/c4ai-command-r-v01。
- **ChatGLM**：ZhipuAI/chatglm2-6b。
- **ExaONE 3**：LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct。
- **XVERSE**：xverse/XVERSE-MoE-A36B。
- **SmolLM**：HuggingFaceTB/SmolLM-1.7B。
- **GLM-5**：Eco-Tech/GLM-5.2-w8a8；Eco-Tech/GLM-5.1-w4a8；Eco-Tech/GLM-5-w4a8。
- **GLM-4**：ZhipuAI/glm-4-9b-chat。
- **MiMo**：iridiumine/MiMo-V2-Flash-W8A8；XiaomiMiMo/MiMo-7B-RL。
- **Arcee AFM-4.5B**：arcee-ai/AFM-4.5B-Base。
- **Persimmon**：Howeee/persimmon-8b-chat。
- **Ling**：inclusionAI/Ling-lite。
- **Granite**：ibm-granite/granite-3.1-8b-instruct。
- **DBRX (Databricks)**：AI-ModelScope/dbrx-instruct。
- **Baichuan 2 (7B, 13B)**：baichuan-inc/Baichuan2-13B-Chat。
- **ERNIE-4.5 (4.5, 4.5MoE series)**：PaddlePaddle/ERNIE-4.5-21B-A3B-PT。
- **MiniCPM (v3, 4B)**：OpenBMB/MiniCPM3-4B。
- **Kimi**：sgl-npu/Kimi-K3-W4A8；Eco-Tech/Kimi-K2.6-w4a8；Eco-Tech/Kimi-K2.5-w4a8；moonshotai/Kimi-K2-Thinking。
- **GPTOSS**：eigen-ai-labs/gpt-oss-120b-bf16。
- **OLMo**：allenai/OLMo-2-1124-7B-Instruct。
- **MiniMax-M2.5**：Eco-Tech/MiniMax-M2.5-w8a8-QuaRot。
- **MiniMax-M2**：cyankiwi/MiniMax-M2-BF16。
- **Solar**：upstage/SOLAR-10.7B-Instruct-v1.0。
- **StarCoder2**：bigcode/starcoder2-7b。
- **Trinity (Nano, Mini)**：arcee-ai/Trinity-Mini。
- **Orion (14B)**：OrionStarAI/Orion-14B-Base。
- **GPT-J (6B)**：EleutherAI/gpt-j-6b。
- **IBM Granite 4.0 (Hybrid, Dense)**：ibm-granite/granite-4.0-micro。
- **Laguna XS.2 (poolside)**：poolside/Laguna-XS.2。
- **Hunyuan**：Tencent-Hunyuan/Hy3。
- **Qwen2.5-VL**：Qwen/Qwen2.5-VL-3B-Instruct；Qwen/Qwen2.5-VL-72B-Instruct。
- **Qwen3-VL**：Qwen/Qwen3-VL-30B-A3B-Instruct；Qwen/Qwen3-VL-8B-Instruct；Qwen/Qwen3-VL-4B-Instruct；Qwen/Qwen3-VL-235B-A22B-Instruct。
- **DeepSeek-VL2**：deepseek-ai/deepseek-vl2。
- **Janus-Pro (1B, 7B)**：deepseek-ai/Janus-Pro-1B；deepseek-ai/Janus-Pro-7B。
- **MiniCPM-V / MiniCPM-o**：OpenBMB/MiniCPM-V-2_6；OpenBMB/MiniCPM-o-2_6。
- **Gemma 3 (Multimodal)**：google/gemma-3-4b-it。
- **Mistral-Small-3.1-24B**：mistralai/Mistral-Small-3.1-24B-Instruct-2503。
- **Phi-4-multimodal-instruct**：microsoft/Phi-4-multimodal-instruct。
- **MiMo-VL (7B)**：XiaomiMiMo/MiMo-VL-7B-RL。
- **LLaVA (v1.5 & v1.6)**：AI-ModelScope/llava-v1.6-34b。
- **LLaVA-NeXT (8B, 72B)**：lmms-lab/llava-next-72b。
- **Kimi-VL (A3B)**：moonshotai/Kimi-VL-A3B-Instruct。
- **GLM-4.5V (106B)**：ZhipuAI/GLM-4.5V。
- **Llama 3.2 Vision (11B)**：LLM-Research/Llama-3.2-11B-Vision-Instruct。
- **DotsVLM-OCR**：rednote-hilab/dots.ocr。
- **GLM-OCR**：zai-org/GLM-OCR（仅A3）。
- **Qwen3-Omni**：Qwen/Qwen3-Omni-30B-A3B-Instruct。
- **Step3-VL (10B)**：stepfun-ai/Step3-VL-10B。
- **DeepSeek-OCR / OCR-2**：deepseek-ai/DeepSeek-OCR-2。
- **Qwen3-ASR (0.6B, 1.7B)**：Qwen/Qwen3-ASR-1.7B。
- **E5 (Llama/Mistral based)**：intfloat/e5-mistral-7b-instruct。
- **GTE-Qwen2**：iic/gte-Qwen2-1.5B-instruct。
- **Qwen3-Embedding**：Qwen/Qwen3-Embedding-8B。
- **GME (Multimodal)**：iic/gme-Qwen2-VL-2B-Instruct。
- **BGE**：BAAI/bge-large-en-v1.5。
- **Llama3.1 Reward**：Skywork/Skywork-Reward-Llama-3.1-8B-v0.2。
- **InternLM 2 Reward**：Shanghai_AI_Laboratory/internlm2-7b-reward。
- **Qwen2.5 Reward - Math**：Qwen/Qwen2.5-Math-RM-72B。
- **Qwen2.5 Reward - Sequence**：Howeee/Qwen2.5-1.5B-apeach。
- **BGE-Reranker**：BAAI/bge-reranker-v2-m3。
- **Qwen3-Reranker (decoder-only yes/no)**：Qwen/Qwen3-Reranker-8B。
- **Qwen3-VL-Reranker (multimodal yes/no)**：Qwen/Qwen3-VL-Reranker-2B。

## 旧表与新表的差异

旧表没有950列，LLM中出现DeepSeek V3/V3.1、V3.2-Exp等宽泛名称；新表更多固定供应方和量化checkpoint，V3.2-Exp不能静默当作V3.2同一权重。以下是旧表出现、当前表不以相同字符串列出的模型标识；其中有改名/供应方替换，也有真正未再列出的项目。**缺行不证明撤销支持**，需要进一步实现和checkpoint证据，不能自行判定弃用。

- DeepSeek V3/V3.1（DeepSeek，旧表A2/A3均支持）。
- vllm-ascend/DeepSeek-V3.2-Exp-W8A8（DeepSeek，旧表A2/A3均支持）。
- vllm-ascend/DeepSeek-R1-0528-W8A8（DeepSeek，旧表A2/A3均支持）。
- vllm-ascend/DeepSeek-V2-Lite-W8A8（DeepSeek，旧表A2/A3均支持）。
- vllm-ascend/Qwen3-235B-A22B-W8A8（Qwen，旧表A2/A3均支持）。
- Qwen3-Coder-480B-A35B-Instruct-w8a8-QuaRot（Qwen，旧表A2/A3均支持）。
- vllm-ascend/QWQ-32B-W8A8（Qwen，旧表A2/A3均支持）。
- meta-llama/Llama-4-Scout-17B-16E-Instruct（Llama，旧表A2/A3均支持）。
- huihui-ai/grok-2（Grok，旧表A2/A3均支持）。
- Shanghai_AI_Laboratory/internlm2-7b（InternLM 2，旧表A2/A3均支持）。
- ibm-granite/granite-3.0-3b-a800m-instruct（Granite MoE，旧表A2/A3均支持）。
- baidu/ERNIE-4.5-21B-A3B-PT（ERNIE-4.5 (4.5, 4.5MoE series)，旧表A2/A3均支持）。
- Kimi/Kimi-K2-Thinking（Kimi，旧表A2/A3均支持）。
- openai/gpt-oss-120b（GPTOSS，旧表A2/A3均支持）。
- minimax/MiniMax-M2（MiniMax-M2，旧表A2/A3均支持）。
- openbmb/MiniCPM-V-2_6（MiniCPM-V / MiniCPM-o，旧表A2/A3均支持）。
- openbmb/MiniCPM-o-2_6（MiniCPM-V / MiniCPM-o，旧表A2/A3均支持）。
- lmms-lab/llava-onevision-qwen2-7b-ov（LLaVA-OneVision，旧表A2/A3均支持）。
- Kimi/Kimi-VL-A3B-Instruct（Kimi-VL (A3B)，旧表A2/A3均支持）。
- iic/gte_Qwen2-1.5B-instruct（GTE-Qwen2，旧表A2/A3均支持）。
- Alibaba-NLP/gme-Qwen2-VL-2B-Instruct（GME (Multimodal)，旧表A2/A3均支持）。
- AI-ModelScope/clip-vit-large-patch14-336（CLIP，旧表A2/A3均支持）。
- AI-ModelScope/Skywork-Reward-Gemma-2-27B-v0.2（Gemma 2-27B Reward，旧表A2/A3均支持）。

部署时先核对权重的architecture、量化描述、MTP与tokenizer，再查该模型专属教程和实际软件版本。已列Embedding/Reward/Rerank不等于可按生成模型接口评估，需使用对应池化、打分和输入契约。本次没有加载或运行任一模型。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/reference/support_models.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/support_models.mdx)（primary）
- [sgl_docs：docs/hardware-platforms/ascend-npus/Support Models on Ascend NPU.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Support%20Models%20on%20Ascend%20NPU.mdx)（primary）
