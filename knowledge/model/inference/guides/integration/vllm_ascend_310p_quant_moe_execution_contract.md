---
type: Guide
title: vLLM Ascend 310P量化接线：本地scheme、权重布局与MoE执行
description: 沿310P本地ModelSlim registry核对W8A8静态/动态、W8A8S/SC的scale、transpose与bias，接入路由、AllGather token dispatch和分阶段MoE MLP，区分实际公共callee与独立helper、累积group_list及NZ例外，保留外部kernel与图精度待验。
aliases:
- AscendModelSlimConfig310.get_quant_method
- AscendW8A8DynamicLinearMethod310
- AscendW8A8SCLinearMethod310
- AscendW8A8DynamicFusedMoEMethod310
- AscendMoERunner310
- TokenDispatcherWithAllGather310
tags:
- task.implementation
- task.debugging
- topic.compute.quantization
- topic.model_adaptation
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/modelslim_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/methods/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/methods/registry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/methods/w8a8_base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/methods/w8a8_dynamic.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/methods/w8a8_static.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/methods/w8a8s.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/quantization/methods/w8a8sc.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/fused_moe/fused_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/fused_moe/grouped_topk_router.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/fused_moe/moe_comm_method.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/fused_moe/token_dispatcher.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/fused_moe/moe_mlp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/base.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/router/router_factory.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_mlp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_comm_method.py
  role: constraint
created_at: '2026-11-03T04:42:52Z'
updated_at: '2026-11-03T04:42:52Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P量化接线：本地scheme、权重布局与MoE执行

## 任务与证据边界

新模型选择310P兼容量化后端时，不能沿用标准设备同名W8A8的布局、bias或通信假设。本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读310P量化九文件和MoE五文件，另核对注册、NZ、router与公共MLP调用的明确片段。它们是Python框架合同；外部torch_npu kernel、Native父类完整生命周期、真实量化精度、图和通信未闭合，保持draft/空平台。

[标准ModelSlim接入](vllm_ascend_modelslim_scheme_adaptation.md)明确不代替310P；[历史compressed-tensors故障](../../runbooks/precision/w8a8_310p_compressed_tensors_missing_ascend_override.md)是另一版本/格式的路由证据。这里不把改量化名字当checkpoint格式转换，也不扩展旧Issue为所有当前后端永久限制。没有导入、注册、运行上游测试、NPU或模型。

## 本地registry与逐层选择

platform按quantization_backend_family选择配置导入；compatibility分支导入AscendModelSlimConfig310，而不是同时导入标准四种配置。其get_quant_method先更新packed_modules_mapping，再映射prefix，以描述文件和packed映射决定quant_type。不能省略QKV/gate-up合并名称处理，否则可能误走浮点或其他布局路线。

310P methods包导入四种实现文件，decorator向独立字典按(quant_type,layer_type)注册：W8A8、W8A8S、W8A8SC只注册linear，W8A8_DYNAMIC注册linear与moe。重复key抛ValueError，构造缺失类型抛NotImplementedError；只存在decorator而实际消费进程未完成导入不算可用。

Linear无量化类型时选AscendUnquantizedLinearMethod；MoE无类型时选310P未量化method，有类型则包装相应scheme。VocabParallelEmbedding遇非None量化类型直接拒绝，否则选310P未量化embedding；其余层类型才委托标准父配置。不能据某一linear方案存在推断MoE、embedding或Attention均支持它。

## 四种dense路线的后处理和运行参数

共同基类创建INT8[output,input]权重、单元素input_scale/input_offset及INT32 quant_bias/INT64 deq_scale；具体子类会覆盖或增加参数。真正消费哪些字段由apply决定，不能由参数存在推导偏移或非对称量化已生效。

| scheme | finalize的关键布局 | apply的关键合同 |
| --- | --- | --- |
| W8A8静态 | 按原input宽repeat输入scale/offset，新增aclnn参数和倒数；weight先maybe_trans_nz再transpose(0,1)，weight scale/offset展平 | 非INT8激活先quantize；quant_bias仅tp_rank=0传入；直接传已转置weight及deq_scale，输出params_dtype |
| W8A8_DYNAMIC | weight先NZ再transpose；FP32通道weight_scale/offset展平 | npu_dynamic_quant→npu_quant_matmul，传pertoken_scale及调用方bias，输出x.dtype；不使用已创建的weight_offset |
| W8A8S | weight只做maybe_trans_nz，输入scale/offset展开为普通Tensor属性 | apply再transpose权重；非INT8输入先quantize，quant_bias仅tp_rank=0传入 |
| W8A8SC | compressed weight/index/info结构；deq_scale加轴并to(UINT64)，quant_bias加轴 | npu_matmul_compress_dequant必须有quant_bias；高rank激活先展平到二维，结果再恢复前缀shape |

W8A8静态apply附近旧注释提及传weight.T，但实际代码在finalize完成transpose，apply没有再次转置；不能照注释增加第二次transpose。W8A8S恰好相反，后处理和apply的分工不同。maybe_trans_nz也有例外：FP32、meta、K或N为1时不转换，然后才考虑FORCE_NZ/配置；“310P使用NZ”不能覆盖这些拒绝条件。

动态linear在pertoken_scale为二维时把激活和scale的dim1 squeeze，最后把输出dim1 unsqueeze。这不等价于任意[batch,seq,hidden]通用flatten；新shape要核对实际量化返回rank和dim1。源码保留某些shape/图路径精度问题注释；未在本次复现或修复，不用load-time反量化为FP16/F.linear伪装相同量化执行。

SC按ceil(K/256)×ceil(N/128)×8创建INT8 index，info为五个INT64；所读apply没有消费info，不据docstring推断所有压缩元信息都传到kernel。后处理中的to(UINT64)是dtype转换，不能直接替成view而假设位语义相同。RowParallel且当前TP rank非0时将quant_bias置零，因为该外部算子不允许None。静态/S的可选调用方bias未在其apply另行相加；不要把dynamic的bias合同套给它们。

这些finalize会改变权重或scale rank并新建缓存属性，没有统一reload幂等guard。重复transpose、repeat或unsqueeze会产生不同布局；完整reload与loader分片需按[权重加载合同](vllm_ascend_paired_native_weight_loader_contract.md)追踪实际调用，不直接重跑finalize宣告恢复。

## MoE：量化stage不等于dense量化算子

动态MoE创建w13[E,2I,H]、w2[E,H,I] INT8权重和FP32通道scale，后处理转NZ并将各expert scale/offset展平。MLP kernel实际只接weight与scale；offset虽保留，不说明非对称权重偏移参与了计算。

_get_group_list遇group_list_type=1先cumsum，其他情况原样返回，交给310P外部kernel的格式是累积计数。GMM1以quant_mode=pertoken在kernel内量化/反量化，再npu_swiglu，返回(hidden,None)；GMM2同样自行量化/反量化，不把上一stage没有的scale伪造传入。

未量化MoE先委托Native父后处理，再pad、transpose(1,2)、contiguous与maybe_trans_nz，并替换为不训练Parameter。GMM1/GMM2使用npu_grouped_matmul，保留输入group_list_type，不能无条件执行动态scheme的cumsum。中间激活为swiglu，没有额外act quant。Native父转换、padding具体算法和kernel完整实现仍是依赖边界。

两条apply均从_EXTRA_CTX取得通信对象，把预选topk、expert_map、mask等交给fused_experts，dynamic_eplb=False。它们不是重新计算路由的入口，也不因字段可传就证明所有EPLB/冗余专家或共享专家组合已验证。

## 路由、AllGather与token重排

router factory先尊重自定义routing_function，再按FUSED_MOE_COMPATIBILITY选择310P router。只有softmax、非grouped topk且无correction bias时使用其专门路径；其余委托父router，不能按类名推成所有路由都走同一kernel。

专门路线把logits转FP16，超过1024 token时按第一维切块调用npu_moe_gating_top_k_softmax再拼接；之后按配置renormalize、乘routed_scaling_factor，ids固定INT32而未遵从任意indices_type请求。1024是每次gate调用的分块阈值，不是模型总batch上限或所有topk算法限制。

TokenDispatcherWithAllGather310要求hidden末维16对齐。apply_router_weight_on_input时要求二维topk_weights且topk=1，再预乘权重。存在expert_map时仅mask本地无效专家的combine权重，active_expert_range按EP rank×num_local_experts计算；不是在这里对topk_ids做任意稀疏expert_map重编号。

npu_moe_init_routing_v2使用quant_mode=-1、drop_pad_mode=0、row_idx_type=0，返回sorted hidden和expanded_row_idx，expert_tokens转INT64且声明group_list_type=0累积式。restore_shape和topk_weights留给继承的combine；完整AllGather准备/合并、rank间同步与逆置换未在这五个子类中重新实现。

Runner310在父构造后替换ALLGATHER配置key的通信对象，关闭shared_experts.multistream_overlap并重新选forward入口；FP16 gate权重时关闭预cast-FP32，FP16 hidden/weight直接调gate，其他交给父路径。不能只改overlap布尔值而保留先前选择的fake/forward入口，或只由FP16属性推断实际ND/NZ布局。

## 实际公共MLP与独立helper分开

所读公共moe_comm_method从标准moe_mlp模块导入apply_moe_mlp；有quant_method时直接调用它。公共MLP按supports_fused_activation选择融合stage，否则走各独立hook，事件通过maybe_record_event按有效overlap配置决定是否生成。动态310P scheme只声明silu融合；未量化method接受silu/swiglu。未知激活必须核对缺省hook是否实现，不能默认有可用回退。

310P目录还保留独立apply_moe_mlp：它明确拒绝非swiglu/silu，并在GMM2前无条件record_event。但本次全Main符号/路径搜索未找到其直接import调用；不能把这份helper的拒绝和事件策略说成当前公共通信链已执行。文件已完整审阅，调用可达性继续pending；也未由搜索证明动态注册/外部patch绝不可能使用它。

## Agent验收与性能诊断

保存真实配置类、local registry key、packed prefix、每个权重的checkpoint/最终shape、stride、dtype与NZ格式，检查scale/offset/bias是否实际进入callee；区分静态量化缓存、dynamic pertoken scale和SC压缩index。核对TP bias归属、不同输入rank、同一layer连续reload与构造前后方法对象。

MoE另保存activation、topk dtype/行数、1024分块、EP专家范围、group_list_type与累积值、expanded_row_idx和真实通信对象；分别比较gate、重排、GMM1/激活、GMM2和combine数值。正确后才量化转ND/NZ、临时量、record_event、AllGather和端到端时延。未关闭外部kernel、stream、版本与模型质量未知项前，不把源码全文、注册或可构造Tensor当完整摄取/硬件/性能验收。
