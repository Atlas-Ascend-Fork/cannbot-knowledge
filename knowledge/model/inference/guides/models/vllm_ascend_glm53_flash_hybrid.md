---
type: Guide
title: vLLM Ascend GLM-5.3-Flash：混合注意力、动态C8与角色配置
description: "按GLM-5.3-Flash混合注意力区分平台动态C8、P/D角色和MTP权重/递归契约，核对rot.weight、head归属及共享专家配置，避免沿用其他GLM模型结论。 GLM-5.3-Flash 按 MRv1、FP8/INT8、MTP eager/graph 和各角色预算区分单机、A2混部与P/D分离；A3 Memcache每worker20GB/总640GB，A2 Mooncake每P worker8GB/总128GB、D零贡献，lookup是IPC。保留A3脚本K3与表K5、A2 Decode脚本60/192/K5/false与旧说明冲突，核对Store自动align、动态C8页及nested优先的recompute参数。HCCL_BUFFSIZE 按 MB 和通信域累计容量预算；A3 Prefill draft eager、Decode draft false 的投机执行与主图模式分开核对。 发布5f5e25的A2池改四节点同24GB/worker+SSD、双P API与独立端口；旧128GB/D零贡献只限ceac。"
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/GLM5.3-Flash.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_mtp_rotation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_mtp_embedding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/5fa10c3799e249627112ead02c8414988d85ddcc/docs/source/tutorials/models/GLM5.3-Flash.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/GLM5.3-Flash.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_mamba_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_speculative_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/tutorials/models/GLM5.3-Flash.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/vllm_ascend/ascend_config.py
  role: constraint
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-11-04T03:05:17Z'
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
- GLM-5.3-Flash
- GLM5.3-Flash
- GLM-5.3-Flash-w8a8
- GLM-5.3-Flash-w8a8-mxfp8
- GLM5.3-Flash.po
- glm5_next
- Glm5NextMTPModel
---

# vLLM Ascend GLM-5.3-Flash：混合注意力、动态C8与角色配置

本卡的部署来源有版本边界。7d9e已回退GLM KPool的INT8实现并拒绝该类型，见[7d9e运行时差异](../integration/vllm_ascend_7d9e_runtime_delta_contract.md)的KPool节；若下面的历史配置涉及indexer INT8，不把它作为7d9e可执行配方。

## 范围与权重

Flash不是GLM-5.3大模型的同名小规格：它有混合sparse/linear Attention与多模态输入。A3 W8A8、950 W8A8-MXFP8和A2多节点参考各用独立权重/容量。不可套GLM5.2/5.3的SFA TurboQuant路径。

## C8和P/D专属条件

来源Flash C8由runtime动态cache量化，不需要独立C8 checkpoint：A3 kv-cache-dtype=int8、950=fp8。主KV格式与权重量化仍分别核对，不将W8A8-MXFP8误作KV必已FP8。

A3参考P用MRv1 enable_dsa_cp、Fused MC2和shared-expert DP，D用shared-expert overlap与FULL_DECODE_ONLY而不启fused MC2。当前Main A3 PD脚本两端MTP K3、P draft eager而D draft graph，第9章表仍列K5；单机A3的K5是另一场景，保留来源内冲突。它是hybrid，不能套非hybrid P1/D5的通用模板。

## 多模态与缓存验证

保持thinking启用，reasoning_effort按checkpoint协议验证；不能设置enable_thinking=false后把内容解析变化当数值正确。正向检查文本/图片的placeholder、positions与状态，对video按明确禁用进行拒绝验收，覆盖chunk/prefix和投机回滚。A3池化device_sdma要求host LingQu>=1.5，仅升级Python包不能满足网络前提。

## 优化与回退

按角色独立调seq/token预算，保存HBM余量。缓存收益必须由远端hit、传输和端到端TTFT共同支持；无hit不能归因优化。遇输出或传输不一致时恢复完整同版本权重/KV/connector，不将不同GLM模型结果互作参考。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## MTP加载与递归精度的源码探针

GLM5-Next MTP按真实加载集合设置head/embedding所有权；checkpoint is_rot_used为真却缺rot.weight时显式拒绝，多模态model.language_model前缀要先规范化。PP末阶段可加载本地embedding，MTP专用embedding优先于target顶层副本。最终norm后状态同时供logits与递归，不再在compute_logits重复norm；详见[共享与PP嵌入](../../runbooks/precision/vllm_ascend_mtp_head_ownership.md)及[两路隐状态](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)。这些源码/CPU断言不代表本卡各部署场景已完成K步或NPU验证。


## 后续文档的镜像、启动阶段和实验功能说明

另行固定的文档提交`5fa10c3799e249627112ead02c8414988d85ddcc`把镜像写为版本模板加硬件后缀：A5/950DT为-a5、A3为-a3、A2无后缀。模板须展开为真实版本并记录digest，不能把{tag}或模板变量当作已存在镜像。若旧glm-5.3-flash镜像或vLLM 0.23.0环境在加载配置时报Transformers不识别glm5_next，失败发生在DP engine初始化前；先核对实际vLLM/Ascend/Transformers配对，再排查分布式通信。

同次文档澄清PD proxy在独立主机的Ascend容器内运行，官方镜像源码入口为`/vllm-workspace/vllm-ascend/examples/disaggregated_prefill_v1/load_balance_proxy_server_example.py`；源码安装用实际checkout前缀。不要依赖调用shell恰好位于源码根目录。实验性[RecoverSSM](../optimization/vllm_ascend_glm_kda_recoverssm.md)仅A3/A5、MRv2并排斥PP/PCP/DCP和APC，不能因本卡基础部署覆盖A2或其他并行就自动开启。上述为分版本文档修订，未整体升级原源码基线或证明全部部署脚本可运行。


## 当前全文、Runner与权重基线

本节完整对照固定ceac提交的GLM5.3-Flash.md英文1909行和PO199条：174原串连续匹配、25人工差异。Main基础部署声明Ascend仅MRv1；950 PD两个角色模板却没有显式导出VLLM_USE_V2_MODEL_RUNNER=0，而总说明声称所有脚本都有该项。必须核对实际继承环境和目标build，不把遗漏当MRv2支持证据。此前单独Site提交的RecoverSSM实验MRv2路线保留为另一版本/功能交集，不用它覆盖本篇基线。

GLM-5.3-Flash是稀疏加线性注意力/mHC的原生多模态模型，reasoning_effort为low/high/max；不由宣传价格或第三方模型比较认定质量收益。950DT使用Eco-Tech/GLM-5.3-Flash-w8a8-mxfp8，A3/A2使用对应w8a8。C8由runtime动态量化而非独立C8 checkpoint，950主KV fp8、A3 int8，不能混换平台权重。950 PD脚本的本地大写目录和0918后缀只是挂载示例，必须指向实际选定checkpoint，不能当新的官方下载资源。

若Transformers不识别glm5_next，失败发生在模型配置加载、早于DP引擎初始化；先记录活动python/vllm/Ascend/Transformers及镜像digest，不通过调整网卡或rank掩盖模型类型问题。后读的HF override选段对glm5_next或glm5_next_text保存num_nextn_predict_layers为n_predict，改model_type为glm5_next_mtp、architecture为Glm5NextMTPModel；配置类型、architecture和命令deepseek_mtp是不同层次，不能以局部映射认定完整加载成功。

## 单机与A2混部：每引擎预算分别保存

| 场景 | 物理主机与逻辑并行 | 总长 / seq / batch / memory | 运行条件 |
| --- | --- | --- | --- |
| 950DT单机 | 一主机96GB×8，DP1/TP8/EP | 132096 / 32 / 8192 / .9 | W8A8-MXFP8、主KV FP8、MTP3/draft eager；FULL_DECODE_ONLY，capture1/2/4/8/16/32/64/96/128；buffer1024 |
| A3单机 | 一主机64GB×16，DP1/TP16/EP | 1048576 / 32 / 8192 / .92 | W8A8、主KV INT8、MTP5/draft eager=false；prefetch、FULL_DECODE_ONLY、shared-expert overlap、API1；AIV/buffer1024 |
| A2混部 | 两主机各64GB×8，DP2/TP8/local1/EP | 133120 / 32 / 8192 / .85 | MTP3/draft eager；FULL_DECODE_ONLY capture4/8/16/32/64/96/128、prefetch；AIV/buffer1024，未显式主KV dtype |

三类例均显式MRv1、image1/video0。A2 Node0省start-rank并提供唯一API，Node1用headless/start1；同master IP/RPC12321、本机IP/网卡各自正确。不要为对齐其他模板给Node0补显式rank或把headless节点当API。单机与A2混部命令未显式列出全部glm47 parser字段，函数调用按FAQ同时核对tool parser/reasoning parser/auto choice；不能只加一个reasoning parser。保持thinking，不设置enable_thinking=false或thinking=false。

maxlen包含输入和输出，seq/batch是每engine而非proxy总量。prefetch读入OS page cache，需要host内存，不等于权重已进NPU。HCCL buffer示例单位为MB且通信域会累计占用，不能用gpu-memory-utilization单值代替完整容量核算。

## PD：三种拓扑及来源内数字冲突

| 平台/角色 | 物理节点、DP/TP与API | 总长 / seq / batch / memory（脚本） | 投机与角色配置 |
| --- | --- | --- | --- |
| 950 P | 一节点DP1/TP8，API8000 | 133120 / 256 / 24576 / .9 | MTP5，spec未显式eager；DSA CP/FlashComm1/shared DP/overlap开、MC2=0；capture列表但未显式主graph模式 |
| 950 D | 一节点DP8/TP1，八API8000–8007 | 133120 / 30 / 120 / .95 | MTP5，spec未显式eager；FULL_DECODE_ONLY、shared DP/overlap/recompute |
| A3 P | 一节点DP2/TP8，API9081–9082 | 1048576 / 64 / 4096 / .92 | MTP3/draft eager；DSA CP、Prefill MC2/Fused MC2=1、shared DP、overlap=false；prefix retention None |
| A3 D | 一节点DP4/TP4，API9900–9903 | 1048576 / 32 / 192 / .92 | MTP3/draft false，FULL_DECODE_ONLY、FlashComm1/shared DP/overlap/recompute |
| A2 P | 两节点DP2/TP8/local1，P0 API9081、P1 headless | 1048576 / 64 / 8192 / .9 | MTP5/draft eager，target eager、async、APC/chunk、FlashComm1/shared DP/overlap，mc2 hierarchy |
| A2 D | 两节点DP8/TP2/local4，D0/D1各9900–9903 | 1048576 / 60 / 192 / .85 | MTP5/draft false，FULL_DECODE_ONLY、async、static kernel true、skip MM profiling，FlashComm1关闭 |

A3两角色各占16逻辑设备；A2每节点8设备，D global ranks0–3与4–7分别放两节点。所有例启EP并限制image1/video0；A2 PD主KV与Indexer均int8，A3只显式主KV int8，950双端主KV fp8，不能补成同一Indexer格式。A2的skip MM profiling不证明图片服务已经正确。

950双端V2 connector显式P DP1TP8/D DP8TP1、KV端口30100/30800；P/D buffer3072/1024、AIV，RPC12325在不同host复用，proxy为独立host8000。A3 V2端口36680/36580但未显式extra topology；HCCS supernode使用hccs:device、资源版本1.2和host socket网卡，来源设备RoCE端口down是适用前提，不是让Agent修改主机网络的默认动作。A3先D后P、全六API健康后启动P容器proxy8081。

A2普通PD的P KV36000/D30100，双端use_ascend_direct=true并声明真实P DP2TP8/D DP8TP2。P内部LB保持local1、P0不传data-parallel-rank，P1通过wrapper添加headless/start1；启动器第四参数可用于lookup等，不能为透传它在Prefill加显式rank而触发external/hybrid拒绝headless。Decode显式rank则是有意提供独立API。D按60000+rank×100到60099+rank×100分HCCL host/NPU socket窗口；IPC、RPC、API、KV、HCCL各自核对，不以一个端口值判定无冲突。

当前A2说明段仍写D seq32/batch1024、MTP3/draft eager=true，和实际脚本60/192/K5/false不同；A3第9章MTP表写5而PD脚本双方3。原摘要中的“两端K5”因此只能作为特定参考，不能覆盖当前A3命令。保留各段来源与差异，先固定目标build/checkpoint及最终生效配置，再做质量和状态验收，不拼接成未经证明的新配方。

共用inline launcher有template参数、七个角色位置参数、按local索引分TP设备/API端口，local默认global、start默认0；parent只join而未汇总child exitcode。不能替换为Pro八参PCP启动器或其他严格rank校验脚本。A2普通启动先P0/D0后立即启动P1/D1以补全各组，别等待缺rank组ready；proxy仅注册P0和八个D API，P1以日志核实。

## ceac 的A3与A2池化：后端、贡献内存和读取职责分开

A3使用Memcache embedded LocalService，每worker20GB、各节点16 worker各320GB、两节点来源总640GB；world_size256是LocalService上限，max.dram1024GB不是实际已分配。使用device_sdma且非零容量按1GB对齐，LingQu>=1.5是host侧平台前提，升级Python包不证明满足。容器保留hccn.conf只读挂载，ACL_OP_INIT_MODE/FABRIC_MEM和LD_LIBRARY_PATH按真实安装位置核对；不运行环境或内存配置。

A3 Meta/config/metrics为5000/6000/8000；多连接器组合V2与Memcache Store，两端APC、chunked prefill、hybrid manager、align、use_layerwise=false，Store child内memcache_dp_init_barrier=true全组一致。P lookup37000–37001、D37100–37103是本地IPC标识；D Store consumer_is_to_load=false、consumer_is_to_put=false，仍贡献host内存且通过V2接收KV。Meta→D→P→proxy，先确认预留内存及所有API，再比较其他P rank远程读取，不能以local prefix hit证明池命中。

A2使用Mooncake/P2PHANDSHAKE/protocol ascend，Master在P0:50088；P每worker8GB、8 worker每节点、两节点来源总128GB，D segment0，所有节点同tenant default/PYTHONHASHSEED。容量按真实parser单位、worker数和可用host内存核对，不套A3的640GB。preferred_segment/same-node allocation为true、SSD关闭；不设置A3 FabricMem，文档此组合不要求通用大页或HCCL_INTRA_ROCE_ENABLE，不扩成其他后端都不需要。

A2 pool片段显式把P V2 KV端口改30000，D仍30100并保留direct/真实拓扑。Store非逐层、D不load不put；P lookup37000–37001/D37100–37107不改变P内部LB。Master eviction .9/.1、KV lease11000、client TTL120/offload=false是来源例；Master→D两节点→P两节点→proxy，与普通PD补rank顺序分场景解释。

Store池化的所有hybrid组、线性状态和完整块必须共同正确。来源解释本模型有non-prefix-cacheable组，池化采用whole segments而非逐层传输。Prefill跨rank的ascend_store_load_get_keys_total增加只记录GET keys，仍需真实传输完成、返回值和输出质量；部分尾块可能重算，不能把HTTP200或单个counter当端到端证据。

## 当前自动align、动态C8页和旧recompute配置

完整patch_mamba_config.py 179行先调用原MambaModelConfig校验，再按当前配置调整。自动强制align要求hybrid KV manager开启，且canonical AscendStoreConnector在顶层或MultiConnector直接child出现，并排除extract_hidden_states方法；none改align，已有其他模式则断言需align。仅PD connector不由该helper自动强制；历史Store alias或任意嵌套并不在此识别分支。APC且align时mamba_block_size取实际attention block_size，否则取max_model_len；不能把文案的“APC自动”或“含Store自动”简化为无条件。

稀疏index_kpool与动态C8场景按真实Mamba state bytes、packed token page及lcm(128,index_kpool×16)对齐；C8 coverage另限制较大请求，源码544→640只是此配置例。不能从旧文默认block128推运行时仍128，也不能只减KV dtype而不核对共享Mamba page padding及完整缓存容量。所调用的原Native Mamba、model shape、packed helper和设备kernel没有在本节闭合，不提升为NPU验证。

SchedulerConfig选段保留nested scheduler_config优先于旧top-level，再到default；旧recompute_scheduler_enable仍fallback并告警，nested同时存在则旧值被忽略。platform选段在P角色警告并写nested false使worker重建时关闭，在非PD/非consumer拒绝，在D按async等配置选择重算scheduler。文档旧键尚可解析不等于所有部署已验收；原生配置、实际角色与完整初始化链继续取证。

## 模态、精度和中文来源边界

基础脚本统一image1/video0；正向检查文本和图片、对视频做拒绝验收，不把原生多模态扩成视频支持。保持thinking并按checkpoint协议校验reasoning_effort；工具场景核对完整glm47三项。MTP加载rot.weight、head/embedding所有权、两路最终norm及递归状态沿已有专用卡验证，不因模板给K而承诺已完成K步精度。

来源GPQA89.9和MMMU-PRO78.4来自更早A3 P DP2TP8/D DP8TP2，经proxy采样temperature1/top_p.95，max_tokens分别131072/98304。当前A3 D DP4TP4，所以它们不是现脚本、本仓硬件或Agent的实测结果。1M总长与输出预算、role seq/batch及APC/remote pool状态分别固定后，才可比较TTFT/TPOT/吞吐。

PO199的25变化主要涉及1P1D称谓、链接anchor、world_size标点、MRv1说明扩范围和LingQu平台前提。174精确匹配中仍有A2旧预算及第9章K5，原串匹配不代表事实正确或全站HTML一致。本批只读固定来源，没有导入上游、下载模型、安装镜像/SDK、修改host或启动服务/NPU/精度性能/Agent A/B。

## 2026-11-03 发布快照：A2 普通 PD 与 SSD 池分开

本节固定 `5f5e25dd94db85b59251be7d3baf7c808475b6d7` 全部文档差异和本次中文发布 HTML。前文A2 8GB/P-worker、总128GB、D零贡献、P1 headless/仅P0 proxy及旧lookup端口均属于ceac配方，不能复制到后续SSD池。后续文档声明GLM-5.3-Flash正式支持v0.30.0，但仍要求包含所选场景maintenance更新的build；这不是main SHA与任意v0.30镜像可交换的证明。

以下是发布文档声称对应 release 维护场景的配方；同5f5e25 Main 的 ascend_config.py 已没有 enable_dsa_cp 字段（3164阶段已移除），不能按网页继续给 Main 设置它。必须先定位包含所需维护更新的 release build 及其真实schema；来源发布与Main实现的这处矛盾尚未由设备实验消除。

普通A2 PD更新为P seq64/batch4096、target不显式eager且enable_dsa_cp=true，draft K5/eager；D seq60/batch192/memory.9，FULL_DECODE_ONLY、draft K5/false。旧说明的D32/1024/K3冲突在该版本已按60/192/K5修订。新增HCCL_INTRA_ROCE_ENABLE=1、P pinned expandable配置，移除dev/profiler、skip-MM和image/video限制等旧例字段；不由“字段删除”推默认视频支持或所有组合通过。

A2 SSD pool四主机用独立生成suite：P0/P1为DP rank0/1、TP8，各有API8000；D0为DP0–3、D1为DP4–7，TP2，每台API8000–8003。两个P都注册proxy，不能复用普通PD的P1 headless wrapper。Master改P1:50088，四节点相同mooncake-ssd.json，global_segment_size=24GB/worker、preferred_segment=false、SSD=true，存于/mnt/mooncake_offload；D也贡献对应segment，不沿用0。按16个P worker与16个D worker分别核预算，调整非零值仍按1GB对齐。

四节点须把可写真实host SSD挂到该容器路径，`df -h`和写权限实际确认；只在overlay内mkdir会耗尽容器root。来源例总/每bucket SSD limit各16106127360字节（15GiB）、local buffer1073741824字节（1GiB）、eviction=lru。common engine执行超时3000、transfer10000、reasoning parser=glm45；MOONCAKE/Python库路径按实际安装目录设置，A2 RoCE不加A3 FABRIC_MEM。

pool P KV30000、engine_id=DP_RANK、lookup0；D KV31000、engine_id=100+DP_RANK、lookup1，lookup仍为本地IPC标识。MultiConnector的V2 direct负责P/D，Store backend=mooncake/use_layerwise=false；D仍不主动load/put，但贡献内存。P/D均APC+chunked、主/Indexer INT8、memory.9、async，P64/4096/draft eager，D60/192/FULL/draft false，K都5。独立wrapper的DP rank、API/RPC/KV与proxy配置整套采用，不把旧模板端口拼进新suite。未运行该suite、SSD、模型或NPU测试。
