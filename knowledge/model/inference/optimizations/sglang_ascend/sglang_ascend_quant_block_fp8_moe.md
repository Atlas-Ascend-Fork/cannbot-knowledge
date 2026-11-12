---
type: Optimization
title: SGLang 昇腾 block FP8 MoE 的默认原生与 opt-in MX 路径
description: 说明 BF16 dispatch、原始 FP32 scale、MX 低延迟通信与激活融合守卫之间的关系。
tags:
- task.optimization
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/block_fp8_moe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/gemm/npu_block_fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_utils.py
  role: implementation
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:43Z'
platforms: []
---

# SGLang 昇腾 block FP8 MoE 的默认原生与 opt-in MX 路径

## 默认与可选机制

该类承接 arch35 的 `[128,128]` FP8 expert checkpoint。默认保留原始 E4M3 权重与 FP32 block scale，两个通信模式均使用 BF16 dispatch，w13/w2 走原生 G-B grouped matmul；每个 expert 的 token 数可为零。仅 `SGLANG_NPU_ARCH35_REQUANT_BLOCK_FP8=1` 才逐 expert 转 MXFP8，normal 模式仍 BF16、low_latency 模式改为 MXFP8，加载后有幂等 guard 避免再次重排。

runner 只接受 auto/ascend；显式 dispatcher_output_dtype 只允许 auto 或 bf16。当前方法不支持 bias，仅支持 gated SiLU，拒绝 alpha/beta/clamp_limit；swiglu_limit 则走已有带限幅激活约定。不能把参数名字相近的 clamp_limit 与 swiglu_limit 当成同一开关。

## 识别错误与启用步骤

LL 的量化输入必须是 E4M3 payload 加 E8M0 或 uint8 原始 scale bytes；普通 FP8 payload 加 FP32 scale 会被拒绝。没有 scale 只有在明确 BF16 fallback 时允许。检查 dtype 和 scale 解释，比仅检查 Tensor shape 更重要。

先以默认路径验证 expert 输出、空组与模型精度，再在重启加载前开启 opt-in，分别测 normal/LL 通信量与实际延迟。转换有加载成本，但误差边界取决于传入的scale_fmt：ue8m0分支仅展开幂二尺度到MX子组并转置布局，保留权重字节、无新增重量化误差；普通FP32 scale分支才先反量化再MX重量化，可能引入新增误差。ue8m0的无损结论限于满足原scale格式及布局/维度检查的转换，不是整个模型计算无误差；清除变量并重新加载 checkpoint 回退。测试源码只能证明有对应断言入口，当前摄入未运行上游测试或真机性能测量。
