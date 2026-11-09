---
type: Guide
title: vLLM Ascend V4.1 草稿适配：延迟mHC、SWA缓存与复合配置
description: 接入V4.1块草稿时，核对辅助残差捕获、FP8主投影的复合配置、普通与packed SWA写入及权重映射，按实际调用验证padding状态和Sink热加载。
  V41草稿DeepseekV41DSparkModel.forward的is_padding生命周期：SP替换mask后正常返回不在本方法恢复，需核外部context收尾。
aliases:
- DSparkDeepseekV41ForCausalLM
- DeepseekV41DSparkModel
- DeepseekV41DSparkSWACache
- V41草稿
- DeepseekV41DSparkModel.forward：V41草稿is_padding生命周期
tags:
- task.implementation
- topic.model_adaptation
- topic.speculative_decoding
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/model.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/dsa_v41_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/mixed_quant_attention.py
  role: implementation
created_at: '2026-10-31T05:08:01Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-02T09:46:26Z'
---

# vLLM Ascend V4.1 草稿适配：延迟mHC、SWA缓存与复合配置

## 任务与固定边界

为适配Agent接入DeepSeek V4.1的DSpark模型接口，为性能Agent识别合并上下文投影、复制权重、缓存格式和图注册的成本。依据Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的deepseek_v41/dspark.py完整665行、专属UT完整406行，以及明确列出的config、Runner、target forward、CP选择和Device writer片段。没有导入这些模块、运行测试或取得NPU结果，整项硬件范围保持未知，使用draft/空平台。

V4.1草稿复用一些[V4草稿](vllm_ascend_dsv4_dspark_adapter.md)和[通用块采样](vllm_ascend_dspark_block_markov_contract.md)接口，但delayed mHC、SWA backend、packed写入、复合配置和checkpoint head名字有独立约定。部署、CED/Engram及已有教程冲突仍见[V4.1模型指南](../models/vllm_ascend_deepseek_v41_platform_boundary.md)；本卡不从教程A2/A3或源码A5字样扩大整项支持范围。

## 复合配置与实际草稿类

DSparkDeepseekV41ForCausalLM使用DeepseekV41DSparkModel，decoder选择DeepseekV41DSparkDecoderLayer，其attention_cls为DeepseekV41DSparkAttention。配置基础来自draft_model_config.hf_text_config并经normalize_deepseek_v41_config处理；量化主投影另从外层hf_config读quantization_config，不能把两个对象当相同资料。

normalize函数补缺失的num_hash_layers=0、n_group=1、topk_group=1，复制并补RoPE字典默认值，补image sentinel/pad ID和Engram rotation配置。setdefault保留已有值；它没有验证所有字段类型、训练basis、旋转参数或checkpoint完整性，不能靠补默认值宣称新模型已适配。

n_mtp_layers优先，缺失时读dspark_num_mtp_layers、缺省3，零值经or回3。源码类注释的“三个serial draft blocks”描述默认模型深度，实际层数由配置决定；不能将它解释为普通MTP逐token重跑或固定K=3。运行时层key仍为num_hidden_layers+i，checkpoint prefix为mtp.i。

## 辅助特征：进入层之前的残差

NPUModelRunner._get_eagle3_aux_layers_from_config先采用父类非空结果；否则在use_dspark分支解开hf_config.text_config，优先dspark_target_layer_ids，再读target_layer_ids，逐项加1转为Runner的一基编号。外层同名字段不会在解包后自动补给内层。源UT的[37,38,39]变为(38,39,40)，只证明该调用例，不能替代实际checkpoint tap确认。

已读target forward在layer.layer_idx+1命中时，取进入该层之前的hidden_states.mean(dim=1)，位于该层Engram及decoder调用之前。SP下先all-gather并裁到真实token数；decoder replay循环按同一层边界补aux。它不是最终weighted hc_collapse、最终norm或Kimi raw-prefix-sum流；tap次序、捕获时刻与训练特征必须一致，拼接宽度正确只是必要条件。

combine_hidden_states对拼接aux执行main_proj/main_norm。草稿forward把embedding扩为hc_mult份，pre_mix初始化为FP32、首列1，其余0，逐层传递hidden/pre_mix，最后调用该decoder层的hc_collapse。源内仍有hc_head辅助方法，但这条forward不调用它，构造中也未建立V4式全局HC head参数；不能仅按同名函数套用V4的聚合或旧checkpoint key。

SP路径分片hidden与input_ids，末尾sp_all_gather后裁回positions行数。开启skip-padding且有forward context时，会将is_padding换成分片mask，本方法正常返回前也没有恢复。专属UT名中的“restores output”指输出恢复，实际断言context仍为[False,True]两行；外部生命周期如何重置需另核对，不能沿用V4的正常路径恢复结论，也不据此直接宣称线上故障已复现。

## 主投影量化与合并WKV

context_wkv_proj继续用mtp.0.self_attn.wkv选择真实checkpoint量化prefix，disable_tp=True，并通过V4的_duplicate_context_wkv_weights把原逐层WKV输入附带shard_id再加载一份合并参数。保留逐层参数、每TP rank新增合并权重及量化元数据，detach共享输入storage不能消除这些模型内存成本。

V4.1的main_proj只在两个条件同时满足时接收quant_config：DeviceOperator.get_dsv41_packed_cache_ops()非None，且外层hf_config.quantization_config.quant_method精确为fp8。读取text config上的同名字段、仅发现FP8权重文件或仅启用target量化，都不证明进入了该分支。来源注释称release checkpoint的主投影为FP8，BF16构造会缺main_proj.scale；这里没有下载该权重或抓取实际错误日志。

非空context仍先跑合并投影，再在没有slot mapping时返回，确保workspace profile包含投影；空states或positions则提前返回。逐层mapping为None时跳过，长度及行对齐由调用者保证。RoPE准备一次包含全部实际层的配置；本实现split NoPE/RoPE、消费旋转返回值，再cat/view/contiguous，未采用V4的输入view无cat复制路径。性能比较须分别量化launch、复制、额外权重和workspace，不从结构差异猜收益。

## SWA spec、CP选择与图注册

DeepseekV41DSparkSWACache沿用父spec的block、head、dtype、window、model_version和bounded_replay等字段，实际返回AscendSlidingWindowMLASpec，backend为DeepseekV41CacheBackend。源注释仍提DeepseekV41DraftSWASpec，不能凭旧名字创造另一种运行时spec或manager。

Attention构造V41LayerRole，compress_ratio=0、无KV/index/candidate source及Engram slot；建立CP-aware v41_impl，并以prefix.v41_attn把自身加入static_forward_context，forward复用DeepseekV41Attention.forward。这只给出接线，不能用对象存在代替真实Attention、图更新或NPU执行。

get_v41_cp_classes按当前消费config选择：legacy DSA-CP与PCP同时启用会ValueError；单独DSA-CP、PCP、都不启用分别得到不同metadata builder/impl。源注释指出target可用PCP而复制草稿另建PCP=1配置，因此不能把target PCP值直接拿来选择draft类。具体复制、同步和元数据仍按[query/KV状态合同](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)验收。

bounded_replay字段传播也不表示该草稿自动进入所有target回放优化；开关、架构allowlist、cacheable组PAD保护和decoder裁剪按[有界回放](vllm_ascend_swa_bounded_replay_contract.md)核对。

## packed和普通SWA写入分别消费slot

writer取cache.kv_cache[0]并把shared_kv squeeze为[token,head_dim]。slot为空返回；它没有V4的cache缺失/单元素容器递归解包合同，调用者须提供实际cache结构。

| 路径 | slot与写入行为 | 适配时保留的条件 |
| --- | --- | --- |
| packed_cache_ops存在 | 原线性physical slot直接传write_attention_cache，kind="win" | 不先改成[block,offset]；保留真实packed cache与设备writer。 |
| 普通cache，一维slot | 按cache.block_size算block/offset，INT32；原负值再mask为[-1,-1] | clamp_min(0)只是中间计算，不能把PAD写到block0；原始负值语义仍需kernel证据。 |
| 普通cache，已格式化slot | 原格式传scatter_cache_sk | 不二次除以block size，不借target或其他cache组地址。 |

DeviceOperator在模块导入时按hardware profile的adaptor_family选类：Base返回None，FP8_OPTIMIZED的A5 adaptor返回MixedQuantPackedCacheOps。按实际进程的选定对象核对；类名、环境晚改或一个静态方法不能证明每个SKU与软件包ABI均支持。

已读packed writer的win分支把cache按float8_e4m3fn重解释，group32、quant_mode="mxfp8_bf16"；cmp另为group16/mxfp4_bf16。随后调用kv_compress_epilog_v2，values/slots contiguous、round_scale=True、x_scale=1.0。view是位模式重解释，不是数值cast；这些参数不构成完整物理布局、负slot处理、量化精度或NPU算子正确性的证明。不要用V4的TurboQuant/compress-scatter路径替换此writer。

## V4.1的checkpoint名字与热更新边界

基本mtp层号、第一层main投影/最后层norm和head的映射沿用同类结构，V4.1另将markov_head.embed.weight改为markov_w1.weight、markov_head.head.weight改为markov_w2.weight，以及confidence_head.weight改为confidence_head.proj.weight。packed_modules_mapping声明gate_up_proj的gate/up成员；量化描述、实际params_dict和当前loader仍要一致。

vision-only e_score_correction_bias_vl仅在目标参数不存在时忽略，不能别名到文本router；loaded_params仍只是唯一名称集合。旧全局HC key、错误stage或缺失必要参数不应吞掉KeyError后继续。full-vocab恒等映射、可选Markov draft_vocab_size、inputs_embeds签名和confidence模块，也不代替真实词表/权重/采样验收。

V4.1 attn_sink分支在no_grad下直接copy_，普通TP先切本rank heads，DSA-CP则保留完整sink。V4的更新实现改走weight_loader，其CPU layerwise-meta回放测试没有参数化V4.1。因此，若实际V4.1外层采用同样依赖loader记录的meta回放机制，直接copy_存在更新未被回放的风险；这是有条件的源码推断，尚无V4.1专属复现或修复结果。

热更新先固定实际loader/包装、参数设备和原storage，逐rank检查更新后sink数值，再恢复服务；不能把[V4测试结论](vllm_ascend_dsv4_dspark_adapter.md)或[RL传输完成](vllm_ascend_rl_weight_update.md)当此分支已验收。这里没有改上游源码或执行更新。

## 来源UT和Agent验收

专属测试模块首先importorskip Native DeepSeek V4.1 config；版本缺失会跳过，不能报通过。10个测试函数及CP/draft-vocab参数化主要使用mock、Identity Linear或最小对象，覆盖spec/manager接线、aux +1与进入层残差、plain/CP类选择、SP输出、普通/packed slot写入、复合FP8主投影、合并WKV加载和context投影分层选择，没有本仓执行结果。

cache示例block128、head512、BF16、131072 bytes/page只是该测试配置，不能推广全部packed布局。slot样例[129,-1,258]在block128下变为[[1,1],[-1,-1],[2,2]]，packed mock收到原slot对象/kind="win"；它不验证真实Device ABI。aux toy层的输出hidden+6、aux hidden与hidden+3也不是完整模型质量。

交付时保存实际类、两个HF config、tap顺序与捕获时刻、主投影scheme、草稿层数、SWA spec/slot、CP配置、static context及真实加载键。先对齐辅助特征、权重和cache，再验证logits/Markov/无投机参考，之后逐项增加SP、图、CP、回放或P/D。异常、slot错配、参数缺失或更新数值不符时关闭新增路径并恢复匹配checkpoint/配置；保持失败证据，不以HTTP输出或预期接受率替代精度和性能验收。

本卡来源范围仍不包含完整target/Engram/CP metadata、Native、Device或全部平台组合闭合；没有上游import、安装/build/测试、服务、NPU或Agent A/B，也未证明最终站点HTML映射。
