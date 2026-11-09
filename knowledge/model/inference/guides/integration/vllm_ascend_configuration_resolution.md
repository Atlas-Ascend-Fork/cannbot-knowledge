---
type: Guide
title: vLLM Ascend 配置生效链：工厂初始化、字段优先级与缓存刷新
description: 解释additional_config初始化、回写与缓存，核对Scheduler、CPP、ShortRequestFirst与profiling-chunk组合及STAIR phase；中文差异按实际字段和消费进程裁决。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/configuration/additional_config.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/large_scale_ep.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/configuration/env_vars.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/configuration/env_vars.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/configuration/additional_config.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ascend_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/parallel_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/mrv2_utils.py
  role: implementation
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-11-03T06:46:24Z'
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

# vLLM Ascend 配置生效链：工厂初始化、字段优先级与缓存刷新

## 适用范围与任务

本卡解释 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的配置解析；硬件范围表示检查流程覆盖四类框架分支，不表示所有配置或功能均可在四个平台启用。产物是用户输入、初始化后的有效配置、实际 Worker/Runner 和回退日志的对应记录。

## 先确认配置由谁消费

在线 `--additional-config` 与离线 `LLM(additional_config=...)` 承载插件扩展；图模式、上游 EPLB、EC manager 等仍有自己的配置对象。不能因为字段最终都影响推理，就把它们任意塞进 additional_config。平台会检查、派生并回写配置，Worker 还要在实际进程初始化。

`init_ascend_config()` 是完整初始化入口：先解析 scheduler、稀疏 offload、KVPP、dump 和 Runtime Guard 子配置，再构造 AscendConfig，运行跨对象 `derive_and_validate()`、RL 应用与细粒度 TP/Xlite 前置检查，最后发布完成校验的缓存。直接实例化 AscendConfig 不会自动完成这条业务链。

## 优先级和类型

调度字段采用 `scheduler_config.<key>` → 顶层遗留字段 → 默认值；二者同时出现时嵌套字段优先并告警。该规则明确属于 SchedulerConfig，不能推广为所有嵌套字典都递归合并。SchedulerConfig的错误类型和未知嵌套键会进入其类型校验；MRv2 EPLB在平台钩子中另有未知键告警过滤/回写，见下文，不使用全局统一的未知键处置假设。

迁移说明开头保留过渡期“支持环境变量”的描述，但本版本参数表与代码已对多个变量说明删除，例如余额调度不再回退旧环境变量。使用实际字段和读取代码判断，不把旧兼容总述当成每个变量仍受支持。`refresh`、上游注入的 GDN/KDA backend、派生字段等在工厂中有专门处理；Omni 安装时还存在共享扩展键的分支，不能把这当作任意拼写都会被接受。

## 缓存与有效配置验证

同一 VllmConfig 对象、未要求 refresh 且缓存完整时，可复用进程内配置。换对象、请求 refresh 或启用 RL 等情形会重新走初始化。失败的构造不应发布成可用单例。不能仅修改原字典后假设所有缓存和子进程同步更新。

验证时保留启动输入，检查最终图模式、Ascend 子配置、选中的 scheduler/Worker/Runner、派生并行参数及降级日志。布尔字符串、整数开关与枚举分别按目标字段校验，不能用 Python 的 `bool("false")` 代替配置语义。

## 失败与回退

出现未知字段、范围错误、功能冲突或实际路径未变化时，先恢复最小配置，再逐项加入。跨进程差异沿[插件初始化](../../concepts/frameworks/vllm_ascend.md)检查；图模式回写见[图优化流程](../optimization/vllm_ascend_graph_mode_selection.md)。变更配置后重新启动需要重建的进程，不通过改内部派生字段绕过校验。

## Evidence

参数文档、SchedulerConfig.from_additional_config、init_ascend_config 与平台配置钩子共同支持上述链路。本次为固定源码核对，未执行 NPU 配置实验。

## 遗留大规模 EP 模板的迁移边界

固定 large_scale_ep 指南仍推荐 v0.9.1，含旧 deepseek_mtp、enable_weight_nz_layout、外部 DP 环境变量与 fork 启动模板。它只作为历史架构参考：实际新版本逐项核对 scheduler/parallel/loader 字段与 worker 生命周期，不能将整段脚本当成当前主线支持。节点内外通信、global/local DP rank 与端口审计仍需完成；旧模板中的 buffer 数字不是性能最优或新版本默认值。


## 中文环境变量入口与迁移总述

env_vars.md与env_vars.po的4条业务译文覆盖标题、环境变量用途、迁移提示和include_code指令，msgid均对应当前英文。页面建议新部署优先使用--additional-config，同时笼统保留“迁移期间旧环境变量仍支持”。该总述不重新启用已经在具体参数表或读取实现中删除的变量；逐项检查真实字段、类型、优先级和消费进程。

页面通过include_code引用envs.py中begin-env-vars-definition与end-env-vars-definition之间的定义，不是独立完整的默认值表。生产每个环境变量的具体合同仍需读取固定envs.py及实际调用点；仅核对这个入口与译文不代表已逐项闭合全部环境变量，也没有执行include代码或网站构建。


## 中文参数表的版本差异与配置归属

STAIR phase指MRv2的load_collection_phase负载采样选择；非all要求--enable-eplb，并且该过滤只对STAIR策略有效。它与Scheduler未知键校验、CPP开关或请求验证阶段不是同一项配置。

固定additional_config.po有181条有效译文，173条msgid在当前英文连续匹配，8条未匹配；匹配不是翻译正确、表格完整或网站渲染证明。不能把这张四类硬件的配置排查流程当成所有选项均跨硬件可用。

| 旧译文入口 | 当前固定英文及所读实现的处理 |
| --- | --- |
| CPP smooth_factor=0可关闭动态调整 | 当前ProfilingChunkConfig要求0 < smooth_factor <= 1，0即使enabled=false也不通过该校验；关闭用enabled=false。need_timing未指定时跟随enabled，显式False保留；disabled且timing=True会告警回写False。min_chunk需正，max_fit_chunk实际拒绝<=5，报错中的“至少30”是推荐，不是>=30硬下界。 |
| ShortRequestFirst不能配profiling-chunk | 当前英文允许此组合；仍不支持batch-job-aware和PD分离D节点。不能由旧译文继续禁止CPP组合，也不据此保证所有调度器组合正确。 |
| load_collection_phase只写批次分类 | 当前补充只有STAIR有效，非all需要--enable-eplb；该开关不是所有policy通用的采样过滤。 |
| KVPP仅MLA、PCP须显式V2环境变量 | 当前描述TP×PCP组内持久KV层分布，DP副本与PP stage隔离；不能把旧行当完整Runner选择规则。 |
| KVPP只能eager且不支持连接器 | 当前英文支持非hybrid MLA/SFA的eager或PIECEWISE，仍不支持Full graph与DCP；MooncakeConnectorV2的P/D、AscendStoreConnector及MultiConnector按子连接器type/role约束使用，P/D仅P端开KVPP。具体实现与验收见[KVPP指南](../optimization/vllm_ascend_kvpp_capacity_tradeoff.md)。 |
| enable_dsa_cp仍在旧表行 | 当前英文表未保留该行，不等于代码已移除字段。所读derive仍拒绝与PCP>1或MRv2组合，并按index_topk与sequence-parallel MoE派生最终开关；有迁移告警，不能仅因表缺行推断任意新模型可启用或API已删除。 |
| early kernel warmup不区分Runner | 当前英文明确rejection sampler和penalty预热仅V1，V2跳过；不能推广成V2跳过所有预热，RMS norm/NZ及实际加载时序要分别检查。 |
| MRv2只异步Gloo，MRv1只排除phase | 当前英文增加全rank可用时HIXL，否则Gloo CPU staging；MRv1同时排除load_collection_phase与stair_config。已经开始HIXL后的失败不是可局部回退Gloo的承诺。 |

当前英文与译文仍共同声称EPLB混用schema启动失败，但所读平台_validate_eplb_config对MRv2部分未知legacy/STAIR字典键先告警、过滤、回写，MRv1出现V2键等条件才另报错。因此先记录用户输入、平台修改后的additional_config与最终AscendConfig；不能把所有未知键统一归成“拒绝”，也不能认为所有错误都会被忽略。完整条件见[EPLB配置指南](../optimization/vllm_ascend_eplb_runner_and_movement.md)。

配置消费对象也须分开：上游--eplb-config与Ascend additional_config.eplb_config不是同一对象；Score管理器使用--ec-manager-config/离线ec_manager_config，不嵌入additional_config；Runtime Guard的启动overlay和JSON热重载分别有优先级。参数表示例中的数字、图模式与开关只是该来源的配置说明，不能作为跨模型/硬件的性能最优值或真实运行结果。

新框架适配时把默认值、示例值、派生值和最终消费值分别留档。具体调度见[短请求优先](../optimization/vllm_ascend_prefill_short_request_first.md)与[CPP校准](../optimization/vllm_ascend_cpp_prefill_calibration.md)，缓存策略见[Score编码器缓存](../optimization/vllm_ascend_score_encoder_cache_policy.md)。本次没有执行配置类、预热、安装或NPU服务。


## 3164固定增量：默认值、Runner与能力派生

本节只说明Main `3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 相对ceac的变化，不移动前文基线。完整语义AST差异与注释变更结合必要原始diff读取；相同函数按AST精确复用，不把变更文件称为逐行全文。未导入配置或运行目标环境，原平台/Scope与验证边界保持。

`FinegrainedTPConfig`的四种size默认由0改为1；1表示不分片，只有>1才启用，0只是旧配置的关闭别名。模型门禁、DP整除、batch-sharded sampling冲突、LM-head/embedding/MLP组创建和utils消费者同步改用>1。capture容量不足时O-proj/MLP也回写1。不要把原“>0即启用”的判断带入此版本，也不能由默认值推断所有细粒度TP组合已验证。

enable_dsa_cp字段、派生、自动启用FlashComm及相关utils缓存入口在这一增量移除；普通SP/共享专家仍各有图capture对齐条件。MRv1/V2 replay不再为旧DSA-CP额外补TP长度。前文ceac表缺行但实现仍存在的判断只属于ceac，不能跨版本继续推荐已移除的开关；PCP/DCP是否支持仍查对应模型和后端。

统一MegaMoe配置判据不再先走独立A5分支。新增/调整的条件包括hidden_size 1024–8192且512对齐，moe_intermediate_size 256–4096且128对齐，跨DP并扣除PP的EP world size至少2、专家数可整除该size、top-k在1–16。MiniMax可从intermediate_size补取MoE宽度，其他模型不无条件借用该字段。这只是所读配置资格的一部分，后续dtype/算子/硬件条件仍保留，不是实测支持矩阵。

`mrv2_utils`的默认V1 blacklist移除了pooling和enable_dsa_cp。环境变量VLLM_USE_V2_MODEL_RUNNER仍先裁决；VL encoder graph、draft_window_size、suffix/ngram/draft_model、非eager DFlash2与P-eagle等剩余理由继续生效。移除blacklist不是证明这些任务的NPU输出/图已通过。平台额外核FlashAttention支持head_size，DSpark候选target增加GlmMoeDsa；Qwen4Exp的Engram校验有模型专门分支。

DeepSeek-V4在platform.update_block_size_for_backend提前保留自身block-size处理，utils仍纠正不在32/64/128的值。新ETP组仅在Engram请求的并行度不同于全TP且旧ETP未独立建立时创建，rank重排沿DP轴；group size或字段存在不是跨拓扑可互换的证明。新版本的实际Worker与state接入见[追版检查](../bringup/vllm_ascend_new_model_onboarding.md)。
