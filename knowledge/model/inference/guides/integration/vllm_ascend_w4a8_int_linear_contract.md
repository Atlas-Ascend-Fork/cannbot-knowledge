---
type: Guide
title: vLLM Ascend W4A8 INT Linear：ModelSlim 打包、补偿与共享输入
description: 按3164新增W4A8_DYNAMIC Linear核对ModelSlim对称INT4、逐token INT8、16分区scale_bias、ND/NZ门禁和PreparedLinearInput clone；区分量化补偿与模型bias。
aliases:
- AscendW4A8DynamicLinearMethod
- ModelSlim symmetric INT4 Linear
- W4A8_DYNAMIC linear scale_bias
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/methods/w4a8/w4a8.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/methods/w4a8/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/methods/__init__.py
  role: implementation
created_at: '2026-11-03T06:28:46Z'
updated_at: '2026-11-03T06:28:46Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend W4A8 INT Linear：ModelSlim 打包、补偿与共享输入

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，完整 unified diff 与上下文已读；不把增量阅读标为目标整文件FULL，没有执行上游、NPU、真实collective或性能验证。

## 创建、分片与后处理

仅支持ModelSlim checkpoint与per-channel权重；group_size>0拒绝。checkpoint weight int8[N/2,K]每字节打包两个输出channel，output partition须8整除；FP32 scale/offset[N,1]。row parallel的scale_bias按16个K分区加载，TP必须整除16，分片轴1；其他Linear一列。不能将此新增Linear与MoE对TP>16的旧门禁当同一接口。

meta设备后处理直接跳过；实际weight_offset经CPU读取必须全零。weight转置后先unsqueeze到单组并contiguous，保留真实三维storage descriptor，再做可选NZ；K16整除且N64整除才转NZ，否则保留ND，例如N80的小TP shard。最后view int32；scale的FP32比特view int32再转int64供CANN低32位消费，不是把float数值直接转换为整数scale。scale_bias沿加载分区求和。

## 输入、输出与bias

二维输入可提前dynamic_quant成PreparedLinearInput。apply使用共享prepared输入时clone其INT8值，因为CANN A8W4会原位改写输入；省掉clone可能污染后续投影或同一图多次重放。普通输入先flatten量化，空输入返回同前导维与N的空输出。

执行使用单组 `npu_grouped_matmul`：group_list_type=1、group_type=0、split_item=2，per-channel bit scale与per-token scale分开；此选择避免quant_matmul fake对per-group的假设。GMM内部bias是激活shift补偿，真实模型bias必须在返回后另加，不能按pertoken_scale一起缩放。输出恢复输入前导shape和dtype。该apply本身不负责普通TP归约或全套weight-switch协议。

## Agent 验收

检查ModelSlim描述实际选中Linear registry、packed输出轴、TP16分区、offset全零、格式tag、scale低位比特与三维descriptor。覆盖N8/64/80、K16边界、empty、prepared多consumer、graph多轮及row/column parallel；分别比较补偿bias和模型bias。新scheme导入/shape正确仍需目标CANN/TorchNPU精度、内存与性能验证。
