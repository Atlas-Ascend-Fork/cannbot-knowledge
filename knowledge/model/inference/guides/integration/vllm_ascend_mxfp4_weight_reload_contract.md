---
type: Guide
title: vLLM Ascend MXFP4权重接入：Linear/MoE布局、scale与RL重载
description: 沿 AscendW4A8MXFPDynamicLinearMethod、AscendW4A8MXFPDynamicFusedMoEMethod 与 DS fp4 叶子核对 W4A8_MXFP 的UINT8打包FP4、E8M0 scale、NZ/转置、_mxfp4_transformed幂等标记与restore_weights_for_rl_loading；区分PreparedLinearInput、TP
  gather、MegaMoE活动列表、EPLB禁用、FUSED_MC2补偿bias及SITU和group_list_type边界。
aliases:
- AscendW4A8MXFPDynamicLinearMethod
- AscendW4A8MXFPDynamicFusedMoEMethod
- AscendW4A8MXFPDSDynamicFusedMoEMethod
- AscendW4A8MXFPDynamicLinearMethod.restore_weights_for_rl_loading
- AscendW4A8MXFPDynamicFusedMoEMethod.process_weights_after_loading
- _mxfp4_transformed
- W4A8 MXFP expert lists RL reload rejected
- get_eplb_weight_views use_expert_weight_list
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.mixture_of_experts
- topic.checkpointing
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/w4a8_mxfp4.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w4a8/test_w4a8_mxfp4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/method_adapters.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/base.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/quant_parser.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/prepared_linear_input.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/fp8_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/weight_switch/linear.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/registry.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_comm_method.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_mlp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/methods/w4a8/w4a8_mxfp4.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/eplb/adaptor/vllm_adaptor.py
  role: implementation
created_at: '2026-11-02T12:15:49Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MXFP4权重接入：Linear/MoE布局、scale与RL重载

## 接入任务与固定证据

新模型使用FP4 checkpoint后出现加载shape不符、scale重解释错误、重复后处理、RL更新后仍读旧布局或切换MoE消费者时，应先识别具体scheme和活动存储。本卡跟踪W4A8_MXFP：权重为微缩放FP4，激活为FP8。它与[普通整数W4A8](vllm_ascend_w4a8_moe_weight_contract.md)、W4A4_MXFP4以及[ModelOpt MXFP8加载](../deployment/vllm_ascend_modelopt_mxfp8_loading.md)各有独立合同，不能由名称中的4/8互换打包、补偿或重载方法。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。17个选定来源包含10份全文和7份有界：全文为w4a8_mxfp4.py518行、专用UT347行、method_adapters365行、methods包133行、quant_parser68行、PreparedLinearInput30行、registry62行、w4a8导入31行、paired pin1行及MLP入口135行；有界为moe_utils315–388、base1–185/287–404、device_op350–405/1205–1238/1348–1475/2082–2104、fp8_config105–144、utils812–822、weight_switch/linear1–215及moe_comm_method130–190/450–615。

共享文件继续保留各自的canonical owner。全文阅读不代表其中其他scheme、LoRA、路由、通信或Device分支全部闭合；本卡只闭合所述Host框架合同。Main实际paired Native为544f182d9f0c9bfe8bd7645525951d5e3692a542，本卡没有用独立5df快照代替该配对ABI，也没有新引入Native实现绑定。

全部源码和测试仅作数据阅读，未导入上游、运行UT、转换真实checkpoint、执行JIT/kernel、NPU、模型、通信、图、RL更新、精度或性能实验。整项硬件与模型范围未知，保持draft、空平台和framework=vllm部分Scope，不从A5某条分支推导整卡适用范围。

## 先确认注册键与存储语义

AscendW4A8MXFPDynamicLinearMethod注册为(W4A8_MXFP, linear)，AscendW4A8MXFPDynamicFusedMoEMethod注册为(W4A8_MXFP, moe)。实际键不是W4A8_MXFP4。registry存在条目只表明导入后的分派合同，不证明某个进程已经导入该模块或完成算子执行。

两类读取quant_description.group_size，缺省32；这里没有完整验证其正值、所有整除或合法shape。以N为Linear输出宽、H为输入宽、E为本层专家槽数、I为本rank intermediate宽、G为group_size，加载前的Host参数如下。

| 参数 | 原始shape与storage dtype |
| --- | --- |
| Linear weight | UINT8 `[N,H//2]`，容纳打包FP4 |
| Linear weight_scale | UINT8 `[N,H//G]` |
| MoE w13_weight / w2_weight | UINT8 `[E,2I,H//2]` / `[E,H,I//2]` |
| MoE w13_weight_scale / w2_weight_scale | UINT8 `[E,2I,H//G]` / `[E,H,I//G]` |

这些floor division不能替代对checkpoint逻辑维与group边界的预检。UINT8是存储容器；forward显式声明weight的float4_e2m1fn_x2语义、激活的float8_e4m3fn语义及scale/per-token scale的float8_e8m0fnu语义，不能把字节值数值转换成普通浮点scale，或套用整数INT4补偿公式。

method_adapters将这些Tensor注册为Parameter并附上loader元数据。is_mx_quant_type会识别该Linear和MoE类，Linear的group scale得到输入维元数据；MoE中group_size>0时相应weight_scale名字标为GROUP。实际Native loader、checkpoint key覆盖和跨rank切片仍需另外验收，参数创建成功不是完整加载证明。

## Linear输入、输出dtype与权重切换

prepare_input_for_overlap只接受二维Tensor；其他维度返回None。它执行npu_dynamic_mx_quant，激活目标为float8_e4m3fn，并返回PreparedLinearInput(quantized, scale, x.dtype)。apply收到PreparedLinearInput时要求scale非None并沿用output_dtype，避免再量化。

apply还接受预量化tuple，取其激活和scale，输出dtype缺省BF16；普通Tensor则现场动态MX量化并沿用原dtype。三条入口的输出约定不同，不能把tuple用于任意原始dtype后假定自动恢复。Prepared包装也不验证输入、scale、请求行及版本是否匹配。

npu_quant_matmul接收FP4权重语义、E8M0两类scale、可选bias及group_sizes=[0,0,G]。这里仅描述固定Host调用参数，不将这些常量解释为已经核验的CANN数学或所有shape规格。

本Linear显式supports_weight_switch=True：weight和weight_scale的输入切分声明gather_dim=0，输出切分声明gather_dim=1，作用于后处理后的直接Tensor属性。它没有声明supports_unaligned_tp_groups=True；不能把同族其他MXFP4方案的非对齐TP组逻辑移过来。通用[权重切换](vllm_ascend_weight_switch_contract.md)继续负责group、句柄、完整视图与缓冲所有权，[scale分片排障](../../runbooks/precision/vllm_ascend_quant_scale_tp_sharding.md)负责边界组与预分片判断。

## Linear后处理与恢复状态

process_weights_after_loading先检查_mxfp4_transformed；为真时直接返回。首次调用只在不存在_mxfp4_original_shapes时记录weight和weight_scale的原始shape，随后直接执行format29转换，显式传customize_dtype=float8_e4m3fn、input_dtype=FP4，再transpose权重。这条路径不通过通用maybe_trans_nz策略，不因其他scheme的NZ开关而自动回退。

scale原始为`[N,K]`，先reshape成`[N,K//2,2]`，再交换前两轴，成为`[K//2,N,2]`。这里K是scale最后维的group数，不是原始H；本Linear没有为奇数K补一项的分支。权重的Host转置示意为`[H//2,N]`，真实设备格式与packed语义仍须结合固定TorchNPU/CANN核验。

转换全部结束才设置_mxfp4_transformed=True。这个标记防止正常重复处理，不提供异常回滚：某一步失败时前面的存储可能已经改变，不能仅因标记仍False就盲目重试。

AscendW4A8MXFPDynamicLinearMethod.restore_weights_for_rl_loading在标记不存在或False时返回；为True时将weight转置回去并cast到ND format2，scale反向转置后reshape到记录的原shape，最后把标记设False。原shape字典不会每次自动重建，换了新shape的checkpoint不能默认沿用旧字典。

因此源码表达的正常周期是原始参数加载→后处理→推理消费→恢复ND/scale→加载匹配新权重→重新后处理。它不提供更新期间的读者排空、异常事务、图引用刷新或版本提交。当前Main搜索只找到该restore的定义及相关注释，所读adapter没有转发此方法；外部RL框架是否直接访问scheme并在正确时点调用，仍需追实际caller，不能据方法存在宣称自动接通。[RL更新指南](vllm_ascend_rl_weight_update.md)的暂停、KV版本隔离和传输流程也不能替代这一具体scheme调用证据。

## MoE聚合布局与MegaMoE列表

AscendW4A8MXFPDynamicFusedMoEMethod.process_weights_after_loading同样使用_mxfp4_transformed和首次原shape字典，先将两组scale分别从`[E,N,K]`reshape为`[E,N,K//2,2]`，再按use_cann_megamoe选择实际存储。这里也没有统一的奇数K补齐逻辑。

非MegaMoE先直接NZ转换两组weight，再transpose(1,2)；scale交换中间两个轴，形成`[E,K//2,N,2]`。若layer.activation为SITU枚举或字符串situ，w13在NZ前额外view为torch.float4_e2m1fn_x2，并传相应FP4 input_dtype。w2继续使用该路径原有FP4语义；不能只统一UINT8名字而丢失专门的dtype元信息。

MegaMoE在转置之前按专家建立cann_mega_moe_*列表：每份weight独立clone并作带FP4语义的NZ转换；每份scale clone后view为torch.float8_e8m0fnu，保留字节位模式，而非重新计算scale数值。列表保持原out/in方向和未转置的scale分块布局，不能拿普通GMM聚合转置Tensor替代。

随后MegaMoE调用dispose_tensor处理原w13/w2 weight及scale四个聚合参数。dispose_tensor只把传入Tensor的存储绑定set_为空Tensor；属性和Parameter对象可以仍在，其他alias或在飞设备读者并不会因此自动消失。活动计算权重已在专用列表中，检查“同名Parameter是否存在”不能证明仍持有有效聚合权重。

MoE restore方法却无条件按聚合三维weight执行transpose(1,2)、cast ND，再反向转换scale；没有读取MegaMoE列表恢复聚合参数的专门分支。专用UT中的恢复周期只覆盖use_cann_megamoe=False的mock路线。因此MegaMoE与RL重载的组合在本卡仍未闭合，不能把聚合路径的恢复结论移植过去，也不将这个静态缺口写成已经复现的运行故障。

非MegaMoE的恢复在SITU时还将w13 view回UINT8，随后按原shape字典还原scale，全部成功后才清标记。它同样不是任意中途失败后的通用恢复器；遇到混合布局或未知读者应先停止更新并重建可核对的加载状态。

## 能力flag与真实消费者

本MoE显式supports_eplb=False。dynamic_eplb在MRv2被设False，MRv1还读取Ascend配置字段；后者的字段值不能覆盖supports_eplb能力声明。[历史EPLB scale遗漏排障](../../runbooks/precision/eplb_remap_drops_independent_scale_tensor.md)说明成组搬运不变量，不为当前W4A8_MXFP增加EPLB支持。

apply把实际layer、TopK、映射、mask、router-weight位置、pertoken_scale及MX量化标志交给typed fused-experts入口；量化标志是FP8激活、FP4权重和E8M0 scale，mxfp_use_bf16在输入为BF16或FP8时为真。包装对象存在不证明所有通信模式已经接受该组合。

get_fused_mc2_weights依据运行上下文use_mega_moe返回专用列表或聚合Tensor，两条路线的w1_scale_bias和w2_scale_bias都为None。所读非Mega FUSED_MC2消费者却要求两组补偿bias非None。因此不能从getter存在推断非Mega FUSED_MC2可直接消费本方案，更不能补上整数W4A8的8×sum补偿来绕过门禁。MegaMoE还有独立资格与算子合同，加载时的use_cann_megamoe和运行上下文必须一致；本卡没有证明配置可任意热切换。

## 激活、scale归一化与SITU门禁

base的_quant_hidden_states在dynamic_scale为None时执行本scheme的MX动态量化；已带scale时沿用传入激活，二者都经过maybe_normalize_mxfp_scale_layout。当前moe_utils辅助函数对None或非二维scale直接透传；二维最后维为偶数时从`[M,N]`reshape到`[M,N//2,2]`，奇数则ValueError。它本身不做硬件判断，不能照搬[历史MXFP8 DeviceAdaptor规则](../../optimizations/rules/950_mxfp8_moe_activation_scale_packed_layout.md)的非950 no-op说法解释当前函数。

共享MLP入口依据supports_fused_activation选stage。本scheme只列silu和situ，不将通用fusion字段视为所有融合hook的唯一开关。其gmm1消费后会dispose原始输入；MLP在激活量化之后、gmm2之前记录可选事件，事件记录不等于计算已经完成。调用方仍须保证scale来源、有效行、别名和异步消费者一致。

SITU专门融合需同时满足activation为SITU、group_list_type属于0/1、G=32、linear_beta按缺省0处理后大于0；随后还受DeviceOperator实现约束。BaseDeviceAdaptor显式拒绝该MXFP SITU调用，A5实现检查quant_type、恢复UINT8 ND Tensor的FP4/E8M0语义，并处理weight/scale布局。DeviceOperator由硬件profile的adaptor family选择，存在此包装不证明整套MXFP4硬件支持、底层kernel闭包或所有shape数值已验。

未满足SITU专门融合条件时，先用grouped matmul得到BF16中间结果，再调用situ_mx_quant，目标为本文件的E4M3FN常量，输出scale继续归一化。SILU分支使用npu_swiglu_group_quant并传swiglu_limit：group_list_type=0时只取累计边界末项，利用当前算子对group_index求和的约定省去两项小算子；其他类型请求cumsum_group_list转换为type1计数。该helper没有实现type2→type1，不能把routing的三种编码都当已等价接受。

gmm2显式传FP8激活、FP4权重、E8M0 scale语义。原输入为BF16/FP16时保留该输出dtype，FP8走BF16，其他分支按代码选择FP16；不能由UINT8存储或另一scheme的dtype规则推断本路径输出。

## DS fp4叶子与验证边界

AscendW4A8MXFPDSDynamicFusedMoEMethod以(FP8_METHOD, ds_w4a8_moe)注册，继承上述MoE实现，只将创建scale的dtype改为实际torch.float8_e8m0fnu，shape约定保持相同。所读AscendDeepseekV4FP8Config仅在expert_dtype为fp4时为MoE选此叶子，Linear另走ds_linear；不能据模型使用FP8配置就把所有层都解释成本方案。[原生FP8规则](../../optimizations/rules/vllm_ascend_native_fp8_execution.md)继续维护其block展开与MXFP8重组边界。

专用UT347行以CPU Tensor和mock的format_cast/量化调用定义getters、shape、幂等、非Mega恢复周期和Mega scale字节重解释断言。identity format_cast不能证明真实NZ可逆，shape测试不能证明非零权重数值、SITU融合、RL caller、EPLB、通信或性能。本次未执行这些测试。

适配Agent应记录实际checkpoint/量化配置、scheme及wrapper、G/E/H/I/N、原始与活动weight/scale的shape/dtype/stride、转换marker、原shape字典、Mega模式、scale位模式、恢复caller和全部读者。先核对加载、逐元素参考与正常非Mega恢复周期，再分别验证预量化输入、SILU/SITU、group编码、允许的通信和实际更新生命周期。Mega恢复、未知caller或活动存储未闭合时，不发布对应组合的支持结论。

正确性成立后才比较加载转换/NZ及clone峰值、运行激活量化/GMM、通信与端到端时延；固定真实硬件、模型、版本、token负载和并行拓扑。本卡没有优化收益、NPU精度或Agent效果结果，也不移植其他仓库的低比特benchmark或整数补偿解释。


## 3164 版本变更：EPLB 与 MegaMoE 共享专家列表

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，完整 unified diff 与上下文已读；不把增量阅读标为目标整文件FULL，没有执行上游、NPU、真实collective或性能验证。

该版本W4A8_MXFP MoE的supports_eplb改为True，`use_expert_weight_list`在legacy dynamic EPLB、MRv2 enable_eplb或分布式初始化后判定MegaMoE时启用。前文“EPLB禁用”仅对应ceac；不能将新开关无条件反推旧版本。

后处理建立唯一常驻、未转置NZ专家列表与N-major连续scale列表；SiTU先clone uint8 packed bytes再附FP4语义dtype，规避直接FP4 clone的aclnnInplaceCopy限制。原四个聚合Tensor属性被del，之后empty_cache；其他外部alias是否仍持有storage必须另外核查，不能把empty_cache当释放所有权证明。

MegaMoE直接使用这份未转置weight列表，scale只view E8M0而不另clone，所以EPLB迁移更新的是实际消费storage。普通GMM由_get_mlp_weights产生zero-copy转置view；SiTU仍取N-major列表。get_eplb_weight_views对列表与聚合Tensor分别返回对应活动视图，不能迁移废弃副本。

**专家列表的RL reload明确抛RuntimeError**，不再沿聚合Tensor的反转置/ND恢复路线。聚合Tensor路径仍保留原幂等与restore；不能因supports_eplb=True就宣称EPLB、MegaMoE与RL在线重载全部组合兼容。验收应检查路由迁移后的实际weight/scale指针、两种GMM视图、SiTU列表与不支持组合的拒绝行为。


## 3164 EPLB 接收 buffer 的物理格式补充

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

VllmEplbAdaptor对W4A8MXFP无论fused MC2均选同四份活动weight/scale列表，并撤掉旧直接拒绝。weight接收buffer用offset0新分配，再原地format_cast到NZ29、附正确FP4输入语义；不能对带view/offset的expert盲用empty_like而丢失物理格式。scale仍按普通tensor分配。MM配置从get_text_config取得text config，不能只假定.text_config字段。迁移后必须核对新buffer与活动消费storage，列表RL reload的明确拒绝仍保留。
