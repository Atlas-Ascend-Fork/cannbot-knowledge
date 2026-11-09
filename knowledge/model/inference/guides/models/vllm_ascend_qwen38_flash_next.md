---
type: Guide
title: vLLM Ascend Qwen3.8-Flash-Next：QSA/GDN 与实验前缀缓存
description: 按A3实验预览范围接入GDN加QSA、PLE和MTP，使用align模式验收前缀状态，不继承已停止维护Qwen3-Next的支持结论。 补齐DP1×TP8、QSA融合开关、draft eager与target graph、图文/工具调用闭环和thinking响应字段。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3.8-Flash-Next.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.8-Flash-Next.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/qwen38_mooncake_basic_pooling.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/tutorials/models/Qwen3.8-Flash-Next.md
  role: primary
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-11-03T01:56:47Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Qwen3.8-Flash-Next：QSA/GDN 与实验前缀缓存

## 范围与结构

来源A3、0.26.0rc预览，W8A8-MTP权重参考一Atlas800A3节点。GDN+QSA、gated residual、PLE与native MTP组成混合执行路径，不是旧Qwen3-Next同一实现或维护状态。

## 状态缓存是接入重点

Automatic Prefix Caching仍实验，要求enable-prefix-caching+mamba-cache-mode=align，并重新验证HBM容量。不能只看总表prefix✅就忽略实验限制；QSA缓存、GDN recurrent/conv state和PLE positions应与目标实现对应。

先无prefix/投机的最小eager参考，验证短长文本及目标支持的多模态；再逐项启MTP、图和align prefix。两请求共享前缀时，检查所有状态可达而非仅Attention KV hit。

## 优化与停止

记录真实命中、accepted长度、TTFT/TPOT和峰值；与原状态路径比较。未知硬件、丢状态或输出偏离时不扩大平台结论，关闭实验prefix并清理不兼容namespace，回已确认配置。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## 完整参考部署与中文版本差异

Qwen3.8-Flash-Next.po 的73条消息对照完整365行英文，58条msgid匹配、15条有修订。旧PO的A3-only与A2/950待支持描述在当前英文不再单列，但现有整套实例仍只有A3；删除一句不构成新增平台支持，本卡平台保持A3。旧Qwen3-Next停更边界也不替代此实验模型的状态。

准确checkpoint为 Eco-Tech/Qwen3.8-Flash-Next-w8a8-mtp，正文DP1×TP8并启enable-expert-parallel，context131072、seq8、batched tokens4096、HBM0.93，端口8088。前置表64GB×8、Docker映射16设备、服务意图使用前8个分别是容量/可见性/部署范围；旧PO曾说只暴露8个。实际rank、使用设备及专家组须看最终解析与运行日志，不从容器映射16行推出TP16或两个副本。

镜像为 qwen3.8-next-a3 或 qwen3.8-next-a3-openeuler；图中/文中标签“已验证”只是来源报告，没有提供本仓digest/实际软件运行记录。模型权重目录、CANN/NNAL与所选版本逐项记录，源脚本清空include环境变量、source脚本和pull镜像都未在本次执行。

## QSA、投机与图的不同开关

| 项 | 来源示例 | 消费边界 |
| --- | --- | --- |
| QSA Lightning Indexer | VLLM_ASCEND_ENABLE_QSA_LIGHTNING_INDEXER=1。 | 选择融合indexer路径，不证明所有shape/精度已覆盖。 |
| QSA Expand E3 | VLLM_ASCEND_ENABLE_QSA_E3V=1，并unset VLLM_ASCEND_FORCE_QSA_REFERENCE。 | 路径选择与实际kernel可达性/数值另验，不把环境字符串当加速测量。 |
| Target decode图 | FULL_DECODE_ONLY，capture[4,8,12,16,20,24,28,32]。 | 这是A3 TP8实例，不能套DUO最多两档规则或反过来移植到DUO。 |
| MTP draft | qwen3_5_mtp，num_speculative_tokens=3，speculative-config.enforce_eager=true。 | 仅保持draft proposer eager，不表示target decode也eager；接受率高也不自动代表净时延更好。 |
| norm/quant路径 | ascend_compilation_config.fuse_norm_quant=false。 | 特定W8A8的来源验证设置，不从“融合更快”直接改成true。 |
| 实验APC | enable-prefix-caching加mamba-cache-mode=align。 | 同时维护GDN与PLE checkpoint以及QSA状态，按context/并发重验HBM；Attention KV hit不是全部state可复用。 |

先建立同硬件、同权重的最小正确参考，再逐项比较这些路径；失败恢复完整旧参数和状态namespace。不能把本卡的align实验条件泛化到3.5/3.6/3.8 Dense的所有APC版本。

## 图文、工具与思考输出分别验收

该参考实例未设置language-model-only，保留视觉encoder。源例提供image_url加text，预期choices[0].message.content描述该图片；要同时核对服务侧可读图片、processor/图像token和语义。仅文本HTTP200不证明图像路径；加language-model-only后不能继续把图片用例当该部署的已支持行为。

Function Calling用enable-auto-tool-choice和tool-call-parser=qwen3_xml；请求tools声明schema并设tool_choice=auto。解析到choices[0].message.tool_calls只完成模型选择与结构化输出，调用方还需执行已授权的函数、回传对应结果并取得后续回答，不能把tool_calls当工具已经执行或副作用已成功。摄入时的天气函数只是示例数据，本次没有执行它。

reasoning-parser=qwen3与chat_template_kwargs.enable_thinking分别控制解析和思考请求；来源默认thinking，可显式false。当前英文把推理字段明确写为reasoning_content，旧PO第50条只称reasoning field；按目标版本保存真实响应，不混用GLM的字段或凭最终content非空就证明parser已拆分。解析字段位置以实际response schema为准。

来源v0.26.0rc A3 W8A8的GPQA Diamond accuracy为90.4，只是对应实例的报告，不是本仓/所有版本、所有模态或工具链正确率；模型简介的架构预览也不是未来Qwen4能力保证。本教程性能部分只给评测入口，没有吞吐/时延数据。图文、工具闭环、thinking开/关、长输入、共享/非共享前缀、抢占与MTP状态分别通过后，再用相同负载比较TTFT、TPOT、吞吐和峰值，不由结构名或开关数量推性能。


## 2026-11-03 main 增量：共享物理页的外部缓存恢复

本节固定3164adc8fe75892fbf7f99f524bb72fddf1e6efd，完整读取新文docs/qwen38_mooncake_basic_pooling.md100行，并有界读取模型教程变更hunk；后者新增消费者能力说明，不是该新教程388行全文。原A3实例、stable状态与平台范围保持，不据未指定硬件的新文档扩展支持，也没有执行其中的CPU套件或NPU恢复。

新文声明MRv2与AscendStoreConnector支持QSA K/V和GDN conv/recurrent共享物理页、但live block IDs互不重叠；raw/compressed indexer各有独立slab，PLE与hidden state是私有bank。视图的物理stride可大于payload，传输要保留stride、其他owner、未用block与padding。只按逻辑tensor.nbytes连续拷贝不能视作已满足此布局。

bulk与已有Mooncake block-key/Memcache GVA逐层路径分别接入。逐层QSA在indexer及main-KV更新后打开传输窗口；PLE读conv前等待。共享物理层只等待一次load，每个owner再复制自己的state行，GDN两行、PLE一行。私有raw-indexer靠replay重建，lookup需先找所有必需状态可恢复的共同边界：文档以粒度1536示例，prompt9216查7680，9217才查9216，不能只因Attention命中最长前缀就恢复所有混合状态。

MTP时save finalization推迟到draft之后，MambaCopyKVConnector.finalize_step转发至被包装connector完成deferred save并清metadata。文档的bulk MTP验证使用FULL_DECODE_ONLY，逐层要求PIECEWISE；load_async沿既有完成/每层等待路径，异步图恢复、任意复用/offload组合仍待独立验证，也没有新增不完整外部读的恢复机制。按配置成功、写入SSD或旧布局结果不能证明当前packed-page正确：外部恢复要有零本地命中、实际backend read和匹配输出；SSD还需逐出后的hit及rewarm bytes。

匹配0.3.14rc1的RoCE配置只是来源列出的一个Ascend环境；它不证明其他机器HCCS不可用。逐层read lease覆盖完整transfer/compute session，lease timeout先与布局错误区分。CPU mock覆盖stride、fragment、block重排、整backing sentinel及owner时序的测试定义，不替代真实跨进程传输和整模恢复。

## 同版本 MRv2 decode 提交的消费者能力

模型教程新段声明仅当最终target architecture为Qwen4ExpForCausalLM或Qwen4ExpForConditionalGeneration，并在KV初始化后一次确认target及MTP draft attention consumers时，启用optimistic CPU长度上界；精确positions、accepted counts、KV slots与递归state仍在device。该声明不要求额外的TP8、DP1、PP1、SP-off、prefix-off、PLE-offload-off、FULL图或固定K条件，不能从旧实例配置发明这些额外guard。

未知target/draft消费者、CP、sparse KV offload、realtime media仍走精确CPU同步；Runner已有PP exact-count保护继续适用。普通非realtime多模态列在文档能力内，connector的load/wait/ack/error不变。能力决定固定于model-state初始化生命周期，变更配置或消费者要重新初始化，启用前一次排空旧copy stream；不能让生产/消费跨batch独立切换。这里只记录文档声明，未闭合新消费者实现或执行多媒体/PP/图；实际其他模型与运行限制仍按对应合同验收。
