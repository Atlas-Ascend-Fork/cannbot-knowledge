---
type: Guide
title: vLLM Ascend ModelOpt MXFP8：别名、排除层与量化方法选择
description: 区分mxfp8/modelopt_mxfp8与原生block FP8加载，保留ModelOpt解析器和exclude映射，核对vision回退及Linear/MoE实际scheme。
tags:
- task.implementation
- topic.precision
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/modelopt_mxfp8_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/configs/test_modelopt_mxfp8_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/utils.py
  role: constraint
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
updated_at: '2026-10-29T11:32:34Z'
---

# vLLM Ascend ModelOpt MXFP8：别名、排除层与量化方法选择


## 先识别格式

固定ceac1a2b中AscendModelOptMxFp8Config继承上游ModelOptMxFp8Config，同时注册mxfp8和modelopt_mxfp8。它不使用ModelSlim的quant_model_description逐层字典，也不是原生fp8配置的别名；后者的block-scale展开/重组见[原生FP8规则](../../optimizations/rules/vllm_ascend_native_fp8_execution.md)。本来源未给整个ModelOpt入口的明确产品范围，保持draft，不从MX算子或某模型的局部支持扩大为所有硬件。

## 排除先于量化

先执行is_layer_excluded。被排除的embedding/LM head取UnquantizedEmbeddingMethod，Linear取AscendUnquantizedLinearMethod，MoE取AscendUnquantizedFusedMoEMethod；其他类型返回None。上游mapper会映射exclude_modules，必须同时检查映射后的名称。

为兼容旧checkpoint，vision_tower、vision_model、vit_large_projector前缀还单独保留浮点方法；不能为了提高量化覆盖率删除这些回退。它们是明确代码边界，不代表所有vision子树已在每种模型里列全。

## 实际分派

未排除的Linear/ParallelLMHead包装AscendW8A8MXFP8DynamicLinearMethod；MoE包装对应MXFP8 FusedMoE scheme，并传入moe_config及tid2eid。embedding与BF16 KV继续原生方法，返回None不等于错误，也不说明KV变成MXFP8。

Linear scheme读取quant_description时容忍不存在，group_size默认32；激活scale算法由硬件能力和当前模型/forward context选择。MiniMax-M3在具备对应能力时使用scale_alg=1以控制FP8溢出，不能机械对所有模型启用或回退为0。

## 加载和更新验收

保存config.json中原始quant_method、上游解析结果、exclude列表、mapper和每层真实方法；核对weight/scale dtype、group phase及post-load布局。上游测试源码覆盖两个别名、排除层映射、Linear/MoE分派和embedding/KV保留，但这些mock断言不能证明数值或硬件执行。

RL重复加载须检查实际MXFP8 scheme的restore→load→postprocess协议及graph持有的地址。Linear实现缓存变换后的weight/scale buffer以维持重放地址，首次分配和后续copy不同；不能假设任意shape/padding的restore都已由此证明。失败保持暂停并恢复完整已知权重，不能服务部分更新模型。本次未执行上游测试、权重加载或性能实验。
