---
type: Guide
title: vLLM Ascend代理示例：长度分桶、EPD/PD与请求生命周期
description: 核对长度分桶、EPD/PD路由及请求生命周期；区分两种代理的首包后重试行为，解释recomputed续写预算与清理，再按固定3164选择prefill会话亲和。示例启发式不证明实际KV命中或恰好一次交付。
tags:
- task.implementation
- task.testing
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/dynamic_bucket_load_balancer/dynamic_bucket_load_balancer.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_encoder/disagg_1e1pd_example.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_encoder/disagg_epd_proxy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_prefill_v1/load_balance_proxy_layerwise_server_example.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_prefill_v1/mooncake_connector_deployment_guide.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/dynamic_bucket_load_balancer/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/dynamic_bucket_load_balancer/hybrid_proxy_server.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/epd_disaggregated/epd_disaggregated_guide.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/epd_disaggregated/epd_load_balance_proxy_layerwise_server_example.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/external_online_dp/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_disaggregated_prefill_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/run_dp_server.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/examples/disaggregated_prefill_v1/README.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/examples/disaggregated_prefill_v1/load_balance_proxy_server_example.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/proxy/test_prefill_session_affinity.py
  role: implementation
created_at: '2026-11-03T05:18:22Z'
updated_at: '2026-11-04T02:53:33Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend代理示例：长度分桶、EPD/PD与请求生命周期

排查重复输出、流中断或重算后输出长度异常时，先读“流式重试与重算预算”；排查会话未命中缓存时，读末尾固定3164亲和机制。P、D、E分别表示prefill、decode和encode服务。以下机制按明确的源版本分段，代理选路成功、HTTP成功与远端缓存可读是三个独立结果。

## 长度与负载不是同一维度

DynamicBucketLoadBalancer先按[min,max)找标准桶，区间全不匹配回退末桶。它只考虑更低负载的邻桶（可选全部邻居），评分为clamp后的1-(neighbor/standard)^sensitivity乘指数长度亲和度，选择最大评分且严格超过0.12才重定向。函数中的probability是确定性评分/阈值，没有随机抽样；标准桶无负载不重定向。

hybrid proxy的token估计为请求长度/4，负载分数默认长度+0.5×max_tokens，ignore_eos时用全max_tokens；这些是示例启发式，不能当模型真实tokenizer或实际decode成本。组/服务器数量和host-port长度有显式约束，真实prompt、图像、tokenizer和吞吐需另测。

Task按ID保存并在释放时回减bucket负载。重复ID的检查发生在计数/负载更新之后，调用方需保证唯一并核失败记账恢复；不能认为抛异常自动撤销全部状态。release同样要求已有任务与有效bucket，reset会清所有任务。模型服务重试、断开和stream结束要与这些租约回收配对。

## 把代理阶段与缓存传输分开

EPD/EC代理有encode fanout、可选prefill及decode，文本/多模态内容用不同入口；layerwise PD/EPD代理还维护prefill/decode请求ID、优先级与metaserver。stream/nonstream、断开取消和重试各有单独函数，不能以一次health响应推所有stage/remote KV已完成。图像尺寸解析与本地路径、各host/port可达性也属于输入/环境前提。

1e1pd shell示例默认encoder/PD使用不同device与端口、共享EC路径，并有cleanup/进程管理；waiting curl成功不是完整业务验收。本次未运行其kill/启动/benchmark。离线PD示例将P设置max_tokens=1并让D继续，实际connector metadata、请求一致性和缓存命中仍按调用链核对，不由代理返回文本直接证明。

external-online-DP说明与run_dp_server示例使用显式DP global/local、TP、地址/网卡和端口；示例IP不是可自动发现的当前环境。设备可见集合、DP rank覆盖、HCCL网络、checkpoint和真实请求分别留证。不同代理实现也不自动共享同一故障重试/恰好一次语义；已读示例不证明生产级全拓扑可靠性。

## 流式重试与重算预算：先确定是哪一个代理

本节补读固定ceac的[layerwise PD实现395–469、491–628](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_prefill_v1/load_balance_proxy_layerwise_server_example.py#L395-L628)及[EPD重试实现446–527](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/disaggregated_encoder/disagg_epd_proxy.py#L446-L527)。两者的`first_chunk_sent`都是“已向下游yield过字节块”，不是“生成过一个token”。

| 入口 | 何时重试 | 首包之后发生异常 |
| --- | --- | --- |
| layerwise PD的`stream_service_response_with_retry` | `httpx.RequestError/HTTPStatusError`分支按尝试次数重试，默认最多3次，等待`base_delay × 2^(attempt−1)` | 上述httpx类型分支仍可重试；只有后面的通用`Exception`分支检查首包标志，已发首包时记录并返回。因此存在重复前缀风险，不能承诺首包后绝不重发 |
| EPD的`stream_retry_wrap` | 未发首包且异常可重试时，默认最多3次尝试，等待`delay × (attempt+1)`；`HTTPException`且状态码小于500直接抛出 | 所有异常先经过首包门禁，已发首包就抛出；调用方还要处理已经开始的HTTP响应 |

layerwise向P发请求时浅复制body，强制`stream=false`、`max_tokens=min_tokens=1`；原body有`max_completion_tokens`时也改为1，并删除`stream_options`。这是生成KV的P阶段预算，不是用户D阶段的总输出预算。P成功后提取`kv_transfer_params`给请求future；不能用它证明D已读到全部缓存。

D返回`stop_reason="recomputed"`时，外层生成循环累积返回文本并重新请求。对于chat，它只取并重写`messages[0].content`，不做完整对话角色重组；文本列表则追加一个text项。completions分支使用`origin_prompt + generated_token`，不能由此推导任意token-ID列表输入都能安全拼接。新预算为：

`max_tokens = origin_max_tokens − completion_tokens + retry_count`

这里`origin_max_tokens`只读取原`max_tokens`，缺省16；`retry_count`在每次recomputed时加1。流式`completion_tokens`对有choices的可解析响应块加1，非流式从`usage.completion_tokens`累计。前者不等于tokenizer计数，后者依赖usage字段，公式也没有给剩余预算做正数校验。一次网络chunk不必是一条完整SSE消息，当前逐chunk JSON解析不提供通用SSE重组保证。

内层传输重试次数与外层recomputed循环分别计数，不能把前者的3次上限当作后者总上限。退出生成循环的`finally`释放decoder负载并调用`cleanup_request_batch`；异常可能被记录后结束响应，而非重新构造可靠的HTTP错误状态。Agent修改代理时应分别验收：首包前失败、首包后httpx失败、recomputed续写、断开清理及非流式usage缺失，保存输出是否重复和负载是否回收的证据。本次没有执行这些服务或故障注入。


## 固定示例职责索引

- `examples/dynamic_bucket_load_balancer/dynamic_bucket_load_balancer.py`：接口/状态与执行顺序示例。
- `examples/disaggregated_encoder/disagg_1e1pd_example.sh`：接口/状态与执行顺序示例。
- `examples/disaggregated_encoder/disagg_epd_proxy.py`：接口/状态与执行顺序示例。
- `examples/disaggregated_prefill_v1/load_balance_proxy_layerwise_server_example.py`：接口/状态与执行顺序示例。
- `examples/disaggregated_prefill_v1/mooncake_connector_deployment_guide.md`：配置与部署说明；记录其版本化声明。
- `examples/dynamic_bucket_load_balancer/README.md`：配置与部署说明；记录其版本化声明。
- `examples/dynamic_bucket_load_balancer/hybrid_proxy_server.py`：接口/状态与执行顺序示例。
- `examples/epd_disaggregated/epd_disaggregated_guide.md`：配置与部署说明；记录其版本化声明。
- `examples/epd_disaggregated/epd_load_balance_proxy_layerwise_server_example.py`：接口/状态与执行顺序示例。
- `examples/external_online_dp/README.md`：配置与部署说明；记录其版本化声明。
- `examples/offline_disaggregated_prefill_npu.py`：接口/状态与执行顺序示例。
- `examples/run_dp_server.sh`：接口/状态与执行顺序示例。

本次只读源码、模板和配置，没有执行示例、下载、安装、部署、测试、量化、NPU或Agent A/B；示例默认值、所称verified或输出打印不提升为本知识卡已复核事件。


## 固定3164：prefill会话亲和与负载调度的取舍

load_balance_proxy_server_example新增--enable-prefill-affinity，默认关闭；启用后仅prefill改为会话亲和，decode继续原负载选路。非空X-Session-Id在请求转发前覆盖body.user；否则使用非空字符串user，再否则以model、首条user及此前system/developer消息构造规范JSON的SHA256。后续对话与采样参数不改变fallback key，没有身份则回负载策略；纯completions要提供显式ID。

选择在未tainted的prefill host:port集合中取SHA256(key+零字节+endpoint)最大者，并以endpoint处理相同分数，因而不依赖Python随机hash或注册次序。集合不变时可跨proxy worker/重启保持路由；移除端点只改原归它的会话，新增端点可吸引部分会话。没有eligible端点明确失败，不能把失败当已预留KV成功。

亲和路径仍更新请求/active KV负载及释放记账，但不会因被选prefill忙而迁走。只有把独立DP rank端点直接注册，才有rank级亲和；隐藏多rank的前置LB不能获得同等保证。它不保留cache容量，也不保证eviction、服务重启或prompt改变后的命中。Agent task、branch、sample应分别使用稳定ID，压缩/重写历史时优先显式ID，不能给所有任务共享一个user值。

新增UT断言增长历史/字典次序不改key、model或首轮内容区分会话、header仅启用时覆盖、初始与重算都传key、移除/tainted端点与失败不泄漏计数，并保留decode负载均衡。它们是源码中的验证入口，本次没有执行代理、HTTP、pytest或真实cache/性能实验。
