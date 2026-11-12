---
type: Guide
title: SGLang 昇腾新模型与外部多模态包的接入流程
description: 从 ForwardBatch、RadixAttention 到外部 EntryClass/processor 注册，保留 NPU 对照验证和热路径要求。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/development/support_new_models.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/development/contribution_guide.mdx
  role: supporting
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# SGLang 昇腾新模型与外部多模态包的接入流程

## 模型适配边界

来源是NPU接入工作流而非每种硬件的功能验证，因此本卡draft空平台。既有模型文件中用NPU条件分支连接hardware_backend/npu；移植时替换CUDA专属kernel为实际NPU实现，不能只改device字符串。

从vLLM迁入需把Attention替换为带layer_id的RadixAttention，LogitsProcessor及RMSNorm/激活等层使用SGLang组件；forward接收ForwardBatch并返回最终LogitsProcessorOutput，不能保留vLLM拆分compute_logits的假设。ForwardBatch携带positions、KV索引、sampling等状态，接口相似不等于执行状态兼容。

多模态还需模型识别、可接图像的chat模板、BaseMultimodalProcessor、pad_input_ids中的多模态hash/展开、图像特征提取和VisionAttention。NPU的ViT graph与processor必须实际支持所用torch_npu操作；单纯注册模型类不能建立图像处理链。

## 外部模型包

程序内可在launch前更新ModelRegistry；标准CLI则用SGLANG_EXTERNAL_MODEL_PACKAGE指向可import的父包，模块EntryClass对应该模型类，checkpoint architectures必须与类名匹配。仅修改architectures而未注册实现会找不到模型。包装已有模型后修改logits属于新模型行为，应另作准确率对照，不因复用了权重就假设输出等价。

外部多模态包另外设置SGLANG_EXTERNAL_MM_MODEL_ARCH和SGLANG_EXTERNAL_MM_PROCESSOR_PACKAGE，将processor与模型类关联；不要求另建processor EntryClass。漏任一识别环节可能使服务走文本路径。文档在torch.npu可用时允许自动检测device/attention backend，但排障时仍应查实际生效值。

## 验收与性能

来源建议NPU E2E测试覆盖模型、视觉、Embedding/Reward/Rerank、接口、cache/sampling/quantization和内存；真实权重服务测试与算子单元测试层次不同。新模型应做NPU设备正确性，并将SGLang GPU结果作为可用时的主要对照、无GPU适配再用HF；多模态还需MMMU等任务验证。不同平台性能比较必须保留资源和版本，不能据跨硬件差值归因某个kernel。

贡献页的200例GSM8K只是sanity check，注明可能1%–5%波动且输出吞吐不适合正式测速。热路径应减少item/cpu等同步、预先缓存每层重复不变条件，并分离硬件组件避免重复实现。本次没有运行上游测试或采纳其提交/CI命令作为知识库操作指令。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/development/support_new_models.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/development/support_new_models.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/development/contribution_guide.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/development/contribution_guide.mdx)（supporting）
