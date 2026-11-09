---
type: Guide
title: vLLM Ascend Qwen3 基线：Dense/MoE 与 310P 量化分支
description: 区分Qwen3 Dense和30B-A3B的层级量化、EP和专用310P权重，核对物理NPU与die单位，避免把旧模板的投机说明当原生支持。
  补充 Qwen3 Dense、MoE、W8A8SC、QuaRot 的310P权重身份与TP起点。 补清Qwen3 Dense部署预算、MoE DUO并发与图参数冲突、严格JSON字段和A3精度评测归属。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-Dense.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-30B-A3B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Dense.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-30B-A3B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/config_utils.py
  role: constraint
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T17:27:31Z'
platforms:
- a2
- a3
- 310p
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Qwen3 基线：Dense/MoE 与 310P 量化分支

## 模型和平台

Dense 0.6/1.7/4/8/14/32B与30B-A3B MoE分别固定权重。A2/A3 BF16及W8A8/W4A4与310P FP16/W8A8SC或QuaRot310权重不同，不能强用标准量化override。文档声称某版本以后稳定只是来源概述，仍以当前维护表和实际build为准。

## 逐层格式与并行

30B W8A8是混合策略：embedding/norm/router高精度、Attention静态scale、专家dynamic activation。加载后查实际scheme，不能全层设统一static W8A8。Dense不启EP，MoE按TP/EP拓扑验证。310P Dense32B有TP4参考、30B QuaRot有TP2参考，不从总参数推单卡可装。

A3双die，一个物理NPU可映射两个logical devices，TP rank按实际可见chip计；不能把TP4必然写4张物理卡。来源吞吐表也有TP1/物理卡描述不一致，保存真实device list与rank映射。

## 投机与缓存

30B教程列Eagle3 draft，又有通用MTP说明；先核target/draft architecture、当前spec config resolver，未有匹配权重不宣称原生MTP。prefix默认关闭/未充分表征与总表支持不矛盾为同一收益保证，按实际复用率A/B。长context YaRN需与checkpoint/精度共同验证，不只增max-model-len。

## 验收

先原精度eager、小batch、加载全层，再量化、图、EP、draft。310P三方依赖和BF16限制按硬件处理，环境包移除只在专用部署中按版本执行。本次不改本机Python环境。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## Qwen3 Dense、MoE 的 W8A8SC 与 QuaRot 权重身份

此前选读阶段仅新增核对 Qwen3-Dense.md 的1–49行和 Qwen3-30B-A3B.md 的1–64行；下面新补充的全文对照另列，不扩大此前证据范围。Dense的8B/14B/32B使用各自W8A8SC-310 checkpoint，表中起点分别TP1、TP1、TP4；30B-A3B MoE另有 Qwen3-30B-A3B-w8a8-QuaRot-310，起点TP2。这些是不同权重身份和来源配置，不是同一通用量化flag，也不能从表格起点推所有负载容量。

旧源30B W8A8仍保留embedding、Q/K norm、router为BF16，attention静态per-tensor scales与专家dynamic input scales分开；MoE的30.5B总参数/3.3B激活不把存储预算缩成3.3B。实际loader、量化描述、分片和硬件能力仍按前文验收，未下载或运行这些checkpoint。此前选读阶段未读取对应两份PO全文，当时不增加中文处理数量；下面新补充的完整对照另列。


## 两份中英文教程全文：版本、权重与部署入口

以下新增对照固定快照的 Qwen3-Dense.md 全文605行、Qwen3-30B-A3B.md全文631行，以及 Qwen3-Dense.po 104条和 Qwen3-30B-A3B.po 118条业务译文；222条msgid都可在对应英文定位。匹配不证明代码块、译文技术结论或发布站点HTML正确。另核对AscendCompilationConfig及其字段区域的明确选段和config_utils.py全文，没有运行这些源码。

Dense教程自述按v0.21.0验证，MoE按v0.22.1rc验证；首次支持、后续所有版本稳定的文案都不能替代当前实际build兼容性。镜像中的版本模板、源码安装未锁定的分支和pip show输出也不能补齐这层证据。A3示例映射davinci0–15，说明8物理NPU/16chip；按实际可见chip配置TP。DUO Docker命名vllm-ascend，而安装检查查找vllm-ascend-env，也须核对真实容器名。

### Dense：量化、上下文和图配置是一组配方

BF16覆盖0.6B/1.7B/4B/8B/14B/32B；表中的整节点硬件建议不等于每种模型最低卡数。A2/A3的vllm-ascend/Qwen3-32B-W8A8、vllm-ascend/Qwen3-32B-W4A4与DUO的Eco-Tech W8A8SC-310分片分别核对，不把一个quantization ascend参数当权重转换或任意格式互换。

| Dense配方 | TP与上下文/token budget | 并发及图/加载边界 |
| --- | --- | --- |
| A2/A3 32B W8A8基础例 | TP4，max-model-len5500，max-num-batched-tokens40960 | FULL_DECODE_ONLY，mp；不能从batch token budget推单请求上下文 |
| A2/A3 32B W4A4基础例 | TP2，context40960，batch16384 | seq64、capture_sizes=[64]、fuse_norm_quant=false；该命令未显式给cudagraph_mode，不补造其默认值 |
| DUO 8B W8A8SC | TP1，context20480 | seq32、capture=[1,2,4,8,16,32] |
| DUO 14B W8A8SC | TP1，context20480 | seq16、capture=[1,2,4,8,16] |
| DUO 32B W8A8SC | TP4，context20480 | seq32、capture=[16,32]；不能假设已覆盖所有小batch捕获 |

三个DUO命令分别指向各checkpoint的TP1/TP4子目录，均为dtype float16、load-format sharded_state、关闭prefix caching、enable_npugraph_ex=false与FULL_DECODE_ONLY；目录分片、TP和可见设备一起核对。容器例映射8080端口，服务却bind 127.0.0.1，外部可达性须按实际容器网络验证，不能把-p映射当host侧已连通。源码安装文中的包卸载只描述该版本DUO部署条件，不在知识生产环境执行。

Dense高吞吐TP4例为context5500、batch40960、block128、weight_prefetch_config与pa_shape_list32–256及特定capture列表；低延迟TP8例另加Eagle3三token且draft enforce_eager=true。长上下文TP4例context135000，YaRN factor4、original_max_position_embeddings131072、rope_theta1000000，另有Eagle3三token。三者是独立场景，不按表格标题拼成一条通用最优命令；表中Async Scheduling On也不证明每条命令都显式开启相同配置。没有与target匹配的draft与位置编码验证，不补造长上下文或投机支持。

### MoE：EP、DUO并发与图参数冲突保留

Qwen3-30B-A3B的30.5B总参/3.3B激活及层级混合W8A8沿用前文；A2/A3的Eco-Tech/Qwen3-30B-A3B-w8a8、DUO的Eco-Tech/Qwen3-30B-A3B-w8a8-QuaRot-310和AngelSlim/Qwen3-a3B_eagle3各有身份。BF16应移除量化参数，不能将Attention静态量化扩展为专家动态输入scale也全静态。

MoE文案说EP required，但高吞吐TP1例和表中EP Off、DUO TP2例未启EP；低延迟与长上下文TP4才显式启EP。这里记录不同分支，不把文案转为所有拓扑强制EP，也不因TP1例就断言多卡无需专家分布。A3低延迟TP4表示4chip/2物理NPU；高吞吐表给1A3/2A2而命令只可见device0，数量单位和实际rank分配需现场核对。

DUO容器片段只映射davinci0，服务却可见0,1并设TP2；命令seq32、capture=[1,32]，说明则写seq16、capture=[1,2,4,8,16]。context16384、FP16、关闭prefix caching是该配方的内存边界，不自动改成某组参数声称已验证。MTP一token只是教程附注；主要实例使用Eagle3三token且需要独立draft，不能据此宣布该target具备原生MTP。

MoE A2/A3基础例为TP4/EP、seq100、context40960、batch16384、gpu-memory-utilization0.95、weight_nz_mode2、HCCL_BUFFSIZE1024；低延迟改context37364，高吞吐TP1/不启EP，长上下文TP4/EP改context131072、seq14、YaRN factor4/original32768。HCCL AIV注释对A2另作说明，不能把一组环境变量推广成各硬件通用要求。

### JSON字段拼写与实际配置校验

DUO MoE命令写enable_npu_graph_ex，而此固定源码的AscendCompilationConfig声明enable_npugraph_ex，Dense命令也使用后者。该类使用裸@config，其helper默认ConfigDict(extra="forbid")；其他调用者可显式覆盖配置，但此处没有这样的参数。若该字典原样交给此dataclass验证，错拼键不在声明字段中。这里仅从字段和decorator推导条件性不兼容，没有执行完整配置初始化来宣称某次部署已报错。

CLI的served_model_name、distributed_executor_backend下划线写法应按部署版本的解析器核对；选项名归一不负责把JSON中的npu_graph改成npugraph。该配置类还按硬件profile降级npugraph_ex/static_kernel/super_kernel并检查依赖；显式传true不保证该硬件最终开启。对照[适配预检](../bringup/vllm_ascend_new_model_onboarding.md)，记录用户输入、实际字段与生效配置后，再讨论图性能。

## Qwen3评测：模型身份、长度预算与指标归属

两个教程API别名均qwen3，但服务端口、客户端配置和模型目录仍要逐一对应。Dense精度示例为AIME2025、host_port2001、max_out_len32768、batch32并提取非reasoning内容；性能例另用GSM8K、stream=True、request_rate=0、use_timestamp=False、port8004、max_out_len1500、batch90、temperature0、ignore_eos=True、360请求。不能把这些配置与context5500或DUO20480的服务直接拼接，先核对最终请求token预算和实际输入加输出长度。

MoE给出来源自报的A3/W8A8/v0.22.1rc精度表：GSM8K 4-shot CoT accuracy92.87%、GPQA-Diamond 0-shot CoT accuracy60.10%、LiveCodeBench 0-shot pass@1 60.05%、AIME2024 0-shot accuracy76.67%。这些指标、shot与版本不互换，不归给Dense、310P或本仓新模型复测；也不是性能吞吐值。MoE精度max_out_len32768和DUO context16384须分别核预算。

MoE性能例用stream、batch32、temperature0.01、ignore_eos及合成Type=string、RequestCount200、输入3500/输出1500；真实token长度仍须观测。随机输入样例用于冷前缀负载，不能拿它测真实prefix复用收益。vLLM bench例则input200/output2048、200请求、rate1，Dense例没有显式random-output-len；这些与AISBench配置属于不同负载，不能并表比较。长上下文tip的131072输入再加1024输出也须确认长度单位和最终token总和，不能直接声称适配context131072。

AISBench教程对--models与文件名/abbr的表述不一致，示例文件下划线名与abbr连字符名也不同；未核对当前AISBench解析实现前，不将某种解释硬编码为通用规则。保留实际选择器、加载配置、服务model/端口、token长度、输出后处理及失败产物，配合[性能基准指南](../optimization/vllm_ascend_benchmark_workflow.md)再比较SLO。本次没有执行任何上游CLI、卸载依赖、下载权重或开展NPU/评测/Agent A/B。
