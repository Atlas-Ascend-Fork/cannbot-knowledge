---
type: Guide
title: vLLM Ascend 量化方案适配：ModelSlim 层映射、scheme 与加载生命周期
description: 按 quant_type 和 layer_type 注册量化方案，核对 packed 模块的一致性、prefix 映射与 create/load/process/apply 生命周期，区分格式识别和实际算子支持。
tags:
- task.implementation
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/quantization.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/registry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/modelslim_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/method_adapters.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/quant_type.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/quant_parser.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/quantization.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/quantization/get_quant_method.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/quantization/quant_algorithm_overview.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/quantization/quant_method_base_class.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/quantization/quant_method_call_flow.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/quantization/quant_methods_overview.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/configs/modelslim_config.py
  role: primary
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-11-03T06:28:46Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 量化方案适配：ModelSlim 层映射、scheme 与加载生命周期

## 范围与前提

本卡说明 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 标准量化后端的新方案接入；310P 有独立量化配置，不能由本卡保证相同 override 与算法支持。首先让目标浮点模型正确运行，固定量化工具、权重、描述文件和校准数据，再增加量化实现。

## 从格式到逐层实现

ModelSlim 使用 `quant_model_description.json` 描述每层权重和参数。AscendModelSlimConfig 根据 prefix、模型名映射和 packed_modules_mapping 确定量化类型，再以 `(quant_type, layer_type)` 查 scheme。Linear、MoE、Attention 的契约不同，同名 W8A8 不代表所有层可复用一套实现。

`register_scheme` 对重复 key 抛错，查询不存在的 key 返回 None，构造层须检查缺失。只有注册语句而模块未导入，也不会自动得到可用方案。新增类型先明确位宽、静态/动态、scale 粒度和适用层，再实现和导入，不为一个未知模型临时跳过检查。

## 加载与运行生命周期

| 阶段 | 必须明确的契约 |
| --- | --- |
| create_weights / scheme 参数创建 | 权重、scale、offset 的 shape/dtype、分片轴和额外 loader 元数据 |
| checkpoint 加载 | 原始 key 到模型 prefix、合并 QKV/FFN、专家号与 rank 分片的对应 |
| process_weights_after_loading | transpose、格式转换、打包、scale 重排及实际参数替换 |
| apply | 激活量化、算子参数、输出 dtype、bias 和通信/多流消费关系 |

不能只让 load_weights 不报错；必须检查加载后的真实 dtype、stride、scale 和生效 scheme，尤其是按模型层名选择不量化部分时。

## Packed 模块和混合精度边界

同一 packed 模块展开后的 shard 默认要求量化类型一致，不一致会明确报错。当前有针对 Gemma4 缺省 v_proj 和 Kimi K3 混合 KDA 投影的专门分支，不能将这些例外推广成任意 shard 缺失或混合类型均可接受。

映射补充进入 `UPDATED_PACKED_MODULES_MAPPING`，专家 shard 可从描述发现；当前实现复制 mapping 后再修改，避免污染模型类上被 LoRA 等消费者复用的字典。prefix_mapper 应作用于正确的层/末级投影，不全局替换同名字符串。

## 验收与回退

对代表性层比较浮点参考、反量化结果和量化输出，覆盖尾块、分片边界、跳过层与专家路径；再测目标模型的实际精度、显存和性能。shape/dtype/scale 不匹配、遗漏权重或 scheme 未生效时停止调优，恢复原权重和方案。未知硬件保持待确认，缺少registry的层类型保持明确拒绝，不用注册成功替代执行验证。

## Evidence

量化设计文档与 registry、ModelSlimConfig、method_adapters 支持接口和流程说明。本次完成源码核对，未生成量化权重或运行精度/性能测试。


## 平台证据待补

量化接入设计和标准scheme/config代码没有整项适配流程的平台支持表；平台注册不能证明所有scheme/层类型均可执行。据此撤回原平台枚举，保持draft/空平台；这是证据不足，不能解读为这些平台不支持。

## 描述文件、namespace与注册时机

只有quant_method/model_quant_type的HF元数据不是真正逐参数描述；from_config将其保留为format metadata，maybe_update_config再从本地或固定revision的远程模型读取quant_model_description。描述已填充时不重复加载；文件缺失给明确错误，不能把失败下载当作浮点权重证明。

HF→vLLM mapper映射参数keys时保留optional原schema，同一mapper对象重复应用会跳过；packed shard先在runtime namespace展开末级投影，再逐项映射，避免对早先同名片段做全局replace。Kimi K3已知混合KDA布局需先拆quant Q/K/V与FLOAT gates；Gemma4只允许有Q/K证据的缺V情形，其余缺shard仍报错。

root quantization包以__getattr__延迟加载重类，quant_type和prepared_linear_input可保持轻量；methods/__init__批量导入实现以触发scheme注册，configs/__init__也会导入配置类。只写decorator、却未在实际消费进程完成对应导入，不等于registry已有条目。registry仍拒绝重复key。

## 新MoE方案不止实现apply

AscendFusedMoEMethod保留Ascend自己的communication/forward路径，maybe_make_prepare_finalize返回None阻止上游modular初始化替换它；不能只照搬上游kernel构造。stage式MLP的apply_gmm1、apply_act_quant、apply_gmm2、get_mlp_weights或fused-MC2 payload默认可抛NotImplementedError，需按真正启用的消费路径实现。fused_activations默认空，不因存在apply就自动支持融合激活。

A16路径保留高精度激活并无dynamic scale；其他scheme按QuantType选择普通或MX动态量化，已经有scale时不重复量化。MX内部scale归一化与整型INT8不同，不以“A8”字符串统一dtype。quant_parser的MoE down-proj回退除W4A4_MXFP4可保留指定round mode外，其他路径收紧为rint；枚举、解析映射与实际scheme注册也不是同一支持层。

scale分片细节见[TP边界诊断](../../runbooks/precision/vllm_ascend_quant_scale_tp_sharding.md)，多流hook见[PreparedLinearInput接入](vllm_ascend_prepared_linear_overlap.md)，KV recipe/名称优先级见[缓存量化诊断](../../runbooks/precision/vllm_ascend_modelslim_kv_recipe_selection.md)。EPLB活动权重与提交仍按[已有契约](vllm_ascend_eplb_model_weight_contract.md)单独验收。本次仅阅读接口和实现，未运行这些路径。


## 中文适配设计与七类算法声明

developer_guide/Design_Documents/quantization.po的31条有效非空译文已完整对照英文，msgid精确匹配，0fuzzy/obsolete。量化description、注册/导入、packed mapping、权重生命周期和算法列表按固定设计理解；PO条数不是实际scheme支持矩阵，也不能凭某条W4A8声明绕过层/硬件门禁。

| 设计所列算法 | 核心参数区别 | 新模型仍要验证 |
| --- | --- | --- |
| W4A16 | INT4权重、FP16/BF16激活，权重按组，MoE专家int32打包 | pack/分片/层类型与真实算子 |
| W8A16 | INT8权重、高精度激活，权重按通道 | 线性层布局、输出与平台 |
| W8A8 | INT8权重和激活，静态激活scale | 校准、offset/bias及逐层参数 |
| W8A8_DYNAMIC | INT8权重、逐token动态INT8激活 | 真实激活/scale及尾部shape |
| W4A8_DYNAMIC | INT4按通道权重、逐token INT8激活 | 设计列ModelSlim/LLM-Compressor的MoE格式，仍分别核对入口与scheme |
| W4A4_FLATQUANT_DYNAMIC | INT4权重/激活，FlatQuant平滑及额外矩阵乘法 | 变换矩阵、精度与实际计算成本 |
| W8A8_MIX | P/D共部署都动态；分离时P动态、D静态 | 两侧权重/scale与KV/通信合同，不能仅按MIX名字共用任意权重 |

这是主设计中的七类说明，不是枚举当前源码所有scheme或为每行声明全部硬件可用。静态/动态描述的性能、精度倾向不是跨模型保证；激活分布、校准数据、kernel、batch与并行变化都要在实际验收中固定。不能将动态必然更准或静态必然更快写作Agent无条件选择规则。

设计强调先有正确浮点模型，再补packed_modules_mapping/UPDATED_PACKED_MODULES_MAPPING、量化描述和各层算法实现。该要求不等于改一张mapping就完成新模型适配；尤其混合KDA、缺V特例、MoE stage hooks和非量化层仍遵守前述实现合同。本次没有转换权重、注册/调用新scheme或执行精度/性能测试。

## 五张量化图的接线用途

固定图示将配置注册→VllmConfig/quant_config→get_quant_method→逐层method wrapper分开；wrapper持有实际quant_method，QuantizedMethodBase的create_weights、embedding、process_weights_after_loading和apply不是同一个阶段。调用流程先分配参数，再load_weights，再做可选后处理，最后forward/apply；“注册成功”或“参数已写入”不能跳过布局和实际消费者核对。

算法图仅列当时设计中的部分W8A8、W4A8、FlatQuant、W4A16/W8A16映射，不是完整当前registry。图中某类型只画MoE或没有MXFP4等分支，均不能据缺项判对应Linear/FP4方案不支持；按现有[WnA16布局](vllm_ascend_wna16_weight_layout_contract.md)、[W4A4方案](vllm_ascend_w4a4_quant_transform_contract.md)和实际注册/导入判断。图也没有提供所有scheme、模型与硬件可互换的证据。


## 3164 版本补充：fused 描述与 loader 生命周期

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，完整 unified diff 与上下文已读；不把增量阅读标为目标整文件FULL，没有执行上游、NPU、真实collective或性能验证。

`_find_quant_description_key` 优先 prefix.weight，其次 bare prefix。packed模块先在runtime namespace展开，再映射整个prefix和shard。存在部分normal shard却缺其他normal项时直接KeyError，不与fused alias混配；仅当没有normal项才接受模块直接描述，或experts的gate_up_proj+down_proj组合。所有选中项仍需量化类型一致，FLOAT返回None；Gemma4缺V例外保留，不推广成任意缺shard。

MoE scale-bias名称映射现在区分 bound method。用MethodType将wrapper绑定同owner，闭包只保留unbound函数，并手动复制函数元数据/flags，避免functools.wraps的__wrapped__保留bound layer。来源动机是Native meta reload的sanitize_layer_refs只识别特定bound method引用；该变化不证明任意callable或所有Python对象环均被消除。非bound callable保留旧wraps闭包行为。新增W4A8_DYNAMIC Linear通过methods包导入注册，详见[INT4 Linear接入](vllm_ascend_w4a8_int_linear_contract.md)。
