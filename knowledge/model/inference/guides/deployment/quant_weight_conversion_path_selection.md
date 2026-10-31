---
type: Guide
title: 量化部署：先检查权重格式，再选转换或直载
description: 昇腾量化权重制备与部署路径：离线系数配合 convert_model.py、原始 compressed-tensors 权重直载、amct 重新标定；按模型、格式与平台选择并验收精度。
tags:
- task.debugging
- topic.precision
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/utils/weight_convert.sh
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/README.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/README.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/kimi_k2_thinking.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:57:02Z'
platforms:
- agnostic
aliases:
- 量化权重部署指南：离线转换、原始权重直载与验收
---

# 量化部署：先检查权重格式，再选转换或直载

## 当前模型路径

| 模型 | 权重入口 | 当前操作 |
| --- | --- | --- |
| V3.2-Exp | 原始FP8→BF16/Int8 | models/deepseek_v3_2_exp/utils/weight_convert.sh，quant_mode支持bfloat16/w8a8c16/w8a8c8/w4a8c8 |
| Kimi-K2-Thinking | 原始发布权重 | 当前kimi_k2_thinking.yaml直接指model_path，无仓内weight_convert.sh和旧rank_64/rank_128 benchmark YAML |

V3.2-Exp脚本的w8a8c8/w4a8c8分支下载各自模型系数包，使用--clip及quant_param_path；BF16和W8A8C16不走同样下载分支。不要复制兄弟模型硬编码的系数URL。需离线使用时先确认系数与目标权重对应；改权重快照后需重新校准，不能仅改目录名。

Kimi当前YAML没有mm_quant_mode/gmm_quant_mode字段。ModelWorker读取HF quantization_config（可回退compression_config），规范化compressed_tensors名称并选量化实现，再由模块loader识别实际scheme。默认原始Kimi方案为普通Linear16bit/MoE W4A16，不是纯BF16；YAML文件名不决定量化格式。

## 转换和验收

在各节点source实际CANN环境后，进入对应模型目录执行其转换脚本，完整保存原始与输出目录、系数、量化配置和日志。不要从历史Issue推导存在msit/msmodelslim的通用w8a8c8命令。

运行时先读当前README、YAML、checkpoint与加载器，确认Linear/GMM/Cache各自量化模式、dtype、scale和后处理；同名位宽在不同模型可能对应不同粒度和算子。仅改model_path也必须重新检查缓存、开关及平台兼容。

先用真实权重验证确定性输出及目标任务精度，再比较峰值内存、TTFT、Decode执行与端到端耗时；缺scale、scheme识别失败或精度不符时回到已保存的权重基线。转换加载成功不等于精度或性能验收。

参见[C8接线](../../optimizations/rules/mla_c8_int8_kv_cache_op_wiring.md)、[权重在线切分](../../concepts/techniques/online_weight_split.md)及[量化布局](../../optimizations/rules/quant_weight_load_layout_and_naming.md)。本次仅源码审阅，未执行转换或NPU代码。


## Evidence

- [weight_convert.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/utils/weight_convert.sh)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/README.md)（implementation）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/README.md)（implementation）
- [kimi_k2_thinking.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/kimi_k2_thinking.yaml)（implementation）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）
