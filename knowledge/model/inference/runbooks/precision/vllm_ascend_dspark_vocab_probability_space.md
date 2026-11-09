---
type: Runbook
title: vLLM Ascend DSpark 精度诊断：d2t 偏移、词表轴与概率导出
description: 排查缩表DSpark的token越界、接受率异常或概率维度错配，区分MRv1 greedy回退与MRv2目标词表scatter，核对Markov反馈、独立head和top-k提案分布。
tags:
- task.debugging
- topic.precision
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/qwen3_dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dspark/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/sample/gumbel.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/tests/v1/spec_decode/test_dspark_topk.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5_dspark.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_dspark_vocab_mapping.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/speculative.py
  role: constraint
created_at: '2026-10-29T14:55:50Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:59:59Z'
---

# vLLM Ascend DSpark 精度诊断：d2t 偏移、词表轴与概率导出


## 触发和证据边界

缩小draft词表后出现token越界、logits/bias宽度不同、拒绝采样使用错误列或接受率异常时，先核对输入词表、draft输出词表和target词表三个大小。本卡依据固定Ascend ceac1a2b及native v0.32.0代码的静态接口；没有本仓故障复现或NPU结果，硬件范围未知，保持draft。

## Loader先排除无效checkpoint

原生Qwen3 DSpark只在draft_vocab_size小于target vocab时分配draft_id_to_target_id（d2t）buffer；d2t是偏移，target_id=draft_id+d2t[draft_id]。例如d2t=[0,2,4]把draft=[0,1,2]映为target=[0,3,6]。t2d是训练项，loader跳过。不要用直接返回d2t[draft_id]替代加法。

缩小输出词表必须有独立lm_head和d2t权重，不能共享完整target head；输入vocab大于target时必须有独立embedding。config声明enable_confidence_head但checkpoint缺该head权重时，Qwen loader将模块置None，不生成已训练head。GLM/Kimi有各自loader，不能由Qwen这几项guard推导所有架构都实现了相同拒绝。

先保存真实加载key、own标志、V_input/V_draft/V_target、Markov两侧shape及映射结果；逐项验证映射在target范围内、整数类型和预期的一一性。特别是MRv2 index_copy_按列覆盖，不负责合并重复目标列的概率；不能把重复映射当作已正确聚合。上述检查是适配验收建议，不冒充源码已逐项验证。

## 按Runner选择消费路径

| Runner和词表 | 固定实现 | 精度探针 |
| --- | --- | --- |
| MRv1，全词表且允许probabilistic | 顺序加Markov bias后调用采样helper，可汇集[B,K,V] draft_probs | 每步概率与同一步条件prev对应 |
| MRv1，存在d2t | 顺序循环明确禁用probabilistic，greedy选draft id、map后反馈target id，概率不导出 | 不能把概率缺失或greedy回退误作随机采样已启用 |
| MRv2，greedy | draft轴argmax后map_draft_to_target | 下一步markov_embed收到映射后的target token |
| MRv2，probabilistic且缩表 | 预计算arange(V_draft)+d2t，将加过bias的draft logits scatter到[B,V_target]临时buffer，其他列为-inf | 采样和draft logits cache按target id索引；临时buffer与持久cache不别名 |

MRv2临时buffer _draft_scatter_buf初始化为-inf并在每step覆盖同一组映射列；运行中更换映射或词表需要重建相关buffer，不能只改Parameter后继续复用。Gumbel接口还核对缓存source的shape、device、dtype和目标词表容量；这些Host断言只覆盖参数合同，完整采样kernel及拒绝恢复分布仍需单独闭合。

## top-k不是采样后随意删列

HF配置dspark_draft_topk不为空时，native speculator先在未加Markov bias的base logits选候选，再仅给候选加bias，其他列为-inf，由同一采样/拒绝路径消费这个截断提案。不能把top-k缓存同dense采样混用，也不能称其与完整Markov提案必然相同；Markov可能把原base候选外token抬高。k等于全词表时才有固定UT比较对应dense计算的条件。

vLLM v0.32.0的SpeculativeConfig规定top-k只用于method=dspark，配置值优先于HF值，范围1到draft vocab size，并只放行Qwen3DSparkModel/Qwen3OmniDSparkModel架构。不能因Kimi/GLM/DSV4复用某个head方法，就跳过这条架构门控。

gathered Markov路径对未量化weight直接选行，并检查weight与embedding dtype；retained ModelOpt W4A16 NVFP4另有专门解包/快速路径。CUDA BF16专用分支不能作为Ascend ModelSlim打包weight可直接index的依据。启用前核对真实scheme、逻辑行布局和保留权重能力；不支持时关闭该top-k优化，不能仅改dtype掩盖打包布局。

## 修复验证和回退

用可逐项计算的小词表验证base logits、bias、加法映射、下一步prev及target轴缓存，覆盖未映射列、边界id、K>1和greedy/probabilistic。再测试真实checkpoint完整加载、拒绝后恢复和质量；统计采样须评估分布，不能仅比少量token或接受率。必要时先关闭top-k、恢复完整匹配词表或关闭草稿，不删除缩表缺权重guard。

GLM专属loader见[GLM MLA DSpark](../../guides/integration/vllm_ascend_glm_mla_dspark_adapter.md)，Kimi的恒等映射和独立head边界见[Kimi MLA草稿](../../guides/integration/vllm_ascend_kimi_dspark_adaptation.md)。所引CPU/CUDA测试是来源断言，本次未运行。
