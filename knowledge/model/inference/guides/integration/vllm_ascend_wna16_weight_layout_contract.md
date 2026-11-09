---
type: Guide
title: vLLM Ascend WnA16适配：整数打包、MXFP4解码与高精度激活
description: 为新模型接入W4A16、W4A16_MXFP4或W8A16时，核对checkpoint位模式、原始与计算布局、group scale/offset、A16激活及GMM消费者，区分post-load转换、EPLB限制与重复加载边界。 WnA16的pack_to_int32区分int32输入调用int4pack与int8输入仅view字节；两个W4
  MoE类supports_eplb=False，MRv2 dynamic_eplb标记不能替代可迁移能力。
tags:
- task.implementation
- topic.precision
- topic.model_adaptation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/wna16/w4a16.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/wna16/w4a16_mxfp4.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/wna16/w8a16.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/wna16/__init__.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/wna16/test_w4a16.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/wna16/test_w4a16_mxfp4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/wna16/test_w8a16.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/base.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/compressed_tensors_config.py
  role: constraint
created_at: '2026-11-02T12:36:59Z'
platforms: []
aliases:
- W4A16
- W4A16_MXFP4
- W8A16
- AscendW4A16FusedMoEMethod
- AscendW4A16MXFP4FusedMoEMethod
- AscendW8A16LinearMethod
- unpack_from_int32
- pack_to_int32
- unpack_uint8_to_fp4_return_float32
- WnA16权重布局
- pack_to_int32：int32打包与int8字节view
- WnA16：supports_eplb=False能力边界
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T07:29:07Z'
---

# vLLM Ascend WnA16适配：整数打包、MXFP4解码与高精度激活

## 先按数值格式和层类型选择路径

本卡聚合Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的三个WnA16 scheme、family导入和三份专项UT。它们保留高精度激活，但权重编码与算子输入不同；新模型必须从checkpoint的实际dtype、位宽、scale粒度和层类型开始选择。

| 注册key与层类型 | 原始权重与运行合同 |
| --- | --- |
| `W4A16`, `moe` | LLM-Compressor INT4按组权重，int32打包；加载后解包、转置、重打包，使用独立scale与零offset |
| `W4A16_MXFP4`, `moe` | UINT8承载两个FP4 E2M1值；按码本解码、布局转换，再打包，scale为UINT8容器 |
| `W8A16`, `linear` | INT8线性权重，转置并按配置处理NZ；每输出通道scale/offset传给反量化matmul |

family `__init__.py` 导入这三个类；存在一个MoE注册不能推导出同名Linear实现。通用注册、模型prefix及加载阶段仍按[量化scheme接入](vllm_ascend_modelslim_scheme_adaptation.md)。所读实现与mock测试没有证明整项硬件范围，保持draft/空平台，不将scheme名称作为所有硬件、模型或通信组合的支持声明。

## 整数W4A16：先恢复数值，再改变布局

`AscendW4A16FusedMoEMethod` 明确针对LLM-Compressor生成的权重。checkpoint为每个专家分别保存gate/up/down的 `weight_packed`、`weight_scale` 和 `weight_shape`，gate/up加载后合成w13，down进入w2。不能把ModelSlim或浮点FP4的字节直接当作同一checkpoint格式。

`unpack_from_int32` 要求int32输入、正且不大于8并能整除32的num_bits，以及packed_dim为0或1；按低位优先移位、mask、沿打包轴恢复，按传入原shape裁剪padding，再减去 `2**num_bits/2` 并转int8。4bit时一个int32包含8个数，恢复值需要减8；原shape是实参，不能把存储容量等同有效元素数。

`pack_to_int32` 的两条输入路径应分别检查：int32三维输入要求末维能被8整除，flatten前两维后调用NPU int4pack，再恢复专家维；int8三维输入要求末维能被4整除，直接view成int32。后者是字节重解释，不能由函数名推导出它执行了同样的数值压缩或能替代int32分支。UT对部分形状和mock调用作断言，没有在本次执行。

以下以E为本地专家数、I为分片后intermediate size、H为hidden size、g为group size：

| 张量 | 分配/加载布局 | post-load后供计算的布局 |
| --- | --- | --- |
| w13 packed weight | `[E,2I,H/8]`, int32 | `[E,H,2I/8]`, int32 |
| w2 packed weight | `[E,H,I/8]`, int32 | `[E,I,H/8]`, int32 |
| w13 scale/offset | `[E,2I,H/g]` | `[E,H/g,2I]` |
| w2 scale/offset | `[E,H,I/g]` | `[E,I/g,H]` |

weight分配检查H/I的pack整除，动态参数分配检查group整除；offset由零张量构造，并非从checkpoint加载。scale/offset的实际dtype来自传入params_dtype，源码docstring中的BF16示例不能替代运行参数检查。post-load解包后转置、contiguous并转int32重打包，再转置scale/offset；仅检查原始checkpoint shape不能证明最终kernel读到了正确布局。

构造器从 `quant_description.group_size` 读取g，缺省32。所读compressed-tensors检测按INT类型、4bit、GROUP、静态权重且无input_quant选择W4A16；这不等于任意逐层group_size已自动传递给scheme。检测函数没有将symmetric作为该分支条件，而本实现offset固定为零，因此检测命中也不足以证明任意非对称checkpoint可用。新格式接入应核对实际构造配置与各层scale shape，不能仅凭量化工具配置里写过g就放行。

## W4A16_MXFP4：FP4码本与整数offset不能混用

`unpack_uint8_to_fp4_return_float32` 先取低半字节，再取高半字节，交错展开后查E2M1码本。正值集合为0、0.5、1、1.5、2、3、4、6，另一半为相应负值，包含负零；这里不执行整数W4A16的减8恢复。

其w13/w2分配分别是 `[E,2I,H/2]`、`[E,H,I/2]` 的UINT8，scale分别是 `[E,2I,H/g]`、`[E,H,I/g]` 的UINT8。post-load将FP4解成float32、转置，调用format29且customize dtype为BF16，再调用int4pack；scale也转置并contiguous。不能把中间float32、BF16格式转换参数或最终int32存储当作checkpoint的原始数值类型。

这条分配使用整除形状，局部代码不能替代所有维度、group、尾块和实际算子要求的完整校验。尤其不要从测试遍历若干group_size就推导出目标硬件kernel支持这些组合；测试中的NPU转换被mock，实际布局与数值仍需对照。

FP4权重搭配FP8激活的另一族见[MXFP4权重与恢复](vllm_ascend_mxfp4_weight_reload_contract.md)。该族的restore marker、Mega处理或FP8激活流程不自动属于本卡A16实现。

## 高精度激活与分阶段GMM

两个W4 MoE类均声明 `act_quant_type=None`、空 `fused_activations`；其 `apply_act_quant` 返回原hidden_states与None，基类 `_quant_hidden_states` 对W4A16/W4A16MXFP也直接保留输入。不要再插入动态INT8/MX激活量化，或把这个hook当作已执行SwiGLU等激活本身；激活仍需由实际stage调度链安排。

| 消费阶段 | 整数W4A16 | W4A16_MXFP4 |
| --- | --- | --- |
| GMM1 | weight/antiquant scale/offset，split_item=2，显式group_list_type，输出dtype取w2 scale | weight/antiquant scale，split_item=3，先用cumsum helper构造group_list，输出dtype取输入 |
| 激活量化hook | 不量化，返回None scale | 不量化，返回None scale |
| GMM2 | w2的scale/offset，同步核对group_list_type与输出dtype | 沿输入group_list_type传原group_list；FP16/BF16输入保持dtype，其余分支按源码回退 |

两类GMM1在计算后dispose原MLP输入，不能让另一并行消费者继续依赖该存储。group_list是累计边界还是counts、split_item与NPU算子实际默认值都应按真正消费者核对，不能因为两个scheme都叫W4就统一替换参数。`apply` 还通过forward context的MoE通信方法分发，实际路由、mask、expert map及通信实现仍分别验收。

## W8A16 Linear：scale、offset和bias一起交接

`AscendW8A16LinearMethod.get_weight` 分配 `[out,in]` 的INT8权重；per-channel参数为 `[out,1]`、使用params_dtype的scale和offset。post-load转置weight并调用 `maybe_trans_nz`，随后flatten scale/offset。运行时 `npu_weight_quant_batchmatmul` 接收真实weight、antiquant_scale、antiquant_offset及可选bias；不能只转置权重后漏掉后两项。

专项UT覆盖分配形状、参数dtype、调用和mock NZ转换后的shape；一个测试函数名包含int8，不构成该A16实现已验证任意激活dtype的证据。NZ能力与配置由外部helper决定，本卡不展开整个硬件策略。

## 重复转换、EPLB与Agent验收

两个W4 MoE类均显式 `supports_eplb=False`。构造时MRv2将dynamic_eplb设False，MRv1可读取配置标记；后者不能推翻类的能力声明或证明真实权重迁移可用。不要仅因为通用MoE路径传了expert map就让新模型启用EPLB。

本卡三个post-load hook都对张量做转置、打包或flatten，未在这些函数中观察到幂等/恢复marker。由此要求继续核对重复调用与实际reload调用方，不能直接宣称整个框架重载必然错误，也不能把另一个scheme的restore函数套过来。保存原checkpoint与阶段标记，在已处理权重上再次调用转换前核对真实入口。

Agent接入时优先保存四组证据：checkpoint key/原dtype/有效shape/scale粒度；load后与post-load后的shape、stride、dtype及存储身份；真实GMM/Linear参数、激活、bias与通信分支；浮点参考、目标TP/EP输出及重复加载后的比较。先确认格式与数值，再在固定batch、序列和并行条件下测显存、吞吐与延迟。

本次聚合源码与测试定义，未导入上游、运行UT、转换权重、执行NPU或测量精度/性能；没有新增verified事件。更一般的scale分片诊断见[TP scale边界](../../runbooks/precision/vllm_ascend_quant_scale_tp_sharding.md)，不要将本卡张量布局当作所有scheme的TP切分规则。
