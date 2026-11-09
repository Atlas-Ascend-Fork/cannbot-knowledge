---
type: Guide
title: vLLM Ascend D2RH部署：Atlas 850E暂存容量、控制端口与超节点准备
description: 按Atlas 850E UBoE与DeepSeek-V4-Flash来源限定D2RH部署，核对pinned CPU arena、host-ready/H2D完成、rank端口、950PR/DT容器和物理NPU端点映射；保留译文版本差异及未知平台draft。 核对 CANN 9.2 前后 route.conf 的挂载条件。 核对HIXL>=9.1.0自动UB条件与HRN5
  provider共享库，区分hrn5.driver配置文件和实际库。
tags:
- task.implementation
- topic.kv_cache
- topic.data_movement
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/pd_disaggregation_mooncake_multi_node.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/pd_disaggregation_mooncake_multi_node.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_d2rh_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
created_at: '2026-10-30T12:11:39Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-02T01:11:40Z'
aliases:
- HIXL 9.1.0 自动 UB 超节点
- HRN5 provider 与 hrn5.driver 共享库
---

# vLLM Ascend D2RH部署：Atlas 850E暂存容量、控制端口与超节点准备


## 范围：具体Atlas 850E实例与未知平台标签

pd_disaggregation_mooncake_multi_node.md的D2RH章节只报告Atlas 850E UBoE、DeepSeek-V4-Flash配置已验证；其他硬件、网络和组合未验证。这是来源声明，本次没有真机复测或新增verified。当前未把这一整套850E窄配方可靠映射到知识库受控platform ID，因此本卡draft、platforms空；不能凭页内另有950PR/950DT容器章节，就将D2RH能力标为所有950或A2/A3已验证。

协议是P HBM→D host DRAM→D HBM，host阶段ready和D可forward分开；[传输设计](../integration/vllm_ascend_pd_transfer_lifecycle.md)说明第一跳完成可让P释放、D仍要等H2D。不是把KV写到外部Mooncake共享池，也不以host hit代替D HBM前缀命中。后续适配先锁定实际产品、HDK/CANN/HIXL、插件/vLLM及checkpoint/量化/布局，再另取平台和结果证据。

## DeepSeek-V4-Flash配方、图模式与请求容量

教程checkpoint路径为DeepSeek-V4-Flash-0731-w4a4c8，P/D各可见0–3、DP4/TP1/PP1、EP开启；两端block-size32、maxlen133120、maxseq32、memory0.9，P batch8192/eager，D batch1024/FULL_DECODE_ONLY。两端APC开启、hybrid KV manager保持开启，indexer_kv_dtype=fp8，dspark num_speculative_tokens=5且draft eager；不能换成A2/A3的INT8 indexer、DeepSeek-R1 MTP=1或单机Qwen无APC后仍称同一配方。

133120是总context上限，输入/输出/prompt模板token共同占用；“128k输入+1k输出”不是对任意tokenizer/template都自动通过的实测容量。model path、parser、served-name dsv4和权重revision/量化需同时锁定。降低gpu-memory-utilization可减少KV容量并影响D host staging，但要重新核对最大请求容量，不能只靠减少staging解决一切内存压力。

## pinned CPU arena：按所有Decode rank算实际内存

来源要求每D worker host KV容量对应其device KV cache并加对齐，而非复制整张卡HBM。实际_make_cpu_staging_caches按传入cache布局计算：仅P TP=D TP=1且PCP=DCP=1时保留同一named cache内的storage重叠别名；不同name不合并，即使其HBM别名相同。重叠判断为start<previous_end，相邻但不重叠的区间仍分段。其他分片先维持独立布局，不能从“共享storage”推导所有TP/CP配置都只计一次。

每region按2MiB向上取整，arena_owner另加2MiB-1字节以取得对齐起点，使用CPU uint8、pin_memory=true，持有owner避免view生命周期失效；保留别名的view恢复shape/stride，其他分支构建独立连续view。注册的是2MiB对齐owner范围，而不是每个tensor view随意注册。所读_get_register_regions仅kv_consumer创建D2RHCPUCacheManager(self.num_blocks)和CPU arena并加入注册范围；日志capacity_blocks/registered_bytes是局部阶段信息，不证明实际传输、可用连续主机内存或全部cache layout已验收。

预算按所有本地D rank的arena、对齐、模型加载、其他CPU内存与容器限制合计；HBM可用、host可用及pin/注册成功分别确认。不要将文档“同容量”简化成host bytes恒等于全部device tensor numel之和，别名、stride/span、named group与对齐都会影响实际数值。全套D2RH metadata、hash、调度、H2D完成和失败清理仍需逐路径证据，本次只读列明函数。

## d2rh_zmq_port与scheduler-ready：两个D侧控制面

示例HTTP为P8100/D8200，DP RPC12321/12322，kv_port36010/36020；D另设d2rh_zmq_port=38100（START_PULL，scheduler触发worker将KV暂存host）和d2rh_scheduler_ready_port=38200（worker通知scheduler host ready）。后者允许后续device block分配/H2D，不意味着H2D或decode结束。两个port搬控制消息，KV字节另走传输引擎；修改kv_port不会修改这两个base。

源码get_dp_port_offset=dp_rank*TP*PP*PCP；get_parallel_device_index=(pp_rank+pcp_rank)*tp_size+tp_rank。pull端口是base+dp_offset+device_index，scheduler-ready为另一base+dp_offset；DP4/TP1/PP1/PCP1因此分别38100–38103和38200–38203。另一个同host实例可用39100/39200仅在相应四端口均空闲时成立，HTTP/DP/KV/TE范围也需互斥。

不要按理想笛卡尔公式替换当前helper：其PP与PCP用和，单看函数在PP/PCP同时扩展时并不保证rank→端口唯一，例如(pp=1,pcp=0)与(pp=0,pcp=1)相同。此为静态公式边界，不证明该联合拓扑可到达或已复现冲突；先核对支持约束并枚举完整映射，不能拿DP4例推广到所有并行布局。

教程D2RH用每节点单个API端点，由服务分发本地DP，配先P后D的普通Proxy；不要再叠launch_online_dp.py启动第二批外部DP进程。/health只证明对应服务入口，Proxy生成结果还需remote stage/H2D/精度和取消失败证据。

## 850/850E/950PR与950DT：UB和Host RoCE准备分层核对

同页另有Atlas 850/850E/950 SuperPod（950PR/950DT）通信说明：默认UB super plane，自动ASCEND_LOCAL_COMM_RES={"version":"1.3"}要求HIXL>=9.1.0，两端启动前设置；UBG用["ub_rtp:device"]，UBoE用["uboe:device"]，均为ASCEND_GLOBAL_RESOURCE_CONFIG字面带点protocol_desc键的值。它们不是所有网络都无需配置的声明。

Host RoCE当前仍需每个物理NPU的endpoint JSON和ascend_local_comm_res_path；只有环境变量选择"roce:host"的简化方式明确未支持。文件名ub_endpoint_npu_<physical_npu_id>.json，comm_id取真实物理NPU对应的host RoCE IP；先确认映射才能按IP数值排序，不能用DP rank或visible序号猜地址。JSON示例version1.3/net_instance_id/endpoint_list中的protocol=roce、placement=host只说明该例，不证明任意JSON均被SDK接受。

MultiConnector将ascend_local_comm_res_path放outer extra与connectors并列，P/D prefill/decode参数和qos_priority仍放对应child；这是不同消费者的位置，不能为“统一配置”全部挪到子connector。容器endpoint目录两侧可不同，配置填container-side路径，文件名保持物理ID。

setup_ascend_local_comm_res所读helper从outer extra取目录，用visible_device_id_to_physical_device_id转换传入user_device_id，读取对应文件，FileNotFound/JSON解析失败显式抛错，成功压缩写ASCEND_LOCAL_COMM_RES。helper没有在此验证完整endpoint schema、生成文件或验证IP可达。worker在logical→visible转换与set_device后、硬件LOCAL_KV_COMM_RESOURCE capability允许时调用；不能把local_rank当入参，也不能从此gate反推所有产品映射或HIXL初始化成功。

## 950容器挂载、route.conf版本和中文差异

八设备950PR/DT示例要求兼容host driver的-a5镜像，openEuler另有-a5-openeuler；包含/dev/ummu、/dev/uburma、完整driver（含topo/950）、memlock无限等。所有host mount源先确认存在且类型正确，缺失-v路径可能生成目录，不能把容器起来当正确驱动库可用。本次没有运行任何容器/挂载/权限修改。

CANN>=9.2不再依赖/lib/route.conf；9.1/9.1.1默认device-only UB同样不需要，显式Host UB（ub_ctp:host）才需挂载，除非driver可由procfs提供路由。Host RoCE走独立endpoint文件；需要/dev/infiniband、匹配host driver和容器RDMA userspace的HRN5 provider共享库，hrn5.driver配置文件不能代替库本身。非privileged方案须显式设备/NET_ADMIN并另验，hiroce5诊断工具可选，不是数据面必需库。

本页中文140条有129原串精确匹配，11条需裁决：术语/大小写两处、源码构建改可选、自动UB新增HIXL下限、Host RoCE物理IP映射与完整容器/route.conf条件等。中文“route.conf可选”或旧局部挂载列表不能覆盖当前英文条件；译文/源码对照不证明整站HTML构建或真实部署已验证。
