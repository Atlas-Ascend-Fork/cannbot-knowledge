---
type: Guide
title: vLLM Ascend SWA 有界回放：恢复载荷、共享KV写保护与降级
description: 适配SWA回放时核对Native恢复载荷、共享KV保护和V2 decoder子批次，验证PCP尾行、DP协调、prompt logprobs保留及图/context边界。
  用 DecoderReplayState.num_actual_tokens 核对实际保留行与补齐行。 SWA bounded replay的replay_start/window生命周期由NPUModelRunner._fill_replay_start管理：窗口到期或computed退回边界之外时清除；完成请求清除，恢复请求先清旧再取新边界。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_swa_bounded_replay.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-V4.1-Flash.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/swa_bounded_replay_probe.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_swa_replay_downgrade.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_swa_bounded_replay.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/decoder_replay_layers.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_interface.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v41.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/compute_slot_mapping.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/decoder_replay_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_decoder_replay_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/decoder_replay.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/model_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/cache_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_cache.py
  role: evidence
created_at: '2026-10-31T00:25:33Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:07:25Z'
aliases:
- DecoderReplayState
- DecoderReplayInputs
- gather_replay_batch
- EngramModelState
- DecoderReplayState.num_actual_tokens
- NPUModelRunner._fill_replay_start：SWA bounded replay start/window生命周期与到期清理
- NPUModelRunner._update_replay_requests：SWA回放边界更新
---

# vLLM Ascend SWA 有界回放：恢复载荷、共享KV写保护与降级

7d9e增加完整cut层KV预写和首SWA专属encoder边界builder，见[7d9e运行时迁移](vllm_ascend_7d9e_runtime_delta_contract.md)的DeepSeek V4.1节；本卡旧回放起点和buffer处理不自动代表新版本。

## 消费任务与来源范围

适配新模型时，先区分prefix命中后的SWA窗口重建、恢复请求的wire边界与decoder层裁剪。它们关系到共享KV正确性，不能用启动成功、ACL Graph replay成功或offload命中替代验证。本卡以ceac提交patch_swa_bounded_replay.py全164行为主证据，结合KV接口551行、decoder层150行、两份UT与probe全文，以及platform/attention/V1 runner/block table/Triton的明确选段。文件来源绑定不是所有分支语义闭合；本卡硬件未知，保持draft/platforms=[]。

## 当前patch是Native协议扩展，旧版本声明需核对

_upstream_carries_replay_start()用hasattr(Scheduler,"_mark_prefix_replay")判断接口，而非版本字符串。没有该Native方法就跳过当前补丁，不在本文件注册旧版配置或重写prefix admission。platform/__init__.py确实导入补丁，但注册不证明gate满足。教程§12声称为旧vLLM0.30回移配置/request/local prefix admission、默认关闭且KV connector报错；这与当前所读扩展不能直接拼成完整兼容实现。实际安装版本、模块与接口须另核对，未读Native admission/default flag与外部镜像补丁不当已证明。

有Native接口时，Ascend补CachedRequestData.replay_start，字段为dict[str,int]、default_factory=dict。只有实例setattr不构成dataclass/wire字段；代码补annotations与field、删除自动生成__init__后重跑dataclass，保留自定义repr/eq以维持既有脱敏。已有同名declared field会跳过添加，不额外验证其类型。必须在engine与worker首次msgspec类型缓存前导入，双方一致；本批没有实际serialization roundtrip。

Scheduler._make_cached_request_data参数名和顺序必须恰为self、running_reqs、resumed_reqs、num_scheduled_tokens、spec_decode_tokens、req_to_new_blocks，漂移显式RuntimeError。包装有idempotent标记；先调用原方法，再仅从resumed_reqs的truthy replay_start构造map，0/absent不发送，空resumed得到{}。这里不校验负值、完整请求序列或admission正确性。V1恢复走cached载荷；V2注释所述新request路径与上游准入仍需单独核对。

## 架构开关、cache spec与调度降级

resolve_bounded_replay仅接受DeepseekV41ForCausalLM与DeepseekV41ForConditionalGeneration，再要求cache_config.swa_bounded_replay为真；缺字段的release lane按False处理。V4或DSpark draft类名不在该allowlist。PCP>1且DP>1警告并返回False，此函数没有硬件能力验证。declared_kwarg只给构造函数明确声明的参数传值，不按vLLM版本猜ABI。

AscendSlidingWindowMLASpec默认bounded_replay=False；启用时prefix_cacheable=False、prefix_replay_tokens=sliding_window，关闭时为True/0；storage_block_size=block_size//compress_ratio。合并要求包括quant/compress/model/window/extra_retained/bounded一致，optional extra字段只有下游类明确声明才转交。通用is_prefix_cacheable对wrapper递归，结合prefix_cacheable与participates_in_prefix_cache；缺属性时的默认True不是任何实际组都可共享的证明。其他Mamba/Tail布局不由此SWA facet全部闭合。

platform._downgrade_swa_bounded_replay在scheduler选择后执行；以下独立复制schedule主体的模式会关闭开关，优先级依次为recompute_scheduler_enable、dyntra_lb_config.enabled、profiling_chunk_config.enabled、enable_balance_scheduling。V41架构才产生相应warning，其他模型也可静默清除开关；cache缺失/开关已关则安全返回。BatchJobScheduler继承super().schedule、ShortRequestFirst未覆写该主体，静态UT保留开关；不能从“自定义scheduler”四字一概禁用所有子类。platform注释称Native开关默认开启，教程旧compat称默认关闭，实际Native CacheConfig未在此卡读取，按配置路径分开而不补默认。

## V1状态生命周期与共享KV写保护

_update_replay_requests仅在prefix_replay_tokens非0时工作。完成请求移除边界；新request先清旧边界再取truthy字段；resumed请求先清旧状态，再从cached.replay_start读取。恢复载荷为0/缺失不会沿用上次回放位置，防止preemption后的陈旧边界。_fill_replay_start先清零整段CPU含padding，仅在start<=num_computed_tokens<start+window时保留，过期pop，整buffer复制到GPU；没有活跃请求时返回None，_attn_replay_start同样阻断profile/capture/dummy残留。所读prepare路径先校正乐观seq长度，再生成各组slot mapping，随后执行PAD pass。

block table构建active各组slot_mapping地址及is_prefix_cacheable组索引，绕过fused路径额外条件，mamba组另排除。pad_replayed_slot_mapping在请求数或cacheable组数为0时不发kernel；每个请求start<=0提前退出，否则只将positions属于[start,start+window)的cacheable组slot改成传入PAD_SLOT_ID。SWA组本身不参与prefix共享，因此必须保留写入以重建窗口；不能把所有组写入都屏蔽。此保护避免重算不同KV覆盖其他prefix命中请求仍共享的cache；它不是已验证跨请求隔离的完整证明。PAD_SLOT_ID数值来自Native，本卡未读该常量，不假设一定为-1。

## 注意力可见区与decoder裁剪是两层条件

build_replay_swa_visible_lens按每个query位置p计算floor=max(p-W+1,replay_start,0)，长度为p-floor+1、INT32列向量；使用query_lens repeat_interleave映射请求。调用方负责query长度和position/replay边界一致，局部函数没有将所有非法负长度自动拒绝。SWA spec window必须等于model sliding_window，以保持写padding与读下界一致；所读attention callsite把长度传给SparseFlashMla的ori_topk_length。退休null block的零值若当有效键会污染softmax分母，不能凭零填充值忽略读边界。Native Device算子与所有非因果/draft路径未在此卡闭合。

AscendDecoderReplayLayers只在有selected rows时裁剪，否则正常执行；DSA CP与sequence parallel需要gather/选择/重分布，重用buffer的恢复与context生命周期按下文新增V2 state范围核对，仍不能据此断言完整图/CP路径已验证。make_decoder_replay以最后KV source层cut划分：cut已到尾部则无收益返回None。以下任一条件禁用该decoder优化：PCP>1且DP>1；SP无DSA CP、PP>1、DCP>1或ubatching；图模式不在NONE/FULL_DECODE_ONLY；Engram层在cut之后；spec方法非DSpark；draft窗口缺失/大于target或包含非sliding_attention层；LoRA配置存在。空draft layer_types不会被any检查单独拒绝，不补不存在的校验。

成功后start=cut+1并输出Ascend MRV2 decoder bounded replay日志；函数自身没有完整Runner版本gate，不凭日志名字宣布V1绝对不支持，也不能把decoder裁剪返回None等同基础SWA回放全部关闭。DSpark状态/LoRA映射/独立并行layout都需另验。

## 验证设计与probe能证明什么

先按[模型部署与Runner边界](../models/vllm_ascend_deepseek_v41_platform_boundary.md)固定版本、checkpoint、并行拓扑与Engram，记录实际开关、Native接口和scheduler实现。教程A5 raw FP8/MRv2 TP1DP4EP4是单独回归场景，不外推全部硬件。

swa_bounded_replay_probe.py静态定义3个case：短算术、长加法、长减法，长上下文段落重复600次；seed1024、temperature0、max_tokens32、timeout600秒、enable_thinking=false。无baseline每case1次共3次；非空baseline每case8次，4线程共24次，长case检查首响应prompt_tokens>4096。请求HTTP失败/空content会assert；结果JSON先写盘再比较。只比较text和finish_reason，usage/logprobs虽保存并不逐项相等检查；没有算术标准答案、激活日志、实际prefix-hit/preemption、质量集或性能阈值检查。baseline={}会走无基线分支，不能将打印PASS当完成差分。

验收需要关闭回放基线→重启明确启用→同请求一致，并另查实际SWA bounded replay is active日志；仅HTTP200/配置True不证明命中过窗口回放。跨chunk预算小于SWA窗口，补混batch、preemption/readmission、短prefix<=window完全重算、无prefix hit、窗口到期/clear、共享组不覆写与SWA可见区golden。UT对dataclass/signature/映射/降级的定义只作检查设计，其中Native接口缺失时skip不能当PASS；本批没有执行这些上游测试、服务或NPU。

出错先关闭本次新增回放开关、恢复配对版本和既有已验证配置；ABI漂移、wire字段缓存时序或scheduler-copy不匹配应显式处理，不绕过保护。只有功能与数值通过后才比较TTFT、TPOT、吞吐及内存，并记录命中率、前缀长度、窗口、chunk预算与并发；本卡没有声称优化收益。

## V2 decoder子批次状态与请求复用

新增范围固定为decoder_replay_state.py343行、decoder_replay_layers.py150行、Engram model_state333行和Triton gather115行，结合236行状态UT及缓存UT全文；没有执行上游import、测试或kernel。DecoderReplayState与基础prefix窗口回放是不同层次，rows=None时adapter走正常run_layers，不把decoder裁剪禁用解释为基础SWA功能全关。

EngramModelState不再另建父类generic decoder replay batch；只有model.decoder_replay_layers存在才创建专属state。add_request按持久request slot刷新_replay_start_np，缺字段变0，并按sampling_params.prompt_logprobs is not None刷新keeps_rows，包括值0；不能在请求slot复用后保留上一个请求的裁剪例外。

prepare每次先清layers.rows/context_factory/num_padded_rows与replay_pcp_context。其他buffer不全清，rows=None才是未启用裁剪的入口；首次slots=None时_initialize发生在capture/graph/profile拒绝之前，用当前VllmConfig找builder、跳过Circular缓存、准备source RoPE并warmup gather。不能由已初始化fixture的“graph不调用_gather”测试，推成首次graph调用从不初始化或编译。

仅eager非profile实际路径继续准备；DP>1且跳过跨DP all-reduce的配置直接不裁剪。普通请求只将prefill query保留末min(query_len,window)，decode、prompt logprobs和dummy的行保留。DP以CPU 2×DP信息协调是否有任一rank裁剪及每rank token数，peer裁剪时idle rank仍参与；跳过coordination的外部模式需另验，不能按本地无query直接退出通信。

## PCP保留行、padding与gather

PCP先按global request决定末窗口，按persistent idx_mapping应用keeps_rows，再计算原来持有这些尾部行的local owner；不是每个rank独立截自己的末window。全局8行/window2的UT例中，global replay_start为6，local end=4的owner保留0行，end=8的owner保留2行；这只是CPU定义，没有运行PCP网络。

num_actual_tokens是本地实际保留行，PCP num_tokens使用全局保留和作为padding容量；非PCP DSA-CP按TP对齐而不增加actual计数。_build_replay_pcp_context通过local_token_indices/gather/sort/search构造compact global batch和hidden_restore_idx，清旧gather/write mask；缺失owner或非法映射的完整保护尚未闭合。

gather_replay_batch的公共参数顺序包括seq_lens、encoder_replay_start、positions与slots，236行UT只用mock核对13个参数。kernel以累计dropped_before构造新offset，选原query尾行；未裁的query仍需前WINDOW-1历史，裁过的history为0，replay_start还取encoder边界最大值，不能一律用seq_len-window。

输入/输出slot各有独立group stride。padding行选row0、用positions[0]，所有group的写slot硬编码-1；它不是“补零后随意写null block”。空/无请求由调用方处理，该wrapper没有给出全局N=0通信安全证明，也不能未经Native核对就把所有PAD常量等同。

## metadata、context与输出恢复

_build_metadata更新query offset、positions、slots与replay_start，保留原seq_lens、block table和请求分类；max_query_len取compact与原batch上界的较大者。PCP再gather slots并传context/group ID，准备共享batch/group metadata、use_cache=False RoPE及device任务。Engram调用在super.prepare_attn之后把self.pcp_context交给state，其与此前局部context的生命周期仍依赖父实现。

forward_context保存mc2 mask副本并在finally恢复，子context尾PAD mask置False；显式继承outer的eplb_heat_collection_status，不是复制所有additional kwargs。outer padding按SP gather→retained rows选择→尾部True→chunk回本rank处理；全局context与实际TP对齐仍需真实consumer验证。

AscendDecoderReplayLayers按states[2]取positions；SP输入除positions外会gather/选行/再切分，输出仅前两项hidden/pre_mix按SP恢复，aux已由模型聚合。DSA-CP row buffer先从旧分区gather再按新行分配；PCP可补零至num_padded_rows。输出以原token数新建零tensor，只index_copy实际保留的行，丢弃行仍为零，不能拿它声称重建了所有原始hidden。

EngramModelState的FULL replay_start含padded请求行并先清零；仅prefill映射真实边界，decode为0。cacheable组在[start,start+window)内屏蔽写入，PCP修改global slots后刷新gathered slots；普通非回放FULL不自动传ReplayAttnMetadata，已有model_specific_attn_metadata也保留。SWA组写重建窗口与共享组保护继续分别验证。

所列状态UT验证正常trim、prompt logprobs、PCP owner、lazy builder、graph/profile清旧rows、DP idle和DSA-CP padding；gather/metadata被mock，source.kernel与缓存/CP测试也未执行。验收记录original/actual/padded三种行数、persistent request slot、offset/position/replay_start、每组slot、context恢复及scatter后的有效行，再比较无裁剪基线；不能只看rows长度或日志当精度与性能通过。
