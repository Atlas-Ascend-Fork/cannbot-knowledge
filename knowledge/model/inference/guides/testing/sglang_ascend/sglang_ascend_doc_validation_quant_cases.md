---
type: Guide
title: SGLang NPU权重量化回归的模型与质量门槛
description: 对齐AutoRound、GPTQ、GGUF和W4A4测试的checkpoint、TP与GSM8K目标，避免量化格式名直接等于兼容性或性能收益。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_autoround_dense.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_autoround_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_gguf.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_gguf_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_gptq_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_w4a4_quantization.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/gsm8k_ascend_mixin.py
  role: implementation
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:36:38Z'
platforms:
- a3
---

# SGLang NPU权重量化回归的模型与质量门槛

## 逐格式质量验收定义

来源注册A3，未执行。这些测试只证明仓库定义了以下checkpoint/配置的验收目标，不代表同名格式所有权重通用支持，也不形成相对BF16的性能收益。PR多数改运行smoke，非PRGSM8K才作质量比较，参见[共同契约](sglang_ascend_test_gsm8k_contract.md)。

| 测试权重 | 配置与GSM8K目标 |
|---|---|
| Qwen3-8B AutoRound INT4 dense | 目标0.85；非PR1319题、5shot、max512、parallel128 |
| Qwen3-30B AutoRound INT4 MoE | 目标0.85，同类非PR完整题集 |
| Qwen3-30B GPTQ INT4 MoE | 目标0.85，同类非PR完整题集 |
| Qwen3-4B GGUF Q4_K_M | TP1，1319题目标0.80 |
| Qwen3-30B MoE GGUF Q4_K_M | TP2，1319题目标0.85 |
| Qwen3-32B W4A4 | TP4，1319题、5shot，实际评测128线程（子类gsm8k_parallel=64未被入口消费），目标0.80 |

GGUF文件和量化checkpoint应固定，与命令量化参数一起记录；“INT4”“W4A4”不唯一标识量化布局、kernel或校准流程。部署量化选择及950 MXFP8边界见[量化指南](../../optimization/sglang_ascend/sglang_ascend_doc_quantization_selection.md)。完整比较需相同数据集、采样、输入输出长度和硬件，另记录吞吐/时延/内存；本组测试并未给出该比较。

## Evidence

- [test/registered/npu/basic_function/quant/test_npu_autoround_dense.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_autoround_dense.py)（primary）
- [test/registered/npu/basic_function/quant/test_npu_autoround_moe.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_autoround_moe.py)（supporting）
- [test/registered/npu/basic_function/quant/test_npu_gguf.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_gguf.py)（supporting）
- [test/registered/npu/basic_function/quant/test_npu_gguf_moe.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_gguf_moe.py)（supporting）
- [test/registered/npu/basic_function/quant/test_npu_gptq_moe.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_gptq_moe.py)（supporting）
- [test/registered/npu/basic_function/quant/test_npu_w4a4_quantization.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/quant/test_npu_w4a4_quantization.py)（supporting）
