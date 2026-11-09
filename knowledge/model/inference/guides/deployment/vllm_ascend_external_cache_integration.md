---
type: Guide
title: vLLM Ascend 外部缓存集成：UCM 架构与 LMCache 版本边界
description: 区分UCM拓扑与LMCache-Ascend外部注册所有权，结合中文安装旧配方核对版本、设备和配置，避免将旧连接器或宣传倍数当当前部署结果。补充UCM三种配方、端口/长度冲突、0.8预种与来源性能表，以及UCMConnectorV1 reserved hook/外部所有权边界。
tags:
- task.implementation
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/ucm_deployment.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/lmcache_ascend_deployment.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/kv_cache_pool_ascend_store.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/lmcache_ascend_deployment.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/ucm_deployment.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ucm_connector/connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/pd_disaggregation_mooncake_multi_node.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ucm_connector/__init__.py
  role: implementation
created_at: '2026-10-29T09:49:02Z'
updated_at: "2026-11-04T02:54:15Z"
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 外部缓存集成：UCM 架构与 LMCache 版本边界

## 范围与依赖边界

UCM指南明确CANN A2/A3，跨平台产品列表不表示Ascend插件可驱动CUDA/MUSA/MACA。本卡基于固定插件文档，外部UCM/LMCache源码和精确兼容版本尚需单独冻结；不能把main依赖当成任意release兼容。来源宣称3–10倍等数字缺完整通用条件，不作为性能结论。

## 三种UCM拓扑

集中PD经共享NFS/3FS等storage传KV，P/D都需访问同一存储，不是各自同名本地目录；示例UCMConnector用kv_both，与P/D业务角色并非同一字段。P2P PD用Mooncake负责P→D，P端通过MultiConnector加UCM prefix cache。PD mixed用单服务交织P/D并连接持久前缀层，不能照搬recompute scheduler的consumer条件。

PipelineStore以Cache|Posix串设备/host与storage层，UCM_CONFIG_FILE指向YAML，cache buffer、event sync、layerwise按目标UCM版本配置。不要将AscendStoreConnector的字段复制到UCM YAML。UCM开篇把KV Pool写成无SSD/持久层的概括已与同提交AscendStore指南不一致；后端选型按具体能力与版本，不沿用该对比。

## LMCache迁移边界

固定LMCache页面保留0.3.12与vllm-ascend0.11.0示例，末尾明确插件已不再注册LMCacheAscendConnector，注册与runtime配置由LMCache-Ascend包负责。不得给最新vLLM生成旧连接器命令。外部包、submodule和当前支持矩阵取得后才能形成新版本部署配方，本卡不宣称已验证外部兼容。

## 验收与回退

先冷缓存对照，再以受控前缀预热，确认hit external与实际prefix ratio，区分HBM本地DP命中下降和共享存储命中。来源A2八服务器GLM-5.1测试用128并发、0.8前缀预种，不能把差值外推至任意硬件/负载。测冷/热TTFT、TPOT、storage带宽、cache失效与故障恢复；路径不可达、layout不一致或净收益不成立则停用目标connector、回已验证本地前缀策略。本次未安装外部包或运行模型。


## LMCache中文安装示例的所有权

lmcache_ascend_deployment.po的15条有效译文均匹配固定英文，明确LMCacheAscendConnector不再由vllm-ascend注册。注册、runtime配置及kvcache ops子模块属于外部LMCache-Ascend包；该页的外部main链接不是本批已冻结/已读取的外部源码，不能据链接存在宣告兼容矩阵闭合。

页面的NO_CUDA_EXT=1与lmcache==0.3.12、Dockerfile.a2.openEuler及vllm-ascend-v0.11.0镜像是该旧配方的具体条件。NO_CUDA_EXT禁CUDA扩展不证明NPU扩展已正确构建，no-build-isolation editable安装也不证明依赖/ABI配对。镜像tag、submodule revision、真实包身份与目标Ascend插件注册逐项核对；不用旧命令为当前v0.32自动生成可用配方。

DEVICE_LIST、ASCEND_VISIBLE_DEVICES、ASCEND_RT_VISIBLE_DEVICES、ASCEND_TOTAL_MEMORY_GB=32和VLLM_TARGET_DEVICE=npu同样是示例输入，不证明实际设备映射/物理容量/后端选路。按具体产品模板核设备、挂载、解释器和有效配置；该页privileged/SYS_RESOURCE/IPC_LOCK不提升为所有UCM、LMCache或Ascend部署的默认要求。克隆、构建、安装与外部服务本批均未执行。

UCM与LMCache分别保留包/配置所有者：不要把UCM_CONFIG_FILE、PipelineStore或AscendStore的backend字段搬进未知LMCache runtime配置。外部注册缺失、版本未知或冷/热输出不一致时停止可用结论；已声明A2/A3范围也不单独验证此LMCache旧示例在每一组合可用。


## UCM三种配方：共享存储、P端前缀与PD mixed

ucm_deployment.md与ucm_deployment.po的113条中文译文已全文对照，原串全部匹配（含性能HTML表），并不证明外部UCM支持矩阵、包版本或整站HTML已经闭合。文档的GSA、CacheBlend、ReRoPE、NPGD、xPYD是UCM能力列表，不能由本页示例直接推导每项均可与当前Ascend硬件、量化、图和混合KV任意组合。存储容量由真实后端预算/故障模型决定，不采用“无限容量”或所有失败都保证持久化的宣传口径。

集中PD示例为QwQ-32B、P节点7800/7801、D节点7802/7803、Proxy7805，各TP4/DP1，P eager、D FULL_DECODE_ONLY，memory0.92/maxlen17000/batch8000/maxseq20。YAML中的ucm_connector_name为UcmPipelineStore、store_pipeline为Cache|Posix，storage_backends=/mnt/test1、cache_buffer_capacity_gb=64、enable_event_sync=true、use_layerwise=false来自该YAML。两端kv_both表示connector读写角色，不能当成业务P/D没有分离。目录相同还要确认挂的是同一共享NFS/3FS；第二实例换可见设备和API，不能在同四卡重复分配0.92预算。

P2P示例为P侧MultiConnector（Mooncake kv_producer加UCM kv_both前缀层），D只用Mooncake kv_consumer，服务各9000/9001、Proxy7850；UCM YAML在该配方use_layerwise=true，不能原样取集中PD的false或AscendStore字段。Mooncake master50088、lease11000、segment"1GB"另属Mooncake配置，64GB UCM cache buffer不等于该segment。所需SDK版本、单位及lease实际消费仍按对应包核验，导出MOONCAKE_CONFIG_PATH不证明store已可用。

PD mixed则是同实例交织P/D并连接UCM，来源DP2/TP4、设备0–7、block-size128、eager；与物理P/D服务分离及recompute scheduler的consumer条件不同。两次10请求、8k输入/1k输出、seed123456、request-rate inf的bench命令只是验证起点，不能从跑两次或一行hit external日志就认定实际外部命中比率、持久恢复和端到端收益均已通过。

## 当前端口合同与旧UCM命令的冲突

UCM P2P命令仍用kv_port20001，第二实例例20002；当前[PD传输合同](../integration/vllm_ascend_pd_transfer_lifecycle.md)按Mooncake多节点教程说明：八设备AscendDirectTransport保留20000–27999、建议kv_port>=28000，16设备则保留至35999。仅把20001加一不满足当前预留范围，而且TP4的handshake端口窗口可能相互重叠。部署前按所选V1/Hybrid/Layerwise、DP serving index与TP/PP/PCP完整枚举各服务范围，使用无冲突且可达的区间；不能把UCM示例小端口当推荐默认。

若实际选择D2RH，另按[暂存与控制端口合同](vllm_ascend_d2rh_deployment_contract.md)核对两个D侧控制面及host容量。

八节点GLM-5.1-w4a8例为A2/910B3、每节点八卡：四P节点共DP4/TP8、每节点一DP，四D节点共DP8/TP4、每节点两DP；P/D各自master/rank组，配置共享后端、quantization ascend，P eager与旧additional-config选项需按当前解析器另核。A800/CE8875是来源设备，不扩成UCM所有部署必需的存储品牌。

run_multi_dp.sh每轮原地更新server_port+=i和mooncake_port+=i*tp_size，不是始终base+i；若扩成三个本地实例，API会是9000/9001/9003。来源localDP=1/2尚未触及第三轮，但推广脚本前应单独生成端口表。背景子进程加wait、vllm命令经tee且未启pipefail，不能只凭脚本退出/日志文件存在判断所有worker就绪。示例shell仅作为数据阅读，本次没有执行或修改上游。

## 0.8预种实验：实际输入、命中率与长度先闭合

来源实验128请求/并发128，预种input=target×0.8、output=1，测试full input、output=1000，例32k使用25600与32000。先确认实际token序列、顺序、模型/权重/模板、block size、namespace/cache salt、共享存储权限与写入完成；同一seed和两个不同输入长度参数，不能单独证明每个测试请求的前缀与预种相同。持久外部缓存仍可能因逐出、部分块、读取失败或命名空间不一致miss，不采用“共享存储保证实际命中0.8”的无条件结论。

源码所附服务命令max-model-len=17000，而表格/bench使用32k、64k、128k输入再加1k输出，页内没有给出与之匹配的服务长度配置。复现先闭合context总预算、实际accepted/successful请求与服务返回，再比较延迟；不能将来源表当这些未修改命令可直接复现的证明。128请求不超过P可用HBM容量也是该实验约束，不能在容量不足时原样外推。

Recalculation、HBM PC、UCM PC分别为无UCM且HBM前缀关闭、无UCM但HBM前缀开启、启用UCM。HBM缓存随DP路由错位而命中下降只是来源解释，需实际rank/命中观测；UCM是否真实从外部取KV与HBM残留命中、重算或仅本地DRAM取回分别记录。

## 来源性能表：TTFT、TPOT与E2EL分开解释

以下仅保留来源报告值，输出均1k、各格依次TTFT/TPOT/E2EL（毫秒）；不是本次测量、当前版本承诺或任意硬件的收益保证。

| 输入 | Recalculation | HBM PC | UCM PC |
| --- | --- | --- | --- |
| 32k | 140730 / 64 / 173820 | 108879 / 65 / 142228 | 51861 / 66 / 85615 |
| 64k | 181864 / 64 / 214988 | 144444 / 65 / 177561 | 69718 / 66 / 103752 |
| 128k | 268016 / 65 / 301648 | 267680 / 65 / 301135 | 105083 / 66 / 138946 |

仅按表中TTFT算术，Recalculation/UCM约2.71/2.61/2.55，HBM/UCM约2.10/2.07/2.55；表内TPOT从64/65变为66，并非所有阶段都变快。该表不能单独支持开篇通用“3–10倍/最高8倍”。E2EL、TTFT和TPOT的统计分母/聚合方式未在表内闭合，不擅自套E2EL=TTFT+999×TPOT或由TTFT比值直接承诺整体吞吐。

## UCMConnectorV1：外部所有权与reserved hook分发

当前connector.py完整333行是Ascend桥接层，模块直接导入外部ucm.integration.vllm.ucm_connector.UCMConnector，构造时传vllm_config、role、kv_cache_config；它不自行实现存储或解析完整UCM YAML。注册表的UCMConnector配置名与UCMConnectorV1类名alias用于MultiConnector按类名重建统计，不能由工厂列出名称推断外部包存在、ABI匹配或metrics成功。SupportsHMA继承声明也不证明所有混合group/layout已端到端验证。

普通register/load/wait/save、metadata bind/clear、get_num_new_matched_tokens、update_state_after_alloc、request_finished/all_groups、get_finished与读取错误等直接委托外部engine，wrapper未在此捕获这些调用异常。get_finished和request_finished的真实异步释放语义由外部实现决定；不能因HTTP结束或wrapper存在wait_for_save入口，就假定写入/持久化完成。

_get_ucm_delegate_for对reserved hook检查name是否在type(engine).__dict__直接声明：有则用dispatcher，否则有inner connector时转给inner，无inner再用dispatcher。它不是完整MRO能力检查，不能理解为所有继承方法都会优先或所有接口都走此helper。_call_ucm_reserved_hook仅在最终getattr结果callable时调用，否则None；有hook但抛错时不吞掉。

shutdown、host buffer ops、preemptions、worker metadata、stats/events、handshake、finished count和reset等走reserved helper。take_events把None转空tuple；reset_cache返回None表示未知/未提供结果，不能报告重置成功。get_loaded_kv_cache_group_ids仅None才调用base默认，外部显式空列表转为空tuple而不回退；实际group是否可跳zeroing需核对应Native和UCM语义。build_kv_connector_stats/build_prom_metrics是classmethod，委托导入的UCMConnector类，不经实例inner选择。空事件或无统计不等于没有传输/没有缓存。

本批没有导入外部UCM/torch、编译/安装、执行shell/bench/HTTP、修改存储/系统或运行NPU。后续适配按目标版本补外部UCM来源与真实配置/输出、缓存写读和取消/失败清理证据，不通过翻转角色、吞异常或把None视作成功绕过缺口。


## UCM包入口的含义

固定 Main 的 `ucm_connector/__init__.py` 只从本地 connector 模块重导出 UCMConnectorV1，并在 __all__ 列出该名；它不实现另一个存储后端，也不为外部 UCM 的导入、版本或运行结果提供兜底。包入口导入仍会进入前述依赖外部 UCM 的桥接模块，不能把可检索的导出名当作环境已安装或注册/传输成功。
