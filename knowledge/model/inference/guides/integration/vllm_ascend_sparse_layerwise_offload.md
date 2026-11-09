---
type: Guide
title: vLLM Ascend 稀疏（Sparse）KV Offload：P 端层复用与 D 端热缓冲
description: 按中文资料裁决 A3 稀疏（Sparse）KV Offload 的 top-k 默认 -1 与旧 4096、MTP 负索引、DSpark V2 初始化及 TP0 主机池分配，保留 P/D、BF16、950 与 CP/PP 限制。 补Attention消费端的Copy-SFA逐step状态、device精确长度与tail恢复，以及fused_overlap的因果token展开、ForwardContext缓存身份、selection失效和TP0规划/写回等待。；补充P/D与scheduler/worker委派、DSpark门控及请求槽退役/回退的主机状态合同。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
- task.debugging
- topic.attention
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/layerwise_and_sparse_kv_cache_offloading.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/layerwise_and_sparse_kv_cache_offloading.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/layerwise_and_sparse_kv_cache_offloading.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/layerwise_and_sparse_kv_cache_offloading.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/sfa_remote_d2h_connector.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/layerwise_kv_offload_concept.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/sparse_kv_offload_concept.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/protocol.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/send_thread.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/layerwise_prefill_kv_offload.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/sparse_kv_cache_offload.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/sparse_kv_offload/sparse_kv_offload_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/sfa_kv_offload.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_kv_offload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/sfa_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/sparse_kv_offload/copy_sfa_topk_slots.py
  role: implementation
created_at: '2026-10-29T09:45:39Z'
updated_at: '2026-11-03T05:38:36Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- AscendSFAKVOffloadImpl
- AscendSFAKVOffloadMetadataBuilder
- prepare_copy_sfa_queries
- _prepare_fused_overlap_decode_common_inputs
- _invalidate_fused_overlap_selection_rows
- SfaRemoteD2HConnector
- CopySfaRequestStates
- CopySfaTopkSlotAllocator
- get_prebound_copy_sfa_slots
---

# vLLM Ascend 稀疏（Sparse）KV Offload：P 端层复用与 D 端热缓冲

## 范围与模型边界

仅解耦 PD，来源组合列 GLM-5.1、GLM-5.2、DeepSeek-V3.2，准备步骤明确 A3，本卡按该范围声明。D sparse offload 明确不支持950；其他稀疏模型尚未验证，不能用同名 backend 直接推广。共置 PD 和 HYBRID 模式不支持。

## P 端配置

shared-buffer layerwise Prefill offload 需 Memcache+eager，MultiConnector 组合 AscendStoreConnector producer 和 SfaRemoteD2HConnector producer。P 端不要设置 sparse_kv_offload_config。组合部署要求 P TP>=D TP 且整除。

layerwise_num_shared_buffers 默认等于 cache-bearing 层数，省略不产生跨层复用；显式设置较小值才复用。independent_layers 默认[0]保留额外专属缓冲，all 关闭复用。检查 reuse merged descriptors 日志和实际分配，不能把默认层数当节省显存。

## D 端配置

仅 D 端开启 sparse_kv_offload_config，使用 SfaRemoteD2HConnector consumer。主 SFA KV 必须 BF16，不支持 C8/TQ4；indexer_kv_dtype=int8 是独立配置，不能当主缓存C8。支持 D DP/TP，不支持 CP 或 PP，与 PreemptOffloadConnector 互斥。

topk_buffer_size=-1 派生为 (1+num_speculative_tokens)×2048；默认 Copy-SFA 显式值需256倍数、至少此值且不超过32512。dram_size_per_dp_GB 默认110GiB，TP共享、不同DP独立且需容纳完整KV，不能按每卡/总节点误配。D 端从 kv_port 起预留 DP×TP 连续端口。

## 验收、失败与回退

先核对完整 host 池、连续可分配内存、热缓冲与独立层，再用真实 sparse 模型比较输出与传输。offload.initialize 分配失败先查 host 内存和碎片/部署条件，不一律增 GPU memory utilization。对照无 offload、仅P、仅D、组合的 HBM、RAM、TTFT/TPOT 和带宽，保留代理地址可达性。关闭两侧对应路径后恢复常规 PD；本次未运行 Memcache 或 NPU。


## 复用与原生算子接入约束

共享物理层缓冲必须同时等待Memcache save和D端远程read完成，不能按逻辑层名或P forward结束提前覆盖。非对称TP的零块contributor也必须ack；握手timeout不能替代每层read gate的deadline，具体探针见[共享槽等待诊断](../../runbooks/runtime/vllm_ascend_sparse_buffer_ack_wait.md)。

默认fused LIM/Copy-SFA依赖_C_ascend中的npu_fused_lightning_indexer_manage、npu_fused_quant_lightning_indexer_manage和npu_fused_scatter_copy_sparse_flash_attention。Copy-SFA的host KV输入是已注册MemFabric内存的CPU tensor视图，其余输入留NPU；普通CPU tensor不可替代这些视图。INT8 indexer的C8 LIM使用Hadamard Q/K与FP16反量化scale，不能把FP8 indexer接到此INT8专用路径。新算子完整Host/Device分析仍需对应源码producer，本文不替代。


## 中文部署步骤的阶段和单位

layerwise_and_sparse_kv_cache_offloading.po的39条有效译文均匹配当前英文，包括PD-only、Memcache+eager、主BF16/独立INT8 indexer、950不支持和MultiConnector内PreemptOffload互斥条件；仍不能推导所有新模型、code blocks、网站构建或NPU结果均已验证。源码/设计中更细的HYBRID、PP和共享槽合同仍按本卡既有实现边界处理。

准备步骤“Decode无额外操作”只指该Preparation小节，不免除后续D端sparse配置、host池、连接器、连续端口和可达地址检查。P用独立MetaService进程及每Prefill节点的MMC_LOCAL_CONFIG_PATH；mmc-meta/mmc-local中world_size=256、dram.size=10GB与端口5000/6000是示例，不与D端每DP默认110GiB混成同一池预算。

P侧layerwise_num_shared_buffers=3是显式较小预算例子，专属层另占buffer，未用槽位不分配；看到reuse merged日志只证明该路径报告复用，不证明安全等待、实际HBM节省或性能改善。D侧keep_device_kv_cache=true仅调试保留完整device KV，不能继续按生产offload节省量估算；显式topk值不因存在投机自动放大，仍须满足Copy-SFA约束。

Sparse KV offload offload.initialize failed首先按连续host内存、MemFabric准备和真实DP预算定位；降低DP是改变部署容量的候选，不是所有错误的统一修复。P/D分别就绪后才启动layerwise proxy，多节点通告可达地址；0.0.0.0是监听语义，示例127.0.0.1/9000不能直接承担跨节点路由。代理响应、buffer ACK/门限、真实传输和输出正确分别留证，本批未启动服务或改主机配置。


## 中文设计、历史SFA译文与物理缓冲预算

设计layerwise_and_sparse_kv_cache_offloading.po的76条译文均匹配当前英文。另完整裁决sfa_remote_d2h_connector.po的66条历史译文；该PO的同名英文已不存在，不能据它恢复一个“当前官方英文页”或以其裸ACK描述代替当前wire协议。旧文中的KV Connector V1是接口代际，不等于只支持Model Runner V1；当前设计明确Sparse Decode覆盖MRv1/MRv2，实际模型/构建仍另验。

两张原概念图layerwise_kv_offload_concept.png和sparse_kv_offload_concept.png仅显示四个示意层。白色表示offload到host，粉色表示device驻留；Prefill图分别标offloading/computing/onloading，Decode图是分散热条目。图中颜色比例不是实测HBM占用、LRU命中率、带宽或固定buffer数；透明底图通过普通白页PDF显示检查，原始文件未改变，预览图不作为新来源。

对同规格、等大小的N个cache-bearing层，I个独立层加B个共享buffer时，main物理buffer数是I+min(B,N-I)，main占比近似该数/N；例如N10/I1/B3为4/10，只是该假设下的整数算术，不含indexer、固定分配或实际显存。规格不兼容不能共享，MTP层也参与规划；按实际descriptor验证，不从层数直接算所有cache字节。

## 四个存储区和两种完成条件

组合路径分P NPU复用buffer、P Memcache host池、D完整main host池、D rank-local indexer和每层hot top-k四区。P→D main以层/块range进入D host，indexer/LIC8 scale进入D NPU；D新增token行先追加host，再经top-k驻留查找只搬miss行并重映射为hot槽。TP0分配/写D共享main host池与每个TP rank持有所需indexer，是不同所有权，不能把host池复制数与indexer复制数混算。

物理buffer完成允许P覆盖先前地址；请求完成才允许D决定进入推理或处理失败。前者同时等Memcache save与所有必要RD2H读取，后者等映射到D的所有P贡献者最终层通知、以及所需D ranks的终态。终态失败不是允许消费坏KV，数据读失败将目的地视为无效并传播错误，不承诺已写字节事务回滚。

非对称TP令ratio=P_TP//D_TP、d_rank=p_rank//ratio、group_member_idx=p_rank%ratio；每组仅member0传对应main份额，indexer/scale贡献范围取并集。零块贡献者仍需ack；重复final信号不应推进计数。共享buffer的completion按实际物理storage slot区分main和indexer，不能只看同名逻辑层的事件。

## 历史ACK与当前握手、等待和地址边界

所读当前protocol.py定义SFAPD_PROTOCOL_VERSION=1和MF_META_ACK；_send_mf_meta发送版本及producer PP rank/size。裸ACK只接受于PP=1，PP>1要求结构化(MF_META_ACK,version)，不匹配会失败。它说明transport握手已有PP字段，不能解除当前Sparse Decode的CP/PP禁用。历史PO的tuple-length兼容描述不足以承诺跨任意分支互通。

初始化MF_META握手的文档100秒，与每层READ_DONE/READ_FAILED门控不是同一timeout。后者发现错误或发送线程已停会失败，但活线程丢ACK时没有整体deadline，可能一直等待，按[共享槽等待诊断](../../runbooks/runtime/vllm_ascend_sparse_buffer_ack_wait.md)保留每端点/层/slot时间线。历史文档提到metadata HTTP重试或状态兼容，本批未重新闭合全部HTTP调用链；不能把HTTP已送达当MemFabric读取成功，连接器数据读不自动重试。

控制端口按kv_port+全局dp_rank×D_TP+tp_rank隔离，host-local DP rank不是全局身份。main/indexer的块号、目标offset和存储注册地址分别核对，不把D逻辑块ID直接当P地址；类定义中出现兼容字段也不证明当前wire一定发送它。源码目录/测试文件名是后续阅读线索，本批未执行相应UT或tools/test_memfabric_pd_read.py。

## 协议可用、算子ABI与功能范围

memfabric_transfer_protocol由配置选取，sdma默认与device_rdma面向A3，device_urma是950PR/950DT的connector协议；存在该协议不代表Sparse Decode能在950运行。当前设计要求P/D协议相同，950的keep-device-cache/overlap也不能绕过offload guard。

Copy-SFA默认需三个_C_ascend符号，LIM C8的19参数管理ABI接int8 Q和FP16反量化scale；它不是FP8 indexer路径。注册MemFabric的CPU视图与普通CPU张量不等价。源文件、绑定存在、成功导入与真实设备算子正确仍是不同证据；本批没有编译或运行kernel。MooncakeLayerwiseConnector缺逐buffer completion provider，不能直接代替RD2H来复用共享层buffer。


## 已撤下单页的共享复用与 Sparse 配置纠偏

layerwise_prefill_kv_offload.po的48条和sparse_kv_cache_offload.po的26条历史译文均无同名当前英文；对照当前组合部署指南、设计与所列配置/manager代码片段处理，不把历史链接当可用当前页。前者专用P端Memcache+eager/producer和完整signature复用仍有当前组合依据；旧kv_both“功能兼容”不开放当前组合共置部署。

跨层共享复用不同于仅use_layerwise=true。N个同规格cache-bearing层含MTP，I专属、R=N-I、B共享预算，R>B才有实际复用；负索引按完整base+MTP布局解释，-1可指最后MTP而非最后base层。多signature各自建池，不能把状态/packed/pre-shared descriptor也按同一共享池公式复用；该限制不等于后端所有非共享layerwise路径都不支持Hybrid。

复用层须重载完整缓存前缀，因为旧物理地址已可被别层覆盖；独立层只恢复未在HBM保留部分。非块对齐的request-scoped partial保存/恢复与全局持久完整块对象分开，不能让一个请求读到另一请求的尾块。主缓存节省比例、indexer/scale与实际页面字节分别核算，日志宣告reuse不替代完成门控证据。

历史Sparse页把dram_size_per_dp_GB标成bool且默认128，把topk_buffer_size默认4096并称应大于index_topk；当前SparseKVOffloadConfig声明int容量默认110、topk默认-1按(1+num_speculative_tokens)×2048派生，显式值不自动扩张，基本检查拒绝小于topk，另有前述Copy-SFA倍数/上下界合同。字段名GB在manager按1<<30换算为GiB字节，不能当十进制GB。

所读manager先算对齐后的planned_pool_size_bytes，超过dram_limit_bytes即报错；实际OffloadConfig reserve_size/alloc_size用规划预算内的值，仅TP0分配CPU池，其他TP alloc_size=0。把110GiB×DP当节点上界/规划估算，不称每个TP实际都已分配110GiB，也不通过扩大热buffer解决host完整池超额。

历史MRV1-only和未来V2描述已过期；当前设计涵盖两代runner，DSpark 另在当前配置中明确要求 V2 远端 prompt-context 初始化。旧SFAPDCpuOffloadConnector用当前SfaRemoteD2HConnector入口核对；临时MemFabric分支、driver>=25.5.1与clang/OpenMP替换计划不当所有当前构建统一依赖。旧GLM-5.2 topk2048约2MB是该例的估算，不是任意batch、dtype或speculation的固定传输字节/TPOT承诺。本批未编译、加载算子或调用offload.initialize。

## Attention消费端：PD角色与两条fused路径

补充Main ceac固定版本sfa_kv_offload.py1637行和专项UT489行全文、SFA父选路与manager明确选段的静态阅读。原A3部署/950与CP/PP限制继续成立；本节不增加平台验收，不证明外部kernel、Mapped CPU内存或graph真机正确。未导入或运行上游/测试、编译、JIT、SDK或NPU。

SFA工厂在offload enabled时同时选择专用builder与impl；impl拒绝context parallel和C8/TQ4 packed主缓存，并强制native预处理，禁用该路径的PROLOG_V3/MLAPO。PD decode consumer必须consumer=True且producer=False，不能靠名字或kv_both得到该身份；只有它可把规定短边界请求当decode处理，长prefill仍不能混入常规D服务。

decode只计算当前NoPE/RoPE，不保留完整NPU main页；新KV交manager写完整host池，fused Copy-SFA还写当前hot/tail行。prefill/mixed仅供keep_device_kv_cache调试：先走父NPU页写，再D2H提交及按新增token更新hot/tail。这条调试路径会读取CPU长度/生成动态索引，不能当正常decode无同步或graph收益证据。fused_copy_sfa_enabled优先；否则fused_overlap可接decode，余下父路径要求保留完整device KV，不能把fallback当免费恢复。

## Copy-SFA：容量、step身份与精确长度

Host要求TopK2048、配置query width=1+投机token数在1..14，hot预算至少width×2048、最多32640且256对齐，因此有效最大对齐值仍为32512；hot预算另须整除真实block size。head不足8时补零到8并只返回原heads，其余接受8/16/32/64/128；这不将FlashMLA的8/12/64/96集合通用于Copy-SFA。

builder为target与每个draft step保留不同CpuGpuBuffer/device向量，避免多个metadata先构建后执行时互相覆盖；LIM历史bank另按target和物理MTP层区分，bank不是draft step的别名。host只上传request pool slot、activity和query边界，缺失或非CPU镜像直接拒绝；seq/prefix/cache/logical长度留device，不能用投机拒绝后仍乐观的CPU seq_lens覆盖它们。

prefix向下按128对齐；短序列走dense行，长序列按hot预算加双块256-token循环tail定位，inactive行用独立dummy pool并把真实slot置-1。只有明确rollback恢复标志才生成H2D tail descriptors；正常PD consumer的prefill tail已D2D就绪，graph replay不能重复恢复。尾复制源/目的offset与长度按NoPE/RoPE各自字节宽展开，不能只复制一个分量或将逻辑token位置当地址。

LIM量化indexer分支需要INT8 query/key和FP16反量化scale，并与BF16 selector使用不同符号。step0保存的TopK、logical/cache extent可由后续MTP复用，但必须随活跃请求一起compact，后续复用不运行LIM或推进其历史；长行保留选中的C预算，短行保留完整dense extent，不能给复用结果额外加tail。共享indexer owner在模型初始化绑定，未绑定不能凭skip_topk跳过选择。

绑定host/device base地址发生在cache注册后、capture前；LIM源/目的映射、miss列表和Copy-SFA输出互为一组协议。换backing、pool槽或层owner后不能只保留地址tensor继续执行。这里读到Host调用与状态生产，LIM/Copy-SFA Device实现及真实cache一致性仍需独立验证。

## fused_overlap：TopK、因果展开与缓存身份

TopK输入归一到INT32三维，可接2D或展平正确的BSND；token数、head整分与配置TopK上界先检查。实际external planner再要求一个TopK head，selection容量按配置最大decode rows与resident blocks预留；超容量且capture正在进行时拒绝重分配，不能在图中偷偷替换selection地址。所需npu_fused_sparse_attention_overlap按_C_ascend、custom、torch_npu顺序查找，符号存在不等于ABI与设备实现已验收。

MTP将每token当一个TND batch：visible KV=请求seq_len−请求query_len+本地query offset+1，Q累积为1..T，block table按token_to_req展开。不能让块内所有query看到相同的最终KV长度。非capture预检检查映射范围、Q末值和正visible长度；capture跳过部分值检查，所以必须在捕获前建立有效输入合同，不能把未触发检查解释为任意mapping有效。

公共decode inputs缓存在当前ForwardContext，key含T/B、TopK维数/dtype/device及request、mapping、table和长度tensor地址。相同forward内各层复用，下一forward重建；同地址内容原位变化不改变key，不能把该缓存提升为跨step全局缓存，也不能在同一forward中随意改输入后期待自动失效。

selection状态按真实request ID失效，且清除本次重写窗口[seq_len−query_len,seq_len)及>=seq_len的历史命中；同时失效mapped membership控制区。单清TopK数组或仅按当前row位置识别请求不足以防止槽复用/投机拒绝后读旧KV。正常external planner已准备时不再走本地fallback invalidator；两条路径的状态所有权必须匹配。

## TP0规划、current注入和写回完成

manager的完整CPU KV与INT16 membership由TP0拥有，其他TP用广播恢复的非拥有GVA视图；必须保留实际注册owner，普通CPU tensor不可替代。external plan要求固定TopK形状、每token request/stable-prefix/visible长度及足够大的mapped INT16存储。skip_topk仅在已有前层owner、匹配token数/TopK等条件下复用其plan，不能只因层名相邻就假设状态可共享。

capture时TP0在专用plan stream等待输入就绪，将设备输入异步拷至host并enqueue planner，再广播plan metadata；eager调用同步planner，TP0异常状态也广播给其他TP并统一抛错。native planner与enqueue完成/错误语义没有在本节执行复验，不把Host返回True写成所有设备写入已完成。

实际顺序是prepare external plan→注入当前KV到selection→fused attention→等待当前KV writeback，再返回NoPE范围输出。capture时current注入等待plan stream，TP0收尾等待current-save stream；缺current KV直接失败。attention返回、D2H已发起或某rank局部完成都不能单独允许覆盖共享host/热槽，仍需沿manager及前文P/D完成协议确认寿命。

专项UT静态定义PD角色/短边界、rewrite失效、raw TopK与完整membership透传、plan→inject→fused→wait次序、每forward缓存刷新、C8 LIM dtype及分派断言，均未运行。诊断先关联request ID/pool slot/step/bank、精确长度/tail、TopK源目的与miss、plan owner及stream依赖，再比较参考数值和host/hot HBM、拷贝字节、TTFT/TPOT；不能把测试名、符号发现或开启overlap当性能结果。


## Connector角色与Copy-SFA请求槽的主机合同

`SfaRemoteD2HConnector` 的 scheduler/worker 与 producer/consumer 是两组独立角色。P 强制 sparse offload 关闭、D 强制开启；P scheduler 标记 requires_full_blocks_on_update_after_alloc。SupportsHMA、supports_layerwise_buffer_reuse=True 和 use_layerwise 默认 True 是接口能力与配置，不是共享层地址已经安全复用的证据。跨层复用仍需前述发送/读取门控。

scheduler 委派匹配、分配、metadata、所有 cache groups 的完成处理；consumer 才转交 connector_output。worker 在 producer 身份才额外 bind metadata，consumer start_load；P 的 wait_for_layer_load 从 `layers.N` 解析层号并等待发送，consumer 的 wait_for_save 则另行委派。save/on_kv_cache_written 在缺 metadata 时可直接返回，不能把调用次数当成功写出计数。

DSpark receiver 与 resident block table 只开放给 D worker，发送 draft KV 与产生 context descriptor 只开放给 P worker；configure draft layers 必须已有 worker。shutdown 对 scheduler/worker 各自调用存在的 shutdown，close 是其别名；没有组件不产生完成证明。

`get_prebound_copy_sfa_slots` 在没有 KV group、没有对应 getter 或返回空时给 `{}`。这与“已获得有效 PD 槽”不同。`CopySfaRequestStates.prepare` 每步先给 padded 行设置超出真实槽容量的 dummy 编号并清 activity；dummy 模式不分配真实所有者。真实路径要求 request ID 唯一、batch 均有 live/prebound owner、computed-token 数足够，检查预绑定范围与互斥，并禁止活请求更换槽。

新槽会把每个 LIM history bank 的对应列置 -1；新分配后的无效化与旧请求淘汰不同。remove_request 还记录 retired 集合，防止残留预绑定把已退役请求重新保活，真实重新进入 batch 后才解除该标记。容量为 max_num_seqs+2；`CopySfaTopkSlotAllocator` 另有 bind/release/free-list，不自动证明与所有 consumer 状态同步。

每请求按 block 向下对齐的 prefix 发生回退时，存在 prebound 槽才请求恢复 tails；若还跨越 hot_tokens 阈值，则生成该槽的 dense fill。tail geometry 对非正长度/块长或整块长度返回零尾，不能无条件复制末块。保留 request ID、槽、prefix 前后值、history bank、PD 预绑定和 restore/dense-fill 输出，才能诊断复用后旧TopK或投机回退。
