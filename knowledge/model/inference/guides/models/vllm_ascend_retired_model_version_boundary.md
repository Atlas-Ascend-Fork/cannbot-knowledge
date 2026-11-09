---
type: Guide
title: vLLM Ascend 历史模型：v0.30 停止维护边界与旧版本知识使用
description: 汇总28个历史模型入口的v0.30停更边界及29份中文资料，说明GLM4.x中文旧精度表与MiniMax-M2.po header的证据限制；先固定旧依赖再核对新框架适配，不以停更或残留声明替代能力、精度和构建验收。
  补充 OCR、InternVL、LLaVA 的历史组件/卡数与残留 C-Eval 配置。 补充 Qwen3 文本/视觉 Embedding 与 Reranker
  的任务、模板和质量边界。 补充Hunyuan/Minitron/Mixtral、Math-RM/ASR、Coder/Next/Omni和gpt-oss的旧量化、任务、拓扑与指标限制。
  保留Mixtral整机/TP/4096、Math RM CPU offload与32GB/144GB预算、Coder q_norm/gate混合W8A8、Qwen3
  Next 的 TP16、head_dim256 与 FIA 旧限制与gpt oss BF16 unsloth镜像路径。 保留 MiniMax-M2.5 的 QuaRot
  与 Eagle3、append_think、旧 FP8 例外及 obsolete 废弃消息指标归属。
tags:
- task.design
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-R1.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-V3.1.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-V3.2.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeekOCR2.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/GLM4.x.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/GLM5.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Hunyuan-A13B-Instruct.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Hy3-preview.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/InternVL3.5.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Kimi-K2-Thinking.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Kimi-K2.5.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/LLaVA-OneVision-Qwen2-0.5B-OV.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/MiniMax-M2.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Minitron-8B-Base.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Mixtral-8x7B-Instruct-v0.1.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/PaddleOCR-VL.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen2.5-Math-RM-72B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-235B-A22B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-ASR-1.7B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-Coder-30B-A3B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-Embedding.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-Next.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-Omni-30B-A3B-Thinking.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-Reranker.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-VL-235B-A22B-Instruct.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-VL-Embedding.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-VL-Reranker.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/gpt-oss-120b.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/DeepSeek-R1.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/DeepSeek-V3.1.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/DeepSeek-V3.2.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/GLM4.x.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Hy3-preview.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Kimi-K2-Thinking.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Kimi-K2.5.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/MiniMax-M2.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-235B-A22B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-VL-235B-A22B-Instruct.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/DeepSeekOCR2.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/PaddleOCR-VL.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/InternVL3.5.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/LLaVA-OneVision-Qwen2-0.5B-OV.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/llava-onevision-qwen2-0.5b-ov-hf.yaml
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Embedding.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Reranker.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-VL-Embedding.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-VL-Reranker.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3_embedding.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3_reranker.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Hunyuan-A13B-Instruct.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Minitron-8B-Base.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Mixtral-8x7B-Instruct-v0.1.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen2.5-Math-RM-72B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-ASR-1.7B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Coder-30B-A3B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Next.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Omni-30B-A3B-Thinking.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/gpt-oss-120b.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/MiniMax-M2.5.po
  role: supporting
created_at: '2026-10-29T09:52:40Z'
updated_at: '2026-10-30T15:10:56Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 历史模型：v0.30 停止维护边界与旧版本知识使用

## 适用范围与版本事实

固定主线的以下28个历史模型入口声明：从vLLM Ascend v0.30.0起停止支持/修复，部署转向v0.23.0历史文档。平台列表只限定本卡的版本核对流程，绝不表示这些模型都曾支持全部四个平台。

其中27份教程仅保留历史迁移说明；第28个GLM-5入口位于仍包含GLM-5.1部署内容的混合页。GLM-5停更不影响GLM-5.1的维护状态。

DeepSeek-R1, DeepSeek-V3.1, DeepSeek-V3.2, DeepSeekOCR2, GLM4.x, GLM5, Hunyuan-A13B-Instruct, Hy3-preview, InternVL3.5, Kimi-K2-Thinking, Kimi-K2.5, LLaVA-OneVision-Qwen2-0.5B-OV, MiniMax-M2, Minitron-8B-Base, Mixtral-8x7B-Instruct-v0.1, PaddleOCR-VL, Qwen2.5-Math-RM-72B, Qwen3-235B-A22B, Qwen3-ASR-1.7B, Qwen3-Coder-30B-A3B, Qwen3-Embedding, Qwen3-Next, Qwen3-Omni-30B-A3B-Thinking, Qwen3-Reranker, Qwen3-VL-235B-A22B-Instruct, Qwen3-VL-Embedding, Qwen3-VL-Reranker, gpt-oss-120b。

## 如何使用历史知识

既有R1、V3.2、Qwen3-Next等机制、算子与旧部署卡保留其原有来源和框架条件；不同项目的支持生命周期互不替代。不要因检索到旧性能卡、ModelRegistry类或通用feature示例就为最新Ascend生成“已支持”的部署建议。

若继续服务历史模型，先获取指定历史版本的模型教程、配对vLLM、Ascend、CANN/TorchNPU、权重与硬件配置；历史URL在此仅作来源指向，本次尚未获取其完整正文。不能把旧教程中的deepseek_mtp、enable_weight_nz_layout、fork或外部DP启动字段机械替换到当前版本。

若目标是最新框架，记录为重新适配：核对registry、模型实现、Attention/quant/Runner能力及回归。停止维护不证明无法运行，但没有维护承诺；不要仅更改status或删除检查就称适配完成。

## 验收、回退与证据

先复现完整历史栈的功能/精度，再单变量升级框架，最后图与多卡、服务SLO。失败按完整版本组合回退，不混用旧模型卡和新feature卡拼出未经验证的命令。检索应同时召回本版本边界和原技术卡。上述停止维护声明来自固定教程，本次没有验证旧镜像、运行模型或改写既有卡片。


## 支持表仍保留的历史功能声明

下表归并当前主线中33个停更行里的32个列对齐行，保留历史单项声明以便识别旧配方；所有行的模型维护状态均为🔴。单项✅、🟡、🔵不会解除停更，也不证明这些值属于某个已复现的历史依赖组合。未列功能仍为空白、未知，长度和硬件不跨行推广。Chunked/APC/Piecewise/Fullgraph含义见[支持裁决](vllm_ascend_model_support_resolution.md)。任务分区仅保留来源归档，RM仍为奖励评分模型。

| 模型 | 来源任务分区 / 硬件 | 上游维护状态 | 明确支持的单项 | 其他显式状态 | 长度与备注 |
| --- | --- | --- | --- | --- | --- |
| DeepSeek-V3.1 | 文本生成 / 950DT | 停更 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：240k |
| DeepSeek V3/3.1 | 文本生成 / A2/A3 | 停更 | BF16、W8A8、Chunked、APC、投机、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：240k |
| DeepSeek V3.2 | 文本生成 / A2/A3 | 停更 | BF16、W8A8、Chunked、APC、LoRA、投机、异步调度、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：160k |
| DeepSeek R1 | 文本生成 / A2/A3 | 停更 | BF16、W8A8、Chunked、APC、投机、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：128k |
| Qwen3-Coder-30B-A3B | 文本生成 / A2/A3 | 停更 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、Piecewise、Fullgraph | 未声明 | 未声明 |
| Qwen3-235B-A22B | 文本生成 / A2/A3 | 停更 | BF16、W8A8、Chunked、APC、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：256k |
| Qwen3-Next | 文本生成 / A2/A3 | 停更 | BF16、W8A8、TP、DP、Piecewise、Fullgraph | 未声明 | 未声明 |
| GLM-4.x | 文本生成 / A2/A3 | 停更 | W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：198k |
| GLM-5 | 文本生成 / A2/A3 | 停更 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：200k |
| Kimi-K2-Thinking | 文本生成 / A2/A3 | 停更 | 未声明 | 未声明 | 未声明 |
| DeepSeekOCR2 | 文本生成 / A2/A3 | 停更 | BF16、Chunked、异步调度 | 未声明 | 未声明 |
| MiniMax-M2.5/2.7 | 文本生成 / A2/A3/Ascend950 (Ascend950 experimental) | 停更 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Fullgraph | 不支持：LoRA；未验证：PP、Piecewise | 长度标注：200k |
| Qwen2.5-Math-RM-72B | 文本生成 / A2 | 停更 | BF16、W8A8、异步调度、TP | 不支持：LoRA；未验证：Chunked、APC、投机、PP、EP、DP、PD、Piecewise、Fullgraph | 长度标注：4096；vllm-rm；TP4；max_model_len=4096 |
| Hy3-preview | 文本生成 / A3 | 停更 | 未声明 | 未声明 | 未声明 |
| Qwen3-Embedding / Qwen3-VL-Embedding / Qwen3-Reranker / Qwen3-VL-Reranker | Pooling / Ascend 950DT&950PR | 停更 | 未声明 | 未声明 | 未声明 |
| Qwen3-Embedding / Qwen3-Reranker | Pooling / A2/A3 | 停更 | 未声明 | 未验证：W8A8 | 未声明 |
| Qwen3-VL-Embedding / Qwen3-VL-Reranker | Pooling / A2/A3 | 停更 | 未声明 | 实验：W8A8 | 未声明 |
| Qwen3-Embedding / Qwen3-Reranker | Pooling / 310P（Atlas 300I DUO） | 停更 | 未声明 | 未验证：W8A8 | FP16 |
| Qwen3-VL-Embedding / Qwen3-VL-Reranker | Pooling / 310P（Atlas 300I DUO） | 停更 | 未声明 | 实验：W8A8 | FP16 |
| Qwen3-VL-235B-A22B | 多模态生成 / A2/A3 | 停更 | BF16、W8A8、Chunked、APC、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：262144 |
| Qwen3-Omni-30B-A3B-Thinking | 多模态生成 / A2/A3 | 停更 | TP、EP | 未声明 | 未声明 |
| Kimi-K2.5 | 多模态生成 / A2/A3 | 停更 | Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：262144 |
| PaddleOCR-VL | 多模态生成 / A2/A3 | 停更 | 未声明 | 未声明 | 未声明 |
| PaddleOCR-VL | 多模态生成 / 310P（Atlas 300I DUO） | 停更 | Chunked、APC、异步调度、Piecewise、Fullgraph | 不支持：BF16、W8A8、LoRA、投机、TP、PD | 长度标注：16k |
| Qwen3-ASR | 多模态生成 / 310P（Atlas 300I DUO） | 停更 | Chunked、APC、异步调度、Piecewise、Fullgraph | 不支持：BF16、W8A8、LoRA、投机、PD；未验证：TP | 长度标注：4096 |

另一个Pooling Qwen2.5-Math-RM-72B行有6列表头却只有5个单元：模型、🔴、Reward Model及`gsm8k_correctness accuracy=0.80`备注、A2、教程链接。末尾链接落到W8A8列位置，不能解释为W8A8状态，也不靠猜测补空列。0.80只作来源披露，无评测数据/环境，不视为本仓精度结果；量化状态保持未知。另一个文本生成行明确的W8A8✅也不自动补齐此Pooling行。

模型表之外的历史教程入口仍保留在前面的28项清单；教程数量、表格行数、唯一模型数是不同口径。


## 中文历史入口：维护状态与旧译文残留

固定提交中的下列10份中文PO与各自当前英文页都包含同一维护边界：vLLM Ascend v0.30.0起不再支持或修复，部署指向英文v0.23.0历史URL。它们有独立的版本事实，即使英文页只有标题和迁移说明，也应先纳入维护裁决，再决定是否继续适配。这里核对的是源文件，不是在线中文latest页面的实际渲染结果；历史URL正文尚未获取。

| 中文来源文件 | 模型名称与边界 |
| --- | --- |
| DeepSeek-R1.po | DeepSeek-R1，v0.30.0起停更 |
| DeepSeek-V3.1.po | 标题覆盖DeepSeek-V3与3.1；对应历史页路径为DeepSeek-V3.1 |
| DeepSeek-V3.2.po | DeepSeek-V3.2，v0.30.0起停更 |
| GLM4.x.po | 标题为GLM-4.5/4.6/4.7；不用于裁决GLM-5.1 |
| Hy3-preview.po | Hy3-preview，v0.30.0起停更 |
| Kimi-K2-Thinking.po | 中文用“停止支持”，仍保留后续不再支持/修复的明确限制 |
| Kimi-K2.5.po | Kimi-K2.5，v0.30.0起停更 |
| MiniMax-M2.po | MiniMax-M2，不能仅凭名称外推MiniMax-M2.5/2.7的模型或功能组合 |
| Qwen3-235B-A22B.po | Qwen3-235B-A22B，v0.30.0起停更 |
| Qwen3-VL-235B-A22B-Instruct.po | 完整Instruct名称，避免和Qwen3-VL其他规模、Embedding/Reranker混用 |

### GLM4.x 中文旧精度表

这些PO共有24条非空有效译文；20条msgid仍对应当前英文标题/维护段落。GLM4.x.po额外保留A3/A2页签、“Before you start, please”以及一张当前英文页已无对应msgid的旧精度表。表内GPQA accuracy 84.85、MATH500 accuracy 98.8，备注为1个Atlas 800 A3（64GB×16）节点；来源没有在该表内给出精确模型变体、数据/评测版本和完整复现栈。将这些值归为旧中文残留声明，不当作当前版本精度门槛、本仓实测或GLM-5.1结果，也不根据孤立页签生成部署命令。字符串未匹配只定位版本差异，不能单独证明翻译错误或网站仍显示这些行。

### MiniMax-M2.po header 与构建验证

MiniMax-M2.po原文件含两个空msgid的header块；其2条业务译文仍分别对应标题和维护声明。本次未执行gettext编译或网站构建，不推定这个结构必然导致构建失败，也不宣称已验证渲染成功。

Agent生成适配任务时，应同时输出目标模型的完整名称、维护起止版本、所选历史/当前依赖组合和待复核能力。维护停止不等于无法运行，功能表历史单项支持也不等于当前仍有维护承诺；先选版本路线，再按原技术卡做正确性和性能验收。


## 四份多模态中文旧教程与当前停更页

DeepSeekOCR2.po、PaddleOCR-VL.po、InternVL3.5.po和LLaVA-OneVision-Qwen2-0.5B-OV.po共234条业务译文中，只有各自标题4条匹配当前英文；另230条对应的旧正文已由当前三行停更页替换。同名英文仍在，因此不是“孤儿PO”。它们均从vLLM Ascend v0.30.0起不再获得支持/修复，当前英文链接到v0.23.0历史文档；当前PO旧内容不能自动等同于那个历史URL正文或某个已复现的旧release。

这些模型的初次支持、旧硬件和性能线索仅用于重新适配的任务拆解。维护停止不证明实现文件或测试配置都已删除；残留文件也不恢复维护承诺。本卡平台范围仍只对应版本裁决流程，不表示下列模型各自支持全部四个平台。

| 历史译文模型 | 可保留的适配线索 | 不能直接生成的当前结论 |
| --- | --- | --- |
| DeepSeek-OCR-2 | 旧文从LLM视角讨论视觉编码器；声称v0.16首次支持，单机视觉/OCR输入与文本输出需分阶段验证。 | “v0.16及以后稳定”不延伸至当前停更版本；A2性能段与A3表不能混为同一配置。 |
| PaddleOCR-VL-0.9B | 旧文描述NaViT式视觉编码器与ERNIE-4.5-0.3B语言模型，另有PP-DocLayoutV2布局组件与独立环境。 | v0.21.0rc1例不代表所有后来版本支持；layout组件的指标不替代VLM识别或OCR文档端到端质量。 |
| InternVL3_5-38B / InternVL3_5-241B-A28B | 两个完整checkpoint与量化后缀分别定位，旧v0.20.2首次支持只是来源声明。 | 不因同族名称共用权重、结构或fusion设置，不能从大模型的enable_fused_mc2推出38B变体的专家路由能力。 |
| LLaVA-OneVision-Qwen2-0.5B-OV | 旧文涉及纯文本、单图/多图理解与视觉对话，单A2例和现存基线可作后续用例入口。 | API文本响应或C-Eval配置不证明图片processor、视觉token或多图推理正确，也不解除v0.30停更。 |

## 历史硬件、组件与卡数必须分别解释

DeepSeekOCR2旧性能段写A2-313T/1080P输入/256输出，后面的场景表又列A3共16NPU却给dp1tp1。它们没有闭合成同一实际worker拓扑，不能从“1 node”或Total NPUs推出该模型本次用了16卡。TTFT2s、TPOT200ms及每卡864TPS也缺配对的并发/负载/统计定义，不据此算跨平台加速比或逐请求TPS；这些均非本次实测。

PaddleOCR旧页的A2 PaddlePaddle与Atlas300I DUO OM说明针对PP-DocLayoutV2辅助布局路径，不能把“DUO只支持OM”推到整个vLLM视觉语言模型。它同时给VL单卡部署、FP16/CANN>=9.0图条件、8卡整机硬件表和A2/A3硬件入口；先分组件/部署阶段再核验，不能把整机装卡量当模型TP。CANN8.0的NumPy/OpenCV兼容提醒与CANN9.0图门槛属于不同上下文，旧PO也没构成当前完整依赖锁。

InternVL旧硬件表写A3 64GB×16整节点，吞吐例中241B用tp4dp2共8卡、38B用tp4共4卡；资源容量、实际占用和复制数分别记录。旧优化选项、dtype=auto、量化后缀与真实loader/模型结构分开，不能从某个单项或同族名字推出全部组合。

## 当前LLaVA测试文件的实际证据

所读tests/e2e/models/configs/llava-onevision-qwen2-0.5b-ov-hf.yaml仍在本提交：model_name为llava-hf/llava-onevision-qwen2-0.5b-ov-hf，model_type=vllm-vlm、hardware=Atlas A2 Series；serve给TP1、dtype auto、max_model_len4096、memory utilization0.8、trust_remote_code=true。它不是当前全部硬件/版本的支持表，auto也不是已解析的FP16/BF16证明。

该文件只声明ceval-valid、acc,none的value=0.42，num_fewshot0、apply_chat_template=false、fewshot_as_multiturn=false、batch_size auto；没有在此文件定义图片/VQA/OCR输入。0.42是配置值，未闭合实际runner比较策略或执行结果，不能标记本仓通过、当前CI正在覆盖或视觉精度已验证。后续适配同时保留该文本回归与真实图像/多图/OCR任务，独立检查processor、占位token、图片尺寸/数量、端到端结果与文本基线。

旧教程的OOM缩减seq/context/concurrency只是候选定位，不能代替内存归因；旧FAQ的宽泛进程清理不作为Agent默认动作。新框架适配先固定checkpoint/依赖/硬件并复现最小eager，再逐项加量化、图、并行和性能；历史PO缺失的代码块不能靠参数记忆补造。本批未拉取历史网页、下载权重、卸载依赖、执行测试/容器或运行NPU。


## Qwen3 文本和视觉检索旧教程

Qwen3-Embedding.po、Qwen3-Reranker.po、Qwen3-VL-Embedding.po、Qwen3-VL-Reranker.po 与旧命名 Qwen3_embedding.po、Qwen3_reranker.po 共266条业务译文已逐条读取。四个连字符命名英文仍在、均从v0.30起停更并指向v0.23历史文档；217条对应译文只4个标题匹配，其余213正文已替换。两个下划线命名没有同名当前英文，49条按历史孤儿处理，不因为标题与连字符版本相同就补造英文页或当作两份当前支持。

| 历史任务 | 权重身份和任务线索 | 复用边界 |
| --- | --- | --- |
| Qwen3-Embedding | Qwen/Qwen3-Embedding-0.6B、4B、8B；向量输出 embedding。 | 旧v0.9.2rc1+支持声明受当前停更截止约束；较新的PO用0.6B性能例，孤儿旧版用8B，不能比较成同一模型的改进。 |
| Qwen3-Reranker | Qwen/Qwen3-Reranker-0.6B、4B、8B；query/document成对并输出相关性。 | 旧文称 relevance_score；实际Score与Rerank API字段须按目标版本核对，不能把向量接口或聊天文本当成重排正确。 |
| Qwen3-VL-Embedding | Qwen/Qwen3-VL-Embedding-2B、8B；文本、图像、截图、视频或混合输入的历史检索线索。 | 模态出现于旧描述不证明每个processor/尺寸/帧数和硬件组合都通过；性能例为2B，不借8B数据补齐。 |
| Qwen3-VL-Reranker | Qwen/Qwen3-VL-Reranker-2B、8B；旧文专列 qwen3_vl_reranker.jinja 模板。 | PO没有保留该代码块的完整内容，不从文件名恢复模板；当前原生架构转换和预处理差异仍要独立检查。 |

旧页有A2/A3/950DT&950PR与Atlas300I DUO页签。它们是历史环境候选，不恢复当前维护或扩大至全部950/310产品。旧DUO的compilation-config/capture_sizes流数限制与max-model-len保守1024、O(max_model_len²) mask OOM提醒，均按旧实现及实际shape重新定位，不把1024设为所有embedding硬上限，也不能从页签推导所有量化/图组合可用。

权重目录路径必须与部署命令及实际checkpoint一致。各节点都有/root/.cache不等于共享文件系统或相同权重；多节点软件和路径身份逐节点留证。docker ps或HTTP200及字段存在只完成各自阶段，不证明跨模态检索质量、MTEB分数或吞吐提升。PO中的MTEB、vLLM benchmark链接和“运行后得到结果”不含本次结果，缺失脚本/输出不能补造。

原生v0.32仍列这些模型/转换入口，与Ascend当前停更并存；见[Pooling任务适配](vllm_ascend_pooling_task_contract.md)区分sequence/token向量、cross-encoder、late interaction和bi-encoder。原生登记/文档支持不恢复Ascend各硬件维护状态。本批没有获取历史网页、权重、MTEB数据集，也没有运行模型或基准。


## 九份历史模型中文正文的使用边界

Hunyuan-A13B-Instruct.po、Minitron-8B-Base.po、Mixtral-8x7B-Instruct-v0.1.po、Qwen2.5-Math-RM-72B.po、Qwen3-ASR-1.7B.po、Qwen3-Coder-30B-A3B.po、Qwen3-Next.po、Qwen3-Omni-30B-A3B-Thinking.po 和 gpt-oss-120b.po 共518条业务译文已逐条读取；当前英文仍各有三行标题和停止维护声明，只有9个标题msgid匹配，另外509条旧正文在当前英文中已被替换。它们不是孤儿PO，也不能当作v0.23历史网页的正文快照。PO日期、字符串匹配或当前同名实现不能重建其精确历史发布版本。

以下全部是旧资料的定位线索，受v0.30.0停止维护截止约束。旧文“某版本及以后稳定”不能覆盖此截止；没有把任何旧安装步骤、样例响应或性能数据作为本次运行结果，也没有恢复这些模型的当前维护承诺。

### Hunyuan、Minitron 与 Mixtral

| 历史模型与来源 | 可保留的线索 | 重新适配时需要补齐的证据 |
| --- | --- | --- |
| Hunyuan-A13B-Instruct / Hunyuan-A13B-Instruct.po | 旧介绍为80B总参数/13B激活、256K上下文，BF16 checkpoint为Tencent-Hunyuan/Hunyuan-A13B-Instruct，单节点4卡例。 | 参数、配置和上下文声明不是当前内存预算或长上下文验收；镜像宏未解析成配对Native/插件/CANN版本。 |
| Minitron-8B-Base / Minitron-8B-Base.po | BF16、单张Ascend910B 64GB；GSM8K 1000样本、5-shot、apply_chat_template=false、fewshot_as_multiturn=false。 | strict-match与flexible-extract是不同答案提取口径；PO仅保留结果表头，没有数值，不能据此填精度分数或当前门槛。 |
| Mixtral-8x7B-Instruct-v0.1 / Mixtral-8x7B-Instruct-v0.1.po | 旧MoE top-2、BF16 mistralai checkpoint、[INST]/[/INST]提示格式；硬件表列一台A3 64GB×16或A2 64GB×8。 | 整机卡数不是实际TP；“8个7B专家”的概述不宜当准确权重总参数；第三方量化可能存在不等于已适配某个量化checkpoint。 |

Hunyuan旧文给CANN8.5.1环境日志：静态权重37.46GB/NPU、PIECEWISE图捕获约18秒、KV容量529152 tokens；这些是来源日志，GB/GiB、各rank差异和实际堆栈未闭合，KV池token总量不等于单请求max-model-len。旧环境写Python3.11.6，并留有Python3.12待核验项；不能据旧TODO宣布3.12失败或已支持。GSM8K 94.77%附短hash 7cd45e，未明确完整仓库/revision/数据集和评测栈，不作固定40位版本或当前Agent质量门槛。

Mixtral旧例中的float16计算dtype和BF16权重标签分开，max-model-len4096是单请求输入加输出限制；eager、block128、memory utilization0.7均是该例参数。旧balance scheduling的吞吐/TPOT可能改善而TTFT可能变差，应按目标SLO测量，不能成为当前调度器的普适结论。Minitron的HTTP文本响应不替代上述GSM8K精度验证；这些资料均没有本次吞吐/时延结果。

### Qwen2.5-Math-RM-72B 奖励模型

Qwen2.5-Math-RM-72B.po旧文称v0.9.0首次支持、数学答案奖励评分、简介128K上下文；当前归档支持行写max_model_len4096，不能混成128K已验证部署。旧`--task reward`和示例`reward_score: 1.69`只是历史API线索，1.69不是概率、准确率或当前API字段保证。当前任务入口和奖励/Pooling的实际输出需按[Pooling任务契约](vllm_ascend_pooling_task_contract.md)重新核对，不能机械恢复已移除的参数。

旧BF16表给“CPU offload时1张910B4 32GB，无offload时4张32GB”。单卡结论依赖offload；多卡表也没有闭合真实权重/计算精度、host offload和余量预算。按72B×2 bytes粗估约144GB，而4×32GB名义合计128GB，这只是按名称估算的预算警示，不是精确checkpoint实测；必须检查真实tensor、GB/GiB、分片和卸载配置，不能从旧表保证装得下。此前归档的gsm8k_correctness accuracy=0.80不是这份PO补出的测试结果。缺失部署代码块不得靠记忆补造，评分响应可用也不等于奖励排序质量正确。

### Qwen3-ASR-1.7B 音频适配

Qwen3-ASR-1.7B.po旧文描述中文/英文/方言、多语言、歌声、长音频与流式识别；声称上游v0.19起引入。历史例checkpoint为Qwen/Qwen3-ASR-1.7B、TP1、单NPU完成音频prefill和decode，硬件有A2与Atlas300I DUO页签。BF16权重表不能证明DUO支持BF16计算：前述DUO历史支持行明确BF16不支持，需分别核验转换和实际dtype，不能跨页拼接。

旧DUO max-model-len4096是保守文本token/展开序列配置，不是音频秒数、毫秒数或所有ASR模型最大长度；旧实现提示causal mask按O(max-model-len²)占内存，长音频还须核对processor、切块、采样率/通道与音频token展开。memory utilization0.9是候选值；enforce_eager针对旧Atlas300I A2 2UP例，不推广为全部A2/DUO要求。增加TP要验证实际拓扑；旧卸载triton/triton-ascend的步骤仅作来源记录，本次未执行，不能当最新环境通用修复。

启动日志、pip show、进程存在、HTTP200和choices内有转写分别只证明对应阶段。PO没有WER/CER数值；重新适配应固定音频样本与转写评分口径，并覆盖短音频、长音频和并发。性能记录音频时长、并发、端到端时延/RTF与吞吐，包含预处理、API、推理和结果解析；普通文本bench不能替代ASR端到端评测。

### Qwen3-Coder：混合量化、版本与旧结果

Qwen3-Coder-30B-A3B.po介绍30.5B总参数/3.3B激活，架构同Qwen3-30B-A3B但面向编码、工具调用等任务；旧文首次支持v0.10.0rc1、验证基于v0.22.1rc。模型家族、底座或工具能力描述不证明具体tool parser、checkpoint和Ascend路径已正确。

旧W8A8不是所有层统一INT8：embedding、q_norm/k_norm及路由gate保留BF16；attention q/k/v/o用静态逐tensor scale，MoE gate/up/down专家投影动态计算输入scale。量化checkpoint或msmodelslim产物要逐层核验格式与loader；旧文“无权重时自行量化”不构成已pin外部工具或当前兼容性证明。旧例`--quantization ascend`属于该W8A8配方，BF16例移除；EP要求也只按该MoE配方解释。

| 旧A3 v0.22.1rc W8A8来源报告 | 评测口径 | 原报数值 |
| --- | --- | --- |
| GSM8K | 4-shot CoT accuracy | 90.14% |
| GPQA-Diamond | 0-shot CoT accuracy | 53.54% |
| LiveCodeBench | 0-shot pass@1 | 38.60% |
| AIME 2024 | 0-shot accuracy | 33.33% |

这些是旧文结果，非本仓实测或所有版本/权重保证；LiveCodeBench v4/v5/v6配置名不等于任意当前题集。AISBench示例的models配置文件名、abbr和实际CLI解析需按工具版本核对；旧精度/性能段写法有差异，不能把它们视为可互换参数。流式性能配置stream=True、ignore_eos=True、batch_size控制并发，以达到max_out_len来观察TPOT；这不同于精度或自然EOS停止场景。随机合成输入不代表真实APC命中负载，不据此否定前缀缓存的实际收益。

旧原生256K、通过YaRN hf-overrides扩到1M的说法是模型/配置线索；PO没有完整配置代码，不能补造rope参数或称1M已通过精度、KV预算和SLO。示例65536/1024、131072/1024及batch32/request_rate0只是负载候选；另有2048/2048、3500/1500，均不能跨场景比加速。

### Qwen3-Next：混合注意力与表格矛盾

Qwen3-Next.po旧文描述高稀疏MoE、混合attention和MTP，首次v0.10.2rc1、v0.16.0及以后稳定的说法受当前停更截止约束；精度段却指向v0.13.0rc1，只保留结果表头，没有数字。不把三个时间点拼成已验证的当前版本栈。旧Triton Ascend标为实验，精度/稳定性/性能可变化，也不能据旧标签断言当前全部Triton仍实验。

旧文说明TP>=16时，16个query heads、2个KV heads及head_dim256涉及GQA/MHA与FIA限制；这只是旧实现不支持TP>=16的诊断线索，不是当前Native或所有硬件的永久上限。检查目标版本的head分片/复制和实际attention后端，不能把概述当成已验证数学推导或恢复当前支持。

Qwen3-Next-80B-A3B-Instruct旧硬件行写一台A3或A2内8卡，另有整机A3 64GB×16和“2 (A3)、tp2”场景行；单位没有统一，不能直接推得实际rank/芯片占用。表中出现“Multimodal (1080p)”和“high-resolution visual inputs”，与本页文本模型主题不协调，没有独立视觉processor证据；记录为旧表残留，不因此为Qwen3-Next增加图片输入能力。16K/128K、带/不带APC的场景行也没有完整启动参数和性能数值，不宣布组合已复现。

### Qwen3-Omni：Thinker 与通用全模态描述分开

Qwen3-Omni-30B-A3B-Thinking.po先概述整个Omni家族可输出语音，随后明确Thinking checkpoint只有thinker、支持音频/视频/文本输入并输出文本。不能借家族概述为Thinking增加talker、语音输出或流式声码器能力；图像、视频帧与音频processor仍按实际checkpoint独立验收。旧首次支持v0.12.0rc1、验证v0.22.1rc和评测段v0.13.0rc1是不同声明，均不解除当前停更。

旧W8A8同样为embedding/QK norm/router BF16、attention静态与MoE专家动态的混合配方；当时量化权重表为N/A，msmodelslim量化是待固定工具/标定/产物的流程线索，不是可下载成品或当前保证。PO旧系统依赖与FFTS+默认模式下HcclAllreduce的stream/shape提醒缺完整命令，不据此修改系统或推荐通用环境变量。

旧评测使用gsm8k、omni_bench、bbh及EvalScope链接，没有保留可归属的分数或完整脚本；“运行后获得结果”不是精度数据。HTTP200/choices文本也不证明音频/视频正确。旧文因模型参数少而不讨论PD分离，是该教程范围，不构成当前框架永久不支持PD的证明。

### A3 拓扑与 Coder/Omni 旧场景

两份PO旧描述A3为8个双die NPU、16芯片，/dev/davinci[0-15]对应芯片编号，TP4用4芯片即2个包的说法须与实际驱动/可见设备映射一致。旧场景表却把“High Throughput TP1”列为1(A3)/2(A2)，不能从整机容量或Total NPUs直接推出单进程TP、EP或复制拓扑。低延迟/长上下文TP4列2(A3)/4(A2)也只是旧候选；记录物理包、芯片、进程rank和实际占用，不能混用“卡”计数生成资源申请。

两份旧示例默认关闭APC是当时效果未充分表征，不等于当前不支持；需用重复前缀/真实命中率负载验收益。旧镜像/workspace/site-packages、docker Up和版本输出分别是安装阶段线索，不代替ABI、NPU执行、图、质量与服务SLO验收。

### gpt-oss-120b：权重、Harmony 与指标归因

gpt-oss-120b.po旧例为unsloth/gpt-oss-120b-BF16，硬件整机A3 64GB×16或A2 64GB×8；不能套用其他原始量化checkpoint的显存估计、dtype、loader或拓扑。介绍中的工具使用/渲染聊天格式也不是每个当前Ascend parser正确性的证明；旧精度/性能段只有表头与执行描述，没有可补写的数值。

旧报错`openai_harmony.HarmonyError: error downloading or loading vocab file: failed to download or load vocab error`被旧文归因于Harmony，并提出提前准备tiktoken编码文件、设置`TIKTOKEN_ENCODINGS_BASE`。本次未访问链接Issue、下载编码或验证新版是否仍需该办法；先查实际包版本、vocab来源/缓存路径和离线可达性，编码资源加载失败不能直接归为模型算子故障。

旧参数段将排队时间泛称计入TTFT和TPOT；初始队列等待通常影响首token时间，不能无定义地重复归入每个后续token间隔，须按实际benchmark时间戳和公式区分队列、TTFT、ITL、TPOT。max-num-seqs×DP>=总并发是减少该类排队的候选配置，不是资源足够或SLO达标保证。更大的max-num-batched-tokens会改变prefill切块、decode竞争与activation压力，不保证所有请求延迟都降低。

同段KV预算公式仅是历史近似，不能省略权重、非torch/通信、图与运行时余量；gpu-memory-utilization0.9不是不OOM承诺，尤其EP负载变化需另核。旧PIECEWISE/FULL_DECODE_ONLY与capture_sizes阶梯只反映旧图入口，当前配置按[图模式选型](../optimization/vllm_ascend_graph_mode_selection.md)和目标版本重核，不能照抄旧默认列表。旧gpt-oss镜像称/vllm-workspace editable安装，而Coder/Omni称site-packages，说明镜像时代不同，不能据此统一猜测当前容器源码位置或修改即生效。

九份历史资料都按“完整checkpoint和任务→历史依赖复现或当前重新适配→最小eager正确性→量化/图/并行组合→质量和SLO”拆任务。旧PO未保留的代码块、原始数据、完整哈希与性能数字保持未知；本批未安装/卸载依赖、拉镜像或模型、请求服务、运行NPU或外部评测。


## MiniMax-M2.5 孤儿教程与废弃消息

MiniMax-M2.5.po 有55条有效消息，以及另45条以 #~ 注释的 obsolete 消息。当前没有同路径英文 MiniMax-M2.5.md；停更依据来自现存支持表明确的 MiniMax-M2.5/2.7 行，不能从 MiniMax-M2 标题或孤儿状态推导。此处增加的是历史适配线索，不新增第29份英文停更通知，也不把45条废弃消息当有效教程或当前推荐。PROJECT VERSION、YEAR 等header占位不是运行版本证据。

旧源 MiniMax/MiniMax-M2.5 的 FP8→BF16 与禁用FP8 kernel是当时MiniMax-M2实现例外，不能推广为全部FP8 checkpoint、当前950或无损转换方案。QuaRot W8A8目标权重与外部 Eagle3 draft 分别固定身份；旧外部标识 eagel-model-0318 按原拼写记录，不补造修正后的可下载模型或已兼容revision。append_think 保留 <think> 内容的旧说法与 minimax_m2 reasoning/Responses 分字段语义需要按当前parser单独检查，不能只凭文字宣布接口等价。

A2示例可见设备0–7与另处TP16不能直接拼接，先核对实际多节点、TP/DP/EP与进程映射。短3.5K输入/1.5K输出、max-model-len32768、TP16/DP1和 BALANCE_SCHEDULING=1 是旧特定起点；64K/128K的移除建议及6144/16384/32768 batched tokens不代表输入硬上限或当前调度器的最优值。active正文没有可归属的精度/性能数值。

| 废弃消息中的来源记录 | 可保留的历史事实 | 复用限制 |
| --- | --- | --- |
| A3短输入表 | 3.5K/1K、batch217、完成217失败0；TTFT10316.56ms、TPOT34.28ms、输出4803.81tok/s、总16096.59tok/s。 | 其标题写4K/1K batch16，与表中负载不同；不当同一case或本仓复测。 |
| A2双节点长输入 | 190K/1K、concurrency4、16prompts、prefix约85%；TTFT3305.25ms、TPOT109.83ms、输出35.29tok/s。 | 与A3负载/前缀/拓扑不同，不能算硬件加速比或当前SLO。 |
| A3长输入残留单元格 | 37.12、2002.37、105.54。 | 缺闭合列归属及单位，不重建为当前延迟、吞吐或加速。 |

上述均为obsolete历史消息，不作为Agent当前基准、自动优化阈值或硬件预算。8000端口可达不证明DP/HCCL链路；旧20004/2347端口和宽泛pkill FAQ不作为当前默认排障操作。本次没有启动/停止进程、转换权重、下载draft或运行评测。重新适配仍按完整checkpoint/历史或当前依赖路线→最小正确性→量化/投机/并行→任务精度和SLO逐项执行。
