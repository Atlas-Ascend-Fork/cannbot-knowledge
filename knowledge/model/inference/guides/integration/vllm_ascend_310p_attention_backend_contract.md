---
type: Guide
title: vLLM Ascend 310P Attention接入：phase、Host qLens与压缩mask
description: 沿 AscendAttentionBackend310、AscendAttentionBackendImpl310 和 AscendAttentionMetadataBuilder310 核对phase分派、KV的16打包与block size128/64、query_lens_cpu复用及is_drafting克隆、_EXTRA_CTX.capturing守卫，以及flash/splitfuse的ND与FRACTAL_NZ mask接口、seq_lens归属和父类边界。
aliases:
- AscendAttentionBackend310
- AscendAttentionBackendImpl310
- AscendAttentionMetadataBuilder310
- _fill_query_lens_cpu
- get_query_lens_cpu
- get_compressed_splitfuse_mask
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/attention/attention_v1.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/attention/metadata_builder.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/attention/test_attention_v1_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/attention/test_attention_mask_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/attention/attention_mask.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T07:22:04Z'
updated_at: '2026-11-02T07:22:04Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P Attention接入：phase、Host qLens与压缩mask

## 任务与证据范围

为新模型接入310P命名Attention后端，或排查prefill/decode选错算子、draft步间Host长度被覆盖、捕获期间隐式拷贝、旧NZ mask误传压缩接口时，先同时核对builder和实际consumer。本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整读取专用attention_v1.py 361行、metadata_builder.py 158行、mask 186行及两个UT 302/45行。公共Attention只读241–494、1208–1391，platform只读256–365，utils只读436–528；没有闭合完整父类、所有选择helper或torch_npu设备算子。

Main记录的配对Native pin为544f182d9f0c9bfe8bd7645525951d5e3692a542，本卡未新增Native源码覆盖，也未验证安装环境ABI。全部上游仅作为数据阅读，没有导入或执行UT、模型、NPU、编译、图捕获或性能实验。类名、API符号存在和mock测试不证明完整软件栈/模型/硬件交集，保持draft与空平台；A2、A3、950及其他硬件的整卡适用范围仍未知。

[输入元数据量纲](../../concepts/frameworks/vllm_ascend_input_attention_metadata.md)解释请求数、token数和slot；[MTP proposer输入](vllm_ascend_310p_mtp_proposer_contract.md)负责拒绝后的草稿输入和逐步图；[设备生产任务生命周期](vllm_ascend_device_metadata_lifecycle.md)处理TargetDeviceMetadata的stage/group等待。本卡只补Attention字段怎样被ATB接口消费，不将这些生命周期合并成同一个机制。

## 先记录真正选中的后端与布局

AscendAttentionBackend310返回AscendAttentionBackendImpl310与AscendAttentionMetadataBuilder310。platform选路先检查FA3/FlashAttn专属条件，之后才处理COMPATIBILITY实现族。其compatibility map仅明确登记非MLA、非sparse项，并对其他key默认回落到这个类；返回一个类名不证明未登记的MLA/SFA模型已适配，也不能只从产品名推断最终backend。专属选择helper及模型特有切换仍需各自核对。

get_kv_cache_shape返回`(2, num_blocks, (num_kv_heads*head_size)//16, block_size, 16)`。这里是整除16的打包表达式，没有在getter内对任意heads×head_size向上补齐或验证整除。实际KV dtype、分配、format cast、cache writer与消费者需要一致，不能把shape返回值当作设备布局和数值已正确的证明。

支持的kernel block sizes为[128,64]。get_preferred_block_size在传入default已支持时原样保留，否则返回128；不是所有配置都强制128。源码注释描述避免默认选更小块的性能动机，本次未比较64/128实际性能，更不能因此跳过scheduler、kernel与缓存页大小的一致性检查。

## phase到consumer的分派

| attn_state | 本专用forward_impl的入口 | 需要核对的输入 |
| --- | --- | --- |
| PrefillNoCache | forward_prefill_310 → _flash_attention | 当前Q/K/V、mask、序列长度及query对齐长度 |
| DecodeOnly | forward_paged_attention → _npu_paged_attention | 持久key/value cache、block table、device context_lens |
| ChunkedPrefill、PrefillCacheHit、SpecDecoding | forward_chunked_prefill_310 → splitfuse或splitfuse_v2 | 真实token前缀、Host qLens、device context_lens、mask接口 |
| 其他state | NotImplementedError | 不由此处自动转换或补齐 |

PrefillNoCache先以seq_lens.sum().item()取得真实token数，再用query.shape[0]减它得到delta。delta非零时clone长度并加到最后一个请求，然后调用flash。此处包含Host标量读取，也没有独立校验任意负delta、空长度或非法padding；不要概括为所有prefill都可直接进入GLOBAL捕获，或该调整能修正任意输入不一致。

splitfuse按num_actual_tokens切query和output前缀，返回原output。它不能单独证明尾部已清零、num_actual_tokens总在容量内，或padding输出被下游正确排除。DecodeOnly可能没有本轮key/value，但仍要从实际cache对象读已有KV；只检查key/value为None不足以判断缓存未接线。

## builder建立device长度与Host qLens

专用builder先执行公共build，再针对DecodeOnly、SpecDecoding和ChunkedPrefill，将seq_lens与query_start_loc分别绑定到common metadata的device前缀。这里是视图与地址归属，不是重新计算所有序列长度。PrefillCacheHit虽然在consumer走splitfuse，却不在该builder的显式splitfuse集合中；要单独核对父build和调用方是否已经提供其Host qLens及正确device长度，不能将相近phase名字当作同一准备路径。

SpecDecoding/ChunkedPrefill的query_lens_cpu来自CPU query_start_loc相邻边界差，长度为num_reqs。builder在forward之前附加动态属性，不要求修改上游AscendMetadata定义。get_query_lens_cpu缺属性时返回None；存在时直接返回该值，没有完整检查类型、形状、顺序或新鲜度。CPU请求顺序和device token顺序必须对应，属性存在本身不等于准备完成。

device.type为cpu时不创建预分配Host buffer，_fill_query_lens_cpu直接返回连续差分；其他device则按max_num_seqs分配int32、pin_memory=True的CPU buffer。该构造没有在这里按通用pin-memory可用性做降级；真实运行环境仍需验证分配与容量条件。

非draft调用返回共享buffer的活动前缀view，后续build可以覆盖它。is_drafting=True时先clone该前缀，再把差分写进clone，避免后续草稿步覆盖step0保留的Host长度。不能把非draft view跨任意后续build保留，也不能仅凭clone推断所有metadata字段都已隔离。build_for_drafting调用build时使用fast_build=True、is_drafting=True；传入draft_index未在本覆盖中直接参与qLens计算。

## 两种捕获守卫与eager fallback

paged和splitfuse检查seq_lens.device是否与query.device一致。不一致且torch.npu.is_current_stream_capturing()为真时明确拒绝隐式H2D；非捕获时才搬到query设备并替换metadata引用。应该在捕获前由builder/输入准备绑定正确device buffer，而不是等forward临时分配新地址。

splitfuse缺Host qLens时另检查_EXTRA_CTX.capturing；为真则要求先运行AscendAttentionMetadataBuilder310.build，为假则把query_start_loc取回CPU并求差。这个fallback不等于没有D2H成本。_EXTRA_CTX.capturing与实际NPU stream捕获检查是两个不同条件，本文件没有证明任意调用方式下二者总一致；手工捕获或自定义wrapper必须核对两边状态，不能只改一个标志绕过检查。

builder提供了某些持久device view，不代表完整forward没有Host工作。未压缩splitfuse mask构造也会取query边界和context长度回CPU；首次mask缓存分配与格式转换还需另行安排。先核对具体分支，再判断是否可以捕获。

## flash与splitfuse的压缩mask不能互换

is_compressed_mask_supported要求torch_npu同时有_npu_flash_attention_v3和_npu_paged_attention_splitfuse_v2。它是联合API符号探测，没有在这里核验具体硬件、版本组合、shape、dtype和设备运行结果；缺任一符号走旧接口。builder和impl还分别保存相关判断，环境或对象切换时要确认实际采用的分支。

| 路径 | 接口与mask约定 | 局部边界 |
| --- | --- | --- |
| 旧flash | _npu_flash_attention，消费metadata.attn_mask | 显式mask的dtype/NZ表示按构造侧核对 |
| 压缩flash | _npu_flash_attention_v3，mask_type=3 | 不使用splitfuse的mask_type=5替换 |
| 旧splitfuse | _npu_paged_attention_splitfuse，按位置选mask行后转FRACTAL_NZ | qLens与context长度参与CPU规划及格式转换 |
| 压缩splitfuse | _npu_paged_attention_splitfuse_v2，固定ND[2048,2048] FP16、上三角-10000，mask_type=5 | forward重新取得该专用mask，避免直接沿用父build的NZ mask |

get_attention_mask在压缩能力存在时也使用2048的逻辑mask，但causal路径经nd_to_nz_2d与format cast；这与压缩splitfuse明确要求的ND矩阵不同。不能因它们都写2048或“压缩”就交换对象。非pooling入口仍返回causal mask，pooling才按causal选择；全可见mask与标准FIA的None区别复用[双向mask诊断](../../runbooks/precision/vllm_ascend_noncausal_mask_contract.md)，不在此重新定义。

未压缩get_splitfuse_mask按每请求context_len-query_len到context_len的行位置选择全局causal矩阵，再用nd_to_nz_spec对行列做16对齐。所读utils片段使用普通pad/reshape/transpose或显式零buffer及permute，本次未执行其设备结果，也没有闭合ATB内部计算。

缓存寿命需额外核对：legacy chunked_prefill_attn_mask在类级首次创建，max_seqlen却由各实例构造更新，未在该缓存入口全面按新maxlen/device失效；压缩splitfuse类缓存检查device变化，尺寸则固定2048。实例causal/noncausal缓存也不是任意dtype、长度变化都会重建的通用缓存。跨实例、不同设备或长度切换不能仅凭缓存非None认定适配完成。

## 保留父forward与历史版本边界

该专用impl继承父forward。已读父片段要求提供output，拒绝fused output quantization，并要求layer的K/V scale满足相应断言；metadata为None时填零返回。父forward还负责初始化cache引用、在本轮有K/V时选择cache写入，以及pooling非causal的encoder入口。专用forward_impl分派正确，不代表这些父接口、量化与cache producer合同可以省略。

父reshape_and_cache对普通decoder裁真实K/V/slot前缀，共享KV层跳过本层写入；PCP还有单独gather与元数据恢复路径。本卡只阅读明示片段，未由此证明310P支持任意CLA、PCP、量化或其他cache布局。需要相应模型和实际consumer证据。

[历史310P bringup约束](../../optimizations/anti_patterns/ascend_310p_bringup_unusable_ops_and_nz_layout.md)来自PR5776；[硬件能力资料](../../concepts/frameworks/vllm_ascend_hardware_profiles.md)另保留旧310p.po的无压缩mask说明。当前固定Main已经有PrefillCacheHit/SpecDecoding和压缩接口分支，应按各自版本读取；新增源码分支不证明旧报错组合已修复，也不证明硬件图模式或整模型已可用。

## 接入产物、验证与停止条件

UT302定义backend/builder选择、KV shape、mock flash/paged/splitfuse/SpecDecoding路由，以及CPU qLens差分、非draft别名、draft clone和drafting调用参数。UT45定义旧mask的NZ形状与局部-inf、splitfuse选择形状。它们未由本次执行，mock算子被调用不能替代真实设备数值、压缩mask、捕获或性能证明。

Agent应记录最终backend/builder/impl、phase、真实与padded token数、请求顺序、query边界、Host qLens对象/地址、device seq_lens、mask形状/dtype/格式/分支、cache布局及kernel block size。先覆盖普通prefill、decode、cache-hit、混batch、MTP、同大小重排、连续build、跨draft步和缓存实例切换，再对照可信eager与目标图路径的输出。

缺Host qLens、发生捕获内Host读取、共享view被覆盖、mask接口或长度不一致时，停止性能结论，恢复已验证的backend与执行配置。分别量CPU差分和mask规划、D2H/H2D、ATB算子与端到端有效token时延；源码中的少拷贝或默认block size动机不代替实测收益。
