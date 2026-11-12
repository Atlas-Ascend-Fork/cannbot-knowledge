---
type: Guide
title: SGLang NPU训练回放所需indexer topk响应测试
description: 保留DeepSeekV4与GLM5.2 dummy六层的indexer topk形状和下界断言，明确未验证排序、上界和训练等价性。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/rl/indexer_replay/test_npu_return_indexer_topk_deepseek_v4.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/rl/indexer_replay/test_npu_return_indexer_topk_glm52.py
  role: supporting
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-08T12:28:23Z'
platforms:
- a3
---

# SGLang NPU训练回放所需indexer topk响应测试

## 返回协议与模型裁剪

两文件均注册base-b/nightly两NPU A3，用dummy权重裁剪为六层，TP2/attention-DP2、DP-lm-head、禁图、enable-return-indexer-topk。固定两个短prompt（法国首都、2+3），temperature0/max-new16，通过异步generate请求return_indexer_topk=true，再调用extract_indexer_topk_from_meta_info并reshape。这是响应结构回归，没有本次运行结果。

| 配置 | 返回reshape | 资源与实现隔离 |
|---|---|---|
| DeepSeek-V4 Flash BF16 | `[-1,2,512]` | attention=dsv4、page128、static0.72；六层compress_ratios=[0,0,4,128,4,128]，quantization_config=null；多个FP8/FP4、fused-hash/topk、TileLang和overlap缓存优化关，WAR barrier强制coarse |
| GLM5.2 BF16 | `[-1,6,2048]` | attention=ascend、static0.56，六层、quantization_config=null |

## 实际断言强度

两者要求ndim3、第一维（代码命名seqlen_minus_1）>0、层数与topk数恰好匹配，并要求所有index≥-1。没有检查index上界、topk是否排序、是否唯一、是否等于参考indexer、返回的时间步与每个原始token一一对应，也没有执行训练回放或梯度等价验证。

dummy权重、少层与关闭优化有意缩小资源需求，不能把这些通过条件直接用于完整模型精度。DSV4用shell source自定义算子环境后启动只是源测试命令，本次未执行或修改本机环境。

## Evidence

- [test/registered/npu/rl/indexer_replay/test_npu_return_indexer_topk_deepseek_v4.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/rl/indexer_replay/test_npu_return_indexer_topk_deepseek_v4.py)（primary）
- [test/registered/npu/rl/indexer_replay/test_npu_return_indexer_topk_glm52.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/rl/indexer_replay/test_npu_return_indexer_topk_glm52.py)（supporting）
