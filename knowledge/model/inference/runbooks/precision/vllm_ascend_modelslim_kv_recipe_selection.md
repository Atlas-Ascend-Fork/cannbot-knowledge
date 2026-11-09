---
type: Runbook
title: vLLM Ascend ModelSlim KV：recipe存在但未启用或scale被错误映射
description: 区分FAKQuant、Indexer、INT8 C8和MXFP8 KV的使能与层选择，按当前引擎配置排查recipe误激活、遗留scale和错误Attention类。
tags:
- task.debugging
- topic.precision
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/modelslim_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/utils.py
  role: constraint
created_at: '2026-10-29T11:32:34Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T11:32:34Z'
---

# vLLM Ascend ModelSlim KV：recipe存在但未启用或scale被错误映射


## 症状与证据边界

描述文件含KV recipe却运行未启用、缺少/多余fa_q/k/v scale、scale落到错误的mla_attn子树，或hybrid非全Attention层被安装错误方法。固定ceac1a2b有多套独立KV量化分支，不能只检查checkpoint名称或一个C8标记。来源没有覆盖本卡全部分支的产品范围，保持draft；本次未复现设备故障。

## 分开记录四条路径

| 路径 | 描述与层选择 |
| --- | --- |
| FAKQuant | fa_quant_type开启，fa_k.scale条目收集层；另受MLA、非SFA、cache dtype及PD角色/FP8能力限制 |
| Indexer | indexer_quant_type开启，按indexer.quant_type层列表；逐层类型优先，缺省再用全局类型 |
| 普通C8 | kv_cache_type='C8'，k_proj.kv_cache_scale条目收集层，K/V scale/offset映射到attn缓存参数 |
| C8-MXFP8 | 当前引擎cache_dtype='mxfp8'才是开关；全局旧recipe或逐层新recipe只决定checkpoint是否携带相应V scale |

get_quant_method的Attention分支按FAK→Indexer→C8→MXFP8 full Attention的顺序判断，不是所有标志并行套用。MXFP8只给_is_full_attention_layer实际识别的Attention类，不能对任意AttentionLayerBase子类安装。

## recipe不是运行开关

MXFP8旧recipe为K_DYNAMIC_V_STATIC_MXFP8_PER_CHANNEL，新recipe为self_attn.quant_type中的QK_MXFP8_DYNAMIC_V_MXFP8_PER_CHANNEL。只携带recipe而未设mxfp8会告警并保持未启用；显式启用却无recipe则V scale可能使用中性默认，需核对真实权重/数值，不能据此宣称已得到校准量化。

enable_mxfp_c8_quant查询当前VllmConfig；构造或mapper阶段若上下文缺失会返回False，不能将这一时刻缓存为最终结论。相反DSV4的独立plan要求显式传入引擎config，见[缓存计划](../../guides/integration/vllm_ascend_dsv4_kv_plan_contract.md)，不要把两个模块的上下文规则混用。

## scale名称和互斥

MXFP8动态量化Q/K，只将fa_v.scale映射到attn.v_cache_scale；legacy Q/K scale/offset和V offset无消费者，按专用suffix处理。get_cache_scale_mapper发现MXFP8与FAK同时开启时关闭FAK，避免把V scale错误移入MLA命名空间。未启用MXFP8时不能无条件丢弃这些字段。

FAK/Indexer的regex带防重复映射条件，适配嵌套模型多次AutoWeightsLoader；ModelSlim的HF mapper也保留optional元数据并避免同一mapper重复应用。删掉这些检查或全局字符串替换可能让文件能加载却丢失scale归因。

## 探针、修复与验收

保存原始描述、mapper前后keys、有效cache_dtype、各enable标志/层列表、被ignore字段及每层最终quant_method。分别验证普通Attention、MLA/SFA、hybrid其他层和嵌套loader；FAK要求对应校准权重，不以强制标志绕过缺失报错。

修复正确开关、层类或名称映射后检查真实缓存dtype/layout与输出；对PD同时核对角色和两端格式。未闭合时恢复已验证KV路径与完整权重，不把中性scale当精度修复。本次仅静态阅读，不声明真机验证。
