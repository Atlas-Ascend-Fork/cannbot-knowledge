---
type: Guide
title: 推理组合量化矩阵乘：A8W4 Meta与参数消费边界
description: 区分npu_inference融合矩阵乘的A8W4提示检查、二维输出、Bitcast与未消费的分组/类型参数。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_fused_quant_matmul.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/auto_register_custom_torch_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T13:28:56Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 推理组合量化矩阵乘：A8W4 Meta与参数消费边界

## 独立命名空间与固定范围

本卡只绑定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`的`torch.ops.npu_inference.npu_fused_quant_matmul.default`，不是`torch.ops.npu.npu_quant_matmul`，也不是已有Matmul-Dequant或Gelu融合入口。Schema来自自定义包的`Library("npu_inference", "DEF")`，Meta与GE Converter分别注册；包`__init__`枚举模块后通配导入。这里只闭合显式启用该包后的定义与装饰器入口，未证明普通`import torchair`必然完成这些注册。

所审实现是图转换与Meta层，不能由它们存在推定Eager设备实现、发布组合或真实产品支持。整卡平台未知，保持draft、空平台；没有执行包导入、模型、GE编译或设备实验。

## A8W4检查只覆盖实际表达式

Meta通过动态导入`torch_npu`取得`getattr(..., "int4", None)`，判据为`x1.dtype == torch.int8`且`x2_dtype`等于该值，不满足就抛出只支持a8w4的RuntimeError。它检查的是`x2_dtype`提示，不是独立核验`x2.dtype`、实际打包内容或K关系。若运行包缺少int4属性，回退None还会影响这一相等判据；不能把错误文案当作完整输入认证。

Meta固定返回二维`[x1.size(0), x2.size(-1)*2]`，缺省INT8，显式output_dtype经GE/torch类型映射后分配。它没有推导任意batch广播或验证输入都是二维、K一致；`bias is not None`则直接拒绝。通过Meta不证明任意高秩输入或所有输出类型都可运行。

## 仅指定的参数进入GE节点

| Schema参数或转换条件 | 实际构图行为 |
| --- | --- |
| x2_dtype等于torch_npu.int4 | 对x2做`Bitcast(DT_INT4, keep_dim=True)`；不是数值量化或权重重排 |
| scale实际GE dtype为INT64 | Bitcast为UINT64；不创建浮点scale量化公式 |
| pertoken_scale / scale / offset | 分别传x1_scale / x2_scale / x2_offset |
| x3、y_scale、fused_op_type | 原样传对应输入/属性，没有本地完整shape或融合类型枚举检查 |
| group_sizes | 未读该参数；局部group_size始终0 |
| x1_dtype、pertoken_scale_dtype、scale_dtype、x3_dtype | 未据这些提示改写对应输入；不能替代真实Tensor编码/类型 |
| transpose_x1/transpose_x2 | 虽在Converter函数签名出现，却不在该Schema中；构图始终传False/False |

output_dtype=None先改为整数1，对应INT8；显式值经映射进入FusedQuantMatMul.dtype，并改写结果描述符的proto dtype。这是类型标记与图描述，不是补齐所有类型转换。固定生成IR声明的输出集合为FP16/INT8；通用映射函数能表示更多类型，不扩大本节点或kernel的合法组合。

Converter会把bias传GE，而同一路Meta明确拒绝非None bias；生成IR有optional bias也不能据此跳过Meta限制宣称高层调用支持bias。group_sizes写在Schema中同样不代表分组量化已启用；以实际节点group_size=0为准。

## 优化与迁移检查

先核对实际命名空间与Schema/Meta/Converter注册，再对齐权重打包、末轴两值承载、scale的位表示、输出dtype、x3及融合类型。对照FX Meta与GE节点输入/属性，尤其确认期望的group_sizes或dtype提示是否真的被消费；不得只因融合名或签名存在就认定消除了量化、格式搬运或后处理。

已有[GE矩阵乘及Matmul-Dequant](torchair_ge_matmul_lowering.md)和[量化View/NZ改图](torchair_ge_quant_matmul_graph_rewrites.md)覆盖其它路径；本入口没有在所审Converter中提供同一套NZ检测、转置消除或自动回退。数值、布局和端到端收益需要独立实验，本次未新增verified或性能数字。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_fused_quant_matmul.py)（primary）：定向范围15–74。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/auto_register_custom_torch_ops.py)（implementation）：定向范围1–7, 36–41, 221–262。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/__init__.py)（implementation）：定向范围1–7。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）：定向范围205–262, 341–401。
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）：定向范围88860–88906, 88996–89010。
