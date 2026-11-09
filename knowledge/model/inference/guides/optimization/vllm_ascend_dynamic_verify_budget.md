---
type: Guide
title: vLLM Ascend MRv1 动态验证预算：条件置信度、全局分配与同步代价
description: 沿DynamicSpecScheduler将DSpark/DFlash条件置信度转为累计生存概率和每请求前缀长度，区分budget_k、min_verify_tokens、周期更新与MRv2
  adaptive。
tags:
- task.optimization
- topic.speculative_decoding
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/dspark_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_dynamic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/spec_decode/test_dspark_deepseekv4.py
  role: constraint
created_at: '2026-10-29T14:55:50Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:56:39Z'
---

# vLLM Ascend MRv1 动态验证预算：条件置信度、全局分配与同步代价


## 范围和三类K

本卡固定Ascend ceac1a2b的MRv1 DynamicSpecScheduler。additional_config.dynamic_spec_config.method缺省None，启用时与speculative_config.method同为dspark或dflash；它先照常生成K个候选，再决定下一次target验证的前缀长度，不是少跑某些draft位置。它不同于MRv2 enable_adaptive_verification，也不同于按batch区间选择K的num_speculative_tokens_per_batch_size。

文档将其列为探索性MRv1功能，DSpark只承诺Qwen、DFlash用无head代理。仓内另有DSV4动态e2e候选，但测试定义及传入config不证明选中了该Runner/分支或已执行成功；不据此扩大模型/硬件支持。整项产品范围未证实，保持draft/空平台。

## 从概率到共享预算

DSpark使用compute_confidence的sigmoid概率，输入每位置hidden及前驱token的Markov embedding；[seed,draft1,...,draftK]只取前K个作为Markov输入，不把draft1错当第一位置前驱。DFlash使用每位置max(softmax(logits))。两者都转float32缓冲并clamp到[1e-6,1]，不能再给DSpark输出重复sigmoid或把raw logit直接当概率。

对每请求沿位置做cumprod得到survival[b,i]=各条件概率的前缀乘积，再周期性统计所有survival>=budget_threshold的元素数/B，ceil为新预算；若为偶数且小于K则加1，再夹到[min_verify_tokens,K]。奇数偏好来自代码中的特定Qwen/A3成本观察及verify含bonus的解释，不是所有硬件上奇数更快的保证。

| 参数 | 源码默认值 | 含义 |
| --- | --- | --- |
| initial_verify_budget_per_req | 5 | 初始共享budget_k，构造时按min/K裁剪 |
| budget_update_interval | 16 | 累计调用update次数后重估预算，不是每请求生成token数 |
| budget_threshold | 0.3 | 比较累计survival，而非单位置置信度 |
| min_verify_tokens | 1 | 每请求保底前缀长度 |

配置对象只校验method枚举；method_params内各值在scheduler中做int/float转换，并非全部参数已完成范围拒绝。适配工作流先检查1<=min<=K、正更新间隔和合理概率阈值，保留最终解析值；不能由config创建成功推导参数均有效。

## 全局分配不等于每请求固定budget_k

先为每请求保底min，再从其余survival位置中跨整个batch取B×(budget_k-min)个最高值（不超过候选数），按request id scatter_add为每请求计数，最终仍验证各请求的前缀。分配的是长度，不是任意不连续token子集；概率并列也不应被解释成可跳过前驱。

手算例：B=2、K=3、min=1、budget_k=2，条件概率分别[0.9,0.9,0.9]和[0.8,0.3,0.2]，survival为[0.9,0.81,0.729]和[0.8,0.24,0.048]。保底后两个额外名额都归请求0，最终长度[3,1]，总量4；不是每个请求都2。这个例子是按源码算法推导，非设备测试结果。

## 真实消费点和性能测量

MRv1 model_runner.take_draft_token_ids读取num_verify_tokens，把每个k夹到[0,self.num_spec_tokens]并按请求切tokens[:k]后交回调度；请求顺序必须和confidence batch一致。切短输出并不等于减少本轮草稿骨干成本，收益来自后续verify/调度形状，必须测净时延。

周期重估使用.item()读取统计量，有NPU→CPU同步；消费点还逐项int(k)，不能声称整个动态路径只每16步发生一次Host读取。需拆分confidence/head、cumprod/topk、预算更新、Host读取、target verify及graph形状变化成本。阈值更高一般减少满足条件的survival项，但奇数取整/min约束使最终预算不是平滑曲线；接受率高不自动抵消额外Host开销。

先在固定模型、负载和采样参数下比较动态关闭/开启，记录每请求实际verify长度、K/Q、保底约束、接受长度、同步时延、TTFT/TPOT/吞吐及质量。更新间隔和阈值逐一改变，覆盖短/长上下文、混batch和空batch；不把e2e声明的golden acceptance数字写成复测收益。异常先移除dynamic_spec_config恢复固定K，必要时关闭草稿；本批未运行模型、设备或Agent实验。
