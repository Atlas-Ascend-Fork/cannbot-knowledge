---
type: Guide
title: DeepSeek-V3.2-Exp A3 长序列部署与验收流程
description: 更新当前Docker环境、六份YAML、统一Executor和真实后端/CP/offload约束，删除acl_graph旧配方。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: implementation
created_at: '2026-10-21T09:56:17Z'
updated_at: '2026-10-29T15:02:18Z'
platforms:
- a3
---

# DeepSeek-V3.2-Exp A3：当前统一 Executor 部署

## 环境与权重

当前README采用Docker镜像，宿主Ascend HDK25.2.0，镜像为CANN9.0/PyTorch2.8的模型专用环境，包含torch_npu和所需自定义算子；不要把旧手工安装步骤当作当前首选环境。各节点配置executor/scripts/set_env.sh的IP/CANN路径，挂载同一权重与源码目录。

原始FP8权重在模型目录通过utils/weight_convert.sh转换，quant_mode支持bfloat16/w8a8c16/w8a8c8/w4a8c8；C8两档使用模型专用系数和clip。先source CANN环境，核对权重快照与系数，详见[转换选择](../deployment/quant_weight_conversion_path_selection.md)。

## 当前六份离线配置

以下文件均位于models/deepseek_v3_2_exp/config；表中名字省略公共deepseek_v3.2_exp_前缀和.yaml后缀。

| 文件 | world/batch | 后端 | next_n | 重点 |
| --- | --- | --- | ---: | --- |
| rank_64_64ep_prefill_benchmark | 64/64 | ge_graph | 1 | BF16、CP64 |
| rank_64_64ep_w8a8c8_prefill_benchmark | 64/64 | ge_graph | 3 | C8、CP64 |
| rank_128_128ep_decode_benchmark | 128/256 | ge_graph | 1 | BF16、denseTP4 |
| rank_128_128ep_w8a8c8_decode_benchmark | 128/256 | ge_graph | 3 | C8 |
| rank_128_128ep_w8a8c8_offload_benchmark | 128/256 | ge_graph | 3 | C8、offline Host卸载 |
| rank_64_64ep_w8a8c8_decode_npugraphex_benchmark | 64/256 | npugraph_ex | 0 | 当前原生图量化样例 |

旧aclgraph文件已被npugraphex样例替换，合法exe_mode只有eager/ge_graph/npugraph_ex。配置里的图模式只影响Decode，Prefill仍eager。当前所有表中多流放model_config.custom_params.enable_multi_streams，offload也在custom_params；投影字段统一o_proj_tp_size。

CP要求world_size==cp_size及attnTP1，仅Prefill分段；Decode使用DP+EP及局部投影TP。各自rank/物理卡单位另核对，不把离线CP配置当在线D侧配置。见[CP案例](../../optimizations/cases/deepseek_kimi_a3_prefill_cp.md)。

## 启动与功能组合

从仓根执行，例如：

```bash
bash executor/scripts/infer.sh --model deepseek_v3_2_exp --yaml deepseek_v3.2_exp_rank_128_128ep_w8a8c8_decode_benchmark.yaml
```

模型已使用统一Executor；InfiniteBench文件放dataset/InfiniteBench，也可用default_prompt。每节点分别启动，日志在模型res目录。在线PD用--mode online和角色/config，offload被模型明确禁止用于在线。

MLA仅q_b投影W8A8、SFA INT8存/BF16算、Indexer A8C8与路由专家W8A8/W4A8等粒度见[量化机制](../../concepts/quantization/w8a8c8.md)。当前量化SFA函数是npu_kv_quant_sparse_flash_attention。PyPTO Prolog与LI有不同量化门控，不与AscendC/TileLang配置混用。

模型eager拒绝多流、SuperKernel或cache_compile，npugraph_ex拒绝SuperKernel。offload使用统一SWAPPED_MEMORY缓存加独立设备workspace，不能只预算Host Full KV。MTP需核对实际预测层权重、状态和接受长度，样例宽度不等于收益承诺。

## 验收、停止与回退

先保存合法eager/关闭待验特性的输出与资源基线，再依次验证融合、量化、图、多流、CP、投机及offload。覆盖变长/多请求、边界长度、EOS、缓存所有者，比较输出/任务精度、峰值内存、TTFT与Decode计时；分开冷启动、预热、稳态和服务端时延。

[性能来源](../../optimizations/benchmark_observations/deepseek_v32_a3_source_benchmark.md)仍有MTP3/perfect-EPLB数据，不能把人工路由结果作为生产精度基线；[当前精度表](../../optimizations/benchmark_observations/benchmark_deepseek_v32_quant_accuracy.md)缺评测环境。失败时恢复权重、合法配置及缓存，本次没有模型执行或硬件复测。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/README.md)（primary）
- [deepseek_v3.2_exp_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（implementation）
