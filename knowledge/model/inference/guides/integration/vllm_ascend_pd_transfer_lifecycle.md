---
type: Guide
title: vLLM Ascend PD 传输：Pull、逐层 Push 与两跳暂存的释放边界
description: "结合中文与原图核对PD的Pull、逐层Push和D2RH两跳，区分路由/字节方向、第一跳释放与D可推理，保留异构硬件、非对称TP和SFA量化布局限制；补充Qwen2.5-VL单机1P1D、Mooncake两种超时和Proxy健康/重试边界，以及图像URL与remote KV fallback验收；单机设备0与设备1各TP1。增加A3多节点外部DP、launch_online_dp七参数/退出状态和P/D QoS发起方合同。 补充 Native API do_remote_prefill 前段拒绝通知、返回流后的清理盲区和RPC释放证据边界。 Hybrid Mamba要求P节点与D节点的num_speculative_tokens一致，其他模型的角色预算另按所列教程核对。"
tags:
- task.implementation
- topic.kv_cache
- topic.data_movement
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/disaggregated_prefill.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/disaggregated_prefill.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/disaggregated_prefill_pull.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/disaggregated_prefill_push.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/disaggregated_prefill_d2rh.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/pd_disaggregation_mooncake_single_node.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/pd_disaggregation_mooncake_single_node.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_prefill_v1/load_balance_proxy_server_example.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/envs.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/pd_disaggregation_mooncake_multi_node.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/pd_disaggregation_mooncake_multi_node.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/external_online_dp/launch_online_dp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/external_online_dp/run_dp_template.sh
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/utils/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_layerwise_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_hybrid_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/generate/base/serving.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/openai/completion/serving.py
  role: supporting
created_at: '2026-10-29T11:00:26Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:49:24Z'
---

# vLLM Ascend PD 传输：Pull、逐层 Push 与两跳暂存的释放边界


## 范围与拓扑

固定设计对 A2/A3 的 MLA/GQA、等 TP 与指定非对称 TP 给出整体支持；不支持 P=A2、D=A3 的异构组合。非对称路径要求 P_TP>D_TP 且 P_TP%D_TP=0。该表不证明文档中后来加入的每种布局、D2RH 硬件或 connector 组合都已端到端验证。

PD 独立搜索 P/D 的并行策略和实例比例，以 TTFT/TPOT 及吞吐为目标；不能只测单端的 forward。每个请求需要可追溯的 Proxy、P、D 身份、transfer metadata、分配块和完成状态。

## Pull 与 Push 的路由方向

MooncakeConnector 的 Proxy 先选 P，以 do_remote_decode=True、max_completion_tokens=1、min_tokens=1 执行 prefill。P 的 request_finished 延迟释放 KV，并返回 do_remote_prefill metadata；Proxy 再选 D。D 进入 WAITING_FOR_REMOTE_KVS，分配块，通过 kv_connector_no_forward 拉取；读取完成后通知 P 释放，再 decode。

MooncakeLayerwiseConnector 先路由 D，D 预分配并经 metaserver 请求 P。P 按层写完后 push，待所有层完成并通知 D 后，D 才进入 decode。不能将 Pull 的“P已返回HTTP”或 Push 的“已发起发送”当作 KV 可立即复用的信号。

## D2RH 的两个完成点

MooncakeD2RHConnectorV1 分成 P HBM→D DRAM→D HBM。第一跳读取完成即可让 P 释放对应缓存，无需等待第二跳或 decode；D 必须完成所需 H2D 后才能算。host hit 只省第一跳，不自动等于 D-local HBM hit；host 块须保持 pinned 直到所有使用它的 H2D 结束。

两端分别 producer/consumer，D 需完整 host staging 预算。设计将具体启动例指向 Atlas850E UBOE；不能凭两跳协议把该实例推广成整个A2/A3功能表的逐模式验证。部署前另取所选硬件的依赖/网络和实际配置证据。

## Sparse SFA 的字节布局

Layerwise contiguous packed C8 主缓存包含量化NoPE、BF16 RoPE及dynamic scales。cache-write event 后直接传这些字节，不能再施加 legacy K/V INT8 量化；indexer K 与 scale 单独作为同层组件传输。

FP8主缓存和indexer两端都需 fp8 且布局匹配，组件处于同一 KV group 和相同 block-size scale。noncontiguous packed main、TurboQuant、DCP-replicated indexer 的不同component scale 不支持该路径。设计明确包括 MultiConnector 在内仍需真机端到端验证，不能把文档描述写成通过结果。

## 验收和故障隔离

在请求取消、局部块/前缀命中、慢D、错误通知、非对称TP和重试场景核对“谁拥有块、谁仍可能读、何时ack”。区分调度预分配、worker注册、cache write、transfer、D可读和释放，保存端口/地址与每层时间线；pooling 另见[KV Pool](../deployment/vllm_ascend_kv_pool_backends.md)，shared-buffer 的更严格释放见[复用诊断](../../runbooks/runtime/vllm_ascend_sparse_buffer_ack_wait.md)。本次未部署Proxy/connector或验证数值。


## 中文设计与三张原图的完成点

disaggregated_prefill.po的52条译文均对应当前英文；disaggregated_prefill_pull.png、disaggregated_prefill_push.png、disaggregated_prefill_d2rh.png按原分辨率核对。Pull图是先P后D的请求路由，Push图则先D、再经metaserver选择P；两图的metadata箭头与KV字节方向不能混读。Push图把metaserver画在Global Proxy内，不规定它必须是一台额外物理服务器。图中被划去的max_tokens=1简写也不代替当前正文的max_completion_tokens=1和min_tokens=1合同。

D2RH图的1–3是代理路由，4–6是P HBM到D DRAM暂存以及通知P释放，7–10才是D调度、H2D和decode。pull箭头表示读请求而不是KV字节流；start_scheduler不是H2D已完成，第一跳ready也不证明D可forward。host-cache命中、D-local HBM前缀命中和真实H2D完成分别记录，host块在使用它的H2D全部结束前保持pinned。

三图均为控制/数据流示意，不能用箭头或P返回HTTP当ACK/内存复用证明。分离P/D有利于独立调并行与实例比例，是优化动机；跨节点传输、排队和缓存命中会改变整体TTFT/TPOT，必须同负载比较，不能据架构自动承诺收益。

## 两种“Mooncake Layerwise”与量化路径不要混用

这里的MooncakeLayerwiseConnector是P/D的逐层Push路径。[AscendStore range/session协议](vllm_ascend_mooncake_layerwise_protocol.md)另用AscendStoreConnector、backend=mooncake、use_layerwise=true，将每block/rank对象内的分层range写入远端池；名称相近不意味着相同connector、SDK接口、对象key或完成门控。

P2P稀疏SFA连续packed C8主缓存可在cache-write event后直接传量化NoPE、BF16 RoPE与dynamic scales，不再做一轮旧K/V INT8量化。FP8主/indexer两端的fp8配置、同group和相同block-size scale是该字节传输路径的条件；它与[稀疏Decode主BF16、LIC8 indexer](vllm_ascend_sparse_layerwise_offload.md)的offload路径不同。某一路支持C8或FP8不能替另一条解除限制，MultiConnector组合仍要独立验收。

正文的端口bind检查、配置类型和P/D TP比例校验属于DFX要求，本次没有证明每个入口都已实现所有检查，更没有占用端口或启动Proxy。A2/A3功能表、不能混A2/A3、非对称P_TP>D_TP且整除分别保留；Atlas850E UBOE链接仅是D2RH部署入口，不据总表扩成所有模式/硬件已验证。


## 单机1P1D配方：Qwen2.5-VL与设备、端口边界

pd_disaggregation_mooncake_single_node.md及其42条中文译文给出的实例是单台Atlas 800T A2、Qwen2.5-VL-7B-Instruct、1P1D。P用设备0、D用设备1，各TP=1/DP=1；容器映射八张卡不表示本例使用八卡。API端口13700/13701、Proxy 8080与KV端口30000/30100是不同用途，2P1D另给每个P独立可见设备和端口，不能把同一组端口直接复制成多个实例。

两端served-model-name=qwen25vl、seed=1024、max-model-len=40000、max-num-batched-tokens=40000、gpu-memory-utilization=0.9，并关闭prefix caching；0.9分别作用在两张不同设备，不相加成同卡可行预算。两端必须对应同一实际权重、revision、tokenizer、多模态处理/布局和并行配置。P为kv_producer、D为kv_consumer，connector均为MooncakeConnectorV1；extra config的prefill/decode各dp_size=1、tp_size=1不能取代真实服务拓扑核验。

这是A2多模态窄配方，不将40000长度、两卡、无APC或该checkpoint推广为所有模型/硬件的推荐值。本卡前述A2/A3设计表仍是另一层证据。教程版本宏需要先解析成实际vLLM、插件、CANN/HDK和Mooncake身份；链接main或容器tag不能取代固定代码与二进制一致性。教程以Mooncake v0.3.9和USE_ASCEND_DIRECT构建举例，不能据此满足当前其他模式的SDK下限，尤其不混入[池化逐层路径](vllm_ascend_mooncake_layerwise_protocol.md)的>=0.3.14条件。

HCCN显示success/UP、hccn.conf可见、主机IP和GLOO/TP网卡选择只是分阶段检查。Docker、安装、网卡/TLS等命令是来源中的部署材料，尚未在本次执行；连通控制面不证明NPU内存注册、KV字节布局和传输完成。

## Mooncake两个超时：延迟释放480秒与bootstrap注册30秒

教程称旧VLLM_MOONCAKE_CONNECTOR_TIMEOUT已弃用，并以VLLM_MOONCAKE_ABORT_REQUEST_TIMEOUT=1800延长P等待D的释放期限；当前Native vLLM v0.32.0的envs.py却仍同时定义两名变量，不能全局搜索替换或认定旧名字已不存在。VLLM_MOONCAKE_ABORT_REQUEST_TIMEOUT默认int 480秒，VLLM_MOONCAKE_CONNECTOR_TIMEOUT默认float 30.0秒，后者的原生注释指prefiller worker向Mooncake bootstrap注册的单请求timeout。

本次读取的Ascend V1 mooncake_connector.py完成队列片段实际消费ABORT_REQUEST_TIMEOUT：get_and_clear_finished_requests收集完成与过期请求，_retrieve_expired_requests按延迟队列首项比较time.time()-delay_start_time，严格大于阈值才移除跟踪并标为finished；首个未到期项即停止。本片段不是每个请求独立定时器，也未证明所有connector/V2/SDK使用同一变量。1800秒=30分钟是教程示例，延长会让失联/失败D对应的P HBM更久不回收，不能照搬“没有任何性能影响”或把到期强制释放视作正常ACK。

释放deadline、bootstrap注册、HTTP重试与[HCCL RDMA传输预算](../../optimizations/rules/pd_kv_transfer_timeout_from_hccl_rdma_budget.md)分开记录单位和消费点；不能用一个秒数替代毫秒级底层传输超时。诊断先关联request ID、P持有块、D读取/取消和真实完成事件，再决定哪一层deadline适合调整。

## 示例Proxy：参数缩写、prefill载荷与健康检查

load_balance_proxy_server_example.py的parse_args正式参数为--prefiller-hosts/--prefiller-ports、--decoder-hosts/--decoder-ports，分别检查hosts与ports列表长度相同后zip。教程写--prefiller-port；当前ArgumentParser()使用默认缩写规则，单数可作为复数前缀，不能仅凭字面不一致判定启动必失败。新部署使用完整--prefiller-ports，防后续新增选项使前缀歧义；这不是本次启动验证。

build_prefill_request浅复制请求并重建kv_transfer_params：do_remote_decode=true、do_remote_prefill=false，其余remote字段None；强制stream=false、max_tokens/min_tokens=1，存在max_completion_tokens时也改1，移除stream_options。它为prefill控制请求生成一个token，不能据此把客户端最终decode输出长度固定成1。所读发送函数遇HTTP 400不重试；max_retries通过max(1,max_retries)解释为总尝试上限而非“额外再试三次”，其余指定HTTP/请求错误按指数退避重试。流式响应已发送首chunk后遇请求/一般异常则记录并结束，不重新播一遍已发内容；这不构成完整重试幂等性证明。

/healthcheck只是scheduler锁内返回status=ok、P/D实例计数和request_num，没有在该方法探测每个后端或传输链路。/reset_prefix_cache向快照中的P/D后端逐一POST并转发query参数，有失败返回500与失败列表，否则200；该响应只反映这些调用，不能当成外部持久池全清空或所有在途读写已停止的证明。教程向/v1/chat/completions发图像URL与文本的请求属于接口样例；收到生成结果仍要核对真正的remote KV命中、fallback/重算、数值与多模态一致性，才能验收P/D路径。


## 多节点A3：2P1D标题、物理节点与DP组分别数

pd_disaggregation_mooncake_multi_node.md及140条中文资料以DeepSeek-r1-w8a8/mtp和四台Atlas 800T A3为例，不能把“2P1D”直接解释成三台物理机。启动命令在两个P主机各启动独立DP2/TP8组（各自dp-address、rank从0重启），共四个P API端点7100/7101；两个D主机共同组成一个DP32/TP1组，master为第一个D，rank范围分别0–15和16–31，API各7100–7115。源码用16个可见chip设备ID，与包装层“8个NPU”命名不能混算。归档实际DP组、rank范围和EP组，不只保存一个2P1D标签。

P侧maxlen40000、batch16384、maxseq8、memory0.9、eager；D侧batch256、maxseq40、memory0.94、FULL_DECODE_ONLY及重算/共享专家/lmhead TP16属于来源的特定调优组合，不是新模型默认值。该例使用ascend量化、关闭APC，MTP=1；其他组合先区分Hybrid Mamba（教程要求P/D num_speculative_tokens相同）与其他模型（P=1/D>=1）。DeepSeek-V4-Flash D2RH则另用不同checkpoint、FP8 indexer和dspark=5，不能把两套投机配置合并。

教程Layerwise用MooncakeLayerwiseConnector并配先D后P的layerwise Proxy；Non-layerwise用MooncakeConnectorV1配先P后D的Proxy。Proxy端口1999、性能配置示例8000与最后验证8080并非自动一致，served-model-name ds_r1和性能例model=dsr1也不同；部署/评测前统一实际路由与别名，再确认KV传输而非仅HTTP生成结果。P预热几轮的建议没有给统一轮数或吞吐保证。

## launch_online_dp.py：七位置参数、资源预检与进程退出

launch_online_dp.py完整源码按i从0生成visible_devices=[i*tp_size,(i+1)*tp_size)、dp_rank=dp_rank_start+i、API端口=vllm_start_port+i，dp-size-local=-1回退为dp-size。它把设备、API端口、总DP、rank、master IP、RPC端口、TP七参数传给CWD相对的./run_dp_template.sh。非连续物理/可见设备、父进程已有可见设备限制和跨节点rank规划不能依赖该简单0起点计算，需先核对映射与无重叠。

参数类型/必填解析不是资源预检：正值、localDP×TP<=真实设备数、rank覆盖范围、master一致/可达、API连续空闲和完整KV/数据面端口预算在外部检查。--dp-rpc-port声明type=str，但省略时default=12345是int，随后未str(...)就进入subprocess argv；此静态类型分支存在调用参数问题，教程显式传12321避免了省略分支，不能描述成已运行复现或已修上游。默认API起点9000也不是教程7100。

子进程内subprocess.run(check=True)会对模板非零退出抛错，但父进程仅join各multiprocessing.Process，没有检查exitcode或聚合失败，不能把launcher父进程结束当所有服务成功。模块顶层直接parse_args，导入也有参数解析副作用，本次没有import或launch。run_dp_template.sh仓内默认仍是model_path、served-name dsv3、maxlen8192、batch2048、maxseq16、mtp=1，未配置PD connector；必须用目标P/D片段替换占位并检查七参数，不能直接把未修改模板当DeepSeek-R1 PD部署。

## P/D QoS：由连接发起方选择，环境注入不是通道验收

当前教程给MooncakeConnectorV1、MooncakeHybridConnector和MooncakeLayerwiseConnector的qos_priority默认1，接受严格int 0–4、拒绝bool；Pull由D发READ，故取D的QoS，Push由P发WRITE，故取P值。数据都从P到D不改变连接发起方，单改被动端不能覆盖发起端channel QoS。MultiConnector内此配置放Mooncake P/D child，不能据此配置或验证池化store。

所读utils/utils.py inject_qos先检查type(qos) is int及范围，再将ASCEND_GLOBAL_RESOURCE_CONFIG解析为object，空/未设置作为{}；非法JSON/非object在写环境前失败。字面的顶层键"comm_resource_config.qos"是带点的一个key，不是嵌套comm_resource_config对象。显式值或省略时default1会覆盖已有顶层QoS并告警，其余键与store保留；三个P2P构造片段均在取得TransferEngine前注入。Injected日志只证明本地环境成功写入，不能替代发起端HIXL channel日志、拥塞/尾延迟测量或驱动生效。[A3 AI QoS工具](../optimization/vllm_ascend_ai_qos_network.md)的high/middle/low、交换机VL与AIV驱动限制是另一功能，不将P/D 0–4和其标签互换。

端口表按AscendDirectTransport来源给8设备保留20000–27999/kv_port>=28000，16设备保留20000–35999/kv_port>=36000；还要审计各DP/TP/PP/PCP实例实际handshake范围，不能只避开一个base。V1、Hybrid和Layerwise所读片段使用的rank/serving-index偏移并非完全相同，独立服务和重置dense compute rank后重新列举范围。Atlas 850E D2RH额外端口/容量与950PR/DT容器准备见[窄范围部署合同](../deployment/vllm_ascend_d2rh_deployment_contract.md)，不由本卡A2/A3设计表扩展成所有硬件/组合验证。


## Native API：远端 prefill 请求在进入 Engine 前被拒绝

固定 vLLM v0.32.0 的 `_with_kv_transfer_rejection_cleanup` 补充上文 PD 传输流程的入口失败分支，不能替代 Ascend connector 的逐块 ACK、异步传输完成或 D 可推理证据。GenerateBaseServing 全文与 Completion 入口/末尾映射选段已核对；未执行 RPC、服务或 NPU，其他 endpoint 的实际调用未闭合。

只有 has_kv_connector 成立、请求带 kv_transfer_params，且其中 do_remote_prefill 为真，包装器才启用拒绝通知；否则直接 await 原协程。启用时先置 notify=True；协程抛异常或返回 ErrorResponse 会保留通知，在 finally 中调用 `notify_kv_transfer_request_rejected`，传原 request.request_id、kv_transfer_params 和从 `X-data-parallel-rank` 解析的 rank。此处的请求 ID 不自动等同后续形成的 cmpl 前缀 ID。rank 仅 int 解析，范围约束待下游验证。

协程返回任何非 ErrorResponse 结果就置 notify=False，包括成功返回流式生成器对象：后续迭代才发生的错误不会由这个包装器再次通知。Completion 的 `create_completion` 确实使用该包装器，而 stream+beam search、模型预检、准入和 renderer 失败属于它可覆盖的前段；不能推广成所有流中断、客户端断连、取消或未知 endpoint 均已回收远端 KV。

通知自身抛异常时只记 warning 并保留原路径结果/异常；“已进入 finally”或“调用通知成功返回”都不能证明 peer 已释放 pinned block，更不是 D2RH 第二跳完成。Agent 诊断时分列：请求进入 Engine 前是否被拒绝、是否满足远端 prefill 条件、拒绝通知参数及失败日志、connector/peer 实际接收与释放信号。没有通知时先检查 gate 和协程是否已成功返回流，再查本卡既有超时、ACK 与释放协议。

验收矩阵应包含无 connector、无参数、do_remote_prefill 为假、ErrorResponse、前段异常、非错误返回和返回流后异常；仅据源码列出待验证分支，尚未运行这些场景。保留原始错误，不为制造通知而重试真实生成或重复释放。关联[模型适配的 API 预检](../bringup/vllm_ascend_new_model_onboarding.md)与[请求计时边界](../optimization/vllm_ascend_benchmark_workflow.md)，把控制端拒绝清理和 Device 传输故障分别留证。
