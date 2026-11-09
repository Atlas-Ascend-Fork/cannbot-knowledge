---
type: Guide
title: vLLM Ascend MooncakeConnectorV2：角色ABI、握手回调与端口边界
description: 适配MooncakeConnectorV2时区分工厂别名、KVConnectorBase_V1与P/D角色，核对多group/PP握手、no-op层接口和按真实TP/PP/PCP计算的完成及控制端口边界。 核对MooncakeConnectorV2的connector注册、缓存layout选择和register_kv_caches的dtype校验委托边界。
  补包导出、PP/PCP/TP结构校验、请求metadata及MiB/串行耗时统计口径。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/connector.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/GLM5.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/base_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/base_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/pull_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/pull_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/metadata.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/stats.py
  role: implementation
created_at: '2026-10-31T01:35:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T05:39:27Z'
aliases:
- MooncakeConnectorV2
- MooncakePullConnector
- MooncakeBaseConnector.register_kv_caches
- MooncakeBaseConnector.get_required_kvcache_layout
- MooncakeTransferMetadata
- MooncakeTransferMetadataGroups
- MooncakeKVConnectorStats
---

# vLLM Ascend MooncakeConnectorV2：角色ABI、握手回调与端口边界

## 范围与消费任务

适配vLLM KV接口时，区分连接器工厂名称、Native基类ABI、scheduler/worker角色、业务P/D角色和Model Runner版本。本卡主证据是ceac提交mooncake/connector.py全279行，另读注册段与五个构造/端口选段；完整Native基类、metadata/peer布局、worker传输及清理尚未闭合，硬件范围未知，保持draft/platforms=[]。模型专用参数见[GLM-5.1部署](../models/vllm_ascend_glm51_sfa_deployment.md)，通用P/D生命周期见[传输合同](vllm_ascend_pd_transfer_lifecycle.md)。

## 名称、基类与角色是三层契约

注册表MooncakeConnectorV2指向mooncake.connector.MooncakeConnector。模块实际令MooncakeConnector = MooncakePullConnector，继承MooncakeBaseConnector，再继承Native KVConnectorBase_V1和SupportsHMA；名字V2不代表Native基类名也变V2，更不能据此推断Model Runner V2已启用。MooncakePushConnector虽在__all__导出，构造立即NotImplementedError，不能拿存在类名当可部署push路径；MooncakeLayerwiseConnector另属不同实现。

Base facade先调用Native super，断言kv_transfer_config和engine_id存在，并把scheduler/worker槽初始化None。Pull facade按KVConnectorRole.SCHEDULER实例化PullConnectorScheduler，WORKER实例化PullConnectorWorker，其他角色ValueError；两个构造均调用各自base。这里的SCHEDULER/WORKER不是kv_producer/kv_consumer。所读worker/scheduler base都要求producer与consumer恰有一个为真，否则ValueError；worker另要求local DP rank非None。不能通过改成kv_both绕过实际P/D协议约束。

## Native缓存与布局接口

get_required_kvcache_layout在model_config缺失时warning并返回None，MLA也返回None，因为其无独立head维，不能说MLA被强制HND；其他返回HND以直接D2D。None表示不由本方法指定，非“缓存不需要布局”。

supports_divergent_local_hybrid_hits返回True，get_loaded_kv_cache_group_ids返回Native _kv_cache_config.transfer_group_ids。注释说P/D恢复请求自己的transfer组，供skip-zeroing及V41 SWA窗口判断使用；它不是旧0.30 replay backport兼容证明，也不表示所有HMA组、混合布局或回放组合已验证。适配必须核对Native实际读取此接口的条件、返回的组与真实恢复块，不能只看SupportsHMA继承或属性True。

## scheduler回调：legacy单组与多组分开

get_num_new_matched_tokens、update_state_after_alloc、build_connector_meta、on_new_request、update_connector_output等断言scheduler存在后委托，不在门面重新实现准入或释放。request_finished把legacy list[int]包装为一元素tuple后传scheduler；request_finished_all_groups将tuple[list[int],...]原样传递，不能把所有group flatten成一个list而丢组身份。

set_xfer_handshake_metadata传给scheduler同名方法，set_xfer_handshake_metadata_pp_aware则调用set_xfer_handshake_metadata_from_workers。PP-aware入口不是重命名后的同一delegate，Native调用哪个hook与metadata key维度都需对齐；门面本身不证明远端地址、cache layout或P/D权重一致。

## worker回调：有方法不等于有layerwise传输

register_kv_caches直接交给worker；类型标注不是门面额外的完整dtype/layout校验。start_load_kv断言worker与MooncakeConnectorMetadata类型，传本实例_connector_metadata给worker，未使用forward_context/kwargs重建metadata。不要以另一个请求的context覆盖当前绑定元数据。

wait_for_layer_load、save_kv_layer、wait_for_save在本门面是no-op，注释明确没有逐层加载/显式保存。这些方法返回不能当传输或持久写入完成信号。get_finished与get_transfer_results虽接受finished_req_ids，实际上不把该集合传给worker，而分别调用worker无参方法；完成集合、错误块与内存释放按worker协议核验，HTTP结束/传入一个finished ID不会在此直接证明块可复用。

get_block_ids_with_load_errors委托worker，get_handshake_metadata返回其xfer_handshake_metadata。get_kv_connector_stats在无worker时返回None，其他对应worker方法多用断言；无统计不表示无传输。build_kv_connector_stats与build_prom_metrics是classmethod，分别创建Mooncake统计与PromMetrics，构建对象不等于已采集实际流量。

shutdown在所读facade仅显式调用scheduler.shutdown，没有显式worker委托；Native/worker完整清理仍需另读，既不宣称资源泄漏，也不把此入口当所有thread/SDK资源已结束。所读Pull scheduler构造会为consumer启动接收线程，Pull worker注册段也进入metadata/接收线程路径；本批仅文本读取，没有实例化或启动线程。

## 初始化维度与控制端口

所读base worker从parallel_config取TP/PP/local DP，从实际PCP group取PCP，从DCP group取DCP。max_device_id按TP×localDP×PCP×PP；side_channel_host=get_ip()，worker side_channel_port为kv_port + data_parallel_index×TP×PP×PCP。device_index=(PP_rank×PCP+PCP_rank)×TP+TP_rank，handshake_port再加该index。serving index可在dense compute DP rank重置后保留实例身份，不可拿重置后的compute rank统一设0。

base scheduler按global DP×TP×PCP×PP算worker端口窗口，scheduler side_channel_port放在其后：kv_port + globalDP×TP×PCP×PP + data_parallel_index，避免与worker握手端口重叠。worker的local DP与scheduler的global DP是不同用途，API端口、HCCL端口、TransferEngine te_rpc_port及这些handshake/control端口分别记录。get_ip()实际通告地址需核对，HCCL/GLOO网卡变量不是此路径选网全部成功的证明。

条件算术例：若实际A3 P配置为DP1/TP1/PCP16/PP2且serving index0，worker窗口30000–30031、scheduler control30032；D配置globalDP8/TP4/PCP1/PP1、serving index0–7，worker窗口30200–30231、control30232–30239。它们只说明公式与所给配置的关系，未打开端口、验证SDK RPC或证明通信可用；不要把旧SDK的预留区间或legacy extra中的tp16直接当当前有效配置/已验证冲突。

当前选段不直接用教程legacy prefill/decode extra替代上述维度，仍未闭合所有superclass/外部代码如何消费extra以及完整PP+PCP互操作。Mamba-specific guard仅拒绝其PCP>1且TP>1联合sharding，不扩成所有模型的通用PCP/TP禁令。

## 适配验收与回退

固定插件/Native/CANN/SDK、实际角色、并行组、layout和metadata版本，先验证注册名→别名→类→正确角色实例，再检查单/多group完成回调、PP-aware握手、真实端口和get_ip地址。补正常/取消/重算/加载错误/部分完成、异步块保活与最终回收；no-op、None、属性True或接口存在都不是成功观测。

缓存匹配与输出正确后才测TTFT、TPOT、传输带宽、prefix命中和HBM；失败先回配对版本的已验证connector/拓扑，不能吞异常、提前释放共享块或改业务角色来绕过协议。外部UCM reserved-hook分发属于[另一桥接合同](../deployment/vllm_ascend_external_cache_integration.md)，不与本门面委托混同。本批未导入上游、注册服务、操作设备/网络或运行NPU/Agent A/B。


## 包导出、分层metadata与统计口径

包级 `__init__.py` 公开 Base/Pull scheduler、worker、connector 和统计、metadata 类型；MooncakeConnector 是已述 Pull 别名，没有在该包中定义一个叫 MooncakeConnectorV2 的新类。导出列表不证明 push 可执行或外部 SDK 可用。

`MooncakeTransferMetadata.__post_init__` 先核对 layer_block_sizes、group_indices、base addresses、strides、lens、shapes、size scales 与 layer_names 层数一致，再核对每层后四类描述与该层地址个数一致。这是结构校验，不校验跨进程指针可达、字节内容、数值 dtype、group 身份或权重一致。frozen dataclass 也不冻结其内部 list。

TP metadata 给端口、layer_indices、地址及 side-channel；PCP 按 TP rank 组织，PP 再带层布局并按 PCP rank 组织，TransferMetadataGroups 按 PP rank 组织且单列 TP/PP/PCP/DCP size 与 use_kv_pp。不能 flatten 后只保留地址总数。请求 ReqMeta 还区分 local/remote/full block IDs、prompt、external/computed token 数与远端 engine/request ID；add_new_req 默认 computed_tokens=0，缺 local_full_block_ids 变空tuple，其余必需远端字段直接索引，不能默认成空值完成握手。

`MooncakeKVConnectorStats` 的成功数是 transfer_duration 列表长度，失败数是失败记录长度。throughput 为各次成功 MiB 总和/各次 duration 总和，不是进程墙钟或并发重叠后的服务吞吐；显示标签虽是 MB，字节实际除 2^20。平均/P90 毫秒不含未记录阶段和失败耗时。clone_and_reset 浅拷贝对象后替换原 data 字典，aggregate 合并各列表；没有传输时统计零不证明链路可用。

Prometheus 指标分别为 mooncake_xfer_time_seconds histogram、mooncake_bytes_transferred histogram 和 mooncake_num_failed_transfers counter，按 engine label 观察。保存原始样本/窗口、成功和失败计数及真实端到端时间；不要由一次 histogram observe、缺失统计或平均带宽推导模型请求成功和缓存可释放。
