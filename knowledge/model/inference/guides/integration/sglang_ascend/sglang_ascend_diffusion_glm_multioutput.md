---
type: Guide
title: SGLang Diffusion GLM-Image：NPU顺序多输出与条件切片
description: 说明模型/配置/阶段如何将多输出请求串行化，以及无KV缓存时逐sample attention裁剪的成本。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/dits/glm_image.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/configs/pipeline_configs/glm_image.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/model_specific_stages/glm_image.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/unit/test_glm_image_multi_output.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/unit/test_pipeline_executor.py
  role: implementation
created_at: '2026-11-08T12:27:27Z'
updated_at: '2026-11-08T12:27:27Z'
platforms: []
---

# SGLang Diffusion GLM-Image：NPU顺序多输出与条件切片

## 触发与模型分支

GLM-Image的NPU配置启用sequential_multi_output及顺序DiT策略，避免把多张输出合并为普通batch。模型forward在batch>1且无KV cache时逐sample递归，切片相应conditioning；按mask求有效text长度并裁掉padding，再清除该sample的mask，不能保留原多batch掩码指向已经缩短的序列。

逐sample可避开NPU多batch形态限制，但带来Host长度读取、重复调用和串行成本，不承诺同吞吐。使用KV cache时不进入此分支，不能普遍认为所有GLM batch都被切开。stage和pipeline executor还负责多输出的请求级顺序、结果收集与清理。

## 接入与验收

分别测试单输出、多输出与KV cache开关，核对每sample的文本、图像条件、随机种子和最终结果顺序；确保一张输出的状态不泄漏到下一张。对比参考实现的形状和质量，再统计每张与整请求耗时。单元测试可证明调度结构，不等价于NPU真机质量。本次没有执行推理，平台未知。
