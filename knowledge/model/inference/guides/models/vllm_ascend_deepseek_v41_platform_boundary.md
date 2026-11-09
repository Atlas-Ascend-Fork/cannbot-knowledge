---
type: Guide
title: vLLM Ascend DeepSeek-V4.1-Flash：CED、Engram、部署与 Runner 分界
description: 按 A2/A3 W8A8 参考识别 CED、CSA2和Engram状态，保留教程/支持表对PD的冲突，避免将A2/A3 MRv1要求扩到950。补充QLI候选块/分页stride、Torch
  V3到Native V2、INT8 Q量化与位置过滤，以及编译矩阵/来源验证边界；明确FP16 scale先舍入与INT32索引的FP32位模式排序/不去重语义。
  DeepSeek-V4.1-Flash 的单机、双机共置与普通分离按角色预算：A3 Prefill 16序列/8192批token、Decode 72序列/512批token；A2对应16序列/4096批token与32序列/400批token。核对Engram
  24头共享、Memcache standalone200GB、Mooncake24GB与lookup_rpc_port字符串0，保留服务名冲突及qualification尚无生产性能基线。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-V4.1-Flash.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/deepseek_v41_qli_candidate.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/deepseek_v41_qli_candidate.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/quant_lightning_indexer_v2_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/quantize_indexer_query.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/prepare_indexer_indices.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/DeepSeek-V4.1-Flash.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-31T00:33:50Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- DeepSeek-V4.1-Flash
- DeepSeek-V4.1-Flash-w8a8
- DeepSeek-V4.1-Flash.po
- dsv41
- deepseek-v41
- vLLM Ascend DeepSeek V4.1：CED、Engram 与平台 Runner 分界
---


# vLLM Ascend DeepSeek-V4.1-Flash：CED、Engram、部署与 Runner 分界

## 范围与结构

本卡限定教程A2/A3：V4.1-Flash是原生多模态MoE，40层CED（20 causal encoder+20 decoder）、CSA2、FP4主缓存、SWA bounded replay、Engram和DSpark。它与V4的缓存和执行结构不同，不能只替换模型路径。

## 版本、权重和Runner

教程以0.30.0rc2模型验证为基线，A2/A3脚本显式MRv1；配对vLLM应按该tag记录，不把当前main已验证commit与release tag混成一个环境。W8A8示例包括draft与INT8 Engram，来源称权重将发布，不能推断下载地址现已可用。

A3单节点暴露16 logical devices，示例DP4/TP4；A2与A3容量/节点数不同，以实际设备和可用HBM核对。950平台代码有单独MRv2约束，本卡未凭A2/A3教程确认其支持范围。

## 支持冲突与验证

同提交总表PD/PP等有明确否定或未验证项，教程仍有PD参考且不建议生产。保留冲突，先做共置最小功能验证，不把存在完整脚本当生产支持。核对CED两阶段调度、Engram表格式、所有cache组与图capture，再测文本/图像、reasoning effort和DSpark状态。

## 回退

MRv1/2、CSA2、Engram和FP4缓存必须按平台与版本整体恢复。加载/状态不符先回指定教程基线，不能去掉校验强启功能，也不能将V4缓存快照跨版本复用。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## QLI candidate：位置、候选块与KV向量分开

deepseek_v41_qli_candidate.md与deepseek_v41_qli_candidate.po的27条译文全文对应当前英文。该集成文档声明导入算子来自ops-transformer-qli_candidate.zip、SHA256为771f0c16b9119c676c10cebef713b168f127ff194f3f2f98edcbcd0979c6f966；这是来源记录，本批未取回ZIP并验证其内容。旧DeepSeek-V3.2/PyPTO或PA_BSND LightningIndexer经验不替代此模型的候选ABI。

文档当前A3约定为INT8 Q/K、FP16 head weight与per-head Q/per-token K scale、quant_mode=2，32或64个复制index heads、head_dim128、一个index-K head，compression ratio1/2、causal mask3。position TopK为1–2048；candidate_topk_blocks是64的倍数且在64–2048，candidate_block_size恰为8。候选为INT32[tokens,1,blocks]、-1填充的压缩块ID，不是位置TopK或K向量；一个块覆盖8个压缩位置，块分数取最大位置分数并保留最后可见块。一次forward内共享、下次重置是来源的状态协议，实际共享状态调用链仍需分别核对。

mode1为source，返回未按候选过滤的位置TopK及候选块；mode2用本层Q/weight在source块内重排；mode3普通位置TopK。所读indexer.py完整298行按source优先、其次uses_candidate_filter选mode；不要用两个bool任意组合替代模型层角色配置。source-owned K更新先做投影/归一/RoPE，再写INT8/FP16 scale，owns_k=false或空latent跳过；packed_cache_ops存在时另走设备打包写入/fold和A5 indexer，不将这一支与当前非packed INT8候选路径混同。

## 四槽分页、实际stride与Torch V3到Native V2

来源四槽layer-outermost页在KV后打包index K及FP16 scale，C2为64行视图/131072字节block stride，C1为128行/147712字节。非packed选择路径直接TND Q与PA_BBND K，不靠将全context gather成dense；key_scale.squeeze(-1)保留页stride，metadata传原query边界、压缩K长度和residual，ratio1的residual按Native约定缺省。

模型实际调用torch.ops._C_ascend.npu_quant_lightning_indexer_v3，而不是按文档V2名字改成另一个Torch API。所读torch_binding.cpp的V3 schema将PrivateUse1与Meta均接到qli_v2::QuantLightningIndexerCandidate，完整159行adapter再调用aclnnVllmAscendQuantLightningIndexerV2，并显式转发key.stride(0)/key_dequant_scale.stride(0)。Torch版本名与Native算子版本名在这里是两个层次。

三返回值为索引、空BF16分数tensor（return_value=0）及source候选/非source空候选；模型忽略中间值，source返回新候选，consumer保留输入候选。adapter检查Q/K非空、各shape维正值、topk>0、mode1–3与consumer候选参数存在，然后Meta分支提前返回；不能把这当成全部dtype/layout/blocks/上限的Meta校验或真实CANN成功。模型的空query/max_cache_seq_len=0会提前返回；有预置输出buffer时与新分配的空索引形状不同，不能宣称所有空上下文consumer必在Native处报无source错误。

metadata的注册入口另为npu_quant_lightning_indexer_v2_metadata_npu，所读实现分配1024个INT32，优先按cu_q、used_k、cu_k、used_q、cmp选设备，再调用Native metadata；header中另一个带Meta早退的helper不是此处注册的同名实现。当前所读注册段只显示metadata PrivateUse1，完整全局Meta/dispatch支持仍需其他注册与测试证据，不能用未注册的helper替实际入口，也不据局部阅读断言全局不支持Meta。

## Q量化与索引准备的实际数值/输出契约

quantize_indexer_query.py完整70行将[tokens,heads,128]转contiguous，输出INT8同shape与FP16每head scale。Triton先用FP32 absmax/127，将scale舍入FP16再回FP32，至少2^-24，然后除以该已舍入scale、nearbyint并钳到[-127,127]。零head使用最小正FP16 subnormal的意图不能扩成所有NaN/Inf/溢出输入都有效；该函数没有完整finite/dtype校验。16行scale一组形成32字节边界是源码的写入分组策略，不是实测加速。

prepare_indexer_indices.py完整149行过滤0<=index<(positions+1)//ratio，再按时间顺序排序、invalid填-1。其FP32排序键采用位模式映射，避免直接INT32转FP32丢掉大索引精度；它不去重，lengths统计有效出现次数而非unique位置。仅ratio1/2、INT32二维selected、匹配行数的INT32/64 positions与TopK1–2048；positions与selected同设备等调用方不变量不能由这些局部检查推定全部已验证。

预置indices_output要求[rows,topk]、lengths_output为[rows,1]，均INT32、contiguous且与selected同设备；output与indices_output互斥。rows×max(nextpow2(topk),32)<=524288时融合写lengths，否则额外torch.sum；128KiB排序scratch预算、按8/gcd(topk,8)行对齐32字节写边界来自代码。可复用buffer不代表整图已验收。本批仅静态阅读Python/Triton，无JIT或NPU，也未生成正式Device VV/CV结果。

## 编译矩阵与来源验证各自限定范围

集成文档A2/A3仅编译该TND/PA_BBND INT8 quant2 QLI key1（从4收敛），A5保留16 key及FP8/MXFP8/HiFloat8/MXFP4/INT8的模式1/3/4/5/2。candidate模式、ratio、TopK/长度仍为运行时参数，裁剪不新增A5 candidate支持；默认包列表与显式A5构建分开。当前模型代码另有packed_cache_ops/A5路径，不能把“V4.1非packed调用INT8”当所有A5路径无用的证明。

同文SparseFlashMla按BF16 TND/PA_BBND SWA/CSA收敛为A2/A3六key、A5十二key，排除HCA/独立original-KV/FP16等；HcPre A2/A3 key0与A5 1000/1001保留。Compressor用于V4而V4.1仍用小算子，其四key/架构与coff1/2对应V4 ratio128/4没有因dtype签名收敛而删掉。上述为文档列明的编译合同，不由保留key数推墙钟构建/运行加速；完整各Host/Device分支仍留待逐项生产。

文档报告原始布局A3、40层W8A8、TP4/DP4/EP16、Engram/DSpark关闭，四功能用例各两次temperature0/seed7，包括20032-token检索且输出一致。使用checkpoint encoding.encode_messages(...,thinking_mode="chat")配/v1/completions，没有标准chat template。它不是本次运行、候选vs基线数据集精度比较或新分页布局全部验证；独立算子混请求/Meta/slot布局E2E明确deferred，Graph、64K/128K、多节点与Engram/DSpark组合未验证。INT32 QK/1024、FP16 ReLU/weight*Qscale、FP32 head归约再K scale的量化golden，也不替全模型质量。来源提及的CPU stub模板测试未在本批执行，不能当CANN构建时长或NPU结果。


## Flash 教程全文补充：版本、checkpoint与容量

此节补读 ceac 固定提交的 DeepSeek-V4.1-Flash.md 全1937行与中文 PO 全164条，覆盖部署场景；前文 QLI 合同继续独立适用。英文称主干552B，Prefill激活8B/Decode16B、文本和图像、reasoning effort 1–100；890 bytes/token全局KV与约V4-Flash八分之一持久KV是模型设计声明，不能代替含所有cache组、权重、Engram和临时工作区的设备预算。

教程支持起点是v0.30.0rc1，所述验证基线v0.30.0rc2；配对Native必须从该tag取，不能用本次Main的v0.32.0配对pin或独立Native v0.32.0快照代替。Eco-Tech/DeepSeek-V4.1-Flash-w8a8来源仍称“will be published”，包括DSpark与INT8 Engram，不宣称checkpoint已可下载；量化外链也不是本仓已执行流程。

硬件约定：A3一台8块128GB物理NPU，暴露16个逻辑设备；A2一台8块64GB，暴露8个。逻辑ID数不能当物理卡数/总容量翻倍。Engram有24个heads，A3的16-way张量切分不可直接整除；保留教程给定并行组合。A2使用TP4/TP2对应6/12 heads，仍需核对各rank加载、host共享与每机实际预算。cpu_offload=true、dp_shared_memory=true依赖host IPC或至少320g共享内存；容器示例512g只是请求值，不保证宿主可用。

## 单机、普通PD与双机共置的具体配方

下表按长度 / max-num-seqs / max-num-batched-tokens / gpu-memory-utilization列出；除A5回归外，均为W8A8、MRv1、block128、lazy safetensors与Engram host共享的教程场景。带变量的启动器按调用参数解释，不替它补隐式默认值。K指DSpark num_speculative_tokens。

| 场景 | 全局与本地拓扑 | 长度 / 序列 / 批token / 比例 | 执行与草稿 |
| --- | --- | --- | --- |
| A3单机 | DP4/TP4，一机local DP4 | 150000 / 32 / 8192 / .9 | async、FULL_DECODE_ONLY；没有显式speculative-config，不补K |
| A3普通PD Prefill | DP4/TP4，一机local4 | 1048576 / 16 / 8192 / .9 | target eager、APC on、DSpark K5；未显式draft eager |
| A3普通PD Decode | DP8/TP2，一机local8 | 1048576 / 72 / 512 / .95 | target FULL_DECODE_ONLY、async、draft eager K5、APC off |
| A2普通PD Prefill | DP4/TP4，两机各local2，start0/2 | 1048576 / 16 / 4096 / .9 | target eager、APC on、K5；未显式draft eager |
| A2普通PD Decode | DP8/TP2，两机各local4，start0/4 | 1048576 / 32 / 400 / .95 | target FULL_DECODE_ONLY、async、draft eager K5、APC off |
| A2双机共置 | DP2/TP8，两机各local1；Node1 headless/start1 | 1048576 / 32 / 4096 / .9 | target FULL_DECODE_ONLY、async、draft eager K5、APC on |

A3单机API8900、16逻辑设备，additional启用fused_mc2=1、DSA CP、Flashcomm1、shared expert DP与CPU binding；npugraph_ex=true/static_kernel=false。P/D两机使用HybridConnector：P KV30000，D KV30100，内部拓扑P4×4/D8×2；P API7100–7103，D7100–7107。D另有recompute scheduler与shared-expert overlap。HCCL buffer1024、connect1800是该示例通信设置，不是模型SLO。

A2普通PD是四机总计：P节点0/1各2个TP4副本、API7100–7101；D节点0/1各4个TP2副本、API7100–7103，各host本地设备重新编号。A2P additional未显式fused_mc2，虽然上方文字称“同A3”；记录缺项，不能自行补1。A2 engine-ready timeout360000秒等于100小时，A3的36000秒等于10小时；这些是等待上限，不是启动实测。

通用inline启动器有七个位置参数；TP决定每个worker的设备段，API按local rank递增，local DP缺省跟全局、start缺省0，RPC缺省字符串12345/API缺省9000。它的父进程只join子进程，没有聚合子退出码；全部join不证明全部服务健康。A2双机共置单独用API8000、RPC13399；Node0省略data-parallel-start-rank且先启动，Node1设置headless/start1；不能沿用旧PO“四机DP4/TP8/EP32”。

## 池化：CED要求整块，后端容量与端口分别核对

V4.1的CED hybrid-attention在本教程要求use_layerwise=false；MultiConnector一边用MooncakeHybridConnector进行在线P到D传输，一边用AscendStoreConnector做持久prefix复用。lookup_rpc_port均为字符串0，不拿Store lookup与API/RPC/KV通信端口混用。

A3 Memcache场景沿用P4/TP4、D8/TP2及上表预算，embedded buffer=0GB，每host一套standalone 200GB，device_sdma/LingQu>=1.5、world256/max1024、storage=false。Meta5000、config6000、metrics7000。顺序是Meta→两台standalone→全部D→P→proxy，proxy四个P与八个D端点分别验活；standalone进程在不等于worker注册/真实pool hit。该200GB不是V4-Flash的20GB、Pro的120GB或GLM的640GB。D没有显式consumer_is_to_load，实际默认需按后端合同核对，不补一个来源没写的bool。

A2 Mooncake场景同四机普通PD预算，embedded24GB、master50088、P2PHANDSHAKE、protocol ascend、preferred=false/samenode=true，master ratio .9/.1、lease11000毫秒。不能将lease与HCCL秒数、ASCEND连接/传输超时直接比较而忽略单位。该路径没有standalone Store，也没明确SSD或tenant参数；不要带入其他模型的SSD测量配方。两个Store均非逐层，outer engine_id P0/D1。A2普通PD明确VLLM_HOST_IP、no_proxy和INTRA_ROCE，池化模板部分缺省；核对有效环境再判断，缺省本身不等于通信必失败。

## 源码、译文与服务声明的冲突

164双语条目中144原串匹配、20人工差异、0仅历史上下文；20来源内限定另存。旧PO A2共置四机DP4/TP8改为当前两机DP2/TP8。当前A2脚本served-model-name全部是dsv41，但服务验证文字与对应PO仍称deepseek-v41；先用/v1/models确认实际ID，再发送文本或图像请求，不能把名称不匹配当模型精度错误。健康200/非空输出仅最小服务证据；Prefill节点必须能读取图像URL，reasoning、工具调用还要deepseek_v41 tokenizer/parser与auto tool choice。

来源一处称A2已验证，limitations却写“本次更新未重新验证”；保留其时间范围，不升格新验证。没有本配置生产性能基线，task-level accuracy与生产qualification未完成。并行、max-num-seqs、batch、HBM比例按目标输入/图像/输出/并发联合调节，先保持来源拓扑再做受控对照；验收记录checkpoint、prompt encoder、reasoning、sampling、dataset、DSpark及actual runner，不能拿配置值当优化收益。

## 有界回放与A5回归分开

[SWA恢复与写保护合同](../integration/vllm_ascend_swa_bounded_replay_contract.md)专门处理CachedRequestData.replay_start、窗口重算、调度降级与probe。教程§12声称提供旧vLLM0.30本地prefix回移且默认关闭、KV connector冲突；当前所读patch_swa_bounded_replay.py却仅在Native Scheduler已有_mark_prefix_replay时补V1载荷，旧pin跳过。该差异未被本批证明兼容，不据文档承诺旧镜像可用，也不据单个patch断言安装环境其他模块全部不存在。

A5 real-weight示例是官方raw FP8、deepseek_v4_fp8、MRv2=1、TP1/DP4/EP4、16384 / 1 / 2048、block128、eager、文本专用image0、Engram cpu_offload=true/dp_shared_memory=false、loader16线程/CPU binding=false/API127.0.0.1:8011。它不是A2/A3 W8A8 MRv1配方或950平台验证；移除旧“MRv1/PP未覆盖”译文也不能当全面MRv2/PP支持。

先保存关闭回放的基线、重启服务启用回放，再对比同请求；除成功HTTP和输出一致，还要实际SWA bounded replay is active日志，跨chunk预算应小于窗口。probe只比较text和finish_reason，不检查日志、算术gold或全模型准确率。本批全文/选段静态阅读、译文对照与检索验收均未执行这些服务、权重、NPU或Agent A/B。
