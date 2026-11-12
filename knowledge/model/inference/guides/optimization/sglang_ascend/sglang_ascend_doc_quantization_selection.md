---
type: Guide
title: SGLang 昇腾量化的格式选择、自动识别与验证边界
description: 按 A2/A3/950 区分 ModelSlim、MXFP8、MXFP4 与 GGUF，并保留在线离线路径及文档冲突。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/quantization.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/quantization.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/developer_guide/quantization_contribution_guide.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: implementation
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-09T04:35:29Z'
platforms:
- a2
- a3
- '950'
---

# SGLang 昇腾量化的格式选择、自动识别与验证边界

## 先核对格式与平台

离线checkpoint通过quant_model_description.json或config.json自动选择量化方法，来源建议无需再传quantization覆盖；普通模型教程中的显式ModelSlim开关不意味着每种在线格式也用同一配置。mixed-bits按层描述加载；文档还把MoE w13/w2独立选择标为进行中，不能据此声明已全支持。

| 方案/层 | A2/A3文档范围 | 950PR/DT文档范围 |
|---|---|---|
| ModelSlim Linear W4A4动态、W8A8静态/动态 | 支持，也列Diffusion | TBD |
| ModelSlim MoE W4A4/W4A8/W8A8动态 | 支持，非Diffusion | TBD |
| MXFP8 Linear/MoE，MXFP4 Linear | 不支持对应MX kernel | 支持，具体层/应用另核对 |
| MXFP4 W4A8 Linear/ModelSlim MoE | 不支持 | 支持，非Diffusion |
| MXFP4 W4A4 Linear | 不支持 | 总表WIP；正文称已设备E2E验证，存在冲突 |
| MXFP4 W4A4 ModelSlim MoE | 不支持 | 支持，非Diffusion |
| AWQ Linear W4A16/W8A16、MoE W4A16 | 支持 | TBD |
| GPTQ MoE W4A16/W8A16、Auto-round MoE W8A16 | 支持 | TBD |
| Compressed-tensors Linear动态W8A8、MoE动态W4A8（可带clip）/W8A8 | 支持 | TBD |
| GGUF标准与K-quant，Linear/MoE | 支持TP；加载时CPU反量化为FP16/BF16后传NPU | TBD |

GGUF的磁盘位宽不等于NPU常驻位宽；应按反量化后的运行内存规划容量。表中的TBD/WIP都不是已证实支持，也不能用页面其他格式的950支持补齐。

## 950 在线与离线的关键差异

MXFP8在线以quantization=mxfp8在加载时量化权重，推理时动态量化activation，block32；离线W8A8_MXFP8读e4m3权重和e8m0 block scale。离线transpose保留非连续view，擅自contiguous会改变block-scale对应或损害带宽。MoE gate也要按描述处理；把离线量化gate当无scale的BF16会破坏路由。

量化文档对所述 MoE MXFP8 路线称 none 通信把 activation 量化融合到 routing，DeepEP 仍传 BF16 并在 gmm1 前量化；这不能作为整个 DeepEP 后端没有 MXFP8 dispatch dtype 的结论。同提交 ModelSlim W4A8 MXFP4 MoE 实现另有 normal=bf16、low_latency=mxfp8 的专用配置。文档只明确其所述 none 路线在950端到端验证，不能据此宣称所有 DeepEP 模式也已验证。

W4A8（mxfp_w4a8）使用MXFP4 packed权重和MXFP8 activation，离线格式W4A8_MXFP；两者共享相应kernel布局，但权重来自RTN或校准。FP4算子参数必须用torch_npu.float4_e2m1fn_x2的int枚举，不能传torch同名dtype对象。

NPU的quantization=mxfp4选择dense W4A4，GPU同名选项语义不同。在线W4A4使用dual-level scale与NZ权重、dual-level量化/matmul；离线W4A4_MXFP4是single-level UE8M0、不同matmul路径。不能以同是FP4就互换scale/layout。来源解释旧single-level在线RTN曾出现greedy循环不出EOS，现用dual-level；正文验证声明与总表WIP冲突需明确核对实际版本。量化文档将 ModelSlim MoE W4A8/W4A4 概括为 BF16 通信、在 expert 输入处量化为对应 MXFP8/MXFP4；同提交 NPUW4A8MXFP4MoEMethod 实现与此存在模式差异：其默认 normal_dispatcher_output_dtype=bf16、low_latency_dispatcher_output_dtype=mxfp8，并在 w13 后处理时传入 dispatcher。应按格式、通信模式及实际扩展接口支持分别核对，不能将文档 BF16 概括覆盖 W4A8 的 LL 配置；W4A4 仍按其自身配置核对。实际 MXFP8 通信还依赖所安装扩展的接口与能力，见[离线 FP4 MoE](../../sglang_ascend/sglang_ascend_quant_offline_fp4_moe.md)。

## Diffusion 的格式准备

来源限定MXFP8为950，ModelSlim W8A8/W4A4为A2/A3。在线给quantization=mxfp8；离线先用msmodelslim导出（不要量化embedding），Wan2.2原始Wan格式还需wan_repack转换Diffusers，再复制原Diffusers中除transformer/transformer_2外的文件。只复制权重却缺配置、tokenizer或量化描述会破坏加载契约。

来源写MXFP8要求CANN≥8.0.RC3与950，这不是整套SGLang环境最低兼容组合；仍需按[安装版本组](../../deployment/sglang_ascend/sglang_ascend_doc_installation_version_sets.md)核对依赖。上文所有验证均归属于上游声明，本次没有转换、加载或运行模型；需要以目标checkpoint同负载核验质量、HBM和吞吐。


## 量化接入与文档选择

通用量化页同样区分950 MXFP8/MXFP4，但compressed-tensors明确标partial且FP8尚不支持，不能因为MXFP8专用路径存在就推导compressed-tensors FP8可用。通用ModelSlim清单把KV cache和attention量化列进行中/待完成，也不能从普通Linear/MoE格式支持借出这两项。离线转换须保留量化描述、config/tokenizer和校准条件；在线activation量化与离线校准权重是不同阶段。

开发新格式时，Config负责解析/选择、Scheme负责权重创建/加载/后处理及Linear/MoE等层接线、backend module负责NPU kernel/layout；不能把Linear scheme硬套MoE或Embedding。硬件import应限制在目标backend，避免未装NPU依赖的平台导入失败。验证至少覆盖格式解析与实际执行路径；数值变化需质量sanity，kernel/layout/dispatch变化需含warmup的基准，并记录checkpoint、量化/后端参数、硬件与命令。格式重构还需保持既有checkpoint和CLI兼容；这些是上游设计指南，非本次已完成的设备验证。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/optimization/quantization.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/quantization.mdx)（primary）
- [sglang：docs/docs/advanced_features/quantization.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/quantization.mdx)（supporting）
- [sglang：docs/docs/developer_guide/quantization_contribution_guide.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/developer_guide/quantization_contribution_guide.mdx)（supporting）
