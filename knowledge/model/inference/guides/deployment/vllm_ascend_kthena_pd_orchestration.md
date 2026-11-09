---
type: Guide
title: vLLM Ascend Kthena PD 编排：CRD、资源映射与旧配方验收
description: 核对 Volcano Kthena 的 ModelServing、ModelServer、ModelRoute 分工，区分旧镜像、NPU资源名、实际并行和
  KV 连接器；保留 Mooncake/nixl 配置差异、heredoc 展开及健康检查的证据边界。
tags:
- task.implementation
- topic.model_serving
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/deployment_guide/using_volcano_kthena.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/deployment_guide/using_volcano_kthena.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-release-tag.commit
  role: constraint
created_at: '2026-10-30T18:54:26Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T18:54:26Z'
aliases:
- Kthena
- Volcano Kthena
- ModelServing
- ModelServer
- ModelRoute
---

# vLLM Ascend Kthena PD 编排：CRD、资源映射与旧配方验收

## 范围和版本身份

本指南服务于Agent将vLLM Ascend部署到Kubernetes并接入Kthena的任务。依据固定Main的using_volcano_kthena.md全文433行、using_volcano_kthena.po全部42条业务译文及内嵌三个对象的静态解析；42条msgid均匹配英文，未编译gettext或验证站点HTML。示例模型是deepseek-ai/DeepSeek-V2-Lite，不把“可替换任意支持模型”当所有模型、量化、网络和PD组合已经通过。

页面只说明Ascend NPU并列驱动资源名，没有整项PD编排的产品矩阵，因此保持draft、platforms为空。资源名称中出现310或910不等于该具体部署已在310P/A2/A3/950逐项验证。CPU控制面和静态YAML解析也不是设备运行证据。

示例engine镜像为ghcr.io/volcano-sh/kthena-engine:vllm-ascend_v0.10.1rc1_mooncake_v0.3.5；本任务固定Main的release pin是v0.32.0。两者不是同一运行组合。downloader和runtime镜像使用latest，外部示例链接/raw URL使用main；Ascend文档的commit不固定这些外部字节。本批未拉取镜像、外部Kthena源码/CRD schema或在线Quick Start。目标适配先补Kthena版本、engine与runtime/downloader的digest、vLLM/插件/CANN/HDK及实际Mooncake身份，再评估配置迁移。

## 三个CRD各自负责什么

| 对象 | 来源示例的职责与身份 | 必须核对的关联 |
| --- | --- | --- |
| ModelServing | workload.serving.volcano.sh/v1alpha1；deepseek-v2-lite，namespace dev；调度器volcano，replicas=1，ServingGroupRecreate | prefill和decode各replicas=1；controller与scheduler、namespace必须真实存在，清单本身不创建dev |
| ModelServer | networking.serving.volcano.sh/v1alpha1；deepseek-v2；通过workloadSelector选择并分PD组 | modelserving.volcano.sh/name=deepseek-v2-lite；group-name及role标签的实际注入/选择另核，workloadPort=8000 |
| ModelRoute | 同networking API，deepseek-v2；modelName=deepseek-ai/DeepSeekV2 | targetModels指向modelServerName=deepseek-v2；公共模型名、ModelServer.model与vLLM served-model-name一致 |

checkpoint路径/下载源DeepSeek-V2-Lite与served-model-name deepseek-ai/DeepSeekV2是不同身份，不按字面相似推成同一字段。换模型时分别核权重与tokenizer、服务别名、路由目标和请求model。CRD名字存在、Pod Running/Ready或路由被创建，都不单独证明PD组已匹配或请求到达正确后端。

prefill模板有runtime sidecar（8100，engine-base-url=http://localhost:8000）及vllm容器（8000）；decode模板仅列vllm。ModelServer使用8000。不要把这一清单说成两端对称sidecar架构，或自行将workloadPort改8100；实际sidecar/controller/router协作需取得所选外部版本的实现证据。

## NPU资源、并行与容量分别数

前提页举MindCluster的huawei.com/Ascend310P、huawei.com/Ascend910，以及CCE AI插件的huawei.com/ascend-310、huawei.com/ascend-1980；选择Node实际公布的extended resource，大小写和名称不能混用。示例两角色均requests/limits：CPU 8、memory 64Gi、huawei.com/ascend-1980为4。该资源申请不等于进程实际使用四张设备，更不据此建立整项功能硬件矩阵。

两端CLI tensor-parallel-size=2，内嵌kv_connector_extra_config的prefill/decode却均为dp_size=2、tp_size=2，没有显式data-parallel-size启动参数。一个角色一个Pod、资源4、TP2、extra_config DP2是四层信息；须核实际进程/设备映射与服务拓扑，不能把metadata中的dp_size当已启动的DP副本。AscendRealDevices来自huawei.com/AscendReal注解，其注入和可见设备语义取决于实际device plugin/controller。

两端max-model-len=8192、gpu-memory-utilization=0.8、enforce-eager；P max-num-batched-tokens=8192，D为16384且关闭prefix caching。D的batch token预算不是每请求context上限翻倍；memory 64Gi、/dev/shm和NPU HBM也不是同一预算。每端权重、KV、运行时与并发分别核实，不把0.8在不同设备/进程间简单相加或当真实空闲内存测量。

## MooncakeConnectorV1与nixl差异保留

P的KV JSON：MooncakeConnectorV1、kv_buffer_device=npu、kv_role=kv_producer、kv_parallel_size=1、kv_port="20001"、kv_rank=0；D是同connector、kv_consumer、"20002"、kv_rank=1。ModelServer的kvConnector.type却写nixl。这个页内差异不是PO原串不匹配，也不能静默把nixl改为mooncake或断言两者已兼容/必然失败；尚需外部router/engine的具体协议和metadata转换证据。

端口20001/20002属于该旧镜像示例。当前[PD传输指南](../integration/vllm_ascend_pd_transfer_lifecycle.md)另有AscendDirectTransport的预留端口与偏移约束；先固定实际SDK/connector，再列出完整端口预算，不把当前规则无条件套到未读的旧镜像，也不将旧小端口推荐为新部署默认值。请求路由、KV字节传输与释放完成按各自路径留证。

## 下载、挂载与网络依赖

两角色initContainer通过downloader下载到/mnt/cache/deepseek-ai/DeepSeek-V2-Lite/，vllm设置HF_HUB_OFFLINE=1，并只读挂同一容器路径。hostPath的DirectoryOrCreate只说明目录可被创建，不证明权重完整、revision一致、缓存可跨节点共享或下载失败能被忽略。两端/etc/hccn.conf为hostPath File、readOnly；shared-memory-volume是Memory emptyDir、sizeLimit=256Mi，不能当HBM扩容或无上限主机内存。

HCCL_IF_IP取status.podIP，GLOO_SOCKET_IFNAME、TP_SOCKET_IFNAME、HCCL_SOCKET_IFNAME均写eth0。Pod IP、接口名与hccn.conf可见只是配置输入，不证明跨Pod NPU数据面、设备注册、网络隔离和KV传输已经成立。检查真实Pod/Node映射和所选插件的网络条件，再沿[PD完成与释放协议](../integration/vllm_ascend_pd_transfer_lifecycle.md)验收。

## heredoc与变量展开：清单字节先固定

内嵌命令使用未引用的cat << EOF | kubectl apply -f -，同时runtime参数含$(POD_NAME).$(NAMESPACE)。在这种shell heredoc中，$()参与命令替换；它与把原始YAML交给Kubernetes后的变量展开不是同一阶段。不要先执行这段示例再观察是否正常；应先离线核对实际提交的清单字节、controller注入及容器环境来源。本文不把两条变量已被正确设置当成事实，也未执行其中命令。

直接应用外部raw main清单和使用页内heredoc，也不能因链接标题相同就视作相同配置；外部文件本批未获取。保存选定版本的确切manifest、展开方式和哈希，区分作者模板、shell输出与API server接收对象。

## 健康、请求和PD链路分层验收

两端/health在8000；readiness初始5秒、period5秒、failureThreshold3，liveness初始900秒、period5秒、failureThreshold3。ModelServing restartGracePeriodSeconds=60，ModelServer trafficPolicy.timeout=10s是不同层的时间预算。不要用一个值替代模型加载、Pod探测、路由超时与KV数据面deadline，也不从这组数字推算所有负载可用的固定SLO。

示例从kthena-system中的kthena-router Service取LoadBalancer ingress[0].ip和ports[0].port，再请求/v1/chat/completions、stream=false。实际暴露方式是否提供该IP/端口要由集群对象确认。一次成功JSON只提供该入口的一次功能信号；页面将其解释成P/D和KV均成功，还需补实际路由日志、P/D请求关联、remote KV命中/重算fallback、传输/释放和目标设备/数值证据，才关闭PD路径验证。

Agent的验收记录至少区分：模型身份与配置、三个对象的实际关联、Pod及设备资源、P/D实际参与、KV传输/完成、最终生成与精度、并发下TTFT/TPOT/吞吐。静态解析、Ready、单请求输出和性能结果各有口径，不互相替代。本批没有部署集群、执行kubectl/curl、启动容器、通信、模型或性能/Agent A/B。

## 失败归属和清理顺序

缺controller/namespace/resource、selector未匹配、modelName不一致、镜像/权重不可用、接口/IP不符和KV协议证据不足分别定位，保留确切manifest与版本；不要靠增加资源、放宽探测或修改connector名字掩盖身份不一致。原页清理次序是ModelRoute→ModelServer→ModelServing，均在dev；这是来源中的对象依赖顺序，本批未删除任何资源。后续操作先核对象所有权、流量与在途传输状态，参考已选版本的控制器/connector协议形成恢复方案。
