---
type: Guide
title: SGLang NPU嵌入、奖励和VLM测试的断言强度
description: 区分Embedding短prompt断言、NoHF Reward类型检查与Gemma HF分数对拍，保留VLM默认MMMU和图模式边界。
tags:
- task.testing
- topic.precision
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/test_embedding_base.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/test_no_hf_reward_base.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/vlm_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/runners.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/reward_models/test_npu_gemma_2_27b_v0_2.py
  role: supporting
created_at: '2026-11-08T12:20:23Z'
updated_at: '2026-11-08T12:28:23Z'
platforms: []
---

# SGLang NPU嵌入、奖励和VLM测试的断言强度

BaseEmbeddingTest使用spawn，按max_position_embeddings截断prompt，再分别HFRunner与ascend SRTRunner得到embedding，检查similarity与1的距离小于逐模型tolerance。但实际assert仅在原prompt字符长度<=1000时执行；长prompt仍运行和打印而不做该断言。名称prefill_logits并不意味着覆盖每个token的语言logits或全部长输入精度。

BaseNoHFRewardModelTest用两条固定对话生成reward，默认FP16、TP4、图禁用、mem_fraction0.8，最终仅assert结果为Tensor；没有断言正确回答比错误回答得分高，也不和HF对拍。日志accuracy字段只是Tensor展示，不能作为奖励质量基线。

TestVLMModels默认ascend、multimodal、TP4、图禁用和mem_fraction0.35，MMMU调用100题、64线程、max_tokens30，将score四舍五入4位后与子类阈值比较。子类可覆写参数，这个测试不自动覆盖图模式、长视频或所有分辨率。

HF与SRT test runners在NPU先初始化NPU后端。复现需记录两侧模型/权重、模板、dtype与实际prompt长度；测试名、成功启动、输出Tensor和数据集质量验收应分层报告。本次未执行上述测试。


## Gemma奖励模型的独立HF对拍用例

另一个注册A3测试对Skywork-Reward-Gemma-2-27B-v0.2、BF16，用同一“sigmoid范围”问题配错误[-1,1]与正确[0,1]回答，分别HFRunner和SRT Runner获取分数，逐元素要求绝对差<0.04。该测试比上述NoHF基类更强，仍未断言正确回答的reward必须更高。MODELS元组带tp_size=1，但assert_close_reward_scores没有把它传给Runner，不能仅由元组认定有效TP；SRT显式static0.95。两个native Gemma/GELUTANH环境开关只在__main__分支设置，模块导入运行不自动获得它们。本次未执行。

- [test/registered/npu/reward_models/test_npu_gemma_2_27b_v0_2.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/reward_models/test_npu_gemma_2_27b_v0_2.py)（supporting）
