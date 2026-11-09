---
type: Guide
title: vLLM Ascend CP/O投影：权重切换、激活交换与异常恢复协议
description: 适配DSA/SFA的CP投影时按全局prefill与分片decode选择权重或激活通信，保持checkpoint和forward分组，核对空rank、SP输出、bias及清理边界。
aliases:
- OProjWeightSwitchMixin
- _o_proj_batch
- _use_full_o_proj_weights
- CP投影协议
- ParallelOProjection OProjectionMode
- apply_weight_shard bias_rank
- FULL_WEIGHT LOCAL_WEIGHT EXCHANGE_TOKENS
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/dsa_cp.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/weight_switch/o_proj.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsa_cp_o_proj_weight_switch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_o_proj_weight_switch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsa_v41_cp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/common_cp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/sfa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/weight_switch/o_proj.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/weight_switch/linear.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/weight_switch/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/methods/base.py
  role: implementation
created_at: '2026-10-31T07:50:04Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T06:28:46Z'
---

# vLLM Ascend CP/O投影：权重切换、激活交换与异常恢复协议

## 任务、来源与分层

模型迁移后出现CP的O投影shape、bias、输出行归属或异常后权重视图错误时，沿具体consumer追踪；完整权重、常驻分片和激活交换是不同分支。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。dsa_cp.py主来源只读1–64、1398–1501、1557–1902、2031–2057、2586–2863、2953–3030；legacy _forward仅早期launch选段，不是3030行完整attention闭合。sfa_cp.py只读1–247、631–890，不是整文件或Native SFA父类。

o_proj.py 83行、common_cp.py 342行、DSA UT244、SFA UT274和CP UT1399均已全文读取；common_cp在这里仅使用decode分片策略，其他DCP/LSE/slot实现仍属独立消费工作。utils.py仅三个相关helper，ascend_config.py仅默认字段。所有源码/测试只作数据，未执行UT、NPU或真实collective。整项平台支持未知，draft/空平台；局部is_950条件不能升级成整项硬件承诺。

[通用权重切换契约](vllm_ascend_weight_switch_contract.md)说明spec、加载器与pool所有权；[CP拓扑](vllm_ascend_context_parallel_topology.md)负责PCP/DCP组合限制；[CVLinear Q/KV接入](vllm_ascend_cvlinear_qkv_overlap.md)负责前处理多流。这里不把拓扑支持或构造默认flag当作所有模型的投影开关已启用。

## 先辨认具体类与角色

legacy AscendDSACPImpl继承AttentionImplBase[Any]；AscendDSAPCPImpl继承dsa_v1.AscendDSAImpl，不能沿同一个类层次传播硬件门控。legacy DSA完整O权重要求enable_dsa_cp_full_o_proj()且is_950()；SFA legacy的本地分支只看对应角色helper，不能擅自加同一个950限制或据缺少限制推导所有平台可用。

enable_dsa_cp_full_o_proj是lru_cache(maxsize=1)：先要求已验证AscendConfig启用DSA CP，再看Native KV transfer配置为空或is_kv_producer（包括both角色）；纯consumer pool不取该分支。缓存的是进程角色下的结果，不能在任意修改配置后假定helper重新计算。

enable_pcp_o_proj_weight_sharding同样缓存，配置字段默认True，但构造器还检查方法能力和整除条件，不满足时warn并回退。is_pcp_decode_sharding_enabled对KPool模型返回False以维护状态和请求顺序，其余要求PCP>1且DCP==1；声明覆盖speculative verification的predicate，不代表全部模型/版本组合都完成数值验证。

## 单投影包装器的进入与退出

OProjWeightSwitchMixin只unwrap一层，要求真实scheme是WeightSwitchMixin且supports_weight_switch；调用方对启用做幂等保护，以类名和role形成pool prefix。_use_full_o_proj_weights在进入时先wait再切full，这两步位于try/yield之前；finally负责yield主体异常后的local恢复，不能承诺所有进入失败也被该finally覆盖。

因此Agent要分开标注“发起前”“发起后”“wait中”“切换中”“projection主体中”的失败。复用通用pool和set_不自动拥有设备侧消费者；通用wait清空句柄也不证明所有Work成功完成。

## legacy DSA的两层完整权重

legacy DSA在满足角色/硬件门控时对wo_a、wo_b保留克隆的local权重，并以量化方法、名称和dsa_cp_o_proj前缀共享兼容pool。post-load要求完整head范围的attn_sink，两个scheme都支持切换，weight与scale按各自声明同时gather；只切weight会破坏量化分组。

gather在Q/RoPE之后、KV工作之前发起，尝试覆盖通信；实际投影前分别wait并切换两层full视图。两次wait/switch同样在projection的try之前；finally在投影主体后恢复local。早期attention失败发生在这些try之外时，不能仅据该局部finally声称完整forward已恢复。

inverse RoPE可走negate_sin能力或负sin Tensor，随后恢复TP heads，TP1或完整权重路径可跳过对应head交换。_forward_o_proj只消费当前活跃权重，调用方拥有准备和生命期；它不自行保证all-gather发生。

wo_a按逻辑分组使用匹配的三维布局或针对unquant/quant路径转换，不能凭packed weight外形推断头数；FP8/MXFP8分支涉及BF16输出、E8M0 scale view和group32，具体设备ABI仍待验证。full wo_b直接quant_method.apply且bias=None以绕过普通层的reduction，常驻分支仍走普通forward；不能把两条路线重复叠加TP归约。

## DSA PCP的常驻分片与加载

AscendDSAPCPImpl在检查投影分片开关之前就禁用projector multistream，因为其上游cache已全局准备。关闭分片flag并不撤销这条构造行为。n_local_groups无法整除PCP或任一方法不支持切换时告警回退；不能把defaultTrue解释为实际成功分片。

checkpoint中wo_a沿输出再分片、wo_b沿输入再分片，外层TP与内层PCP组合加载rank，forward TP group保持原值。常驻wo_a及scheme的组数缩小，attention的TP-local group计数仍服务attention布局。不要同时缩小两个计数再“修正”激活shape。

激活交换buffer按activation dtype/device分配，capacity取max_num_seqs*(1+num_speculative_tokens)、max_capture_size和capture_size列表最大值的最大值。AG输入/RS输出用本地capacity，AG输出/RS输入用PCP world乘capacity；共享pool仍要求串行O投影消费。warmup提前创建切换状态与稳定别名，地址不变不是实际图捕获证明。

## _o_proj_batch按全局批次决定路线

| 全局条件 | 投影权重与通信 | 需保持的行/组关系 |
|---|---|---|
| 分片未启用或无global metadata | 基础常驻/普通投影路径 | 不假造完整权重已准备 |
| 分片启用，存在global metadata，decode_sharded且无global prefill | 激活AG→常驻组投影→RS | rank-major padded token顺序与owner rows一致 |
| 分片启用，存在global metadata，其余批次 | full_weight，等待并切两层完整别名 | global prefill不能被本地单token误识别成decode |

replicated decode可narrow本rank常驻O组后做PCP sum；sharded decode用固定all-gather与reduce-scatter，不是all-to-all。不能因为某个rank只有一个token而跳过global prefill需要的权重通信。

quant_bias只在全局TP0且PCP0加入，TP all-reduce是否执行还看reduce_results。当前源码含小batch未见明确收益的注释，没有可复用的实验数据集/测量数字；不把它转写为本次性能结论。Native量化bias、GroupCoordinator及真实通信顺序仍需成对验证。

空query rank仍参与cache、weight和激活collective；正常路径要为别人的token投影，再将自己的输出清零。空rank退出的条件应依据全局协议，不能只看本地output行数。异常清理负责已有任务，不应为“补齐次数”凭空启动额外激活collective。

## SFA PCP与SFA legacy的区别

SFA PCP只有一个o_proj。构造检查逻辑输入宽度可被PCP整除及scheme能力，checkpoint按输入做嵌套加载且保留forward TP；decode验证输入激活宽度使用加载状态保存的逻辑宽度o_proj_weight_load_state.input_size_per_partition_before，不能读packed weight物理维来替代。

global prefill或本地非decode取完整gather；分片decode取固定激活AG/RS，否则PCP sum。quant_bias同样只加一次，普通bias还要遵守reduce_results、skip_bias_add以及TP归约规则，不能将两种bias无条件相加。

SFA legacy DSA-CP先将Native hidden补到TP对齐，再选rank局部区间；等待KV gather后才发起O权重gather。完整O权重且reduce_results=False时，零化输出并将rank-local token放入对应槽位，供上游SP消费，不做TP gather；reduce_results=True时gather行并校验/裁剪。decode走激活all-to-all与普通Linear，这与PCP的AG/RS路线不同。

PAD语义按输出函数核对：V4.1基础投影会清PAD；SFA forward的CPU定义中实际切片为1时，外层尾部仍可保留123。不能为所有projection统一加一个“尾部必须清零”的结论。完整SFA父类、KV数据面、LoRA及设备kernel未由这些选段闭合。

## 异常恢复与测试证据

DSA PCP的_o_proj_batch在finally中依次drain和切回各state，但清理循环没有隔离每个state的失败；真实第一个wait本身失败可能阻止后续state清理。legacy的进入失败边界也要单列，不能统一标成事务性恢复。

已读CP UT1399定义world2/4、四个cache平面、13类metadata场景、修正后的device序列游标、局部/全局RoPE消费和空rank；这些metadata定义不等于全部builder实现已闭合。O投影部分有TP×PCP checkpoint rank、packed FP8 scale/weight指针一起切换、owner token dense golden 3对30（错误求和21）的断言，以及六类失败注入。

weight_wait注入先调用原wait再主动抛错；它覆盖等待成功后的Python异常，不模拟第一个真实Work.wait失败。相关kernel/collective大多被CPU或MagicMock替换，is_950 False/True与FP8 False fixture也不是所有硬件证明。此次未执行通用或DSA/SFA/CP的上游UT。

后续获准运行时按legacy DSA、DSA PCP、SFA PCP、SFA legacy分别保存全局metadata、role/cache helper结果、逻辑组数和物理shape、每rank有效/补齐行数、两种通信字节、bias加法次数、local/full指针与异步任务状态。逐项验证prefill、mixed、replicated decode、sharded decode、空rank、spec、SP及故障；比较完整参考数值后再测真实端到端收益，不能用知识检索通过替代NPU或Agent A/B。


## 3164 版本补充：ParallelOProjection 的统一生命周期

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，完整 unified diff 与上下文已读；不把增量阅读标为目标整文件FULL，没有执行上游、NPU、真实collective或性能验证。

新的 `ParallelOProjection` 取代本节前述单目标Mixin，封装单层或grouped输入/输出两投影，提供FULL_WEIGHT、LOCAL_WEIGHT、EXCHANGE_TOKENS三模式。prepare_weight_load先校验groups正值与world整除、grouped kernel齐备，按嵌套TP/切换group准备checkpoint分片并缩小输入层local groups；forward的TP group独立保留。没有prepared/opt-in能力时不能仅按类存在启用切换。

batch在forward_context内enable，再按global metadata+decode_sharded+无prefill选择token AG/RS，其余global路径取full weight；无global保持local。all_gather_weights仅在full模式发起；forward真正消费前逐层wait再切full，finally逆序恢复local。进入switch之前先加入恢复列表，能覆盖部分切换失败；但恢复自身抛错仍不是事务性保证。forward_context异常时抑制drain次级异常并保留原异常，正常结束传播drain错误；wait_for_weights遍历所有已有handle后再抛首错，改善旧路径首错阻止后续drain的问题。

激活buffer在capture前按max序列×(1+spec)、capture上限分配，权重buffer与activation key分开；pool只允许串行投影消费。token AG是rank-major补齐行，RS必须匹配该owner顺序，超capacity显式拒绝。local模式先按切换group切feature，再按需grouped input projection，最后调用apply_weight_shard并对该group sum；交换模式改为AG→局部计算→RS。

AscendLinearScheme的apply_weight_shard把bias_rank传作tp_rank，量化完整补偿仅全局TP0且切换rank0承担；普通WeightSwitchMixin默认只去掉model bias，不同method仍需核对override。最终TP reduction看reduce_results；真实model bias读取当前layer属性，skip_bias_add和延迟归约只在指定TP rank加一次，支持在线替换bias。不能把量化shift补偿、普通bias和两种通信重复叠加。

以上只闭合统一执行器的增量。DSA/SFA各consumer如何翻译global metadata、启动gather及处理空rank，须与该版本caller成对使用；其增量另按attention主题维护，不能将独立helper源码当任意backend已接通。
