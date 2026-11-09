---
type: Runbook
title: vLLM Ascend 量化scale分片：MX组相位、预分片与block尾部
description: 在TP后出现scale形状错误或静默精度偏差时，分别排查MX边界组、重复切片和把block scale误当bit packing的截断。
tags:
- task.debugging
- topic.precision
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/method_adapters.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/test_method_adapters.py
  role: evidence
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
updated_at: '2026-10-29T11:41:26Z'
---

# vLLM Ascend 量化scale分片：MX组相位、预分片与block尾部


## 触发与边界

单卡正常、增加TP后scale shape/copy失败，或shape能对齐但输出偏离。固定ceac1a2b的AscendLinearMethod存在专用MX loader和BlockQuantScaleParameter分支；本卡不把这些框架代码视为所有量化方案的硬件支持，平台待确认。本次没有复现NPU错误。

## MX：保留全局group相位

RowParallelLinear且scheme声明supports_unaligned_tp_groups时，adapter包装scale loader。若loaded_weight.shape已等于本地param.shape，直接copy，不能再次套全局TP offset。否则在local input size不能被group_size整除且param有input_dim时，以global_start=tp_rank×input_size_per_partition、scale_start=floor(global_start/group_size)切出param需要的scale_count，保留跨rank共享边界group。

源码断言示例为rank3、local input528、group32：global_start1584，scale起点49；本地scale宽17时取全局[49:66]，不能将66列平均切成四段。整除路径或其他参数仍交原loader，不能把这个例子推广为所有张量统一手工narrow。

实际MXFP8 Linear postprocess还按global_start%group_size补前缀、按组对齐补尾部，激活端使用相同padding。只修scale切片、漏掉weight/activation对齐仍可能错误。记录转换前后的shape、padding及scale组顺序，再核对实际算子输入。

## Block：不是bit packing

scheme返回_block_quant_scale时，adapter设置layer.weight_block_size并注册上游BlockQuantScaleParameter，供loader将尾部向上覆盖完整block。不能以普通packed_dim/packed_factor的整除截断替代，否则非整块shard丢失末scale。bit packing的物理pack和量化block是不同单位。

BlockQuantScaleParameter的weight_loader/input_dim/output_dim经构造器传入，该分支过滤这些只读属性，避免再用set_weight_attrs重复设置。其他per-group参数通过_input_dim或明确类型推导归约轴，不能只按参数名猜分片方向。

## 探针、修复与验收

保留checkpoint scale、loader收到的global/local形状、param类型/属性、rank、group/block size、postprocess前后布局。先判别预分片，再看组相位，最后检查block尾部和构造属性；禁止为消除报错随意丢最后一列或补任意scale值。

按同一权重比较TP1/目标TP与反量化参考，覆盖整除/非整除、预分片、packed输出尾部及rank边界。源码测试展示上述phase、预分片和block参数断言，本次未运行这些测试或精度实验。错误未闭合时回退已验证TP与权重布局，不宣称扩展支持。
