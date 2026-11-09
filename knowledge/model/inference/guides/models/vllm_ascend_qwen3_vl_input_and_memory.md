---
type: Guide
title: vLLM Ascend Qwen3-VL：Dense/MoE、视觉 token 与媒体路径验收
description: 按Dense和30B MoE区分平台/并行，验证chat template、图片视频限制及310P图前提，排除媒体下载和placeholder错误造成的性能假象。
  补齐Dense的DUO重复dtype/context、950量化权重与API别名冲突；核对 Qwen3-VL MoE 的 TP2、EP、Attention 与专家层，区分图像/视频/PP配方和多模态评测口径。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen-VL-Dense.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-VL-30B-A3B-Instruct.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen-VL-Dense.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-VL-30B-A3B-Instruct.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T16:12:50Z'
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
aliases:
- Qwen3-VL-8B-Instruct
- Qwen3-VL-32B-Instruct
- Qwen3-VL-30B-A3B-Instruct
---

# vLLM Ascend Qwen3-VL：Dense/MoE、视觉 token 与媒体路径验收

## 范围与版本

Dense 8B/32B、MoE30B-A3B是不同实现分支。Dense教程旧0.11演示不是当前各硬件最低版本，特别提示Atlas推理产品需>=0.18、950>=0.23rc1；MoE不从Dense的310P路径推支持。235B教程已停止维护，不因同family复用成当前承诺。

## 平台和媒体输入

310P仅FP16、不支持npugraph_ex；Dense图编译需CANN>=9.0.0，低版本先eager。950 W8A8-MXFP8使用对应权重，A2/A3 BF16例子另算。图capture尺寸和投机列在旧表出现不证明matching drafter已提供。

先图像再视频，限制实际image/video数、帧数、分辨率和token预算。image-only明确video=0可避免未用媒体规划。local file需容器可见目录和allowed-local-media-path；网络下载耗时须单独观测，不能当NPU前向时间。

## 多模态质量与并行

chat template应插入正确image placeholder，lm_eval需apply_chat_template；占位符缺失先修输入而非Attention kernel。对齐MRoPE positions、视觉embedding与token数，再测混batch/图。MoE才启EP，PP2短context例子只作功能验证，不能据此声明所有长视频/投机/PD组合。

## 调优和回退

按视觉token加文本/输出的总context、encoder工作区和KV峰值调并发。唯一媒体通常prefix命中低，先量真实hit再归收益；Dense表TP1/TP2描述冲突时按实际命令与日志定界。媒体/数值失败回image-only最小路径，保留processor/模板/权重版本。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## 两份完整教程与可复现配置

本节完整对照 Qwen-VL-Dense.po 的91条和 Qwen3-VL-30B-A3B-Instruct.po 的111条中文消息，以及对应449/483行英文。202条msgid均匹配，没有fuzzy或空译文；代码块不包含在这些译文的匹配计数内，因此“全部匹配”不能证明启动命令、图片输入或表格配置没有矛盾。来源命令作为数据阅读，本次未执行。

准确区分 Qwen3-VL-8B-Instruct、Qwen3-VL-32B-Instruct 与 Qwen3-VL-30B-A3B-Instruct。前两者是Dense不同checkpoint，后者约30B总参数/3B激活的MoE；不能把3B激活当全部权重存储需求，也不能把Dense的310P配方借给MoE。简介对整个Qwen-VL家族的bounding box/多图能力不替代每个checkpoint与当前API的专项验收。

### Dense 命令中的冲突先裁决

| 来源位置 | 观察到的原值 | 适配时的处理 |
| --- | --- | --- |
| DUO dtype | 先 --dtype float16，后又 --dtype bfloat16，而紧接的说明只支持FP16。 | 保留唯一符合目标硬件的dtype，记录最终解析值；不能因第一项是float16就宣布有效配置正确。 |
| DUO context | 同时有 --max_model_len 16384 与 --max-model-len 32768。 | 下划线/连字符是否归一化、重复项如何处理按目标版本核对；生成一项明确预算，不假定16384生效。 |
| 950权重 | 表列Eco-Tech的8B/32B W8A8-MXFP8 checkpoint，服务例却指向Qwen原始8B并加quantization=ascend。 | 量化flag不把浮点权重转换为MXFP8；核对真实repo/revision、quant配置和loader，不能拼成“该原始权重已按此格式验证”。 |
| API模型名 | 服务设 served-model-name=qwen3vl，请求/随机bench却用原始HF模型ID。 | 读取实际/v1/models的id，再发送该服务接受的名称；模型目录路径与API别名分开，不由文档示例推请求必然能路由。 |
| 可见设备与TP | A2/A3 Docker模板只映射davinci0，启动脚本用$1/$2/$3/$4分别传设备、port、DP、TP；场景表又混写TotalNPUs=1、tp2建议与详情TP1。 | 展开所有位置参数，检查实际device/rank和DP×TP占用，不能把“整节点”或表头当实际使用卡数。 |
| MTP | Dense推荐表给MTP Speculation Num=3，实际服务块没有draft身份或speculative-config。 | 不能单凭表格增加投机能力；先确认匹配drafter/head和状态契约。 |

针对vLLM v0.32的普通CLI解析，见[新模型预检](../bringup/vllm_ascend_new_model_onboarding.md)。该固定Native证据不自动解释旧v0.11.0rc3演示环境。DUO仍按FP16、enable_npugraph_ex=false和CANN>=9.0.0图门槛裁决，低版本来源建议eager；图尺寸、DP/TP和每个checkpoint的完整组合另验。未运行任何纠正后的命令，不把配置修订当适配完成。

### MoE 的图像、视频与PP场景分开

| 场景 | 固定来源的布局与预算 | 边界 |
| --- | --- | --- |
| A2/A3图像服务 | Qwen/Qwen3-VL-30B-A3B-Instruct，DP1/TP2加EP，context32768、seq32、batch16384、HBM0.9；A3 HCCL_BUFFSIZE=1024。 | 来源表写BF16，命令依赖实际checkpoint/auto解析；A3两处相同fused_mc2 additional-config不代表启了两个独立功能。 |
| 950DT图像服务 | Eco-Tech/Qwen3-VL-30B-A3B-Instruct-w8a8-mxfp8，DP1/TP8加EP，context32768、seq32、batch8192、HBM0.9，HCCL_BUFFSIZE=400。 | 与A2/A3浮点权重、TP及通信预算不同，不能只替换镜像后缀；不是310P或所有950型号配方。 |
| 视频推荐表 | TP2/PP1、context128000、seq8、batch4096，本地媒体路径。 | 表中推荐与前述只允许image1/video0的实际启动块不同；增加video前重新规划encoder、KV、媒体与并发容量。 |
| PP图功能验证 | TP1/PP2，两设备、context4096、batch1024，prefix关闭。 | 仅功能布局，不证明128K视频、PD、MTP或高吞吐的组合已验证。 |

#### MoE 的 TP2、EP 与 Attention 分工

MoE的“同一专家层不要同时用MoE TP与EP”不能解释成所有--tensor-parallel-size必须为1：源例明确TP2与EP同开，Attention等并行与专家层选路应分开。实际专家组、切分轴与通信仍要按实现/运行日志核对；本段没有穷尽MoE实现。

两种图像启动块均用 --limit-mm-per-prompt.image 1 和 --limit-mm-per-prompt.video 0 限定输入；MoE的 --enable-expert-parallel 与整体 --tensor-parallel-size 按层职责核对。intro所列“离线/视频”不构成缺失脚本已被本次复现。shm-size=512g是部分A2/A3容器模板的宿主共享内存设置，950模板为1g，不当NPU HBM预算或已分配容量。通信buffer、图、activation、encoder、KV以及宿主媒体处理分别计量。

### 输入、质量与性能的独立判据

先实际图像请求，核对模型名、processor、chat template、image placeholder、视觉token与MRoPE位置，再加入视频、混batch、图与目标并行。仅文本“Who are you”或HTTP200/choices存在不证明视觉encoder参与。来源TONGYI Qwen图片例只是smoke，不能硬编码成所有输入的正确答案。

视频file URL需要宿主媒体目录确实挂入容器、服务allowed-local-media-path允许该目录、请求引用对应容器路径三者同时成立；源例将目录挂入 /media，服务设 --allowed-local-media-path /media，请求为 file:///media/test.mp4，这些路径按实际挂载调整。媒体URL可下载不证明解码/processor正确；下载等待与NPU计算分开计时。图像占位符缺失先查模板和输入，不能直接归为attention kernel错误。

| 来源精度报告 | 模型、环境与口径 | 不可借用的结果 |
| --- | --- | --- |
| MMMU 0.5389，stderr0.0159 | Dense8B，旧v0.11.0rc3 A2/A3；lm_eval vllm-vlm离线、maxlen8192、HBM0.7、batch32、apply_chat_template。 | 非32B、MoE、DUO或950结果。 |
| TextVQA 80.57 | Dense8B，DUO v0.23.0rc1，AISBench textvqa_gen_base64。 | 数据/单位与MMMU不同，不作跨平台加速或质量等价比较。 |
| MMMU acc,none=0.58 | MoE30B教程的扁平来源表，未闭合完整硬件、模型revision和评测原始记录。 | 不补造本仓执行、置信区间或全部平台精度通过。 |

随机文本bench的input200、prompts200、request-rate1仅可定位对应服务流水线；源文没有实际吞吐/时延结果，也没有图像/video payload，不能把它当视觉token性能。真实多模态评测固定分辨率、帧数/采样、视觉token、输出长度、并发和缓存命中。唯一媒体或随机prompt缺少可复用prefix，不据此否定所有APC收益；保存真实hit与无cache对照。先修身份/输入/数值，再比较TTFT、TPOT、吞吐和峰值，本次未下载数据、运行评测或增加verified。
