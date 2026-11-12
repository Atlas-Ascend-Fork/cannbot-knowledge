---
type: Optimization
title: LongCat A3 Decode 权重预取：QBMM 与 MLA_Prolog 的相邻排布
description: LongCat A3 Decode GE/npugraph_ex 的 QBMM/MLAProlog 预取：18/36/7 MiB、GMM1 int8 每专家字节预算、触发窗口与事件依赖。
tags:
- task.optimization
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-prefetch/SKILL.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py
  role: supporting
created_at: '2026-10-20T11:23:20Z'
updated_at: '2026-11-10T04:11:13Z'
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
      - npugraph_ex
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

## 固定实现的字节预算与触发点

| 预取目标 | 触发依赖 | 固定参考范围 |
| --- | --- | --- |
| router.classifier | o_proj 输出；下一层也可由 gmm2_out 触发 | Attention 路径固定 18 MiB；FFN 路径按权重维度计算 |
| q_a_proj / q_b_proj / kv_a_proj_with_mqa | dense 中间 dsq；下一层用 down_proj 输出 | 分别 18 / 36 / 7 MiB，即对应整数乘 1024×1024 字节 |
| dense gate_up_proj | o_proj 输出 | H×I×2×dtype_bytes / dense_tp_size |
| dense down_proj | gate/up 所在计算窗口，按实际事件依赖 | H×I×dtype_bytes / dense_tp_size |
| experts.w2_weight | router_logits 输出 | H×I×dtype_bytes / moe_tp_size × experts_per_rank |
| 下一层 experts.w13_weight | 当前层 gmm2_out 输出 | FFN 分支为 H×I×2×dtype_bytes / moe_tp_size × experts_per_rank / 2 |

dtype_bytes 在该实现 W8A8 时为1，其他所示分支为2；代码变量虽叫 dtype_bit，公式实际用字节。GMM1 末尾的 /2 是该分支预算选择，不是权重大小的数学定义。18/36/7 是该 A3 模型的预取范围，不是通用缓存容量、起始 offset 或其他平台推荐值；不能以“理论大小取50%”覆盖当前各调用点的真实范围。

大型 MatMul 的输出可以作为后续权重预取的依赖，但应检查它完成后到目标消费之间是否真有可用窗口。原生预取流须等待生产事件，消费方也须收口；不能只复制 npu_prefetch 调用而省略事件。先以实际本 rank tensor 的 shape、dtype 和切片范围复核预算，再逐项调整，过度预取可能挤占缓存和带宽。

## 验证与回退

按[预取规则](../rules/decode_weight_prefetch_ordering.md)比较关闭/开启的输出、带宽、发起与消费时刻、TPOT。来源整网 benchmark 含 MTP2/perfect EPLB，不能归因于预取。本次仅静态审查。劣化时关闭 enable_prefetch，保持其他条件不变并使用匹配编译产物。


## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）

- [.agents/skills/model-infer-prefetch/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-prefetch/SKILL.md)（supporting）

- [models/longcat_flash/models/ffn.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py)（supporting）
