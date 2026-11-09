---
type: Guide
title: vLLM Ascend MoE路由接入：TopK分派、分组门禁与Host tiling
description: 从router factory与AscendFusedTopKRouter追踪softmax/sigmoid的DeviceOperator分派，区分自定义MoeGatingTopK与A5 TorchNPU归一化位置；核对专家分组、2048上限、256专家特化key、Meta弱校验及950 tiling限制，避免把推形成功或同名入口当作完整算子支持。补充普通Device与Hash视觉路由的bias选择、padding恢复、查表索引、归一化、流水及静态缺口。
aliases:
- check_npu_moe_gating_top_k
- AscendFusedTopKRouter.is_fused_supported
- create_ascend_fused_moe_router
- vllm_ascend::moe_gating_top_k
- MoeGatingTopKTilingBase
- MoeGatingTopKTilingRegbase
- MoeGatingTopKWithoutGroup.SelectTopKExpertScore
- MoeGatingTopKHashRegbase.HashCompute
- MoeGatingTopKHashTilingBase.GetTilingKey
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.mixture_of_experts
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/moe_gating_top_k_torch_adpt.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/router/router_factory.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/router/fused_topk_router.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/moe_gating_top_k_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/moe_gating_top_k_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/moe_gating_top_k_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/moe_gating_top_k_tiling_arch35.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/moe_gating_top_k_tiling_base.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/moe_gating_top_k_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_kernel/moe_gating_top_k.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_kernel/moe_gating_top_k_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_base/tiling_templates_registry.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_base/tiling_base.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/math_util.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_host/moe_gating_top_k_proto.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_kernel/common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_kernel/error_log.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_kernel/moe_gating_top_k_e_k_fullload.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_kernel/moe_gating_top_k_generalized.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k/op_kernel/moe_gating_top_k_without_group.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_host/moe_gating_top_k_hash_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_host/moe_gating_top_k_hash_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_host/moe_gating_top_k_hash_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_host/moe_gating_top_k_hash_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_host/moe_gating_top_k_hash_tiling_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/arch35/common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/arch35/moe_gating_top_k_hash_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/common_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/moe_gating_top_k_hash.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/moe_gating_top_k_hash_e_k_fullload.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/moe_gating_top_k_hash_generalized.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/moe_gating_top_k_hash_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/moe_gating_top_k_hash/op_kernel/moe_gating_top_k_hash_without_group.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/gate_linear.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/router/grouped_topk_router.py
  role: implementation
created_at: '2026-11-03T01:57:16Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MoE路由接入：TopK分派、分组门禁与Host tiling

普通TopK在7d9e已改走CANN原生torch_npu入口，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的MoE节。以下旧自有adapter/kernel机制只适用于对应旧提交，不能据此推断新入口的ID dtype、内部算法或SDK支持范围；hash/vision路线另核对。

## 任务与证据范围

本卡帮助新MoE模型接入时分辨router对象选择、实际硬件adaptor、打分归一化和自定义算子的Host合法域。它补充[路由权重只应用一次](../../runbooks/precision/moe_router_norm_topk_prob_fused_topk_npu.md)的历史排障规律，不更改历史来源的版本语义，也不把某个专家数特化解释为所有模型的硬上限。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。全文读取router_factory118行、fused_topk_router241行及该TopK族11份Host/入口/构建文件；共享device_op258–289/1221–1249/2095–2104、torch_binding3155–3169、Meta519–553及1824注册、公共tiling注册和执行框架只读所列有界范围。共享来源保留旧canonical owner。

这是模型框架接口与Device静态执行facet。追加范围已完整审阅普通三模板与Hash Host/Device族，采用完整代码投影及同族基线与全部差异阅读；外部AscendC排序、SoftMax、MicroAPI和真机行为仍未闭合。普通950自定义实现仍有源码依赖缺口；固定目录中的APT入口引用`arch35/moe_gating_top_k_regbase.h`，该路径未在本次固定源码树中定位，不能据Host文件存在宣称950自定义kernel已完整打包。没有构建或实际加载结果，也不将静态未定位写成已复现编译故障。未导入上游、运行测试、NPU、图、数值或性能实验；draft、空平台、framework=vllm范围仅记录已读框架合同。

## 对象工厂与运行时检查是两层门禁

factory先处理custom_routing_function，直接返回Native CustomRoutingRouter；随后兼容硬件能力走310P独立router。其余才调用`check_npu_moe_gating_top_k`：top_k≥1、1≤topk_group≤num_expert_group，评分限定softmax/sigmoid/sqrtsoftplus，sigmoid且不renormalize被拒。缺省group数均为1。这个函数没有校验router logits的专家维、k是否超过专家数、dtype或Host tiling全部限制，名称中的“support”不等于完整算子适用证明。

通过工厂检查可建立AscendFusedTopKRouter，未通过则建普通AscendGroupedTopKRouter。运行时`is_fused_supported`还检查传入hidden_states最后维对group数的整除、每组大于2，以及源码的两条top_k不等式；它使用的是hidden_states宽度，不是从router_logits读取E，不能替代后者真实专家维校验。bias_vl存在会绕过这项普通fallback判断，应单独核对视觉路由合同。

softmax/sigmoid路径将实际router_logits交给DeviceOperator，group_select_mode固定1，out_flag固定False，bias若dtype不同会先转换到logits dtype；norm_type分别0/1。适配时应保存factory参数、hidden_states和router_logits两套shape，不根据对象类名推断每次调用必走同一个kernel。

sqrtsoftplus走另一套hash/视觉分支，不是本卡普通MoeGatingTopK的norm_type扩展：需要时对input_ids作通信布局对齐、TP chunk、-1占位替换，再由能力决定Python视觉参考或`moe_gating_top_k_hash`。该分支向hash入口传norm_type2、renorm0；Hash Device静态语义见后文；所有token-id边界、表容量和完整Python/C++ ABI仍需按真实调用核对。

## STANDARD与FP8_OPTIMIZED分派不要混用

DeviceOperator由hardware profile的adaptor family选择。STANDARD的BaseDeviceAdaptor调用`torch.ops._C_ascend.moe_gating_top_k`，透传renorm/out_flag；FP8_OPTIMIZED的A5DeviceAdaptor调用`torch_npu.npu_moe_gating_top_k`，固定renorm=0且不传out_flag。若norm_type0且调用方renorm1，A5包装在Python用topk权重和再除一次，最后统一id为int32。

所以自定义Host对renorm的接受范围，不是TorchNPU原生路线的完整API文档；反之，A5包装的Python补归一也不能无条件搬到自定义路径。当前补归一代码没有额外clamp；全零/极端值是否可能以及处理策略需要实际数值证据，不能按其他视觉参考分支的clamp行为代替。

尤其当routed_scaling_factor非1时，应追踪缩放是在归一化前还是后，以及后续combine是否还加权。保留固定版本的逐阶段参考值；不能只比较专家索引，或在模型、算子、finalize三处各做同一份归一化。

## 自定义C++入口的形状和输出

adapter要求二维x，dtype为FP16/FP32/BF16。可选bias存在时必须同dtype、一维且长度E；输出y为`[rows,k]`并沿用x dtype，expert_idx同shape/int32，第三个out总会分配`[rows,E]`/FP32，即使out_flag=False。

out_flag=False不代表返回对象为None，也不意味着第三块数据有效或已初始化；普通模型router忽略它。Agent只应消费对应flag保证的结果，不能把empty分配当成已计算的全专家概率。

Meta检查x rank/dtype和bias rank/dtype，但没有真实adapter的bias长度检查，也没有完整k/group限制。InferShape甚至接受未知rank标记和k=0来推形，而Host tiling要求k>0。因此编译Meta通过、输出shape看起来正确或某个动态shape可推导，均不证明实际launch合法。

## 两套Host tiling的合法域与key

公共registry按较小priority先尝试：950 Regbase注册1000并在IsCapable限制ASCEND950，一般Base注册2000。公共DoTiling先读shape/attrs和platform，再判IsCapable；只有GRAPH_PARAM_INVALID继续后续模板，GRAPH_FAILED会终止。因此某个先尝试模板的实际校验失败，不能默认自动回退到较宽松实现。

两套都要求k>0、k≤E、E≤2048、group_count与k_group正值、k_group≤group_count、E能被group_count整除，且选中分组可容纳k。norm_type只接受0/1，group_select_mode只接受0/1；SUM模式还要求每组至少2专家。按32对齐后的组规模也受2048包络约束，不能只看原E≤2048便认为分组必然合法。

一般Base接受renorm0或1。其三个key为：

| key | Host选择条件 |
| --- | --- |
| 0，E/K特化 | E256、group_count8、k_group4、k≤32、有bias、SUM、renorm0、sigmoid且out_flag=False |
| 1，不需分组筛选 | group_count1，或group_count=E，或k_group=group_count |
| 2，一般分组 | 其余已通过Host校验的组合 |

因此256是特化谓词的一部分，不是当前Base的统一最大专家数。历史[CANN形状白名单排障](../../runbooks/compilation/fused_op_host_tiling_hardcoded_shape_whitelist.md)仍需结合其固定版本，不能套成当前所有TopK的256限制。

950 Regbase只接受renorm0、固定key10000；当k_group=group_count或group_count=E时会把内部组数归一成1，再按归一后的每组容量检查SUM和k条件。外部传入参数与内部tiling字段可以不同，排障时应同时记录。原生TorchNPU调用不等于自动使用本仓此Regbase源码，必须辨别实际加载库和接口。

两套从AIV核数分rows并预留16MiB workspace；这不是整条模型route、输出分配或其他通信缓存的峰值。所读SplitRows没有完整空rows成功短路，950版本甚至在检查perCoreRows前已用于除法。空EP rank应先核对上层空输入处理，不用零行输入直接推断Host支持或已复现故障。routed_scaling_factor/eps在所读Host中没有完整finite与数学域检查，也不从缺少拒绝推导数值合法。

## Agent验证顺序与未关闭边界

先固定Main、配对Native、TorchNPU/CANN、hardware profile和实际库，核对factory/运行时两层选择；再用真实router_logits核k、E、分组、bias、dtype、renorm及scale顺序。保留参考scores、选中ids、选中权重、缩放后权重与combine结果，覆盖group退化、带bias、不同score函数及重复归一化风险。

Host key和输出布局明确后，才分别验证Device排序/tie规则、极端值、空rank、图与异步存储寿命；后文补充已审读Device执行端；仍需解决普通950缺失依赖、外部原语及运行证据才能宣称完整算子闭包。与[GMM+SiTU接口](vllm_ascend_gmm_situ_quant_host_contract.md)协同时，TopK合法不代表后续group_list编码、FP4布局、计数容量和融合门禁已经成立。

## 普通Device：选择分数与返回权重是两条数据流

WithoutGroup和Generalized先将输入转FP32，计算全专家softmax或sigmoid，保留未加bias的`xNorm`；只把bias加到排序分数。选中专家的最终权重从原`xNorm` gather，不能把校正bias直接带进combine权重。out_flag=True写回的第三输出也是未加bias、未做TopK再归一、未乘routed_scaling_factor的FP32全专家分数。proto注释称其为renorm结果，Agent应以实际Device数据流为准；proto的renorm仅0说明也不能覆盖普通Base已实现的renorm1。

| 路径 | 专家选择与权重处理 |
| --- | --- |
| WithoutGroup | E补到32的倍数，排序尾部填负无穷；全量Sort后取k个ID，再从未加bias分数取权重 |
| Generalized | 每组专家数补到32；先组内Sort，按MAX或前2项SUM选组，再四路归并和多轮归并选专家；输出ID减去前面各组的padding |
| E256/G8/kG4特化 | 固定Sort32、组内前2项SUM和四路归并；按Host特化条件使用sigmoid、有bias、无out输出 |

普通三模板的sigmoid选择后都会除以`sum(selected_scores)+eps`，即使属性renorm=0；WithoutGroup/Generalized的softmax仅在renorm=1时再除选中权重和。之后统一乘routed_scaling_factor，FP16/BF16输出使用CAST_RINT。属性值0在这里不能直接读成“绝不再归一化”。Generalized padding值先负无穷参与softmax/sigmoid，排序前再屏蔽；真实ID恢复发生在用带padding ID从局部分数gather之后。

这些实现对每个core分到的row逐行计算。Generalized有Ealign×FP32×10临时区，WithoutGroup为Ealign×FP32×8，另有输入、bias、排序、输出和索引缓冲，不能只按Host workspace估计UB。E256特化复用sigmoid/sort临时队列并使用多槽流水；Generalized/WithoutGroup主要是一槽队列和显式MTE2_V、V_S/S_V同步。E、每组对齐浪费、k_group归并轮数和bias dtype转换都会影响开销；源码未提供本卡可引用的吞吐收益或稳定tie顺序。

还应保留一个静态核验点：普通及Hash WithoutGroup的`SelectTopKExpertIdx`使用expertCountAlign作为DataCopy长度，而对应topK ID及输出队列按k对齐分配。Ealign大于k对齐时，这个局部拷贝范围不能由Host的k≤E证明安全；需要核对实际AscendC API语义与边界测试，当前未执行，不写成已复现越界。

## Hash视觉路由：查表是条件分支，不能代替所有TopK

Hash OpDef声明ND、FP16/FP32/BF16 logits和同dtype bias/bias_vl，input_ids与tid2eid支持INT32/INT64四种组合。注册的源码配置是ascend910b、ascend910_93、ascend950；仅表示构建声明，不把本卡platforms提升为已验证硬件。Host要求bias_vl为[E]且input_ids存在，tid2eid存在也要求input_ids；两者同时存在才置hashFlag。Hash Host没有在所读范围完整验证input_ids长度、tid2eid二维容量、每个token key或专家ID的合法值，调用方需证明这些内容。

Base仅接受renorm0，norm_type支持0/1/2；norm_type2与bias_vl都要求原始group_count=1，image_sentinel_count在bias_vl存在时必须为正。普通group限制、E≤2048及选组容量限制仍生效。950 Host同样仅接受renorm0、bias_vl要求原始group_count1，但未实现Base那条norm_type2仅group1的拒绝；不能把两个Host的接受范围合并成已验证支持集合。

Base按input_ids是否存在及两整数dtype选key1或3–6；950对应10000–10004，dtype排列为无input_ids、(I32,I64)、(I32,I32)、(I64,I64)、(I64,I32)。这项分派独立于hashFlag：仅有input_ids、没有tid2eid也可选有dtype的模板，但不查表。Base的key0/2分组模板不接收input_ids/tid2eid，即使Host置了hashFlag也不会执行Hash；真正需要token查表的调用必须核对实际key及无分组执行分支。

WithoutGroup及入口实际包含的根目录Regbase都将token_id=-1映射到0；图像token由`[image_sentinel_lo, image_sentinel_lo+image_sentinel_count)`识别，缺省129257与5。图像行用bias_vl做排序，并绕过hash改为真正TopK；非图像行在hashFlag时从`tid2eid[token_id*k:token_id*k+k]`取专家ID，INT64表转INT32后输出。其余负ID、越界key、超范围专家、重复专家均未在所读Device中过滤。Python TP对齐与占位替换不能替代Device表容量证明。

norm_type2实际为`Sqrt(Ln(1+Exp(x)))`，不是任意稳定softplus库调用；没有按logits符号分段的防溢出改写。选中权重仍从未加bias分数gather，sigmoid或sqrtsoftplus除以选中和加eps，softmax不在renorm0下再次归一，最后乘scale。输出out仍是归一/激活后、bias前的全专家分数。对极大logits、全零选中和、NaN/Inf以及很小eps应分别建立数值参考，当前只有静态源码证据。

## 950 Regbase、重复副本及launch缺口

Hash入口在`__DAV_C310__`下包含根目录`moe_gating_top_k_hash_regbase.h`，不是同名arch35子目录文件。完整代码差异表明arch35副本没有bias_vl接口、没有视觉路由判断，也没有根目录的-1到0替换；本卡记录其差异以免错误复用，未从目录名推断实际选中。两份common Regbase helper技术代码相同，FP16/BF16输出为RINT，整数store helper为TRUNC，不能将整数规则套给路由权重。

Regbase无分组分支双槽预取下一行，先计算/可选回写当前全专家分数，再查表或TopK并写当前结果；有分组时先组内排序、选组、预取下一行、归并和gather。Hash查表处显式MTE3_MTE2和MTE2_V同步，不能删除为普通标量读。实际HashCompute只在k≤`VECTOR_REG_WIDTH/sizeof(float)`时调用权重gather，k更大仍入输出队列但未见对应大k计算；Host仅限制k≤E，没有此门禁。因此大k Hash不能由普通TopK已有LargeK实现推出可用。

Base和Regbase都定义把workspace置16MiB的GetWorkspaceSize，但本族所读DoOpTiling没有调用它，workspaceSize初值0直接写入结果。与此同时kernel入口在workspace或GetUserWorkspace为空时直接返回。系统workspace如何与用户workspace拼接需要实际生成launch/API证据，不能把普通TopK的16MiB结论照搬到Hash，也不能将静态0直接等同于已经复现空指针失败。空row拆分也没有完整成功短路。

本补充对24份剩余源作逐源裁决：23份代码/协议/构建语义纳入本卡，单独proto.cpp仅include已读注册头，记重复包装skip。math_util的局部CeilDivision在除数0时返回0，不证明其他除法安全；error_log宏多级别为no-op或只输出opname，诊断时不保证能看到传入格式串的完整参数。尚未闭合的普通950缺失头、外部AscendC原语、生成API、图存储寿命、数值/性能实测仍作为Operator生产的后续输入。

## GateLinear与Torch grouped fallback不完全沿用融合规则

补充完整阅读AscendGateLinear115行和AscendGroupedTopKRouter127行。GateLinear缺省out_dtype设FP32；force_fp32_compute把存储weight dtype设FP32。仅当x/weight均BF16、out_dtype FP32且bias为None时用torch.mm(...,out_dtype=FP32)，否则先将x转weight dtype，调用ReplicatedLinear.forward，再把output转所需dtype，按return_bias返回Tensor或二元组。不能用最终logits dtype推断输入乘法或累加全程FP32；注释中的约6倍收益与数值等价不是本次测试结论。

Torch grouped fallback在use_grouped_topk时以每组最大分数选组，不是普通融合入口固定的组内前2项SUM；选组外分数置0而非负无穷。带校正bias时分组选择用biased分数，但最终权重从原unbiased分数gather；无分组且带bias时直接从加bias分数topk，返回权重包含bias。不能将“bias永远只影响索引”的融合经验推给全部fallback分支，也不能假定负biased分数时零mask一定排除未选组。

fallback的renormalize只有调用方标志为真才除以选中和，没有额外eps/clamp；最后乘routed_scaling_factor。sigmoid且renormalize=False在这一类可有不同数学语义，是否工厂允许仍按实际上层分派。softmax/sigmoid不显式将整个打分提升FP32，grouped的topk排序会转FP32；非grouped topk沿当前分数dtype。sqrtsoftplus用F.softplus(...).sqrt，与Hash Device的直接exp→log→sqrt不是相同数值实现。input_ids及indices_type参数在本_compute_routing中没有消费，IDs最终强制INT32；不要把该签名当视觉token查表或任意索引dtype已实现。
