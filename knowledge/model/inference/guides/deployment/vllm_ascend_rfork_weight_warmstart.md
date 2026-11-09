---
type: Guide
title: vLLM Ascend RFork：兼容 seed、处理后权重与回退生命周期
description: "RFork 使用总览：核对 seed 兼容身份、端口、租约和默认加载入口，串联新模型 manifest、处理后权重与失败清理的实现边界及中文 PO 差异。 后续发布5f5e25补齐Engram共享组fallback限制、legacy lease/removal、身份headers与seed信任边界。"
tags:
- task.implementation
- topic.checkpointing
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/rfork.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/rfork.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/identity.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/manifest.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/rfork_loader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/session.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/transfer_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/safety.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/rfork_flowchart.jpg
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/feature_guide/rfork.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/rfork.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/vllm_ascend/model_loader/rfork/config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/vllm_ascend/model_loader/rfork/rfork_loader.py
  role: implementation
created_at: '2026-10-29T09:49:02Z'
updated_at: '2026-11-03T09:36:02Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend RFork：兼容 seed、处理后权重与回退生命周期

## 范围与前提

draft：来源描述主流DeepSeek/Qwen/GLM，未提供具体硬件验证表。load-format=rfork 使用YuanRong TransferEngine和外部planner，需 model_url、model_deploy_strategy_name、rfork_scheduler_url。首实例通常本地加载，后实例请求seed；无seed/失败清理后default loader，不保证首次冷启动加速。

## 兼容身份不能只看模型名

seed key由value-semantic配置指纹、transferable tensors结构digest和shard ranks构成。revision、quant config、RoPE、架构、PD role等影响内容；names/shapes/dtypes/NPU format影响结构。TP/PP/EP以及实际DP分片身份必须区分；相同shape的不同专家或fine-grained DP shard也不能互换。

量化传输为post-load后的live tensors，包含transpose/NZ/packed/derived scale与MLA吸收矩阵，已释放empty tensor不纳入。receiver先构造同样layout，最终manifest仍校验；更新实现/参数须新strategy namespace并替换旧seed元数据。

## 字节和生命周期边界

协议有意复制非重叠dense tensor的numel×element_size范围，允许storage-preserving view，拒绝gap/overlap；不隐式复制allocation padding或相邻storage。新格式若需额外字节要扩协议，不能凭descriptor容量自行扩read。layout semantic/physical digest是诊断，不证明value相等。

seed HTTP端口非零base时main=base+2×global_rank、draft再+1，异常可OS分配；TransferEngine RPC用OS端口或自身合法范围，HIXL数据端点又独立。旧“全部随机”描述不能覆盖新增base字段。lease release异步，未解决可延迟seed发布而不阻断已加载模型推理；mock planner不代表生产容量/高可用。

## 验收与回退

记录source=transfer/local/fallback/shared_target、bytes/chunks、注册/metadata/read以及peer_session。分别测ready时间、seed推理干扰、seed hit、失败和fallback，不能只看单read带宽。dynamic EPLB/record等会使权重placement变化，固定实现还旁路sleep、在线weight transfer和静态expert_map_path等，详见后文。数值验收失败时应隔离seed、用完整default加载核对；这不是代码内已存在的通用自动数值回退。本次未做NPU存储/传输验证。


## 配置指纹与DP分片的细化

固定英文/中文文档将兼容指纹分为值语义配置、tensor结构和shard身份。结构digest来自最终可传输tensors的names/shapes/dtypes/NPU formats；值语义还包括协议版本、resolved revision、checkpoint quant config digest、architecture、RoPE、P/D kv_role和mix_placement，不能只据model_url或shape匹配。

sharded_dp_rank只在权重确实沿DP分片时加入：细粒度TP使用DP维度，MoE且data_parallel_size>1的expert还可沿DP×TP分片，文档明确即使EP关闭也需区分同shape不同内容的DP shard。复制DP可共享seed池；不要统一把所有DP rank都合并或全部强行隔离。本批已对照identity/loader实现补充下述任务卡；未知MoE的保守DP分区与所有模型真实shard内容仍须分别核对。

## 布局摘要、协议意图与中文PO

RFork tensor layout summary每rank仅给有界样本和semantic/physical digests，peer_session须与seed session对应；checkpoint路径看receiver_before_read/receiver_after_post_load，processed路径看receiver_after_transfer_finalize。digest差异本身不拒绝传输，也不证明数值不同；digest相同也不证明tensor值相等。

稠密transpose/reshape协议允许metadata替换为保持storage的seed shape，不额外要求stride相等；gapped/overlapping仍拒绝。处理后NZ载荷按命名tensor的numel*element_size读取，不因storage capacity或descriptor padding自行扩大。新布局若改变实际byte order/需要额外字节，应更新兼容描述或协议并取得目标NPU证据，不能用CPU测试或摘要代替。

rfork.po的67个有效非空条目已全文对照当前239行英文，0obsolete/fuzzy且msgid均为当前英文子串；作为补充来源绑定。两文仍有“各worker端口随机”的旧概述与seed_port_base表的并存，应按端口类别和实际配置解释，不能用翻译抵消冲突。外部TransferEngine、planner高可用、真实lease/存储行为及全部模型格式未在本批验证；中文生成/线上HTML映射也未证明。


## 固定实现的三条消费路径

新模型的指纹字段、条件DP shard、tensor发现/alias、共享skip、manifest与dense view验收见[兼容身份与manifest](../integration/vllm_ascend_rfork_manifest_contract.md)。代码并不计算tensor值checksum；发布时verify_structural_digest只返回False且调用方未检查，与重新bind时抛错不同，不能概括成所有结构漂移都自动拒绝。

预布局/processed模式、checkpoint后处理、shared_target、main/draft session以及受控fallback见[权重加载接线](../integration/vllm_ascend_rfork_processed_weight_loading.md)。sleep、在线weight transfer、静态expert_map_path与动态EPLB等按固定实现旁路；不是任意legacy开关的同义词。精度失败应隔离seed并用完整default加载做对照，该代码没有通用数值验收后的自动回退保证。

注册内存owner、部分read、lease快速预算后降频、DEFERRED发布、HTTP退役与finalize条件见[内存与租约排障](../../runbooks/runtime/vllm_ascend_rfork_retained_memory_cleanup.md)。默认加载必须先满足服务/内存清理门禁；planner已无lease与本地MR安全释放分别取证，不以mock planner或CPU定义代替NPU实测。

本批已将RFork13个Python模块、单进程planner及所述测试/原生接口范围蒸馏进上述任务；完整文件已读不代表所有模型、全部外部SDK、每一运行分支和设备结果都已闭合。中文PO进度仍按上批记录，未新增线上HTML映射证明。

## 固定架构图的控制面与数据面

RFork图把外部rfork-planner与两端vLLM-Ascend/YuanRong TransferEngine分层，并画出各NPU权重经RoCE/NIC/网络到接收端的方向。它用于区分seed选择控制和权重字节传输，不证明planner高可用、租约事务、所有NPU格式或整个allocation均可复制。

图中的weight盒子仍须按本卡实际manifest、numel字节范围、处理后布局和生命周期合同解释；不能从箭头推出任意设备直读、零拷贝或启动加速保证。没有据图扩平台、运行传输或替代失败回退验收。

## 2026-11-03 发布快照：Engram、legacy planner 与配置失败

本节固定 `5f5e25dd94db85b59251be7d3baf7c808475b6d7` 的完整 RFork 文档/PO和实际中文 HTML；前文239行/67条及未获取HTML的记录只属于旧ceac批次。新增声明按这个版本读取，不能提升旧源码或全部模型的验证等级。

DeepSeek V4.1 Engram CPU offload 的 host table 与进程本地 UVA 指针不通过RFork传输；每个receiver仍需同revision的indexed safetensors及Engram weights/scales。`dp_shared_memory=true` 沿用共享writer同步，但部分rank回退、其他rank已返回时会重新进入collective，可能启动挂起；跨共享组协调fallback尚未解决。拓扑/模型允许时可用false避开该共享风险。host table完成、tensor identity/address/checkpoint binding校验后才获得非NPU状态例外；其他CPU state仍拒绝。清理失败不分配第二套host表，构造未完整返回的Engram错误也不盲目重跑default loader。

配置校验在启动完成。seed健康超时默认5秒、HTTP超时10秒，有限正JSON值优先、否则有效env、再默认；heartbeat默认30秒、lease快速次数3及间隔30秒是JSON专用并拒绝非法值。`rfork_model_identity_headers` 默认false，显式JSON bool优先于RFORK_MODEL_IDENTITY_HEADERS；开启后每个planner请求带MODEL_URL/DEPLOY_STRATEGY/IS_DRAFT，前两项须ASCII，错误类型/值失败，不会静默忽略。seed HTTP没有自带认证/限流，seed_key可获取tensor地址及TE会话，应按文档在可信隔离网络保管它与模型URL身份信息。

legacy planner 的最小协议仍为add_seed/get_seed/put_seed，SEED_KEY按完整opaque值匹配，SEED_RANK必需且非负，SEED_REFCNT固定0仍须接受。LEASE_TTL_SEC可缺省：不续租、无本地到期计时，但成功或失败均释放lease；若存在却非法则协议失败。heartbeat只报存活，不续receive lease。未发布receiver的legacy put_seed失败可保留pending而不阻止native finalize，shutdown仅在无在途release时做一次best-effort。

seed removal默认false；true表示管理员确认200=移除、409=draining、404=记录不存在；null自动探测只有200/409确立支持，未知404不作成功、405/501为不支持。未确认撤回的已发布seed仍保有注册内存；超时/5xx保留服务与内存供重试。fallback最多两次必要清理，失败或session已finalized就停止启动，不能把default loader当无条件恢复。

处理后路径新增非量化weight_nz_mode=2/FORCE_NZ；发布前的processed布局可复用final post-eval摘要、deferred发布重扫并在结构不匹配时拒绝。checkpoint路径后处理重建registration/manifest但保留原seed key，不在发布时再次校验digest；沿用前文精确字节范围与数值边界。AscendDeepSeekMTP在注册前读取safetensors header准备head/alias；PT/bin或metadata不可读则走default且不发布seed，远端未缓存checkpoint可因这一步下载。

seed miss/未取得合法lease记录source=local；setup/registration/read失败记录source=fallback。TE RPC仍初始化port0并读取绑定端口，可由YR_TE_RPC_PORT_MIN/MAX共同限制1024–65535且排除32768–60999；HIXL默认base22000、每物理device100端口，和Mooncake ADXL默认20000段分开。tensor ID优先注册module路径，余下取受支持属性最短路径/字典序；容器key带类型，拒绝未知key和同label冲突，完全同范围alias去重但不同view保留。这些文档边界没有证明外部planner/SDK或NPU运行正确。
