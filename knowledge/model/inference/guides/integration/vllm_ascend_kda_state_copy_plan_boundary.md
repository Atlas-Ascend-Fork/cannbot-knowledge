---
type: Guide
title: vLLM Ascend KDA状态拷贝：页索引、启动计划与纯kernel边界
description: 区分Kimi KDA的worker-owned prepare/seal生命周期与_kda_state_copy_kernel实际寻址，核对无效页/初始标志、INT64页偏移、dtype/inner
  layout及图和编译器边界；不把GLM RecoverSSM或kernel私有入口当完整sealed plan。
aliases:
- KDAStateCopyPlan
- _kda_state_copy_kernel
- _validate_cache_layout
- vllm::kda_state_gather
- vllm::kda_state_scatter
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/kda_state_copy.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/kda_state_copy_kernel.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/kda_state_copy_plan.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/kimi_kda.py
  role: implementation
created_at: '2026-11-03T06:08:34Z'
updated_at: '2026-11-03T06:33:14Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend KDA状态拷贝：页索引、启动计划与纯kernel边界

## 任务、来源与证据强度

当Kimi KDA prefill需要把paged recurrent state gather到packed状态、在chunk计算后scatter回cache时，分别核对数据协议和启动/服务生命周期。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文阅读state-copy技术文档182行以及kernel模块146行的完整AST程序投影；没有导入/运行上游、编译/JIT、NPU、图或性能实验。

文档描述worker-owned KDAStateCopyPlan，所读kernel模块只保留私有kernel、配置快照helper和公共layout校验；它没有prepare/seal、worker发布、Fake注册或fallback launcher实现。本文将这些plan职责明确标为文档/调用方合同，不能只调用私有kernel就宣布启动无JIT、all-or-nothing或整模编译闭合。完整plan/worker代码与真实运行仍应另取证。

[Kimi部署](../models/vllm_ascend_kimi_k3_kda_mla.md)拥有模型/硬件与混合cache组合，[GLM KDA接入](vllm_ascend_glm_next_kda_dispatch_contract.md)和[RecoverSSM元数据](../../runbooks/precision/vllm_ascend_glm_recoverssm_graph_metadata.md)拥有另一套状态推进。此拷贝路线不替换GLM KDA或chunk/recurrent数学，不将GLM的null页规则套入本kernel。

## 数据移动与索引

cache为[N,H,V,K]，packed为按选择序号展开的dense内层payload。kernel把selected、tile、lane和读到的cache index先转INT64，再乘page stride，避免INT32索引在大于4GiB页间距时先溢出。payload内部按固定8192元素tile处理，末tile有mask；cache页gap和layer storage offset并不属于packed输出。

- gather读取valid index所指页，存在flags时还要求对应flag非零；无效index或false flag输出零。重复gather index可以读同一页。
- scatter只写valid index，flags不抑制最终写回；有效目的页须唯一且不重叠，kernel未实现多writer仲裁。
- 此处valid为`0<=index<cache_rows`，所以index0是有效状态。无效index的寻址基址先用safe_row=0，再按valid mask屏蔽；不能直接传负页地址并假定masked load总可安全。
- packed和cache不得相互重叠；flags/index stride由调用方提供。copy是存储搬运，没有归一化、recurrent更新或接受长度裁剪。

_validate_cache_layout要求NPU、rank4且N>0，dtype仅FP32/BF16，各inner维为正；按K→V→H核对非singleton轴的dense stride，并要求page stride不小于payload。它不在此扫描索引值/目的页唯一性、不验证整个worker绑定，也没有判断950设备。不能把这一个validator通过等同融合路线完整资格成立。

## 文档规定的启动与服务边界

文档将A5/950且上述FP32/BF16 layout可用的cache导向fused plan；A3/非950或不满足融合布局走启动准备的masked byte-copy fallback，其中不合法inner layout仍拒绝。fallback有自己的Torch清理和预编译launcher，未在本kernel模块实现，不因看见ELSE路线描述就宣称所有硬件已运行支持。

每个绑定layout由plan在scratch上准备INT32/INT64 index×gather/scatter四个compiled variant，固定block8192；prepare/seal比较编译器环境/版本，全部层ready后才发布worker。准备失败应阻止发布，不允许先服务再补compile。scratch索引0仅访问一条可抛弃payload，启动同步后再释放，不能拿活cache做warmup并污染状态。

服务调用只用存储的compiled object，选择数和索引值是运行数据，grid可以重绑定；超scheduler.max_num_seqs、未seal、layout变化或意外JIT应在launch前拒绝。aligned contiguous INT32 metadata保持INT32，只有stride/对齐不满足时才规范化；不能每次统一转INT64或扫描os.environ来“优化”variant数。plan不保留request Tensor/stream/live pointer；改变compiler backend或startup环境须重启prepare，不据此推导compiled object可以自行JIT。

这些是文档明确的生命周期要求，不是本次看到完整实现或运行过no-compiler测试。当前模块的_configuration只构造torch/triton版本及指定环境前缀快照，本身不证明服务期是否被调用；验证其调用频率必须沿plan caller，不能把helper存在说成每次copy都扫描。

## 图、Fake与版本

文档的worker-bound计划在Dynamo trace时发出vllm::kda_state_gather/scatter，Fake只处理pointer-free metadata与输出/变更模型；执行由forward context的no_compile_layers解析sealed plan。独立prepare的plan是eager/graph API，不自动成为可导出的layer-context handle，也不是_C_ascend::kda_state_copy ABI替代品。

图重放需保持捕获layout、地址、launch与plan生命周期；改变metadata内容与改变cache物理布局是两件事。shape/布局改变应重新初始化，而不是复用旧compiled handle。纯kernel的dynamic grid、同layout rebound及no-compiler约束仍应在实际launcher层核验。

## 验收方式与未完成范围

文档列CPU路由/全或无发布、NPU精确FP32/BF16、INT32/64、stride/gap/offset、invalid index、图重放及FP16 fallback测试；其中FP16属于fallback，不扩为本_validate_cache_layout融合支持。可选PR17301 native参考缺失只应skip该差分，不能取消独立正确性测试；native库存在也不是本次干净构建证明。

性能比较须纳入生产输出分配、metadata规范化与state dtype转换，交替相同算法/分配边界；分别记录host enqueue、同步wall、Event和graph。Event包含Host提交间隙，不是纯kernel时间，也不能相减不同轮次中位数拼收益。本文没有新吞吐或时延结果。

先证明绑定layout和读写协议，再验证index0、无效/重复gather、唯一scatter、false flag、空选择、page gap、非零storage offset、超过4GiB偏移和图输入变化，最后才评估整模prefill/TP/PP/并发/sleep-wake。plan实现、worker调用、fallback和所有编译后端尚未由这两份来源闭合；保持draft/空平台，不能将文档历史局部测试当Agent或NPU真实性验收。

## 实际plan与Kimi consumer补充取证

本节完整读取固定Main kda_state_copy_plan487行和kimi_kda750行的技术程序/AST投影，补齐前文仅按文档描述的prepare/seal/fallback/worker绑定与模型消费；旧节“plan代码未取证”的限定在本节范围内由实际源码替代。外部Triton/CANN、worker调用初始化的完整时序、Native父模型和真机数值仍未因此闭合，未执行任何JIT或NPU。

### prepare、seal、发布与服务调用

supports_kda_state_copy明确要求NPU、is_950、FP32/BF16、非空rank4、dense正inner payload和不重叠page stride；不满足融合资格则选StridedKDAFallbackPlan，后者仍要求非空NPU rank4/dense inner/non-overlap，不是任意非法layout的保底。cache_signature包含device/dtype/shape/stride与data_ptr模16，不保存完整pointer；相同布局/对齐的不同cache可复用compiled计划，不能据signature相同推实际Tensor是同一存储。

严格prepare要求max_selected为正的内建int，按cache alignment构造scratch，拒绝不对齐allocator输出和JIT pre-run hooks，编译I32/I64×gather/scatter四变体并同步。prepare只使用scratch，不写活state；seal再检查配置快照和hooks，才设sealed。运行_indices检查sealed、cache signature、hooks、同device一维I32/I64与scheduler选择上限；不逐项读取索引值到Host。规范化只在device/dtype或contiguous/16B/stride不满足时另copy，严格路线保持合格I32索引，不总转I64。

_launch只用保存的compiled object和动态grid，空选择直接返回。gather按flags布尔向量规范化、分配packed输出；scatter验证packed shape/device，再规范化dtype/layout。内核仍负责前文valid页范围和false flag归零，唯一scatter目的、cache/packed不重叠和跨流寿命不是这些元数据guard的自动证明。配置快照只在prepare/seal比较，服务期未每次扫描环境；改编译环境必须重建，而不是期待下一copy自动重新JIT。

fallback启动用32字节scratch预编译batch_memcpy(block8192)，依据compiled signature是否还有constexpr决定启动实参；服务期构造INT64源/目的地址表，invalid索引先clamp到安全页但copy size0。gather先zero packed，再copy valid页、最后用flags清不需初态的行；scatter只写valid页，不用flags抑制最终状态。FP16等只走这条byte-copy资格，不能扩为融合kernel dtype。相同目的页多writer仍无仲裁。

initialize_kda_state_copy先将所有_requires层旧plan清None/ready False，要求kv_cache恰为两项并以第1项为recurrent state；按(plan_type,signature)去重准备，所有计划seal完成后才循环发布每层浅副本和layer_name，最后ready True。首个新计划发布前全部prepare/seal已成功，但发布循环没有一般多线程事务屏障；失败后不能继续沿旧ready假象服务。clone的是plan包装，compiled mappings可共享，不共享layer_name。

Dynamo编译时gather/scatter转vllm custom op，经forward_context.no_compile_layers[layer_name]解析已ready计划；独立prepare得到的plan没有自动layer_name绑定，不据eager可用推它可独立导出。Fake检查shape/stride/index设备与输出形状，但不读页索引值、不核最大选择数或真实allocator对齐；scatter声明mutates state，gather不变更state。Fake成功仍不等于prepared服务计划或copy数值正确。

### Kimi投影加载、卷积权重和双流

Kimi混合投影由quant_config.uses_kimi_k3_mixed_kda_projection(prefix.in_proj_qkvgfab)决定：QKV改三路merged投影，BFG另输出[heads,projection,projection]。f_a要求完整形状，f_b接受本地或全局输出轴权重并按TP narrow；两份都加载后以FP32 f_b@f_a组合，再cast写入merged f投影片段。重复reload会在任一callback后用当前另一份重算，完整更新事务需暂停消费，不能把两个loaded flag当全部权重原子替换证明。

卷积packed参数形状为[conv_size,3*local_projection]，原quant_method后处理完成再从conv1d weight view/transpose/cast/contiguous打包；v0.32.0向replace_parameter传prefer_copy=True，其它版本不传。仅修改原weight而跳过后处理会留下旧packed消费视图，图引用和reload都需核对。

混合forward在全局懒建BFG stream上做BFG投影/后处理，主流做QKV量化/矩阵乘；用record_event/wait_event及record_stream保护输入和beta/g1/g2寿命。该stream不按device建字典，多device实例需核对真实创建上下文。QKV仅在特定MXFP4/MXFP8 method、BF16二维输入时显式预量化，后续quant_method.apply接Tensor或量化二元组，不能再无条件量化一次。

### metadata、接受数与持久state必须按分支匹配

模型_forward为eager_break_during_capture边界，metadata缺失时仅将output清零。真实执行按prefix取GDNAttentionMetadata，先wait KV connector/记录compute-start，按num_actual_tokens裁mixed_qkv/g1/g2/beta；mixed路径的beta已FP32 sigmoid，用标志避免再次激活，普通路径在_prepare_beta处理。

卷积cache_indices为二维时只取首列；卷积使用外部fla_npu causal_conv1d_fn/update，不是下文通用Python参考。prefill用run_mode0和has_initial_state；普通decode用update/max_query_len1；spec用update/max_query_len=num_spec+1并传num_accepted_tokens。SSM recurrent仍有自己的完整state_indices和接受数，不能把卷积首列索引套给recurrent。

prefill按prebuilt metadata选择Host或kernel cu_seqlens，keep_meta同步过滤state_indices和has_initial_state；计划未ready明确拒绝。随后state_copy.gather→run_chunk_kda→state_copy.scatter，最终state与同一选择行对应，不把chunk输出当已自动写回pool。recurrent直接把state pool、索引、A_log、dt_bias和lower_bound交run_recurrent_kda，数学与外部callee按各自证据核对。

spec/non-spec可按token indices分流，再index_copy回原顺序。无spec且同时有decode/prefill时才额外按num_decode_tokens拆普通两段；别按请求数猜token边界。有效输出前缀先清零，最终o_norm以g2原位处理，容量尾部清零，再发空列表的connector保存调用；该调用不能单独证明哪些层或哪种缓存已被导出。需要同时验证多步接受、state恢复、conv/SSM索引、mixed权重reload、图编译和真实KV传输，本次均未执行。
