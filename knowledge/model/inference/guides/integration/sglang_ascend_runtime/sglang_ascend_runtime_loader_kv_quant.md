---
type: Guide
title: SGLang NPU权重加载的融合模块映射与KV量化配置
description: 说明NPU视觉与语言融合权重映射、ModelSlim target/draft KV dtype配置、跳过CUDA capability检查及校准scale来源边界。
tags:
- task.implementation
- topic.memory
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_loader/loader.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/model_runner_components/load_model_utils.py
  role: implementation
created_at: '2026-11-08T12:10:39Z'
updated_at: '2026-11-08T12:10:39Z'
platforms: []
---

# SGLang NPU权重加载的融合模块映射与KV量化配置

_get_quantization_config在NPU扩充packed_modules_mapping：visual的qkv/gate-up，vision_model的qkv/proj，语言model的qkv、gate-up、MLA fused q/kv-a及index_qkv。它描述checkpoint名称到融合参数的映射，不保证所有模型同时具有这些模块，也不等于任意checkpoint格式可混用。

ModelSlim配置读取requested KV dtype：draft模型且显式speculative_draft_kv_cache_dtype时用draft值，否则用全局KV dtype，再configure_kv_cache_quantization。NPU跳过按CUDA major×10+minor的minimum capability检查，但仍检查模型activation dtype是否在量化配置支持列表；跳过GPU检查不是昇腾能力全部通过。

load_kv_cache_scales在NPU且ModelSlim时直接返回，因为scale随checkpoint权重加载；不能再要求通用quantization_param_path校准文件来覆盖该语义。其他fp8_e4m3路径才按独立文件/模型loader处理。device_loading_context借stage_module_for_post_load临时上设备做后处理，模型加载后NPU清allocator缓存的位置移至memory-saver region之外，不能在活region中随意照搬清缓存。

验收同时核对源权重键、融合分片顺序、target/draft量化dtype、scale来源、NZ/packed后处理和完整精度。缺CUDA capability错误不是成功信号；以实际NPU方案、算子版本和模型约束判断。在线更新后也需重做相应后处理。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
