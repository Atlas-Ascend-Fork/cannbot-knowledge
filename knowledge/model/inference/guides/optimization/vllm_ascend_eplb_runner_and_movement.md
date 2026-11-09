---
type: Guide
title: vLLM Ascend EPLB：Runner 分流、专家搬运与负载窗口
description: 区分MRv2 STAIR与MRv1配置及中文旧配方，核对参数告警忽略/实际生效、阶段窗口、硬件/量化搬运限制与热点日志，使用真实路由验收EPLB。 补充孤儿 SwiftBalancer 的零开销、容错、冗余等于 TP 及旧经验值的证据边界。 单独说明 EPLB gettext 扁平表格的量化、硬件和列对齐，不能从合并词条恢复全部组合。
  补Triton副本表选行与负载计数的局部并发/提交边界。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/expert_parallelism_load_balancer.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/model_runner_v1_eplb.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/model_runner_v2_eplb.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/expert_parallelism_load_balancer.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/model_runner_v1_eplb.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/model_runner_v2_eplb.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_random.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/eplb_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/eplb_swift_balancer.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_factory.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/eplb_img.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/eplb.py
  role: implementation
created_at: '2026-10-29T09:49:02Z'
updated_at: '2026-11-03T05:56:49Z'
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
- map_to_physical_triton
- record_expert_tokens_triton
---

# vLLM Ascend EPLB：Runner 分流、专家搬运与负载窗口

## 适用条件与收益前提

只用于支持 EP 且量化方法提供完整 expert-weight movement layout 的 MoE。A2 不支持冗余专家，两个 Runner 均必须 num_redundant_experts=0；A3/950 的冗余预算还需满足 (logical+redundant)%EP=0。来源建议短P输入<1024、D每die专家过多或token<128先评估开销，非普适硬阈值。

## 先选 Runner，再选配置

MRv2 使用 enable-eplb、上游 eplb-config 的 window_size/step_interval/redundancy/policy/communicator；additional_config.eplb_config 只承载 load_collection_phase/stair_config。Ascend 默认STAIR策略（代码值 stair），异步搬运，use_async=false 被告警归一为true。不能带入 DYNAMIC_EPLB、EXPERT_MAP_RECORD 或MRv1字段。

MRv1 dynamic需配置+环境安全门控，record需record_path和对应环境，static加载map无需环境。默认policy2 SwiftBalance，policy0为固定swap测试不是生产随机均衡。完整周期含heat interval+algorithm interval+逐MoE层应用，不是一个forward完成。记录文件用绝对路径，只有global rank0写。

## 权重格式与通信一致性

MRv2允许BF16/FP16、W8A8/dynamic、W4A8，以及950的W4A4/W8A8 MXFP路径；W4A8 MXFP、W4A16与W4A16 MXFP因layout拒绝，不能靠换硬件绕过。仅W8A8有来源所列同级模型NPU回归，enabled不等于所有格式已验证。weight offload/prefetch与MRv2 EPLB互斥。

自动HIXL要求全部EPLB ranks解析同一binding类并达成共识，任一不可用或不同类全组回退Gloo staging。自动回退仅把未显式设置的迁移上限收紧为1；显式设置保留。已开始HIXL后初始化/运行失败显式终止，不中途混成Gloo，防止rank进度分歧。

## 采样窗口、观测与回退

MRv2任意batch含prefill即整批prefill，PD D端重算tail按decode；不匹配phase贡献零负载但推进共享window，无新负载可跳过重排。MRv1按padded token阈值分类，未匹配时不推进heat interval，二者不能互换。STAIR有hysteresis门，降低step_interval不保证持续搬运。

先用真实路由保存输出，观察 actual cycle committed、changed layers、transfer和热点变化，再测TTFT/TPOT与迁移成本。balancedness日志额外通信，仅诊断打开。enable_force_eplb覆盖真实topk，精度无效；机制见[理想均衡规则](../../optimizations/rules/perfect_eplb_profiling_upper_bound.md)，开关名须按本版本。停用EPLB并恢复可用权重/专家映射后回测；本次未运行重排或性能实验。


## 新模型与量化方法的接入验收

配置可用还不足以证明权重正确搬运。MRv2需活动weight/scale view、physical expert计数和原位device lookup更新，按placement→lookup→接收区ack提交；HIXL存储在注销前保持所有权。MRv1是逐层热度汇聚、子进程策略和每次forward一层应用的独立控制链。新模型须按[模型与权重接入契约](../integration/vllm_ascend_eplb_model_weight_contract.md)验收连续重排、真实路由精度和失败清理，再执行本卡的性能调参。


## 中文资料的版本裁决

固定expert_parallelism_load_balancer.po有114条有效非空译文，76条msgid在当前英文中找到连续匹配；model_runner_v1_eplb.po为56/31，model_runner_v2_eplb.po为45/43。三份均0fuzzy/obsolete，共215条、65条未匹配。当前英文全文及所有有效译文已核对；匹配是字符串/分段状态，不等于译文覆盖完整新段落、断言正确或zh-cn/latest实际渲染已证明。

| 旧译文或文档表述 | 本固定提交采用的裁决 |
| --- | --- |
| 静态EPLB计划在v0.25.1移除 | 当前用户指南仍保留MRv1 static/record模式，EplbConfig也有expert_map_path/record_path；旧计划不作当前已移除事实，不反推历史版本当时结果 |
| MRv2使用vLLM默认策略 | 当前文档定义Ascend默认stair，上游default只作显式比较；不把MRv1 policy_type=2的SwiftBalance当MRv2默认算法 |
| load_collection_phase是MRv2唯一扩展字段 | 还有stair_config；phase只在STAIR采样中生效，上游default策略不受其过滤，未匹配批仍推进共享window |
| V1 eplb_heat_collection_stage与V2 phase可互换 | V1按padded token阈值判迭代，未匹配不推进heat interval；V2按batch分类，混合prefill为prefill，PD D端prompt-tail重算为decode，未匹配贡献零但推进共享window |
| W4A16/W4A16 MXFP/W4A8 MXFP只是未完成验证 | 当前MRv2文档将其归为movement layout不支持、supports_eplb=False的启动拒绝，不能靠换硬件当可用；enabled格式与同级模型验证仍分开 |
| Random策略随机交换专家 | 当前policy0固定交换EP ranks 3和1的最后槽位，是测试策略，至少需要4个rank；它不同于enable_force_eplb替换真实路由的合成基准 |
| 搜索旧[Expert Hotness]日志 | 当前MRv1锚点为[eplb/worker] Expert hotness imbalance，MRv2为Ascend async EPLB cycle committed及临时balancedness日志；预测updated不当已提交/实际性能改进 |
| V1设计末尾泛称EPLB都需环境变量 | 按模式和实际配置校验：dynamic/record有安全门，static加载不要求该门；MRv2有另一套开关。不能把段落的连续字符串匹配当完整正确性证明 |

部分未匹配仅因标题、缩进、表列扩展或拆段，不把65条都判成错误；V1旧“key optimizations/通用函数规范”等编辑说明不提升成当前强制运行合同。MRv2新表增加required/range说明，200/200是短验证窗口示例，文档生产默认1000/3000；不要把验证反馈速度配置当通用最优值。D端每die专家>16的来源提示只明确950DT，不扩写到所有950子型号；P<1024、D<128 token等仍是先量测的经验起点。

## 分流参数与数值口径

以下默认值来自当前固定文档和所读Ascend扩展配置类；上游字段放在--eplb-config，Ascend扩展放在additional_config.eplb_config。字段位置本身是合同，不能只因名字相同就互换。

| MRv2上游字段 | 文档默认/范围与边界 |
| --- | --- |
| window_size | 1000，正整数；记录最近窗口 |
| step_interval | 3000，正整数；大于window_size时只采用最后window_size步负载 |
| num_redundant_experts | 0，非负；A2须0，逻辑+冗余总数须能被EP整除 |
| use_async | true；所读Ascend校验将false告警后改true |
| policy | Ascend文档默认stair；default为上游策略比较入口 |
| log_balancedness | false；额外通信，只临时调试打开，不当生产常开配置 |
| log_balancedness_interval | 1，正整数；仅开启日志时有关 |
| communicator | None自动候选；只接受None、hixl或torch_gloo，自动共识/显式设置的合同分别核对 |

| MRv1扩展字段 | 所读EplbConfig默认与边界 |
| --- | --- |
| dynamic_eplb | false；dynamic启用还需环境安全门 |
| expert_heat_collection_interval | 600；局部after-validator拒绝负数，不据此推荐零 |
| algorithm_execution_interval | 50；完整更新周期还包含heat和逐MoE层应用 |
| eplb_policy_type | 2，限定0–3；新增策略需同步配置枚举与factory |
| num_redundant_experts | 0，局部非负检查；硬件/EP整除还在其他层核对 |
| eplb_heat_collection_stage | all，枚举all/prefill/decode；不替代MRv2 phase |
| expert_map_path | None；static加载路径需.json、存在、可读，内容另验 |
| expert_map_record_path | None；非None会使dynamic为true并创建父目录 |

MRv2的stair_config是独立冻结配置，其before-validator拒绝原始布尔数值，范围如下；z_score由NormalDist().inv_cdf(load_risk_quantile)计算，不是服务TPOT/TTFT的分位数保证。文档定义balance为平均max/avg rank负载比的倒数；具体风险估计、协方差与滞回门组合须继续读策略实现，不由默认值宣称最优或性能收益。

| STAIR字段 | 默认 | 局部校验/文档含义 |
| --- | --- | --- |
| load_window_bins | 64 | 2–256，时间窗压缩bin数 |
| load_risk_quantile | 0.75 | finite且(0.5,1) |
| relative_balance_threshold | 0.95 | finite且(0,1]，相对上次已commit balance阈值 |
| absolute_balance_threshold | 0.90 | finite且(0,1]，绝对balance阈值 |
| rank_transfer_limit | -1 | -1或正数，单rank迁出/迁入上限 |
| cross_node_transfer_limit | -1 | >=-1；文档中0禁止跨节点迁移 |
| replica_search_num_stages | 4 | 1–8 |
| replica_search_radius | 8 | 0–32 |
| replica_search_beam_size | 64 | 1–128 |
| placement_search_backtrack_limit | 32 | 0–64；0关闭该回溯 |

固定指南对MRv1阶段选择给出的起点是：典型输入>1024可先试prefill；输入<1024且并发>1024可试decode或all；其余/混合流量比较三者。这些是来源经验，不是配置拒绝条件或跨模型最优规则。MRv1 FlashLB可能使用时间序列负载，其他策略不能仅凭collection_interval就统一增加窗口维；具体启用谓词与完整采样链仍需核对。

## MRv2混入遗留字段：文档与实现的失败方式不同

当前英文指南称混入MRv1字段/环境变量会显式启动报错；但同提交platform.py::_validate_eplb_config的实际动作更细。Agent诊断采用所读代码的分支，并保留这处文档差异，不以进程启动成功判断参数已生效：

| 该函数的输入/条件 | 源码动作 |
| --- | --- |
| additional_config.eplb_config不是dict | TypeError |
| MRv2扩展dict带_V2_EPLB_CONFIG_FIELDS之外的键 | warning后仅保留load_collection_phase、stair_config，并回写vllm_config.additional_config；不在此处因这些键直接抛错 |
| MRv2的stair_config为dict但有未知键 | 同样warning并过滤到StairConfig声明字段；错误类型/值仍可能在后续typed配置阶段失败 |
| MRv2检测到DYNAMIC_EPLB或EXPERT_MAP_RECORD的true/1真值 | warning称为V1控件并忽略其MRv2控制作用；不是在此分支raise |
| phase非all但没有--enable-eplb | ValueError |
| enable-eplb且communicator不在None/torch_gloo/hixl、elastic EP开启或weight offload/prefetch非零 | 对应条件ValueError；use_async=false则warning后改true |
| MRv1显式输入load_collection_phase或stair_config键 | ValueError，即使显式phase值为all；不是只拒绝非默认值 |
| MRv1启用上游enable-eplb | ValueError；它不是MRv1 dynamic开关 |

可定位的原始源码日志片段为The following parameters are unsupported and will be ignored。错误位置的window_size/step_interval等不会由此函数自动搬到上游EPLBConfig；从完整序列化对象复制所有字段也可能触发过滤或V1拒绝。保存原输入、warning、回写后的扩展dict、上游eplb_config、实际Runner与controller，再判断哪些参数真正被消费；上述局部函数通过不证明整条启动管线必成功。

该校验由_fix_incompatible_config调用，位于正常平台流程的init_ascend_config之前。另有独立导入条件：platform/__init__.py仍用旧环境变量决定是否导入legacy executor patch，因此“在MRv2控制分支忽略”不等于清除了环境变量或证明全进程无任何导入影响。MRv2配方应按文档unset旧变量；具体被导入补丁的全部行为仍需独立核对。

DeepSeek V4.1的所读平台硬检查针对DeepseekV41ForCausalLM/DeepseekV41DSparkModel两个准确architecture、DSV41_PACKED_CACHE能力与最终use_v2_model_runner=False，不检查原始环境键是否存在。显式VLLM_USE_V2_MODEL_RUNNER=1便于固定路径，但不把文档/错误提示中的设置建议改写成“必须存在该环境键”的通用实现断言；其余模型与功能校验继续生效。

## MRv1配置校验的真实边界

EplbConfig在record_path非None时先设dynamic_eplb=True，检查小写.json后创建父目录，再进入数值/策略/环境安全门。bare相对文件名的dirname为空，不能当完整记录路径；这个配置校验函数包含目录创建，不是纯只读探针。本次没有构造它。

加载路径只在此处检查后缀、存在与可读，不能据此证明JSON结构、专家覆盖、权限或后续加载均正确。三个legacy整数字段的局部范围判断是value<0拒绝，零不会被这条判断拒绝，尽管错误消息含must greater than 0；不据构造期允许零推荐零间隔运行。

DYNAMIC_EPLB的安全门接受lower后的true或1；EXPERT_MAP_RECORD只接受准确小写true。dynamic/record配置需要这个门，static不因这一段代码自动要求它。STAIR的数值字段另有before-validator明确拒绝布尔、范围/finite检查，不能把legacy校验规则推广过去。

MRv1 actor的updated热点日志在placement校验/回滚前计算，表示预测计划，不证明层已被接受、搬运或commit。完整的接口与局部检查边界见[模型/策略接入契约](../integration/vllm_ascend_eplb_model_weight_contract.md)。源架构图只作放置示意，不由GPU字样或整数槽位补出NPU SKU、负载或实测结论。上述均为固定来源静态核对，未运行EPLB、解析业务专家图、安装库或执行NPU/性能实验。


## 孤儿 SwiftBalancer 旧指南的使用范围

eplb_swift_balancer.po的82条业务译文完整读取，没有同名当前英文页。它描述动态、record与static三种模式，策略0–3和多种MoE/量化条目；不凭文件名将它补成当前MRv2的Swift默认配置。MRv1仍按本卡现有配置/环境安全门，MRv2走enable-eplb和STAIR入口。

旧PO称异步专家迁移“零开销”、始终降低TTFT/TPOT、冗余可在硬件故障时恢复。异步不等于无搬运/通信/调度成本，冗余放置也不是故障检测、状态恢复、rank替换或业务连续性的实现证明；本次没有复现这些性能/容错结果。应分别保留真实路由、已commit层/映射、迁移成本和服务指标，不将概述作为Agent保证。

### 参数与策略要按当前实现约束

旧“num_redundant_experts必须等于TP”“超过可用NPU数就系统失败”不能代替实际物理expert slots、全局/局部计数、EP整除及策略限制。本卡既有固定资料明确A2冗余须0，A3/950还核对(logical+redundant)%EP；不按旧“16 NPU就填16”机械配置，也不据这句话证明大于rank数的任意预算可用。

本次复读EplbConfig类与PolicyFactory，已有来源/读取信用不重复计算。MRv1配置默认heat600、algorithm50、policy2；数值局部判断拒绝负数而非所有零，record path还会创建目录，本次没有构造该配置。DYNAMIC_EPLB接受lower后的true/1，EXPERT_MAP_RECORD只认准确true；static路径后缀、存在和可读检查不验证专家图语义。与旧“只写config即可”或统一变量解析的推断分开。

PolicyFactory的0/1/2/3分别映射RandomLoadBalance、DefaultEplb、SwiftBalanceEplb、FlashLB；policy3构造后调用warm_up。未知type直接到工厂会fallback Random并warning，但正常EplbConfig先限制0–3，不能据工厂fallback宣称用户无效配置均被接受。旧Random的“随机交换”不覆盖当前已读固定rank/槽位测试策略；旧FlashLB关于滑窗均值/方差/协方差、FlashTree和minimize_redeploy仍为历史算法说明，本次未补读其全部实现或验证“最适合高频变化”。

### 老表、经验值和观测不能当跨模型保证

PO列DeepSeekV3/V3.1/R1与Qwen3-MoE，并出现W8A8/dynamic、W4A8 fused MC2、MXFP4/MXFP8、A2/A3/950文本。gettext会合并重复msgid，扁平词条不保留完整表格行列关系；没有同名英文时不能据相邻词条给每种量化分配全部硬件，也不借EPLB资料解除历史模型停更或310P边界。按当前Runner movement layout/模型weight和scale接入验收，而非模型家族名即支持。

旧建议稳定负载heat400+、波动100–200、algorithm>=30、网络>=10Gbps、首次均衡1–2分钟，均是缺完整实验环境的旧候选，不是当前配置硬拒绝范围、调度周期秒数或SLO。完整周期还包含采样、算法与逐层应用，按实际步数/时间测量；同容量NPU和网络建议也不构成异构支持或任意当前路径必拒绝的证据。

旧列expert_load_balance_ratio、ttft_p99、tpot_avg、npu_utilization作为观察项，本次未核对这些精确名字是否为当前exporter指标。按实际日志/导出器和统计定义采集，balance改善不自动推出p99/吞吐改善。expert map能被JSON工具解析仅关闭语法层，专家覆盖、索引、权重/scale、重复迁移与已commit状态另验。旧预热避免突发/映射先生成等流程建议不代替本卡的版本、Runner与实测验收；没有执行系统、模型或EPLB实验。

## 旧进程图与当前提交合同分开

保留的EPLB图将forward侧distribution_record/gather送入task queue，后台进程计算算法与p2p_policy，再经update queue送回expert table/权重更新，并单列d2d异步stream。它说明采样、计划生成、搬运和前向应用有不同所有者；计划已生成不是权重已提交或收益已实现。

这是旧工作进程的示意，不把queue或六步箭头当作MRv2 controller的实际ABI。当前MRv2仍按模型接入、[通信合同](../integration/vllm_ascend_eplb_transport_contract.md)与[STAIR计划](../integration/vllm_ascend_stair_planning_contract.md)分别核对placement、lookup、ack和提交；图不放宽Runner、格式、冗余与硬件限制，也不是本次运行证据。


## Triton路由映射与负载记录的局部合同

ops/triton/eplb.py 的完整程序结构显示：map_to_physical_triton按token_idx=扁平offset//topk，再用token_idx%routing_table_rows选择副本路由行；逻辑专家ID越界或负数写-1。它不移动专家权重，也不验证物理ID对应的weight/scale已经提交。空topk输入原样返回，不创建新结果；非空要求表行数、逻辑宽度与topk正且与请求布局闭合。

record_expert_tokens_triton只有device record_enabled非0才原位累加；group_list_type=1直接counts，其他值按累计count差分，未在这里限制只0/1。使用单program读旧load再store，没有原子加，调用者必须维持正确的stream/并发和清零窗口；不能跨多并发更新当安全计数器。local_expert_start只是写入offset，不在此校验全局范围。热度采样、映射输出与权重迁移commit仍分别验收。
