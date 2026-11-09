---
type: Guide
title: vLLM Ascend 量化权重加载：ModelSlim、compressed-tensors 与原生 FP8
description: 从 checkpoint 描述、上游自动识别与 Ascend 重建 quant_config 判断格式和加载路径，保留 310P 独立后端以及文档与固定实现差异。
  保留孤儿 Qwen3 32B W4A4 和 Qwen3 8B W4A8 旧工具起点、权重和单 NPU 证据限制。
tags:
- task.implementation
- topic.precision
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/quantization.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/fp8_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/quantization.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/compressed_tensors_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-32B-W4A4.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-8B-W4A8.po
  role: supporting
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-10-30T14:16:33Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 量化权重加载：ModelSlim、compressed-tensors 与原生 FP8

## 适用范围

固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 下，先识别 checkpoint 格式，再核对目标平台的配置注册、量化算法和层支持。本卡覆盖格式判断流程，不声明三个格式在全部平台互通。既有 CANN Executor 的离线系数路径另见[权重部署指南](quant_weight_conversion_path_selection.md)，不能直接套到 vLLM 插件。

## 三种入口

ModelSlim 用独立 `quant_model_description.json`，部署可显式 `--quantization ascend`。compressed-tensors 和原生 fp8 通常在 config.json 的 quantization_config 中标记 quant_method，上游先识别。不要根据文件夹名、模型名或 BF16 启动模板推断存储格式。

来源用户指南要求 ModelSlim 显式指定 ascend；固定实现还提供自动识别：检测到描述文件且当前 quantization 为空时设置 ascend，并重新创建 VllmConfig.quant_config。只改字符串而不重建配置，会遗漏前面初始化阶段尚未创建的逐层量化对象。

已有显式值或上游已识别的值受到尊重；自动检测发现不同格式时告警，不覆盖原选择。远程配置读取失败只产生未检测到的结果，不足以证明权重是浮点。需核对模型 revision、下载/cache 和真实文件。

## 平台与格式不能互相替代

标准平台初始化导入 ModelSlim、compressed-tensors 与 FP8 等配置，310P 则走独立 ModelSlim 配置。不能由标准后端的注册清单推导 310P 原生 FP8 或 compressed-tensors 可用，也不能靠强制指定另一格式转换权重。

原生 FP8 仅有 block-wise、dynamic activation 路径；被忽略的层仍走浮点。950 的实际执行和非 950 的展开路径不同，详情见[原生 FP8 规则](../../optimizations/rules/vllm_ascend_native_fp8_execution.md)。新量化类型接入见[scheme 适配](../integration/vllm_ascend_modelslim_scheme_adaptation.md)。

## 验证与失败处置

记录工具与权重版本、量化描述、最终 quantization、quant_config 类、每类关键层的 scheme 和加载后参数。固定校准数据与目标精度标准，再比较显存与服务性能。配置与存储不符、缺少 scale、后端未注册、加载走到浮点 fallback 或精度失败时先定位来源和映射，回到已验证组合。

ModelSlim 和 LLM-Compressor 的来源示例是特定模型的量化方法，不是所有模型通用脚本；量化前还需足够 host RAM。本次没有运行工具或转换权重，不将示例结果作为已完成验证。


## 继续到逐层实现核对

compressed-tensors的组内format、target/ignore、纯权重量化和MX判据按[逐层分派指南](../integration/vllm_ascend_compressed_tensors_dispatch.md)核对，不能套用其他框架的同名配置判据。另有独立的[ModelOpt MXFP8入口](vllm_ascend_modelopt_mxfp8_loading.md)，mxfp8/modelopt_mxfp8不等于本卡原生fp8分支；该入口的平台范围仍待确认，不能从这里的流程平台枚举推导其硬件支持。


## 目标与草稿分别识别

投机模型不能只沿target格式判断。MRv2 DSpark在同checkpoint与独立草稿间有不同quant_config分支，见[草稿量化加载排障](../../runbooks/runtime/vllm_ascend_dspark_draft_quant_loading.md)；QuaRot的投影basis、词表TP切片及共享后副本另见[草稿权重对齐](../integration/vllm_ascend_draft_quarot_alignment.md)。格式识别、参数加载、basis对齐与实际算子支持仍分别验收。


## 中文量化指南、工具版本与路径差异

user_guide/feature_guide/quantization.po的36条有效非空译文已全文与固定英文对照，msgid全部精确匹配，0fuzzy/obsolete；这不证明线上zh-cn/latest页面与此提交的构建映射。ModelSlim、LLM-Compressor与原生FP8是三类来源入口，不能因中文工具说明相同而把它们的描述文件、scheme或安装方式互换。

固定指南以ModelSlim 26.0.0分支和Qwen3-MoE脚本作示例；工具分支名及外部master链接并没有冻结本次工具内容。量化前的host RAM、多卡可见性、校准/anti数据、原始与输出checkpoint分别留证；本次没有获取、安装或执行外部工具。指南要求ModelSlim指定--quantization ascend，而在线命令示例没有写该参数；应按本卡已核对的自动识别/显式值优先逻辑检查最终quant_config，不能把示例省略解释成所有环境都不需要。

指南仍引用旧文件vllm_ascend/quantization/compressed_tensors_config.py；同一固定提交中实际文件位于vllm_ascend/quantization/configs/compressed_tensors_config.py，头部声明AscendCompressedTensorsConfig。按[逐层分派指南](../integration/vllm_ascend_compressed_tensors_dispatch.md)定位实际配置，不把旧路径当成可直接打开的源码。本批只补充路径/头部身份，不以70行片段替代完整分派分析。

## 原生FP8中文声明的执行与内存边界

主指南及译文把quant_method=fp8加weight_block_size作为block-wise入口，量化权重为float8_e4m3fn并配逐块float32 scale。ignored_layers或modules_to_not_convert中的浮点层继续按其原格式处理；没有weight_block_size的per-tensor/per-channel原生FP8不能仅靠改名字进入同一后端。

来源描述950PR/950DT在加载时重组为MXFP8，其他代际展开到模型dtype并用高精度矩阵乘法。文档的“约两倍权重内存”用于容量预估，不是整个服务显存精确翻倍或实际allocator峰值；KV、临时工作区、padding与其他层另算。文档的数值等价也不能当作本环境已经完成逐bit、全模型或全部代际的精度证明。仍按[原生FP8实现](../../optimizations/rules/vllm_ascend_native_fp8_execution.md)和310P独立后端裁决有效路径，不新增格式跨平台保证。


## 两份孤儿 Qwen3 低比特教程

Qwen3-32B-W4A4.po与Qwen3-8B-W4A8.po共26条业务译文完整读取，均没有同名当前英文页；不按文件名重建脚本或当前支持表。前者旧文声称W4A4 Flat Quantization从v0.11.0rc1开始、modelslim从tag_MindStudio_8.2.RC1.B120_002开始；后者声称W4A8从v0.9.1rc2起支持。这些是历史支持起点，不证明当前每个工具/框架/硬件组合仍兼容，也不把不同位宽互换成同一scheme。

旧来源分别链接vllm-ascend/Qwen3-32B-W4A4与vllm-ascend/Qwen3-8B-W4A8的ModelScope产物，并允许自行转换。本次未获取这些外部权重、模型描述、工具tag内容或标定集，不能凭仓库名证明权重完整、量化质量或当前loader能加载；固定checkpoint revision、quant_model_description、scale/zero-point和逐层目标后，再沿本卡判断最终quant_config。

两份旧文都有“转换后文件结构”“单NPU在线/离线”和“启动后可查询”等阶段，但PO不包含完整代码、文件清单或数值结果。单NPU没有闭合SKU、内存和实际dtype；不扩展为全部A2/A3/310P/950都可运行，也不由位宽推得固定压缩比、速度或精度。它们要求量化方法ascend；当前固定实现的自动识别逻辑仍按本卡前文核对，旧教程的显式要求不能覆盖当前代码的有效配置优先级。
