---
type: Guide
title: vLLM Ascend DeepSeek V4：Flash/Pro 权重、混合缓存与拓扑边界
description: 区分 A2/A3 的 ModelSlim 与950原生混合MX权重，按 Flash/Pro 的容量和 Runner 选择拓扑，独立校验主KV与Indexer
  C8。 DeepSeek-V4-Pro 按950的PP2/PCP8与DP32、A3的DP16/TP2及A2的MTP1/DSpark7区分配方；Memcache
  embedded40GB、standalone120GB加UBS IO600GB与Mooncake async_bypass分开，保留PCP逐层池化、设备数量、EP和auto/BF16与FP8差异。
  DeepSeek-V4-Pro 的950混合配置关闭 MC2 并启 shared expert 与 overlap；分离配置的 P 主模型和 draft 走 eager，D
  draft false，PP2 Prefill 分层32,29。A3 使用 BF16 主 KV 与 INT8 Indexer；950 的 KV 端口示例为30000、30200、30100。W4A4C8
  中 Router、compressor、indexer、MTP 保持高精度；Indexer 采用 Hadamard、FP8 与 FP32 scale。池化核对
  PYTHONHASHSEED、jemalloc 和配置路径，force_new_disk 会重建未挂载缓存设备的元数据；1M 输入输出计入总预算。启动器 dp-rank-start
  必填、HTTP 默认8000；v0.30 教程、Main v0.32 与 Native 快照分别追溯，精度 89.90、92.93、97.54 属于来源记录，NPU
  与 Agent A/B 未运行，HTML 映射未证明。 DeepSeek-V4-Flash 覆盖五种单机配方，按 MRv2 PCP 与 MTP/DSpark、单节点和跨主机的
  P/D 角色核对预算。保留2P2D的P150000/D508576、文字draft4/51与脚本1/128、特定测量镜像和额外runtime；Flash池化区分embedded40GB、standalone20GB另50GB
  UBS IO、Mooncake SSD ABI0.3.13与Memcache嵌入式1GB，核对consumer_is_to_load、PC90和retention版本差异。Flash
  的 prefetch 使用 host page cache；TurboQuant4bit 不支持 P/D 分离。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-V4-Flash.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-V4-Pro.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_attn_kv_plan.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/DeepSeek-V4-Pro.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/context_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/DeepSeek-V4-Flash.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T23:57:26Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- DeepSeek-V4
- DeepSeek-V4-Pro
- DeepSeek-V4-Pro-0813
- DeepSeek-V4-Pro-0813-w4a8
- DeepSeek-V4-Pro-w4a8-mtp
- DeepSeek-V4-Pro-0813-w4a4c8
- DeepSeek-V4-Pro.po
- DeepSeek-V4-Flash
- DeepSeek-V4-Flash-w8a8-mtp
- DeepSeek-V4-Flash-0731
- DeepSeek-V4-Flash-0731-w8a8
- DeepSeek-V4-Flash-0731-w4a4c8
- DeepSeek-V4-Flash.po
---

# vLLM Ascend DeepSeek V4：Flash/Pro 权重、混合缓存与拓扑边界

## 模型与版本范围

Flash/Pro采用mHC与压缩混合Attention，不能把V3的单一缓存组配方直接复用。固定教程基线0.30，Flash所列W8A8一节点A2/A3与Pro所列W4A8两A3/四A2节点是特定权重容量参考，不是按active参数估算整模型大小。

## 权重与缓存分开选

A2/A3采用其ModelSlim量化checkpoint；950DT可直接使用相应官方0731/0813混合MX权重，Attention MXFP8、MoE MXFP4存储/不同计算路径，并非一律先转W8A8。W4A4C8还采用混合精度，router/compressor/indexer/MTP等保留高精度，不能全模型uniform INT4。

950主Attention cache的FP8 tile及RoPE BF16与Indexer的Hadamard+FP8+FP32 scales是不同接口；C8是runtime cache选择，不由checkpoint文件名自动确定。主KV默认/override与indexer_kv_dtype分别检查，不能把FP8等同A2/A3的INT8。

## 并行与长上下文

MRv1 enable_dsa_cp与MRv2 PCP字段不是可同时打开的同义开关。MooncakeHybridConnector的特定Flash实现要求PP1×PCP8，PP+PCP需另选受支持connector；不要从Pro V2 PCP+PP场景推导Hybrid也可用。A2某测量路径有max-num-seqs×(1+K)<=256约束，仅适用于其dispatch实现，不能通用于所有A2模型。

Pro最后PP stage还容纳drafter；按实际层分区/峰值调负载。百万context是prompt+output总预算，输入正好1M再加输出会超限。1M低并发与短输入吞吐配置不同，不能拼接一表的最大并发和另一表最大长度。

## 验证重点

先检查全部hybrid组、压缩coverage与draft状态，再增加DSpark、graph、PD和pool。教程PD示例声明仅参考，不直接作为生产认证；特定runtime改动未随文档交付的性能结果不能在main上直接复现。真实精度与传输失败停止条件优先于来源吞吐表。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## 当前缓存计划的实现核对

文档模板与当前runtime需要分开对照。固定实现把引擎config、主KV dtype、compressor slot格式和Attention/metadata统一进DsaAttnKvPlan；950的用户auto请求按BF16处理，FP8物理tile/epilog是另一套接口，PAD slot还受静态图约束。适配新变体时先按[DSV4缓存计划契约](../integration/vllm_ascend_dsv4_kv_plan_contract.md)闭合这些关系，不能把教程的某个默认值直接视为当前所有层的实际布局。本次未据此新增模型运行通过结论。


## Pro 全文与版本：先固定 checkpoint 和 Runner

本节对照固定 ceac 提交 DeepSeek-V4-Pro.md 全文2688行及中文PO138条。页面声明基于v0.30.0；Main的发布pin为v0.32.0，所配原生commit与本地Native v0.32.0快照也不同，不能拼成已经部署通过的软件栈。mHC、Compress-4/Compress-128 Attention和DeepSeekMoE是此模型结构入口，不能以V3的单一KV布局代替完整混合状态。

旧DeepSeek-V4-Pro-w4a8-mtp用于MTP参考；DeepSeek-V4-Pro-0813-w4a8内含DSpark草稿，不另指定draft-model。950DT的原始DeepSeek-V4-Pro-0813使用Attention MXFP8、MoE MXFP4权重及W4A8计算路径，不需要Ascend专属转换或quantization=ascend。950PR/DT的W4A4C8另是本地msmodelslim混精度量化路径，不等于原始权重和全部模块INT4。权重页/外部量化配置未下载执行，实际模型架构、分片、tokenizer和量化元数据仍需逐项确认。

## Pro 混合部署：主机数不等于逻辑设备数

| 平台 | checkpoint与并行 | 总长度 / seq / batch / memory | 投机、缓存与运行条件 |
| --- | --- | --- | --- |
| 950DT | 两主机，各96GB×8；原始0813，DP2/TP1/PCP8，local DP1、EP | 1048576 / 16 / 2048 / .95 | DSpark K5；MRv2、async、hybrid KV、block32、主KV FP8和Indexer FP8、FULL_DECODE_ONLY；CPU binding/shared-expert DP/overlap开，Fused MC2为0 |
| A3 | 两主机；0813-w4a8，DP2/TP16，local1、EP | 135000 / 16 / 4096 / .9 | DSpark K5/draft eager；block32、Indexer INT8、ascend量化、FULL_DECODE_ONLY/FlashComm1；AIV/buffer1024 |
| A2 | 四主机，各64GB×8；w4a8-mtp，DP4/TP8，local1、EP | 135000 / 16 / 4096 / .9 | MTP K1/draft eager；block128、APC显式关闭、Indexer INT8、ascend量化、FULL_DECODE_ONLY/shared DP/FlashComm1；AIV/buffer512 |

A3正文把节点写作128GB×8，但TP16/local1命令需要每节点16个逻辑设备；后面的调优表也把四节点计为64 NPUs。来源没有在页内解释8与16的关系，不能静默改写硬件数量，也不能直接承诺在每节点8设备上执行。先保存物理NPU/die、运行时可见设备和各rank映射，再核算拓扑；不从显存总量猜设备数。

所有mixed例只由Node0提供HTTP API，Node0省略start-rank；远端headless按唯一rank启动。A2的Node1–Node3代码把start-rank示例写成1，按本页说明分别设1、2、3，不能三节点复用rank1。950用PCP8分摊长prefill和o_proj权重，不能只删PCP变成独立TP1部署；旧enable_dsa_cp与MRv2 PCP互斥。A2/A3 mixed命令没有显式hybrid-KV标志，而公共说明又称DeepSeek-V4要求保留hybrid KV，实际默认/解析结果须单独核对。

## Pro 分离部署：实例、stage、DP rank与API分别计数

| 平台/角色 | 物理节点与引擎拓扑 | 总长 / seq / batch / memory | Connector和其他差异 |
| --- | --- | --- | --- |
| 950 P | 四节点形成两个P实例；每实例跨两节点，DP1/TP1/PP2/PCP8 | 1048576 / 16 / 8192 / .94 | MooncakeConnectorV2；分层32,29同时写环境与connector；主模型和draft eager，DSpark K5 |
| 950 D | 四节点组成DP32/TP1 pool，每节点8 local ranks | 1048576 / 32 / 512 / .92 | MooncakeConnectorV2；APC关闭、async、target FULL_DECODE_ONLY/draft eager=false；nested recompute/shared DP/overlap、combine_quant_mode4 |
| A3 P | 两节点形成一个P引擎，DP1/TP2/PP2/PCP8 | 150000 / 16 / 4096 / .92 | V2；主/draft eager、DSpark K5、APC/chunked-prefill、FlashComm1/Fused MC2=1；分层32,29写环境 |
| A3 D | 两节点，DP16/TP2/PCP1，每节点8 local ranks | 150000 / 30 / 180 / .95 | V2；APC关、async、FULL_DECODE_ONLY、nested recompute；spec未显式draft eager字段 |
| A2 P | 四节点DP4/TP8，不启PCP或PP | 150000 / 16 / 4096 / .92 | MooncakeHybridConnector；0813-w4a8、DSpark K7/draft eager、主eager、APC关、FlashComm1/Fused MC2/shared DP |
| A2 D | 四节点DP4/TP8，不启PCP或PP | 150000 / 32 / 256 / .92 | Hybrid；同checkpoint和K7/draft eager、APC关、async、FULL_DECODE_ONLY、nested recompute |

950 P/D使用相同FP8主KV/Indexer、block32，P CCU_SCHED/buffer1024，D buffer2048且模板未显式expansion模式。两个P实例的KV端口分别30000、30200，D pool30100；这些是来源选择，实际完整范围仍按connector实现核验。P每实例只有master API8000，worker加headless；D每节点8000–8007，共32个API；proxy注册两个P master与全部D端点，不能把四P主机误称四P实例。

A3两端默认BF16主KV/Indexer INT8；P/D buffer1024/1800、AIV。A3同样存在设备数量不闭合的问题，TP2×PCP8和local8×TP2均需每节点16个可见设备。环境partition为32,29，connector只显式声明pcp_size而未写pp_layer_partition，不照950自动补成已验证默认。A3还要求PP worker另选kv_port例30200，保留该来源安排并验证实际传输，不自行合并端口。

所有PP节点model/TP/PP/PCP/partition与master地址一致，node-rank0/1唯一，先master再worker。P/D同checkpoint声明的DSpark K；950/A3为5，A2为7，后者不能套mixed MTP1。顶层enforce-eager控制target，spec内字段控制draft，D full graph不代表draft一定走图。共用inline launcher有八个位置参数、每实例TP×PCP设备、local端口递增并汇总子进程退出码；它不是Kimi通用七参数脚本，也没有完整rank边界/设备资源校验。不能因文件同名替换实现。

## Pro 池化：三种平台配置不能互抄

| 平台 | 传输与Store | 服务/内存模式 | 逐层与启动顺序 |
| --- | --- | --- | --- |
| 950DT | MultiConnector组合V2与Store backend=memcache | embedded LocalService，每vLLM进程dram40GB/max2048GB，Device UB用device_urma、UBOE用device_uboe；不另起standalone | P layerwise=true/prefetch3，D省略该字段并按来源称默认非逐层；先meta，P master先worker，其余P/D无先后要求 |
| A3 | MultiConnector组合V2与Memcache Store | vLLM local0GB，四节点各一个standalone init(0)：120GB DRAM另加600GB UBS IO host pool，max1024GB；device_sdma需LingQu>=1.5 | P layerwise=true/prefetch3，D显式false；meta→standalone初始化→D→P→proxy |
| A2 | MultiConnector组合Hybrid与Store backend=mooncake | Mooncake>=0.3.11、P2PHANDSHAKE/protocol ascend/global_segment_size24GB、master50099 | 两端layerwise=false、Store async_bypass；transfer tiered=true/threshold.85；master→P→D→proxy |

950的Meta/config/metrics为5000/6000/8000；A3为5000/6000/7000并设eviction70/60，按实际host避免与API冲突。world_size256是允许的LocalService上限，非NPU数；已连接后更改需重启meta。950 embedded每进程40GB须累计进程数，不能当整节点40GB；A3每节点120GB与额外600GB均占host内存，另留OS/vLLM余量。A3 standalone SSD的force_new_disk=true会重建专用未挂载缓存设备的布局与元数据，使旧缓存无效；本批仅阅读，没有运行或改动磁盘。

A2 master的lease TTL11000、eviction high .9/ratio .1，所有engine用相同master/PYTHONHASHSEED0并显式MOONCAKE_CONFIG_PATH；jemalloc路径须在目标环境核验。P pool命令相较unpooled未显式no-enable-prefix-caching，不假定有效值完全相同。lookup0为本地IPC标识，不能把它当TCP端口或凭它认定无冲突。热请求需分别证明远程Store lookup/get/put/hit与正常P→D传输，排除仅local APC；HTTP200只证明请求入口。

当前完整CP指南明确PCP pooling要求Store use_layerwise=false，但Pro A3/950的P PCP8池模板显式true。这是同提交未消除的组合冲突；保留模型专属示例与通用限制，先核对实际build/后端/调用链，不自动关闭一个选项就称为已验证方案，也不将本卡平台范围扩展为所有组合已运行。

## Pro 混精度与当前KV计划必须分两层核验

W4A4C8模块策略是routed experts W4A4 MXFP4、Attention/shared experts W8A8 MXFP8，router gates、compressor wgate/wkv、indexer与MTP保持高精度；32元素块的微缩放不等于uniform INT4。C8是runtime cache而非checkpoint权重。FAQ描述压缩KV latent每64元素FP8 E4M3/E8M0 scale、RoPE BF16且Q不量化；Indexer Q/K先Hadamard再逐token FP8、FP32 scale，与主KV不同。

当前完整dsa_attn_kv_plan.py按DSV4_COMPRESSED_CACHE能力和引擎cache_config选择：auto/bf16/bfloat16走BF16 plan，FP8路径用另一套Attention/metadata、slot和epilog。FAQ称950主KV默认FP8，不能据此忽略实际auto的BF16分支。950例显式两处fp8时再核对真实page/layout和writer，而不是由文件名C8推断。

FP8 writer代码使用PA_BBND的608B/token物理格式，含64 BF16 RoPE、448 FP8 NoPE、7 BF16 scales及padding18B，quant_mode=fp8_bf16、round_scale=true；FAQ的E8M0逻辑scale描述不能直接当每scale只占1字节。实现与文档对逻辑数值格式、存储dtype和算子参数分别核验，未据此断言算法错误。BF16 PAD scatter保持静态索引、不把-1 clamp到0；详细接口及draft/空平台状态见[DSV4缓存计划](../integration/vllm_ascend_dsv4_kv_plan_contract.md)，本节不以教程平台覆盖提升其硬件验证等级。

## Pro 调优：保持完整场景，不拼接表格极值

A3短序列参考为P DP1/TP2/PP2/PCP8、16 seq/4096 batch，D DP16/TP2/PCP1、30 seq/180 batch。另一个A3约1M参考改两端DP2/TP16/PCP1、两端2 seq，P batch4096/D16，关闭Fused MC2、P保留FlashComm1。它不是在短序列PP2命令上只改max-model-len；来源没有给出把两套配方拼接后运行通过的证据。

950约1M表沿用两个PP2 P实例与DP32 D pool，但表把EP列为Off，5.1/5.2/5.3命令却显式enable-expert-parallel。保留冲突，禁止Agent静默删EP后声称遵从全部来源。文档intro PD仅供参考且不推荐生产，与5.2架构推荐生产措辞也不同；本知识不把示例当生产认证。

maxlen1048576包含prompt和output；增加长度需对所有rank及P/D取最小L×C粗估，不能把启动日志容量乘积当安全并发保证。max-num-seqs×DP与压测并发只是排队负载选择，TTFT/TPOT的initial queue口径按实际benchmark核对。固定checkpoint、Runner、hybrid组、K、graph、输入输出长度、APC与remote hit、host/HBM峰值，先精度和状态，再比较TTFT/吞吐；运行成功或单一开关名不证明性能收益。

## Pro 中文差异与结果边界

138条PO全部逐条中英对照：108条连续原串匹配、30条人工差异，其中3条旧标题/泛称仅作结构上下文。旧launcher起始rank No/default0已改必填，默认HTTP7100改8000，旧run_prefill.sh改PP master/worker两模板；新版还增加950、PCP/混精度及池化内容，不能由PO数量推全英文都有中文翻译或站点HTML已构建一致。

来源GPQA89.90、GSM8K96.21标两A3，GPQA92.93标八950DT，GSM8K97.54标950PR/DT W4A4C8；均为来源报告且含采样/重复平均说明，不是本次NPU结果或不同平台可直接比较的加速证据。本批未导入上游、下载权重、安装镜像/SDK、启动服务/通信、执行NPU/精度/性能或Agent A/B；完整Native/Ascend Device与外部后端闭包仍待继续生产。


## Flash 全文、checkpoint与版本范围

本节对照固定ceac提交的DeepSeek-V4-Flash.md全文3163行和PO126条：104原串匹配、22人工差异，其中1条旧版本/镜像只保留历史上下文。DeepSeek-V4-Flash文档称从0.26功能较完整、基于0.30编写；Main发布pin0.32、本地Native快照和测量镜像是不同身份，不能将这些材料拼成已经部署通过的软件栈。

DeepSeek-V4-Flash-w8a8-mtp是MTP参考权重，DeepSeek-V4-Flash-0731-w8a8用于A3及新A2 DSpark配方；950原始DeepSeek-V4-Flash-0731与另行msmodelslim量化的DeepSeek-V4-Flash-0731-w4a4c8分开。旧PO保留v0.25和特制0731镜像，当前英文安装例为0.30.0rc2及硬件后缀，A2 DSpark另要求nightly-main；不把旧译文镜像当最新推荐。A2单机DSpark命令的路径仍写w8a8-mtp，须检查真实checkpoint的内置草稿结构，不能只改method而假定权重兼容。

## Flash 单机：五种配方不拼接

| 场景 | 并行拓扑 | 总长 / seq / batch / memory | 草稿、缓存与运行条件 |
| --- | --- | --- | --- |
| 950DT DSpark | DP8 / 未显式--tensor-parallel-size / PCP1，一主机96GB×8 | 1048576 / 32 / 16384 / .9 | 原始0731、K5、MRv2、block32、主KV及Indexer FP8、hybrid KV、chunked、prefetch、FULL_DECODE_ONLY、shared DP/overlap；target/draft eager未显式 |
| A3 MTP | DP4 / TP4 / PCP未显式 | 1048576 / 64 / 10240 / .9 | w8a8-mtp、K1/draft eager、block32、Indexer INT8、ascend量化、FULL_DECODE_ONLY、npugraph_ex开/static kernel关、shared overlap |
| A3 DSpark | DP4 / TP1 / PCP4 | 1048576 / 64 / 10240 / .9 | 0731-w8a8、K7/draft eager、其余预算同上；不能把PCP4改回TP4仍称同一草稿方案 |
| A2 MTP | DP1 / TP1 / PCP8，一主机64GB×8 | 133120 / 32 / 8192 / .9 | w8a8-mtp、K1/draft eager、block128、APC关、Indexer INT8、FULL_DECODE_ONLY、shared overlap |
| A2 DSpark | DP1 / TP8 / PCP未显式 | 800000 / 32 / 8192 / .9 | 来源路径仍w8a8-mtp、K7/draft eager、block128、Indexer INT8、hybrid KV、FULL_DECODE_ONLY；与MTP不是仅改K的对照 |

上述A3/A2脚本未显式主KV dtype，不能将Indexer INT8当主KV或从其他平台的FP8命令推默认值。只有950单机例显式导出MRv2；PCP的实际Runner必须按目标build确认，不能由省略变量推同一Runner。A3硬件表写128GB×8，而命令按16个逻辑die使用，物理NPU、die和visible ID分别存档，不能只按商品数量分配设备。

所有命令保留deepseek_v4 tokenizer、tool parser、reasoning parser和auto tool choice。maxlen是输入加输出，batch是每调度步预算，seq是每DP引擎准入；prefetch使用host page cache而非证明NPU已驻留。seq×DP与客户端并发用于解释排队口径，不是安全内存或吞吐保证。block32的实验性4K prefix与block128另核对；通用retention建议为非负block倍数、推荐128×block，即4096或16384，只在相应构建实际消费该设置时适用。

## Flash 普通分离：950单节点与A3/A2多节点

| 场景/角色 | 引擎拓扑与API | 总长 / seq / batch / memory | 草稿与传输 |
| --- | --- | --- | --- |
| 950 P | DP1/TP1/PCP4，设备0–3，API7100 | 1048576 / 16 / 8192 / .9 | DSpark5、target/draft eager，V2 producer30000 |
| 950 D | DP4/TP1/PCP1，设备4–7，API7200–7203 | 1048576 / 56 / 1024 / .9 | DSpark5/draft false、async、APC关、FULL_DECODE_ONLY，V2 consumer30100 |
| A3 MTP P | DP4/TP1/PCP4，一节点16 dies，API7100–7103 | 1048576 / 16 / 8192 / .9 | MTP1、target/draft eager，Hybrid producer30000 |
| A3 MTP D | DP16/TP1，一节点16 dies，API7100–7115 | 1048576 / 60 / 120 / .9 | MTP1/draft eager、APC关、FULL_DECODE_ONLY，Hybrid consumer30100 |
| A3 DSpark P | DP2/TP1/PCP8，一节点16 dies，API7100–7101 | 1048576 / 16 / 16384 / .94 | DSpark5、target/draft eager、MRv2、Fused MC2=1，Hybrid producer30000 |
| A3 DSpark D | DP16/TP1，一节点16 dies，API7100–7115 | 1048576 / 60 / 480 / .95 | DSpark5、draft eager未显式、MRv2、async、APC关、FULL_DECODE_ONLY，Hybrid consumer30100 |
| A2旧MTP P | 四个独立P组各DP8/TP1、local8，各API7100–7107 | 135000 / 16 / 4096 / .9 | MTP1、target/draft eager，Hybrid producer各实例独立KV端口例30000、30100 |
| A2旧MTP D | 一个DP32/TP1组跨四节点，local8，各API7100–7107 | 135000 / 30 / 60 / .9 | MTP1/draft eager、APC关、FULL_DECODE_ONLY，Hybrid consumer30400 |

950两端主KV/Indexer FP8、block32、hybrid KV、MRv2；P HCCL buffer1024/CCU_SCHED、Fused MC2=0/shared DP/overlap，D combine_quant_mode4/shared DP/overlap及旧top-level recompute。P/D同host却分别使用DP RPC12321/12325。D脚本将启动器给的单设备序号加4，不能再从父层加一次偏移；确认五个API健康后启动proxy，不套D2RH的host staging配置。

A3/A2普通分离均显式Indexer INT8，主KV dtype未在命令中指定。A3 MTP P/D buffer2560/1024，DSpark P/D为1800/2400；不能从普通MTP的draft eager推DSpark D也eager。A3 PO旧MTP DP4TP4已改DP4TP1PCP4；DSpark P仍DP2TP1PCP8。两套模板名称相同不代表参数相同。

A2旧MTP的每个P组独立master、rank从0开始；D四节点rank-start为0/8/16/24且同D master。connector声明P DP8/D DP32，不能把四个P组相加后改成一个P DP32。来源intro的4×1P与1×4D是分组标签，设备、进程、API和物理主机分别计数。该段还给1M时另用DP4TP8的粗略说明，不能把135000例只改长度就称已通过1M。

950 inline启动器带--script并向角色脚本传八位置参数，按TP×PCP分配设备、聚合child exitcode并启pipefail；DP1通过删除包含rank和external-LB字符串的整行执行脚本，不是完整任意参数过滤器。A3 inline八参和A2旧七参父进程仅join，不汇总child失败。它们不等同仓内通用CWD模板，也不能互换成Pro PP master/worker启动方式。

## Flash A2 2P2D：测量镜像、非对称长度及脚本冲突

新A2 DSpark参考为四台八设备主机：P external DP2/TP1/PP1/PCP8，每主机一个P引擎，API分别7100/7101；D DP16/TP1、每主机8进程，API各7100–7107。P节点设p_rank0/1、D节点rank_offset0/8，同角色master一致，先补齐各rank再等待就绪。P每实例api-server-count4不表示四份独立算力；EP/MC2可能跨两P组collective，聚合P吞吐须用同一wall-clock窗口。

| 当前完整脚本 | 总长 / seq / batch / memory | 条件 |
| --- | --- | --- |
| A2 2P2D普通 P | 150000 / 16 / 4096 / .96 | DSpark5/draft eager、target eager、block32、APC/chunked、Indexer INT8、Fused MC2=1、hybrid KV、MRv2 |
| A2 2P2D普通 D | 508576 / 128 / 720 / .97 | DSpark1、draft eager未显式、target FULL_DECODE_ONLY、async、APC关、Indexer INT8、MRv2 |
| A2 2P2D池化 P | 150000 / 16 / 8192 / .96 | P仍DSpark5/eager，APC开；同PP1/PCP8并组合Store |
| A2 2P2D池化 D | 508576 / 128 / 720 / .97 | D仍DSpark1/graph参考，改APC开、consumer_is_to_load=true |

这些测量来自dev-26.2.0.day20261021，另外包含UVA dirty tracking、exact request-hash reuse和RoPE capacity运行时改动，文档更新没有交付这些改动。不能据此认定当前Main、rc2或nightly都接受同样参数或重现收益。P maxlen150000、D508576不对称，D较大值不扩展端到端prompt上限；1M需独立验证的长序列部署。

来源文字称“完整脚本使用16K pure-D：D draft4/mns51”，但完整普通D脚本实际是draft1/mns128；池化intro也写4/51而实际两后端D脚本仍1/128。保留两处冲突，记录最终实际生效配置后才选择复现目标，不能将文字中的吞吐结果归到另一组脚本值。通用DSpark“P/D同K且K>=5”与本测量P5/D1、2、4同样分版本保留，不改通用DSpark模型协议来掩盖额外runtime依赖。

该测量分支限制D max-num-seqs×(1+draft)<=256：5/42、4/51、2/85、1/128分别核算，42不是通用最大并发；PP>1与PCP>1同时启用被该实现拒绝，保持PP1×PCP8。工作负载表分别保存：4K-total P4096/APC开、D2/85、proxy4 workers；4K-stable及16K为D4/51；64K/128K为D5/42、proxy1 worker；cold-pd P8192/APC关、D1/128；pc90 P8192/APC开、D1/128。它们不是同一次最优配方。

源客户端普通输入有84-token模板偏移：4180/2048、16468/1024、65620/1024、131156/1024。4K-total N4096/CC1536，4K-stable N8192/CC2304；16K total试验N8192/CC2048与native stable N8192/CC2304分开；64K N3840/CC576；128K total N3920/CC960、stable N2960/CC960；cold full-PD N240/CC60，rate均0。不能把total代替native stable，也不能把client concurrency当每引擎seq。

源16K total试验TTFT mean/P90从21.30/50.32秒降至11.32/42.51秒，output throughput变化-0.54%，TPOT93.6ms，不是20ms SLO通过；本次未复测。该镜像没有读取旧VLLM_PREFIX_CACHE_RETENTION_INTERVAL，须检查实际--prefix-cache-retention-interval；零不代表关闭全部prefix reuse。普通与池化都核对proxy18590、两P/十六D端点和ulimit65536；healthcheck计数本身不证明每个后端和KV数据面正常。

## Flash 池化：950 embedded、A3 standalone、A2两后端

950单节点池化沿用P设备0–3/D4–7、1M与16/56 seq、8192/1024 batch、.9、K5和FP8主/indexer；MultiConnector组合V2与Memcache Store。embedded每vLLM进程40GB、max2048GB、world256，device_urma对应Device UB、UBOE用device_uboe，不另起standalone。P PCP4却明确Store layerwise=true/prefetch3，与当前通用CP非逐层限制不一致；保留该组合冲突，不替它制造运行通过结论。

A3 Flash池化是两主机各16 dies：P DP2TP1PCP8、D DP16TP1，预算沿用A3 DSpark分离表。embedded LocalService0GB，另各启动一个standalone贡献20GB DRAM；max1024GB、world256、device_sdma需LingQu>=1.5。Meta/config/metrics为15000/16000/18000，与Pro或950端口不同。DRAM-only storage=false；可选SSD在standalone中用20GiB DRAM另加50GiB UBS IO、device_count1和专用未挂载无文件系统设备，force_new_disk会重建缓存布局。embedded继续使用0GB配置，不把50GiB当NPU数、额外模型容量或所有rank各分配一份。

A3两端Store whole/nonlayerwise、lookup_rpc_port="0"，实现会按DP rank派生本地IPC；P APC开、D APC关且默认不load/put池。Hybrid负责实时P→D，Store负责复用；顶层kv_load_failure_policy=fail，hybrid不支持recompute load-failure策略。启动meta→两standalone初始化→全D→两P→proxy1999；至少4096-token长prompt先完成save，再在local cache冷的另一个引擎确认put/lookup/hit/get，HTTP200或local APC不足以证明远程池复用。

A2新池化的拓扑、150000/508576和P8192/D720预算沿上表；P/D都APC开、D Store consumer_is_to_load=true。P2PHANDSHAKE/protocol ascend的Mooncake测量要求client/native ABI0.3.13兼容，master50088、tenant a2-flash-pc90、global_segment1GB/local_buffer1GB、preferred_segment=false/same-node=true，SSD开且目录按worker隔离。两项32GiB total/bucket上限不机械相加成已分配64GiB，offload buffer另1GiB；按真实每client/rank与node总量核算。master offload/evict开、force_evict关、high .5/ratio .1、lease11000/TTL120；只有环境变量没有JSON开关和master支持不证明SSD启用。

A2测量Mooncake脚本后置清空ASCEND_GLOBAL_RESOURCE_CONFIG只属于该路径；不能删掉其他部署的传输协议配置。Memcache另是integration recipe：embedded每LocalService1GB、max1024GB/world256/device_rdma RoCE，storage=false，不启SSD，不套A3 device_sdma或separated部署；也不承接Mooncake测量的吞吐。其Meta/config/metrics为15000/16000/18000，PYTHONHASHSEED0；Mooncake模板未显式该值，需核对实际一致身份。P lookup传p_rank、D传global_rank+2并非TCP端口，最终IPC派生与命名空间按实际实现核验。

PC90要预热多个不同prefix组，再发送未见过的suffix；重复完整热prompt近似PC100。requested ratio、P local hit、D external KV hit和SSD实际restore分别留证；正式计时排除warmup，诊断与负载串行、轮间drain18端点，保留完整成功数/token数与native window。不得声称所有请求走SSD，或把某后端结果迁移给另一后端。上述均为来源验收要求，本次没有启动Store、服务、代理或压测。

## Flash 精度、量化、中文与Agent消费边界

W4A4C8的routed FFN用W4A4 MXFP4，Attention/shared FFN用W8A8 MXFP8，router、compressor wgate/wkv、indexer及MTP保持高精度；32元素微缩放不是uniform INT4。950主KV的FP8 C8与权重量化独立，Indexer Q/K Hadamard、逐token FP8与FP32 scale也独立。当前KV plan的auto BF16及FP8物理BF16 scale与FAQ的默认FP8/E8M0逻辑表达差异，按前述实现专卡核对，不以教程替代writer/metadata证据。TurboQuant4bit compress4缓存不是PD支持路径，也不是权重或Indexer量化开关。

源质量表GPQA88.17/GSM8K96.30属于单A3，A3分离DSpark GPQA90.40/SWE Multilingual68.33，950 W4A4C8 GPQA90.40、950 DSpark W4A8C8-MXFP GPQA90.91，均有采样非确定性/重复平均条件；A2 TPS>50/2X也只是源记录，不是本仓硬件或Agent结果。新模型适配先检查checkpoint、Runner、K/Q、Markov反馈、KV/layout及角色状态，再独立比较加载/精度/TTFT/TPOT/吞吐，不用HTTP生成或来源分数替代验收。

PO126的104精确原串不代表所有新增英文配方已有翻译；22差异包括标题/大小写、950同节点范围、A3 MTP PCP迁移、旧主备节点措辞改API/proxy，以及旧VLLM_ASCEND_ENABLE_FUSED_MC2环境变量改additional enable_fused_mc2枚举0/1/2。旧v0.25镜像仅历史上下文，普通参数表的DSA-CP说明与MRv2 PCP不混用。完整模型DSpark适配实现、外部运行时改动、SDK和Device kernel仍待闭合；本批仅数据阅读与知识生产，没有import上游、下载安装模型/镜像、改host/磁盘、运行NPU或Agent A/B，也未证明网页HTML/build映射。
