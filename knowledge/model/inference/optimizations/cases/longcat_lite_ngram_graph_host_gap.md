---
type: Optimization
title: LongCat-Lite A2/A3 入图案例：NgramEmbedding host gap 与精度边界
description: 当前N-gram buffer/packed图适配和A2来源对照，撤下旧A3中间值并区分最终Prolog组合结果。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_tp.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md
  role: constraint
created_at: '2026-10-20T12:16:14Z'
updated_at: '2026-10-29T13:59:24Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - latency
      - tpot
      model_features:
        all_of:
        - moe
        - mla
      execution_mode:
      - ge_graph
      quantization:
      - bf16
      parallelism:
        all_of:
        - tp
      framework:
      - cann_executor
---

# LongCat-Lite N-gram 入图与 Host gap

## 条件与机制

当前TP优化报告覆盖A2/A3、BF16、TP8、batch1，主案例输入1024/输出128。N-gram子模块包含大量小算子与子表通信，设备占比小不代表图外Host开销小。

实现以预分配ngram_context buffer、原地copy_和静态展开shift-right保持可捕获，并将Embedding纳入完整Decode图；packed Prefill另按段边界处理。当前buffer为persistent=False，在权重处理完成后按实际batch初始化，不能称为checkpoint持久状态。

## 当前报告结果与边界

TP报告的A2累计阶段表记录GE但N-gram在图外18.5ms，入图后7.14ms；同报告A3最终含MLA Prolog的结果为5.76ms。后者不是A3单独N-gram消融，不能和旧A3中间阶段数字拼成同一对照。

报告将图外约11ms的差值主要解释为Host小算子/通信下发；没有原始时间线时不能将差值完全归因于Python。BF16约20 token后分歧的作者解释也不等于精度验收。

## 验证

按[图模式决策](../rules/graph_mode_enable_decision_profiling.md)分别测图外模块wall-clock、设备时间线和端到端Decode，固定软件、Prolog与并行，检查多请求N-gram上下文和token/任务精度。本次未运行模型。


## Evidence

- [optimization_report_tp.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_tp.md)（primary）
- [modeling_longcat_flash_lite.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（implementation）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md)（constraint）
