---
{
  "type": "Runbook",
  "title": "Qwen3.8 hybrid GDN 模型启用 prefix caching 零命中后回退",
  "description": "来源短提示负载启用 prefix caching 后服务正常，queries=3704、hits=0，随后回退。没有长共享前缀或缓存资格对照，不能据零命中认定 hybrid GDN/自定义 KV 布局语义不兼容，也未测量吞吐影响。",
  "tags": [
    "task.debugging",
    "topic.kv_cache"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Qwen3.8 hybrid GDN 模型启用 prefix caching 零命中后回退

## 适用场景
- vllm-ascend 上部署 hybrid 架构（GDN/Mamba 线性注意力 + 全注意力混合）且使用自定义 KV 布局（as_strided 共享池 + K/V 交错 4D strided 页）的模型时，评估是否开启 vLLM prefix caching。
- 共享系统提示词等重复前缀负载下，判断 block 级前缀缓存是否可用的快速验证流程。

## 触发与观测
- 触发：部署记录剩余优化方向中的"prefix caching（快速验证，~10min）"。
- 观测：移除 --no-enable-prefix-caching 重启后，服务与精度完全正常，但 /metrics 显示前缀缓存零命中：
````text
=== check vllm metrics for cache hits ===
# HELP vllm:kv_cache_usage_perc KV-cache usage. 1 means 100 percent usage.
# TYPE vllm:kv_cache_usage_perc gauge
vllm:kv_cache_usage_perc{engine="0",model_name="qwen3.8"} 0.0
# HELP vllm:prefix_cache_queries_total Prefix cache queries, in terms of number of queried tokens.
# TYPE vllm:prefix_cache_queries_total counter
vllm:prefix_cache_queries_total{engine="0",model_name="qwen3.8"} 3704.0
# HELP vllm:prefix_cache_queries_created Prefix cache queries, in terms of number of queried tokens.
# TYPE vllm:prefix_cache_queries_created gauge
vllm:prefix_cache_queries_created{engine="0",model_name="qwen3.8"} 1.7884411789794853e+09
# HELP vllm:prefix_cache_hits_total Prefix cache hits, in terms of number of cached tokens.
# TYPE vllm:prefix_cache_hits_total counter
vllm:prefix_cache_hits_total{engine="0",model_name="qwen3.8"} 0.0
# HELP vllm:prefix_cache_hits_created Prefix cache hits, in terms of number of cached tokens.
# TYPE vllm:prefix_cache_hits_created gauge
vllm:prefix_cache_hits_created{engine="0",model_name="qwen3.8"} 1.788441178979503e+09
````

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${LAUNCH_ROOT}`：模型启动脚本所在目录。

- 启用改动：
````text
{"filePath": "${LAUNCH_ROOT}/start_vllm.sh", "newString": "    '--gpu-memory-utilization', '0.87',", "oldString": "    '--gpu-memory-utilization', '0.87', '--no-enable-prefix-caching',"}
````
- 重启与 warmup：tmux 重建服务；3 次 warmup 请求输出完全一致。
- 精度与并发验证：2+2 精度测试输出正确（思考后答案 4）；12 并发风暴 ×20 = 20/20 correct in 8.1s（ALL PASS）。
- 缓存命中检查：curl /metrics 过滤 cache/prefix/gpu_block 指标。
- 回退：恢复 --no-enable-prefix-caching 重启，服务健康、答案正确。

## 机制与判别

来源把 hybrid GDN、Mamba 层与自定义 KV 布局的组合列为零命中解释，但这没有通过独立消融证实。短提示可能未形成完整可缓存 block，是否满足缓存资格、请求前缀是否一致及计数采样时刻也未核对。服务与简单问答通过只能说明该有限负载运行正常，不能证明缓存管理器的通用兼容性。

## 验证信号
- 客观信号：事件 1119（warmup 3 次一致）、事件 1122（Storm x20: 20/20 correct in 8.1s / ALL PASS）、事件 1131（queries 3704 / hits 0.0，见上文工件）、事件 1146（回退后服务正常、答案正确）。
- 验证层级：device_functional（服务端到端行为验证）；未观察到缓存命中，性能收益尚未测量（无量化基线对比，未做启用/关闭的吞吐 A/B）。

## 适用与失效边界

来源在这次短提示/简单问答负载下选择回退，是局部部署决策。不能推广为所有 hybrid GDN 模型都应关闭缓存。需增加超过 block 长度的可缓存共享前缀、重复请求和启用/关闭吞吐 A/B，才能判断兼容性与收益；本卡没有这些结果。
