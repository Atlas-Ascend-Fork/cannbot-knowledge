---
type: Guide
title: vLLM Ascend 图融合：注册生命周期、四类 pass 与匹配门禁
description: 按GraphFusionPassManager、BasePattern及四类融合核对配置/硬件门禁、全局与局部注册、QK/QKV dtype与UB、量化tuple/scale、MMRS组和零padding，区分开关、注册、匹配、设备执行及净性能证据。
aliases:
- GraphFusionPassManager
- QKNormRopeFusionPass
- AddRMSNormQuantFusionPass
- MatmulReduceScatterFusionPass
- MulsAddFusionPass
tags:
- task.implementation
- task.optimization
- task.debugging
- topic.graph_execution
- topic.attention
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/graph_fusion_pass_manager.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/base_pattern.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/utils/npugraph_ex_utils_check.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/norm_quant_fusion_pass.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/qknorm_rope_fusion_pass.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/mm_reduce_scatter_fusion_pass.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/muls_add_pass.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/compilation/test_graph_fusion_pass_manager.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/linearnorm/split_qkv_rmsnorm_rope_vnorm.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/compilation/compiler_interface.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/compilation/passes/base_pattern.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/compilation/passes/muls_add_pass.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/compilation/passes/norm_quant_fusion_pass.py
  role: implementation
created_at: '2026-11-03T02:07:58Z'
updated_at: '2026-11-03T06:46:24Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 图融合：注册生命周期、四类 pass 与匹配门禁

## 任务与证据范围

新模型能跑但开关未产生融合、编译后tuple/scale错误、第二个模型的pattern缺失、跨流替换异常或MMRS通信不匹配时，先沿配置→注册→匹配→替换→设备执行检查。本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取manager79、BasePattern66、stream检查75、NormQuant405、QKNormRoPE396、MMRS300、MulsAdd110及manager UT72行。其余五份来源仅列明Host/硬件片段，不以引用代表整文件或Device已闭合。

[历史三守则](../../optimizations/rules/graph_fusion_register_replacement_guardrails.md)解释v0.13参考实现；这里核对当前Main及新增注册/匹配约束。旧文的FP16或第一层head128规则不能无版本地覆盖当前QKV-VNorm分支。底层归一化Host见[融合RMSNorm](vllm_ascend_fused_rmsnorm_host_contract.md)，旋转入口见[Partial RoPE](vllm_ascend_partial_rotary_host_contract.md)。没有导入上游、注册实际pattern、构造NPU样例、执行UT/图或性能实验；保持draft、空平台和framework部分Scope。

## 开关、硬件 profile 与执行范围

NPUPlatform.get_pass_manager_cls返回此manager路径，供平台custom pass接入；不是所有模型默认都完成融合。configure消费已递归验证的Ascend compilation config，不能重新用原始additional_config中字符串false的Python真值裁决。manager按添加顺序执行各pass，先询问compile_range是否适用，最后调用graph.recompile。这里的三个普通pass范围方法均返回True，MMRS只按TP组大小判断，不是按名字自动保证全部动态shape可融合。

| pass | manager与局部注册条件 |
| --- | --- |
| NormQuant | fuse_norm_quant且GRAPH_NORM_QUANT_FUSION；再查dtype、W4A4、custom-op与MX能力。 |
| QK/QKV Norm RoPE | fuse_qknorm_rope；类内先检查BF16和Attention层，再区分q/k-only与VNorm、Triton和UB。 |
| MulsAdd | fuse_muls_add且GRAPH_MULS_ADD_FUSION；类内dtype为FP16/BF16/FP32。 |
| MatmulReduceScatter | enable_sp读取已解析use_sequence_parallel_moe，且GRAPH_MM_REDUCE_SCATTER_FUSION；不是另造fuse_gemm_comms公开开关。类内TP只接受2/4/8。 |

所读profile中STANDARD能力供A2/A3继承，包括三种manager硬件门禁及GRAPH_QKV_NORM_ROPE_FUSION。A5有NormQuant/MulsAdd/MMRS及DynamicMX能力，未声明QKV-VNorm能力；310P没有前三种manager能力。QK-only在manager中没有同一profile guard，仍依赖其独立实现；不能从VNorm不注册推整个QK融合不可用，也不能把profile枚举当全卡/所有模型实测支持矩阵。profile选择在进程初始化固定，不假设改配置即可热切硬件。

configure往现有passes列表追加，没有clear或去重；add仅断言VllmInductorPass类型。静态工程推断：反复configure同一实例可能追加多个pass，不能把方法当幂等重置。是否实际重复调用需记录真实编译器生命周期，本次未复现。

## BasePattern 的两套注册与全局身份

BasePattern先向PyTorch PatternMatcherPass注册fwd_only替换，再向npugraph_ex（ImportError时用torchair）注册带stream extra_check的替换，最后把pattern_id放到模块全局集合。普通key只有类名与epsilon。已在全局集合时，整个register早退，包括新实例自己的局部matcher注册；只看全局已注册不能证明第二个pass实例也有局部pattern。两步注册不是事务，异常时没有在此回滚先完成的注册。

QKV-VNorm覆盖key，加入head_dim、num_heads、num_kv_heads和rope_dim，避免混合Attention第二种shape被静默跳过。普通QK-only、NormQuant及MulsAdd沿用基类key，不能由它推dtype、设备、模型、scale或所有shape都已纳入身份；多模型/重建配置需保存实际key、local matcher与全局注册状态。此为代码边界，不是已复现的跨模型错误或建议默认清全局状态。

MMRS覆盖register：每次先注册当前局部PyTorch matcher，再仅对全局npugraph_ex去重，key含pattern类、TP大小和group_name。其局部行为不同于BasePattern；不能把一个类的去重策略推广到全部pass。不要仅吞Duplicate pattern来判断本次局部matcher完整。

extra_stream_scope_check只看match内call_function节点的stream_label：全默认、同一非默认或没有该类节点返回True；不同非默认流、默认和非默认混用返回False。基类把这个检查传给npugraph_ex注册，所读PyTorch注册没有同样传参；MMRS对两种matcher另带语义extra_check，npugraph_ex再与stream检查合取。因此不能仅由公共helper存在就声称所有匹配器都拒绝所有跨流模式。

## NormQuant：量化格式、scale 与 tuple 语义

本pass先限model dtype为BF16/FP16；quant_description任一值精确为W4A4_DYNAMIC或W4A4_FLATQUANT_DYNAMIC就整pass早退。缺quant_config/description返回未检测，不证明任何未知或未来INT4格式均兼容。它按字符串检查权重方案，不应从类名W8A8误读成所有FP8/MX分支不存在。

每个epsilon1e-5/1e-6注册普通dynamic AddRMSNorm+Quant；有DYNAMIC_MX_QUANT_FUSION再注册Add及无残差RMSNorm的MX E4M3模式；enable_custom_op为真才注册静态量化及bias相关模式。custom-op关闭不等于整pass无任何pattern，manager持有pass也不等于所有模式已注册。

| 搜索/替换 | 必须保留的输出与参数 |
| --- | --- |
| 静态AddRMSNormBias→vllm.quantize | pattern的scale与scale_reciprocal为独立输入；replacement直接传scale与offset给npu_add_rms_norm_quant，不现算倒数。bias变体传beta；保留quantized及residual输出。 |
| AddRMSNorm→dynamic quant | replacement设置output_mask=[True,False]，将底层output[0]/[3]/[2]映射为quantized、scale、residual，不能沿用普通RMSNorm tuple序号。 |
| AddRMSNorm→dynamic MX quant | dst_type=E4M3，replacement返回底层[0]/[2]/[1]；与上一行scale/residual位置不同。 |
| 无残差RMSNorm→dynamic MX quant | replacement只返回quantized与scale两项。 |

数值方向和tuple根据精确算子版本确认，不能把“都是归一化加量化”当签名可互换。自有RMSNorm的Meta与真实输出差异另按Host指南裁决，本pass的外部torch_npu kernel没有在本卡完成Device验证。

## QK-only 与 QKV-VNorm 是不同的模型结构

当前pass的外层dtype仅BF16；历史FP16声明不是当前注册条件。没有Attention层便返回。q/k-only从第一个Attention取得head数与head_dim，仅head128时注册两种epsilon及有/无biaspattern，使用view式拆头和NeoX RoPE；replacement走DeviceOperator。A5所读适配片段选择qkv_rmsnorm_rope_simt，不能把普通标准设备的kernel路径套到所有硬件。

QKV-VNorm在q/k-only注册后独立判断HAS_TRITON、GRAPH_QKV_NORM_ROPE_FUSION，再枚举所有Attention的去重shape。因此第一层非128会跳过q/k-only，但不自动关闭后面的VNorm分支。VNorm采用unflatten/flatten与全head RoPE；split sizes在结构匹配中可能是wildcard，源码把不匹配split的ValueError转为RuntimeError，使matcher将它当不匹配而不是编译中断。

VNorm注册前调用qkv_rmsnorm_rope_vnorm_fits_ub，按单token活跃tile估算、head整除关系和87040字节预算判断。Host另一个batch tiling heuristic统计非同时活跃buffer，不能替代此可行性检查；Host用max(1,heuristic)也不能修复一个token超过UB。TP可减小每卡head数是源码给出的候选方向，仍须重验新切分、图和输出。

所读VNorm Host说明V按无可学习scale的RMSNorm处理。pattern形式虽含v_weight，replacement并不把其值交给DeviceOperator/Host；不能据这个形参宣布任意learned V gamma模型已适配。实际目标须证明无权重VNorm语义吻合，并核对cos/sin宽、Q/K bias和模型RoPE。底层Device1–299未读，只有Host300–479及头部部分常量，不声称完整Operator或数值等价已证明。

## MMRS：bias-free GEMM、精确通信组与 padding

该pass构造时固定TP world size、group_name和该NPU backend的hcom_name；匹配检查dim=0、world_size相同且group_name精确一致。不能把EP/DP组或同样size的另一个TP组替代，也不能跨组复用注册状态。适用TP为2/4/8，输入和weight都需2D、dtype相同且为BF16/FP16；输入归约维必须静态Python整数，256<=K<65535。符号K、未知meta或GEMM bias非None都不匹配，不代表整个模型无法运行未融合路径。

三种结构为GEMM→RS、GEMM→cat(output,zeros)→RS、GEMM→constant_pad_nd→RS。cat要求dim0、顺序精确[gemm,zeros]、二维同device/dtype/输出宽，填充值0；constant-pad要求四项width前三项0和零填充。replacement把零行padding移到GEMM输入，再用weight.t()调用DeviceOperator.npu_mm_reduce_scatter_base，reduce_op=sum。bias-free是零行在线性映射后仍为零的必要条件之一，不能将该变换直接推广到带bias/激活/非零padding/任意cat顺序。

pad_rows=13是scalar_workaround追踪样例，不是要求实际请求补13行或固定batch。匹配层并未给出所有布局/stride、设备通信生命周期与外部fused kernel的完整校验，不能删除额外guard来强行扩大shape。融合数、HCCL名称存在或图重编译成功都不是分布式输出正确的证明。

## MulsAdd 与 Agent 验收顺序

MulsAdd将x*routed_scaling_factor+y替成vllm.muls_add；scale来自hf_text_config，缺省1。pattern key仍继承类名/epsilon，不包含scale。FP16/BF16/FP32只是注册门禁，不能由样例2×2048推所有broadcast/stride或数值情况已验收；具体kernel未在本卡闭合。

manager UT72只定义字符串false被规范化和mock SP/TP2/hardware下一个MMRS pass被添加，没有运行，且不证明任何pattern真正命中、跨流、分布式通信或设备数值。Agent按以下证据逐层推进：

1. 固定Main/实际Native/torch_npu/图后端、硬件profile、最终typed配置、Attention shape与量化方案。
2. 保存真正pass顺序、每个pattern key、局部及全局注册状态、compile_range与matched_count；多模型、重复configure及不同shape单独观察。
3. 对比替换前后FX图，核对tuple、scale方向、RoPE、VNorm语义、stream_label、RS组和padding；没有匹配先定位门禁，而不是删除guard。
4. 在目标环境比较输出/误差、请求grow/shrink与多层异构，再测kernel、通信、compile/capture及端到端时延/显存；开关或matched_count不能替代质量与净收益。

失败保留原图、真实注册/匹配日志及输入，恢复已验证的原未融合路径和正确版本；不把任意模型的禁图smoke当原目标配置已通过。本次没有设备结果、性能收益或Agent A/B。


## 3164固定增量：局部matcher注册与INT8融合

以下固定Main `3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，与前文ceac分开解释。只读完整AST语义差异/必要原始diff，不执行pattern样例、编译、图或NPU；不增加真实收益或已验证事件。

BasePattern新增WeakKeyDictionary，以每个PatternMatcherPass对象为键保存其局部pattern集合。相同pattern_id在新matcher仍注册PyTorch replacement，而npugraph_ex保持模块全局去重；同matcher重复注册则跳过该局部项。它修正了前文ceac全局早退连带跳过新matcher的行为。普通pattern key仍未自动包含所有模型、dtype、scale或shape，注册中途异常也未形成回滚事务，不能把新去重表当全生命周期正确性证明。

MulsAdd同时注册`x*scale+y`、`y+x*scale`及两种单元素foreach_add顺序；都是out-of-place表达，不扩展成任意列表长度或原位写入融合。原dtype、stream检查与scale身份边界仍需核对。

NormQuant的普通dynamic模式显式要求`dst_type=torch.int8`，新增`npu_add_rms_norm_bias(..., beta=None)`加dynamic-INT8的无bias模式，替换仍按quantized/scale/residual三项重排。它覆盖Qwen3.5/Next一类无beta调用，不代表将FP8、INT4或任意量化节点都融合。W4A4整pass关闭条件继续有效；W4A8只有INT8 activation部分与本pattern相关，权重bit数不直接出现在该图结构中。

MRv2 separate-routine的decode capture候选在原集合外增加按uniform_decode_query_len向上取整的size，但不得超过max_cudagraph_capture_size；最终仍按decode最小/最大token范围排序过滤。静态kernel排除表新增PoolKeyIndexer。保存最终capture列表和实际算子路径，而非从“加入候选”推断一定capture或发生融合。
