---
type: Guide
title: vLLM Ascend Kimi-K2.6：多模态权重、外部 Draft 与旧版本限制
description: 在A2/A3按W4A8目标和匹配Eagle3/DFlash区分加载，核对图capture、视觉输入和tool parser版本，不将K2.5/Thinking配置直接替换。
  针对 Kimi-K2.6 分开核对 TP4、DP4 单机与2P1D四主机的DP4/DP8、HTTP/KV端口、APC、MLAPO 和多模态预算；区分 DFlash
  K15 与 Eagle3 K3、legacy 调度回退及 YaRN attention_factor 的窄兼容，保留精度和质量验收。 区分 instant、thinking
  能力和模式字段缺口；分别核对 HTTP 与 KV 端口，按 VllmConfig 工厂缓存及 refresh 确认配置生效。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Kimi-K2.6.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Kimi-K2.6.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/external_online_dp/launch_online_dp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_speculative_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-release-tag.commit
  role: constraint
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T21:08:49Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- Kimi-K2.6
- Kimi-K2.6-w4a8
---

# vLLM Ascend Kimi-K2.6：多模态权重、外部 Draft 与旧版本限制

## 范围与权重

教程基线0.20.0rc1，K2.6是多模态MoE，A3一节点/A2两节点W4A8参考。K2-Thinking/K2.5停止维护状态不能转移成K2.6状态，旧CANN Executor的legacy runner不是当前vLLM路径。

## 草稿与版本条件

Eagle3使用匹配K2.6 draft；教程另列K2.5-DFlash草稿，跨名兼容只能按该实际checkpoint和实现验收，不把所有K2.5 draft视为通用。配置中K15等数值是某方法/图/负载参考，需计算K+1的backend与capture上限，不能照抄到不匹配proposer。

工具调用对transformers<=4.57.6的历史要求仅旧Ascend适用，教程说明0.21以后不再需要，不应为最新环境强降级。固定tokenizer、processor、reasoning/tool parser与目标模型版本，再进行请求构造。

## 视觉、缓存与测量

1080p、多图、128K无命中和有命中使用不同TP/DP参考，视觉token数量参与context/激活预算。先纯文本和单图数值，再eagle/dflash、图、PD；逐步覆盖长输出、混batch、拒绝状态和图padding。来源PD为示例，不作为自动生产配方。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## Kimi-K2.6：全文、译文与版本边界

本节补读固定Main的Kimi-K2.6.md全文801行与Kimi-K2.6.po全部121条业务译文，100条msgid完全匹配，21条原串差异逐条裁决；其中旧Service Verification标题和旧YaRN段落共2条仅用当前上下文定位，不冒充语义替换。PO编号按121个业务msgid顺序，不是源码行号或API选项。字符串匹配不证明中文网页、实际依赖或NPU行为。

模型首次支持与教程基线均为v0.20.0rc1，Main release pin v0.32.0、Native实际commit、镜像与checkpoint revision分开。tool_calls的transformers<=4.57.6限制属于旧教程，文档明确Ascend>=0.21后不再要求；不能为最新环境自动降级，也不能由解除这一项推定其他依赖均兼容。A3镜像带-a3，A2例使用无后缀tag；宏、tag、docker ps或同名路径不证明实际包/模型身份。

Docker例A3映射16设备、A2映射8设备，均shm1g、host网络及privileged；这是来源容器输入，shm与NPU HBM、KV预算分别计算，本次未运行容器或主机设置。

W4A8目标权重行列一台A3（64GB×16）或两台A2（64GB×8）；Eagle3与Kimi-K2.5-DFlash草稿行当前另列一台A3条件。草稿行不是把每种草稿都额外占一整台主机的计量公式，也不证明主/草稿共载、量化或图预算已通过。单机与详细PD命令均以A3为例，不能据A2权重行生成已验证A2四主机PD或950配方。

## 单机A3：TP4、DP4与多模态预算

实际单机命令为Kimi-K2.6-w4a8、quantization=ascend，TP4、DP4、EP开启；maxlen15000、每DP maxseq4、batch16384、memory0.87，APC关闭。它与参考表的TP8/DP2、17k、128k或1080P场景分别保留，不能拼成一套已验证启动配置。15000是输入加输出上限，不是每调度步token预算；文档精度测试另建议至少35000，不能直接用性能例预算评测长答案。

来源介绍instant与thinking能力，但本页未列明确的模式切换字段；不照搬Qwen的enable_thinking选项，按实际chat模板和parser补验。

单机draft为method=dflash、model=z-lab/Kimi-K2.5-DFlash、K15；这不是PD Decode的Eagle3 K3，也不是DFlash2架构的通用配方。FULL_DECODE_ONLY、enable_mlapo=true、mm-processor-cache-gb=0、mm-encoder-tp-mode=data和torch profiler是该命令的输入。视觉缓存0不表示没有视觉编码/激活占用；profiler配置也不是已经生成的profile结果。

单机显式allowed-local-media-path=/data/media，reasoning-parser与tool-call-parser均为kimi_k2，served-model-name=kimi_k26。媒体文件需在实际服务端可达目录；容器挂载/root/.cache不自动让/data/media可见。单机命令没有enable-auto-tool-choice，而PD命令显式开启，不能将parser存在等同自动工具选择或客户端已经执行工具。

enable_balance_scheduling在单机命令中为false。说明中的可选true只讨论v1 scheduler的吞吐/TPOT与TTFT取舍，长prompt、多模态和突发并发可能恶化TTFT，PD场景不建议开启；v1 scheduler不是Model Runner V1的同义词。W4A8节约权重空间不保证提高maxseq后仍有足够KV与激活预算。

## 2P1D是四台主机、三个服务组

当前A3 W4A8 2P1D例共四台16设备主机、64 NPUs：P0与P1分别是独立的DP4/TP4服务组，各占一台；一个D服务组为global DP8、TP4，跨D0和D1两台主机。不能按字面算成三台，也不能把两个独立P组拼成一个global DP8组后继续沿用KV JSON的prefill.dp_size=4。

| 主机 | global DP / local DP / start rank | DP主控地址 | 本机HTTP端口 | 模板KV端口输入 |
| --- | --- | --- | --- | --- |
| P0 | 4 / 4 / 0 | P0自身 | 7100–7103 | 30000 |
| P1 | 4 / 4 / 0 | P1自身 | 7100–7103 | 30100 |
| D0 | 8 / 4 / 0 | D0自身 | 7100–7103 | 30200 |
| D1 | 8 / 4 / 4 | D0 | 7100–7103 | 30300 |

四条launcher命令显式传DP RPC12321；主控IP不同，端口号相同不代表同一个DP组。proxy在P0监听1999，分别列出8个P HTTP端点与8个D HTTP端点，主机和端口一一配对。功能请求用单机8000或PD proxy1999，不把RPC12321、KV端口或某个engine7100当作同一入口。

模板MooncakeConnectorV1分别使用kv_producer/kv_consumer，JSON的prefill为DP4/TP4、decode为DP8/TP4。只有P0模板显式use_ascend_direct=true，其他模板省略，不能自行补造默认生效值。上表KV端口是模板输入；connector是否再按rank展开、最终绑定与连接状态仍需实际实现/日志核对，不能仅由四个字符串判所有engine无冲突。

## launcher：本地索引与全局rank分开

本批完整读取固定launch_online_dp.py的64行，未导入或执行。它逐本地索引i计算global rank=start+i、HTTP port=start_port+i、visible设备为[i×TP,(i+1)×TP)。D1虽为global ranks4–7，仍使用本机设备0–15和HTTP7100–7103，不能改成7104–7107或本机设备16–31。

launcher调用相对当前工作目录的./run_dp_template.sh，并传七个位置参数：visible、HTTP port、global DP、global rank、DP address、DP RPC port、TP。模板是否存在也按当前工作目录检查，不按launcher绝对路径自动定位。改变local DP或TP时需重新核可见设备，代码计算num_cards不等于已查询/验证主机资源。

脚本父进程只join子进程，没有显式汇总child exitcode为父进程失败；不能把launcher正常退出当成全部engine健康。dp-rpc-port参数声明type=str，但默认值写为整数12345并直接进入子命令参数，存在默认路径类型需核验的静态差异；本页显式12321路径与省略参数路径分开，本次未执行或复现异常。

## P/D预算、MLAPO与投机配置

| 角色 | maxlen / 每DP maxseq / batch / memory | 图与草稿 | 其他显式配置 |
| --- | --- | --- | --- |
| P0/P1 | 133120 / 1 / 16384 / 0.92 | enforce-eager，未配speculative-config | APC关闭，shared expert DP=true，mm encoder=data，HCCL_BUFFSIZE=1536 |
| D0/D1 | 133720 / 8 / 32 / 0.91 | FULL_DECODE_ONLY，Eagle3 K3，lightseekorg/kimi-k2.6-eagle3 | APC关闭，MLAPO=true，shared expert overlap=true，HCCL_BUFFSIZE=800 |

P/D的133120与133720分别保留，不静默改成同一个数。P没有草稿、D Eagle3 K3是此例，不套Qwen hybrid要求双端等K的规则；K与实际接受长度、每步输出或净收益也不同。

PD说明建议只在D启MLAPO；单机混合命令却显式MLAPO=true，须区分场景。D命令TP4、overlap=true，未显式shared expert DP=true，而说明文字的overlap条件为TP1或shared expert DP=true；需核派生后的有效配置和消费分支，不擅自补true或宣称overlap实际生效。P/D都给旧顶层recompute_scheduler_enable=true，但其当前兼容规则见下节。

## SchedulerConfig：嵌套优先，旧字段仍有回退

本批只复读ascend_config.py的1620–1695与1770–1942行。SchedulerConfig.from_additional_config按嵌套scheduler_config中键是否存在、顶层legacy、默认值依次解析；显式嵌套false会覆盖旧顶层true。旧顶层仍可回退并告警，不应仅凭旧写法判启动必失败；新配置优先使用additional_config.scheduler_config.recompute_scheduler_enable。

scheduler_config=None按空字典处理，非字典会显式报错；未知嵌套键向类构造转交，不能据resolver未丢弃就认为都被接受。工厂先解析sched、剥离已消费的legacy键，再传入AscendConfig并走后续派生。相同VllmConfig身份、完整缓存且未refresh可复用旧对象，修改原字典不等于各进程生效。完整通用链见[配置生效指南](../integration/vllm_ascend_configuration_resolution.md)，本节不声称读完全部配置类或执行校验。

## DFlash YaRN：删掉文档段落不等于删掉实现

PO119的旧兼容段落已不在当前英文教程；本批另完整查看patch_speculative_config.py的263行，只蒸馏其中Kimi DFlash兼容helper及接线，不将其他DSpark/K3/EP分支标为语义闭合。模块把SpeculativeConfig.hf_config_override接到包装器，包装器调用_normalize_kimi_dflash_rope。

该helper仅匹配DFlashDraftModel架构、model_type=qwen3、hidden_size7168、vocab_size163840、num_target_layers61，且target_layer_ids=[1,12,24,35,47,58]。还需plain YaRN的factor64、mscale1、mscale_all_dim1、original_max_position_embeddings4096全部匹配；识别依据是配置，不是本地目录名，不能推广到任意DFlash/DFlash2、target或新模型。

优先读取rope_parameters，仅其为None时回退rope_scaling；要求字典且attention_factor为None才考虑补值。补入1+0.1×ln(64)，约1.4158883083，使用新字典保留原参数。显式attention_factor优先，包括1.0，不是“字段存在但false就当缺失”。源码注释把此shim关联旧YaRN幅度与接受率变化，但外部vLLM PR56446、实际checkpoint、上游copy链和运行接受统计本批未验证；不由此证明target输出或所有新框架数值一致。

Eagle3、DFlash、DFlash2与DSpark按实际草稿架构、hidden-state接口、Runner和验证器分别选，参见[投机解码选型](../optimization/vllm_ascend_speculative_method_selection.md)。保持无投机与原精度基线，独立记录接受长度、质量、图预算、显存和端到端收益。

## 21条译文差异与验收边界

PO23/119是删除标题/段落后的上下文锚点，PO24/44是功能/代理验收文案变化；HTTP非200还需区分请求、服务与传输错误，不自动等于未启动。PO63/64是标题格式，PO76去表头星号但全节点NPUs定义仍在。PO85–93的八行模型显示大小写变化不证明资源路径大小写不敏感；PO89–93的msgstr甚至仍是整行英文，非空和0 fuzzy不等于已完成中文本地化。

PO99明确D组跨两主机；PO110将旧16384例改15000、补媒体路径与TTFT退化场景，精度建议35000不变。PO112修正权重链接路径大小写，PO113/114补draft硬件行；外部权重内容未获取，不把模型名相近或表格变化当并载/精度已验证。

当前推荐表的17k、130k、1080P、TP8/DP2、TP1/DP16与K15/K3都是另列场景，并非第5章实际命令的自动补全。页首把具体PD例限定为非生产参考，后文又泛称PD架构适合生产；至少须区分架构动机与具体配方，保留范围冲突，不用泛称解除示例限制。英/中MindIE Motor Quick Start正文本批均未读取。

精度表是v0.20.0rc1、一台A3的来源报告：AIME2026 90.00、GPQA 89.90、MMMU 82.67，未补百分率换算、数据revision、seed或原始输出。bench旧页仍有latency/serve/throughput、random-input1024、200 prompts、rate1及“几分钟”文案；不能套其他模型删段结论，也不据旧命令证明当前CLI接受或固定运行时间。

单机与PD验收curl都只发送文本，HTTP200、choices、usage或示意JSON不证明图片/视频、长上下文、全部rank、KV路径、投机质量或净性能。PD模板未显式带单机媒体路径选项；媒体/模板、per-engine端点、并发完成与cache槽复用、故障与streaming须在目标环境补验。本节闭合指定教程/121条PO及所列窄实现事实，未安装、执行主机设置、导入上游、启动服务/通信/benchmark或运行NPU与Agent A/B。
