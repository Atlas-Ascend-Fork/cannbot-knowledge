---
type: Concept
title: SGLang 昇腾路由的 count、逆映射与 scale 复用
description: 明确 RoutingV2 的量化枚举和 expert 顺序，并区分计数、累积边界以及 weighted/unweighted finalize。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/routing.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/standard_dispatch.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/quant.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/matmul.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:31:21Z'
platforms: []
---

# SGLang 昇腾路由的 count、逆映射与 scale 复用

## 路由元数据是一组契约

RoutingV2 返回 expert 顺序 payload、row map、INT64 expert token counts 和可选 scale。该封装的 BF16/INT8/MXFP8 mode 分别为 `-1/1/3`；MC2 dispatch 的 `0/2/4` 是另一套枚举，不能互换。MXFP4 常量的存在也不表示 StandardDispatcher 已开放此 wire dtype，后者只映射 BF16、INT8、MXFP8。

已有 per-token scale 时，调用 `npu_moe_init_routing` 封装仍须传入原量化 mode `1/3/9`（INT8/MXFP8/MXFP4）；外层传 `-1` 会被拒绝。封装仅在内部调用 `npu_moe_init_routing_v2` 时改用 `quant_mode=-1`，并按外层 mode 设置 `x_dtype`，只重排并复用 scale，不再次动态量化；MX flat scale 可规范化为 pair 布局，重复规范化保持幂等。active_num 与 top-k 展开容量影响逆映射，必须按调用方的有效路由范围传入。

## counts 与 finalize

Ascend runner 通常以 group_list_type=1 表示每 expert 的 count；融合 GMM+SwiGLU 接口则需要 cumulative group_list，封装在调用前对 counts 做 cumsum，不能把所有 group_list 参数都按同一种含义解释。普通 finalize 不带权重仅 unpermute，带 topk weights 才执行 weighted TopK 汇合；封装只在 hidden_states 行数非零且与 expanded_row_idx 行数不等时显式报错。传入 topk_ids 会启用 export 语义，作为 export_for_source_row 透传，用于跳过无效（drop 或重复）路由；调用方可用非本地专家 sentinel 完成汇合，不能把所有无效 ID 一概视为失败。

检查元数据时同时保存 payload/scale dtype、expert counts 总和、row map 范围、有效 TopK IDs 与输出容量。用单 token、多 token、空 expert、padding 和已有量化输入分别比较 unfused 参考结果。切换 dispatcher 或 kernel 时应重建配套元数据，复用旧逆映射可能产生无报错错位。本卡只描述模型级路由封装，未分析 Device 内部实现或声称已执行验证。
