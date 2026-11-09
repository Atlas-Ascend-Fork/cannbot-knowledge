---
type: Guide
title: vLLM Ascend KV Pool：后端选择、命名空间、内存与故障边界
description: 结合当前中文与历史KV Pool页核对A2/A3/950后端能力、逐层依赖、SSD预取/驱逐和每进程预算，区分本地IPC与TCP、Yuanrong预注册与真实数据面证据；补充Qwen2.5-72B双节点多实例、Store别名、JSON与冷/热TTFT实验合同，以及107374182400字节即100GiB的预算。；补ceac后端能力校验、Memcache
  lazy/SSD rewarm及非逐层load_get统计窗口。
tags:
- task.implementation
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/kv_cache_pool_ascend_store.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/KV_Cache_Pool_Guide.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/KV_Cache_Pool_Guide.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/kv_cache_pool_ascend_store.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/kv_pool.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/yuanrong_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/pd_colocated_mooncake_multi_instance.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/pd_colocated_mooncake_multi_instance.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/ascend_store_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/lookup_key.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/mooncake_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/user_guide/feature_guide/kv_cache_pool_ascend_store.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/memcache_backend.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/memcache_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/metrics.py
  role: implementation
created_at: '2026-10-29T09:45:39Z'
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
- MemcacheBackend
- require_aligned_batch_results
- AscendStoreKVConnectorStats
---

# vLLM Ascend KV Pool：后端选择、命名空间、内存与故障边界

7d9e的scheduler factory及保存引用生命周期已有增量，见[7d9e运行时差异](../integration/vllm_ascend_7d9e_runtime_delta_contract.md)的AscendStore节；以下旧版本后端合同不自动代表新版本的bulk/逐层保存与reset路径。

## 适用范围与后端选择

来源明确支持 A2/A3/950，起始版本声明 v0.23.0；以固定提交的依赖表为准，不混用旧 release。AscendStoreConnector 把 KV 放入外部存储，PD connector 仍负责 P→D 传输，二者可用 MultiConnector 组合。Mooncake 提供池化、SSD/租户；Memcache 基于 MemFabric，A3 可选 HCCS/device_sdma；Yuanrong 适用于 Datasystem/Remote H2D 场景。

硬件与网络条件分开：来源 CANN>=9.1.0，950 HDK>=25.6、A3 按依赖组合>=26.0或>=25.5、A2建议>=25.5；A3 FabricMem/device_sdma 要求 LingQu>=1.5。950 还需 UBOE/UB 设备和配置可见。不要把某一后端安装成功推导为所有传输协议可用。

## 对象一致性先于性能

读写端须一致：权重版本、模型/布局 namespace、量化、block size、TP/PP/CP、transfer mode 与 cache_salt。strided MLA 的修正分段表示与旧 contiguous-range 不兼容；bulk coalescing 又使用 physical-page-major，不能与旧 component-major 或 layerwise 对象混用。总字节相同不代表布局兼容，重启 worker 不会失效持久对象；升级全部读写端并换 namespace/清理受影响条目。

Mooncake tenant_id 是 namespace/配额标识，不是认证；严格模式需注册包括 default 的全部租户，未启严格模式 tenant IDs 不隔离 placement。hybrid 的 kv_load_failure_policy=recompute 尚不支持，不设置为“任何读失败都可安全重算”。MultiConnector 的失败策略写在顶层。

## 角色、端口与内存预算

lookup_rpc_port 是本地 scheduler/worker IPC 标识，不能解决 V1 handshake/V2 scheduler 的 TCP 端口重叠；独立服务需唯一 IPC 标识并审计完整 TCP 范围。consumer_is_to_put、consumer_is_to_load 和 save_decode_cache 含义不同；save_decode_cache 只写完整 decode 块，不释放活动请求 NPU KV，且要求非 layerwise。PP key 兼容需描述实际 prefill 分区。

Mooncake SSD 分别配置 client 与 master；worker rank 子目录应互不冲突，独立服务 global rank 重叠时用不同根目录。每 rank SSD buffer 独立于 global_segment_size，BUFFER_OVERFLOW 不能只增 segment。A3 FabricMem buffer 要按1GiB对齐，预算至少 segment+SSD buffer+余量，max-num-batched-tokens 不缩减该 buffer。限额按真实每 rank 磁盘分配，不能默认每 rank 2TB。exist-trigger SSD prefetch 是额外能力，需对应 API；缺失时告警关闭，不能把 SSD offload 当成预取已生效。

Memcache host/device 协议有不同对齐，按所有 LocalServices 汇总 DRAM 与 UBS IO 内存；A3 进程分离部署先起贡献内存的 Memcache，再起 dram.size=0 的 vLLM。SSD force_new_disk 会清盘，不能直接将示例用于已有数据设备。memcache_dp_init_barrier 默认开启且全组一致；DP1/metadata-only/lazy 路径跳过，不能在按请求 lazy 初始化时强插 barrier。

Yuanrong 每节点 worker_addr 必须可达且指向本地 worker，Coordinator/etcd 二选一。Remote H2D 的前置条件见[既有指南](yuanrong_kv_pool_remote_h2d_ascend_prereqs.md)；新版本 HIXL/P2P_TRANSFER/FabricMem 的 device preregistration 有独立条件，不能从旧指南推导所有模式都需预注册。

## 验收、诊断与回退

先禁高级组合，在隔离池验证冷/热输出、真实远端 hit、部分块与 chunk 边界、失败策略，再逐项加 PD、图和异步。区分首次 HCCS 建链 warmup 与稳态收益；观察缓存命中、TTFT、传输、端到端吞吐和各进程 host/HBM。put 空间不足需 eviction headroom；get lease 过期需 TTL 覆盖传输；SEGMENT_NOT_FOUND 要检查客户端心跳及初始化 CPU 绑定；底层 HIXL 错误需 plog，不能一律扩大池。

回退停用目标 connector 并用隔离 namespace 的已验证部署；格式升级不能仅回滚一个 reader。主机大页、盘和驱动配置须按运维流程执行，本次未改系统、启动服务或复测性能。


## 调度/worker边界和历史设计的冲突

池化先计算on-chip prefix hit，再只获取池中额外命中的块，避免重复搬运；前缀连续性要求不能越过首个未命中块拼接后续hit。scheduler负责命中探测、分配后状态、connector metadata与request_finished的延迟释放；worker负责register/load/save/wait及get_finished的发送/接收完成，不能在HTTP结束就释放仍被异步操作使用的块。

同一commit的KV_Cache_Pool_Guide仍使用MooncakeStoreConnector(V1)旧名，写有“仅DRAM”“仅P端put/get”和get失败仅日志继续。这些与当前主来源的AscendStoreConnector、SSD/多后端、consumer写入及失败策略不一致，本卡把旧设计仅作为架构/历史约束，不将其限制升级为当前部署规则。特别不能按旧文静默跳过读取失败而接受精度风险；实际接口拼写、配置与失败策略须按当前实现/主指南核对。


## 中文旧设计不能替代当前KV Pool部署合同

KV_Cache_Pool_Guide.po的41条有效译文均与同提交英文msgid连续匹配；这只说明所读译文能在当前设计文档找到原文，不代表设计文档已同步当前实现。中文仍保留MooncakeStoreConnector/MooncakeStoreConnectorV1、仅DRAM、仅P端put/get以及get失败仅日志继续的叙述，须与前述AscendStore部署合同区分。SSD、consumer写入与失败策略不由翻译匹配率裁决。

对Agent的适配入口，Lookup Engine/Lookup Client、ChunkedTokenDatabase、KVTransferThread及移除LocalBuffer是该设计的架构解释；它们不是所有当前后端都有相同类名、线程数、零拷贝保证或固定收益。片上前缀先命中，再只取池中额外连续块；两层命中率、远端传输字节和最终请求时延分别取证，跨节点可见不意味着每次都更快。

源码适配时把get_num_new_matched_tokens、update_states_after_alloc、build_connector_meta、request_finished归scheduler，把register_kv_caches、start_load_kv、wait_for_layer_load、save_kv_layer、wait_for_save、get_finished归worker。设计中done_sending/done_receiving对应put/get完成，不能从request_finished或HTTP结束跳过实际异步完成。接口名称是此固定设计的阅读入口，真实签名、必选/可选和错误传播仍按所选原生/插件版本核对。

DFX节的“首个miss后不再查后续块”和“put失败后不继续后续块（可变更）”也必须标注设计来源，不能扩成所有后端通用重试策略。发现lookup存在但get失败时，不按旧文静默继续接受精度风险；保留当前配置/布局和失败阶段，沿目标connector失败策略取证。本批没有补测缓存收益、故障重算或外部Mooncake实现。


## 当前中文与历史改名页的裁决

kv_cache_pool_ascend_store.po的320条译文有311条与当前同名英文原串匹配，另9条存在实际变化；kv_pool.po的303条则没有同名当前英文，作为历史改名/重排资料对照，不恢复成另一套当前指南。逐条译文阅读不表示网站已按这些内容构建，也不代替目标SDK验证。

当前英文为Mooncake逐层路径增加>=0.3.14，为Memcache逐层增加memcache_hybrid>=1.3.0；非默认租户>=0.3.12、SSD>=1.2.0与基础安装0.3.11.post1分别针对不同能力，不能用一个最低版本覆盖全部组合。glibc>=2.35是Mooncake wheel条件，不是NPU型号识别条件。

中文MetaService参数的四个No已在当前英文改Yes：meta_service_url、meta_service.config_store_url、meta_service.metrics_url和log_level。保留实际解析器/后端版本确认，表格必填更改不证明插件入口已强制验证所有字段。中文旧lookup_rpc_port“每实例唯一端口”应按本地IPC标识解释；同一服务DP自动隔离，独立服务共享RPC目录时使用不同标识，不能拿它修复TCP保留范围冲突，也不把旧mooncake_rpc_port=0说明泛化为自动选择空闲TCP端口。

## SSD预取的额外依赖与数据保持

SSD Offload、exist-trigger SSD Prefetch、offload-on-evict是三件事。enable_ssd_prefetch要求先enable_ssd_offload且Mooncake提供ExistOptions；缺该API时告警并禁预取。省略ssd_prefetch_cooldown_sec/ssd_prefetch_dedup_ttl_sec保留SDK的5/30秒默认，0分别关闭该策略；只有显式字段才转发。配置任一prefetch knob会使用config-dict setup重载，该重载不接共享engine，Store自行创建TransferEngine，不能仍按全局共享引擎估算连接/资源。

低水位100GB×0.5只是在该例中50GB触发驱逐，不保证异步SSD写完。offload_on_evict把无LOCAL_DISK副本的对象排队并pin一个内存副本，offload_force_evict=false在无法入队时延后驱逐；队列和DRAM仍需余量，不当数据永不驱逐或故障持久化保证。只读端、writer和master的版本/模式分别核对。

worker拥有rank_<global_rank>子目录，scheduler不占SSD根目录；独立服务rank重叠需换根。storage_path already held by another live client属于实际客户端bucket实现，不能只查Master版本。client_ttl秒、KV lease毫秒、连接/传输timeout的实际单位分开；旧译文用1-eviction_ratio表示剩余空间，当前英文已删除该公式，按实际used/free与单次BatchPut需求确认。出现NO_AVAILABLE_HANDLE先分空间余量和对象批量，LEASE_EXPIRED先分租约/传输阶段。

## Memcache容量、分离进程与大页操作边界

ock.mmc.local_service.world_size是允许的LocalService上限，非vLLM TP×DP实际worker数；已连接后改值需按来源重启meta。ubsio.standalone.device_count数实际贡献DRAM的LocalServices，在独立进程部署时不直接等于NPU卡数或vLLM worker数。先按节点扣除OS、模型和池化DRAM，再算min(3072,floor(UBS IO可用GB/DRAM-enabled进程数))；200GB/4得到50GB仅静态示例，低于SSD下限5时不能继续套10/50推荐值。

旧kv_pool.po的max.dram.size=2028GB例不突破当前表[0,1TB]与按进程实际配置核对。A3独立进程部署先贡献内存，再以dram.size=0的vLLM加入；host_shm自身要求DRAM>0且HBM=0，不能把A3/HCCS的0GB片段搬到所有协议。Memcache DP init barrier的DP1、metadata-only和lazy例外保持，独立请求触发的lazy初始化不强插全组屏障。

主指南包含清大页/drop_caches、修改签名校验、privileged容器及force_new_disk清盘的展示步骤；它们是目标环境运维操作，不能作为Agent只读诊断的默认动作或盲目整段运行。不同后端对大页的需求分别核对：不能把950残留页清理步骤套到需要2MiB HugeTLB的Yuanrong Worker。本批未执行这些步骤。

## Yuanrong预注册的实际AND条件与配置类型

所读yuanrong_backend.py片段表明：有效enable_remote_h2d=enable_data_plane AND config.enable_remote_h2d；随后还需transport_backend精确为HIXL、enable_fabric_mem=false、enable_dev_mem_pregister=true，才设置_needs_dev_mem_pregister。收到ptr/length并实际调用register_buffer后，_register_buffers_if_needed才执行预注册并标记完成。只选HIXL不是充分条件，默认toggle=false；P2P_TRANSFER/FabricMem始终跳过。metadata-only scheduler禁数据面，不能从其初始化日志推导设备注册成功。

YuanrongConfig.from_file用bool(...)转换相关字段而非严格布尔验证；JSON字符串false非空，不能当关闭。使用JSON true/false并记录有效配置；不把PreemptOffload真bool校验的结论搬到此解析器。YR_CONFIG_PATH必须设置且JSON须object，worker_addr解析/可达与SDK.init/数据面成功分别验证。文档环境变量说明不能替代此处传给HeteroClient的显式值；本批未验证外部SDK对环境变量的读取/优先级。

HCCS client需在启动前显式DS_RH2D_LINK_TYPE=HCCS，Worker的HCCS与client HIXL、ROCE与P2P_TRANSFER对应，HIXL RoCE direct另需两端条件。request_timeout_ms=0沿SDK连接timeout行为，而get_sub_timeout_ms=0是不等待对象；两者不能合并为“无限等待”。支持ASCII的1024字节键与规范化hash后缀用于诊断，不将raw key直接当后端对象标识。40GiB/2MiB=20480页是容量算术，不是已预留/可用连续内存证明。

DSv4需核对--no-disable-hybrid-kv-cache-manager；来源约300GB/1M token包含全部压缩比族状态，是特定描述而非所有模型的每token常数。成功返回choices、打印Available KV cache memory或完成租户查询，各自只证明对应入口；热hit、部分块/布局正确与真实性能仍独立验收。


## 双节点多实例教程：PD共置与旧Store别名

pd_colocated_mooncake_multi_instance.md的实例是两台Atlas 800T A2、Qwen2.5-72B-Instruct，每台一个TP4实例、各用设备0–3，P/D在同一实例共置。它不是“一个节点只P、另一个只D”的1P1D，也未使用每台全部八卡。服务8002、BF16、max-model-len=25600、max-num-batched-tokens=4096、gpu-memory-utilization=0.9与HCCL_INTRA_ROCE_ENABLE=1属于此例；各节点模型revision、tokenizer、cache namespace/布局和真实TP仍需一致。

教程的MooncakeConnectorStoreV1、kv_role=kv_both、use_layerwise=false、load_async=true、mooncake_rpc_port="0"及register_buffer=true应按当前源码解释。kv_transfer/__init__.py仍将MooncakeConnectorStoreV1与AscendStoreConnector注册到同一个AscendStoreConnector类；构造器对旧名告警推荐新名，未将旧名删除。默认backend为mooncake（转小写），角色可写条件是producer/both、consumer_is_to_put或save_decode_cache；不能只凭名字推断运行了旧Store实现。

注册表另将MooncakeConnectorV1指向P2P旧V1模块、V2/Pull指向另一模块、MooncakeLayerwiseConnector指向逐层P/D模块，不能与池化use_layerwise混用。_register_with_class_name_alias为名称与类名不同的指定connector补class alias，服务MultiConnector按类名重建统计；override显式处理config-name，类名冲突先告警再替换。此helper用于UCM和native offload等所列调用，不表示表内所有connector都自动经过它，更不能用“注册成功”证明外部依赖/传输可用。

教程说true适合单节点、false适合跨节点，只是该配方说明，不能作为当前所有后端的物理限制。当前requires_piecewise_for_cudagraph由use_layerwise决定；scheduler/worker所读初始化片段均读load_async，异步bulk与逐层hook分开，mamba同步bulk与逐层copy-after-load标志也不同。启用一个true不证明重叠已经发生。

## lookup_key.py：端口0是IPC名字，失败与重置分别验收

get_zmq_rpc_path_lookup先取lookup_rpc_port，否则兼容mooncake_rpc_port并告警，缺省0。实际地址是VLLM_RPC_BASE_PATH下的ipc://.../lookup_rpc_port_<值>_dp_rank<serving data_parallel_index>，不是向OS申请一个空闲TCP端口。DP serving index不等于dense引擎重置后的compute rank；共享目录的独立服务仍需不同标识。此隔离不保证V1 worker handshake/V2 scheduler TCP范围互斥。

LookupKeyClient独占ZMQ context，REQ接收RCVTIMEO=1000毫秒；ZMQError时记录、close(linger=0)、term context并返回0 hit，已closed的后续lookup也直接0。此分支会把探测失败表现成miss，不能只看命中率就下结论“数据已被逐出”。成功分支把响应字节转整数，不将它描述成所有错误都严格验证并返回0。server收到LOOKUP时用use_layerwise=false传给worker.lookup_scheduler，消息携带token_len、KV group、hbm_hit_tokens和hash hex；RESET调用reset_store，未知/处理异常返回RESP_ERR，接收失败则退出而不合成响应。

reset的docstring提出drain queued puts后remove_all(force=True)，但真正池清理细节不在本批读取范围。client.reset没有lookup同样的ZMQError兜底，不能将超时等价成reset成功；reset可能影响共享池数据，消费Agent先确认namespace、范围和在途操作，再按部署流程执行。

## Mooncake JSON、内存注册与容量的版本核对

教程Master端口50088、eviction_high_watermark_ratio=.95、eviction_ratio=.05，JSON用P2PHANDSHAKE、protocol=ascend、device_name空串、master_server_address以及global_segment_size=107374182400。后者是100GiB（100×1024³字节），不是十进制100GB；需要按真实贡献内存的进程数累计预算，不能只看单份JSON。预装镜像或可选Mooncake v0.3.9构建示例不是当前SDK兼容性证据。

所读MooncakeStoreConfig.from_file先读JSON；MOONCAKE_MASTER与MOONCAKE_GLOBAL_SEGMENT_SIZE只要非None就覆盖JSON相应值，空字符串也会覆盖而不是自动回退。protocol缺省ascend、device_name缺省空串、preferred_segment缺省false、prefer_alloc_in_same_node缺省true；MOONCAKE_CONFIG_PATH未设置会直接ValueError。相关SSD开关用bool(...)转换，字符串"false"是非空真值，必须传JSON布尔值。

_parse_global_segment_size接受GB/MB/KB/B（大小写不敏感，实际乘1024幂）和裸字节字符串，数值字符串经float乘单位再int；直接int原样返回，非字符串其他类型尝试int转换。故不能将docstring当成已完成所有非负/严格类型检查：例如负整数分支未拒绝，bool亦属int，非整数数值可能截断。Agent生成配置应先确认正值、单位、精度和总预算，不依赖此宽松解析器替资源校验。

pool_worker.py所读缓存注册hook实际调用m_store.register_buffer(ptrs,lengths)，再验证相应逐层支持并启动线程，该片段不以教程的extra register_buffer=true为条件。MooncakeBackend.register_buffer对独立TE或prefetch dict-setup走store逐buffer注册，失败记录ret；非FabricMem的其他分支走global_te，FabricMem另有路径。不能把旧表的一个开关当成注册成功的充分证明，也不把历史0.11.0rc3的补丁当当前所有后端必需操作；历史诊断见[后端不兼容](../../runbooks/runtime/vllm_ascend_mooncake_connector_backend_incompat.md)。当前注册/SDK错误传播及所有布局仍需目标路径证据。

## 冷、local DRAM与remote DRAM的TTFT实验合同

教程描述Dataset A为完全随机、input=1024/output=10、100请求、并发25；先Instance1冷运行得TTFT1，再送Dataset B试图驱逐A的HBM前缀而保留DRAM，重放A到Instance1得TTFT2，发到Instance2得remote DRAM的TTFT3。来源结果为2322/739/948毫秒。这是教程报告值，不是本次测量或新版本/全部硬件的收益保证；三种缓存状态必须通过HBM/池命中、远端读字节及逐出时间线独立证明，送过B不自动证明A仅剩DRAM。

所附AISBench配置为VLLMCustomAPIChatStream、request_rate=0、retry=2、batch_size=25、max_out_len=10、temperature=0、ignore_eos=true，但命令选择gsm8k_gen_0_shot_cot_str_perf，与文字“完全随机Dataset A”没有在页内闭合成同一负载。复现需保存实际数据、样本顺序/seed、长度分布、prompt/template、是否重试、端到端成功与TTFT统计分母，再分别测冷、local、remote；不能拿2322/739/948反推任意模型的吞吐、TPOT或通用3–10倍加速。

该教程PO共66条，其中64原串精确匹配，2条只差行折/缩进（hccn.conf及success/UP说明）；单机PO42条全部匹配。译文与源码核对不证明整站HTML构建、真实运行或缓存收益。本批没有启动Master、Proxy、vLLM、网络探测或AISBench。


## 2026-11-03 main 增量：Memcache 依赖与初始化同步变化

本节固定3164adc8fe75892fbf7f99f524bb72fddf1e6efd，只读KV Pool文档及Memcache backend相对ceac的完整变更hunk，没有宣称新版本1715行指南、backend整文件或重构后的pool worker已全文生产。新的Memcache软件要求为memfabric-hybrid>=1.3.0且memcache-hybrid>=1.3.0，不再只按旧SSD1.2/逐层1.3选择单一依赖；A3 device_sdma仍需LingQu Computing Network>=1.5。版本下限不提供具体模型/协议组合运行结果。

旧ceac正文的memcache_dp_init_barrier是旧合同。新MemcacheBackend删除dp_init_barrier构造实参、类型检查、_dp_init_barrier派生及初始化后的get_dp_group CPU barrier；新文档也删除相应配置段，整个新提交vllm_ascend代码搜索不再出现旧配置名。不能继续把旧flag或旧日志当新版就绪门槛，也不能把它静默未消费解释为已获得旧同步保证。这里没有闭合上层所有同步，删除一个backend barrier不等于所有初始化均无同步。

新backend把layerwise_data_plane=gva、bind_layerwise_keys和make_partial_key放到类接口，旧模块级约定不是新扩展backend的完整契约。已读变更保持key格式的来源说明，但未闭合外部服务或全部调用者；不能自行改wire key来迁移。就绪与故障仍核对各worker初始化、PP成员、真实load/wait/error及恢复输出，不能以首HTTP响应替代整组成功。未执行服务、安装、传输、UT或设备验证。


## ceac基线：后端能力、Memcache初始化与测量合同

本节补齐 ceac 的 Python 可执行结构阅读，和上节 3164 增量分开解释；没有运行 SDK 或复测 NPU。

backend_map 按 mooncake/memcache/yuanrong 延迟导入，只有前两者配置 layerwise_protocol；协议只将 block_key/gva 识别为数据面，未知值返回 None。可选 validate_topology/runtime hook 不存在时不调用，不构成隐式支持。基类 Backend 的租约、readable、range/commit 等默认接口抛 NotImplementedError；子类必须实现具体所需能力，不能只继承基类就被判定兼容。

`require_aligned_batch_results` 要求每 key 一项 Integral，显式拒绝 bool、None、长度不等和非整数；不能把零个结果当整批成功。qos_priority 必须是 Python int、非 bool 且在 0..4；Memcache 将它写入进程环境 MF_DEVICE_UB_QOS，并另对环境字符串转 int 验证。该注入具有进程级副作用，不能当 per-request QoS。

ceac Memcache 的 lazy_init 只有实际 MMC_LOCAL_CONFIG_PATH 文本中 protocol 精确等于 device_sdma 才生效；不是任意 lazy=True 都延迟初始化。构造的 DP barrier 开关要求真实 bool，且 DP>1、非 lazy，并在 init_bm 路径才用 CPU group barrier；scheduler client 用映射后的 device、init_bm=False。初始化成功后还有固定 0.1 秒 sleep，它不是 peer ready 探测。

register_buffer 暂存一份指针/大小并在初始化后逐项注册；该注册路径 zip 不做等长校验，也未核对每项返回值。unregister_buffer 则先核对等长。不要把调用完 register_buffer 当所有内存已成功注册；并发注册、换缓冲和 close 后状态需按有效 owner 取证。close 清 store/初始化标志，但不重置所有 lazy 配置。

### SSD存在、可读与rewarm是不同阶段

lazy 未初始化时 exists 返回全 miss、readable 返回全 False、key-info 返回空；get 返回 None，put/alloc 可触发 ensure_initialized。看见 miss 不直接归因为对象逐出。

batch_is_readable 要求 key-info 与 key 数一致、size>0、GVA 非空且首个 GVA>0；损坏 metadata 可抛 BatchResultShapeError，不是所有异常都静默变 miss。for_load=True 的 key-info 会对“有 SSD 副本但没有正 GVA”的对象分配 NPU scratch、注册、batch_get_into(COPY_G2L)、finally 注销，再重新查询 metadata。注册或回读失败返回整批 None；SSD存在不等于已可按 GVA 读取，也不能省略 scratch 内存预算。

普通 get/put 捕获 SDK 异常并返回 None/False 或逐项成功布尔值；日志里的首次 DSV4 失败预期只说明该分支提示，不能把实际失败视为正确恢复。batch_alloc/add/remove lease/write_finish 是不同后端操作，具体成功值和上层消费逐条核对。

### AscendStore统计窗口

只记录 operation=load_get 的非逐层 Backend.get worker 耗时与 key 数；不是完整 lookup/load、逐层传输、scheduler排队或端到端 TTFT。聚合会合并 durations/keys，delayed_release_requests/blocks 则覆盖为收到的快照，不把多次快照相加。Prometheus 的 load_get_duration_seconds histogram、load_get_keys_total counter 与 delayed_release 两个 gauge 分开使用；零样本不能证明没有传输或延迟释放。
