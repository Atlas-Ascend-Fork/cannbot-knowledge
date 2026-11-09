---
type: Guide
title: vLLM Ascend W4A8 MoE权重接入：位打包、补偿bias与活动视图
description: 沿 AscendW4A8DynamicFusedMoEMethod 核对ModelSlim与compressed-tensors原始weight/scale差异、FP32位模式转int64容器、INT4打包、scale_bias、EPLB与MegaMoE活动列表及SITU和MLP阶段分派；区分构造门禁、loader元数据、普通INT4与MXFP4、真实消费和未执行验证。
  按group_list_type将累积边界diff为专家计数，核对gmm1消费后dispose输入、gmm2前可选事件与存储寿命；_maybe_convert_group_list属于AscendW4A8DynamicFusedMoEMethod。
  核对grouped_matmul_swiglu_quant_v2固定INT8/FP32输出及quant_dtype、transpose_weight未转发的实际Host边界。
  区分adapter传入ACLNN与WeightNzV2 builder的quantMode、quantDtype、bias及transposeWeight默认字段，避免把签名存在视为handler已消费。
aliases:
- AscendW4A8DynamicFusedMoEMethod
- AscendW4A8DynamicFusedMoEMethod.process_weights_after_loading
- AscendW4A8DynamicFusedMoEMethod.get_eplb_weight_views
- AscendW4A8DynamicFusedMoEMethod.get_fused_mc2_weights
- AscendW4A8DynamicFusedMoEMethod.apply_gmm1_act_quant
- _pack_int4_to_int8
- AscendW4A8DynamicFusedMoEMethod._maybe_convert_group_list
- torch.ops._C_ascend.grouped_matmul_swiglu_quant_v2
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.mixture_of_experts
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/w4a8.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w4a8/test_w4a8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/dataclass/fused_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/dataclass/moe_mlp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/dataclass/moe_quant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_mlp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_moe_mlp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/base.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/method_adapters.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/registry.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/modelslim_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/compressed_tensors_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_comm_method.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_forward_context.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/grouped_matmul_swiglu_quant_v2_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/aclnn_grouped_matmul_swiglu_quant_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/grouped_matmul_swiglu_quant_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_fusion_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/grouped_matmul_swiglu_quant_utils.h
  role: constraint
created_at: '2026-11-02T11:02:07Z'
updated_at: '2026-11-03T05:11:01Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend W4A8 MoE权重接入：位打包、补偿bias与活动视图

## 接入任务与固定范围

新模型开启W4A8后出现加载shape不符、GMM tiling失败、scale数值异常、EPLB后精度变化或切换fused路径后读错权重时，先核对实际scheme、checkpoint原始布局、加载后存储和最终消费者。本卡跟踪AscendW4A8DynamicFusedMoEMethod的普通整数W4A8动态MoE合同，不将名称相近的W4A8MXFP或Linear方案合并进来。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。15个选定来源范围为10份全文与5份有界：全文包含scheme561行、专用UT305行、fused_experts/moe_mlp/moe_quant数据类144/116/159行、MLP入口135行、MLP UT646行、family导入31行、registry62行及pin1行；有界为base287–404、method_adapters263–365、utils330–425/812–822、ModelSlimConfig1–145/322–360/655–810及compressed-tensors config135–259/290–390/420–445。数据类和通用UT虽全文阅读，本文只闭合W4A8相关输入、权重和分派合同，不宣称其中其他量化、LoRA或路由路径已全部完成。

另只读communicator130–190/450–615及forward_context90–128/163–192/250–285，作为两个未选定范围的constraint引用；本卡不为它们新增来源绑定，也不以这些片段宣称完整通信、上下文或算子闭包。Main实际paired Native pin是544f182d9f0c9bfe8bd7645525951d5e3692a542；本卡未引入独立5df Native实现，也没有证明完整paired ABI。

全部上游源码和测试仅作数据，未导入、运行UT、转换真实checkpoint、执行kernel/JIT、NPU、模型、图、通信、精度或性能实验。硬件与模型整项适用范围未知，保持draft、空平台和framework=vllm部分Scope。[scheme接入](vllm_ascend_modelslim_scheme_adaptation.md)、[逐层格式分派](vllm_ascend_compressed_tensors_dispatch.md)和[EPLB事务](vllm_ascend_eplb_model_weight_contract.md)继续维护各自的通用合同。

## 先确认普通INT4方案与构造门禁

本类以(W4A8_DYNAMIC, moe)注册，quant_type为QuantType.W4A8，激活目标dtype为torch.int8，fused_activations只列silu和situ。family包还导出MXFP类，不代表普通INT4与浮点微缩放共享权重、scale、kernel或Linear支持。registry条目必须经过真实进程中的模块导入才存在，不能由描述字符串推导算子已执行。

构造读取quant_description.group_size，缺省0，正数明确ValueError，要求per-channel权重。它没有在这里统一检查全部非法整数、shape或数值。enable_expert_parallel为真时，本方法的有效MoE tp_size取1，否则读取标准TP world size；只有ModelSlim方法且该有效值大于16时触发tp>16拒绝。这个上界检查不证明其余任意TP尺寸、分片或模型都成立。

MRv2将dynamic_eplb字段置False，但use_expert_weight_list仍在MRv2 enable_eplb=True时打开；MRv1则还会读取Ascend动态EPLB开关。不能只检查dynamic_eplb=False就认为计算和迁移都使用单个聚合Tensor。构造获取MC2 group名称时只捕获AttributeError，不能概括成任意通信初始化失败都回退空字符串。

compressed-tensors按逐层format、位宽、channel/token、对称性和动态性选择W4A8_DYNAMIC，再按moe类型构造本scheme；未匹配的浮点回退和已识别却无scheme的拒绝仍是不同情况。ModelSlim按映射后的逐层量化类型构造，不能靠改配置名称把另一种checkpoint变为本类输入。

## 原始checkpoint到注册参数

以下以E为本层所创建的专家槽数、H为hidden size、I为本rank的intermediate_size_per_partition、T为本方法有效tp_size。gate/up合并到w13，down进入w2。示意形状以实际尺寸满足所需整除为前提；本scheme不提供完整维度预检。

| 加载前属性 | ModelSlim原始约定 | compressed-tensors原始约定 |
| --- | --- | --- |
| w13_weight | INT8容器，`[E,I,H]`，每byte已装两枚INT4 | INT8容器，`[E,2I,H]`，每int8存一枚INT4 |
| w2_weight | INT8容器，`[E,H/2,I]` | INT8容器，`[E,H,I]` |
| w13/w2_weight_scale | FP32，分别`[E,2I,1]`、`[E,H,1]` | BF16，同样逻辑形状 |
| weight_offset | 分配相应FP32参数 | 此scheme的参数创建不分配这些offset |
| scale_bias | FP32，w13为`[E,2I,1]`，w2为`[E,H,16//T]` | 加载后由未打包weight与scale计算并注册 |

params_dtype不是上述权重与scale的统一存储dtype；本方法显式选择它们的类型。也不能以两种格式最后都能形成同形GMM输入为由，交换其加载前shape、dtype或打包状态。

AscendFusedMoEMethod先调用scheme的get_weight/get_dynamic_quant_param创建Parameter并附上loader属性。普通weight_scale通常使用CHANNEL标记，scale_bias等名字命中专门规则后标为GROUP；这是上游loader的切分元数据，不意味着本W4A8方案因此允许per-group权重量化。

ModelSlim在MoE参数注册前包装layer.weight_loader。_make_modelslim_moe_weight_loader只把末级w13_scale_bias/w2_scale_bias名字分别映射为w13_scale/w2_scale，保留prefix、param、loaded_weight、shard_id、expert_id和return_success交给原loader。它不是全局字符串替换，也没有闭合Native loader的全部分片计算、所有key覆盖或版本ABI。

## 两种后处理不能交换

AscendW4A8DynamicFusedMoEMethod.process_weights_after_loading先分派对应checkpoint格式，再统一执行NZ与存储路线处理；不能交换两种原始输入。

ModelSlim路径先将w13/w2权重转置为计算轴顺序并contiguous，再转换scale。其scale_bias先transpose后沿中间轴求和，把原分片贡献归并为每输出通道的补偿；不能重新套用compressed-tensors的未打包weight公式。weight_offset的分配也不等于本卡已找到它在所有运行消费者中的用途，不据此随意删除checkpoint字段。

compressed-tensors路径先transpose未打包weight，用转置并reshape的scale计算`8 * sum(weight.float() * scale, dim=输入轴)`，分别注册w13_scale_bias和w2_scale_bias。补偿必须在逐元素INT4仍可见时计算，不能对已打包字节求同一个加权和。这里按Main实际8×sum描述，不把常数8解释成有符号INT4最大值，也不由公式存在证明完整算子数学或非零数值已经验证。

_process_scale先transpose/contiguous并取得CPU NumPy数组，将FP32内存重解释为uint32位模式，再把这些无符号位模式值转入int64容器并传回NPU。最终torch.int64不是把浮点scale数值直接取整；也不能把它当成普通FP64或任意框架的scale格式。compressed-tensors输入先显式转FP32再执行该过程。w13通常squeeze成`[E,2I]`，w2保留`[E,1,H]`供其GMM消费，不能为统一shape把二者都squeeze。

compressed-tensors随后调用_pack_int4_to_int8：相邻两枚值分别落在低、高4bit，沿最后一维缩为一半，并clone打断view链。它没有在这里逐元素验证所有INT4范围或完成通用checkpoint校验；不以按位掩码代替制备阶段的格式和数值检查。

## NZ、INT32视图与专家列表

两格式处理后都调用maybe_trans_nz，但结果受真实策略控制：FP32、meta和受限singleton形状不转换，FORCE_NZ能力策略及weight_nz_mode决定其他分支。调用过函数不能证明所有硬件、所有weight都已获得有效NZ存储；真实格式、clone后的布局与kernel输入仍须检查。

加载后根据use_expert_weight_list及use_cann_megamoe选择存储。应在加载与运行记录这些最终值，不把enable_fused_mc2、MegaMoE、EPLB当成可任意热切换而无需重建权重的同一开关。

| 存储路线 | 加载后动作 | 计算消费 |
| --- | --- | --- |
| 普通聚合Tensor | 将已装两枚INT4的INT8字节view为INT32并contiguous；最后byte维必须整除4 | 普通MLP/GMM读取INT32参数和对应scale/bias |
| use_expert_weight_list=True，普通计算 | 六类weight/scale/scale_bias按专家unbind后clone，删除原聚合属性 | getter返回真实列表；GMM权重列表再view为INT32 |
| use_expert_weight_list=True且MegaMoE | 保留每专家INT8形状权重，必要时将bias转FP32 | fused payload保持INT8形状并整理scale/bias列表 |
| 无expert-list模式但启用MegaMoE | 创建cann_mega_moe_*列表，权重clone、scale展平、bias整理后删除原六类属性 | 专用payload直接读取这些列表 |

在普通聚合路线，最终w13示意为INT32 `[E,H,I/4]`，w2为`[E,I,H/8]`。_pack_to_int32是按dtype改变视图，不是又做一次数值量化；前面的格式步骤与整除条件必须成立。专家列表在加载时保留INT8形状，不能只看Parameter是否已消失或dtype名字就判定丢失权重。

MegaMoE消费者的已读注释说明A8W4按INT8 storage shape推导宽度，并要求每专家NZ；套用普通八枚INT4/INT32形状会错误缩小其解释的N。本文只核对Host调用合同，没有执行设备检查或证明全部形状都可用。加载后处理会替换存储或删除参数，源码没有通用幂等/事务回滚标记，不能对已处理对象重复调用并假定仍是原始checkpoint布局。

## EPLB必须拿到实际活动张量

AscendW4A8DynamicFusedMoEMethod.get_eplb_weight_views优先检查w13_weight_list，返回两组weight和两组scale的真实列表；否则返回实际聚合Tensor。w13/w2_scale_bias存在时一起追加。两组补偿bias必须同时存在或同时为None，只有一组会RuntimeError；这只是getter的成对检查，不证明所有compute分支都接受无bias。

迁移对象是当前kernel正在读取的活动存储，包含scale与补偿bias。不能只搬加载前同名Parameter，或在postprocess删除聚合属性后继续缓存旧引用。专家clone的storage_offset为0是专用UT表达的条件，不是连续两次真实迁移、图引用或跨流一致性已经验收。

普通fused payload的bias.detach仍共享原存储，不产生独立数据快照；weight/scale列表也不因新建Python容器就获得存储隔离。修改、重排或释放之前分别确认消费者与迁移提交完成。[EPLB接入](vllm_ascend_eplb_model_weight_contract.md)保留placement、lookup和commit/ack协议，本卡不重新定义这些事务。

## Typed输入的layer所有权与量化状态

apply将hidden、TopK、expert map、冗余数、MC2 mask、router-weight位置、pertoken_scale、activation和per-channel标记交给build_fused_experts_input，再委托当前moe_comm_method.fused_experts。W4A8没有要求在legacy weights字段填满所有张量；实际layer被保留到MoEMlpComputeInput，stage hook从layer读取本方案的后处理权重。legacy payload为空不等于未加载，也不能用另一份旧weight覆盖实际layer owner。

这些数据类是frozen/slots包装，内部Tensor和所引用layer仍可变，不能由dataclass类型推导权重、hidden或存储已只读。普通communicator先dispatch，再构造MLP输入，执行stage并combine；FUSED_MC2另走下面的payload接口，不能把两条链路的入口Tensor和生命周期混为一套。

_quant_hidden_states在dynamic_scale为None时执行本scheme的动态INT8量化，已经带scale时沿用hidden与scale，避免重复量化。这个分支不完整验证传来的dtype、scale对应关系或请求行；适配方须保证二者属于同一次dispatch与相同布局。

_maybe_convert_group_list在group_list_type=0时将累计边界用首项加diff转换成type=1计数；其他类型直接透传。它不是对任意group_list的完整单调、总和或dtype校验。累计边界、专家计数、有效行与padding尾部必须和真实routing结果对应。

## MLP融合、SITU与输入寿命

apply_moe_mlp按quant_method.supports_fused_activation选择融合路径；本scheme的silu/situ会进入AscendW4A8DynamicFusedMoEMethod.apply_gmm1_act_quant。通用MoEMlpComputeInput.fusion由另一份量化集合及开关生成，不能仅看fusion=False就断言本W4A8不调用融合hook。实际LoRA启用时还有优先委托的量化LoRA分支，本卡没有闭合其W4A8权重协议。

SILU路线使用grouped_matmul_swiglu_quant_v2，传真实w1、scale、dynamic scale、group_list、weight_assist_matrix和swiglu_limit。SITU路线先运行带补偿bias和per-token scale的GMM，再调用dequant_situ_quant。SITU的per-channel scale额外unsqueeze为`[E,1,N]`，不能将展平通道数误当quant group数；它还把group_index转INT64，传beta与linear_beta，后者缺省按本调用转换为0.0。

不在fused_activations中的激活走独立gmm1、通用activation、动态量化，再gmm2；不能从“SILU可融合”推导任意新模型激活都使用同一kernel。SITU、SwigluOAI、GELU等通用分支还各有参数和能力要求，本卡不因通用UT出现其名字就声明本scheme全部组合已运行支持。

W4A8的gmm1 hook在消费后调用dispose_tensor，将传入hidden Tensor的存储绑定重设为空Tensor；这不等于所有alias或在飞设备读者均已消失。若调用方计划复用MLP输入，应先核对所有权和别名，而非事后读取被处置的同一Tensor。通用入口在激活量化之后、gmm2之前记录可选事件；shared-expert overlap配置关闭时可省事件，未初始化配置时保留记录。事件被记录与全部计算完成是不同条件，不能据Python返回复用正在被读写的缓冲。

## FUSED_MC2与MegaMoE消费边界

AscendW4A8DynamicFusedMoEMethod.get_fused_mc2_weights按实际expert-list/MegaMoE状态生成MoEWeights；普通列表路线提供INT32 view，MegaMoE路线保留INT8形状并展平相应scale/bias。该方法是Host payload整理，不执行通信，也不把任意列表形状验证为可用。

所读FUSED_MC2 communicator直接调用该getter，绕过普通MLP stage。非MegaMoE分支在enable_fused_mc2==1时要求两组scale_bias非None，并把权重、scale、补偿bias、TopK和通信组等传给dispatch_ffn_combine；其他enable值会在该方法拒绝。不能以EPLB getter允许两组bias同时缺失为依据，删除此分支要求的补偿。

MegaMoE资格还受算子存在、硬件能力、精确enable_fused_mc2==1、MoE模型、EP启用且1<EP world_size<=64、无LoRA等条件约束。加载后处理和forward context均会使用use_cann_megamoe，但本次仅读这些调用片段，未证明配置切换、动态上下文或所有模型的完整一致性。真实token容量、active mask、激活参数和通信资源还有独立合同，不因payload构造成功就声明多卡或图已支持。

## 验证、停止与性能归因

专用UT305定义构造拒绝、两格式getters、scale/bias shape、expert-list删除/clone与EPLB成对检查；后处理主要使用零weight及mock NZ/NPU路径。通用UT646中的W4A8部分检查SITU `[E,1,N]` scale、bias与beta分发，其他测试表达stage顺序、事件和回退。它们没有提供非零INT4逐元素pack/unpack、真实GMM数值、真实NZ/MegaMoE、EPLB迁移或性能结果，本次也未执行。

Agent应保存真实模型/格式、量化描述、loader与scheme对象、E/H/I/T、原始和处理后shape/dtype/stride、scale位模式、bias来源、列表/聚合属性及最终getter返回的地址。先用可逐元素追踪的非零权重和scale核对两种输入、位打包、反量化及补偿，再覆盖TP/EP、列表、SILU/SITU、不同group编码、预量化输入和允许的fused路线；EPLB还需连续迁移并验证真实输出。

[历史GMM规则](../../optimizations/rules/moe_expert_gmm_weight_lowbit_prep.md)、[clip/clamp规则](../../optimizations/rules/precision_low_bit_quant_clip_clamp_outlier.md)和[Prefill跳bias案例](../../optimizations/rules/w4a8_moe_gmm_prefill_skip_bias.md)各有其仓库、模型和路径边界。本Main接口没有由这些材料获得per-expert alpha、阶段性省补偿bias或同等吞吐收益的保证。不要把加载、打包或服务启动成功当作精度与性能完成。

shape、位模式、活动存储或补偿不匹配时，停止性能结论，恢复匹配的checkpoint、scheme、并行与通信配置；不要靠丢scale/bias、改字符串或重复postprocess掩盖问题。正确性通过后再分别测加载期CPU转换、打包/NZ及clone峰值、运行量化/GMM/通信和端到端TPOT。本卡没有模型、硬件、Agent A/B或优化收益结果。


## GMM-SwiGLU V2真实Host入口补充

补充读取本族adapter74行、ACLNN API207行、L0包装86行、tiling入口78行及INT8 fusion tiling204行全文；另读本scheme的447–509调用面、共享torch_binding3012–3017、Meta185–219及A5/Base设备包装333–363/1311–1349。这里仅扩展Host接口和分派facet，gmm_dsq_base/各架构handler、Base tiling、MX tiling及Device模板没有完整展开，不据此标完整算子闭包。

本scheme的SILU直接调用`torch.ops._C_ascend.grouped_matmul_swiglu_quant_v2`。其C++ adapter先读weight_scale[0]的末维N和x的二维形状，分配INT8 `[M,N/2]`及FP32 `[M]`，再调用`aclnnGroupedMatmulSwigluQuantWeightNzV2`。它没有先穷尽空列表、rank、偶数N或scale一致性检查；调用方必须预检，不应把这个低层入口作为任意输入探针。

Torch签名包含quant_dtype和transpose_weight，但adapter并未将这两个参数传给实际ACLNN调用；输出分配也不随quant_dtype改变。dequant_mode/dequant_dtype/quant_mode缺省各取0，weight_assist_matrix、bias、smooth_scale、group_list_type、tuning_config与swiglu_limit则按所读调用传入。参数名存在不等于该包装开放底层所有输出模式或转置能力。

Meta同样按x的M和首份weight_scale的尾宽构造固定INT8/FP32输出，忽略这些模式和转置参数。更底层L0在DAV_3510分支却可依据quantDtype、transposeWeight和quantMode产生不同输出dtype或三维E8M0 scale。这是不同接口层的能力差异，不能由L0或原生TorchNPU的能力反推本Torch自定义包装已支持FP8/MX，也不能用Meta形状通过代替实际Host验收。

所读WeightNzV2 API先调整ACL Tensor descriptor的storage shape/format，再将参数交给公共handler；这是对描述符的解释，不是把未知原始权重数值重排为NZ。单Tensor和专家列表分别使用不同维数与N推导，部分groupList/scale访问发生在公共handler完整校验之前。必须先保证已有存储确实匹配期望格式，不能用改descriptor或Tensor view修复不匹配的checkpoint布局。

公共API按NpuArch枚举为DAV_2201和DAV_3510注册两个handler；没有匹配项时返回参数不合法。handler内部的完整校验、转换及所有版本ABI仍待展开，不把这两个枚举自动扩展为本卡全硬件支持。所读tiling入口又按平台是否提供BF16 L1-to-BT intrinsic，选择priority2的MX策略或priority0/1的INT8策略；这些分支不是单看SOC名字或函数后缀V2即可确定。

INT8 fusion tiling的IsCapable只接受INT8 weight及4/5维storage，检查group_list_type为0/1和swiglu_limit非负；workspace表达式为`M*N*sizeof(int32_t)+20MiB`。普通W4A8所持INT32 view不满足该INT8 weight谓词，因此不能把这个特化的key、workspace或性能行为直接写成本scheme所有输入的实际路径。其他Base/MX策略和Device共享内存尚未闭合，上式也不是整条模型的显存峰值。

A5 DeviceOperator的同名近邻方法可转发原生`torch_npu.npu_grouped_matmul_swiglu_quant_v2`，其中FP8路线有独立quant_dtype/dequant_dtype参数；这不覆盖本scheme直接调用自定义包装的事实。适配Agent应同时记录Python真实caller、Torch schema、adapter最终ACLNN symbol、实际架构handler、输出dtype/scale布局与选中tiling key，不按名字相似合并支持结论。

SiTU的INT8与MX独立量化入口、count尾部和文档差异见[SiTU量化Host指南](vllm_ascend_situ_quant_host_contract.md)；FP4融合GMM/SiTU的不同入口见[GMM+SiTU接入](vllm_ascend_gmm_situ_quant_host_contract.md)。这些补充仍只有源码与测试阅读，没有本次构建、NPU数值或性能结果。

## WeightNzV2 builder的下游转发限制

补充核对同一固定Main的ACLNN API175–183及ParamsBase39–60：普通V2 API显式SetQuantAttr与SetBias；WeightNzV2的builder则只有输入scale、smoothScale、分组、辅助矩阵、dequant属性、limit、scenario及tuning配置，没有SetQuantAttr、SetBias或SetTransposeAttr。它交给handler的quantMode/quantDtype/bias/transposeWeight因此仍为0/0/nullptr/false；部分handler后续从stride识别转置，应另按真实分支判断。

前文“bias等按调用传入”限定为adapter到ACLNN函数实参这一层，不能推导最终ParamsBase已完整转发或handler消费。这与adapter自身未转发quant_dtype/transpose_weight是两段不同的限制。不能仅改Torch关键字就宣称打开MX、任意bias或转置路线，也不能把普通V2 builder的行为移植到WeightNzV2。后续handler、workspace、MSD/A4W4数值及Cube/Vector调度差异见[GMM/SwiGLu执行族](vllm_ascend_gmm_swiglu_execution_family.md)，此处保留原来源owner，只引用这些有界合同。
