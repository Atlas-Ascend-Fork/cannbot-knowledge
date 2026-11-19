---
type: API
title: torchair.ops FIA：GE Device 长度 Tensor 与版本差异
description: 区分 TorchAir 图专用长度 Tensor 入口和 torch_npu 接口，记录 v1/v2 参数名及文档签名冲突。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_npu_fused_infer_attention_score_v2.py
  role: header
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_npu_fused_infer_attention_score.py
  role: header
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_npu_fused_infer_attention_score.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_npu_fused_infer_attention_score_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-09T02:51:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# torchair.ops FIA：GE Device 长度 Tensor 与版本差异

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。本卡选取来源支持的 A2/A3 推理范围，其他产品和特殊参数另行核对。

## 两个入口

`torchair.ops.npu_fused_infer_attention_score` 的 actual_seq_lengths、actual_seq_lengths_kv、actual_shared_prefix_len 为 INT64 Device Tensor；v2 的参数名改为 actual_seq_qlen、actual_seq_kvlen，不支持 prefix。

它们服务 GE Tiling 下沉，减少长度参数 Host→Device 拷贝；与标准 torch_npu 同名接口的 Python int 数组契约不同。返回两项，布局、长度表示、分页和量化限制仍需匹配对应算子版本，本卡不重定义这些数值契约。

## 运行与声明边界

只用于 GE max-autotune，不支持 Eager 或旧 reduce-overhead；同提交实现的 CPU/PrivateUse1 直接抛 NotImplementedError，存在注册并不表示能在这些模式执行。

v2 文档示例错误地传 scale，Schema 使用 softmax_scale；文档签名 num_key_value_heads=1，实际 Schema/Meta 为 0（按 Query 头数补齐），另有文档遗漏的 quant_scale_p。调用应核对安装包 Schema、显式填写目标头数和 softmax_scale，不能将示例直接当作可运行代码。本文不提供混合量化或 GQA 的未确认配方。

## 检查

核对实际使用的是 torchair.ops 还是 torch_npu 命名空间、长度 Tensor dtype/设备、MHA/GQA 头数以及 Tiling 下沉配置。避免把来源中关键字抄错造成的失败归因于算子精度。

- [标准 FIA 数值接口](../torch_npu/npu_fused_infer_attention_score.md)
- [标准 FIA v2 数值接口](../torch_npu/npu_fused_infer_attention_score_v2.md)
- [Tiling 与静态下沉](../../guides/optimization/torchair/torchair_ge_dynamic_shapes_and_fa_tiling.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线对应接口与未闭合的数值组合

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 两份FIA Device长度页已对照，继续区分v1的actual_seq_lengths/actual_seq_lengths_kv/actual_shared_prefix_len与v2的actual_seq_qlen/actual_seq_kvlen；长度Tensor为INT64，v2不支持prefix。主线删除了发布页显式A2/A3产品段，但其他数值约束仍委托标准torch_npu同名API。本卡继续限定A2/A3的上述接口层知识，标准主线数值页的分项审阅和仍未确认的产品组合见后文，不把总览或产品标题替代包装入口的全部参数验收。

主线Schema仍是Tensor query/key/value，Converter内部才把key/value包装为单元素列表；不能因为标准torch_npu某些路径支持KV TensorList就把列表直接传给这个包装入口。v2示例错用scale、声明的KV头默认1、inner_precise缺默认值与实际Schema不一致的问题仍在：实际为softmax_scale、KV头默认0、inner_precise默认0，并有文档未列出的quant_scale_p。头数0会在Meta中按query头补齐；实际GQA仍需明确头数与底层约束。

v2的key_shared_prefix_dtype/value_shared_prefix_dtype提示不等于存在prefix输入，Converter明确将prefix数据置None。主线Meta在return_softmax_lse=False时返回[0]的FP32占位，不能直接沿用标准数值接口卡里的[1]说明；Meta形状也不独自证明真实运行返回。打开LSE时另行核对有效输出及布局。

主线代码中出现INT32打包INT4、FP4、HIFLOAT8或E8M0的转换分支，不表示任意产品/混合量化组合均已支持。这些数值模式、scale与物理布局应同时消费后文标准API专题中的限定及未确认项；本次未执行任何包装或数值测试。

## 标准主线数值审阅后的接线约束

对应OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的标准FIA两页已经全文审阅，并按[KV伪量化](../../guides/fia_kv_antiquant_modes.md)、[全量化](../../guides/fia_quantized_attention_paths.md)、[MLA布局](../../guides/fia_mla_and_packed_layouts.md)、[mask/LSE](../../guides/fia_mask_prefix_and_lse.md)分开保存。标准主线Meta/C++同样关闭LSE返回[0]FP32，说明与[1]的差异并非仅Device包装存在；发布卡的占位文字不回推主线。

这次全文审阅也暴露产品/类型表与示例、MLA TND全量化和GQA NZ tree mask的矛盾；明确保留为未确认组合。标准接口GQA FP8模式3/3/2的Meta只允许Eager，而本包装入口本身只服务GE，不能据转换分支拼出该包装的可用配方。包装主线950组合仍需独立支持与软件配套证据，本卡不因标准产品页出现950就自动扩大平台标签。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score_v2.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_npu_fused_infer_attention_score_v2.py)（header）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/__init__.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ops/_npu_fused_infer_attention_score.py)（header）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/npu_fused_infer_attention_score_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_npu_fused_infer_attention_score.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_npu_fused_infer_attention_score_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp)（implementation）
