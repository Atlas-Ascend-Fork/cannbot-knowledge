---
type: Guide
title: vLLM Ascend Xlite 新模型适配：架构注册、权重、RoPE 与 KV 合同
description: 沿 XliteModelBase 和 StandardXliteModel 核对首架构注册、get_layer_weights、量化scale、RoPE与MHA/MLA/DSA缓存；区分Host接线与外部xlite._C的ABI及Device验证。
tags:
- task.implementation
- task.debugging
- topic.checkpointing
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/xlite.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/graph_mode.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/xlite_model_runner.py
  role: implementation
created_at: '2026-10-29T23:07:05Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T23:07:05Z'
---

# vLLM Ascend Xlite 新模型适配：架构注册、权重、RoPE 与 KV 合同


## 消费任务与固定范围

用于新模型已有原生Ascend runnable、准备接入Xlite，或启动后缺权重、KV布局不符、RoPE/量化数值偏差的定位。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与参考vLLM v0.32.0；这里只蒸馏Host适配层。整项硬件/模型矩阵没有被完整证明，保持draft/空平台，不由某个已注册类推出所有权重变体与量化均可用。

## 架构身份与初始化顺序

get_adapter_xlite_model只查model_config.architectures[0]；不是依次尝试列表中所有候选。没有映射会raise ValueError（not supported!），不会自动改用原生forward。XliteModelBase.__init_subclass__检查metadata类型与_supported_architectures，重复架构注册同样raise；新增架构应明确唯一adapter，不能靠覆盖顺序接管。

固定主指南和实现声明11个architecture字符串，按以下adapter划分。这是代码映射范围，不是本地运行结果，也不是名称相似模型的通配符。

| Adapter | 声明架构 |
| --- | --- |
| StandardXliteModel | LlamaForCausalLM、Qwen2ForCausalLM、Qwen3ForCausalLM、Qwen3VLForConditionalGeneration |
| QwenMoeXliteModel | Qwen3MoeForCausalLM、Qwen3VLMoeForConditionalGeneration |
| Glm4MoeXliteModel | Glm4MoeForCausalLM |
| DeepseekV3XliteModel | DeepseekV3ForCausalLM |
| DeepseekV32XliteModel | DeepseekV32ForCausalLM、GlmMoeDsaForCausalLM |
| MiniMaxM2XliteModel | MiniMaxM2ForCausalLM |

adapter保留runner.fallback_model作为权重权威，先定位RoPE，再创建XModelConfig/XModel，调用_build_model_config、_build_model、native init，最后准备RoPE cache。已有原生模型加载完成不表示这套提取与native init成功。VL路径从language_model.model.layers取层及prefix；普通路径取model.layers，需核对PP本地层与实际容器。

## 配置、权重与扩展ABI逐项对齐

StandardXliteModel提取head、KV head、head_dim、层数、norm_eps、词表、TP/DP及条件EP配置；weight_nz_mode==2与量化对象存在是不同判据。quantization字段由quant_config是否非None推导，不能代表每一种scheme、packing、bias或activation dtype都已被native引擎支持。

_build_model把embedding/norm/head、QKV/O、dense与shared/routed expert权重映射到native属性，按模型条件处理QK norm和bias；tied head可以引用embedding。核对真实处理后storage、layout、每层数量及本地expert顺序，而非只比较checkpoint原始名字。原生加载流程与[RFork预布局接线](vllm_ascend_rfork_processed_weight_loading.md)解决不同阶段的问题，不能把传输成功当Xlite提取成功。

get_layer_weights按候选模块路径逐层取值：无mask时可能略过缺失层，有mask时可填_DUMMY_TENSOR。非空的占位列表也可能结束候选查找，不能从返回list非空推断每层有真实权重。postprocess仍可能作用于placeholder，contiguous只在配置要求时检查；二次flatten与mask有互斥限制。适配时分别核对候选命中、层索引、mask、真实tensor数量和转换后dtype/stride。

AttributeSetterMixin默认对不存在的native字段warning后忽略，日志含Your `xlite` version might be incompatible.；未抛异常不证明Python与xlite._C ABI相容。condition是每实例/每线程的条件栈，嵌套按AND且finally恢复；它只约束最终赋值，右侧get_layer_weights或转换仍先求值。该机制不是native对象修改的事务或跨线程同步。

_transform_deq_scale对int64直接返回；其他输入转FP32，新建长度为shape[0]两倍的零数组，把scale写入偶数位置。注释描述fixpipe/TF32消费格式，但Python没有显式uint64 cast或低10bit清零步骤；应核对实际外部ABI、预期一维shape及bits消费方式，不把注释替代转换结果证据。

## RoPE与KV按注意力族分别适配

基础RoPE从现有cossin_cache或_compute_cos_sin_cache取得，Standard路线再转模型dtype；MLA路线构造complex64表示，检查二维与最后维偶数，按条件处理Yarn缩放。没有找到RoPE时的占位不是所有新模型都可以无RoPE运行的保证。mRoPE与deepstack字段也需要与真实VL结构对应。

| 缓存族 | 固定Host提取 | 需要额外核对 |
| --- | --- | --- |
| MHA | 截取前2*n_layers项，检查最后维，zip成K/V对 | 没有由此完整保证总数量，奇数尾项可在zip中被截断；核对层顺序、dtype、stride、alias与生命周期 |
| MLA | 按kv_lora_rank与rope_head_dim过滤，拒绝两者相等，截到层数并检查所需数量 | 最后维分类依赖角色维度可区分，不能替代真实layout及地址身份 |
| DSA | 按NoPE/RoPE/index维度分类，拒绝index维与其他角色冲突；按index mask补位并组成三元组 | mask与full层声明要匹配；局部数量检查不证明所有缓存格式或native执行正确 |

set_dummy_tensor在utils中重新绑定全局_DUMMY_TENSOR；xlite.py使用from-import取得的同名引用不会因该rebind自动更新，DSA占位使用该导入引用。这是静态Python名字绑定事实，可能需要结合外部消费方核验；未执行扩展，不能据此声称已复现CPU/NPU占位故障或给出已验证修复。

_TensorRepr会压缩重复/超过上限的列表项，并在对象repr中略过全空tensor值；可显示shape、必要时stride、dtype及NPU非ND格式。压缩日志不是完整每层清单，也不证明未展示字段不存在或真实权重完整。

## 新模型交付与停止条件

先冻结architecture、原生runnable结构和外部扩展实际版本/内容身份，再核对配置→真实权重→RoPE→逐层KV→metadata接口，最后接[Runner选路](vllm_ascend_xlite_runner_dispatch.md)。缺层被略过、字段warning、角色维度碰撞、layout/alias未确认或输出不一致时，停止性能结论，修复接线并重新对照原生输出。

覆盖单请求、多请求、prefill/decode混合、不同TP/DP/EP、投机回退和VL输入；分别记录路径、输出误差、启动/内存/稳态性能。本文未导入xlite/torch，未执行上游UT、模型、NPU或基准；外部xlite._C、Device kernel、全部量化与硬件模型组合仍须继续生产和验证。
