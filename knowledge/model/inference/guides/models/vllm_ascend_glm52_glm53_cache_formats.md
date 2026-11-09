---
type: Guide
title: vLLM Ascend GLM-5.2、GLM-5.3：量化、TurboQuant 与验证边界
description: 区分GLM-5.2、GLM-5.3在A2/A3与950DT的量化、TurboQuant和长度预算，保留950DT BF16、Chunked
  Prefill及Piecewise未验证项，避免跨平台复用结果。完整对照普通PD、MemCache、1M DCP与PP4拓扑，核对local DP rank、CPP异步、图模式及MC2有效配置，保留parser与精度分母边界。
  按950配方分别核对 Indexer Q/K 的 Hadamard 旋转、per-token FP8 与 FP32 scales，以及 routed 专家 MXFP4、attention
  和 dense FFN 的 MXFP8、router 高精度回退。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/GLM5.2.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/5fa10c3799e249627112ead02c8414988d85ddcc/docs/source/tutorials/models/GLM5.2.md
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/engine/arg_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/GLM5.3.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/GLM5.2.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/base_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/scheduler_profiling_chunk.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/docs/source/tutorials/models/GLM5.2.md
  role: supporting
- resource: https://docs.vllm.ai/projects/ascend/zh-cn/latest/tutorials/models/GLM5.2.html
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-11-04T03:05:50Z'
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
- GLM-5.2
- GLM-5.3
- GLM5.2.md
- GLM5.2.po
- GLM-5.2-w8a8c8
- GLM-5.3-w8a8c8
- GLM-5.3-W4A4C8-mxfp4
---

# vLLM Ascend GLM-5.2、GLM-5.3：量化、TurboQuant 与验证边界

## 模型与版本

GLM-5.2/5.3共享基座但post-training不同，部署命令可复用部分结构，checkpoint、精度和性能结果不可互借。来源0.30维护分支的专属修复须在实际build内确认，未冻结的模型工具YAML不作事实源。

## 平台量化与KV

A3/A2 W8A8C8与950 MXFP8/MXFP4权重不可互换，保持repo大小写、tokenizer、quant描述和runtime KV一致。950 C8主KV和LI cache分别选fp8；主latent tile、RoPE高精度、Indexer Hadamard/per-token scale与回退层必须分别记录，不能按“C8”统一推INT8。

TurboQuant SFA路径适用MRv1、A2/A3 BF16激活，kv-cache-dtype=turboquant_4bit_nc，禁Xlite，不可与enable_sparse_sfa_c8或PCP/DCP同开。PD两侧use_ascend_direct=false且同格式；不适用于950 FP8例子或GLM-5.3-Flash。因此不能把TQ与DCP百万context参考直接拼接。

## 拓扑和容量

普通PD、pooled PD、1M PD是不同拓扑。独立两个P实例不等于一个DP2组；global/local DP与每engine seq/token预算分开计算。950 1M DCP8 Decode与A3 DCP4/Prefill PP2+DCP16各有场景依据。输出预留在总context内，不能由一请求1M验证推大并发容量。

## 验证与回退

若使用VLLM_USE_FASTOKENS先确认同环境安装该依赖。每模型独立测质量，thinking/parser语义单独核对，GLM-5.3不可按无thinking假设解析。先检查真实KV格式/scale再测pool hit与transfer，回退整个P/D格式和namespace，不能只改一端。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## 总表按平台保留的未验证项

GLM-5.2/5.3的950DT行：BF16、Chunked Prefill、Piecewise为🟡，APC、投机、异步调度、TP/PP/EP/DP、PD、Fullgraph为✅；5.2长度🟡，5.3长度1M。A2/A3行列BF16/Chunked/Piecewise✅，5.2长度200k，5.3为A2 135k/A3 1M。以上均为上游单项声明；950 MX权重教程不是950 BF16已验证的证据，A3百万上下文也不能替代A2容量。


## 后续教程修订对启动计划的影响

文档提交`5fa10c3799e249627112ead02c8414988d85ddcc`相对本卡原ceac基线澄清以下条件，不表示整份数千行教程或新增源码已完成穷尽验证。

- A3单节点W8A8C8的TP16/DP1、DSA context parallelism与FlashComm1示例必须带--enable-expert-parallel；该示例limits为max_num_seqs=12、batched tokens=8192、总context=32768。不能把它与多节点colocated汇总表的TP/调度预算互换。
- 对文档DP8/local DP4的多节点布局，API node0省略--data-parallel-start-rank以保留internal DP load balancing，headless node1显式4。vLLM v0.32.0的EngineArgs在local size已设、非headless且start rank非None时推导hybrid LB；显式0与省略虽都可能得到rank0，却不等价。这个条件不能泛化成所有拓扑都必须省略或禁止hybrid LB。
- 多节点同组选择硬件镜像与digest，A5/950DT用-a5、A3用-a3、A2无后缀；版本模板必须实际展开。PD代理在容器内按绝对checkout路径启动；请求model要匹配示例served-model-name=glm，不能继续用glm5。
- 950DT W4A4C8的记录使用历史本地镜像，不能凭旧日期或HTTP 200推导某公开镜像标签已验证所有精度/长度。GLM-5.2与5.3分别验收，保留原950未验证项。

先校验最终解析的DP rank、LB模式、角色预算和请求模型名，再开始调优；回退到完整旧镜像/参数组。以上改动仅来自固定文档diff与已读EngineArgs分支，未在NPU或多节点运行。


## GLM5.3 独立旧译文与合并教程的读取边界

GLM5.3.po 的149条消息完整保留了旧独立教程，没有同路径当前英文 GLM5.3.md；替代主题在 GLM5.2.md。孤儿状态不等于GLM-5.3停更。本次对合并英文只新增核对1–56、191–236、4682–4882行（模型/权重、参数、验收、调优表与FAQ），其余大型安装/角色脚本未在本批逐行闭合；旧PO中的角色描述不能冒充当前英文脚本已验证。

旧页的v0.23多节点描述、0.30 RC的PD描述以及header时间不组成同一兼容栈。旧DP8/local4/start0、4适用于两节点布局，不能与“四台A2、headless节点1–3”一句直接拼接。当前合并文档要求选定0.30维护build并包含场景修复，GLM-5.2与5.3共享部分结构不转移checkpoint、post-training、parser或精度结果。

| 历史PO场景 | 旧资料中的拓扑与关键预算 | 与当前合并说明的区别 |
| --- | --- | --- |
| A3 PP2 PD | P0/P1承载一个TP16/PP2引擎，78层分42/36，仅P0有API；D0/D1承载DP16/TP2，分别rank0–7/8–15，端口8000–8007各8个。P seq64/batch16384/MTP1，D seq64/batch256/MTP5。 | 汇总表仍给A3 198k的该类预算，但表不是全部脚本/依赖闭合；PP stage不当额外P API。 |
| 旧Memcache pooling | 与上述PP2角色使用MultiConnector：MooncakeV2传输加AscendStore非layerwise Memcache；需要独立SDK/配置/元数据服务，参数不会启动这些服务。 | ordinary D KV base30100与pool30200分开；lookup_rpc_port字符串0在该IPC设计含rank，不解释成通用TCP随机端口。共享池load需排除仅本地APC命中。 |
| 旧1M DCP | P: DP2/TP16/DCP16/PP1，两个P API；D: DP4/TP8/DCP8/PP1，四个D API；PCP1/interleave128，V1 producer/consumer，无Memcache。P batch8192/seq64，D batch192/seq32。 | 当前A3汇总为P DP1/TP16/PP2/DCP16、batch16384/seq64；D DP8/TP4/PP1/DCP4、batch48/seq8。不能把旧6API/PP1、旧端口与新表合成命令。 |

P/D同格式、独立engine身份、组内rank/主地址、代理注册API与headless stage分别验证。旧PP2 P端单API加16个D API不等于17个独立模型副本；旧1M的6API不是PP2部署的API数。配置端口开放、服务模型目录和非空短文本只关闭各自阶段，不能证明长序列分布式forward、传输或shared-pool复用。

## 当前合并教程的格式与结果归属

950普通PD的两个独立TP8/PP2 P实例跨四台P主机，不能写作一个DP2组；D为一个跨D0/D1的DP16/TP1组。不同pool/1M行有自己的节点及角色预算。950 1M表中P的max-model-len原值1046576，而D为1048576，应按实际两端共同可接纳长度与输出预留核验，不能静默改成同值或由表保证一请求跑满。

W4A4C8不是全模型统一INT4：GLM-5.2来源FAQ列routed专家W4A4 MXFP4，部分attention/dense FFN用W8A8 MXFP8，router及kv_b_proj、wk、weights_proj保高精度；QuaRot/FlexSmoothQuant与32元素microscale是该配方解释，不替代固定外部工具和模型专属YAML。950 attention C8、LI cache C8与fallback分别验收，不借“C8”统一INT8。

当前function calling示例明确 tool-call-parser=glm47、reasoning-parser=glm47、enable-auto-tool-choice；旧PO没有完整块，不能从旧缺失重建。GLM-5.3保持thinking，禁用仍会生成reasoning，源文比较Native的content与Ascend的reasoning字段；这是该版本/模型语义，不推广GLM-5.3-Flash。此前950历史验证用glm45，当前glm47调整没有对应NPU复验，保留这个缺口。

| 来源结果 | 能证明的范围 | 不可转移的结论 |
| --- | --- | --- |
| GLM-5.3 W8A8C8 GPQA Diamond | A3 PD 91.92、A2 PD 89.39的来源报告。 | 非本仓结果，不是1M精度、所有parser或GLM-5.2质量。 |
| 950 W4A4C8本地checkpoint记录 | 历史TP8/DP1/EP eager、配置135000，两个模型均通过启动/短请求；GLM-5.3 GSM8K1279/1319=96.97%，包含10请求错误。 | 没跑真实135K输入/工具/性能；local权重未匹配公开revision或逐分片哈希，glm47更新也未复验；5.2无dataset分数。 |

GSM8K口径为zero-shot chat、content数值exact match、temperature0、seed42、max_tokens8192、concurrency20、timeout900秒、无重试；1309正常加10错误为完整分母，不删除错误重算。性能表只给A3工作负载：16K/1或128K/1 prefill零前缀命中；16K/1K、128K/1K decode百分百命中；完整PD零命中；1M/1K单并发；pool128K/1K的90%/32前缀，及40–80K/2.5K重复前缀。它没有实际TTFT/TPOT/TPS，缓存命中统计定义仍需实测闭合，不能把工作负载表称性能收益。

1M是输入加输出总限，seq caps不保证相同数量百万请求。TurboQuant禁止PCP/DCP的边界继续适用，不能把它与旧/新1M DCP合并；pooling、普通PD与1M连接器也分别验收。先冻结build、checkpoint、图模式、KV格式和角色拓扑，完成短/长正确性与跨角色传输，再开展目标SLO对照；本次未运行SDK、服务、NPU、量化工具或bench。


## 合并教程全文：按硬件和角色选择完整场景

本节完整对照 ceac 提交的 GLM5.2.md 英文4882行及 GLM5.2.po 318条消息；前文“本批只读选段”描述历史批次，不再表示本节的阅读范围。英文仍要求包含目标修复的0.30维护构建，共享命令默认GLM-5.3，Main发布pin为0.32.0。Native源码快照5df与Main配对Native提交544f亦不同；不能把它们合成为已验证的软件栈。旧独立GLM5.3.po另有历史边界，仍不代替当前命令。

先选硬件、checkpoint、普通PD/池化/1M，再计算每角色组的DP、TP、PP、DCP及local ranks。下表保留本节ceac来源的配置输入，7d9e的950DT单机图执行差异见文末，非本次容量或性能结果；长度均包括输入和输出，seq/batch是每engine调度预算，不是proxy全局并发保证。A3按64GB×16逻辑设备，A2按64GB×8，950DT按96GB×8；不能按旧译文128GB×8改变设备编号。

| 场景与角色 | 全局DP / TP / PP / DCP | max-model-len | seq / batch / MTP K | 角色组和API |
| --- | --- | --- | --- | --- |
| 950DT单机W4A4C8 | 1 / 8 / 1 / 1 | 135000 | 20 / 16384 / 未显式投机 | 一主机，一个API；eager、FP8两种KV、APC开 |
| A3单机缩短上下文 | 1 / 16 / 1 / 1 | 32768 | 12 / 8192 / 3 | 一主机，FULL_DECODE_ONLY、int8两种KV |
| 950DT多机共置 | 1 / 8 / 2 / 1 | 135000 | 500 / 16384 / 5 | 两主机，一个API8000，另一PP stage headless；eager |
| A3多机共置 | 8 / 4 / 1 / 1 | 202752 | 6 / 4096 / 3 | 两主机local4，master API、远端headless；起始rank存在下述LB差异 |
| A2多机共置 | 4 / 8 / 1 / 1 | 135000 | 128 / 8192 / 3 | 四主机local1，API节点省略start-rank，worker显式1–3 |
| 950DT普通PD P，每独立实例 | 1 / 8 / 2 / 1 | 135000 | 500 / 16384 / 1 | 两个独立P实例各跨两主机，P0/P1与P2/P3；API仅P0/P2 |
| 950DT普通PD D | 16 / 1 / 1 / 1 | 135000 | 10 / 60 / 5 | 两主机local8，start0/8，HTTP8000–8007各八个 |
| A3普通或池化198k P | 1 / 16 / 2 / 1 | 200000 | 64 / 16384 / 1 | 两主机分层42,36；仅P0 API8000 |
| A3普通或池化198k D | 16 / 2 / 1 / 1 | 200000 | 64 / 256 / 5 | 两主机local8，start0/8，HTTP8000–8007 |
| A2普通PD P | 1 / 8 / 4 / 1 | 200000 | 64 / 8192 / 1 | 四主机分层20,20,20,18；仅P0 API8077 |
| A2普通PD D | 16 / 2 / 1 / 1 | 200000 | 32 / 256 / 3 | 四主机local4，start0/4/8/12，HTTP10010–10013 |
| 950DT池化P，W4A4C8 MXFP4 | 1 / 8 / 2 / 1 | 1048576 | 8 / 4096 / 1 | 两主机分层42,36；仅P0 API8000 |
| 950DT池化D | 16 / 2 / 1 / 1 | 1048576 | 10 / 60 / 5 | 四主机local4，start0/4/8/12，HTTP8000–8003 |
| A2池化P | 1 / 8 / 4 / 1 | 200000 | 64 / 8192 / 1 | 四主机同一P实例、仅P0 API8000；不是旧双PP2实例 |
| A2池化D | 16 / 2 / 1 / 1 | 200000 | 64 / 256 / 5 | 四主机local4，HTTP8000–8003，D RPC12990 |
| 950DT 1M P | 2 / 8 / 1 / 1 | 1046576 | 64 / 32768 / 1 | 两主机各一API8000，KVPP开、PCP1、interleave128 |
| 950DT 1M D | 2 / 8 / 1 / 8 | 1048576 | 32 / 192 / 5 | 两主机各一API8000，PCP1、interleave128 |
| A3 1M P | 1 / 16 / 2 / 16 | 1048576 | 64 / 16384 / 1 | 两主机分层42,36；仅P0 API8077，P1 headless |
| A3 1M D | 8 / 4 / 1 / 4 | 1048576 | 8 / 48 / 5 | 两主机local4，start0/4，HTTP8000–8003 |

950普通PD为六角色主机48设备，池化也是六主机48设备但P/D分配不同；950 1M为四主机32设备。A3普通/池化/1M各四主机64设备；A2普通/池化各八主机64设备。DCP复用TP ranks，不能再乘DCP算物理设备。950 1M P与D长度差2000，按较小的1046576保留输出预算；不能静默补成两端1048576。A3 198k是工作负载名，总长200000，与共置202752分别保留。

## KV传输、代理与池化的场景映射

| 场景 | 连接器与base KV ports（P / D） | 代理路由 |
| --- | --- | --- |
| 950普通PD | MooncakeConnectorV1，30000 / 30300，显式direct=true | 独立host:8000，两个P API加16个D API；不注册P1/P3 |
| A3普通198k | MooncakeConnectorV2，30000 / 30100，direct=true | 独立host:8000，一个P API加16个D API |
| A2普通PD | MooncakeConnectorV2，30000 / 30100，direct=true | proxy8000可同P0共置，P API8077加16个D API10010–10013 |
| 950池化 | MultiConnector内V2加AscendStoreConnector，30000 / 30300；Store use_layerwise=true | 独立host:8000，一个P API加16个D API；Mooncake direct未显式设置 |
| A3池化198k | MultiConnector内V2 direct=true加Store use_layerwise=false，30000 / 30200 | 独立host:8000，一个P API加16个D API |
| A2池化 | MultiConnector内V2 direct=true加Store use_layerwise=false，30000 / 30200 | proxy1999可同P0共置，仅P0:8000加16个D API |
| 950 1M | V2 direct=true，30000 / 30200，无MemCache | 独立host:8000，2P加2D API；P RPC16500，D16600 |
| A3 1M | V2 direct=true，30000 / 30100，无MemCache | 独立host:8000，P0:8077加8个D API；D RPC16600 |

两端JSON必须描述同一实际P/D拓扑和PP分层，engine_id各自核对；HTTP端口、DP RPC、PP master与KV派生端口不是同一类资源。A3普通V2示例按N=DP×PP×PCP×TP预留worker B至B+N−1、scheduler B+N至B+N+DP−1，P为30000–30032、D为30100–30147，额外transfer RPC还要核对；不将此公式直接搬到V1。950池化只有Store明确layerwise=true，不据此补出Mooncake的direct或传输layerwise默认值。

指南内嵌launch_online_dp.py按local索引分配本机设备与HTTP递增端口，global rank=start+local；D1 start8/4仍从本机设备0及HTTP8000开始。A3内嵌版限制16设备，950/A2限制8；七位置参数依次为设备、API port、global DP、global rank、master IP、RPC、TP。它们有参数边界检查、RPC转字符串及子进程exitcode传播，与仓库另一个同名通用launcher不同；即使launcher退出0，也仍须检查全部API和headless PP伙伴加入。

所有场景served-model-name是glm；A2普通文字残留glm5而实际请求JSON也是glm，不创造别名。第6节通用“PD proxy8000”不覆盖A2池化实际1999。curl应指向所选proxy/API，/v1/models逐端点通过后仍要验证真实P→D传输。HTTP403先区分业务IP被环境HTTP proxy拦截；--noproxy检查只是网络诊断，不能证明模型计算或KV正确。

## MemCache后端与就绪证据

先准备目标版本的memfabric-hybrid、memcache-hybrid、MetaService、每节点MMC_LOCAL_CONFIG_PATH及实际vLLM Python可见的库。MultiConnector参数不会启动后端，所有P/D访问同一池；PYTHONHASHSEED=0、ACL_OP_INIT_MODE=1及MEMCACHE_ROOT是来源池化环境条件，不代表已在本机配置。A3/A2非layerwise、950 layerwise分别按目标后端依赖验收，详见[KV Pool后端](../deployment/vllm_ascend_kv_pool_backends.md)。

A2配置MetaService TCP5000、config store6000、metrics HTTP8009；world_size=256是LocalService上限而非64个NPU或vLLM DP大小。device_rdma下dram.size=40GB按每LocalService，八个合320GB/完整A2节点，不与HBM、Docker shm或其他节点总预算混算。来源要求八宿主机vm.nr_hugepages=200000并回读；这里没有执行sysctl，也不能仅按页数推实际字节容量和成功分配。

D侧应看到All DP MemCache initializations completed全组屏障完成；P DP1跳过该DP屏障，仍需核对每个P后端初始化与全部PP伙伴。A2当前P1–P3加入同一PP4实例，旧“每实例两个PP stages”句不适用。lookup_rpc_port字符串0在Store含DP rank的本地IPC命名中使用，不是TCP零端口或空闲端口分配器。

热池验收使用超过一个cache block的prompt及重复前缀，检查saves、lookups、loads、hit metrics；确认本地engine没有该前缀时仍发生共享池load。只见HTTP成功或local APC hit不足以证明池复用。A3普通D关闭APC、池化D开启APC，不能原样复用普通D的--no-enable-prefix-caching；A2池化两端也开启，950池化两端开启。90%/32前缀等只定义工作负载，不证明实际命中率。

## 源码与教程冲突：先核对有效配置

- 本地DP rank：当前Main base_worker.py 133–136仍先取data_parallel_rank_local，None立即抛Mooncake worker requires a local DP rank，之后才取local size；教程展示的条件fix尚不能视为已在此Main实现。fix只在data_parallel_size_local==1推0，多local ranks仍必须显式；实际部署先查每个P节点的有效安装包/构建，不能删断言或直接修改所读上游快照。
- A3共置DP8/local4：Main教程仍API显式start-rank0、远端headless；前述5fa补丁已把API改省略。已读Native EngineArgs在local size给定、非headless且start-rank非None时推hybrid；local1还会转external，而local==global又会关闭hybrid。因此显式0与省略不等价，也不泛化成任何模式都禁止start-rank。0.30实际build仍须独立核对，不能用5df静态分支假称旧build运行失败。
- A3普通PD的D命令显式enable_npugraph_ex=true、enable_static_kernel=true，后面说明却写禁用，中文PO241还写使用；保留输入与说明冲突。Main AscendCompilationConfig默认static/Super关闭，但显式static=true且未给enable_super_kernel时后者继承true；A3 profile含NPUGRAPH_EX，不能解释成硬件会无条件把三者关掉。最终仍受平台/backend回写、图模式、编译与TP布局限制；只测static时需显式Super=false。A3池化和1M D也有static=true/Super省略，950普通/池化D则显式static=false/Super=false，见[图模式验收](../optimization/vllm_ascend_graph_mode_selection.md)。
- MC2输入2在Main先探cann_ops_transformer并归一为1，派生校验按1先禁shared-expert overlap，随后可能因模型配置不支持再降MC2为0；不假称两个显式优化均生效，也不由后续降级自动恢复overlap。A3 P模式2、950普通P模式2与其他MC2=1场景均须记录最终值，不能把维护分支配方当当前Main所有模型保证。
- A2池化P明确MRv1、--no-async-scheduling、scheduler_config.profiling_chunk_config.enabled=true。教程仍说CPP加async被拒绝，但当前Main platform.py会根据async标志选择ProfilingChunkAsyncScheduler或ProfilingChunkScheduler，且当前类确实声明async变体。这是维护配方与Main接线差异，既不改原配方为async，也不把旧拒绝推广当前全部构建；选段不证明完整CPP异步正确性。嵌套Scheduler字段、legacy回退与缓存机制见[配置生效链](../integration/vllm_ascend_configuration_resolution.md)。

A2普通P与池化P的实际拓扑均DP1/PP4/TP8；当前文字仍声称池化分区更宽，与当前表和命令不一致。普通A2说明残留“两端K3”，实际P K1、D K3；池化为P K1、D K5。950普通intro写“两端DP16TP1”，实际两端JSON均为P DP1PP2TP8、D DP16TP1。Agent须保留这些冲突，不拼接旧译文造一套不存在的启动方案。

## 新模型适配与调优的验证顺序

固定build、镜像digest、精确checkpoint与分片哈希、tokenizer、量化元数据、图模式和真实拓扑；所有节点使用同一兼容栈。先最小输入验证加载和数值，再验证各PP伙伴、全部D rank、状态推进及跨P/D格式/传输。按真实长度分布逐步增加context和并发，输出预算从总长度扣除；最后再对照APC、池化、DCP、KVPP、投机、图和MC2的目标SLO。A3 HCCS-only hccs:device与resource1.2不能直接用于不匹配网络；A2普通P来源unset HCCL_IF_IP、D显式本机IP亦不能合成全局网络规则。

950 1M是FP8、P KVPP且无PP2、D DCP8；A3 1M是int8、P PP2+DCP16、D DCP4且关闭APC，不与旧独立教程PP1/六API混合，也不自动启用MemCache。KVPP和DCP不可随意同端组合；两端PCP1/interleave128仍需匹配实际cache block与连接器，见[CP拓扑](../integration/vllm_ascend_context_parallel_topology.md)。TurboQuant保持A2/A3、BF16、MRv1、禁xLite、禁C8/PCP/DCP及P/D direct=false的独立路径。

精度和性能沿前文来源口径保存：A2的200成功请求不是精度；950历史glm45短请求不证明当前glm47、工具调用、135k/1M或吞吐；GLM-5.3 GSM8K分母1319含10错误，不删除失败；GPQA A2/A3结果不转给GLM-5.2。GLM-5.3必须保留thinking，工具和reasoning parser均glm47并auto-tool-choice；关闭thinking仍产生reasoning的字段行为仅作来源声明，不泛化到Flash。

## 中文差异与本节覆盖边界

GLM5.2.po的318条中，284条msgid可在当前英文连续找到，34条逐条裁决；匹配只反映原串存在，不能消除语义冲突或保证站点HTML版本。旧PO157–159、166、171、178–179、251、318的A2双PP2实例/128000/旧调度预算改为当前单PP4实例/200000，删除旧P2 API。PO72/222/224硬件表达改64GB×16；7/23/100/106–109/112/137–148/203/298–303另有脚本目录、端点、章节链接和格式变化；133/135/138修订长度、DP语义与结果归因，241保留图模式冲突。即使精确匹配的PO101/132/170/175/192也分别存在拓扑、模型名、CPP版本、PP stage和代理端口边界，不按100%翻译匹配替代判断。

本节已将当前完整教程的部署场景与读到的条件融合进既有卡，保留原主来源、生命周期和平台；实现只读Mooncake局部、配置validator/MC2、A3 profile、CPP选路/类声明及Native参数分支，未声称完整实现闭包。外部模型、量化YAML、Motor、SDK、fastokens及CANN网络文档未在本节展开；未导入上游或启动服务、修改主机、运行NPU/benchmark/Agent A/B，也未证明zh-cn/latest HTML与此快照一致。

## 7d9e 与 11-04 公开配方：950DT 单机不再强制 eager

固定`7d9e52da97606050f61f33275b9d9a0def86881a`相对11-03所对照的5f5e25，在合并教程5.1.1的950DT单机W4A4C8/MXFP4命令中删除`--enforce-eager`，同时删除对应“禁用图执行”的说明。11-04 02:59:18 UTC抓取的中文HTML有同一变化，91个代码块全部对应7d9e，唯一改变的代码块就是此单机命令；前文ceac表中的eager因此不能无条件作为新配方的必选项。

该命令仍为TP8/DP1/EP、总context135000、seq20/batch16384、attention与indexer FP8缓存，并保留FlashComm1、CPU binding、shared-expert overlap及`enable_dsa_cp`配置。删除eager开关没有新增显式图模式，不能推导默认图模式、设备图捕获或该权重的完整图执行已验证；实际build的解析配置、捕获与短/长正确性仍须分别验收。维护配方中的`enable_dsa_cp`也不能直接搬到已移除该字段的Main schema。

7.3节的2026-10-10历史本地checkpoint记录仍明确是eager、glm45及短请求结果；没有因启动示例改动而变成非eager或glm47复验。950DT的BF16、Chunked Prefill、Piecewise等原未验证项也未由删除开关自动关闭。A3单机`FULL_DECODE_ONLY`和其余多节点/PD/池化/1M命令本次均未改动，不把950DT单机的一行修订推广到它们。公开页面与固定来源的内容对应不证明整站共用一个build，发布身份边界见[文档渲染核验](../../runbooks/validations/vllm_ascend_document_rendering_evidence.md)。
