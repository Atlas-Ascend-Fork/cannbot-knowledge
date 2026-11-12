---
type: Guide
title: SGLang 昇腾 DSV4 与 Xing4 的超连接布局约定
description: 区分950 HC batch轴、Xing4矩阵方向，以及DSV4非CUDA分支的deferred残差收尾与DP行传输。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v4_mhc.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/xing4_0.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/layernorm/mhc.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v4_platform_stage.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_common/moe_transport.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:22:44Z'
platforms: []
---

# SGLang 昇腾 DSV4 与 Xing4 的超连接布局约定

## DSV4 HC post 的版本布局

DSV4 的 HC 状态逻辑上为 residual `[T,mult,H]`、post_mix `[T,mult]`、comb `[T,mult,mult]`。非 arch35 NPU 直接调用 custom.npu_hc_post；950 构建要求每个 operand 增加 leading batch 轴，结果再 squeeze(0)。空 token 直接构造 `[0,mult,H]`，不能让空张量触发不支持的 kernel。

HC pre 只完成混合/Sinkhorn 内部归一化，不包含子层 input_layernorm，所以 norm_fused=False；y 恢复输入 dtype，post/comb 保持 FP32，idle dummy 也遵守此约定。

## Xing4 的矩阵方向

Xing4 接收 flattened residual `[T,n*C]`，NPU pre 先 view 成 `[T,n,C]` 并转 BF16，参数 fn/scale/base 为 FP32。返回 comb_mix 先 transpose 最后两轴并 contiguous，再 flatten 为 `[T,n*n]`；此方向匹配 checkpoint 的训练约定。不能因与 DSV4 API 名相似就删除转置。Xing4 pre 同样不融合 output Norm，post 再恢复多流 residual 的 flattened shape；空输入保留 FP32 mixing metadata。

比较显式 torch 混合公式、连续与空批次、950 leading axis 和 checkpoint mixing direction；检查 norm_fused 防止漏做/重复 RMSNorm。更改布局需同时更改生产和消费状态，回退恢复原 adapter 与权重。本卡未执行 kernel 或评估性能，不从单个 HC 功能推广整体型号支持。

## 非 CUDA 层的 deferred 状态与 DP 行传输

DSV4 NPU 平台 decoder 继承 NonCudaDecoderMixin。use_fused_mhc_post_pre 打开时，本层可返回 hidden/residual/post/comb 给后继消费；融合边界函数返回 None 时先完成旧 hc_post，再做本层 hc_pre，且 norm_fused=False 时必须补 Norm。最终层/单层 draft 没有后继，需显式完成 deferred state。不能把四元组当普通 hidden，也不能同时提前完成和交给下一层重复完成。

FFN 通过 MoeRowTransport 适配 CP、attention DP 无A2A gather、以及attention TP有A2A的token scatter。已在attention-TP复制的hidden用replicate gather，防止求和倍增；变长DP优先reduce_scatterv，等长ReduceScatter另需MAX_LEN和TP=attention-DP等条件。shared expert可先在本地行计算，再加回恢复后的local routed slice；hash路由ID与hidden必须同分片。scope临时设置mlp_reduce_scatter并退出恢复，不能泄露给下一层。验证时除HC公式，还需比较DP不等长行、shared加和与deferred状态恰好完成一次。
