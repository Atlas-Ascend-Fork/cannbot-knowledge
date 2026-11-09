---
type: Guide
title: vLLM Ascend层替换与并行Linear：分组、bias、归约和融合门禁
description: 沿CustomLinearOp和Kimi O-proj核对MLP/OTP/DSA-CP选择、token轴通信、bias只加一次及BF16 MM-ReduceScatter门禁，补充activation/FLA/Kimi concrete-class桥接与dummy fusion对象的真实边界。
aliases:
- get_parallel_op
- CustomRowParallelOp.get_input_parallel
- KimiOProjMMReduceScatterOp
- ShardedCPColumnParallelOp
- register_dummy_fusion_op
- AscendDCPGroupColumnParallelLinear DCPGroupColumnParallelOp
- qrep_active dcp_q_replicate
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.parallelism
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/activation.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/conv.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_rms_norm_gated.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/kimi_mla.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/linear_op.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/linear.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/linear_op.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/mla.py
  role: implementation
created_at: '2026-11-03T06:23:41Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend层替换与并行Linear：分组、bias、归约和融合门禁

## 接入的是具体执行类与协议

固定Main ceac1a2，完整静态阅读linear_op498行及5份注册/小原语桥接文件。它们服务新模型层替换和通信诊断，不证明所有模型已选中该类，也不代替Native父层/QuantMethod/collective/Device完整闭包。未导入模块、执行NPU、模型、图或性能，保持draft/空平台。

CustomLinearOp先update_attrs取得layer.bias、skip_bias_add、return_bias、quant_method和prefix；这些属性不自动监听后续修改。普通replicated按skip_bias_add决定是否把bias传quant_method，输出是否打包二元组由return_bias控制。Row层若input_is_parallel=False，先按当前comm_group的TP数沿最后维切分并contiguous；不同子类切换通信组后，必须同步核对checkpoint分片、input_size_per_partition和真实输入布局。

## 按prefix选择的通信不是标准Linear名字的同义词

| 选择与类 | 实际通信/计算 |
| --- | --- |
| dense gate_up_proj + MLP TP | MLPColumn先沿token轴all_gather，再quant_method.apply |
| dense down_proj + MLP TP | MLPRow取特征分片、仅rank0加bias，再沿token轴reduce_scatter |
| wo_a/wo_b + OProj TP | DSV4 Column/Row改用OTP组；wo_a直接本地apply，wo_b取特征分片后本地apply，此层不另做归约 |
| 普通o_proj + OProj TP | 重排token×TP×chunk后all_to_all_single，再apply与token轴reduce_scatter、恢复原输出shape |
| DSA-CP q_b_proj/kv_b_proj | ShardedCPColumn暴露size1/rank0/无device_group，直接本地apply |

get_parallel_op先处理shared_expert类prefix；shared-expert DP开启时返回无custom op的TP1，否则不会再进入后面的elif disable_tp分支。普通非shared层disable_tp则返回TP1。不是所有名字带MoE就被排除：is_moe_layer只按layers.<index>.正则、n_routed_experts非None、first_k_dense_replace和moe_layer_freq判断，没有独立检查专家数>0；缺正则直接False。内部lru_cache helper定义在每次is_moe_layer调用内，不能从装饰器推断跨调用配置缓存已生效。

这些匹配用prefix子串，不会为新模型自动识别不同层命名。初始化后先记录最终类/comm_group/rank/size，按layer真实weight shard验证；不能只改配置开关或沿用模型源代码里的Column/Row名称。

skip_bias_add=True时权重计算不加bias并将bias单独返回；否则Row仅rank0加，避免归约后重复bias。文件里若干custom实现没有按reduce_results或gather_output再执行标准父层动作，属性存在不是额外collective保证。ShardedCPColumn.apply_impl在return_bias=False时直接返回Tensor，而基类apply按二元组解包，真实调用必须核对是否走另一个入口或满足return_bias约定；这只是静态协议点，未复现运行故障。

## Kimi O-proj融合MM-ReduceScatter有两级门禁

构造拒绝已有layer.custom_op、非UnquantizedLinearMethod、非BF16权重、bias、缺TorchNPU V2接口、TP不在2/4/8/16/32/64、空/非2D权重以及K不在[256,65535)。成功后从本组backend取得HCCL comm name，不是按任意模型名直接启用。

运行_can_fuse还要求2D/BF16输入与权重K相等、weight或其转置连续、非零token和输出宽度，以及按TP补齐后的通信字节严格小于16*256MiB。有forward context时，从attn_metadata或dict中取有num_prefills/num_decodes的对象，只接受有prefill且无decode；无forward context则没有这条phase拒绝，因此不能概括成任何入口都只会prefill融合。

可融合时先将token行补到TP倍数，调用npu_quant_mm_reduce_scatter，reduce_op=sum、comm_mode=ai_cpu；名字有quant不表示这里量化了BF16权重。返回不在本方法裁掉SP补齐行，真实consumer需按其token合同处理。不能融合则quant_method.apply后sp_reduce_scatter；apply_into另始终用独立matmul和dist.reduce_scatter_tensor写外部output，并非同一个融合调用。通信/累加精度、workspace和性能需按实际TorchNPU实现验证。

## activation、FLA和具体类桥接

QuickGELU调用npu_fast_gelu，SiluAndMul调用npu_swiglu；clipped变体把limit/alpha/beta交DeviceOperator，不在此硬编码统一平台实现。SwigluOAI用临时对象调用Native forward_native；Step变体拒绝limit=None，HAS_TRITON时转Triton，否则Native。源码注释的等价或速度不是本卡实测，输入split、clamp方向和dtype仍沿实际callee核对。

普通Conv3d forward_oot转父_forward_conv，310P则有独立forward_native替代，见[310P原语](vllm_ascend_310p_primitive_fallback_contract.md)。FusedRMSNormGated模块被import时就导入FLA/Triton并执行CustomOp.register_oot；所谓按需加载依赖外部何时import本模块，不能把读类的import当无设备/注册副作用。forward把activation、bias、eps、prenorm、residual_in_fp32和out直接传rms_norm_gated，选项存在不证明任意组合已通过数值。

KimiK3MultiHeadLatentAttention的Main-lane桥同时继承Ascend MLA和Native AMD具体子类，目的是匹配OOT concrete class名与初始化MRO，没有重写完整Attention算法。实际Native路径/类版本与替换注册必须一致，不将独立快照的类似类名当配对ABI。

ops包导入fused_moe/layernorm/register_custom_ops等模块，HAS_TRITON时导入数个融合linearnorm注册模块。register_dummy_fusion_op另将若干torch.ops._C_ascend名字替换为default=None的dummyFusionOp对象；这些对象没有真实计算/__call__，也不是失败后的数值fallback。只有明确compiler融合/注册流程才应使用，不能见符号存在就认为RMSNorm或FP8量化可直接执行。

新模型验收先覆盖最终OOT类/前缀、bias与返回形态、token/feature分片、真正collective组与顺序，再对比fallback/融合、prefill/decode/混batch和非连续输入。把图/stream与真实量化consumer加入后再测净收益，本次未运行这些验证。


## 3164 版本补充：DCP group Q 复制与明确的加载 TP

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

新增AscendDCPGroupColumnParallelLinear以DCP size为group_size，TP rank%group确定组内head选择，要求output_size可TP整除。qrep_active>1时优先选DCPGroupColumnParallelOp，loading tp_rank/size分别除group_size，apply直接消费group完整Q heads、不做output gather。prefill再_local_view挑当前rank heads并contiguous；实际head数/整除还需caller与backend保证。

旧ShardedCPColumnParallelOp的fake world1与enable_dsa_cp prefix判断被删除，不能用旧q_b_proj/kv_b_proj名字在3164绕过真实分片。MLA wrapper从实际q_projection.qrep_active传dcp_q_replicate，post-load直接走impl处理，避免通用dense packing覆盖该布局；IndexerWrapper也移除attn_q_gather_handle参数。模型层、真实Linear加载metadata与backend必须来自同一版本，不把新helper视为所有attention已支持DCP复制。
