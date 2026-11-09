---
type: Guide
title: vLLM Ascend GDN310P接入：专用状态、分块算子与补丁入口
description: 接入310P GDN时核对worker分派、FP16 SSM、phase索引、padding和AscendC chunk前提，区分参考函数与生产接口及状态布局。
aliases:
- GDN310P接入
- _flatten_state_indices
- chunk_gated_delta_rule_310
- chunk_gated_delta_rule_pytorch
- l2norm_310p
tags:
- task.implementation
- topic.model_adaptation
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/gdn_310.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/chunk_gated_delta_rule.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/fused_gdn_gating.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/l2norm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_idex_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/gdn_attn_builder_310.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_qwen3_5.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_chunk_gated_delta_rule_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/causal_conv1d_310_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_host/causal_conv1d_v310_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_host/causal_conv1d_v310_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_host/causal_conv1d_v310_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_host/causal_conv1d_v310_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_host/math_util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_kernel/causal_conv1d_v310.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_kernel/causal_conv1d_v310.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_kernel/causal_conv1d_v310_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_kernel/causal_conv1d_v310_tiling_data.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/causal_conv1d_v310/op_kernel/causal_conv1d_v310_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/op_kernel/arch20/epilogue/block/block_epilogue_gdn_fwdo_output.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/data_copy_transpose_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/data_copy_transpose_tiling_def.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/error_log.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/tiling_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/tiling_templates_registry.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/tiling_type.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_fwd_o_vllm/tiling_base/tiling_util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/op_kernel/epilogue/block/block_epilogue_gdn_fwdh_update.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/op_kernel/epilogue/block/block_epilogue_gdn_fwdh_vnew.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/op_kernel/epilogue/gdn_fwd_h_epilogue_policies.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/op_kernel/gemm/block/block_scheduler_gdn_fwd_h.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/op_kernel/gemm/kernel/gdn_fwd_h_kernel.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/data_copy_transpose_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/data_copy_transpose_tiling_def.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/error_log.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/tiling_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/tiling_templates_registry.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/tiling_type.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/chunk_gated_delta_rule_fwd_h_vllm/tiling_base/tiling_util.h
  role: implementation
created_at: '2026-10-31T11:43:07Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T06:23:04Z'
---

# vLLM Ascend GDN310P接入：专用状态、分块算子与补丁入口

## 任务与固定证据

接入310P GDN时，沿worker补丁入口、conv/SSM dtype、phase/state索引和chunk实际算子逐项核对。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，主来源gdn_310.py441行，chunk586、gate62、norm43、补丁54、worker90和UT191/147全文；另复用四份同SHA全文证据。仅作数据阅读，未执行上游导入、测试、NPU、compile或模型，整项功能平台交集待验，保持draft/空平台。

Native父类/外层custom op、AscendC完整实现、RC检测和SP调度仍未闭合。版本身份沿[框架记录](../../concepts/frameworks/vllm_ascend.md)核对；[公共GDN执行](vllm_ascend_gdn_runtime_dispatch_contract.md)的FLA/CANN/Triton选择、registered packed权重和connector wait不能直接套来。

## 先确认实际worker入口

worker按STANDARD_WORKER_PATCHES选择patch_qwen3_5，否则导入patch_idex_310；条件是capability，不能把else泛化为硬件名或支持认证。310P profile没有该flag。patch_idex_310将Qwen GDN的core、get_state_dtype、get_attn_backend替换为310类并取消warmup；RC条件还替换Native GDNAttentionBackend.get_builder_cls。

仅对AscendGatedDeltaNetAttention310类调用get_attn_backend的CPU断言，不能代替实际worker已装上补丁的证据。patch_qwen3_5的兼容分支只替core/dtype，须与真实bundle入口分开读。其他draft、FLA index、RC vision和V2补丁不属于本卡的已生产语义。

## 状态dtype、卷积权重和phase

get_state_dtype沿原方法保留conv state dtype，仅将SSM state改为FP16。core从self.kv_cache取两种state；这里没有公共core的显式connector wait，末尾仍save，外层传输同步需另核。

conv weight每次从self.conv1d.weight按[D,1,W] view/transpose成[W,D]；没有公共GDN注册packed参数的读取和LoRA base_layer解包。不能为本路径机械增加公共重载hook或宣布GDN LoRA已支持。

非SP时先裁qkv/a/b到num_actual_tokens；SP时保留图输入宽度，后面按有效输出切片。spec-only直接用投影，混batch按spec/non-spec token indices选择。卷积spec用descriptor offsets/state/accepted裁到num_spec_decodes，run_mode=1；普通prefill用顶层offset/history、run_mode=0，普通decode以num_decodes切行、run_mode=1且query_start_loc=None。

这些卷积调用传PAD_SLOT_ID，不能由此把所有phase的state padding改成-1：普通decode metadata仍可能含NULL0，须按实际query span和kernel消费判断。activation_mode仅由activation真假决定。

## padding与recurrent索引

uniform spec-only用spec descriptor末offset作为有效token数。_zero_padded_tokens按设备arange比较并乘mask，先遮投影尾部、合并后再遮core尾部；不读取valid_tokens.item。它对有限值的CPU用例成立，但NaN×0仍为NaN，不能当通用NaN清理器。

_flatten_state_indices一维切total_tokens后转int32/contiguous；二维在capturing或完整均匀slots条件下reshape前num_seqs行。capture分支依赖uniform布局，不能推广成任意ragged输入安全。

eager ragged将state IDs和seq lengths拷到CPU，masked_select有效槽、截断，再non_blocking拷回。源代码的pin分支写成属性flat_cpu.is_pinned而未调用is_pinned()，不能据此证明缓冲已pin或拷贝实际异步。这里记录源码核对点，没有执行或修复上游。

npu_recurrent_gated_delta_rule_310将q/k/v/beta转FP16连续，g转FP32，state原样传递；actual_seq_lengths为diff(cu_seqlens)，不是前缀和。可选q/k norm由l2norm_310p处理。PAD_SLOT_ID不能clamp到0，否则会指向真实block0。

_mask_padded_recurrent_accepted_tokens对零长度请求将accepted变0；producer为仍启用的graph dummy填1是另一层合同，不能合并成一个全局常量。先裁实际请求，再核accepted、offset和state行是否一致。

## gate与归一化

fused_gdn_gating_pytorch将非线性输入转FP32，g=-exp(A_log)×softplus(a+dt_bias)，默认beta参数1、threshold20，beta输出为FP32 sigmoid后转回b.dtype；二者补[1,T,H]维。torch.where的分段表达不自动证明所有输入都无overflow。

l2norm_310p将末维reshape成连续2D，缓存weight=1/sqrt(dim)，调用NPU RMSNorm时eps_rms=eps/dim，再恢复shape。这样对应L2分母sum(x²)+eps；缓存、epsilon公式和真实NPU数值是不同证据。

## reference与production入口必须分开

chunk_gated_delta_rule_pytorch是reference-only，生产chunk_gated_delta_rule_310明确不会回退到它。UT147行的三个CPU函数只调参考入口；norm开启时还替换npu_rms_norm，不能拿该测试证明生产算子。

生产_require_ascend_chunk_ops要求q在NPU、h/o两个AscendC符号存在、q/k/v全FP16、value head dim至少128且整除128。参考用例的V=12不是生产支持shape；这些guard在空token返回之前也会执行。

接口接受BTHD或带cu_seqlens的TND，后者先补B=1；q/k shape、g/beta的B/T/Hv分别校验，可变长要求B=1，head_first=True直接raise DeprecationWarning。Grouped value heads要求Hv可被Hqk整除，q/k用repeat_interleave扩头。

## chunk64、状态布局与回写

生产在Torch中准备FP32 WY前缀、g cumsum和三角递推，w/u转FP16，再委托AscendC h/o。均匀输入pad到64倍数；可变长将cu拷CPU，逐序列独立pad，构造Python offsets/chunk列表，空段跳过并紧凑重编号。不能宣称没有CPU同步或capture问题。

输入初态预期[N,Hv,V,K]且device匹配；缺初态时分配FP32，已有初态保留其dtype。传kernel前VK→KV transpose/contiguous，use_exp2=False、transpose_state_layout=False；返回final state再转回VK。完整kernel的空段state恢复与真实stride仍需核对。

空token路径返回空输出及请求时的原initial_state；若initial_state=None，final state也可能None。它不绕过NPU、dtype、head维guard。参考路径则使用FP32 state clone和Torch递推，不能混用两者的返回dtype/空段承诺。

prefill后将last state转SSM dtype，再对pool行做index_copy_；mixed输出用_merge_spec_and_non_spec_outputs_310校验两个输出长度后直接索引写回有效core前缀。避免的是这处输出index_copy，不是全路径删除index_copy算子。

## 接入交付和验证

保存实际patch/backend/builder、conv与SSM dtype、各phase有效请求/token数、state IDs、accepted和offset、chunk扩展与shape guard、初末state布局及写回行。先验证eager的数值与连续步state，再在实际获准软件栈测试graph/SP/RC；CPU graphmetadata fixture不能宣布整模型图模式支持，也不能覆盖旧版本已记录的捕获限制。

本批12个测试函数均只读，未执行。失败恢复匹配worker bundle、模型、metadata、扩展及完整state，确认基线后再测新组合；不将PAD改0、删shape guard或强制参考函数当生产回退。具体场景探针见[310P GDN诊断](../../runbooks/precision/vllm_ascend_310p_gdn_padding_readiness.md)。


## v310卷积：有效请求与状态历史由谁保证

补充固定ceac的v310卷积Host/Device和GDN h/o辅助模板。35条路径中27份内容唯一；8份tiling_base文件是h/o两处的同字节副本，复用同一语义。五份小入口/注册文件逐行全文，其余按完整声明、分支与调用结构投影，并直接核对下述数学、索引和状态片段；这不是完整Device算法或算子级闭包。

`npu_causal_conv1d_310`用`at::empty`分配输出，传入state、query_start_loc、cache_indices、initial_state_mode与num_accepted_tokens。OpDef注册ascend310p，实际主数据/权重/偏置/state/output只列FP16；Device入口也固定`RunCausalConv1d<half>`。Host错误文案出现bf16对齐不能增加BF16支持声明，注册配置更不能替代真机证据。

Host接受二维packed `[T,D]`、二维decode `[B,D]` 或三维 `[B,L,D]`；权重必须是`[W,D]`且W为2至4、D整除16，state为`[pages,stateLen,D]`且至少W−1个历史槽。ragged二维prefill要求显式query_start_loc。二维decode在offset数量与行数不等时改按ragged布局解释，不能只由输入rank判断每行一个请求。InferShape只复制x的shape，不验证这些语义。

cache_indices可一维或二维；二维只按stride读取每请求第一列，不表示每token独立state。缺索引时按请求序号取page并要求page足够。initial_state_mode可选BOOL/INT32/INT64；缺省时decode读历史，prefill不读。Host核对长度/dtype，具体offset单调性、cache ID合法性仍在Device逐请求判断。

`num_accepted_tokens`只允许decode，且当前要求W=4；三维spec输入还要求stateLen容下`2+L`。Device用accepted−1选择历史起点并夹到有效范围：accepted为0并不会使一个正长度请求自动不执行。调用方须同时保证query span、有效请求数与PAD ID，不能把本卡recurrent的零accepted屏蔽规则直接套给卷积。

Device遇到无效offset、零长度、PAD ID或越界cache page直接跳过对应请求；由于输出来自`empty`，被跳过的区域不保证为零。普通回写只保存最后W−1个输入历史；spec W=4保留两个历史位置，再保存当前整段输入。spec容量/宽度不满足的Device内部路径会走普通回写，而不是完整spec历史，这也不免除Host和调用方前置检查。

卷积weight、bias与ring转FP32累加，激活可选SiLU，结果转回FP16。输出的CAST_NONE/CAST_RINT随分支不同；两块输出缓冲与MTE/V事件属于本次kernel的调度，不能由源码阅读声明跨stream并发或数值误差已验证。

## GDN h/o辅助模板：紧凑请求、门控与尾块

通用fwdh scheduler在varlen路径扫描INT64 cu_seqlens，跳过空段并把非空请求紧凑编号；tokenOffset仍指原packed输入，但initial/final state按紧凑batchIdx寻址。调用方必须把state行与同一个紧凑映射配对，不能把原始请求号或含空段的state直接套用。两个stream的workspace按core与stream分区复用，并以chunk推进请求任务。

fwdh Vnew分开保存`u-WH`与带门控衰减的workspace，两个量分别RINT转输出dtype；不能交换这两处消费者。h update支持初始/最终FP32 state路径，中间h可能先窄化；k-gated分支对最后gate乘LN2再Exp，其他门控选项由模板政策与实际实例决定，不能从helper存在推导310P Python入口启用了所有组合。

当尾块有效token少于16时，Cube侧只发完成标志，Vector侧随后显式计算tail V/H workspace并执行相同epilogue；这不是静默丢弃尾部。fwdo输出epilogue则按子块/阶段处理行，把FP32 attention项与`exp(g)×h`相加后乘scale，再转输出dtype。固定UB偏移和ping-pong事件的全shape容量证明仍须结合实际tiler、模板实例与运行证据。

两份tiling_base副本提供通用流程和模板注册：自动候选只有返回`GRAPH_PARAM_INVALID`才尝试下一项，其他错误直接返回；显式优先级列表同样区分成功、拒绝与失败。日志中的success字样不覆盖返回错误码，框架接入时应保存最终status、SoC、选中key与workspace。这里没有执行编译、上游测试、模型、NPU或性能基准，完整Operator、混合精度误差和图/SP组合仍待验证。
