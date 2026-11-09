---
type: Guide
title: vLLM Ascend 共享专家多流：PreparedLinearInput 的生产与消费
description: 将量化预处理前移到调度屏障前时保留dtype、scale、padding和LoRA语义，区分输入准备、GEMM时序与host提交顺序。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.precision
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/base.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/prepared_linear_input.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/shared_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/w8a8_dynamic.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/w8a8_static.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/w8a8_mxfp8.py
  role: implementation
created_at: '2026-10-29T11:32:34Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
      model_features:
        all_of:
        - moe
updated_at: '2026-10-29T11:32:34Z'
---

# vLLM Ascend 共享专家多流：PreparedLinearInput 的生产与消费


## 适用任务

固定ceac1a2b，面向新Linear量化scheme接入共享专家多流优化。这里约束Python接口与调度，不替代底层算子完整分析；没有整项功能硬件范围证据，保持draft。使用前先按[scheme流程](vllm_ascend_modelslim_scheme_adaptation.md)完成普通执行的正确性。

## 显式选择，保持原路径

AscendLinearScheme.prepare_input_for_overlap默认返回None。调用者只有在multistream_overlap启用、无LoRA、输入仍是Tensor且实际scheme提供hook时尝试前移；未支持则保留原Tensor与注册Linear路径。不能直接跳过wrapper、假定所有scheme都能独立量化，也不能对已经带scale的输入重复准备。

PreparedLinearInput包含quantized、可选scale和output_dtype。生产hook和apply必须成对适配：动态W8A8消费非空per-token scale并保留输出dtype；静态W8A8使用层中已有scale/offset，不要求相同动态字段。MXFP8先执行本scheme的padding和scale算法，再消费准备结果；普通tuple输入在该实现默认BF16，不能用tuple替代对象后假定输出dtype仍与原输入相同。

只有不改变shape、dtype、padding、scale或LoRA语义才可opt-in。当前共享专家使用二维输入的hook，高维输入仍走wrapper以保留原reshape。移动前后比较实际数值与元数据，不能仅看dataclass类型。

## 设备依赖与host提交分别正确

共享输入ready事件之后立即向辅助流提交Vector/AIV预处理，使其有机会覆盖router的Cube计算；Gate-Up GEMM仍等待router_output_ready，并在routed TopK/dispatch之前提交。只提前record event、却等整个routed MoE提交完才enqueue辅助工作，不会自动产生预期重叠。

Down激活/量化可在指定routed阶段准备，Down GEMM仍遵守combine依赖。现有融合SwiGLU+MX准备还要求精确scheme/activation类型、无LoRA、BF16二维输入、默认scale算法/group、无TP padding、输入并行、对齐和算子存在；不能从W8A8MXFP枚举单独放行全部融合。

## 验收与回退

用相同weight/输入/采样比较原路径与准备路径，检查只量化一次、scale消费、padding、输出dtype/reshape及LoRA回退。再看host enqueue、stream wait和kernel时间线，分别证明顺序正确和重叠发生，最后测端到端收益。未知wrapper返回原输入即可回退，不能绕过barrier追求表面并行。本次未执行NPU、多流或性能A/B。
