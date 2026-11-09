---
type: Guide
title: vLLM Ascend MRv1采样：随机流、top-k/top-p与惩罚哨兵
description: 按AscendSampler区分批次不变性回退、processed logits/logprobs、FP32概率和指数噪声流，核对generator行映射、prompt/output惩罚与padding哨兵。
aliases:
- AscendSampler
- AscendTopKTopPSampler
- apply_all_penalties
- random_sample
tags:
- task.implementation
- task.debugging
- topic.model_serving
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/sample/sampler.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/sample/penalties.py
  role: implementation
created_at: '2026-11-03T05:28:26Z'
updated_at: '2026-11-03T05:28:26Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MRv1采样：随机流、top-k/top-p与惩罚哨兵

## 范围与真实分支

固定 ceac1a2 的 sample/sampler.py 与 penalties.py 全部程序通过整文件AST投影读取，未执行采样、Triton、NPU或统计实验。这里是MRv1 AscendSampler；[MRv2流水线](vllm_ascend_mrv2_sampling_pipeline_contract.md)与[310P采样](vllm_ascend_310p_sampling_contract.md)采用各自入口，不能按Sampler同名统一判断。

AscendSampler继承Native，替换top-k/top-p子采样器；greedy直接argmax。top-k/top-p实际绑定MRv2模块中的PyTorch helper，不因HAS_TRITON=True就自动使用同名融合kernel。VLLM_BATCH_INVARIANT开启时整个forward_native委托Native实现，其算法/RNG与此分支需分别核对。

## 随机数流与输出量纲

过滤logits后按logprobs_mode选择返回处理后的logits或FP32 log_softmax；其他mode此局部不附加处理后矩阵，Native外层仍有自己的合同。softmax用FP32，随后指数噪声q在global_stream生成；current stream显式wait，并对q record_stream，最后以argmax(probs/q)采样。probs.div_原地修改概率临时量，不能重用它作为原概率记录。

generators以行号为键。数量不等batch时先为全部行填默认指数随机数，再覆盖具名行；数量恰等batch时跳默认填充，因此caller必须保证键恰覆盖全部有效行，不能只检查字典长度。请求重排后generator行映射与device/stream生命周期要同步更新。源码没有在该函数用_SAMPLING_EPS做clamp，不从常量名推零噪声/端点保护。

## 惩罚输入与验证

缺Triton时警告并委托Native apply_penalties；有Triton且no_penalties直接返回原logits，否则要求prompt_token_ids存在。output token列表先在CPU按vocab_size padding，转设备non_blocking，再把-1也改成vocab_size哨兵；不能将这个哨兵当合法词表token。prompt矩阵的有效ID与padding仍由调用方及被调用kernel合同保证，本wrapper没有对任意负数/越界统一修复。

验收覆盖greedy/随机混batch、部分/全部generator、请求重排、batch-invariant、不同logprobs mode、空/不同历史长度、-1/pad与三类penalty；比较分布、可复现性和真实数值，不要求不同实现同seed必定逐位相同。性能计入Host构造历史、H2D及global stream等待，少一次Python循环不单独等于端到端收益。
