---
type: Guide
title: vLLM Ascend Kimi-K3：KDA/MLA 混合状态与多节点部署契约
description: "按A2仅文本、A3/950图片能力选择Kimi-K3部署，核对KDA/MLA状态、平台草稿、PP4、DCP与MemCache。950分层仅环境变量，不补JSON；P侧MC2模式2、shared expert与D侧recompute、MLAPO分开。角色预算与来源评测绑定版本，外部draft/SDK、HTML归属及NPU仍未验证。"
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Kimi-K3.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Kimi-K3.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/external_online_dp/launch_online_dp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/pd_disaggregation_mooncake_multi_node.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_speculative_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/engine/arg_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: implementation
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-11-04T03:35:06Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- Kimi-K3
- Kimi K3
- Kimi-K3-w4a8
- Kimi-K3-DSpark-MLA-NPU
- Kimi-K3-DSpark-Block5
- Kimi-K3.po
---

# vLLM Ascend Kimi-K3：KDA/MLA 混合状态与多节点部署契约

## 范围与模型差异

K3由KDA、周期Gated MLA、Stable LatentMoE和MoonViT组成。教程覆盖A2/A3/950的指定多节点配置；**A2配方仅文本，图片请求只适用于本卡来源的A3/950配方，视频不支持**。总支持表较窄，保留差异并按具体版本验收，不能把多模态包装类存在当成所有平台都支持图片。

| 先确定的条件 | 应读位置与使用边界 |
| --- | --- |
| A2 | 下文“当前全文、权重和版本”及混合部署A2行；保留来源0.23基线与text-only，不套Main pin或A3/950图片、DSpark配方 |
| A3或950混合部署 | “混合部署：global DP与每引擎预算”；按各平台草稿、TP、batch及容量分别配置 |
| PP4分离、1M或MemCache | “普通PD与1M” → “Launcher、PP rank与端点” → “MemCache”；先分清P的PP rank与D的DP rank，再核全组状态可读 |
| 接入代码而非复制部署模板 | “MTP注册入口”与“DSpark草稿实现”；target、MTP和DSpark是不同实现入口 |


## 权重与接口

目标W4A8需完整config/tokenizer/image processor。A3和950的DSpark checkpoint不同，两端选同平台draft，保持相同K，P保持eager。tokenizer-mode/reasoning-parser/tool-call-parser均用kimi_k3，结合auto-tool-choice，不能只换reasoning parser。

## 拓扑与混合缓存

TP须整除attention-head数，同时改变KDA state与专家placement。来源PP4在950分区24,24,24,21，在A3为25,25,24,19，必须按真实checkpoint隐层和版本核对，不通用套某表。PP worker rank、DP rank和lookup IPC id含义不同，headless只在worker节点且全组master参数一致。

长context建议DCP与平台相关，basic模板DCP1不代表开到1M仍满足容量。混合部署的1M参考至少八节点；PD的1M参考沿用基本八节点拓扑，仅按角色调整总长度和D侧DCP。prompt+output一起计；hybrid全部state组可达后才能prefix hit，不能仅MLA缓存就绪即复用。保留DSpark状态和KDA回滚的独立检查。

## 验证顺序

先text/image单请求与state，再PP/DCP/投机/池化逐项组合，监测各rank加载、网络、cache格式和输出。协议或scale变化换namespace，部分加载/状态不完整时保持服务停止并回完整已知配置。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## MTP注册入口与教程部署分开

KimiK3MTPModel另有[专用MTP接入契约](../integration/vllm_ascend_kimi_mtp_adaptation.md)，包含替换decoder容器、禁block residual、权重完整性和本地EPLB注册。存在该代码不把本卡DSpark部署参考自动扩为同平台MTP可用；继续按具体Runner、状态与数值验收。


## DSpark草稿实现不能套MTP或Qwen合同

进入[Kimi K3 MLA DSpark专属适配](../integration/vllm_ascend_kimi_dspark_adaptation.md)核对raw-prefix-sum辅助流、tap+1边界、可配置causal、逐层NoPE/RoPE cache视图、checkpoint自有head与PP本地embedding。该草稿类继承的恒等映射和本地未建立confidence head，不能据native/Qwen实现或本卡部署平台推导任意缩表/adaptive均可用。图/词表/预算还需按[DSpark块合同](../integration/vllm_ascend_dspark_block_markov_contract.md)与实际Runner逐项验收。


## 当前全文、权重和版本

本节完整对照Main ceac提交的Kimi-K3.md英文2389行与PO202条；发布配置只覆盖已验证子集，不代表所有优化都可调或已在本仓运行。A2能力仍按来源0.23基线保留，不能把Main pin0.32或Native5df快照当成A2已升级的实测栈。模型总表、通用PP组合表和专属教程的支持声明仍分别核对。

目标Eco-Tech/Kimi-K3-w4a8需完整config、tokenizer、image processor和权重文件。A3草稿为Eco-Tech/Kimi-K3-DSpark-MLA-NPU，950为Inferact/Kimi-K3-DSpark-Block5；旧RadixArk GQA草稿不替代这两个资源。相同本地目录名不证明同checkpoint，所有节点实际挂载路径、版本/分片哈希和target/draft配置分别记录；未下载外部权重。

## 混合部署：global DP与每引擎预算

| 平台 | 主机、设备与拓扑 | 默认总长度、seq、batch | 功能与运行条件 |
| --- | --- | --- | --- |
| 950DT | 四主机，各8设备；DP4/TP8/EP32，local DP1 | 131072、16、24576；memory .9 | DSpark K7、draft TP8/greedy/eager；APC、FULL_DECODE_ONLY、CPU binding与FlashComm1，HCCL buffer800，expansion unset |
| A3 | 四主机，各64GB×16逻辑设备；DP4/TP16/EP64，local1 | 131072、16、8192；memory .9 | DSpark K7、draft TP16/greedy/eager；其余上述MM服务字段相同，buffer800、expansion unset/AICPU；来源要求unset LD_PRELOAD |
| A2 | 八主机，各64GB×8；DP8/TP8/EP64，local1 | 262144；本段未显式seq/batch，memory .90 | language-model-only、BF16、APC、FULL_DECODE_ONLY且capture sizes1/2/4/8；CPU binding/npugraph开、static与FlashComm1关；buffer256、HCCL_INTRA_ROCE_ENABLE1，不设AIV；无本例DSpark配置 |

950/A3混合1M至少八主机、DP8、maxlen1048576，worker start-rank1–7；950 batch24576改8192，A3维持8192。只改maxlen不能补齐节点、KV容量或输出预算，也不能用这些MM例扩A2图像支持。950/A3 mixed使用MM cache0、data encoder、vision_chunk上限2、四项kimi_k3 tokenizer/tool/reasoning/auto-choice；allowed-local-media-path为来源的根目录示例，应按实际服务数据路径配置。

950/A3 API节点省略start-rank、远端headless显式1–3。A2命令仍API显式start0/local1并让其他节点headless，而验收文案要求internal LB；已读Native EngineArgs选段会在非headless、local已设且start非None时推hybrid，local1又转external。因此显式0与省略不等价；这是源码快照与0.23配方的待核对差异，不假称旧build已运行失败。A2的X-data-parallel-rank只在Node0 API上做0–7的定向验证，正常流量按所选有效LB模式分发，不直接访问headless节点。

## 普通PD与1M：四P主机只承载一个PP引擎

| 平台/角色 | DP / TP / PP | 分层或DCP | basic batch / seq / memory |
| --- | --- | --- | --- |
| 950 P | 1 / 8 / 4 | partition24,24,24,21；DCP默认1 | 16384 / 32 / .80 |
| 950 D | 4 / 8 / 1 | basic DCP1，1M用DCP8；block/interleave768 | 768 / 32 / .80 |
| A3 P | 1 / 16 / 4 | partition25,25,24,19；DCP默认1 | 8192 / 32 / .80 |
| A3 D | 4 / 16 / 1 | basic DCP1，1M用DCP16；block/interleave384 | 8192 / 32 / .80 |

普通PD总长262144，1M在相同八主机拓扑把两端maxlen设1048576并选D侧DCP8或16；DCP复用TP ranks，不增加物理worker。来源建议总输入输出超过65536时启DCP，但这不是所有后端统一的硬门槛。每请求输出必须预留在总context内；八主机950共64设备，A3共128逻辑设备，不能称四个独立P实例。

两端TP相等，connector内P DP1/PP4与D DP4均描述实际布局。950 Prefill只通过VLLM_PP_LAYER_PARTITION声明分层，A3还在两端connector prefill.pp_layer_partition写25,25,24,19；不补950省略项或direct默认值。两平台Model Runner V2与MooncakeConnectorV2、APC开、MMcache1/data encoder/skip profiling/vision_chunk2；skip profiling不证明MM请求正确或没有视觉内存。

DSpark两端使用同平台draft与K7/greedy，P保留主模型enforce-eager和draft eager=true，D主模型FULL_DECODE_ONLY但draft eager=false。P MegaMoE模式2/shared-expert DP、overlap=false，D recompute nested=true/MLAPO/overlap=true；最终有效配置仍按目标build核对。950 P/D均CCU_SCHED和buffer800；A3 P expansion unset/AICPU，D AIV，双方buffer1024。不能把GLM的P K1/D K5配方或旧K3 GQA草稿JSON直接搬来。 通用Mooncake教程还保留nonhybrid模型P K1的概括，本K3专属配置明确双方K7；不依据这句泛化改写模型配方，实际骨干/状态与版本另核对。

K3专属教程的PP4+DSpark与通用[PP接入表](../integration/vllm_ascend_pipeline_partitioning.md)所列模型范围不同，不能由任一表直接消除版本/组合差异；固定模型、Runner、target辅助状态与真实输出后再验收，未新增真机verified。

## Launcher、PP rank与端点

K3通过Mooncake工作流引用通用external_online_dp/launch_online_dp.py：它按local索引生成本机设备与HTTP port，第三参数来自dp-size，第四来自start+i，第五/六来自master/RPC，第七TP。P dp-size1/local1且第四参数0–3实际被模板作为PP node-rank；D dp-size4/local1第四参数才是DP rank。不能套另一指南会检查start<dp-size的不同内嵌launcher，也不能仅凭文件同名认定实现相同。

所有P节点显式传同一master IP和master port（来源举41000）；只有node-rank0提供API，P1–P3须手工在模板增加headless，并让VLLM_HOST_IP指本机。每个D节点一个API，proxy只注册真实API；本页通过通用工作流配置proxy，没有给完整固定端口映射，需按实际选值核对。generic launcher只有类型/必选检查，parent join不汇总child exitcode；cwd下的run_dp_template.sh、显式RPC字符串和节点就绪须另外检查。

## MemCache：服务内存、lookup标识和传输分别验收

池化保持P DP1PP4与D DP4、equal TP8/16，在两端MultiConnector里组合MooncakeV2与AscendStoreConnector。所列Store只显式backend=memcache与lookup_rpc_port，没有明确use_layerwise；Mooncake也没有显式direct，不能从GLM或旧教程补默认。基本pool仍256K/DCP1，来源另建议长context按5.3调整DCP和长度并保留池配置；组合正确性与真实性能还需目标后端/版本证明。

先MetaService，再每节点独立MemCache进程init(0)返回0并持续运行，全部节点打印初始化成功后再启动vLLM。配置MetaService5000、config store6000、可选metrics8000，metrics不得与同host API/proxy端口冲突。MMC_META_CONFIG_PATH指meta文件，standalone与vLLM的MMC_LOCAL_CONFIG_PATH指各自local文件；连接器参数不会起这些服务。

vLLM local配置dram.size=0GB，standalone示例600GB只有实际扫描每节点可用至少600GB才作为待核验输入；是一节点一个贡献内存进程，不是每NPU或每vLLM进程600GB。world_size256为LocalService上限，max.dram1024GB也不是已分配；共享device_sdma文案注明典型A3 intra-SuperPod，不能据双平台标题单独证明950网络兼容。

P四PP stages均为DP0/lookup0；D DP rank0–3映射lookup4–7，标识是本地IPC名字而不是TCP端口。Meta/standalone初始化、APC命中、P→D传输与远程pool load分别取证；复用前核对所有KDA/MLA state及namespace，只有HTTP200或本地prefix hit不能证明池可用。

## MLA草稿适配的实现入口

完整查看的kimi_k3_dspark.py 416行与[专用适配卡](../integration/vllm_ascend_kimi_dspark_adaptation.md)一致：draft disable_mlapo不等于D target MLAPO关闭；raw-prefix-sum要求tap+1边界和hidden宽度匹配，PP group>1需本地checkpoint embedding，自有LM-head的shape/唯一性/ownership独立于target共享。placeholder先mask到0再合并target预计算视觉特征，不建第二套vision tower。未从教程平台声明将该实现卡的draft/空平台升级。

注册回调将K3DSparkModel映射到AscendK3DSparkForCausalLM，文本KimiK3ForCausalLM只是KimiLinear的兼容别称，MM与MTP另有注册；定义存在不等于实际checkpoint选择了它。Main补丁仅对k3_dspark替换特定DeepseekV2Config架构validator，不能跳过全部配置检查。DSpark DCP临时guard复制target parallel config并仅在原post_init期间把DCP设1，finally恢复原引用，不证明运行时DCP被禁用或任意组合已正确。EP开启、非MoE且runner_type=draft时包装的verify_with_parallel_config实际直接return，绕过该次整个原方法，不只是删除一条EP断言；target与MoE draft仍按其他分支，剩余校验必须继续按完整初始化链核对。

这些仅是选段Host适配入口，配套Native类、target捕获、cache writer、alignment和Runner全链路仍不能由阅读或CPU断言替代；更完整的块/词表/Markov限制见[DSpark接入合同](../integration/vllm_ascend_dspark_block_markov_contract.md)。

## 结果、评测与中文来源边界

来源表GPQA92.42/OCRBench0.88标八A3，GPQA93.5/OCRBench0.891标一950DT；后者与权重/部署的四或八节点叙述没有在页内闭合成同一运行记录。原样保留来源及指标单位，不据此新增单950部署方案、不改成OCRBench百分制，也不是本次结果。比较必须固定checkpoint/tokenizer/chat template、采样、dataset和evaluator。

bench示例八请求/并发八、custom dataset、output1024、temperature0/seed0/ignore-eos、无shuffle、request-rate inf、保存结果；input128K取决于实际数据与tokenizer，命令没有强制input128K的参数。若输入实际为131072再加1024，已超过mixed默认总长131072；先核对部署总长与实际token预算，不把“128K/1K”名称当已验证容量或吞吐。图像请求只适用于来源950/A3例，video不支持，A2保持text-only。

PO202条有136连续msgid匹配、66条人工差异，其中10条删除表头/tab/预算行仅用当前上下文定位，不伪称一对一替换。18条硬件拼写、7处pool章节重编号、旧target/draft表、P PP4/DP语义、通信模式、D recompute及lookup变化分别裁决；PO140/173表头仍英文。精确匹配也不证明旧A2 LB、图、内存、全部实现或zh-cn/latest HTML一致。本节没有执行上游导入/脚本、下载模型、安装服务或修改主机，也未运行NPU、质量/性能/Agent A/B。
