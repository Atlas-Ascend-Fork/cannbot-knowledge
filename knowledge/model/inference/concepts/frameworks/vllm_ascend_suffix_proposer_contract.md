---
type: Concept
title: vLLM Suffix proposer：CPU后缀缓存、变长草稿与Ascend接线
description: 核对v0.32 SuffixDecodingProposer的Arctic缓存、请求身份、CPU token输入、长度边界和stop_request，区分固定名义K与逐请求变长输出，再检查Ascend工厂和Runner传参。
tags:
- task.implementation
- topic.speculative_decoding
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/spec_decode/suffix_decoding.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/suffix_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/suffix_speculative_decoding.md
  role: constraint
created_at: '2026-10-30T13:07:50Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T13:07:50Z'
---

# vLLM Suffix proposer：CPU后缀缓存、变长草稿与Ascend接线


## 范围与所有者

原生vLLM v0.32.0的suffix_decoding.py完整102行定义SuffixDecodingProposer，Ascend的suffix_proposer.py是薄适配。这里只解释固定源码接口与CPU token/cache状态，未知整项硬件支持保持draft、空platforms；[A2四卡配方](../../guides/optimization/vllm_ascend_suffix_decoding_contract.md)另有窄平台证据，不能由继承关系推广到所有模型/设备。

构造要求speculative_config非None，保存num_speculative_tokens、suffix_decoding_max_tree_depth、suffix_decoding_max_spec_factor、suffix_decoding_min_token_prob及model max_model_len；内部lazy import arctic_inference.suffix_decoding.SuffixDecodingCache，用suffix_decoding_max_tree_depth/suffix_decoding_max_cached_requests分别传入外部max_tree_depth/max_cached_requests初始化，实例保存在self.suffix_cache。没用该方法时不在这个构造入口导入Arctic，选择方法后缺包/不兼容不由该类自动回退。外部Arctic版本、树实现和淘汰细节未冻结，不能从max_cached_requests字段名推定LRU、字节上限或线程安全。

## 固定num_speculative_tokens与每请求变长不是一回事

propose先assert调用num_speculative_tokens与构造时配置相等，再按sampled_token_ids顺序遍历，返回list[list[int]]，各请求长度可不同。sampled_ids为空时视作partial prefill，追加空草稿并跳过；input_batch.num_tokens_no_spec[i]>=max_model_len也返回空草稿。

其余请求传给外部speculate的max_spec_tokens为min(名义K,max_model_len-num_tokens-1)，再传max_spec_factor/min_token_prob。因此接近长度上限时可为0，不能硬填满配置K或把上限当每步实产量。逐请求返回长度动态，也不能推导该入口可任意改变全局调用参数K；接入动态预算时先核等值assert、调度器与实际验证窗口的契约。

## 请求身份、prompt树与响应状态

req_id来自input_batch.req_ids[i]。不在active_requests时，如果同ID已在cached_requests，先evict_cached_response，再用req_id_to_index查索引，从token_ids_cpu[index,:num_prompt_tokens]启动新prompt树。随后add_active_response追加本步sampled_ids。

匹配pattern取token_ids_cpu[i,max(0,num_tokens-max_tree_depth):num_tokens]，不是全量prompt重新搜索的接口。prompt读取经ID映射，而pattern/num_tokens按批次i读取，调用方需保证InputBatch映射与sampled列表对齐；此函数没有验证所有索引/身份不变量。重排、抢占、恢复和同ID复用应沿上游InputBatch/Arctic实际语义核对，不能凭接口存在宣称全部状态迁移已验证。

每次遍历后，对active_requests减去input_batch.req_id_to_index.keys()所得ID调用stop_request。它不是本函数内主动删除所有历史缓存；外部stop/cached转换、内存释放与并发语义仍由Arctic实现决定。slot_mappings参数注明unused；此提议入口只消费CPU token缓冲，不代表目标推理没有KV或NPU验证成本。

load_model为pass，表示该proposer本身没有草稿模型要加载；不能将其解释为外部包/缓存不用初始化或服务没有权重/设备资源。

## Ascend工厂、dummy_run与Runner实参

spec_decode/__init__.py将method="suffix"映射到AscendSuffixDecodingProposer(vllm_config,runner)。薄适配super().__init__(vllm_config)并保存runner；dummy_run为pass，不能把调用该函数当作已预热树、已捕获draft图或已经实际运行提议。

Ascend propose接受num_tokens_no_spec/token_ids_cpu等可选参数，但本方法不读取它们，而是转发num_speculative_tokens、runner.input_batch、sampled_token_ids和slot_mappings给原生类。所读model_runner.py分支传入scheduler_output.num_spec_tokens_to_schedule及valid_sampled_token_ids；进入分支前会清旧_draft_probs/_draft_prob_req_ids。这里的固定K约束与原生assert需同时满足，不能用绕过assert解决动态预算不一致。

工厂当前还按版本lane限制Medusa于v0.32.0，其他MTP/EAGLE/DFlash等另有架构分支；名字同属speculation不使其共享Suffix缓存或参数协议。本次没有导入torch、Arctic、Runner或执行propose，CPU提议、目标数值/采样一致性、缓存内存与端到端净收益分别验收。
