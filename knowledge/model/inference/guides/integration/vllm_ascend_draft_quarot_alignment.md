---
type: Guide
title: vLLM Ascend DSpark 草稿权重对齐：QuaRot、TP 词表与 PP 副本
description: 沿align_draft_weights在共享后、预计算前对齐草稿输入basis，区分投影WQ、重载词表WQ转置、草稿自有权重和PP末阶段的独立embedding。
tags:
- task.implementation
- topic.precision
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/qwen3_dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/llama_eagle3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3_dspark.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/qwen3_dflash2.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dspark_model_loading.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/test_qwen3_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_kimi_k3_dspark_weights.py
  role: evidence
created_at: '2026-10-29T13:13:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:55:50Z'
---

# vLLM Ascend DSpark 草稿权重对齐：QuaRot、TP 词表与 PP 副本

## 场景与顺序

目标使用QuaRot而草稿训练basis不同，或PP末阶段拿不到target embedding时，按实际own标志与后处理检查；不要就地修改共享target参数。固定实现的Qwen3 DSpark用fc，GLM/Kimi DSpark用context_proj；这些是同一对齐helper的调用，不能由此证明各模型部署或量化组合均已验收。

MRv1先共享embedding/topk/head，再post_process，最后预计算parallel draft隐状态；MRv2 Ascend DSpark先super加载/共享，再post_process(self.vllm_config)，再配置target辅助状态捕获。post_process接收target配置，不能错误使用已替换的草稿quant/config。相关测试覆盖失败时不进入后处理和临时配置恢复，但本次未执行。

## 两个矩阵方向不能混用

get_rotation_path从quant_description.optional.quarot.rotation_map.global_rotation得到目标目录下文件；get_rotation_matrix读取其global_rotation tensor。缺文件/键会失败，不回退为“未旋转”。

process_weight将投影输入维按Q.shape[0]分块，要求整除；每块以float32计算W_block @ Q，再转回原dtype，copy_保留投影Parameter对象。它不是词表参数的处理公式。Q还需满足实际hidden basis的矩阵形状；helper显式验证的是输入维整除，后续matmul/copy仍有自己的shape约束。

目标词表权重需要新建草稿副本时，按TP原始vocab行范围取target checkpoint切片，计算W_vocab @ Q.T；尾部padding置零。原target权重及先前共享对象保持不变。不能把WQ和WQ.T交换，也不能把大词表整份复制后忽略rank切片。

## own标志、旋转与PP的组合

| 条件 | 投影 | embedding / LM-head |
| --- | --- | --- |
| 有QuaRot | 按输入分块做WQ | own=True的草稿自有词表层保持；own=False则新建层，从target checkpoint重载并用Q.T对齐，再process_weights_after_loading、置own=True |
| 无QuaRot且PP1 | 不变，helper返回 | 保持现有共享/自有关系 |
| 无QuaRot且PP>1 | 投影不变 | 仅为own=False的embedding重载末阶段本地副本；LM-head仍可在最后stage共享 |

helper以getattr(...,False)处理缺失own标志，先检查真实加载如何设置它。由copy_与无状态标记可推得：helper没有“已经对齐”的幂等标记；重复调用可能重复旋转投影，不能把它当每次请求可安全重放的hook。只在实际加载生命周期的约定位置调用，并核对恢复/重载路径。

_find_safetensors_weight优先按index.json的精确候选key找shard，否则只扫描safetensors键；load_quarot_target_layer按org_vocab_start/end取行，不读取无关完整shard。此精确加载helper与旧EAGLE3中“找任意含embed键”的扫描函数不是同一保证。

DFlash2仅在有QuaRot时调用此helper，并要求存在aux-hidden projection fc；不据DSpark无旋转PP重载的分支推断DFlash2也走该分支。它的候选词表/采样限制仍见[方法选型](../optimization/vllm_ascend_speculative_method_selection.md)。

## 验证与停止

保留target共享参数前后快照、草稿own标志、加载key/TP行区间、投影Parameter地址及后处理次数。以受控输入验证各aux块basis和投影输出一致性，检查padding、独立head、PP1/PP>1及有无旋转；CPU/mock断言只证明测试表达的接口条件。

缺旋转权重、投影维度不整除、必要词表key缺失、target被改写或logits不对齐时停止性能比较，恢复完整匹配checkpoint和加载顺序。硬件/实际量化kernel范围未证实，保持draft；本次未运行数值或模型测试。


## Kimi checkpoint自有head先于后处理保留

[Kimi MLA DSpark适配](vllm_ascend_kimi_dspark_adaptation.md)在mapper丢弃之前截获checkpoint LM-head，正确加载后置has_own_lm_head，防止共享/QuaRot helper替换或重复旋转它。固定UT只证明head加载失败保持旧head/标志，不证明整个模型参数具事务回滚；不要把缺自有head与加载失败都无条件改成共享。
