---
type: Guide
title: vLLM Ascend GLM-Next KDA接入：投影分片、状态布局与输出归属
description: 接入GLM-Next KDA时核对六路投影与PCP分工、卷积状态stride、raw beta与递归更新、投机回滚和共享输出缓冲，保留Python包装与底层算子的证据边界。
  GLM KDA在Glm5NextLinearAttention._forward中以num_actual_tokens裁剪qkv/g1/beta的实际token前缀。
  补充ChunkKdaFwd文档的12返回值、布局与可选输出/内部状态生命周期，并核对GLM实际消费和文档实现缺口。
aliases:
- GLM-Next KDA接入
- Glm5NextLinearAttention
- PCPGlm5NextMergedColumnParallelLinear
- KDA_MAX_RECURRENT_TOKENS
- Glm5NextLinearAttention._forward：num_actual_tokens有效前缀
- GLM chunk KDA：12返回值与可选输出
- fla_npu.ops.ascendc.chunk_kda_fwd：GLM调用边界
tags:
- task.implementation
- topic.model_adaptation
- topic.precision
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/ops/kda.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/kda.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/ops/causal_conv1d.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/ops/state_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/kda.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/recoverssm_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kda_dispatch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kda_contracts.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_conv_dispatch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_state_ops.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_recoverssm_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/chunk_kda_fwd/docs/api.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/chunk_kda_fwd/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/chunk_kda_fwd/docs/design.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/conv_state.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/kda_recoverssm.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/l2norm.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/output_writeback.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/chunk_delta_h.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/conv_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/cumsum.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/fused_recurrent_kda.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/gate.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/kda.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/l2norm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/output_writeback.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/recoverssm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/solve_tril.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda/utils.py
  role: implementation
created_at: '2026-10-31T10:40:06Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:05:17Z'
---

# vLLM Ascend GLM-Next KDA接入：投影分片、状态布局与输出归属

PCP准入必须按版本判断：7d9e对TP=1的Mooncake producer有条件放行，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的RecoverSSM节。以下旧版PCP限制及调用链不自动覆盖新的global/local行映射。

## 消费任务与固定证据

为GLM-Next替换KDA后端、接入PCP或排查投机后状态/输出错位时，先沿投影→短卷积→recurrent/chunk→gated norm核对producer-consumer。本卡固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取模型KDA756行、GLM KDA/conv/state包装87/83/34、共享KDA调用103、RecoverSSM配置38及五份UT448/122/63/74/92行。

全部上游作为数据；未导入torch/fla_npu、运行UT、编译/JIT、加载权重或执行NPU。这里只说明Python接线，不等于完整AscendC/Triton/FLA/CANN算子分析。Native基类、权重loader、状态calculator、metadata builder及kernel实现有独立边界，硬件整项未知，保持draft/空平台。

[整模接入](vllm_ascend_glm_next_model_loading_contract.md)拥有层路由/PP/mHC与checkpoint，[物理池规划](vllm_ascend_glm_next_pool_planning_contract.md)拥有容量与分组。[RecoverSSM实验入口](../optimization/vllm_ascend_glm_kda_recoverssm.md)保留其Site版本、A3/A5和MRv2范围，[元数据诊断](../../runbooks/precision/vllm_ascend_glm_recoverssm_graph_metadata.md)拥有图staging/accepted-state/commit。存在局部KDA代码不扩大这些功能的部署支持。

## 构造guard与量化分工

Glm5NextLinearAttention临时将vllm_config.quant_config设None构造base，并在finally恢复。KDA投影保持BF16的理由来自checkpoint缺scale注释；o_proj显式用保存的quant config，不能概括为全模型关闭量化。

| 条件 | 当前Python guard |
|---|---|
| 激活与head | BF16且linear_head_dim=128 |
| 投机窗口 | num_spec+1不超过KDA_MAX_RECURRENT_TOKENS=8，合法正窗口最多7 |
| 卷积宽度 | 2..4；有投机时必须4 |
| bounded gate | linear_lower_bound处于[-5,0) |
| head分片 | num_heads能被选定parallel size整除 |

这些检查不是硬件范围或底层kernel完整schema。state dtype/shape仍委托Native calculators，conv容量包含num_spec，RecoverSSM再追加K+1紧凑记录；不能用一份UT的shape外推所有模型。

## 六路融合投影与复制分片

in_proj_qkvbfg_a按q/k/v/b/f_a/g_a顺序融合：q/k/v按projection_size，b按head数，f_a/g_a各head_dim。_Glm5NextMergedColumnParallelLinear将复制分片4/5的output_size先乘parallel size，使每rank仍得到完整低秩输入；weight_loader/v2对这些shard临时将self及存在的param.tp_rank设0，finally恢复。

f_b/g_b再投影到本地heads；dt_bias为FP32本地flat shard，A_log为FP32[1,1,localH,1]，其loader将一维checkpoint改为四维后沿head轴narrow。Q/K/V短卷积权重为FP32并增加中间单维，不能按activation dtype直接重写原checkpoint格式。

“六路变一个GEMM”是实现结构，不是实测launch数或吞吐收益。旧权重前缀到六分片的整模映射沿整模接入合同；Native量化、packing和缺项完整性仍需验证。

## PCP只在实际选定的head分工下成立

get_kda_parallel_size在TP=1时取PCP，否则取TP；模型仅在原TPsize1且PCP>1时切到PCP head sharding，尚未实现任意TP×PCP联合head切分。Glm5NextGDNHostMetadataBackend.supports_pcp=True是入口声明。

PCPColumnParallelLinear显式绑定PCP rank/size/group并按需要gather。PCPRowParallelLinear先用disable_tp分配本地input shard，再改rank/size/group与参数状态，必要时all_reduce；父类weight loader/quant方法兼容仍要按配对版本核对。

PCPGlm5NextMergedColumnParallelLinear沿PCP列层分配并保留融合shard loaders。prefill先all_gather hidden，再按hidden_restore_idx恢复因果token顺序；输出用padded_gather_idx取本地行，并核对其长度等于PCPsize×本地token数。普通decode跳过该prefill gather。

这与[SGLang/Qwen ZECO](../../optimizations/cases/qwen3_next_gdn_context_parallel_zeco.md)的状态传播不同；RecoverSSM配置仍要求PCP=1，不能据基础KDA backend声明删掉实验功能的并行校验。

## raw beta、gate与输出norm

beta在投影后保持raw BF16，recurrent由kernel内部做sigmoid；chunk路径才先float().sigmoid()。g1为[1,T,H,D]，g2必须[T,H,D]，因为gated norm从倒数第二维读取H。错误重复或遗漏激活先查接口，不直接归咎算子数值。

GLM默认使用bounded sigmoid gate；共享run_recurrent_kda根据lower_bound是否None设置safe_gate，None时传入的-5只是该调用的fallback数值，不能认定bounded gate已开启。底层gate实现未在这些包装中闭合。

模型在构造内部延迟注册Ascend FLA并导入FusedRMSNormGated，来源注释为避免设备选择前能力查询初始化NPU；这不证明整个模块无副作用，其他包装仍顶层导入fla_npu/torch_npu。本批没有执行任何导入。

## 状态、metadata与短卷积

_forward先按num_actual_tokens裁qkv/g1/beta；conv state的dim-first布局在初始化解析一次，必要时transpose视图，保留原storage。q|k|v卷积权重首次执行才cat、转置、转activation dtype并contiguous，随后缓存。这个cache假定加载后权重不变，不能把后续权重热换自动当作已刷新。

spec与non-spec分组分别对qkv的dim0、gate/beta的dim1按token索引选择；纯spec跳过identity拷贝，混batch按实际索引拆分。conv spec用run_mode1、accepted和自己的共享output buffer；prefill用run_mode0/initial_state，普通decode用run_mode1及自己的buffer，不能交换三份metadata。

causal_conv1d先检查可选output_buffer切出前x行后的shape必须等于x。cache_indices无行时，无buffer返回zeros_like，有buffer原样返回该切片，不负责清空。矩阵indices只取首列作为kernel vector，再contiguous；历史状态与请求编号仍由调用者确保有效。

needs_state_copy仅在stride0<=0、stride1<=0或channel stride!=1时成立。正的page/row stride可保留原地alias；channel-strided布局才分配[requests+1,state_len,dim] staging并借copy_conv_state搬入/写回。不能用整个tensor非连续就断定必然整池复制。

staging的null_block_id=requests，预留在请求行之后，使packed request0仍是有效状态；来源说明UPDATE不认识PAD_SLOT_ID，不能把负sentinel或另一个后端的index0规避经验搬来。copy kernel自身及CANN接受的全部stride范围另验。

run_mode=0交causal_conv1d_fn，传Silu、initial_state、PAD_SLOT_ID与null block；其他值进入causal_conv1d_update（UPDATE），局部代码未另验证完整枚举。UPDATE只有没提供buffer时才zeros_like，来源注释将共享目的区重置交metadata，本文件不保证任何传入buffer都已清理。

## recurrent与chunk的producer-consumer

GLM recurrent_kda将state_indices和可选accepted裁到cu_seqlens.numel()-1；调用共享run_recurrent_kda时beta_is_preprocessed=False。共享层保持独立Q/K/V strides，仅gate/beta/A_log/dt_bias做contiguous，设置BSND、scale=D^-0.5、state_v_first、inplace_final_state及内部q/k L2、gate、beta sigmoid，不请求额外final_state。

GLM chunk_kda按keep_meta筛state IDs和has_initial_state，gather后转FP32 contiguous；cu_seqlens优先kern版本，否则host，chunk64 descriptors来自metadata。调用共享run_chunk_kda前显式做FP32 beta sigmoid；返回final_state转回pool dtype，只scatter选中行。keep_meta对token的完整压缩归builder负责，不在这里凭空重排q/k/v。

共享chunk调用延迟导入l2norm，对contiguous q/k归一化，带contiguous v/gate/beta、chunk size64、host descriptors，output_final_state=True、state_v_first=True、disable_recompute=False且不返回intermediate。fla_npu外部compiled kernel未读未运行，不以这103行Python替代算子实现闭包。

gather_initial_states只是从Triton Mamba state_ops导入；新请求sentinel/poison行为应沿其实现及测试确认。GLM scatter_states在非NPU用index_copy(int64)，NPU空索引/零extent提前返回，其余检查维度、shape、index device/dtype和每个内层state连续，再view成cache rows调用npu_scatter_nd_update_，保留页padding/offset。unique indices是docstring前提，代码没有显式去重校验。

## 输出缓冲区和投机回滚

普通spec recurrent收到多列state IDs及accepted用于回滚；RecoverSSM verify只取首列checkpoint和两份记录、capacity=K+1，随后真实采样/commit由既有元数据合同处理，不能提前写全部候选状态。

仅无spec、无prefill且有decode时启用direct_output，把caller的core_attn_out交recurrent wrapper；write_recurrent_output写回并返回同一buffer。没有该buffer时，kernel的padding行由caller负责；prefill与混batch另拼接recurrent前缀/chunk后缀，再按spec/non-spec token索引scatter。

metadata缺失或当前层缺键时，_forward清core后在connector之前返回。有效metadata但没有q_ns等分支会save后返回，局部不保证清core；customop外层随后仍可能执行norm，不把这个局部行为解释成最终输出恒为NaN或恒为0。

glm5next_kda_forward从no_compile_layers取层，先_forward再o_norm.forward_oot(...,out=core_attn_out)。注册mutates_args包含该buffer，fake实现为空；保持地址和Triton进程内索引的动机来自注释，不证明NPU图捕获通过。o_proj在其后消费此buffer，不能换成临时norm结果却让已捕获片段读取旧地址。

## connector时序与配置范围

真实metadata分支先wait_for_kv_layer_from_connector，再record_attention_compute_start，执行state更新/verify后maybe_save；profile缺metadata分支不推进connector。调用save标记不是传输完成、目标rank可见或PD协议互通证明。

use_glm_recoverssm检查glm5_next/_text与use_replayssm；validate要求speculative_config存在、无stochastic rounding/APC、mamba mode none、PP/PCP/DCP各1，connector为None或MooncakeV2/Pull。FP16 KV cache仅有未验证注释，不等于此validator硬拒绝；这与前述激活必须BF16的构造guard是不同字段。开关派生/平台与回退复用实验入口，普通KDA PCP能力不放宽这些组合。

## 测试定义与Agent验收

| 已读测试 | 实际证据边界 |
|---|---|
| dispatch448、7函数 | CPU假层/PCP group，替换NPU customop、conv/recurrent/verify；检查重排、cache spec、spec/非spec合并、profile connector与direct buffer，未运行 |
| contracts122、2函数 | mock FLA/l2norm/writeback，检查raw gate/beta、accepted裁剪、padding及chunk compact；未运行 |
| conv63、1参数化函数 | page/row/dim-first×run mode，mock copy与AscendC；不能证明实机stride支持 |
| state74、4函数 | CPU poison/fresh/empty与padded backing，不能覆盖NPU scatter分支 |
| config92、6函数 | SimpleNamespace/CacheConfig与patch校验定义，不是启动或数值结果 |

Agent交付实际dtype/head/conv/K/lower_bound与量化分工、融合权重分片、PCP map、每种conv/recurrent metadata、state shape/stride/offset以及buffer地址/有效长度/清理owner。先验证匹配checkpoint和逐层参考，再加入partial/all rejection、混batch、padding、收缩/空闲、eager/graph与connector；分别计投影、卷积、状态gather/scatter、norm和通信开销。

失败恢复完整已验证的checkpoint/config与状态，关闭新增并行/图/RecoverSSM组合后重建基线；不改null slot、吞guard或随意清所有padding来掩盖错位。当前没有真实checkpoint、NPU、性能或Agent A/B验收。

## ChunkKdaFwd文档接口与GLM实际消费

Main中的ChunkKdaFwd README、API和design共409行描述同名AscendC接口。当前共享包装确实从fla_npu.ops.ascendc导入chunk_kda_fwd，不能把它误写成另一个Triton模块。三个文档提供接口与内存设计证据；本固定目录只有文档，没有文中op_host/op_kernel或测试实现，因此不是完整Operator源码闭包，也没有执行公开样例。

| 接入检查 | 文档合同与当前GLM对应 |
| --- | --- |
| 返回对象 | 稳定Python顺序为attn_out、final_state、gk、Aqk、Akk、w、u、qg、kg、v_new、h、initial_state；当前run_chunk_kda只取前两项，其余用星号丢弃。第12项是Python原initial_state对象透传，不是额外aclnn输出 |
| 最终状态 | output_final_state=True要求计算并导出最终状态；state_v_first=True时最后两维为V,K，与当前GLM读取/写回VK状态对应。非空finalStateOut兼有请求计算与写回的含义 |
| 可选中间输出 | 文档规定Aqk/Akk始终存在；gk在use_gate_in_kernel=False或disable_recompute=True时保留；w/u/qg/kg/v_new仅在disable_recompute=True保留；h在disable_recompute=True或return_intermediate_states=True保留 |
| 内部状态寿命 | 当前use_gate_in_kernel=True、disable_recompute=False且不返回intermediate，不表示内部hCompute消失。hCompute仍供FwdH→Finalize使用；hOut为空只是不向Python公开。丢弃Python返回值也不是避免全部内部张量和拷贝的证明 |
| 输入/输出布局 | layout只解释q/k/v/g/beta输入，attn_out固定BSND/TND，中间量为head-major，公开h为sequence-major；不能把输入BNSD/NTD推广成所有输出都保持同一布局。当前包装固定BSND |

当前GLM先把raw beta转FP32再sigmoid，q/k经独立l2norm，初始state gather后为FP32，传入chunk64和Host descriptors。文档的beta系数与raw/已激活gate是不同入口语义：use_gate_in_kernel=False表示g已是自然对数gate；True才按A_log、dt_bias和safe_gate公式激活，随后chunk-local cumsum除ln(2)供exp2使用。替换后端时应逐项核对，避免重复gate/beta变换或把已累计log2 gk传给稳定顶层入口。

API文档另列legacy torch.ops.npu.npu_chunk_kda_fwd与受限torch.ops.ascend_ops.chunk_kda_fwd_direct；后者仅覆盖dense BNSD、K=128、V=128/256，并接受已累计gk，不能据同名chunk函数交换这些入口。aclnnChunkKdaFwdGetWorkspaceSize/aclnnChunkKdaFwd用独立输出指针控制导出，不接收Python重计算三个开关；cuSeqlens/chunkIndices在aclnn签名为aclIntArray，在当前Python包装则是Host序列，不能从Tensor形状描述推导转换和拷贝已完成。

文档接口列chunk64/128、K/V为16..256内16的倍数、最多1024条变长逻辑序列及rank4变长B=1；这些是文档边界，不放宽本模型BF16/head_dim128和固定chunk64 guard。README列出的产品范围也不替代模型、包版本、CANN与算子实际联调；本卡继续draft/空平台。

README顶部以单个物理L0概述，design又给出A5 dense对齐快路径单launch、其他多chunk按私有stage四段launch的例外。design所述tiling key1/2是形状模板族而非平台编号，隐藏h和其他阶段值可能由workspace或executor内部张量承接。缺少对应Host、Device和构建源码时不能独立确认实际分支、同步、字节账或收益；分析峰值/事件前须取得真实安装的flash-linear-attention-npu与CANN配套版本，闭合入口和执行图。当前仅增加模型推理接口facet，不宣称CV source_closed或真机验证。


## 本地Triton KDA族、RecoverSSM与索引合同补充

同一固定Main补充`ops/triton/kda`十一份Python的完整AST程序投影及四份技术文档全文。AST保留实际控制流、数学、地址、分配与launch，但剔除注释/docstring，来源表不伪称raw逐行全文。这里提炼模型后端接入facet，没有完整Operator、外部Triton/AscendC/CANN编译执行闭包。前文GLM共享包装实际导入`fla_npu.ops.ascendc`的事实保持；本地Triton实现存在不证明该普通GLM caller自动改用它，RecoverSSM另有真实显式入口。

### 同名功能须按具体模块分辨

| 本地文件 | 实际producer/consumer合同 |
| --- | --- |
| `kda.py` | 普通recurrent、chunk流水、gated norm和fused gate包装；chunk64按cumsum→KKT/Aqk→solve→w/u→h/v_new→输出执行，不等于前文外部ChunkKdaFwd十二返回ABI |
| `fused_recurrent_kda.py` | FP32 recurrent状态，读取初始页和accepted-1对应列，逐token写有效目的页；输入q/k可选内部L2，K维只有单tile，状态页索引<=0直接返回 |
| `gate.py` | safe分支为lower_bound×sigmoid(exp(A_log)×(raw_g+bias))，另一分支为-exp(A_log)×softplus；先转FP32并验证head数 |
| `cumsum.py` | 3D标量gate和4D逐通道gate分别实现chunk-local前/反向累计；变长输入要求batch1，chunk_size必须2的幂，累计后乘1/ln2才供exp2的chunk math消费 |
| `solve_tril.py` | 只接尾宽16/32/64，16块求逆再合并32/64；输出转换显式rtne、DOT_PRECISION=ieee，不由chunk其他候选常量推128也可用 |
| `chunk_delta_h.py` | 按逻辑序列保存各chunk入口状态与可选FP32 final_state，K最多256并拆最多四段64；h为[V,K]布局，变长chunk_offsets不能拿原token偏移代替 |
| `utils.py` | lens、chunk_indices、chunk_offsets及contiguous/device guard；最多8条按对象身份缓存，`.tolist()`构建Host chunk索引不是纯device且无同步的准备过程 |
| `conv_state.py` | 从有stride持久卷积cache pack到request-local临时状态，或仅对active请求写回；不计算卷积/接受数 |
| `output_writeback.py` | 把有效recurrent输出搬入最终缓冲并清padding；不计算recurrent、不提交状态 |
| `l2norm.py` | KDA自己的persistent/tiled两种L2实现，FP32平方和加eps后rsqrt；不是RecoverSSM的无eps非零向量归一化 |
| `recoverssm.py` | verify只产输出和紧凑记录，采样后用commit plan、卷积compact与反向记录重建推进checkpoint |

普通Triton recurrent包装在compute_gate=True时总以safe_gate=True调用gate，即使lower_bound=None也代回默认-5；RecoverSSM的lower_bound=None才进入负softplus。不能在这两个包装之间照搬None的含义，也不能把普通Triton内部q/k的`sqrt(sum+1e-6)`与RecoverSSM“非零除真实norm、零向量为零”的政策合并。普通wrapper还按k分配输出、要求NK=1；底层kernel出现独立V参数不说明任意K/V组合均通过包装shape与buffer验证。

### chunk中间量、输出alias与gated norm

本地chunk固定FLA_CHUNK_SIZE=64，g按chunk累计后乘RCP_LN2，A/Aqk以FP32建立，solve结果转换到k dtype，w/u及kg供状态推进，输出把chunk入口状态贡献与下三角局部项相加。最终调用将`o=v`作为目的缓冲；上层v.contiguous()在已经连续时不会自动克隆。替换/重排时应把v所有权与后续读者列入合同，不假定chunk返回另一个独立输出。

gated RMSNorm有D<=512、无residual/prenorm、3D或leading1的4D、连续x与指定packed gate stride的多行快路；直接out须shape/dtype/device匹配且连续。packed beta/gate/gate行宽为`H+2*H*D`，与一般gate stride不是一个索引公式。其它情况进入reshape/通用norm；direct out与residual/prenorm组合明确拒绝。快速路径不交付mean/rstd，不应因共享底层norm参数就要求每次都有stats或允许任意packed布局。

chunk metadata helper的cache只比较参数对象的`is`身份，没有检查Tensor内容版本。复用同一cu_seqlens对象并原位更新时，不能据对象/地址稳定推导lens、chunk_indices和offsets已经随内容重算；应沿实际builder/prebuilt_meta的生命周期核对刷新。input_guard会把Tensor参数contiguous并选设备上下文，它不是值域、所有stride与无Host同步的完整验证器。

### 卷积staging哨兵与输出padding

copy_conv_state按有效slot且query长度>0判断active。pack清inactive数据，writeback只改active状态并保留物理页gap；cache页地址将slot转INT64，页内行/通道继续显式stride。256通道tile与最多65535程序的循环grid覆盖实际状态，不表示一次复制整个物理page。空request提前返回；writeback同页多writer和storage重叠仍是caller前提。

这里存在文档/实现差异：`docs/conv_state.md`写inactive packed_indices=-1，固定代码实际写`REQUESTS`，与前文GLM在请求行后预留null block一致。不得照抄文档-1喂给UPDATE；应以真实kernel、staging分配和AscendC consumer共同核对。该文档泛称non-contiguous触发copy，而实际GLM wrapper依据特定stride条件决定，不能以文档概述改成所有非连续整池复制。

write_recurrent_output以16KiB为tile，device读取最后query end并截到source token数；整个source为空或tile完全越过source allocation时，不发起source load而写零。只用全False mask的越界地址并不等价于跳过load。destination空直接返回，其余全部元素被覆盖，不能用padding旧值当状态信号。do_not_specialize的计数仍是捕获时固定的launch实参；图重放可改缓冲内容，不自动变更捕获shape/grid/标量参数。

`docs/l2norm.md`主指FLA路径及persistent69行策略；KDA实现另有use_tiled_kernel=True的32行/BD列mask，chunk caller明确选择它。该KDA persistent分支的列索引直接arange(N)，不能凭另一文档的非2次幂测试描述证明任意D下该分支可编译。`rsqrt(sum(x*x)+eps)`也不应与使用max(norm,eps)作分母的任意normalize参考不加区别地互换。

### RecoverSSM：verify记录与采样后commit

verify读取[P,H,V,K] checkpoint，逐token在FP32寄存器推进并交付输出，写FP32 correction[P,H,Q,V]以及原始k/raw_g拼接的kg[P,H,Q,2K]；它不写持久checkpoint，末token甚至不做无下游用途的完整state更新。Q/K无eps归一化后，query再乘K^-0.5；gate和raw_beta sigmoid在内部处理，不接受调用方误传已累计log2 gate或重复sigmoid。

commit先把spec行映射到sampler行，将接受步数截到[0,min(query_len,Q)]。接受数包含该行应提交的target输入步，不能直接等同“额外命中draft个数”；null页或0接受为no-op。随后卷积将历史区间[c-1,c-1+W)移到[0,W)，递归状态从最后接受记录向前积累decay与correction outer product，再与原checkpoint合成。拒绝后缀不应被读取或提交。

context.create要求各层checkpoint/记录shape、dtype和内层stride对应，允许逐层page stride不同；它保存实际layer Tensor引用、INT64地址/stride表，并stack A_log/dt_bias与分配固定plan arrays。创建必须先于图捕获，层存储重分配、参数热换或state layout改变时不能继续盲用这些地址和堆叠参数快照。捕获后仅改变内容并不自动更新create时的派生表。

底层align需要block_table、num_computed_tokens、mamba_block_size全有或全无，且block size覆盖Q；可额外写boundary checkpoint/history。这是低层分支，不放宽GLM serving已声明mamba_cache_mode=none/PP/PCP/DCP等门禁。普通commit与grouped commit都使用调用方SPEC_QUERY_LEN，没有固定6步默认。

A5、FP32 checkpoint、无align、K=V=128、H=32或64才选两head grouped commit；其它情况走ordinary。A3 accepted循环保持运行期迭代，A5可静态展开。ordinary按真实UB预算、BK、2或6个矩阵buffer及两行临时量限制BV；属性缓存缺失采用192KiB保守fallback，不等于声明A5物理UB就是192KiB。A3 strided卷积compact用256通道，A5或连续通道可用4096；切设备/布局须重看实际选择，不能只修改tile常数。

文档记载了独立FP64 golden、逐输出比例与绝对误差双门槛，以及早期A3/A5结果；提取版又明确当前A5因微基准OOM未完成完整精度套件，历史A5通过不能转授该源码。本次只读取资料，未运行这些测试。算法off/on的服务TPOT与相同算法stride/UB改动微基准是两类比较，不把历史数值合成普遍收益或本次Agent真实性证明。实际验收应覆盖零/小norm、接受0/部分/全部、null页、图收缩、stride/page gap、不同Q、ordinary/grouped及未知align路径，再分别归因数学、metadata、copy和编译资源。
