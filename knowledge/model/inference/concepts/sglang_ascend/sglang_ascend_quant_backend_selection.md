---
type: Concept
title: SGLang 昇腾量化配置与后端选择边界
description: 区分量化注册名、权重格式、Dense 与 MoE 分派，避免把 GPU 配置名等同于 NPU 内核支持。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/__init__.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/npu_mxfp4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/npu_mxfp4_w4a4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/unquant.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-08T12:01:09Z'
platforms: []
---

# SGLang 昇腾量化配置与后端选择边界

## 配置名与实际执行链

固定版本的量化注册表在 NPU 上把 `gptq` 指向 `GPTQAscendConfig`，把 `mxfp4` 指向 NPU 专用配置；`mxfp8` 复用 `Fp8Config`。注册成功只说明能够构造配置，仍须检查具体 layer 的 `get_quant_method`、加载后处理、MoE runner 与 dispatcher。

`Fp8Config` 对 MXFP8 固定采用 `[1,32]` 块；在线未量化权重与离线序列化权重分别经过量化和布局分支。NPU Dense 选择 `NPUMXFP8LinearMethod`，MoE 选择 `NPUMXFP8OnlineMoEMethod`；ignored layer 经 packed-module 映射匹配后保留未量化方法。arch35 的 `[128,128]` block-FP8 与 DSV4 FP4 experts 另有守卫。

## 适配步骤与边界

先核对 checkpoint 的 quantization_config、scale 格式和是否预量化，再查看 Dense、routed experts、shared experts 是否实际选中同一方法。在线 MXFP4 配置对 MoE 会告警并保留全精度专家；这不能推出离线 FP4 expert checkpoint 不受支持。未量化 NPU MoE 也进入 Ascend runner，量化 kernel 自己设置 dispatcher dtype，公共父类不会再次硬编码 BF16 覆盖子类。

排查时记录每类 layer 的 quant_method、w13/w2 kernel、runner 和实际通信 dtype；以同一模型全精度输出作精度基线。配置名不构成产品型号范围或性能结论；本卡未获得覆盖整个选择树的型号证据，保留 draft。
