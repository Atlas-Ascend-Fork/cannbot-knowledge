---
type: Guide
title: vLLM Ascend 3164 发布片段与升级诊断入口
description: 汇总固定 main 3164 相对 ceac 新增的发布片段，关联适配、量化、缓存、投机与性能回归；区分片段声明、源码合同和设备实测。
aliases:
- 3164发布片段
- 新版本性能修复入口
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/16350.yaml
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/17147.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/18447.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/18459.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/18549.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/19395.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/19460.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/19601.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/19639.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/19708.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/19756.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/19954.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20107.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20111.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20116.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20120.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20134.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20207.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20210.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20258.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20276.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20290.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20303.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20308.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20321.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20369.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20382.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20404.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20456.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20469.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20474.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20512.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20533.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20544.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20567.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/release_notes/fragments/20660.yaml
  role: implementation
created_at: '2026-11-03T06:48:03Z'
updated_at: '2026-11-03T06:48:03Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 3164 发布片段与升级诊断入口

## 适用范围与使用顺序

本卡读取固定提交 `3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 新增的36份 `release_notes/fragments/*.yaml`。比较基线是 `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`；PR编号用来回查片段身份，本卡没有抓取PR讨论或运行其中的测试。这些片段还不是一份已发布版本的兼容矩阵，也不能证明下列能力已包含在任意release镜像。

Agent先固定目标Ascend/Native提交与实际安装依赖，再用下表选择源码合同和验证任务。片段的“优化/修复”是上游声明，不能直接写成本地实测收益、已解决全部故障或跨硬件支持。基线知识与本次增量各自保留版本身份；完整环境沿[版本化环境](../deployment/vllm_ascend_versioned_environment.md)，升级动作沿[发布迁移](vllm_ascend_release_migration_contract.md)。

## 模型与权重适配

| 片段PR | 新声明与适配检查 |
| --- | --- |
| 18447 | GLM-5.3-Flash在支持的950上可选FP8 pooled-key indexer，scale为FP32；与下文A3 INT8不同，不把量化名称、scale dtype与硬件互换。 |
| 18459、18549 | W4A8 MXFP MoE加入EPLB；MRv2/A5 AllGather修复冗余专家路由和负载计数。核活动专家列表、有效source mask及物理/逻辑专家坐标，不能由开启EPLB推所有格式兼容。 |
| 19395 | MRv2对旧DYNAMIC_EPLB/EXPERT_MAP_RECORD警告并忽略，改用--enable-eplb/--eplb-config；additional_config.eplb_config和stair_config不支持字段改为告警过滤，受支持值继续保留。启动成功不说明被过滤的字段已生效。 |
| 20111 | oproj/lmhead/embedding/mlp四个finegrained_tp_config默认统一1，只有>1启用。显式1走未分片路径；MLP=1不再要求重算调度。旧0仍作为禁用兼容值，但已不在文档范围；不能把旧0作为当前推荐默认。 |
| 20120 | MiniMax MXFP8 dispatch/combine修复scale policy，保留显式量化输入及配置覆盖；验证实际scale选择，避免把格式转换和策略选择合并成一个布尔开关。 |
| 20276 | Qwen4Exp PLE embedding在A2/A3增加Engram TP，可分片表以适配DP+TP；ETP不是普通TP数值的同义替换，需核表owner、通信组和offload生命周期。 |
| 20469 | ModelSlim W4A8动态Linear新增对称per-channel INT4权重、per-token INT8激活；这条声明不包含任意groupwise、非对称或静态激活格式。 |

实现分别进入[W4A8 Linear](vllm_ascend_w4a8_int_linear_contract.md)、[MXFP4重载与活动专家](vllm_ascend_mxfp4_weight_reload_contract.md)、[细粒度TP](../optimization/vllm_ascend_finegrained_tp_contracts.md)、[Qwen4 PLE](vllm_ascend_qwen4_exp_ple_contract.md)及对应EPLB合同。若源文件名称相近，仍以来源提交和实际分支为准。

## 注意力、缓存与图执行

| 片段PR | 新声明与诊断检查 |
| --- | --- |
| 16350 | native SFA DCP优化query布局、output/LSE交换和稀疏索引映射，C8 key/scale联合发布；大payload用有界tile修复UB分配失败，单token奇异singleton stride修复BF16→INT32 view。分开验证坐标、scale、stride与UB资源。 |
| 19639 | MLA decode补齐layerwise KV load wait与prefetch-start；短prefill复用外部KV可能触发错误输出、陈旧completion event或下一次load阻塞。先核wait/start顺序和事件消费，不把HTTP成功当缓存恢复正确。 |
| 19756 | FX fusion修复只给首个compiled model prefix注册pattern；draft空matcher会静默关闭融合。无bias RMSNorm动态norm+quant补匹配，且限制INT8，避免把INT4/FP8 quantize节点替换为INT8算子。 |
| 19954 | aligned Mamba cache降低GDN metadata准备开销，包含混合prefill/decode与可变投机长度；性能测量仍需分离host metadata与设备kernel。 |
| 20107 | DeepSeek-V4 VL memory profiling的dummy image考虑宽图及token/宽高比约束；短方图启动成功不能证明最坏视觉激活预算正确。 |
| 20116 | A5 QSFA优化可选RoPE和INT8 paged sparse KV；尾部/全invalid索引排除计算，空有效范围输出初始化。以实际有效前缀与padding sentinel做数值边界验证。 |
| 20210 | MRv2 DeepSeek-V4.1 SWA bounded decoder replay支持PCP+DP，包含不均衡/空闲DP batch；不能只验证所有rank等长满载。 |
| 20290 | MiniMax-M3在A5增加AscendC sparse decode index scoring，以及CEIL-scale MXFP8 clipped SwiGLU融合；其他activation/quant路径保留，不能强制所有MXFP8走CEIL。 |
| 20303 | A3/DeepSeek-V4.1 QLI采用自适应Top-K accumulator宽度与Level-0重复的向量批处理；核Top-K边界及输出索引，不把kernel级优化当整模型吞吐保证。 |
| 20308 | A3 MiniMax-M3融合QK norm/RoPE/cache insertion复用归一化权重，减prefill延迟；片段也明示极小batch可能回退，评测需要覆盖该区间。 |
| 20404 | fork QSFA在arch32/35内部清零TND输出尾部，修复capacity缩小后的stale/NaN；GLM SFA C8 decode移除逐层冗余masked_fill。先确认目标kernel已承担清零职责，再裁定删除host补丁。 |
| 20456 | A2/A3 INT8 per-tile sparse attention使用实际NoPE宽度、加速KV gather与地址准备，覆盖大页表和valid-prefix后invalid slots。不能把逻辑宽度与存储padding宽度混用。 |
| 20512 | GLM-5.3-Flash修复PCP query行、NoPE metadata容量、decode partition和混合批packed-KV破坏；回归需同时核query坐标和物理缓存owner。 |
| 20567 | A3可通过--attention-config.indexer_kv_dtype int8选择PoolKeyIndexer，需兼容ops-transformer；默认BF16不变，main KV dtype仍独立。 |
| 20660 | QSFA dispatch tiling访问修复覆盖A2/A3/A5静态kernel；不能由分发修复推算任意shape或编译版本均已测试。 |

复用[DeepSeek新版迁移](vllm_ascend_deepseek_3164_migration_contract.md)、[GLM/Kimi新版迁移](vllm_ascend_glm_kimi_3164_migration_contract.md)、[MXFP8 CEIL激活](vllm_ascend_mxfp8_ceil_activation_contract.md)与相应SFA/QLI合同。旧版chunk、物理页stride、输出tail清零及图捕获约束须逐条核对，不能用同一个模型名取并集。

## 投机解码与状态恢复

| 片段PR | 新声明与验收边界 |
| --- | --- |
| 17147 | LiLiCorr是DFlash变体，Ascend需MRv2及eager draft；使用匹配训练checkpoint，不能用普通DFlash/DFlash2权重替代。 |
| 19460 | MRv2新增Entropy Verify，additional_config.rejection_sampler_config.enable_entropy_verify开启；与upstream block互斥，标准rejection的无偏分布保证不能直接沿用。 |
| 20134、20369、20474 | GLM KDA RecoverSSM为MRv2实验路径，需--use-replayssm及投机；后来加入block-aligned前缀checkpoint，设备端request routing/一维grid降低边界与混合提交开销。前缀支持不等于任意token位置都有状态checkpoint。 |
| 20382 | A5 GLM GQA DSpark draft可用device-length CANN FlashAttn；head192补零到256，draft KV payload增加1/3，合格消费者可免投机CPU长度同步。该资格门禁与概率接受率是不同问题。 |
| 20258 | V2 penalty prompt-mask采用有界Vector-core tile循环；大history bincount修复program上限及Triton3.6全局常量规则。只调请求batch而不覆盖history长度会遗漏这类失败。 |

完整使用条件见[投机方法选择](../optimization/vllm_ascend_speculative_method_selection.md)和[新版GLM/Kimi](vllm_ascend_glm_kimi_3164_migration_contract.md)。必须分别比较target-only、greedy draft、probabilistic draft，并保留质量指标；本卡未运行这些实验。

## 服务调度、外部缓存与依赖

| 片段PR | 新声明与排查入口 |
| --- | --- |
| 19601 | batch-job-aware scheduler清除被移除请求的cached selection；模拟abort/finish后再调度，不能只看首次schedule。 |
| 19708 | proxy可选--enable-prefill-affinity，使多轮Agent请求固定prefill端，decode仍按负载调度；不是强制所有请求或全部角色粘连。 |
| 20207 | balanced scheduling补报prefix-cache queries/hits计数；旧零计数不能直接判没有cache命中，新指标也不证明外部SSD恢复。 |
| 20321 | AscendStore bulk/layerwise初始化清除陈旧Memcache barrier参数；版本迁移要核实际constructor，不能继续塞旧配置以期待同步。 |
| 20544 | AscendStore把scheduled request IDs和leased KV keys反复扫描换为线性查询；host准备开销变化与网络/存储吞吐分别测量。 |
| 20533 | A2/A3 Ubuntu/openEuler镜像的flash-attention-npu更新到main快照2e5320494cb474365bacaf42c94abf0c7de0affc（0.5.0）；精确镜像与包版本一起留证，不把包名混同FLA NPU或CANN Ops。 |

实际升级仍需要对应UT/E2E选择、真实设备与模型正确性、性能负载和回退版本。[测试证据选择](../bringup/vllm_ascend_test_evidence_selection.md)用于划分mock、shape/ABI、数值和真实服务证据。本文未执行上游、NPU、网络、安装或Agent A/B；新卡保持draft，不新增任何已验证硬件声明。
