---
type: Guide
title: SGLang NPU视觉语言模型质量与ViT批处理回归配方
description: 保存MMMU模型目标、TP覆写和图像顺序缓存回归的shape，区分继承默认与视觉质量断言。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_26b_a4b_it.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_31b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_e2b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_e4b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/mmmu-val.yaml
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_ascend_glm_4_5v.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_gemma_3_4b_it.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_janus_pro_1b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_janus_pro_7b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_kimi_vl_a3b_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_mimo_vl_7b_rl.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_minicpm_o_2_6.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_mistral_small_3_1_24b_instruct_2503.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_phi4_multimodal_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen2_5_vl_3b_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen2_5_vl_72b_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_235b_a22b_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_30b_a3b_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_4b_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_8b_instruct.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_vit_batching.py
  role: supporting
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-08T12:28:23Z'
platforms:
- a3
---

# SGLang NPU视觉语言模型质量与ViT批处理回归配方

## MMMU质量配方

注册模型主要计划A3运行；手工Gemma4没有明确产品。所有数字是子类声明的目标，没有本次执行分数。基类默认TP4、禁图、static0.35，MMMU100题/64线程/max30并四舍五入4位，细节见[嵌入、奖励、VLM契约](sglang_ascend_test_embedding_reward_scope.md)。没有覆写的模型继承默认，不能从模型大小猜TP。mmmu-val.yaml只固定本地MMMU snapshot路径，不表示任何下载或测试已经完成。

| 模型 | MMMU目标 | 重要覆写 |
|---|---:|---|
| GLM4.5V | 0.20 | TP8、static0.7，图禁用 |
| Gemma3-4B-IT | 0.20 | 继承默认 |
| Janus-Pro-1B / 7B | 各0.20 | 继承默认 |
| Kimi-VL-A3B-Instruct | 0.20 | 继承默认 |
| MiMo-VL-7B-RL | 0.20 | 继承默认 |
| MiniCPM-o-2.6 | 0.20 | 继承默认，不覆盖语音质量 |
| Mistral-Small-3.1-24B-Instruct-2503 | 0.20 | 继承默认 |
| Phi4-multimodal-instruct | 0.20 | 继承默认 |
| Qwen2.5-VL-3B-Instruct | 0.20 | 继承默认 |
| Qwen2.5-VL-72B-Instruct | 0.20 | TP8、static0.6，禁图 |
| Qwen3-VL-235B-A22B-Instruct | 0.20 | TP16、static0.8、launch timeout3000，禁图 |
| Qwen3-VL-30B-A3B / 4B / 8B Instruct | 各0.20 | 继承默认 |
| 手工Gemma4 26B-A4B-IT /31B/E2B/E4B | 0.40/0.50/0.15/0.30 | 继承TestVLMModels，文件未声明芯片产品 |

0.2阈值是低强度回归目标，不能当模型完整能力测评；它与[高精度任务配方](sglang_ascend_doc_validation_accuracy_recipes.md)中的MMMU目标不可互换。

## ViT混合图像、顺序与缓存复用

专门用例默认Qwen3-VL-8B-Instruct单NPU，可环境覆盖模型或指向外部服务；BF16、context8192、chunk512、max-running8、static0.7，语言侧disable-cuda-graph，但设置SGLANG_VIT_ENABLE_CUDA_GRAPH=1与FIA=1，不能把“语言图关”误读成ViT图也关。

4线程并发发送纯色PNG：红448×448、蓝448×448、绿+黄两张336×448、黄896×896。要求回答按输入顺序出现英文颜色名；第二轮倒序提交并加“Look carefully.”前缀，检查关联关系及缓存复用后的输出。请求temperature0/max16/timeout180。该测试不读取内部cache hit计数，不证明某缓存实现实际命中，也不测长视频或开放域视觉准确率。

## Evidence

- [test/manual/ascend/vlm_models/test_npu_gemma_4_26b_a4b_it.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_26b_a4b_it.py)（primary）
- [test/manual/ascend/vlm_models/test_npu_gemma_4_31b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_31b.py)（supporting）
- [test/manual/ascend/vlm_models/test_npu_gemma_4_e2b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_e2b.py)（supporting）
- [test/manual/ascend/vlm_models/test_npu_gemma_4_e4b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/vlm_models/test_npu_gemma_4_e4b.py)（supporting）
- [test/registered/npu/vlm_models/mmmu-val.yaml](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/mmmu-val.yaml)（constraint）
- [test/registered/npu/vlm_models/test_ascend_glm_4_5v.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_ascend_glm_4_5v.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_gemma_3_4b_it.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_gemma_3_4b_it.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_janus_pro_1b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_janus_pro_1b.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_janus_pro_7b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_janus_pro_7b.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_kimi_vl_a3b_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_kimi_vl_a3b_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_mimo_vl_7b_rl.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_mimo_vl_7b_rl.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_minicpm_o_2_6.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_minicpm_o_2_6.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_mistral_small_3_1_24b_instruct_2503.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_mistral_small_3_1_24b_instruct_2503.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_phi4_multimodal_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_phi4_multimodal_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_qwen2_5_vl_3b_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen2_5_vl_3b_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_qwen2_5_vl_72b_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen2_5_vl_72b_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_qwen3_vl_235b_a22b_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_235b_a22b_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_qwen3_vl_30b_a3b_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_30b_a3b_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_qwen3_vl_4b_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_4b_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_qwen3_vl_8b_instruct.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_qwen3_vl_8b_instruct.py)（supporting）
- [test/registered/npu/vlm_models/test_npu_vit_batching.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/vlm_models/test_npu_vit_batching.py)（supporting）
