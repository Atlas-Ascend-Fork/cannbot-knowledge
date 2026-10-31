---
type: Guide
title: LongCat-Lite A2/A3 的 TP、EP 部署与验收流程
description: 当前四类Lite配置、统一离线入口、已实现SP、MC2回退、无旧Prolog开关、GE多流及文档/源码差异。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_tp.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: supporting
created_at: '2026-10-21T09:56:19Z'
updated_at: '2026-10-29T13:59:24Z'
platforms:
- a2
- a3
---

# LongCat-Lite A2/A3 当前部署与验收

## 环境与权重

按当前README准备CANN9.0.0、PyTorch2.8.0/torch_npu26.0.0及模型requirements，核对实际设备和可见进程数。BF16与compressed-tensors W8A8权重分别匹配model_path；当前量化MoE专家和Dense MLP，MLA保持BF16。

## 当前四类配置

| 文件 | 使用条件 |
| --- | --- |
| longcat_flash_lite_rank_8_8tp.yaml | BF16、全模块TP8、batch1 |
| longcat_flash_lite_rank_8_8ep.yaml | BF16、EP8、attn_tp4/attn_dp2，N-gram TP8 |
| longcat_flash_lite_rank_8_8ep_w8a8.yaml | W8A8、EP8、默认Decode MoE overlap |
| longcat_flash_lite_rank_16_16ep_w8a8.yaml | W8A8、EP等比扩展，核对整除与实际设备 |

旧b8/4k1k独立YAML不再是当前清单；修改scheduler_config.batch_size、data_config.input_truncated_len、max_new_tokens并提供匹配prompt。N-gram表和主Embedding的TP是不同配置，不能继承满配LongCat的AFD/KVP开关。

## 运行与实现边界

```bash
bash executor/scripts/infer.sh --model longcat_flash_lite \
  --yaml longcat_flash_lite_rank_8_8tp.yaml
```

当前样例只声明offline。GE为默认，npugraph_ex为另一后端；Decode MoE overlap仍调用GE scope helper，迁移后端时先关闭并独立验证该组合。custom_params.enable_moe_stream_overlap默认False，enable_limit_core_num默认True，核数可由当前代码的对应字段调整。

EP Prefill的RS+AG现已实现；纯TP不触发is_sp。A2 routed experts/rank>24会回退double routing，不能把A3 MC2行为直接套用。Decode当前直接调用MLA Prolog，旧enable_mla_prolog=false不再是可用回退开关。

共享编译器实际缓存路径为output_path/compile_cache，可按decode宽度分区；README的config/cache_compile路径与代码不一致，此处按代码。README长序列OOM建议中的kvp_size也不在当前公共配置或该模型实现中，不能据此添加该键。

## 验证与回退

先固定权重、平台、并行和输入，验输出后再逐项比较量化、多流、图模式与batch。报告将BF16 token分歧解释为语义等价，不能代替业务精度标准。分别保存首次编译、稳态、输出误差与峰值内存。

失败时恢复合法串行/eager和匹配缓存；Prolog等无当前配置回退的路径需先定位模型实现，勿填写失效flag。来源性能不保证任意新batch/长序列达到同值，本次未运行NPU。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md)（primary）
- [modeling_longcat_flash_lite.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（implementation）
- [optimization_report_tp.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_tp.md)（supporting）
- [optimization_report_ep.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md)（supporting）
