---
type: Guide
title: vLLM Ascend 投机解码：方法、Runner、验证器与动态 K 选型（含 MTP 概率恢复）
description: "按模型、草稿架构和 MRv1/MRv2 区分 MTP/EAGLE/DFlash2/DSpark，拆开分布保持验证、近似接受和合成基准，按净时延验证收益。补充Suffix固定名义K/逐请求草稿、CPU缓存接线与A2来源SLO口径。 对照孤儿 MTP 译文区分点质量恢复、指数噪声，以及 draft、recovered、bonus 三种 token。 细化 MTP 的 PyTorch 函数、bonus_logits_indices、IS_NGRAM 与 draft_probs 为 None、理想 0.2/0.3/0.5 分布及 2/7、5/7 点质量恢复；区分 standard、entropy、synthetic、block 和 Triton/MRv2 未读片段。保留 FIA 的 15 与 K+1、fullgraph、disable_padded_drafter_batch、False/JSON 旧例，以及 DeepSeek V3 旧维护和单层权重的 K>1、K>=3 边界。 补充 draft_window_size 的草稿侧边界、实际 Runner 选择与接受长度术语，保留采集和采样质量约束。 解释原生 sliding_window 与 SWA、env 覆盖及默认 V2 排除表；说明 extract_hidden_states 的 K1（K=1）、单个输出 token，以及 ExampleHiddenStatesConnector、kv_producer、safetensors 采集与 B H N C、hidden_size 布局、/dev/shm 客户端清理，区分近似 posterior_threshold、posterior_alpha 和 fp64、fp32、tl.rand、seed 的质量边界。 后续发布5f5e25的DFlash2 MRv2已允许draft FULL_DECODE_ONLY图；旧eager强制条件保持版本限定。"
tags:
- task.optimization
- topic.speculative_decoding
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/5fa10c3799e249627112ead02c8414988d85ddcc/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/dspark_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Kimi-K3.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/suffix_speculative_decoding.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/suffix_speculative_decoding.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/suffix_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/Multi_Token_Prediction.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/sample/rejection_sampler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/speculative_decoding.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/mrv2_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/draft_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/eagle_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/ngram_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/ngram_proposer_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/medusa_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: supporting
created_at: '2026-10-29T09:49:02Z'
updated_at: '2026-11-04T03:05:17Z'
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
- 投机
- 投机解码
- Speculative Decoding
- extract_hidden_states
---

# vLLM Ascend 投机解码：方法、Runner、验证器与动态 K 选型（含 MTP 概率恢复）

方法选择同时绑定版本：7d9e有RecoverSSM PCP producer准入变化，见[7d9e运行时差异](../integration/vllm_ascend_7d9e_runtime_delta_contract.md)的RecoverSSM节；本卡其他旧版本方法限制和验证边界仍各自成立，不因一条新路线扩展所有硬件/拓扑组合。

## 起点与通用契约

仅在目标模型/硬件/backend有对应实现时启用，先固定无投机基线。speculative_config 指定 method、K及必要draft模型；使用单次decode query最多16 token的FIA路径时，Q=K+1的方法需K+1<=16；这不是所有backend/状态统一上限。DSpark按anchor协议可取Q=K或K+1，full capture容量须按该方法实际batch×Q核对。来源旧式“倍数加速”概述不替代实际draft/verify/通信成本。

PD下hybrid Mamba（Qwen-Next/3.5）P/D K要相同；通用参考中的其他模型建议P K=1、D K>=1，但Kimi DSpark等专属教程另要求双端匹配，必须按实际模型/方法裁决。draft TP通用可取1或target TP，但EAGLE专门路径要求draft TP1。不把CANN Executor的next_n/registry接口套到vLLM。

## 方法判断

ngram/suffix依赖重复模式，suffix需Arctic并已按请求动态，不能再机械叠batch动态K。MTP复用模型结构，DeepSeek单层暴露权重对K>1尤其>=3不保证质量/收益。EAGLE3需匹配draft及hidden-state接口。extract_hidden_states只收集指定层训练数据、每请求仅1输出token，K=1、ExampleHiddenStatesConnector producer，不是加速模式。

DFlash2仍使用method=dflash，由DFlash2DraftModel架构识别；候选lattice依赖target完整未量化LM-head，不支持缩小draft词表。ceac/3164文档中MRv1仅greedy，MRv2支持probabilistic但draft必须enforce_eager=true，target可保留图；后续5f5e25的图迁移见文末。不能将draft eager当成整服务eager。

DSpark confidence-head adaptive verification只MRv2，不支持target fully eager或纯PIECEWISE，也不能PP/PCP/DCP/LM-head TP/LoRA；模型许可约束按来源和checkpoint核对。低延迟、host瓶颈或高接受率时可能无收益。

## 三类“动态”和两种 block 必须区分

MRv1 additional_config.dynamic_spec_config 是探索性confidence预算；文档只承诺DSpark Qwen，仓内DSV4动态测试候选不构成已执行或Runner可达的证明，DFlash用softmax max proxy；不是MRv2 adaptive开关。batch-size动态K用speculative_config.num_speculative_tokens_per_batch_size的[start,end,K]区间，支持方法有限，DSpark、MTP+DCP+DSD不支持，K=0表示该区间不draft。区间须按实际schema验证，不原样照抄文档中K大于名义K的示例。

MRv2 rejection_sample_method=block沿上游累计target/draft比率与残差恢复分布，temperature=0保持greedy；不能与synthetic参数混用。MRv1 additional_config.rejection_sampler_config 的block/entropy是改变接受阈值的近似方案，可能损精度，需独立质量验收，不能宣称同一分布保证。

synthetic按人为rates接受，与target/draft匹配无关，只做基准。rates长度K、[0,1]单调不增，与synthetic_acceptance_length二选一；生成不具业务语义。MRv1/MRv2随机数路径不同，不以相同seed要求跨实现bitwise相同。

## 验证与停止条件

先greedy对齐token及KV/接受状态，再按选定验证器验证采样/质量，覆盖零/部分/全接受、EOS、拒绝回滚、抢占、混batch及并发变化。分别记录draft、target verify、sample、接受长度、端到端TPOT/吞吐及新增显存，接受率高不必然净加速。关闭speculation恢复基线；近似/合成结果不得写成正确性证明。本次未运行投机实验。


## 进入实际模型与加载接口

MTP模型接入后先分别检查[LM-head真实归属](../../runbooks/precision/vllm_ascend_mtp_head_ownership.md)与[logits/递归状态和最终norm](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)；模块存在、Tensor注解或预测层数都不能替代实际加载/返回协议。Kimi专用继承和EPLB见[Kimi MTP接入](../integration/vllm_ascend_kimi_mtp_adaptation.md)。

DSpark的[同checkpoint量化继承](../../runbooks/runtime/vllm_ascend_dspark_draft_quant_loading.md)、[QuaRot与PP词表副本](../integration/vllm_ascend_draft_quarot_alignment.md)、[GLM MLA骨干/Context KV](../integration/vllm_ascend_glm_mla_dspark_adapter.md)分别解决加载、basis和模型协议；这些静态草稿卡均未扩大本指南的运行支持范围。


## GLM实验性递归状态恢复的专用交集

后续Ascend文档`5fa10c3799e249627112ead02c8414988d85ddcc`新增[GLM KDA RecoverSSM](vllm_ascend_glm_kda_recoverssm.md)：GLM-5.3-Flash、A3/A5、MRv2，使用--use-replayssm，默认关闭。需要投机、APC关闭、mamba_cache_mode=none、禁随机舍入、PP/PCP/DCP均1；PD仅文档列出的V2/Pull且双端窗口与状态协议一致。这是比通用MTP或hybrid PD说明更窄的交集，不扩到本指南全部平台/模型。浮点差异可改变token，需独立质量和净时延验收；不要借上游Mamba2开关说明推导Ascend GLM的支持范围。


## DSpark的实际块和预算接口

DSpark的[块与Markov协议](../integration/vllm_ascend_dspark_block_markov_contract.md)区分每请求Q=K或K+1，并把映射后的target token反馈到下一位置；[词表概率空间诊断](../../runbooks/precision/vllm_ascend_dspark_vocab_probability_space.md)说明MRv1缩表greedy回退与MRv2 target轴scatter，不能仅凭forward通就宣称probabilistic适配完成。[MRv1动态预算](vllm_ascend_dynamic_verify_budget.md)按全batch survival分配前缀，并有Host同步成本；它不是MRv2 adaptive或少跑draft位置。Kimi的[专属MLA草稿接口](../integration/vllm_ascend_kimi_dspark_adaptation.md)与普通Qwen/GLM不同，不能由父类或测试候选泛化head支持。


## Suffix的名义K、CPU状态与A2性能口径

[A2 Suffix配方](vllm_ascend_suffix_decoding_contract.md)以Qwen3-32B四卡、Arctic及K=3为窄范围；18行性能表的倒数时延增益和严格<50ms SLO边界分别保留，不能把表内TPS或接受率当此指南全部方法/平台的保证。[原生Suffix proposer](../../concepts/frameworks/vllm_ascend_suffix_proposer_contract.md)按请求返回变长草稿，但assert调用名义K等于构造K；这是与batch动态K不同的接口，近长度上限或partial prefill可以无草稿。

所读Ascend工厂将suffix接到薄适配并沿Runner传num_spec_tokens_to_schedule/valid_sampled_token_ids；CPU缓存、输入身份与目标验证分开。工厂Medusa仅v0.32 lane，DFlash2/Gemma4/多KV组MTP等另按架构分支，不能按方法名字互换提议状态或靠版本环境字符串保证外部ABI。该注册/调用关系是静态证据，本次未执行任一proposer或扩大原支持矩阵。


## 孤儿 MTP 译文：历史命名与概率恢复

Multi_Token_Prediction.po的34条业务译文完整读取，没有同名当前英文页。旧文以DeepSeek-V3为例，方法/参数/单层权重和图约束只能按历史版本解释；DeepSeek-V3当前维护边界见[历史模型指南](../models/vllm_ascend_retired_model_version_boundary.md)，不能借旧MTP功能入口恢复维护承诺。

旧例为method=mtp、num_speculative_tokens=1，并带disable_padded_drafter_batch=False；PO称不填K时可取draft配置或成为必填。字段、默认、padding与Attention后端支持必须按目标版本schema和实际Runner检查。字面量False不是标准JSON写法，本次未核对目标CLI是否有兼容解析，不据此宣称启动成功或失败，也不把缺失代码块补造成现行完整命令。

旧资料泛称“并行多个token、倍数加速且无质量损失”，还只列ngram/EAGLE/EAGLE3/MTP。当前本卡已有Suffix、DFlash2、DSpark等特定接口，该旧列表不是当前白名单；净收益包含draft/验证/采样/通信，分布保持条件和近似/合成验证器也不能混用。“最多15”仅在相应FIA单query-token预算下推导；fullgraph按K+1整倍捕获的旧说法仍需具体Runner、方法和Q定义，不能扩到全部backend。DeepSeek单层MTP权重对K>1尤其>=3的旧质量/性能提醒也不是实测所有模型失败。

### P_draft=1只指候选token，不能对整个词表减1

旧PO将恢复分布写为Q=max(P_target-P_draft,0)，再因“不提供P_draft”简化成Q=max(P_target-1,0)。后一步若用于整个词表，所有合法概率<=1时会得到全零向量，无法正规化为恢复分布；不应被Agent当成实现公式。

本次仅补读固定Main sample/rejection_sampler.py所列调用和PyTorch函数片段。sample_recovered_tokens在draft_probs is None时给PyTorch helper传IS_NGRAM=True；这个标记按是否有概率决定，不能只从名字推成所有当前MTP都必走该分支。该helper先clone target_probs，只将该位置候选draft token的概率置0；有draft_probs则逐词表计算max(target_probs-draft_probs,0)。没有将整个target向量减标量1。

按确定性proposal的点质量解释，q(y)=1[y=x]：只在候选x处为1，其余为0；接受候选的比率使用p(x)/1，拒绝后的未归一化残差为max(p(y)-1[y=x],0)。例如p=[0.2,0.3,0.5]、候选x=1，残差=[0.2,0,0.5]，理想正规化为[2/7,0,5/7]；这是静态数学例，不是执行框架、随机数或NPU实验。一般概率draft还需其完整分布，不能用点质量代替。

源码helper注释将q称normalization factor，但已读调用处q来自exponential_()的每请求词表随机张量，随后用argmax(prob/q)取样；它是指数噪声，不能把这个q与proposal分布q(y)或概率归一化常数混为一谈。零/inf的局部处理也不证明所有输入有限、合法或所有随机路径跨版本等价。Triton、block和MRv2其余实现本次未读完，更没有正式Device VV/CV或全模型分布证明。

### Draft、recovered 与 bonus 是三个对象

所读forward从metadata.bonus_logits_indices提取target logits，单独经self.sampler取得bonus_token_ids，再构造target行的概率/约束。已读PyTorch random helper按首个拒绝位置输出recovered token并停止该请求后续draft；仅全接受时，在num_draft_per_batch位置添加传入的bonus。旧文把“第二个不确定的draft”泛叫bonus不适合作为新适配接口定义。

该random helper同时有standard、entropy和synthetic分支；synthetic按人为rates绕过target/draft比较，entropy修改阈值。所读父调用还拒绝synthetic与block同时启用，普通all-greedy可提前返回。这里记录的是具体静态调用/采样数据对象，不能据PyTorch片段推定Triton、不同temperature、词表映射或全部Runner的质量、种子和性能已验证。继续按前文覆盖首拒绝、部分/全接受、EOS、KV回滚、混batch和真实质量，保持原无投机基线。


### 已读 PyTorch 采样接口的精确名字

| 符号 | 所读作用与范围 |
| --- | --- |
| sample_recovered_tokens | 构造每请求词表指数噪声，按HAS_TRITON等条件派发；本次没有读完或执行Triton/kernel分支。 |
| sample_recovered_tokens_pytorch | 无draft概率时仅清候选坐标；有概率时做正残差，按指数噪声取argmax。它是本卡所说的PyTorch恢复helper。 |
| rejection_random_sample_pytorch | 用首拒绝位置截断后续draft，输出recovered；全接受才加bonus，并有standard/entropy/synthetic分支。 |
| bonus_logits_indices | 已读forward索引target的bonus行，单独经sampler生成bonus_token_ids。 |
| IS_NGRAM / draft_probs / None | wrapper按draft_probs是否为None设helper标记，不凭IS_NGRAM名字证明所有MTP都走此分支。 |

这里的理想概率示例也可分写为0.2、0.3、0.5；[2/7,0,5/7]只作归一化算术。K>1、K>=3、FIA预算和fullgraph是不同层次的旧/条件约束，不用已读PyTorch片段替代完整MRv2或NPU正确性。


## 当前投机解码页的完整双语对照

本节新增复读固定Main speculative_decoding.md全文1000行及speculative_decoding.po全部145条业务译文，145条msgid均定位到英文。它与前述孤儿Multi_Token_Prediction.po是不同材料；字符串匹配、文档列出方法或引用PR，都不证明各模型/硬件组合、Triton分支或发布站点HTML已经验证。本节不扩大原平台范围，具体新功能仍取模型、Runner、backend及硬件的交集。

### draft_window_size：只截草稿注意力的窗口

draft KV sliding window只限制drafter看到的最近上下文，target仍保留完整上下文。文档限定MRv1下的eagle3、dflash、dspark，MTP因复用target层而force-disabled；MRv2尚未支持这一路径。draft_window_size按文档使用正整数并在内部block对齐，512–4096是参考范围；关闭时省略或删除该键，不能把0当作不改变Runner的安全默认值。

已读mrv2_utils.py先使用上游解析后的环境覆盖；未覆盖时，只要additional_config.draft_window_size不为None，就进入V2排除表并选V1，条件不是大于零。显式V2优先不会把未支持的窗口变成已支持。文档窗口段称MRv1为default，后文却称V2默认；以[实际Runner选择](../../optimizations/rules/vllm_ascend_model_runner_selection.md)、生效配置与Worker日志裁决。不要在同一次性能对照中无记录地切换Runner。

窗口适合排查短上下文训练的draft在长对话中接受长度下降的场景；若draft自带native sliding_window，先核训练窗口，再比较大于等于训练窗口或关闭的配置。来源举早期GLM-5.2 DSpark在32k时约5降至约1、512–1024窗口恢复约4.7–5.5、吞吐最高+381%的个案，也给出1024窗口小于原生2048时平均接受下降4.5%的观察。这些不是本仓复测或全模型收益。

### 接受长度、接受率与质量分别留证

PO第107、108条把相关指标称为“接受率”，但引用的日志是SpecDecoding metrics: Mean acceptance length。约4.7–5.5应按接受长度语境核对，不按概率或百分率解释；同时记录名义K、实际草稿/验证长度、端到端时延、吞吐、显存和服务并发。target上下文未缩短也不足以单独证明质量不变，仍要区分standard分布保持条件与近似entropy、V1 block或synthetic方案。

三类动态仍分开：MRv1 confidence预算先运行草稿再缩verify前缀；MRv2 DSpark adaptive需要confidence head且限制target图模式和并行组合；batch区间共享K不适用于Suffix、DSpark及MTP+DCP+DSD列出的交集。EAGLE3示例名义K=3却含K=5/4区间，不能不经实际schema就作为可启动命令。MRv1窗口本身也没有在本页给出独立硬件表，不把本指南platforms枚举当该窗口已在每个平台验证。

### 采集模式与两种block不能互作质量证明

extract_hidden_states用于训练数据采集，单token草稿预算K1（K=1）、每请求1个输出 token、ExampleHiddenStatesConnector/kv_producer与每请求.safetensors文件分别核对；K1只是此处的预算简称，不是新增API选项。示例层号[2,18,34]须按实际checkpoint层数校验；文件中(num_tokens,num_layers,hidden_size)不等于底层私有[B,H,N,C]缓存布局。使用/dev/shm也仍由客户端承担文件生命周期，不能推定自动清理。文档提到的V2私有缓存和PR/0828 pin只作来源线索，本批未复核这些外部提交。

MRv2 speculative_config.rejection_sample_method=block与MRv1 additional_config.rejection_sampler_config的block/entropy是不同路径。前者按目标/草稿概率及恢复分布讨论分布保持，temperature=0仍为greedy；后者posterior_threshold0.95、posterior_alpha0.4修改接受标准，需独立质量验收。synthetic只作受控接受率基准，不作业务语义输出；V1外部fp64随机数转fp32与V2核内fp32 tl.rand的边界，不提供跨Runner同seed逐位一致保证。这里仅完成文档和Runner控制面阅读，未执行任何proposer、采样kernel、模型或Agent A/B。


## 2026-11-03 main 增量：LiLiCorr 与 MRv2 Entropy Verify

本节固定3164adc8fe75892fbf7f99f524bb72fddf1e6efd的speculative_decoding.md变更hunk，不代表该1135行新版本已全文重读、旧ceac实现自动升级或网站HTML完全等价。前文“entropy只属于MRv1”的裁决限于原版本；新文档声明MRv2也支持Entropy Verify，使用additional_config.rejection_sampler_config.enable_entropy_verify=true，并选择rejection_sample_method=standard，不能与上游block合用。旧MRv1 Block Verify与上游MRv2 block仍是不同算法。

MRv2新路径基于采样参数处理后的target logits，对每个draft位置算min(exp(-entropy*posterior_alpha),posterior_threshold)；raw/processed logprobs模式都按此输入阶段解释。greedy保持原行为，synthetic仍用人为rates。阈值放宽可能改变输出分布，接受长度变高不证明质量保持；alpha=0使阈值成为posterior_threshold，默认0.95并不等于恢复标准拒绝器。实现入口与额外词表扫描开销见[MRv2拒绝合同](../integration/vllm_ascend_mrv2_rejection_resampling_contract.md)的版本增量。

新文档的LiLiCorr使用专门训练的LiLiCorrDraftModel checkpoint，普通DFlash/DFlash2权重不能互换；名义K通常为训练block size减1，可缩短到1但需测接受长度，不能增加到训练长度以外。MRv2与嵌套draft enforce_eager=true同时要求，target保留自身模式；普通TP与fine-grained embedding/LM-head TP、PCP词表分片分别裁决。候选top-k与卷积几何来自训练配置，不能当普通服务调参。

LiLiCorr的greedy/probabilistic都消费correlator条件分数，随机draft需把真实proposal交拒绝器，并与target使用独立随机流。ModelOpt NVFP4能被上游loader识别不证明格式可在Ascend执行。文档的Qwen3.8-27B、TP2、K7 real-weight CI只是测试定义/指定checkpoint，不是本次执行结果；按相同target模式、TP、cache与负载比较无投机/两种draft方式的质量、延迟、吞吐及接受长度。实际Ascend guard见[DFlash运行接入](../integration/vllm_ascend_dflash_runner_graph_contract.md)。

同一文档新增950DT、MRv2、GLM DSA target与Qwen3DSpark GQA draft的device-length FlashAttn路径，要求FP16/BF16 query与未量化draft KV。只有全部draft层选择该backend时才可跳过相应CPU长度同步；PP/PCP/DCP、KV传输、sparse offload、adaptive verification保留原同步。head192补零至256、保持原scale并裁回输出，KV物理页增加三分之一容量，不能把少一次同步直接当净加速或接受率提高。具体backend仍按[Draft FlashAttn](../integration/vllm_ascend_cann_flash_draft_backend.md)核对。


## ceac MRv1 适配器：类名、空方法与实际调用分开

本节回到原Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整读取MRv1的draft17、eagle12、CPU ngram60、NPU ngram35及Medusa72行，复读同版本方法工厂全文；Runner只核2021–2090，Ascend base只核175–205。没有闭合Native proposer、完整Runner或n-gram Device算法，也未运行模型/UT。它与上一节3164新增LiLiCorr/MRv2 entropy不是同版本入口。

CPU AscendNgramProposer无模型加载或dummy forward，propose要求scheduled K<=构造self.k、存在num_tokens_no_spec与token_ids_cpu；跳过本步没有有效输出或已达max_model_len的请求，再以原batch大小、有效请求索引、真实token历史与K调用batch_propose。它不需要草稿权重，但仍需要正确请求映射及调度长度，不能以load_model为空推提议无需输入状态。

AscendNgramProposerNPU.propose虽为pass，实际MRv1 Runner对这个类型直接调用triton_ngram_spec_decode，而不是调用空方法。Runner使用token history、num_tokens_no_spec、discard mask及min_n/max_n/k，取回next/draft IDs、有效draft数和sampled数，再安排CPU计数复制。因此类内stub不能单独证明ngram_gpu不可用，工厂返回类也不能单独证明kernel/异步scheduler已可用；需要核对真正consumer。该Runner片段每步先清_draft_probs和请求ID缓存，避免没有新proposal时消费旧概率。

draft_model构造直接进入AscendSpecDecodeBaseProposer并传pass_hidden_states_to_model=False，再显式调用词表/draft TP一致检查方法；Eagle传True。这个布尔参数的签名表示是否把hidden states交模型，不是仅凭类名或变量use_eagle推导全部模型协议。Ascend base还立即使用runner buffer/并行字段，构造形参runner=None不证明它可脱离真实Runner独立初始化；这里未闭合所有检查方法和父类版本。

Medusa只在vllm_version_is(0.32.0)的lane导入/创建，其他版本工厂显式ValueError；本地文件存在不能恢复被上游移除的能力。其propose在hidden rows已等于请求数时直接使用，否则按每请求累计(num_draft_tokens+1)起点，加本次valid sampled长度减1取最后有效hidden，再交Native parent与scheduled K。这里的长度包含实际有效输出，不机械等于接受draft数；空有效输出、请求重排与metadata一致性需要caller保证，不能用shape注解替代。dummy_run使用最大token容量的hidden tensor，在draft forward context中执行模型/可选logits；参数列表保留图字段不表示所有capture模式已验收。

同名方法在MRv1/MRv2、Native/Ascend和不同版本可能只是注册标识，不代表相同forward、KV、proposal或RNG合同。Agent先保存最终工厂类、实际Runner分支、请求坐标、scheduled/名义K及真实proposal，再进入本卡原有质量与性能验收；这些静态适配器没有新增硬件或方法支持保证。

## 2026-11-03 发布快照：DFlash2 draft 图与原生滑窗

本节固定 `5f5e25dd94db85b59251be7d3baf7c808475b6d7`，对应本次中文发布页的实际命令和正文。前文 ceac/3164 的“MRv2 draft 必须 eager”不再覆盖这个版本：target 启用 FULL_DECODE_ONLY、draft 的 `enforce_eager` 省略或 false 时，DFlash2 可使用外层完整 ACL 图；显式 true 用于 eager 对照。这里不改变 LiLiCorr 的独立 guard 或 MRv1 的采样条件。

示例仍是 method=dflash、DFlash2 专用 checkpoint、TP2、K8，但新增 `max_num_seqs=1` 和 capture_sizes=[9]。Q=K+1 的每请求图容量需随实际 batch 和训练支持的 K 调整；K4/5/6 对应5/6/7的倍数，不能保留9并任意改K。candidate selector 的请求维度 context/编译缓存与外层 draft 图接线见[DFlash接入增量](../integration/vllm_ascend_dflash_runner_graph_contract.md)。

非因果 draft 原生滑窗 W 现用 FIA band mode `sparse_mode=4`、缓存压缩 mask，`pre_tokens=next_tokens=W-1`；无窗口层保留 full attention。它修正早先 eager 也忽略非因果滑窗的 workaround，和本卡 MRv1 `draft_window_size` 参数是两条不同路线。先在目标 NPU 对照 eager/graph、请求复用与采样质量，再报告收益；两卡 acceptance 测试仍只是来源定义，本次未执行。
