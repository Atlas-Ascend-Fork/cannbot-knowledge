---
type: Guide
title: vLLM Ascend EPLB 接入：路由映射、真实权重与迁移提交
description: 面向新模型与量化方案的EPLB接入，核对MRv1注册列表、空MoE rank初始化、策略三元组、真实权重及scale搬运；MRv2按placement、lookup、commit/ack与HIXL所有权验收。 补充AscendEPLBController/AscendEplbState的target与draft注册、采样phase和共享时间轴、physical转logical统计、fresh全组门禁、异步readiness及关闭清理。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/model_runner_v2_eplb.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/model_runner_v1_eplb.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/expert_parallelism_load_balancer.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_kimi_k3_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/model_runner_v1_eplb.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/model_runner_v2_eplb.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/adaptor/vllm_adaptor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_abstract.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_random.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_factory.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/eplb_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/routed_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/eplb.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/eplb_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_eplb_controller.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_eplb_load_collection_phase.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/policy/factory.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/policy/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/eplb_utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/eplb/eplb_state.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/eplb_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/eplb/eplb_communicator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/eplb/eplb_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/eplb/tensor_ops.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/platform/patch_eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/platform/patch_fused_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/speculator.py
  role: implementation
created_at: '2026-10-29T11:00:26Z'
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
      model_features:
        all_of:
        - moe
      parallelism:
        all_of:
        - ep
updated_at: '2026-11-03T06:46:24Z'
aliases:
- AscendEPLBController
- AscendEplbState
- PreparedLoadStats
- is_eplb_load_collection_phase_matched
- _has_global_fresh_recorded_load
- _discard_samples_from_old_mapping
- EPLB共享采样时间轴
- EPLB异步readiness
---

# vLLM Ascend EPLB 接入：路由映射、真实权重与迁移提交


## 先确定控制权

固定 ceac1a2b；A2/A3/950 依据功能指南的整体范围，A2 必须无冗余专家，量化格式与 Runner 限制见[EPLB 配置指南](../optimization/vllm_ascend_eplb_runner_and_movement.md)。本卡服务模型/quant method 接入，不将迁移算法当成新模型默认可用能力。

MRv2 使用上游 EPLB controller/state/transaction，Ascend 扩展路由数据、量化权重视图及 communicator；不能同时启动 MRv1 的管理进程和另一套重排事务。AscendEPLBController 按 batch phase 过滤采样；不参与采样的批仍需遵守共享 window 的推进规则。

## 路由与权重属于同一代 placement

逻辑专家只选择一次，映射后的 physical expert ID 传给实际量化 MoE 计算。负载计数在 physical expert 空间，排除 padded rows；不要重复路由或把 padding 当热点。AscendEplbState/LayerState 的 device lookup tensor 原位 copy 更新，保持对象/地址稳定，保护 graph 与长期持有引用的 router。

quant method 必须暴露实际 compute 正在读取的活动 weight view，包括随权重迁移的 scales 等张量。不能由 controller 猜参数名、搬 canonical model 参数却让算子仍读旧的转置/打包权重。至少验证连续两次重排，防止第一次移动后视图失效。冗余专家初始化按逻辑专家 round-robin，不能只重复最后一个专家填满尾部。

提交顺序是新 placement 生效→刷新 device lookup→确认接收 workspace 可复用；ack 之前后台线程不得覆盖仍被本轮计算引用的接收区。精度对照必须使用真实 topk，force-EPLB 合成均衡不能验正确性。

## HIXL 注册与退出

HIXL 的 receiver 单边读取依赖所有参与模型的活动 tensor 存储范围，按对齐与邻接合并后注册；不是遍历 allocator 的全部分配。注册期间持有底层 storage 引用，直到 deregister 成功。单 session 上限4000个合并区域，超限应在 backend 注册前失败。

自动 communicator 选择先形成本地候选，再在 EPLB 全 ranks 达成同一 HIXL binding 类的共识；Python package 与 ctypes binding 不能混组。任一不满足时统一 Gloo staging，显式 communicator 不走自动共识但仍需满足依赖。已经开始 HIXL 后的失败不支持中途局部换 Gloo。

退出先排空已提交事务，断开并确认对端不再访问，再注销区域和 finalize。清理失败时保留尚未注销句柄与 storage 所有权，进入 fatal 链并终止 worker，不能先释放权重底层内存后继续执行。

## MRv1 的另一条契约

MRv1 的 layer 注册需跳过 PP missing layers，从实际 MoE 层推导专家数。每层 physical heat 全组汇聚后交给每 rank 的 spawn 子进程计算策略，再按每次 forward 一层搬运并提交。设计要求logical expert覆盖、同rank不放重复副本；实际worker的局部检查与回滚条件见下节，不将其当成所有形状/ID/集合校验。子进程失败会停用本进程的动态优化。

扩展策略必须同时接入 PolicyFactory 和配置枚举，返回 changed flag、层优先级和新 expert table；不能只实现策略函数。按节点分层还是全局分配取决于专家组与节点整除关系，不能从算法名推断固定拓扑。

验收保存每代 logical→physical 映射、活动 tensor/scale view、真实输出、迁移完成与 commit/ack，再测负载变化和端到端收益。本次只读设计，未执行迁移或通信测试。


## Kimi 主模型与MTP的初始副本加载

以下是固定Kimi adapter的静态接口，不扩大本卡硬件/量化支持范围。load_eplb_expert_weights在无冗余或非MoE时直接透传原weight条目；开启时按真实初始物理placement分派。前N个物理槽未必就是identity逻辑专家：helper为上游loader改写checkpoint expert编号并保留tensor及附带metadata；其余物理槽直接调用对应param.weight_loader，避免上游首次命中break漏掉replica和scale。直接加载分支传tensor和expert/shard参数，不等于也转发任意附加metadata；metadata身份保留的声明限于透传或重命名yield条目。

MRv2初始布局按EP rank分配冗余数，每rank槽数=(N+R)/EP，要求正EP和物理专家总数整除。R=0返回identity；MRv1 mapping上下文用EP=1，不能把MRv2跨rank布局直接照搬。patch若发现上游原生build_map已有ep_size参数则返回，不再安装这段兼容实现；生成mapping时出现多个MRv2 EP size会拒绝。

KimiMixtureOfExperts从非PPMissingLayer的真实本地MoE层取得num_moe_layers；无本地MoE时计数与专家列表归0。物理布局更新必须保持num_local_physical_experts不变，随后更新各层计数与expert map。检查每rank每slot的w13/w2和scale、反向文件顺序与metadata身份，再与真实路由输出比较；所引UT使用fake/CPU模型，本次未执行，不作为A2冗余专家支持证据。


## 中文设计与当前MRv1接口的差异

model_runner_v1_eplb.po的56条有效译文中31条msgid在当前英文找到连续匹配，25条未匹配；model_runner_v2_eplb.po为45/43、2条未匹配。旧V1说明的model_register、num_roe_layers及eplb/utils.py扩展指引不作为当前接入点。当前vllm_adaptor.py以register_layer收集实际本地MoE层，routed_experts.py有调用点；模型config提供first_k_dense_replace等事实，首个真实层提供local_num_experts/ep_rank。源码与译文的匹配并不证明完整段落仍覆盖新合同，例如策略factory说明后面新增的配置枚举步骤仍需单独保留。

## MRv1 注册列表与空MoE rank初始化

对于文本/多模态包装，所读adaptor在model.language_model存在时使用该对象和model.config.text_config，否则使用model与model.config。VllmEplbAdaptor._registered_moe_layers 是class属性的注册列表，register_layer向其追加，构造时moe_layers引用它并直接取首层，初始化buffer还取首专家张量。空MoE rank的初始化必须沿这些访问检查：后面的空load分支不能证明无MoE PP rank或零本地专家初始化已支持。跨模型/重复加载的列表清理与完整PP生命周期仍需追调用方，不把Kimi/MRv2的空层处理推给此MRv1类。

## 策略返回三元组，实际消费者不采用优先级

旧PO写只返回newplacement，当前policy_abstract.py注释又写二元组；当前具体Random策略返回三项，worker.calculate_rebalance_experts也明确拆包(changed, priority, new_map)。新策略按三元组对接，并同时登记PolicyFactory和EplbConfig的0–3枚举扩展，不能照旧说明只实现一个函数。

所读do_update使用_, _, new_placement丢弃前两项，后续greedy composer按layer_id迭代；不能只因设计文档称per_layer_priority就认定这条消费者据它排序或按changed=false跳过。正常调用中第三项仍要可用于后续placement/负载计算，不能用空值代替“不变”。完整其它消费者/未来版本另核对。

原始诊断锚点为[eplb/policy] Unrecognized policy_type。PolicyFactory当前映射0 Random、1 DefaultEplb、2 SwiftBalance、3 FlashLB；直接绕过配置校验传入未知可哈希键会告警回退Random，而非保证拒绝。policy0固定交换ranks3/1末槽，至少4个rank，不能把它当真实随机均衡。选择3还调用warm_up，成本/外部依赖本批未展开；Random模块导入含random.seed(42)，factory会导入该模块，不把导入策略当无副作用的接口探针。本次未导入或执行这些模块。

## placement局部校验与观测先后

当前check_expert_placement逐层检查：新unique数量少于旧unique数量；同rank出现重复ID；留在同rank的专家改变槽位。命中这些条件时把该层新placement改回旧层并记录error。unique数量比较不是完整集合相等证明，也不替代shape、ID范围、旧表/别名等工程验收；不能因本段未显式检查某项就宣称整条运行路径会接受非法输入。

do_update在此检查之前已计算并记录current/updated热点，随后才校验、转换专家图、构造发送/接收信息。updated是预测值，非法计划可能在日志之后回滚，甚至尚未发生真实搬运；用它直接声称精度通过、实际均衡改善或commit完成均不足。每次前向的真实映射、活动weight/scale、commit/ack和输出仍按前文验收。

## MRv1活动张量访问与缓冲区

adaptor按(QuantType, effective enable_fused_mc2==1)选EPLB_EXPERT_WEIGHT_NAMES，不把原始配置值随意布尔化；配置回写也要纳入核对。

| 量化键 | 所读MRv1张量族 |
| --- | --- |
| NONE，非fused/fused | w13/w2的weight或weight_list |
| W8A8 | weight_list、w13_weight_scale_fp32_list、w2_weight_scale_list；fused还含fused_w1_scale_list/fused_w2_scale_list |
| W4A8 | weight_list、两组weight_scale_list与scale_bias_list；字典中fused和非fused均有键，不能把文档“with fused MC2验证”推成非fused已同级验证 |
| W4A4MXFP | 原weight及weight_scale张量 |
| W8A8MXFP | weight_list与weight_scale_list |

W4A8MXFP显式抛RuntimeError，缺失字典键的组合另ValueError。存在键只表示这段访问布局，不能代替硬件、kernel或MRv2格式能力。

有静态声明的get_eplb_parameter时由该访问器取得真正owner张量，否则取layer属性；getattr_static用于判断可选访问器，避免动态代理/MagicMock制造不存在的接口。相同量化/fused键的各层buffer shape必须一致；buffer按真实首专家张量empty_like创建，更新weight时逐张量copy_。不能少搬独立scale/bias，或让kernel仍引用旧的打包/转置存储；本段不证明全部Device/stream语义已闭合。

_export_tensor_to_file只由global rank0写JSON，包含moe_layer_count、逐layer_id/device_count、device_list里的device_id/device_expert。device_expert通过查找每个本地物理槽在map中的位置生成，不能直接把内部global→local表原样当导出格式。导出layer_id由传入expert_maps第一维枚举生成，不自动加入dense/PP的全局层偏移；实际模型层号对应、map形状与内容仍需校验。

## 源图的逻辑专家与物理槽位示意

![EPLB逐层放置示意](https://raw.githubusercontent.com/vllm-project/vllm-ascend/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/eplb.png)

图的两行明确标为Layer 0和Layer 1，两节点各有4个设备列，每列每层2个槽位。按专家放置上下文阅读编号，每层16个槽位覆盖12个不同编号，因而有4个额外副本；两层放置不同，同一层的重复编号分布在不同设备列。这是示意图的计数推读，不是实际运行测量、die数、TP/EP部署配方或产品支持证据；GPU列名也不证明该实现运行在CUDA。尤其不能把图里的非零冗余复制成A2配置，A2约束仍按功能指南num_redundant_experts=0。

源PNG未改动。首次透明背景预览遮蔽了左侧黑色层标签，后以原图嵌入白色PDF页完成核对；不沿用初览中“行语义未标明”的判断。

## MRv2仍以当前文档的事务合同为准

当前model_runner_v2_eplb.md使用配置选定policy，Ascend默认STAIR，旧译文“vLLM默认策略”不覆盖该选择。PD D端tail重算的phase例外、STAIR-only过滤、共享window推进、初始冗余round-robin、稳定lookup原位更新、commit后refresh再ack，以及HIXL最多4000个合并区域/失败保留storage合同分别核对，不与MRv1 tuple/registry混用。完整HIXL/STAIR实现、目标模型与连续重排的NPU结果仍待验证；文档/本段源码阅读不新增verified事件。


## MRv2控制器与注册：先分开target、draft和重载

本节将Ascend `ceac1a2b` 的controller/state实现与独立Native `5df63a72` 的 `EPLBController` 对照；实际配对pin是 `544f182d`，两份Native不能按同路径视为同一版本。整卡仍保留原A2/A3/950、MoE与EP范围；下述代码存在不增加硬件、量化组合或弹性EP支持声明。

`AscendEPLBController.prepare_load` 先置 `state=None` 和 `_has_registered_models=False`，仅在target的 `enable_eplb` 开启时构造 `AscendEplbState`。该函数本身未先关闭旧state，不能将重新调用当作完整热重载事务；已有后台线程、communicator及注册storage的退出按后述关闭合同另行处理。

`maybe_register_speculator` 先检查draft自己的 `enable_eplb`，draft关闭时返回False；父类仍检查target使能、speculator/model是否存在、dummy weights、实际MoE与DSpark配置，并拒绝draft与elastic EP组合。关闭draft不等于关闭target，也不能因为子类额外检查存在而跳过父类门禁。正常主模型注册同样由父类 `get_mixture_of_experts_model` 取得真实MoE对象。Main文件中的 `_unwrap_moe` 有针对多模态包装的单测，不能以此证明实际注册调用了这个helper。

controller构造在策略/state之前协调communicator选择，避免各rank先形成不同binding。所读factory只接受 `default`、`stair`；自定义统计入口由 `uses_custom_load_stats` 检查policy的 `prepare_local_load_stats` 是否可调用决定，不能只看策略字符串。该属性为False时 `prepare_forward` 直接委托state的上游准备路径，不套用下述Ascend自定义phase过滤。

## 采样窗口、phase与sticky fresh是三件事

自定义统计路径先由 `_should_record_current_step` 判断本步是否处于sampling窗口，再与 `is_eplb_load_collection_phase_matched` 的结果相与，写入 `should_record_tensor`。phase为 `all` 时全匹配；其他值按batch是否含prefill区分prefill/decode。所读Runner在输入准备处用 `batch_req_state.has_prefill` 调用 `set_batch_phase`；不能按请求名自行判定混合batch的采样类别。

| 状态 | 所读实现的含义与寿命 |
| --- | --- |
| `_is_load_sampling_step` | 本步sampling资格，尚未包含phase条件；step消费后清False |
| `_should_collect_local_load` | sampling与phase均匹配的本地收集资格；step消费后清False |
| `_has_fresh_recorded_load` | 自上次正常rearrange后曾产生合资格记录的sticky标记；当前phase不匹配不能抹掉此前的True |

`step` 将dummy/profile排除出有效sampling，但自定义时间轴只对profile停止推进：非profile的dummy或phase不匹配步仍占据一个共享时间位置，其mask为0、physical slot为-1。`_num_recorded_load_steps` 记录填入的时间位置，达到window size后转动起点，不是有效样本数。性能Agent应同时观察共享时间mask、物理采样slot和实际有效计数，不能仅用该整数推断样本充分。

## 共享时间轴与physical→logical统计

`_local_load_collection_mask` 保存每个共享时间位置是否有本地样本，`_physical_load_sample_slots` 将其映射到上游physical load window；两种索引不能互换。`collect_global_load_stats` 先在EPLB组的CPU group归约时间mask，只保留至少一个rank采过样的位置；本地缺样的位置填零，存在的physical slot按索引取出，再交policy准备统计。

`_map_physical_stats_to_logical` 用physical-to-logical map将各副本负载 `scatter_add_` 到逻辑专家。负mapping写到额外sentinel列，最后丢弃该列；这不是任意正越界ID的完整校验。随后跨模型拼接统计值，在EPLB device group归约，再按模型拆回 `PreparedLoadStats(values, sample_counts)`，不能把physical专家槽直接当logical专家热点。

任一model的 `_load_mapping_generation` 与已观察代数不同，`_discard_samples_from_old_mapping` 会清空所有model共享的mask/slot与窗口索引，并更新观察代数，避免新旧映射混用。这里核对的是消费guard；已读Main state只定义初始化与比较，不以helper存在宣称mapping generation的完整发布链已闭合。实际适配仍要沿提交调用方核对递增、窗口失效和多模型时序。

## fresh门禁、完整快照与两种通信组

`_has_global_fresh_recorded_load` 使用EP组而非前述EPLB统计组，优先CPU group；缺CPU group才回退device group，单rank直接用本地值。任一EP rank有fresh即可让全组进入后续门禁，避免有样本rank与无样本rank各自决定是否参加collective。

`rearrange` 首先受 `_suspended` 拦截。普通非profile、无 `rank_mapping` 且非elastic EP的分支才执行fresh gate；profile、显式mapping及elastic分支的条件不同，不能统一按“本地本步没有样本就跳过”。自定义异步统计还要求async、非profile且无rank_mapping；没有可用全局统计时不发布快照。正常非profile返回前清fresh；同步路径还刷新routing tables。

`publish_async_load_stats` 要求字典key与全部model_states精确相等，不能只发target或部分draft。先给各model写统计快照，再把所有model标记rebalanced，最后record rearrange事件。`get_rank_node_ids` 返回EPLB stage内部rank顺序下的节点序号，并校验发现mask形状与自成员；不能将其当全局设备ID或固定物理拓扑编号。STAIR算法、HIXL传输实现和完整跨rank事务仍按各自证据核对，本节未补齐这些内部实现。

## graph引用、live mapping与异步readiness

`AscendEplbLayerState.refresh_expert_replica_routing_table` 只有在旧表存在且shape相同时才原位 `copy_`；shape变化会替换tensor。因此前文“保持lookup引用”应在shape不变的前提下验收，不能推广为任意专家数/弹性扩缩都保证graph地址不变。初始化本地physical range还要求总physical专家数可被EP size整除。

`setup_from_mapping` 沿父类复用live state调用 `update_mapping`，Ascend随后刷新routing tables，避免重复构造communicator。这一接口存在不覆盖当前Ascend配置对elastic EP与EPLB组合的拒绝，也不证明目标模型的warmup、capture与重新映射已通过。

多rank `_poll_pipelined_readiness` 先等待上一轮CPU异步all-reduce；只有所有rank的ready flag之和等于组大小才返回True，否则提交新的ready归约并返回False。它刻意跨一次foreground迭代，首次本地 `pending_result` 非空不能直接认定全组已ready。单rank分支直接检查本地pending。此处readiness、权重真正迁移、lookup刷新和workspace消费ACK是不同状态。

所读Native state提交边界由Ascend patch临时延后 `consumed_event.record`，在routing refresh成功后再flush；提交或刷新抛错时不能提前释放接收workspace。需要比较commit、刷新与ACK的实际顺序，不能用一个ready日志代替端到端提交。

## close与配对版本的warmup差异

`close` 先检查既有清理错误，设置suspended；有后台线程时检查存活、drain真实已完成结果，再设置stop并join，超时上限300秒，之后才关闭HIXL session。`drain_async` 会等待在途readiness work，并消费changed-layer或no-op结果、record其真实consumed event。超时和后台线程死亡会失败；`raise_if_close_failed` 将session错误带入 `SystemExit`，要求在释放注册memory之前终止worker。不能吞掉普通RPC错误继续使用可能被对端引用的storage；本节没有执行关闭、线程或通信测试。

独立Native `5df63a72` 的 `step_eplb_after` 在forward成功后遇 `skip_eplb=True` 只跳过末尾step。实际配对 `544f182d` 则将整个该次forward包进 `self.eplb.suppress()`：保存先前suppressed状态和 `should_record_tensor`，临时禁record，finally恢复。只对照末尾step会漏掉router在forward内记录负载的窗口。不过Ascend自己的 `prepare_forward` 还可能写should_record，完整warmup调用链与不同版本嵌套关系仍需继续追踪，不能由这个decorator差异宣称全部warmup已安全。

## 新模型与性能Agent的验收入口

接入时保存target/draft实际使能、注册MoE对象、model key、policy能力、batch phase、sampling与fresh三状态、共享mask/physical slot、映射代数、EPLB/EP组身份、routing表shape和对象身份，再追踪pending→全组ready→commit→refresh→ACK。故障退出保存stop/drain/join与storage所有权，明确哪个阶段尚未完成。

性能比较固定模型、权重、量化、EP布局、采样窗口、phase和重排周期，分别观测有效样本、热点变化、foreground等待与端到端吞吐/延迟；不以统计发布、局部ready或预测均衡直接声称收益。所引两份CPU/mock UT定义了注册、phase、sticky fresh与远端fresh等断言，本次仅静态阅读，未运行UT、NPU迁移、精度、性能或Agent A/B，也未新增verified事件。


## 3164固定增量：AllGather负载资格与接收区消费事件

以下固定Main `3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，保留本卡既有平台、Scope和状态；只读代码增量不增加硬件/量化组合或运行结果。

新增tensor_ops从MoE注册/执行依赖中分离routing-table和负载统计。make_allgather_mask先按有效token、padding及record_enabled形成源行资格；SP时用TP rank对应的token段，再由调用方以与MoE输入一致的gather/unpad扩展。count_allgather_tokens按本rank的physical expert区间统计合资格topk，不直接改GMM计数。不能将gather后的行号当本地原请求顺序。

AscendEplbLayerState.record_load仍要求operator提供expert counts，即便另计算了allgather local_load；缺失、计数长度不等于local_expert_count或统计state未初始化会报错。使用allgather时改用type=1局部计数并以allgather_record_tensor标记真实有效source，而非仅靠forward是否dummy。controller先运行必要上游prepare，再按phase过滤初始化−1哨兵；step在获得真实记录后才更新fresh资格，profile仍排除。

CAPACITY_AND_WORLD_SIZE策略另持有ep_rank=0构造的公共replica表；ordinary表继续按真实rank构造。physical mapping变化时同步_allgather_physical_map、清pass/window并递增_load_mapping_generation，使旧采样不能继续按新mapping解释。相同shape按原位copy维护引用，shape变更仍需独立图生命周期审查。

AR draft的source padding由set_eplb_state绑定到每层；prefill复制实际padding，普通多步decode只把有效请求前缀置False，dummy/capture保持True。这个mask属于草稿统计资格，不代替Attention有效token或主模型padding合同。

HIXL communicator新增_consumed_event。async worker把上一层真实consumed_event交给下一层transfer，并在finally清该临时设置；execute优先等待该事件，缺事件才同步选定stream。依赖的是接收buffer已被消费，而非所有stream全局空闲。commit/lookup刷新/ACK的原顺序和失败保留storage仍需遵守，未运行实际HIXL、EPLB或连续重排验收。
