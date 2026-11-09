---
type: Guide
title: vLLM Ascend Qwen Hybrid MoE：35B/397B 容量、P/D状态与C8（Qwen3.6-35B-A3B、Qwen3.5-397B-A17B）
description: 按Qwen3.6-35B和Qwen3.5-397B分别选择平台与拓扑，核对混合缓存、P/D等K、量化scale及MC2/共享专家的角色差异。
  补充 Qwen3.6 35B 的950DT单卡MXFP8、A2/A3双卡W8A8、DUO FP16与图捕获配方，以及中英版本、容量和评测口径差异。 针对 Qwen3.6-35B-A3B
  核对 MoE 的 TP 与 EP、长上下文的 KV 与 APC 预算、MTP、版本和多模态精度验收；区分旧 PO 禁止语句与当前配置，以及35B的PD限制和397B的既有范围。A2
  和 A3 的双卡配置分别核对。 补充 Qwen3.5-397B-A17B 的 A3 单主机P8/D8、950DT W4A8C8不等TP与V2 Pull、A2 MP/PD参数，以及159条PO的95处差异、APC、代理端口、Runner和精度验收。
  Qwen3.5-397B-A17B 分别核对 W8A8、W4A8、MXFP 与 C8；按角色选择 MC2 与 flashcomm1、MLP预取，保持重计算嵌套配置。MRv1、VLLM_USE_V2_MODEL_RUNNER
  与多进程 property patch 分开验收；健康检查、请求完成和缓存槽复用分别留证。 397B的分离部署连接器：A3/A2采用 MooncakeConnectorV1，950DT
  C8采用 MooncakeConnectorV2；均使用标准 Pull 代理。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3.5-397B-A17B.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3.6-35B-A3B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.6-35B-A3B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-release-tag.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.5-397B-A17B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/mrv2_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T22:12:22Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- Qwen3.6-35B-A3B
- Qwen3.6-35B
- Qwen3.5-397B-A17B
- Qwen3.5-397B
---

# vLLM Ascend Qwen Hybrid MoE：35B/397B 容量、P/D状态与C8（Qwen3.6-35B-A3B、Qwen3.5-397B-A17B）

## 两个规格分别建容量

397B和35B均为hybrid MoE，但全权重、专家分片和KV容量不同。397B来源覆盖A2/A3/950多卡/多机，不推310P；35B有310P独立W8A8路径。既有CANN Executor Qwen3.5卡的GE/六路TP不是本插件启动接口。

## 权重、缓存与MTP

quantization=ascend选择权重实现，kv-cache-dtype=mxfp8选择950支持的C8；W4A8/W8A8或MXFP名称不证明KV scale存在。P/D保持同checkpoint revision、quant描述与缓存设置。hybrid MTP两端method/K相同，移除投机也需两侧同时调整，不能套MLA P1/D3。

397B A3 PD、950 W4A8C8 PD与A2 PD的global/local DP和device分配各不同，seq/token预算按每engine。融合MC2=1与=2分别是不同实现，A2例子未启不能由A3推支持；shared-expert DP增加复制权重，overlap与fused路径需核对有效配置。

## 35B与310P边界

35B950来源可单NPU MXFP8、A2/A3候选TP2，310P走专用模式且来源建议关闭prefix；总表的单项支持不能覆盖该部署限制。其PD在表中为❌，不因397B有PD就推广。静态kernel增加启动编译时间，要等capture完成后测稳态。

## 验证与回退

覆盖GDN state、Attention KV、chunk、prefix、抢占和MTP回滚，C8异常重复输出先核scale/格式/双端版本。HTTP ready不证明HIXL/Mooncake连通。每次只改一项优化并保留精度，失败回完整权重+状态格式+connector基线，避免仅更换一端KV dtype。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## Qwen3.6-35B-A3B：全文与译文的版本边界

本节新增复读固定Main Qwen3.6-35B-A3B.md全文500行及Qwen3.6-35B-A3B.po全部86条业务译文，60条msgid完全匹配、26条保留原串并逐条裁决。部分旧段落已删除，裁决中的当前章节锚点只是定位上下文，不冒充被删内容的逐字或语义替换。该35B复读批次当时未闭合397B教程或其PO；后续397B全文审阅见下文独立小节，原397B正文、主来源和平台保持。

模型首次支持v0.18.0rc1、950DT要求v0.30.0及以上、本页具体示例目标v0.30.0、本任务Main release pin v0.32.0分别记录。PO第4条仍只有旧0.18rc1下限，不能覆盖950新条件。文档build宏、镜像tag、真实包/二进制与checkpoint revision也不是同一版本身份。本批没有解析站点宏、获取权重或运行镜像。

35B是总参数量，约3B是每token激活量；权重与HBM预算不能只按3B估计。BF16权重行列950DT 96GB×8节点、A3 64GB×16节点、A2 64GB×8节点或DUO；普通W8A8列A2/A3/DUO，950DT另外列W8A8-MXFP8、W8A8C8-MXFP8和W4A8-MXFP权重。节点可用设备总数、权重行要求与具体服务实际使用NPU数分别数，不把普通W8A8行当所有MX格式通用支持。

## 三种35B实例：实际设备与图模式分别保留

| 来源实例 | 实际设备/并行 | 请求与调度预算 | 图、MTP及其他关键配置 |
| --- | --- | --- | --- |
| 950DT W8A8-MXFP8 | visible=0，TP1、DP1，单NPU | max-model-len=135168、max-num-seqs=128、max-num-batched-tokens=4096、memory=0.90 | MRv2，qwen3_5_mtp K=3，FULL_DECODE_ONLY，CPU binding，npugraph_ex=true、static_kernel=true、super_kernel=false，APC开启 |
| A2/A3 W8A8 | visible=0,1，TP2、DP1，两NPU；EP开启、dtype=float16 | 同为135168/128/4096/0.90 | MRv2，qwen3_5_mtp K=3，FULL_AND_PIECEWISE，CPU binding及共享专家overlap，APC开启 |
| Atlas 300I DUO W8A8 | visible=0,1，TP2、dtype=float16 | maxlen20480、maxseq16、memory0.90 | npugraph_ex=false，FULL_DECODE_ONLY、capture=[1,8]，APC关闭；默认命令不启MTP |

两种大内存实例的135168是输入加输出的单请求总上限；4096是每调度步token预算，128是活动请求上限，不能由参数同时出现就宣称128个满长请求都可驻留。按真实KV容量、运行时和图内存留余量，分别测不同长度/并发。950与A2/A3共同使用lazy权重加载和quantization=ascend，不等于相同quant布局或相同CPU/通信路径。

950 C8权重另加kv-cache-dtype=mxfp8；权重名包含C8仍须检查正确scale/实际KV格式，不能把该选项搬给任意硬件或普通W8A8。该段的950DT条件不扩大为950PR均已验证。

A2/A3例的HCCL_BUFFSIZE=1024、HCCL_OP_EXPANSION_MODE=AIV、allocator expandable_segments和线程设置是来源实例输入，不证明真实通信/NUMA已优化。其CPU频率、swappiness、numa_balancing、sched_migration_cost命令会涉及主机设置，本次只作为数据阅读，不把它们当新模型适配前置或HBM碎片已改善的证据。DUO安装页的卸载Triton命令同样未执行。

## 静态kernel与Super Kernel：显式false有实际含义

ascend_compilation_config的真实字段名为enable_npugraph_ex、enable_static_kernel、enable_super_kernel；表中短名不能直接作为JSON键。DUO的capture集合对应cudagraph_capture_sizes。

本批只复读AscendCompilationConfig所在96–180行，不声称完整AscendConfig/CLI初始化已执行。其before validator在enable_static_kernel显式给定而enable_super_kernel缺席时，将后者补为前者；显式enable_super_kernel=false会保留false。950配方的static=true/super=false因此不能缩写成只给static=true后仍声称同配置。

after validator按当前hardware profile的NPUGRAPH_EX能力禁用相关三项，再检查super→static→npugraph_ex依赖；配置字段存在、字典显式为true或代码可构造都不证明设备后端已运行。DUO页要求npugraph_ex=false，与decode ACLGraph不是同一开关；不把关闭npugraph_ex写成所有图模式均关闭。该硬件profile与实际Worker生效仍需按目标版本验收。

## DUO：capture、APC和MTP的窄配方

权重表将BF16版本列入DUO硬件，支持矩阵310P的BF16栏却为❌，而DUO运行例显式dtype=float16并提示部署BF16模型时去掉quantization。checkpoint标签、执行dtype和量化选项分别记录；这些文字不证明DUO支持BF16执行，也不证明权重转换已通过。先验实际加载/有效dtype与数值，不从权重名称推出算子精度支持。

PO68（第68条）仍列capture=[1,2,4,8,16]，当前英文与命令均为[1,8]。maxseq16和只列两个capture size不能据静态文本推成其余batch必然失败或必然自动补齐，先核实际Runner/图fallback与日志，再决定捕获集合。

DUO可选MTP使用method=mtp、num_speculative_tokens=1，来源建议并发少于2时考虑开启、否则不启；这是该实例的调优线索，不是跨模型/所有负载的性能定律。它与950/A2/A3的qwen3_5_mtp K=3分开，不能照抄K或method。优化表还写enforce_eager=true，而5.1主命令没有显式该键；保留命令与参考表的区别，不补造实际生效值。

支持表的310P行给APC✅、长度256k，具体DUO教程却推荐关闭APC、maxlen20480；前者是单项声明，后者是窄配方，不由总表改写配方或宣称256k/16并发已验证。A2/A3与950DT的35B行PD均❌，310P也❌；页首PD参考设计/MindIE Motor建议不解除这条限制，更不能借397B的PD示例推35B可部署。参见[模型支持裁决](vllm_ascend_model_support_resolution.md)。

## 容器、监听与阶段验收

950-a5例映射8设备、/dev/ummu、/dev/uburma和较完整driver/firmware/网络路径，shm=500g；A3例16设备、A2例8设备且shm=1g；DUO容器映射8设备、shm=10g并发布8080。这些是容器可见资源，并不改变服务只选单NPU或两NPU的事实，主机shm也不替代NPU HBM。

DUO实际监听127.0.0.1:8080，文档明确在服务节点或容器内部检查；Docker发布端口不证明容器内仅loopback绑定能被外部访问。950/A2/A3示例监听0.0.0.0:8000，health与评测base_url使用各自实际端口，不能把8000示例直接当DUO入口。权重目录/root/.cache名称相同也不证明节点间共享或revision一致。

静态kernel会增加启动编译时间；等待capture完成和ready，再以请求验证生成。返回HTTP 200并含choices字段只证明窄文本功能请求，不证明135168满长、所有混batch、图、并行、多模态质量或净性能已通过。保留eager/原精度基线与目标配置，按[新模型验收](../bringup/vllm_ascend_new_model_onboarding.md)和[性能评测口径](../optimization/vllm_ascend_benchmark_workflow.md)逐层取证。

## 26条中文差异：删段、证据强度与指标分别裁决

PO35（第35条）旧译文称推荐配置已在特定环境验证，当前英文已删除这一断言，不能借旧中文补上已验证标签。PO63（第63条）的旧A3整节点262144引言已换成950单NPU135168；同页另一个参考表仍有262144/16384，不能拼接为5.1的135168/4096命令已达到262144。高吞吐DP4/TP2、每DP seq32与低延迟默认关投机也分别是参考场景。

第29–32条旧bench子命令/serve示例/几分钟出结果已从当前模型页删除，当前8.2只链接benchmark文档。这不证明Native CLI消失，也不给出固定运行时间或本次性能结果。PO74（第74条）的旧同MoE层TP/EP禁止和maxseq×DP必须不小于测试并发的表述不在新参数列表中，不把旧PO规则带回当前配方；具体实现组合仍按实际模型和功能约束核对。

当前精度表把旧version列换为hardware，MMMU与GPQA均列accuracy/gen、A3 64GB×16节点、83.3。它们是来源报告值，没有补齐shot、样本/数据版本、seed、精确服务配置或原始输出；不归给950/DUO，不推定使用本页两设备配方，也不当本仓复测。MMMU外部数据指南、lm_eval和MindIE Motor的英/中Quick Start正文本批未读取。

PO76（第76条）的msgid虽完全匹配，仍将排队时间计入TTFT和TPOT。实际口径取决于客户端/服务端采样边界，需沿已固定的评测流程核对，不能由一句文案生成通用TPOT公式或直接承诺减小排队就改善每个decode步。接受长度/接受率、吞吐、TTFT、TPOT、显存与启动编译时间分别留证。

本节只是模型文档、译文、支持表选段与配置类选段的知识生产，未导入上游、下载模型/镜像、安装卸载依赖、执行CPU/内核设置、启动服务、通信、评测或Agent A/B。已固定来源和检索通过不提升为NPU实测，该35B批次当时未闭合397B未读范围；整站HTML映射仍未证明。


## 模型与条目身份的消费约定

Qwen3.6-35B-A3B与同卡397B部分分别保留版本、模型权重和硬件条件。本批PO35、PO63、PO68、PO74、PO76等标签按86个业务msgid的对照顺序编号，不是文件行号或API选项。当前35B来源命令设置TP=2并启用EP，两者分别核对；不能把旧PO的同层禁止解释成整个服务不可同时设置TP和EP，更不能由配方文本当成本仓执行通过。


## Qwen3.5-397B-A17B：全教程与中文差异的适用范围

本节补充固定Main的Qwen3.5-397B-A17B.md全文1409行与Qwen3.5-397B-A17B.po全部159条业务译文，64条msgid在英文中完全匹配，95条原串差异逐条裁决，其中10条被删除的段落只记录当前上下文锚点。完全匹配的通用句也可能从旧A3上下文移到当前A2章节，不能用字符串相等复原旧拓扑。下文PO编号按这159条业务msgid的顺序，不是源码行号或启动参数。

397B首次支持v0.17.0rc1，950DT首次支持v0.23.0rc1，本教程基于v0.30.0；任务固定Main的release pin为v0.32.0。这四项与Native vLLM实际commit、镜像展开结果、Python包位置、模型revision分别保存。教程PD仅为参考设计，不建议直接用于生产；其MindIE Motor建议不等于本文已读取对应外部Quick Start或验证生产方案。

BF16权重表列两台950DT（每台96GB×8）、两台A3（每台64GB×16）或四台A2（每台64GB×8）；普通W8A8/W4A8列一台A3或两台A2。950DT另有W8A8-MXFP8、W4A4-MXFP4与C8权重行。容器映射设备数、单服务实际visible设备与权重行的主机数量分别计算，不能按约17B激活量估整套397B权重容量。本节没有397B的310P配方；同卡310P平台来自35B部分。

quantization=ascend与kv-cache-dtype=mxfp8分别选择权重实现和KV存储；普通W4A8、W8A8或MX权重名称都不足以证明C8兼容。P/D必须核对checkpoint revision、tokenizer/chat模板、量化描述、KV scale及实际KV格式。BF16基线选auto，不能把950DT C8开关移给任意权重、A2/A3或950PR。

## 397B单机与A2 MP：DP跨节点、TP在节点内

| 来源实例 | 主机与并行 | 单请求/调度预算 | 配置边界 |
| --- | --- | --- | --- |
| 950DT单机W4A4-MXFP4命令 | 一台8设备，TP8、DP1，EP开启 | maxlen133000、maxseq128、batch8192、memory0.90 | MRv1，qwen3_5_mtp K3，FULL_DECODE_ONLY，APC和async开启；fused MC2=1、flashcomm1、MLP预取 |
| A3单机W8A8 | 一台16设备，TP16、DP1，EP开启 | 133000/128/16384/0.90 | MRv1，K3且draft enforce_eager=true，FULL_DECODE_ONLY、APC开启；MC2=1与flashcomm1 |
| A2双节点MP W8A8 | 每台8设备，global DP2、local DP1、TP8，EP开启 | 每DP maxlen32768、maxseq16、batch4096、memory0.90 | node0 API server count2，DP RPC13389；node1 headless、start-rank1；APC关闭、shared expert overlap=true |

A2 MP不是跨主机TP16；EP的实际world与权重分布还要按模型实现和DP×TP核对，不能仅凭两台机器推定完整权重复制。maxlen是输入加输出上限，batch是每调度步token预算，maxseq是每DP活动请求预算；133000×128不是已证明能同时驻留的KV容量。

当前397B英文仍保留“maxseq×DP不小于性能测试并发”的建议，以及同一MoE层的TP/EP说明；这与35B新版删除旧句的裁决不同。它是测试配置建议，不是服务不满足该乘积就必然启动失败；命令同时设置TP与enable-expert-parallel也不等于同一MoE层同时采用两套分片。短prefix还可能因hybrid缓存块较大而不能复用，APC开启不保证每个短前缀命中。

## 397B A3 PD：一台主机的P8与D8

当前5.4采用单台16设备A3、W4A8-MTP。P使用visible=0–7、TP8/global-local DP1/1；D使用8–15、TP4/global-local DP2/2，两组EP world均为8。一个D launcher创建两个本地DP engine，不再为DP2启动两份占用同组设备的D进程。1P1D指两个服务组，不是两台主机。

| 角色 | maxlen | 每DP maxseq | 每DP batch tokens | HTTP / KV / DP RPC |
| --- | --- | --- | --- | --- |
| A3 P | 133120 | 64 | 20480 | HTTP30060，KV55220 |
| A3 D | 133120 | 100 | 300 | HTTP30050，KV56010，DP RPC6884 |

P eager，D FULL_DECODE_ONLY；双方K3、APC、async开启，MC2=2、shared expert DP=true、overlap=false。D的recompute开关位于additional_config.scheduler_config.recompute_scheduler_enable，不能恢复旧PO里的顶层同名键。MC2=2是CANN MegaMoe路径，必须匹配算子栈与token形状限制；不能由单机MC2=1推成相同实现。

当前connector为MooncakeConnectorV1标准Pull：代理先调用P再调用D，由D拉取KV。P/D同一服务IP、不同HTTP端口，代理8000。旧PO101/102/116/132的双A3主机、双方TP16/DP1、W8A8或48 NPUs性能行不能套到此配方；旧“48”也不能与另一旧双节点文字拼成一套自洽拓扑。

## 397B 950DT C8 PD：两主机与不等TP

5.5改用W4A8C8-MXFP权重与mxfp8 KV，P、D各一台8设备950DT。P TP8/global-local DP1/1，D TP4，global/local DP2/2，两组 EP8（EP world均为8）；D仍只启动一个管理两本地DP engine的launcher。双方maxlen133120；P每DP seq64/batch20480，D每DP seq100/batch300。不能把后两项当D主机合计预算。

该例为MooncakeConnectorV2标准Pull，非layerwise；不等TP的8→4实例不证明任意比例、反向4→8、复制KV head或任意hybrid状态布局都受支持。P/D分别用自己的高速服务IP与HTTP30060/30050，D RPC6884不能填入代理；KV端口55220/56010也不是HTTP后端。每台容器的ascend_local_comm_res_path=/etc/hixlep应来自该主机的端点资源，不是可写共享KV存储目录，也不能复制另一主机的端点配置充数。

P eager、D FULL_DECODE_ONLY，双方K3/APC/async开启，MC2=0、enable_prefill_mc2=false、shared expert DP=true、overlap=false。教程要求其v0.30.0 MRv1栈包含PR19017、release fix 14c6c3f43或等价修复；这里仅记录教程的要求，未读取该外部PR/commit内容、未证明任何当前二进制包含修复，也未据此证明C8 scale正确。

旧PO144/145/146/148中的W4A4-MXFP4 PD、双方TP8/DP1和layerwise代理已不是当前实例，不能只改权重显示名后照搬旧配置。

## 397B A2 PD：七参数脚本与固定KV拓扑

5.6为两台A2，各8设备，W4A8-MTP；P、D均TP8/global DP1，MooncakeConnectorV1标准Pull。P maxlen133120/seq64/batch16384，D maxlen133120/seq200/batch300；APC、async、K3两端保持一致。shared expert DP只在P开启，D为false，不能照抄A3/950双方开启的配置；该例未显式启融合MC2，不由文档缺字段推定所有版本默认。

run_p与run_d都接受七个位置参数：visible、HTTP port、global DP、rank、master address、DP RPC port、TP。P脚本仅消费1–3和7，4–6是兼容占位；D消费全部七项。此例DP1/TP8与固定KV JSON必须一致，不是传任意DP/TP就自动重写KV拓扑。代理使用各自真实IP及第2参数的HTTP端口；不能把D脚本的RPC6884当HTTP30050。

## Runner与容器身份：保留可核验的窄约束

397B的MRv1实例显式设置VLLM_USE_V2_MODEL_RUNNER=0。本批完整阅读mrv2_utils.py的176行：上游已解析环境值非None时优先，0选择V1；未设置时默认V2，配置命中blacklist才回退V1。这条选择路径不证明模型、硬件和connector整套兼容。类property patch须在每个读取配置的frontend、worker、engine-core进程重新应用，pickle不会携带该类补丁。

platform.py本批只复读1040–1054行：选段中的V2强制校验同时要求DeepseekV41ForCausalLM或DeepseekV41DSparkModel架构、DSV41_PACKED_CACHE能力以及当前非V2。不能把它解读成所有950DT/Qwen都禁止MRv1；也不能由未命中该分支推定397B在最新栈全部通过。Runner迁移参见[Runner选择](../../optimizations/rules/vllm_ascend_model_runner_selection.md)。

容器应保持所选镜像内/usr/lib64；整目录挂载主机库即使readonly也会遮蔽匹配的系统库。只按目标URMA/RoCE文档挂载确有需要的兼容文件或vendor目录，再查loader路径。实际服务容器内核对解释器、vllm命令、模块__file__、包distribution版本；同包名、镜像tag或同名/root/.cache目录不证明实际模块/权重身份一致。HCCL_IF_IP填NIC的IP，HCCL_SOCKET_IFNAME/GLOO_SOCKET_IFNAME填接口名。本文的shell、Python身份探针和CPU/sysctl命令仅作为来源数据阅读，本次未执行。

## 397B验收：HTTP、KV、工具调用和精度分层

先逐端查P/D health健康检查与模型名，再通过匹配connector的代理发送请求；HTTP ready或200不证明KV数据路径、量化scale或模型准确率。至少覆盖非空连贯短输出、checkpoint chat模板、并发完成并复用cache槽、重复标点/异常重复、传输失败及streaming分块路径。C8应先核格式、scale与双端版本，再扩大负载。MTP acceptance统计不能代替数值或生成质量验收。

function calling需两端均配置enable-auto-tool-choice、tool-call-parser=qwen3_coder与reasoning-parser=qwen3；客户端执行get_weather后，将assistant tool-call及带匹配tool_call_id的tool结果放入下一轮请求。服务只解析工具调用，不执行天气函数。

当前GPQA参考值为88、W8A8、v0.30.0 release；精度表仍是dataset/version/metric/mode，第77条仅空格对齐改变，不是35B那种version改hardware。AISBench示例batch16、max_out_len65536、temperature0.6、top_p0.95、top_k20、min_p0、presence_penalty0、repetition_penalty1.0。prompt加输出预算须在实际服务上下文内；这些是来源参考值和输入配置，没有本仓原始样本输出或NPU复测证据。

## 95条差异的迁移规则

PO68–71仍围绕旧PD关闭APC与Issue7944，当前A3/950DT/A2 PD实例均开启APC；未读取外部Issue，不声称它已关闭、任意组合均兼容或全部请求都命中缓存。A2 MP仍关闭APC，不能把PD结论扩大到全部部署。

优化表将通用MC2=1换成角色1/2/0，重计算键放入scheduler_config；旧默认AddRMSNormQuant、zero-like和RoPE行被删除，不证明实现消失或所有新栈默认关闭。旧本模型bench子命令与“几分钟出结果”步骤也被删除，当前页只给benchmark入口，不代表Native CLI移除，不提供运行时长或收益承诺。

PO56/113–119的推荐表按当前第5章实际实例、每主机角色设备数、global/local DP及每DP seq/batch解释；不要照旧列顺序逐值迁移。性能调优先固定硬件、版本、权重、工作负载和正确性基线，再逐项改变MTP、MC2、overlap、图或预算，分别记录TTFT、TPOT、吞吐、HBM、启动编译时间及P/D统计。来源的已验证实例措辞不变成本仓复测，也不使不同角色/负载组合自动通过。

本节闭合的是指定397B教程与159条PO的文档审阅，不是完整实现、外链、站点HTML映射、所有硬件模型或真实服务验证。35B的PD限制与DUO配方保持独立；新模型适配和性能Agent应按[新模型验收](../bringup/vllm_ascend_new_model_onboarding.md)、[模型支持裁决](vllm_ascend_model_support_resolution.md)及[性能评测口径](../optimization/vllm_ascend_benchmark_workflow.md)继续收集目标环境证据。
