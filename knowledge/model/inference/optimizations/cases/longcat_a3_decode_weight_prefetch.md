---
type: Optimization
title: LongCat A3 Decode 权重预取：QBMM 与 MLA_Prolog 的相邻排布
description: 当前 LongCat GE/npugraph_ex 的 Decode 预取开关、专用 stream、事件依赖与字节预算边界。
tags:
- task.optimization
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-10-20T11:23:20Z'
updated_at: '2026-10-29T13:44:43Z'
platforms:
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
      execution_mode:
      - ge_graph
      framework:
      - cann_executor
      model_features:
        all_of:
        - mla
---

# LongCat A3 Decode 权重预取

## 当前入口

model_config.custom_params.enable_prefetch 必须与 enable_multi_streams>0 同开，后者只在 Decode 进入多流前向。单开预取在模型校验时报错。当前 GE 与 npugraph_ex 都有预取路径，不能继续沿用仅 GE 的旧 runner 描述。

## 排布与依赖

为 MLAProlog 留出带宽窗口，先预取前置 QBMM/MLP 权重；attention、dense MLP 和下一层还在 o_proj、dsq、down_proj 等依赖点预取。字节数随量化和 TP 计算，不是通用缓存容量。

npugraph_ex 使用专门的预取 stream：attention o_proj、MLP gate-up/down 等点记录事件，预取流等待后再搬权重。模型创建预取流的条件为 npugraph_ex、多流与预取同开；不能将 GE 的 tagged-stream API 复制到该路径。多流入口本身不覆盖 Prefill。

## 验证与回退

按[预取规则](../rules/decode_weight_prefetch_ordering.md)比较关闭/开启的输出、带宽、发起与消费时刻、TPOT。来源整网 benchmark 含 MTP2/perfect EPLB，不能归因于预取。本次仅静态审查。劣化时关闭 enable_prefetch，保持其他条件不变并使用匹配编译产物。


## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
