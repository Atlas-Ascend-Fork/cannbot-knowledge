---
type: Guide
title: SGLang Ascend DeepSeek-V3.2：DSA长上下文与CP/PD配方
description: 限定v0.5.18+A3的W8A8、ZigZag CP32 Prefill和低时延Decode，按128K输入的真实并发保留上游TPOT观测与版本限制。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_v3_2.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v3_2.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/DeepSeek/DeepSeek-V3_2.mdx
  role: supporting
created_at: '2026-11-08T11:50:28Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a3
---

# SGLang Ascend DeepSeek-V3.2：DSA长上下文与CP/PD配方

## 版本与资源

教程和最佳实践都要求SGLang v0.5.18、v0.5.18-cann9.0.0-a3镜像，明确不覆盖后续版本。本页的685B/37B激活MoE+MLA+DSA模型部署，不能直接用[当前通用安装版本组](/model/inference/guides/deployment/sglang_ascend/sglang_ascend_doc_installation_version_sets.md)替换。来源W8A8权重694.47GB，最低推荐TP16×64GB设备，即一个A3节点物理8卡；128K最佳实践资源明显更多。

## 长序列配置必须分阶段

1P1D标题下的P、D各是跨两节点的TP32进程组，总计32张A3物理卡。P设置--enable-prefill-cp、--cp-strategy zigzag、--attn-cp-size 32，同时关NPU graph与RadixCache，chunked-prefill-size=-1，max-prefill-tokens=68000，max-running-requests=1，DeepEP normal、ModelSlim量化。该组合不等于每个128K请求只用68000上下文，调度预算与完整输入长度是不同概念。

D使用TP32/EP32、DP attention 8、MoE dense TP1和DP LM Head，DeepEP low_latency，最大运行请求32、decode图max-bs4。NEXTN在P示例为(steps1,topk1,draft2)，D为(3,1,4)；不要用一个全局投机步数覆盖两个角色。

HCCL/GLOO网络接口须按跨节点环境设置，P/D共用MemFabric store；P/D的DEEPEP_HCCL_BUFFSIZE分别1200/400MB，D每rankdispatch容量8。P与D使用不同TASK_QUEUE设置是具体配方，不能解释成所有模型固定最佳值。通用[CP决策](/model/inference/optimizations/rules/long_seq_prefill_context_parallel.md)仍需按DSA实现验收。

## 上游观测与限制

来源用RANDOM输入131072、输出1024、range-ratio1，PD32物理卡、W8A8、上述软件组合。并发8/prompts8时给TPOT26ms，并发16/prompts16时给107ms；两个配置的主服务设置相似，工作负载并发不同，不可把这两个数字当作单开关优化倍率。一个26ms示例明确seed1，其他未写seed；warmup、重复次数、方差、独立基线未提供。这里未测TTFT，标题的low latency不能代替长输入首token时延。

## 验收与回退

先验证DSA索引与分页KV的正确性、P/D路由、非均匀输入长度、CP重排和NEXTN接受结果，再按固定并发及长度测TTFT/TPOT/吞吐。容量不足时调整并行与内存预算后重新评估，不能仅放大图batch或关闭错误。回退保持同一权重与镜像并关闭待验证特性，记录各项的独立成本。本次未启动模型、运行基准、执行量化或上游代码。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_v3_2.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_v3_2.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v3_2.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v3_2.mdx)（constraint）

## Cookbook的镜像入口不等于同一配方

Cookbook另列lmsysorg/sglang:dsv32-a2与dsv32-a3两个NPU镜像标签，但没有把它们固定到本卡v0.5.18+CANN9.0最佳实践的同一二进制。其生成器介绍只列GPU平台；不要把GPU的FlashMLA/FA3/TRT-LLM调优或性能结果套给这些NPU镜像。该页在DSA kernel枚举中将tilelang标为GPU/HPU/NPU可用，是后端家族说明，不能替代具体昇腾构建、模型shape与精度核验，也不意味着本卡A3长序列PD配方已经在A2验证。

- [docs/cookbook/autoregressive/DeepSeek/DeepSeek-V3_2.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/DeepSeek/DeepSeek-V3_2.mdx)（supporting）
