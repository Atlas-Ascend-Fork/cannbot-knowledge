---
type: Guide
title: vLLM Ascend 发布沿革：版本迁移与历史限制裁决
description: 发布沿革按42个版本边界识别新增、实验、撤销、弃用与已知问题，核对依赖和参数迁移，再进入当前模型、硬件与运行合同验收。 补充3164 main文档增量的模型配方、格式与开发目录迁移边界。
aliases:
- release_notes.md
- 发布沿革
- RC迁移
- COMPILE_CUSTOM_KERNELS
- enable_sparse_c8
- ASCEND_BUFFER_POOL
- release_notes.po
- 发布译文
tags:
- task.implementation
- task.design
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/release_notes.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/release_notes.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/GLM5.2.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/GLM5.3-Flash.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/Kimi-K2.6.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/Kimi-K3.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/DeepSeek-V4-Flash.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/DeepSeek-V4-Pro.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/DeepSeek-V4.1-Flash.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/Qwen3.5-397B-A17B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/Qwen3.8-Flash-Next.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/developer_guide/contribution/doc_writing.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/developer_guide/contribution/testing.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/testing.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.8-Flash-Next.po
  role: supporting
created_at: '2026-10-31T04:19:37Z'
updated_at: '2026-11-03T01:59:54Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 发布沿革：版本迁移与历史限制裁决

## 消费任务与来源边界

为适配或性能Agent判断“这个版本是否真的包含某能力、旧参数该如何迁移、Fix后是否仍有已知限制”。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的release_notes.md全2617行、42个版本章节，以下是英文发布声明的中文蒸馏。外链PR/Issue、tag源码、测试报告、镜像和当前线上HTML没有在本卡逐项验证，不把链接、发布文字或Fixed直接当运行证明。

这是跨历史分支的资料，没有覆盖整张卡所有硬件/模型组合的实测，保留draft/platforms=[]、无verified。本卡负责变化与限制的版本边界；整套依赖选择、main配对、镜像和安装步骤见[版本环境](../deployment/vllm_ascend_versioned_environment.md)，当前两两组合见[功能裁决](../integration/vllm_ascend_feature_combination_resolution.md)。历史声明不覆盖当前专用指南/实现，也不能反过来用main消除旧版缺陷。

## 发布沿革的读取方法

一个条目至少绑定Ascend版本/分支、Native实际身份、hardware、模型/checkpoint、量化/缓存布局、Runner、图、并行及P/D角色。以下是Agent使用本卡的建议证据字段，不声称原文模板强制这些字段。新增支持、Experimental、推荐、待弃用、已移除、暂时回退、已知问题分别保存；“下版会修”不是已修，“支持”不能越过同节Known Issues。

源文按自己的章节序排列。v0.9.1正式版日期晚于v0.10.0rc1与v0.9.2rc1，v0.13正式版又晚于v0.14rc1；不能按数字或发布时间构造全功能包含关系。v0.23正式版汇总自v0.18的多个RC周期，†是RC后合入；v0.11正式版只列自rc3的重要变化，v0.14要求从v0.13rc1升级时同时读v0.13rc2。重复PR/描述不是独立实现或独立测量。

下表日期是release_notes正文原值，不是已核验的真实发布时间。它与环境卡所载versioning_policy日历有差异：v0.16rc1为03.09/03.10、v0.8.4rc2为04.29/04.28、v0.7.3rc2为03.29/03.28；政策还有本文未列的v0.13rc3。保留来源差异，不补造统一日期或遗漏版本的已知问题。

## 发布沿革逐版本路由

| Ascend版本 | 正文日期 | 能力变化与必须保留的限制 |
| --- | --- | --- |
| v0.30.0rc1 | 2026.10.11 | 四旗舰模型与MRV2/CP/KV Pool/投机栈；MRV2默认全开、MRV1 dirty block-table和prefix retention传播均有撤销，不能只读Features。 |
| v0.23.0.post1 | 2026.09.21 | v0.23分支tag后修复DP dummy slot、310P MTP overlay与RL图中量化buffer；memfabric_hybrid/memcache_hybrid固定1.2.0。 |
| v0.26.0rc1 | 2026.09.03 | 完整验证声明限定Kimi K3、GLM-5.2、DSV4 Flash0731/Pro0813；其他模型可有条目，仍不在该保证内。移除一批优化与MRV1 PCP。 |
| v0.23.0 | 2026.08.16 | 累计自v0.18正式版变化，†表示RC后合入；GLM-5.2 1M仅A3验证，PP+PCP、950 SFA CP及reduce sampling等有专门限制。 |
| v0.23.0rc1 | 2026.07.20 | SFA DCP/C8、KV offload和950量化；Step3P5/P7与Gemma4有Experimental标记。不能用final依赖覆盖本RC。 |
| v0.22.1rc1 | 2026.06.30 | DSV4/hybrid Mooncake、HCCL RL与950动态量化；P-Eagle/PARD为上游稳定声明，SSD多DP仍实验，池化和PD精度有已知问题。 |
| v0.21.0rc1 | 2026.06.16 | 950 DSV4、hybrid/Mamba align APC与FULL_AND_PIECEWISE；图数量声明依HDK/CANN流预算修复，DSA-CP与FC1分别启用。 |
| v0.20.2rc1 | 2026.06.03 | DSV4 DSA/缓存/PD/MTP及950 MXFP；FA3依公开包可用，clamp默认改变，reduce sampling实验、KV Pool仍有问题。 |
| v0.18.0 | 2026.04.30 | 多模型及RL/PP async带实验限定；npugraph_ex和ARM CPU绑定默认，310P/部分功能需CANN9及同步配套包，非通用默认栈。 |
| v0.19.1rc1 | 2026.04.30 | MRV2初始MoE/Eagle、DFlash FULL_DECODE_ONLY、zero-bubble、Bailing与310P；Transformers升级5.5.3/lm-eval0.4.11，仍有GLM5非PD已知问题。 |
| v0.18.0rc1 | 2026.04.01 | target/draft独立Attention、VL MoE SP与GQA C8；FIA大TP head-dim、R1计数错误及MiniMax2.5 PD GPQA回退保留。 |
| v0.17.0rc1 | 2026.03.15 | 950、MRV2 ACLGraph、并行投机及远程ID量化自动识别；GLM5需Transformers5.2，QwenNext权重切分、hybrid缓存阈值仍限制。 |
| v0.16.0rc1 | 2026.03.09 | QwenOmni/GLM5量化、FabricMem实验、EPLB可观测与310P W8A8SC；量化自动识别撤销，仍需--quantization ascend。 |
| v0.15.0rc1 | 2026.02.27 | npugraph_ex默认、310P MoE/W8A8实验、KimiK2.5与自动量化；Kimi需额外Native PR修复，清理ProfileExecuteDuration/rotary/旧环境变量。 |
| v0.13.0 | 2026.02.06 | 正式版许多模型/CP/full graph仍Experimental；去Torchair/AscendScheduler、改dump_config类型，旧量化权重与大EP/长上下文有已知限制。 |
| v0.14.0rc1 | 2026.01.26 | 包含v0.13rc2再列差异；310P仅基础dense/VL eager，EPLB参数集中、profiler迁--profiler-config，MLAPO decode默认且增加内存。 |
| v0.13.0rc2 | 2026.01.24 | CP/MTP/Eagle/EPLB稳定性改进和MRV2基础支持；TorchNPU2.8.0.post1、部分弃用为未来移除，不能当final的post2。 |
| v0.13.0rc1 | 2025.12.27 | CP实验、QwenNext MTP+chunked、跨机器PD/UCM/W8A16；旧配置迁移，QwenNext长输入及超短DSV3.2输出仍有问题。 |
| v0.11.0 | 2025.12.16 | 正式版只列自rc3重要差异；TorchNPU2.7.1.post1/CANN8.3rc2，Torchair/LLMdatadist/Scheduler宣布弃用，QwenNext EP/MTP不支持。 |
| v0.12.0rc1 | 2025.12.13 | 新增自定义算子为运行前提、移除COMPILE_CUSTOM_KERNELS开关及旧modeling入口；Torchair/LLMdatadist/Scheduler移除，suffix有支持与已知失效两条声明。 |
| v0.11.0rc3 | 2025.12.03 | NZ loader临时关闭、Mooncake入镜像及OOM/DP VL/MTP长服务修复；只按本RC看变更，不能据Fix推所有配置通过。 |
| v0.11.0rc2 | 2025.11.21 | CANN8.3RC2、Ngram回归、启动与图档位优化；Ray+EP、response_format、多实例CPU绑定及Mooncake IPv6仍有条件。 |
| v0.11.0rc1 | 2025.11.10 | APC/chunked默认、W4A4、MTP>1与实验FULL_DECODE_ONLY；TorchNPU2.7.1、旧图/connector弃用计划，长期服务/精度仍有问题。 |
| v0.11.0rc0 | 2025.09.30 | 特殊RC：DSV3.2、Qwen3-VL、aclgraph/EPLB/CPU offload；LoRA/Eagle3回归不等于以后所有RC/final无已知问题。 |
| v0.10.2rc1 | 2025.09.16 | QwenNext初始支持但无EP/MTP、HBM偏高；Ray aclgraph及量化；LoRA坏、P/D异TP需未含的Native修复，AscendScheduler APC+chunked受限。 |
| v0.10.1rc1 | 2025.09.04 | Mooncake register/pull、MLP TP与lmhead TP、openEuler24.03；多项环境变量/参数更名，MLP TP有内存代价，SWA/chunked限制。 |
| v0.9.1 | 2025.09.03 | 正式版汇总自0.7.3，要求V1、旧MindIE Turbo不兼容；MoE aclgraph仅TP、V1 PP不支持，PD稳定性问题仍在。 |
| v0.9.1rc3 | 2025.08.22 | V1 scheduler MTP、LMhead组与mask/metadata修复；A2 910B1 full_cuda_graph测试失败保留为特定报告。 |
| v0.10.0rc1 | 2025.08.07 | 另一发布线：移除V0，V1 PP、A3镜像、KimiK2/QwenCoder/GLM4.5；aclgraph DP+EP流不足、W8A8多流精度及SP组合仍限制。 |
| v0.9.1rc2 | 2025.08.04 | W4A8、动态EPLB、V1 PD与多类修复；Torchair TP<=4和Atlas300I不进final的限定，不能借其他RC覆盖。 |
| v0.9.2rc1 | 2025.07.11 | V1默认且最后支持V0的该发布线；300I W8A8与Qwen3-MoE图为已测子集，PP+Ray+graph仍有问题。 |
| v0.9.1rc1 | 2025.06.22 | 300I系列和Eagle3为实验且明确不进v0.9.1 final；MLA chunked、MC2与静态EPLB修复，GatherV3/APC scheduler仍有限制。 |
| v0.9.0rc2 | 2025.06.10 | 修复非editable安装import错误；这是源文建议替代rc1的补丁，不能推广为所有当前安装故障的修复。 |
| v0.9.0rc1 | 2025.06.09 | V0冻结、V1 opt-in；Qwen图仅相应系列充分测试、其他失败回eager；多机DP Native修复未包含。 |
| v0.7.3.post1 | 2025.05.29 | Qwen3/Qwen3MoE与在线权重、VL RLHF改进；V1 MLA chunked仍实验，modelscope<1.23，MindIE Turbo建议属当时版本。 |
| v0.7.3 | 2025.05.08 | 首个正式版为上游验证声明；CANN8.1RC1/TorchNPU2.5.1、MindIE Turbo集成、LoRA/动态服务及SOC_VERSION，不是本卡真机verified。 |
| v0.8.5rc1 | 2025.05.06 | Native0.8.5.post1、CANN8.1RC1与V1 APC/chunked；早期llm_datadist PD及R1 W8A8 32k，不能混成0.7.3部署配方。 |
| v0.8.4rc2 | 2025.04.29 | Qwen3/W8A8和DeepSeek DP/TP/MTP仍实验；V1 ACLGraph依CANN8.1、默认未开，openEuler与VLLM_VERSION选路另核。 |
| v0.8.4rc1 | 2025.04.18 | V1实验默认可回V0，睡眠/投机当时仅V0；PD仅1P1D，structured output仅xgrammar；custom ops默认开启。 |
| v0.7.3rc2 | 2025.03.29 | AscendC custom-ops框架，编译默认关闭，V1基础、APC与dev TorchNPU精度修复，不能继承后续默认值。 |
| v0.7.3rc1 | 2025.03.14 | DeepSeek MTP、早期pooling、MiniCPM与dev TorchNPU；长输入/输出精度及乱码报告，临时温度建议不替代根因验证。 |
| v0.7.1rc1 | 2025.02.19 | 初始硬件插件/DeepSeek/Qwen/Llama，Ascend量化当时仅配置入口；依未发布TorchNPU，特定平台/import日志被称无害，不能推广忽略当前错误。 |

## 发布沿革：v0.30模型范围与撤销

v0.30.0rc1的原始标题和正文仍称rc1，英文入口却链接en/v0.30.0rc2；不能据链接自动把本节改为rc2。它宣称配Native0.30，经main2main对齐，区别于本知识任务冻结的Native0.32，也区别于main已验证SHA。下列仅是本节明确的发布范围，不将型号列和精度列作笛卡尔展开。

| 旗舰模型 | 本节硬件与范围 | 不能外推 |
| --- | --- | --- |
| DeepSeek V4.1 | Atlas800I A2/A3，W8A8、MRV2、TurboQuant INT4 latent KV、torch.compile与PD | 不能从“V4”推任意checkpoint、任意Runner或全部CP组合。 |
| GLM-5.3 | A2/A3，A3注明128GB×8；W8A8C8多机、sparse SFA packed C8与DSpark | 不能把GLM5.2 indexer修复或单项算子登记变成所有GLM版本等效支持。 |
| GLM-5.3-Flash | A2/A3，A3注明128GB×8；W8A8、PD与KV Pool | layerwise/non-layerwise、DRAM/SSD、Mamba和connector仍按对应实现。 |
| Qwen3.8-27B | A2/A3及Atlas300I DUO，310P列明确W8A8-310P；hybrid non-contiguous KV，范围文字含BF16/W8A8 | 不能由一行文字推310P所有精度/量化/图/并行均验证。 |

其他模型/硬件组合在该节范围之外。Highlights中又有GLM-5.2/Qwen3.5、GDN、DSV4与量化修复条目，它们不是扩充上述完整验证范围的独立表。

MRV2默认覆盖所有配置的改动已撤销，仍按配置opt-in；MRV1 dirty block-table和prefix retention config传播也有撤销。Features中async CPP、新CP执行、batch-sharded sampling等不等于默认生效，更不保证通过任意多项组合。Known Issues仍指向DSV4.1+DSA-CP和GLM-5.3 PD精度调查，未在本卡核其实时状态。

本节优化涉及移除每步复制/同步、缓存RoPE和KV计划、GDN/SiTU/KDA/SFA算子融合、PCP/DCP通信、KV Pool miss/RPC、路由GEMM、PP/AscendStore同步和CPU tokenization。它们分别是目标路径优化声明，非一个通用开关或端到端提升百分比。修复涉及dummy slot、packed C8尺度、hybrid/Mamba页表、DSpark词表映射、权重reload、PD receive/重算、HCCL生命周期与EC设备；继续进入相应任务合同定位真实执行路径。

## 发布沿革：依赖和配置不可跨版本拼接

完整常规配对表在环境卡，本卡保留发布正文额外条件：v0.30写CANN9.2、HDK26.0.RC1、PyTorch2.10/torch_npu2.10.post4、Triton3.2.2、Mooncake0.3.11.post1、FLA NPU v26.9.1-beta2、ray>=2.47.1且<=2.48.0，镜像基于Python3.12；镜像Python值不自动替代包支持范围。

v0.23 RC到final的CANN9.0.1→9.1、torch_npu post2→post4、Triton3.2.1→3.2.2必须整套处理。v0.26明确Triton3.2.2用于A2/A3/950，300I DUO不支持；310P专用CANN也不能由通用行补全。v0.18的CANN8.5.1通则另给FabricMem/310P/QwenOmni/x86的9.0例外，并要求对应TorchNPU post2/Triton3.2.1；其Mooncake原串3.9.0与环境表v0.3.9分别保留，不擅自纠正。

v0.19.1将Transformers4.57.4升5.5.3并配lm-eval0.4.11；v0.17 GLM5又有5.2.0特定要求。v0.12去Python3.9，v0.8.5实际Native为0.8.5.post1；同号、省略post或单改VLLM_VERSION都不构成兼容验证。旧文手动wheel、Native cherry-pick、清缓存、卸载旧入口只提供历史背景，本卡没有执行，不作为默认修复所有新环境的步骤。

| 变化 | 精确的版本边界与迁移动作 |
| --- | --- |
| V0/V1与MindIE Turbo | v0.8.4 V1实验可回V0、sleep/spec当时V0；v0.9 opt-in/冻结V0，v0.9.2线V1默认但最后支持V0，v0.9.1 final明确不支持V0，v0.10完全移除。0.7.3推荐/集成MindIE Turbo与0.9.1旧版不兼容说明不混用。 |
| custom ops开关 | v0.7.3rc2编译默认off，v0.8.4默认on；v0.12将custom ops变运行前提并移除COMPILE_CUSTOM_KERNELS，旧0值绕过编译不沿用。 |
| legacy图/调度/connector | v0.11弃用Torchair/AscendScheduler/LLMdatadist，v0.12移除；v0.13又列清理/替代。旧入口或env存在不能当当前支持。 |
| 量化自动识别 | v0.15加入，v0.16因远程ID问题撤销而需--quantization ascend，v0.17恢复远程ID路径；不能合并为单调能力。 |
| FX/运行时图默认 | v0.15/0.18 npugraph_ex默认声明、v0.23 FULL_AND_PIECEWISE默认、310P降级与v0.30 MRV2 opt-in是不同维度。HDK25.5.1/CANN8.5流预算修复的约32k/64k图数量不是HBM容量或所有配置捕获保证。 |
| 配置名字 | v0.13 dump_config字典改dump_config_path字符串；旧dense_optimize等删除，prefetch为当时替代；v0.16 enable_flash_comm_v1改enable_sp，v0.20/0.23又迁enable_flashcomm1并要求DSA-CP显式独立开关。按目标schema确认，不按字符串近似替换。 |
| profiling/EPLB | v0.13弃用ProfileExecuteDuration转ObservabilityConfig，v0.14旧profiler env转--profiler-config，EPLB旧参数移到eplb_config；存在类/日志不说明当前采集或EPLB已开启。 |
| 待弃用与已移除 | v0.23列layer sharding/FlashComm2/weight prefetch等待弃用，v0.26列多项已移除、MRV1 PCP移除；DeepSeek旧模型计划v0.28移除还需目标源码证明。ASCEND_BUFFER_POOL在0.23称removed、0.26称deprecated，保留措辞差异。 |
| v0.30算子和KV字段 | bundled KDA迁外部fla_npu、冲突算子加_vllm、MLA迁ACLNN两阶段；移除store_kv_block/c8_enable_reshape_optim、量化KV统一--kv-quant-dtype。目标算子包与加载路径需实际核对。 |

## 发布沿革：已知问题仍参与适配裁决

| 版本与组合 | 原文范围和后续取证 |
| --- | --- |
| v0.26模型受限版 | 四指定模型以外不保证；KimiK3长输入DSpark接受率、DSV4-Flash128K/1K pool single-prefix、Qwen/A3 PD与950 CPU绑定回退分别留负载。MiniMaxM2.7双机阈值失败还需更多样本，未直接定为持续回归。 |
| v0.23 CP与量化 | PP+PCP不支持；GLM5.2 1M只有A3验证；SFA PD两端DCP必须对称，950 SFA无CP、MLA/GQA CP实验；DCP+SFA C8及量化精度/性能问题各有条件。不能覆盖main V2 connector的新能力。 |
| reduce sampling | v0.20引入实验、v0.23默认off，与PD/lmhead TP不兼容时自动关闭；请求logprobs时分区logits可能导致数值/top-k不对。后续batch-sharded sampling不是同一开关。 |
| v0.21 DSV4 KV Pool | 需--no-disable-hybrid-kv-cache-manager以免启动OOM，原文1M约300GB说明所有压缩率族状态存储；不能当任意checkpoint/当前KV方案的容量公式。 |
| GLM5/5.1与MTP/FlashComm | v0.20/v0.21 CANN9 MC2数值、FULL+EP图、PD长服务AICore timeout、MTP3接受率等分别核模型、软件栈和拓扑，不统称“GLM不支持”。 |
| v0.18前后实验组合 | MiniMax2.5 PD的13% GPQA回退、R1高并发counter、FIA TP>=16 head-dim、soft partition+PIECEWISE、Qwen PD精度和fused MC2多DP padding均版本受限。 |
| 旧图与服务 | v0.9.1 TP-only MoE图/no V1 PP，v0.10图DP+EP流不足，v0.10.2 LoRA坏/异TP PD待Native修复，v0.11 CPU绑多实例等不能当当前全局禁令。 |
| 文内声明冲突 | v0.12既称suffix支持又在Known Issues说不工作；v0.13 EPLB展开写Elastic Prefill Load Balancing，不能据此混同Expert Parallel Load Balance与DPLB。保留原始出处，核实际实现。 |

性能段中的5× split_qkv kernel、2.7×卷积、0.95% TTFT/0.59%吞吐、约10% penalty、1–2秒TPOT尖峰、1–2ms小batch变化、15%吞吐差与GPQA百分比各有版本/模型/负载/基线。算子收益不等于端到端收益，精度百分点不等于吞吐比例，SWE容器/超时/下载/Agent随机性也不自动归为NPU kernel数值错。

## 发布沿革的交付与回退

先建立目标版本对和已验证组合，分别记录source/tag、实际安装包、配置、模型权重、设备与工作负载；用变化表找需要迁移的字段与已知限制，再进入[新模型接入](../bringup/vllm_ascend_new_model_onboarding.md)、[测试证据选择](../bringup/vllm_ascend_test_evidence_selection.md)、[图优化](../optimization/vllm_ascend_graph_mode_selection.md)和[性能基准](../optimization/vllm_ascend_benchmark_workflow.md)。MooncakeConnectorV2命名不等于Native ABI或Runner V2，按[门面合同](../integration/vllm_ascend_mooncake_v2_facade_contract.md)核对。

每次只增加明确的功能组合，保存正确性、真实case/skip、图/通信有效配置和可比NPU基线。失败回到最近验证的版本/配置，保留原始失败与尝试身份；不能修改版本字符串、删assert、吞异常或用tag名称掩盖不匹配。本文的迁移建议不是已经执行的升级、回滚或性能证明。

## 发布译文：固定中文来源与裁决方法

固定同一提交的release_notes.po全部389条已逐条读取，与完整2617行英文发布正文对照；383条原msgid能精确定位，另6条保留旧串并核对当前对应。条目编号只指本次固定PO的读取顺序，不是稳定API或网页锚点。原始msgid/msgstr、版本上下文和链接身份用于回查；全文阅读、源串匹配、字段校验仍不能证明中文语义无误或实际站点覆盖。

发布译文不能覆盖模型、硬件和执行条件。先比较英文与中文的限定词、版本、否定/实验/撤销、数量/单位和标识符，再进入前面的迁移表；英文自身有歧义或错误时，两份原文一同保留，转目标版本schema/实现取证，不自动把英文当运行真值。

### 发布译文中需要保留的差异

| PO条目/版本上下文 | 原串或译法风险 | Agent消费边界 |
| --- | --- | --- |
| 58：v0.22.1rc1 | cache-scale译为“缓存规模”，DP ranks译为“等级” | C8量化scale不是KV缓存容量；rank保留分布式逻辑身份，不能据译词改变内存配额或拓扑层级。 |
| 71：v0.20.2rc1 | PCP/DCP适配行的中文遗漏DeepSeek-V3.1与Ascend950 | 按英文保留模型3.1及950范围；不能扩大为全部DeepSeek、硬件或所有CP组合。 |
| 79：v0.18 | host-bound译为“主机绑定” | 这里指主机侧瓶颈，区别于CPU affinity；同版本CPU绑定默认也仅ARM，不据此宣称x86默认。 |
| 92、96 | worker warmup译“工作线程”；C locale译“C语言环境” | 保留worker角色，不凭译文确定Python线程/进程；C locale用于子进程输出解析，不要求C编程工具链。 |
| 95、103、115 | moe_load“加载精度”、GPQA“性能下降”、TTFT“提升” | 不据标签归因为权重加载；GPQA任务指标不是吞吐，百分比/百分点需原指标；TTFT改善不是延迟数值变大，旧负载数值不当通用收益。 |
| 131：v0.13 | 英文把EPLB展开为Elastic Prefill Load Balancing，中文继承“弹性预填充” | 这是源文本身的术语问题，不能据此混同Expert Parallel Load Balance、DPLB和prefill调度。 |
| 150、245、266 | ModelRunnerV2“下一代vLLM”、DBO“新型DeepSeek模型”、pyhccl“替代torch.distribute” | Runner代际不是产品版本/Native ABI；DBO是执行重叠方法，不能当新checkpoint；不推所有collective均被替换。 |
| 171：v0.12 | pick this commit却指向Ascend Issue #5010 | 保留Issue/PR/SHA对象类型，不执行以Issue编号作SHA的cherry-pick；suffix支持与Known Issues仍同时保留。 |
| 196 | 同段enable_shared_pert_dp与enable_shared_expert_dp不一致 | 保留拼写差异，按目标schema/实现核对，不能发明或直接执行新配置。 |
| 211：v0.10 | 中文W8A8修饰范围可能扩到Kimi K2、Qwen Coder、GLM4.5全部 | 英文明确Kimi K2带量化、并列其他模型；不能据此断言三者W8A8均测试。 |
| 232、281–298 | 通用/前缀标题可能命中多个英文位置 | exact substring和上下文列表不是整段最终替换或HTML位置证明。 |
| 324、334 | word_size疑似源拼写；MoE dispatch译“调度” | 未核实现前不改成world_size/新API；token路由kernel区别于请求scheduler策略。 |
| 344、354、356 | reasoning-effort直译；DSpark acceptance；SparseFlashAttention译“稀疏闪存注意力” | 保留checkpoint/API标识；acceptance是草稿token接受率；Flash指注意力计算，不是SSD/闪存存储，C8也不改变这一点。 |
| 373–388：v0.30 | backport译作“回合”；功能条目与后面的撤销并列 | backport指回移至相应版本线，并非对话轮次；MRV2默认、async CPP及其他撤销要一起裁决，四模型硬件表不得做笛卡尔展开。 |

### 发布译文中六条旧原串

29、165、189、322的旧英文分别位于v0.9.1、v0.11正式版、v0.10.2rc1、v0.11rc1，均为expert parallel改成expert parallelism的原串差异；360位于v0.21rc1，有两处Expert Parallel改为Expert Parallelism。保留旧PO与当前英文对照，不能据五处术语修订宣称模型组合或精度限制已经变化。

372的v0.30引言中，PO旧msgid/msgstr仍指en/v0.30.0rc1，当前英文指en/v0.30.0rc2；节标题仍是v0.30.0rc1。不能自动改节版本，也不能把两个链接当同一网页构建。虽然本PO无空译且383条精确匹配，中文仍有遗漏和术语风险；这两个统计不能换算为译文质量或最终HTML覆盖率。

### 发布译文的后续取证

发布译文给Agent提供中文入口和差异边界；用于适配前，回到相应版本实现与专用运行合同。若网页仍有英文回退、旧链接或未替换段落，沿[文档构建与中文转换](../../runbooks/validations/vllm_ascend_document_rendering_evidence.md)核对generate_zh_docs、当前msgid、最长非重叠替换、生成Markdown和HTML；本卡没有运行翻译器、MkDocs或获取整站HTML。1661个规范PR/Issue链接身份只作读取追溯，没有抓取这些对象内容。

本卡已生产完整英文发布知识及这份固定中文PO的逐条裁决，保留draft/空平台、无verified。没有安装、上游测试、CI、服务、NPU或Agent A/B执行；211份PO的台账处理完成也不代表Main源码、全部硬件模型、翻译器输出或整站知识生产完成。


## 2026-11-03 main 文档增量：模型配方与开发路径

以下固定从ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2到3164adc8fe75892fbf7f99f524bb72fddf1e6efd的main文档变化，不是新release版本，也不把移动分支名当可复现身份。这里只摄取各页新增/修改行和已读上下文，未重读数万行完整新教程；删除旧配方不自动证明旧版本功能失败，新增示例也不提供本仓设备结果。旧release沿革与旧ceac知识保留各自版本边界。

| 新版本材料 | Agent生成适配/优化方案前需要改变的裁决 |
| --- | --- |
| [GLM-5.2](../models/vllm_ascend_glm52_glm53_cache_formats.md) | 镜像按A2/A3/950DT选择无后缀/-a3/-a5并保持各节点一致。单节点TP16/DP1示例为DSA CP与FlashComm1显式加EP；多节点API node0省略data-parallel-start-rank以保留内部DP负载均衡，headless node1才显式4。单节点和多节点推荐表不是同一组容量。 |
| [GLM-5.3-Flash](../models/vllm_ascend_glm53_flash_hybrid.md) | 新A3 KPool indexer_kv_dtype=int8独立于main KV dtype，auto/bf16保留旧BF16路径；调用pool_key_indexer，per-vector FP16 scale随key共页传输，需支持INT8及零completed-pool的ops-transformer接口，文档指定2026-10-31 A3/CANN9.3.0构建。教程仍明示MRv1，不用另一实验RecoverSSM页的MRv2声明无条件覆盖此checkpoint/路径。 |
| [Kimi-K2.6](../models/vllm_ascend_kimi_k26_multimodal_draft.md) | first-support v0.20rc1与当前模板版本分开。示例加auto-tool-choice并把served/API模型名统一为Eco-Tech/Kimi-K2.6-w4a8；不能继续请求旧kimi_k26。Transformers<=4.57.6限制只保留给v0.20及以前，不无条件降级当前环境。参考评测换成v0.23的A3实例，AIME96.67、GPQA90.91、MMMU81.89；不是跨版本实测增益或本仓结果。 |
| [Kimi-K3](../models/vllm_ascend_kimi_k3_kda_mla.md) | 新文明确只支持MRv2，每个节点显式开启。950DT的P/D及pool例分别memory0.80/0.90，A3仍0.80/0.80；这是配方预算，不能把0.90推广为任意模型/硬件默认值。 |
| [DeepSeek-V4-Flash](../models/vllm_ascend_deepseek_v4_deployment_contracts.md) | 新例统一0731-w8a8 DSpark身份，A2 nightly-main镜像仍需固定digest。K至少5并核checkpoint config；A3 PD例P/D采用不同batch、HBM与HCCL预算，launcher更新PCP8/DP2/TP1及connector DP2，不能只替换method字段而保留旧整套拓扑。环境变量不证明两端实际transport engine一致，低KV使用也不能排除其他内存/计算瓶颈。 |
| DeepSeek-V4-Pro | 部分脚本仍显式MRv1=0，不能把整页或整个家族统一写成MRv2。950DT DP2/TP1/PCP8的o_proj权重还沿PCP分片；PCP与enable_dsa_cp互斥，不把TP1解释为所有投影完全不分片。 |
| [DeepSeek-V4.1-Flash](../models/vllm_ascend_deepseek_v41_platform_boundary.md) | PD的no_proxy覆盖本机及所有P/D服务IP；新增一段配方batch8192和DSA CP/FlashComm1/shared-expert DP仍属于该段，不能把MRv1选项套到MRv2或推所有段落全开。 |
| [Qwen3.5-397B](../models/vllm_ascend_qwen_hybrid_moe_35b_397b.md) | w8a8/w4a8名称显式保留-mtp。长上下文配方建议shm64g并同时提高memlock；只增shm不解除锁页限制，host allocation 207001和HCCL超时不应直接归NPU HBM。CPU governor/sysctl源例需在宿主执行，容器内返回0不证明生效；本仓未执行这些操作。lm_eval的served model与tokenizer分开，后者用实际checkpoint本地目录，不能把served name或ModelScope ID无条件当HF tokenizer标识。 |
| [Qwen3.8-Flash-Next](../models/vllm_ascend_qwen38_flash_next.md) | 模型页和PO删除旧QSA两个显式环境开关描述；删除示例不证明QSA融合功能已撤销。新增optimistic CPU长度的消费者生命周期/未知路径回退，与共享物理页外部恢复分别验收，见模型卡的同版本增量。 |

GLM系列proxy新例使用官方镜像内/vllm-workspace/vllm-ascend/examples/disaggregated_prefill_v1/load_balance_proxy_server_example.py；独立proxy主机也需对应环境，源码安装用实际checkout前缀。不能在任意cwd照抄相对路径，或用API就绪替代所有Decode rank Memcache初始化及Prefill PP成员成功。Memcache旧init barrier的撤销与依赖升级见[KV Pool版本增量](../deployment/vllm_ascend_kv_pool_backends.md)。

### 新版算子目录与测试入口

新版doc_writing说明MRv2 Triton实现归ops/triton/、文档归ops/triton/docs/，v2命名空间被布局重构退休；MRv1样例仍有v1目录。路径迁移不等于运行能力、ABI或Operator数值验证，不能按包含v2的旧路径反推Runner支持。对已有知识先固定原commit再按新布局查实际符号，不用全局字符串替换掩盖代码变化。

testing.md与对应PO把单卡示例更新为tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_0_6B_basic.py，定向用例为test_qwen3_dense_graph_mode；大小写B、目录与case分别保留。文档命令、select_tests路由和真实pytest/NPU结果分开记录。本次没有运行这些命令，也没有修订公共evaluator、检索排序或Scope规则。

### 如何消费这次 main 增量

先选择一个完整版本对，不能从旧配方借量化/拓扑再从新配置借默认值。安装FLA与硬件包、FinegrainedTP默认1/旧0别名、Sparse HCCL格式、LiLiCorr与MRv2 entropy分别进入[环境](../deployment/vllm_ascend_versioned_environment.md)、[细粒度TP](../optimization/vllm_ascend_finegrained_tp_contracts.md)、[RL更新](vllm_ascend_rl_weight_update.md)与[投机方法](../optimization/vllm_ascend_speculative_method_selection.md)的版本增量。文档冲突或未知模型消费者继续保留未知，不能用不同页面各一个支持句做能力笛卡尔积。

本节没有把整个3164源码升级或线上中文HTML等价性写成完成；真实网站构建身份、发布兼容行、配对Native、checkpoint、硬件和有效配置仍须一起固定。全部新内容来自静态材料，未执行服务、模型、UT、NPU或性能/Agent A/B。
