---
type: Guide
title: Qwen3.5-MoE A3/950 当前部署
description: 当前Qwen3.5环境、batch32/4/1与950量化、原生GDN/Mamba状态、纯EP/TP及真实守卫，撤下旧fallback。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen3_5/qwen3_5_moe_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/config/mxfp8/qwen3_5_35b_mxfp8_tp4.yaml
  role: example
created_at: '2026-10-21T09:56:19Z'
updated_at: '2026-10-29T14:31:37Z'
platforms:
- a3
- '950'
---

# Qwen3.5-MoE A3/950 当前部署

## 当前环境与配置

文本侧适配，视觉不据此推导支持。README现要求A3 CANN9.1.0、950 CANN9.2.0-beta.1，PyTorch2.7.1/torch_npu2.7.1.post5（发布26.1.0-beta.1）、Python3.11。旧下载链接与环境分歧已修正文档，按当前组合准备。

| YAML | 并行 | 默认batch / 后端 |
| --- | --- | --- |
| qwen3_5_35b_ep8.yaml | world8，AttentionTP8、MoEEP8、sharedTP1 | 32 / eager |
| qwen3_5_122b_tp8.yaml | world8，Attention/MoETP8 | 4 / GE |
| qwen3_5_397b_tp16.yaml | world16，Attention/MoETP16 | 1 / GE |
| mxfp8/qwen3_5_35b_mxfp8_tp4.yaml | world4，Attention/MoETP4 | 4 / eager |

旧“所有batch必须1”注释不作为当前契约。MoE只支持纯EP或纯TP，混合明确拒绝；当前模型断言next_n=0。修改model_path、平台、输入长度和真实设备，从仓库根运行：

```bash
bash executor/scripts/infer.sh --model qwen3_5 --yaml qwen3_5_35b_ep8.yaml
```

## 950量化与通算融合

FP8使用对应权重config；在线MXFP8使用BF16/FP16，custom_params.enable_online_mxfp8_quantization=true并选择linear/gmm、忽略lm_head。当前MX YAML未显式platform_version，950部署应按README显式设为950或核验设备识别，不能保留错误A3默认。

量化仅950，A3 FP8/MXFP8会报错；MXFP8+GE也拒绝，使用合法eager或独立验证npugraph。转换会跳过已量化、忽略层和K维不满足32对齐的权重，检查实际计数和dtype/scale；开启不表示所有层成功转换。

enable_mm_all_reduce_base当前仅950；优化文档仍称A3适用，与源码守卫不符。它还受Prefill、TP、非量化/无bias等路径条件，且与Prefill token分片互斥。

## GDN与缓存

输入投影已分qkvz与ba，旧in_proj_fused和PyTorch solve_triangular回退不再存在。Full cache与GDN Mamba状态都由共享管理器分配；block_table[Mamba]选择conv/ssm槽。950融合causal conv，A3卷积适配；chunk/recurrent GDR输入的归一化、beta、g按代码准备，不能复制Next自研op签名。

Prefill token分片需EP==AttentionTP、MoETP1/sharedTP1等条件；实现AllGather恢复GDN输入后计算，再ReduceScatter，不能当作独立长序列CP。首次Prefill状态从零开始，检查多请求重排/回收后不串槽。PD的Mamba支持另按共享执行器限制核对。

## 验收与回退

A3按README开启HCCL_DETERMINISTIC=true核对归约确定性；评测另固定AIV与thinking设置，不能因输出正常忽略波动。用MMLU脚本时核对当前tokenizer模板是否已关闭thinking及few-shot/数据划分，保存逐题结果。

分别测BF16/目标量化、eager/图模式与batch，验Full/GDN状态、router、生成质量和内存。优化文档仍称npugraph暂未验证，代码已提供适配也不构成本仓硬件验证。本次未执行NPU；失败重载BF16和合法配置，不通过旧fallback开关处理。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/README.md)（primary）
- [modeling_qwen3_5_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py)（implementation）
- [qwen3_5_moe_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen3_5/qwen3_5_moe_optimization.md)（supporting）
- [qwen3_5_35b_mxfp8_tp4.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/config/mxfp8/qwen3_5_35b_mxfp8_tp4.yaml)（example）
