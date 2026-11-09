---
type: Guide
title: vLLM Ascend MiniMax-M3 / M3.1-Flash：权重格式、Draft KV 与部署边界
description: 区分M3主线实现和M3.1-Flash镜像预览，按W8A8/MXFP8选择量化，显式隔离target FP8与draft BF16并核对多模态内存。
  MiniMax-M3按普通133000与1M分开，保存单机/分离的EAGLE3、PP分区和每worker预算；核对Mooncake SSD、FP8 cache
  skip、图捕获与每rank并发，保留parser/多模态及单请求版本验证边界。 按host数量分别列出950双机DP2、TP4与A3三机配方；1P1D按服务组计数。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/MiniMax-M3.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/MiniMax-M3.1-Flash.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/MiniMax-M3.po
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/scheduler.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/core/sched/scheduler.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/compilation.py
  role: constraint
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-31T01:03:00Z'
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
- vLLM Ascend MiniMax M3/M3.1：权重格式、Draft KV 与镜像边界
- MiniMax-M3
- MiniMax-M3-w8a8
- MiniMax-M3-MXFP8
- MiniMax-M3-EAGLE3-GQA
- MiniMax-M3.po
---


# vLLM Ascend MiniMax-M3 / M3.1-Flash：权重格式、Draft KV 与部署边界

## 先确认交付物

M3教程基于主线，M3.1-Flash教程明确支持代码尚未合入、仅指定Docker预览，不支持普通源码pip安装。不能因为文档在当前仓库就给M3.1生成main编译部署承诺。两者全量参数、缓存和draft策略各自固定。

## 权重和草稿

M3 BF16不设quantization，ModelSlim W8A8用ascend，原生MXFP8用mxfp8；mxfp8权重和fp8 KV仍是不同选项。M3配专门GQA Eagle3，PP支持还受Runner/模型条件限制。M3.1官方routed NVFP4不能直接在Ascend执行，必须用指定A2/A3 W8A8或950 MXFP8权重。

M3.1参考DSpark K7，950 PD target kv-cache-dtype=fp8，但speculative_config.kv_cache_dtype=bfloat16；不显式指定draft会继承target并因缺FP8参数失败，需P/D两侧都设置。不能为draft报错直接把target全部换dtype然后宣称同一方案。

## 多模态与服务

M3省略limit-mm不等于禁多模态规划，纯文本明确language-model-only。视频默认32帧可形成巨大视觉token负载，控制真实frame采样而非只降低text max_tokens。reasoning启用/禁用、mm:think分界、XML tool schema coercion与stream fragments都需实际parser验证。

## 容量和回退

M3 A3 BF16建议多节点而量化可单节点，M3.1预览拓扑不外推；按每rank权重、KV、MoE工作区和图峰值选预算。完整初始化后再代理请求，日志持续加载与已失败区别看所有角色首个错误。恢复相同模型/交付物基线，不混用两个系列的draft和权重。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## M3 教程全文：版本、权重与服务形态

此节仅补 MiniMax-M3.md 全2952行和中文PO全326条；前文M3.1-Flash镜像/draft合同不变，不将M3的EAGLE3、PP或长上下文配方自动移植给M3.1。教程称基于main；后述1M实测记录另是0.30.0+empty配Ascend 0.30.0rc2.dev166+g7672a5b50，不把版本记录当本次Main或独立Native快照的成功证明。

M3接收文本、图像和视频。BF16不设quantization，ModelSlim W8A8用ascend，MXFP8用mxfp8；权重量化与KV-cache-dtype分别决定权重和缓存。草稿明确MiniMax-M3-EAGLE3-GQA，不能照搬GLM MTP或M3.1 DSpark。来源BF16建议双A3且不推荐单A3，另称A3非PD多机不推荐；保留推荐场景差别。A2至少两机BF16与单机W8A8只在文字/表中列出，教程脚本主要覆盖A3与950，不补A2实测。

参考容量为A3每host16个64GB逻辑NPU、A2八个64GB、950DT八个96GB。普通PD一处写A3 64GB×24，同一拓扑与池化段却用16逻辑worker/host，不能将24直接当每机物理NPU数。容器A3 shm100g/950 shm60g是请求配置，实际host余量需核对；950 Device UB的ummu/uburma与驱动挂载不照抄A3 devmm_svm。镜像、SDK、权重和设备均未在本批下载或运行。

## 普通上下文的角色预算

下表预算按max-model-len / max-num-seqs / max-num-batched-tokens / gpu-memory-utilization排列，未显式值保持未知。全体示例显式MRv2，K表示EAGLE3 num_speculative_tokens。

| 场景 | 全局拓扑与每host本地rank | 长度 / 序列 / 批token / 比例 | 缓存、图与草稿 |
| --- | --- | --- | --- |
| A3单机BF16 | DP2/TP8 | 133000 / 16 / 未显式 / .92 | FULL_DECODE_ONLY、APC/chunk on；spec未显式 |
| A3单机W8A8 | DP4/TP4 | 133000 / 32 / 32768 / .92 | FULL_DECODE_ONLY、APC/chunk on、K3；long threshold4096 |
| 950单机MXFP8 | DP2/TP4 | 133000 / 500 / 16384 / .92 | target FP8 KV/draft BF16、K3、async/prefetch/fullDecode |
| A3双机BF16 | DP4/TP8，各local2、start0/2 | 133000 / 32 / 未显式 / .92 | K3/fullDecode；第二host headless |
| A3双机W8A8 | DP8/TP4，各local4、start0/4 | 133000 / 32 / 未显式 / .92 | K3/fullDecode；第二host headless |
| A3 PD Prefill | DP1/TP4/PP4，一host一个engine | 133000 / 32 / 8192 / .92 | target eager、APC/chunk on、K3 |
| A3 PD Decode | DP8/TP4/PP1，两host各local4、start0/4 | 133000 / 128 / 32768 / .92 | fullDecode、APC/chunk on、K3、fused_mc2=0 |
| 950 PD Prefill | DP2/TP4/PP1，一host local2 | 133000 / 128 / 32768 / .92 | target eager、main FP8/draft BF16、K3、APC/chunk on |
| 950 PD Decode | DP2/TP4/PP1，一host local2 | 133000 / 256 / 32768 / .92 | main FP8/draft BF16、K3/fullDecode；APC/chunk未显式 |

普通服务API11223，served-model-name=minimax-m3。单图默认image1/video0，ViT DP未默认开启。A3单机BF16无草稿项不补K3；双机脚本有K3，不能互换。A3单机W8A8另设API server count1、shared expert DP/Flashcomm1、weight_nz_mode=2与fuse_norm_quant=false。950单机有async、prefetch与fuse_qknorm_rope=false，PD Prefill却显式qknorm/normal quant融合true；这些是不同配方，不由单个布尔判断全模型支持。

## 1P1D按服务组，不按两台机器

A3普通分离跨三host：P一host TP4×PP4占16逻辑设备，60层按16,15,15,14切分；D两个host组成一个global DP8，每host四个TP4。两端MooncakeConnectorV1 extra布局一致，P含pp_layer_partition，D的PP保持1。P API31050/RPC6884/KV36000；D每host API31260–31263/RPC31422/KV36100，所有D用D0协调地址且global ranks0–3/4–7唯一。proxy8009注册一个P与八个D端点，不能只注册每host一个API。

950普通两host为P2TP4/D2TP4：P API31050–31051/RPC6884/KV30000，D31060–31061/RPC5964/KV26900。扩为三host时P不变，D global DP4，两host各local2，start0/2、API31060–31061与31062–31063；P/D两端extra都改D4，global rank偏移保持唯一。原始KV26900可保持相同base，由global DP rank派生握手端口，API与握手端口不是同一用途。

PP-aware inline launcher用命名环境变量，不是旧七参脚本。local DP缺省全局，start0、RPC12321、API8000，设备段长度TP×PP，API按local rank递增；仅DP>1传data-parallel-rank，DP1仍保留rank供connector端口计算。子进程subprocess check=True，父进程却只join，没有聚合exit code；全部join不证明全部API就绪。P/D模板在共享文件系统也分目录，launcher从当前目录读run_dp_template.sh。先等协调器日志后让两个D host并发初始化，所有rank就绪再启动proxy；路由换MindIE Motor不自动改变真实拓扑或调度预算。

## 捕获大小、rank容量与全局并发的三个量

教程给出capture ceiling512的EAGLE3 K3示例：若某rank实际接收128个请求，每步扩展4×128=512；129个则516，超过该档位范围时需按实际图调度核验fallback。DP2、全局并发256/257得到128/129是均匀分配的假设，不能把--max-num-seqs256解释成两个rank合计最多256。增大capture到1024会占额外HBM，不保证吞吐提升。

独立Native v0.32.0快照5df的SchedulerConfig选段明确max_num_seqs按每个DP rank，runner buffer/图容量与max_num_active_seqs准入上限可分开；scheduler初始化也独立取max_num_scheduled_tokens或batch budget。CompilationConfig选段中capture max初值None，由配置推导，注释说默认ceiling512、Blackwell另1024；这不是Ascend所有运行环境默认一定捕获512的证明，完整capture列表构造、NPU dispatcher和教程0.30容器未在此段闭合。

同一Native配置文档说long_prefill_token_threshold=0关闭cap，batch中只有一个请求时不施加公平性cap。教程单请求1M仍用max-num-batched-tokens8192或8限制每迭代总预算；不能因此推广“单请求任何预算下都被long threshold硬限制”。记录每rank实际request/token批大小、capture列表、graph/eager命中与HBM峰值，再比较吞吐/TPOT。分配失败不能仅凭memory文案归因SQ/CQ；只有出现对应[特定失败签名](../../runbooks/runtime/aclgraph_sq_cq_alloc_fail_capture_sizes_budget.md)才按该Runbook取证，不将它的旧版经验公式套成本教程失败原因。

## Mooncake三层池化：每worker预算与真实SSD

普通分离不要求Master，池化用MultiConnector把在线MooncakeConnectorV1与持久AscendStoreConnector组合；默认由P lookup/load/write。A3保持上述三host拓扑，950池化例保持两host，不拿普通三host扩展示例当池化已验证。Store lookup端口为P37000+DP_RANK、D37100+DP_RANK，每rank唯一，不能借用V4.1教程的字符串0。

每个worker都有mooncake.json：P2PHANDSHAKE、protocol ascend、Master50088、tenant default，global_segment_size按1GB对齐，A3三host均15GB、950 P/D均64GB；950P preferred_segment=false、D=true，prefer_alloc_in_same_node=true。容量按TP/PP所有NPU worker累计，非每host15/64GB；环境MOONCAKE_GLOBAL_SEGMENT_SIZE会覆盖JSON。额外SSD IO buffer是1073741824 bytes，独立于segment；内存碎片、权重和通信预算另留余量。

SSD起始预算为每worker10GiB，同时设reported total limit与local bucket max，同一预算不加成20GiB；LRU另显式启用。默认reported 2TiB只是通告容量，不是立即占盘；bucket默认0表示磁盘容量90%。A3十六worker合计160GiB加各自IO buffer，所有worker共享同盘时还要留其他数据空间。实际本地SSD挂载、可写绝对路径、容器bind mount、setup()支持SSD参数、各rank目录都需核对；ROTA0、目录名/nvme或网络共享目录都不证明本地SSD层可用，不操作本机磁盘来代替知识验证。

Master设置offload=true、lease11000毫秒/client_ttl120秒、eviction .9/.1。A3 HCCS用fabric memory条件，RoCE另需INTRA_ROCE/网卡/hugepages；950普通SuperPod UB用LOCAL_COMM_RES version1.3 blob，RoCE用hixlep静态路径。池化模板保留静态path，按实际fabric调整MultiConnector内层并与资源env一起核对，不将UB与RoCE设置全拼上。950 pooled D未显式Flashcomm1而ordinary D有，保留差别，不自动补true。

启动Master→全部D→P→proxy。验收A3九个API或950四个API、segment注册、重复prefix触发P lookup/get/put及正常P→D transfer；再用大于host pool的工作集验证实际SSD offload和读回，memory-pool hit与HTTP200都不证明SSD被使用。详见[通用池后端预算](../deployment/vllm_ascend_kv_pool_backends.md)；本卡具体大小不升级成所有模型固定要求。

## 1M单机与分离：预算、图模式和证据强度

1M指1048576 tokens，max-model-len覆盖输入加输出，chunk budget不是总上下文。以下均MRv2、序列1、无spec、APC/async/static关闭，不能沿普通K3/高并发模板叠加。

| 场景 | 并行布局 | 长度 / 序列 / 批token / 比例 | 独立条件 |
| --- | --- | --- | --- |
| A3单机W8A8 | DP1/TP4/PP4，15,15,15,15 | 1049600 / 1 / 8192 / .95 | FULL_DECODE_ONLY、auto KV、threshold8192、language-model-only、block128 |
| 950单机MXFP8 | DP1/TP8/PP1 | 1048576 / 1 / 2048 / .92 | FULL_DECODE_ONLY、FP8 KV skip layers0/1/2，image0/video0 |
| 950单机MXFP8 | DP1/TP4/PP2 | 1048576 / 1 / 8192 / .92 | 同FP8 skip0/1/2；命令未显式禁MM，不凭文字补language-only |
| A3 1M PD Prefill | DP1/TP8/PP2，30,30，一host | 1049600 / 1 / 8192 / .95 | NONE+eager、auto KV、threshold8192、HCCL256 |
| A3 1M PD Decode | globalDP4/TP8/PP1，两host各local2 | 1049600 / 1 / 8 / .99 | NONE+eager、threshold8、HCCL64、KV47620449894 bytes/worker |

A3的1049600可容纳1048576输入加最多1024输出，需allow-long-max-model-len许可；950总1048576若预留1024输出，输入最多1047552。950需要匹配experimental_950_transformer vendor环境，不能只复制source命令宣称包已具备。A3 1M单机Flashcomm1/overlap on、shared expert DP off、weight NZ2；950两单机关闭Flashcomm1、shared DP和overlap。它们不是普通PD的分区或融合设置。

A3 1M PD每个D进程local DP1，launcher每host启动2个进程，共global ranks0–3。两host各API31260–31261，P31050；proxy改18919、监听0.0.0.0，客户端用真实proxy IP，不用普通八D端点映射。P分区30,30，D unset PP partition，P/D均显式声明P1TP8PP2/D4TP8PP1、KV36000/36100。D shared expert overlap off，P on，二者均text-only、Flashcomm1。

显式KV47620449894 bytes约44.35GiB/worker会覆盖gpu-memory-utilization对KV大小的推导，不与.99相加；这是特定布局值。按所有D worker中最少可用HBM，扣权重、通信、activation、workspace与runtime余量，调整后还要核对KV token capacity足以1049600，装不下就改拓扑，不能缩小分配后仍声称支持1M。早先fullDecode+auto KV分配失败只属该测试环境，不证明所有1M图模式都不可用。

来源记录vLLM0.30.0+empty/Ascend0.30.0rc2.dev166+g7672a5b50，仅一个真实1M输入、33输出、三处随机值检索正确、P prompt计数与D transferred-prefix hit增量相同、无preempt。它不证明四个同时1M或AISBench性能；规范化env脚本未重跑，原container既有改动未完整审计。复现时先短请求，再用实际tokenizer精确构造1048576输入、留输出预算，核对五API健康、P计数/D外部prefix命中和答案，不能仅看配置长上限。

## 多模态、parser与评测边界

图像/视频共用Vision Tower，unused modality显式0；任一保持开启仍保留塔，省略MMlimit不关闭规划。mm-encoder-tp-mode=data可增加每卡占用，重新定长度/序列/HBM；language-model-only可配Flashcomm1，但多模态请求必须移除。默认视频32帧，8/16只用于快速smoke，正式数据集按协议采样；仅减text max_tokens不能抵消视觉token。file媒体路径要按实际目录允许，默认模板单图image1/video0不自动支持视频或混合。

thinking_mode=enabled/disabled/adaptive，未设置默认adaptive；旧enable_thinking相当enabled。minimax_m3 reasoning parser分离mm:think为reasoning与content，启用模式的prefill delimiter与parser默认plain-content分层看。工具参数是tool-call-parser minimax_m3并配auto tool choice；namespace XML支持递归schema coercion、多invoke和流片段是文档声明，不能代替实际parser/schema/stream验证。客户端PD请求走对应proxy，模型名取/v1/models实际结果。

精度分数沿用旧记录未随文档重测：GSM8K A3 96.36/H20 96.72的out/batch不同；AIME93.3 repeat2/95 repeat4也不是同试验。GPQA统一133000文字却有A3表行263000、out131072、batch64、temperature1.0，旧PO仍133000/out65536/batch8/.6；950 GPQA92.9和MMMU-pro78.9当前温度1.0，不能沿旧.6。TextVQA NPU72.75/GPU70.82，Video-MME NPU74.21/GPU73.41仅chunk1+2、32frames/8192out，非完整数据集或本仓结果。950三host的232请求、128k/1k、CC58、TPOT27.3ms/约1840TPS与Flashcomm1约1.8%也只属来源特定text-only配置。

HCCL buffer2048→1024MB或4K短输入batch32768→8192是优化起点，先确认通信/内存瓶颈再做受控对照，不能记为既得收益。回退恢复同一权重、runner、draft/KV、分区和池化状态，不能混M3.1预览或其他模型缓存。

326双语条目中304原串匹配、22人工差异、0仅历史上下文，15条空中文集中在1M预算/启动/验证，另保留24来源限定。当前英文新增LRU bullet超出PO原串的两条前缀，单列保留；原串匹配不是完整翻译、事实正确或HTML一致证明。Native三段仅0.32配置边界，不覆盖教程0.30环境、完整scheduler/capture实现或主线配对commit。本文未运行NPU、服务、通信、上游测试或Agent A/B。
