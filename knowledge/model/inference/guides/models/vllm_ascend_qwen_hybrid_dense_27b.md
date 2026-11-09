---
type: Guide
title: vLLM Ascend Qwen 27B Hybrid Dense：3.5/3.6/3.8 与四平台分支
description: 针对GDN加全注意力的27B Dense系列区分版本、W8A8/MXFP8/310P权重，按平台选择TP或DP并验证MTP、C8及混合状态。
  补齐 Qwen 27B 的 DUO event-id 与 MTP 捕获尺寸、prefix-match-unit、950DT QFA 及旧 GSM8K 归属。 补齐
  Qwen3.8-27B 的950PR与DT权重冲突、reasoning_effort、旧PD与1M扩展说法及中文前缀缓存表行遗漏。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3.5-27B-Qwen3.6-27B.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3.8-27B.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.5-27B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.5-27B-Qwen3.6-27B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.8-27B.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T15:31:13Z'
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
- Qwen3.5-27B
- Qwen3.6-27B
- Qwen3.8-27B
---

# vLLM Ascend Qwen 27B Hybrid Dense：3.5/3.6/3.8 与四平台分支

## 共同结构与版本

3.5/3.6的27B共享GDN+full Attention，3.8同属hybrid backbone并带MTP；Dense不启routed EP。教程的首次支持版本不同，固定主线中引用0.17/0.18/0.23是最早入口或文档基线，不表示与任意最新vLLM兼容。

## 平台与权重选择

A2/A3用对应BF16/W8A8，950用匹配MXFP8/C8 checkpoint，310P用专属W8A8/FP16分支；前置表笼统写BF16可到DUO与实际硬件表矛盾时不能强用BF16。950 C8采用kv-cache-dtype=mxfp8，需要checkpoint metadata；短输入可比较非C8而非一律启用。

来源A2/A3吞吐候选TP2+剩余DP、极长context再评估更大TP；950候选TP1+DP，310P只有TP2/4参考，3.8至少两设备。它们是特定权重/容量起点，不因同27B就互用峰值预算。

## 混合状态与验收

Full Attention KV与GDN recurrent/conv state需同时正确，prefix、抢占、chunk与MTP接受推进分别核对。模型方法别名qwen3_5_mtp按目标版本解析，不能替换成其他框架next_n。PD hybrid两端K一致；310P图、cache/依赖限制独立核对，不能照抄A3命令。

3.8教程明确性能推荐尚未充分验证，DP-first建议不等于本仓测量结果。先固定原始精度短/长输出，再图、量化、prefix与投机，比较缓存格式、状态、acceptance和净时延，失败回同平台原权重/eager。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## Qwen3.5 旧译文与当前 3.5/3.6 配方

Qwen3.5-27B.po 的69条消息是历史孤儿；当前英文已改为 Qwen3.5-27B-Qwen3.6-27B.md。本节完整读取该661行合并教程正文，对照旧译文；不把链接指向的其他教程或外部模型仓算作本次已读。旧 hybrid APC 的 align 模式与 block_size=2048 仅保留为当时实现条件，不能当所有后续版本默认值。当前长公共前缀可选 prefix-match-unit=16，要求整除每个 KV cache group 的 block size；细粒度复用会增加哈希元数据、copy-on-write 与边界 prefill split。

| 分支 | 固定来源示例与检查点 | 不可外推项 |
| --- | --- | --- |
| A2/A3 W8A8 | Qwen3.5-27B-w8a8-mtp 或 Qwen3.6-27B-w8a8；DP1/TP2、MTP3、seq32、batched tokens16384、max-model-len133120、HBM比例0.85。 | 整机8/16设备不是此命令实际使用量；吞吐表TP2×DP4/8另列，低延迟表seq4/batch4096，不能混为同一测量。 |
| DUO | TP2或4；实际示例TP4、float16及mamba-ssm-cache-dtype=float16、MTP1、seq128、context16384。 | 仅TP场景；表的128K/256K是另一长序列候选，不证明当前16384示例已验256K或相同并发。 |
| 950DT | Qwen3.6-27B-w8a8c8-mxfp8；TP1、DP1例，MTP3，context153600；吞吐候选TP1×DP8。 | 专属MXFP8权重与C8格式不可替代A2/A3或DUO权重；支持语句提及950PR不把本教程DT整套配方扩到全部PR。 |

DUO 在 TP 模式受 event-id 限制，最多两个 cudagraph_capture_sizes；MTP 后尺寸按 n×(num_speculative_tokens+1)换算。示例MTP1的[2,16]来自无MTP的[1,8]。正文另列[1,2,4,8]→[2,4,8,16]仅说明换算，不解除最多两个的限制，不能直接照抄四档。enable_npugraph_ex=false 与 FULL_DECODE_ONLY 同时存在，不能推成“DUO全图不可用”。

950DT 的 --kv-cache-dtype mxfp8 用于 full-attention 层：E4M3数据配 E8M0 scales，走QFA；--block-size 必须为512倍数，未设置时来源给512。短输入如16K比较非C8的W8A8 MXFP8权重，并移除该KV选项；这不是仅改dtype就能把另一checkpoint变成匹配权重。--quantization ascend 的省略也不会反量化文件，仍须检查checkpoint元数据与实际loader自动识别。

## 调优与验收时保留真实口径

Qwen3.6 的262144是输入加输出总context声明，不能从“256k+”表头推无限更长或借给3.5所有权重。TP2+剩余DP、长序列TP8及950TP1+DP分别是来源的容量/通信起点；约30GB权重能装单卡不等于包含KV、混合state、图、activation和通信余量后仍可承载目标负载。

max-num-batched-tokens 是每步调度预算，chunked prefill并不把它变为输入长度上限；增大它可能减少prefill轮数，也可能增加activation与decode竞争，不保证整体延迟下降。初始排队影响TTFT，TPOT/ITL是否包含何种等待须按真实时间戳定义，不能把同一初始等待重复摊入每个token。旧简化KV预算公式和EP不均衡泛用提醒不证明本Dense模型有routed MoE。

reasoning-parser=qwen3 的响应字段按API版本核验；mm-processor-cache-gb按API/engine进程复制而占宿主内存，0关闭，data encoder TP与shm cache的配置只描述相应多模态路径，不证明所有模态已通过。CPU binding、FlashComm1及源命令的sysctl属于实际运行优化措施，不能未经测量当必有收益或在摄入时修改host。

离线/在线短请求、混合状态推进、长上下文、APC重复/非重复前缀、MTP接受率及端到端SLO分阶段留证。源GSM8K 96.74只属于旧v0.17.0rc1 A3 Qwen3.5 W8A8报告，不能借给3.6、3.8、DUO、950或当本仓结果；本教程没有具体吞吐/时延测量。顶部PD是参考设计声明，正文未给本模型完整PD脚本，不补造可运行的P/D命令。


## 准确模型身份与当前中文资料

本卡覆盖 Qwen3.5-27B、Qwen3.6-27B 和 Qwen3.8-27B；它们是不同checkpoint，不能因共享GDN、full attention或MTP head互借权重、质量分数和性能结论。本节对照完整 Qwen3.5-27B-Qwen3.6-27B.po（141条）与 Qwen3.8-27B.po（99条），分别有81/76条msgid连续匹配当前英文，另60/23条有版本或内容差异。没有fuzzy不代表翻译正确或已生成中文网页。

Qwen3.8的英文范围是文本服务；64层中16层full attention、48层GDN，full_attention_interval=4，原生context为262144。旧PO另外描述 Qwen3_5ForConditionalGeneration、vision_config、图片/视频与可扩1M；当前简介已移除这些细节。它们可作检查真实config、processor、视觉encoder和长上下文策略的线索，不能当当前Ascend已验多模态/1M的证明；英文出现mm参数也不替代模态用例。相同底座不让Dense成为2.4T模型的MoE专家拓扑。

### 旧PD文字不能恢复当前部署命令

3.5/3.6合并PO仍有旧“高并发生产推荐Mooncake”的段落，涉及 launch_online_dp.py、run_dp_template.sh 和 load_balance_proxy_server_example.py；当前模型英文已删除该PD章节，顶部只保留参考设计、不建议生产的声明。这不是运行能力不存在的证明，也不允许从旧文字还原一套当前可执行脚本。

旧“1P1D”指两台A3主机，每台TP2/DP8，共32个逻辑设备、每角色8个API engine，并非P/D各一个engine。旧端口7100–7107按local rank展开，launcher参数表默认起始端口9000是另一默认值；--dp-size、--dp-size-local、--dp-rank-start、--dp-address、--dp-rpc-port和--vllm-start-port是旧外部launcher参数，不与现代 vllm serve 参数按名字机械替换。旧recompute_scheduler_enable只放D的建议也须按实际connector/scheduler重新确认。

PO引用外部B200文章称从9.5k到95k tok/s；本文没有读取或复核该外部文章、负载、精度和设备数，当前英文也未保留该段。它不提供Ascend提升10倍的证据，不能据此保证TP2+DP8或PD优于所有TP8配置。P/D分离仍需计算通信、队列、混合state与传输协议的端到端收益，见[PD生命周期](../integration/vllm_ascend_pd_transfer_lifecycle.md)。其中A2/A3的既有窄配方不自动证明本系列模型或全部硬件组合。

### APC、翻译与默认配置的三种差异

旧合并PO将某些混合KV的有效block_size≈2048与“短重复前缀考虑关闭APC”绑定；当前3.5/3.6英文改成APC默认启用，并给prefix-match-unit=16的更细匹配。这个修订不能解释为所有版本的短前缀永远不缓存或都应关闭；仍按每组block整除、state checkpoint、copy-on-write和实际命中统计验收。

Qwen3.8当前正文也称APC默认启用，优化表却把Prefix Cache列在“需显式开启”下面；图、CPU binding的“默认优化”表又不能代替实际build配置。保留原文冲突，检查解析后的prefix、graph和binding值；测试中显式记录所选设置，不由表标题推定开关已生效。其PO第67条msgid正是Prefix Cache技术表行且匹配当前英文，msgstr却只给通用调优/矩阵导航，遗漏了该行的场景、开关、KV复用和命中率条件。知识按英文补齐，不由这一中文缺行推定APC不支持。

### Qwen3.8 的 PR、DT 与 DUO 分支

| 分支 | 当前教程的明确示例 | 要保留的冲突或界限 |
| --- | --- | --- |
| A2/A3 | Eco-Tech/Qwen3.8-27B-w8a8，TP2/DP1、BF16、MTP3、seq32、batch16384、context133120、HBM0.85。 | 是样例预算，不能由整机8/16设备推出DP已用满。 |
| 950DT | Eco-Tech/Qwen3.8-27B-w8a8c8-mxfp8，TP1/DP1、KV mxfp8，MTP3、seq32、batch16384、context133120、HBM0.85。 | C8按full-attention QFA/E8M0与block512倍数核验；短16K可比较非C8 MXFP8。 |
| 950PR | 页签暂推荐普通 Qwen3.8-27B-w8a8，TP1/DP1、context256000、HBM0.9，称MXFP8进一步优化后再切换。 | 当前前置权重表的普通W8A8行只列A2/A3，后文却把C8/TP1+DP8推荐到PR&DT；不能无条件选择其中一段当整套已验证配方。旧PO的W8A8行曾显式列PR，保留这种版本差异。 |
| DUO | Eco-Tech/Qwen3.8-27B-w8a8-310p，TP4、FP16/SSM FP16、MTP1、seq128、context16384、capture[2,16]、npugraph_ex=false。 | 只按TP2/4可见设备选择；前面27B图的最多两档和MTP倍数条件仍适用。页签说量化需ascend，而命令未显式写该flag，检查真实quant metadata及loader，不推未量化。 |

镜像分别出现 qwen3.8-a2、qwen3.8-a3、qwen3.8-a5 和 v0.23.0-310p，都是来源标签，必须解析实际digest及依赖；不能把专用镜像名当完整复现记录。旧PO曾报告单流32→63 tok/s的CPU binding收益，当前英文只保留优化原理；缺完整负载/版本/统计，不设为Agent默认性能门槛。

### 思考控制、质量与优化验收

Qwen3.8 Chat请求的 reasoning_effort 放顶层，来源列 xhigh（默认）、medium、low；enable_thinking 与 preserve_thinking 放 chat_template_kwargs，后者保留历史消息的推理上下文。区分模板是否接受、parser是否拆分和实际response字段，不把preserve_thinking当GDN/APC状态已正确复用；也不能把该可关闭thinking的语义借给GLM-5.3。

英文v0.23.0参考GPQA Diamond分别为BF16 90.40、W8A8 89.90、W8A8-MXFP8 89.39；旧PO对应句写v0.23.0rc1。分数无完整hardware列、权重hash和评测原始记录，不借给C8、DUO、Flash-Next或本仓新verified。当前性能推荐明确未完全验证；先固定同一输入/输出长度、precision、prefix命中和并发，测接受率、状态正确性、峰值与SLO，不能由chunk/graph/binding原理直接承诺吞吐提升。本次未下载权重、执行脚本或推理。
