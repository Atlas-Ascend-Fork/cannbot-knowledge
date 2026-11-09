---
type: Guide
title: vLLM Ascend 融合RMSNorm接入：残差、量化输出与Host tiling
description: 聚合AddRmsNormBias、RmsNormCast和RmsNormDynamicQuant的caller/输出ABI、Host分派与Device数学；明确INT8
  Meta dtype不一致、rounded FP32 routing、per-row scale与SingleRow gamma/队列、SliceD workspace静态缺口。
aliases:
- AscendRMSNorm.forward_oot
- AscendGemmaRMSNorm.forward_oot
- npu_add_rms_norm_bias
- npu_rms_norm_cast
- npu_rms_norm_dynamic_quant_npu
- npu_rms_norm_dynamic_quant_meta
- TilingAddRmsNormBiasRegbase
- Tiling4RmsNormCast
- RmsNormDynamicQuantTilingHelper
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_host/rms_norm_dynamic_quant_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_host/rms_norm_dynamic_quant_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_host/rms_norm_dynamic_quant_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_host/rms_norm_dynamic_quant_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_kernel/rms_norm_dynamic_quant.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/add_rms_norm_bias_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_host/add_rms_norm_bias_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_host/add_rms_norm_bias_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_host/add_rms_norm_bias_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_host/add_rms_norm_bias_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_host/add_rms_norm_bias_tiling_arch35.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/add_rms_norm_bias.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/add_rms_norm_bias_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_host/rms_norm_cast_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_host/rms_norm_cast_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_host/rms_norm_cast_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_host/rms_norm_cast_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_kernel/rms_norm_cast.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_kernel/rms_norm_cast.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/op_kernel/rms_norm_cast_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/rms_norm_cast/rms_norm_cast_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/layernorm.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/model.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/model.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_kernel/reduce_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_kernel/rms_norm_dynamic_quant_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_kernel/rms_norm_dynamic_quant_cut_d_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_kernel/rms_norm_dynamic_quant_helper.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_kernel/rms_norm_dynamic_quant_normal_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/rms_norm_dynamic_quant/op_kernel/rms_norm_dynamic_quant_single_row_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/add_rms_norm_bias.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/add_rms_norm_bias_merge_n.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/add_rms_norm_bias_multi_n.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/add_rms_norm_bias_single_n.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/add_rms_norm_bias_split_d.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/arch35/add_rms_norm_bias_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/arch35/add_rms_norm_bias_regbase_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/arch35/add_rms_norm_bias_regbase_split_d.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/arch35/deps/reduce_common_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/arch35/deps/rms_norm_regbase_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/reduce_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/add_rms_norm_bias/op_kernel/rms_norm_base.h
  role: implementation
created_at: '2026-11-03T01:52:45Z'
updated_at: '2026-11-03T05:59:46Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 融合RMSNorm接入：残差、量化输出与Host tiling

## 接入任务与阅读范围

新模型把RMSNorm与residual、量化或FP32 routing输入融合时，先确定需要的输出语义，再检查实际Torch binding、Meta、OpDef、shape与tiling。三个同族入口不能按名字互换；构造成功、Meta返回Tensor或设备文件存在都不证明当前配置可执行。

固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。本卡全文阅读三族Host定义、tiling/数据结构、Torch adapter和device dispatcher，RmsNormCast另读两个实际kernel header；读取layernorm.py225行及必要有界caller/binding片段。总选定34来源3186行，服务框架接入合同。AddRmsNormBias的主要Device模板、编译器/平台库、完整API executor和运行环境仍未闭合，没有发布Operator或source_closed声明。未执行编译、UT、模型、NPU、图、数值或性能测试，保持draft与空平台。

通用图抽象错误见[lowering与Meta排障](../../runbooks/precision/custom_op_graph_lowering_converter_meta_correctness.md)，结构门禁见[Host shape约束](../../runbooks/compilation/fused_op_host_tiling_hardcoded_shape_whitelist.md)。这些跨版本经验不能替代本卡固定Main的实际实现。

## 三个输出ABI与模型消费者

| 入口 | 实际返回 | 接入时要保留 |
| --- | --- | --- |
| npu_add_rms_norm_bias | y、FP32 rstd、残差相加结果x | y与residual是两条状态；rstd保留归一化轴为1 |
| npu_rms_norm_cast | 输入低精度的y、同shape FP32 y_fp32 | FP32结果来自已舍入y再拓宽，不是独立高精度RMSNorm结果 |
| npu_rms_norm_dynamic_quant | INT8 y_out、FP32 per-row scale_out | 真实量化数据与每行scale一起送量化matmul |

AscendRMSNorm有residual时启用custom op并取三元组中的第一和第三项；无residual时走torch_npu.npu_rms_norm，只有bias_loaded才补加bias。量化描述出现norm.bias会创建bias Parameter，loader完成才设置bias_loaded；仅分配零Tensor与真实加载是不同证据。描述扫描按dict对象身份缓存，原位改写同一描述对象不会自动重算缓存判据。

AscendGemmaRMSNorm传入1+weight；有residual时按enable_custom_op选择自定义融合或torch_npu.npu_add_rms_norm，无residual另走DeviceOperator。不能直接把普通RMSNorm的gamma复制到Gemma路线。AscendRMSNorm构造器还接受var_hidden_size，但本卡所读融合Host以gamma覆盖的尾维计算D；新结构仍须证明所需归一化集合与此一致。

DeepSeek V4/V4.1的rms_norm_cast消费者需要(normalized, normalized.float())用于routing。实际kernel明确先产生FP16/BF16 y，再Cast到FP32输出，保持与原RMSNorm后float的离散值一致。替换为“更高精度、尚未舍入的结果”可能改变HashTopK输入，不能当无语义影响的优化。V4.1通过DeviceOperator能力和op存在性检查，可返回None再用普通norm；V4本地caller的门禁不同，不能共用一个缺省回退结论。

DSA的动态量化Q路径把qr和qr_pertoken_scale同时交给npu_quant_matmul，并显式要求模型输出dtype。只接INT8数据、漏per-token scale或把scale并入权重scale，均改变协议；scheme存在不意味着所有DSA或模型都使用这条分支。

## 当前Main的Meta dtype静态不一致

csrc/torch_binding.cpp的npu_rms_norm_dynamic_quant_npu用empty_like(x, dtype=at::kChar)分配INT8输出；同提交torch_binding_meta.cpp的npu_rms_norm_dynamic_quant_meta仍直接empty_like(x)，继承FP16/BF16输入dtype。二者是静态可见的不一致，本次没有运行图模式复现，也没有在此修改上游。

该Meta的scale用符号shape并显式FP32，移除x最后一维；AddRmsNormBias Meta将归一化尾维置1且显式FP32 rstd，RmsNormCast Meta显式构造FP32第二输出。Meta注册能让图推导获得输出结构，但不会自动证明真实dtype、可选输入、数值和runtime guard等价。旧Issue记录修法不代表当前固定Main已经包含修复。

排查eager正常而compile/graph错误时，依次对齐Torch schema、实际返回dtype/shape、Meta和GE/OpDef原型。不能靠把下游要求改为错误Meta dtype来消除报错；需要在对应上游修复与图/eager数值验证后再使用。其余自定义算子的Meta不得从本次三项局部阅读推定正确。

## DynamicQuant：Torch两输出与底层四输出

Torch wrapper只暴露smooth_scale、beta、epsilon，要求x/gamma非空、gamma为1D且匹配x末维、epsilon>0及x为FP16/BF16。它向底层固定传smooth_scale2为空，output_mask和dst_type空指针，分配INT8 y1及占位y2、两组FP32 scale，只返回y1和scale1。不能由底层存在第二分支或INT4选项推导Torch入口能返回双份量化或任意dst dtype。

OpDef注册y1/y2为INT8或INT4；proto文字和枚举还提到FP8/HIFLOAT8，但已读tiling的合法输出列表只含INT8/INT4且要求二者dtype相同，真实Torch wrapper又固定INT8。错误文本中出现hifp8不能推翻实际检查。OpDef仅声明ascend910b和ascend910_93，不能由proto枚举扩展950或其他平台支持。

Host要求gamma1D并与x末维一致，定义N为前导维乘积、D为gamma元素数。smooth存在性以非空shape判断，存在时shape须等于gamma；无明确两元素output_mask时，两flag设为-1，此时拒绝smooth2存在但smooth1不存在。beta的存在标志、smooth和output mask分别参与资源/工作区决策；已读Host没有完成所有beta形状/dtype或输出形状校验，caller仍应按真实算子合同准备，不能依赖任意非法输入都被一致拒绝。

D按INT8的32元素或INT4的64元素取对齐宽。tiling按UB容量依次尝试Normal、SingleRow、SliceD，key分别1/2/3；Normal每次最多16行，SingleRow一次1行，SliceD用固定8832(INT4)或8864(其他)列长度切分。常量是当前实现资源策略，不能直接修改成新模型hidden size或当任意硬件的最优tile。

Normal/SingleRow workspace为库系统需求加1字节user量；SliceD为系统需求加useCore×D×4×workspaceRowsNum，其中workspaceRowsNum依据output flags和smooth是否存在选择1或2。应记录真实N/D、flags、useCore与选择的key，不用shape总字节估算取代该额外分配。dispatcher有key0 no-op，但本Host计算的isEmptyTensor未用于走该key；Torch已拒绝空输入，不能把no-op分支当对全层空Tensor的统一支持。

## AddRmsNormBias：尾维集合、beta和平台分派

输入x1/x2 shape相同；gamma可覆盖一到多条尾维，x/gamma rank须满足1<=gamma rank<=x rank<=8，所有x维非零。输出y和残差x保持输入shape，rstd保留输入rank并将归一化尾维置1。Torch adapter与Meta按同样的shape构造，不能把rstd随意压为每token一维后接所有消费者。

950的OpDef为ascend950指定add_rms_norm_bias_apt文件。Host在扣除legacy UB reserve前根据SoC分派到独立arch35 tiling，不能把A2/A3 key/tiling结构直接用于950。950还明确检查输入输出dtype匹配、FP32 rstd、beta与gamma同shape/dtype、epsilon有限且非负，以及正维度、地址乘积和N/D uint32范围。

legacy key=dtype_key×10+mode，dtype_key为FP16=1/FP32=2/BF16=3，mode为Normal/SplitD/MergeN/SingleN/MultiN。beta是否为None改变UB阈值；小D、单行或对齐多行有不同路径。只有某些910B形状置performance flag，它既不覆盖整个后端，也不构成实测加速结论。部分310P分支和编译guard可见，不代替其公开OpDef或实际构建支持。

950使用独立key1000全行加载或2000 SplitD和对应数据结构。全行rowFactor受UB、blockFactor、uint16循环及FP32局部offset约束；SplitD按512字节对齐与实际队列/临时buffer计算tile，并拒绝不能装入UB或字段范围的配置。两种key的字段布局与legacy不同，不能仅放宽shape白名单而复用旧结构。

该族Host申请16MiB系统工作区加256字节user量；这不等于整模型峰值或每次真实新分配。dispatcher读取可选beta并把nullptr_beta带到具体实现，但主要Device模板与arch35依赖未在本卡全部展开，因此不对完整搬运、同步、精度与所有tail声明闭合。

## RmsNormCast：单行UB门禁与舍入语义

Torch bridge要求x为FP16/BF16且与gamma同dtype，gamma1D匹配x末维。Host进一步拒绝空Tensor，D向16元素对齐，以aligned_D×12字节和1024字节reserve限制单行UB容量；大于容量直接失败，没有DynamicQuant那样的SliceD回退。输出workspace为0，不能由此推导kernel没有UB、临时Tensor或框架开销。

Host epsilon允许0但拒绝负值；DynamicQuant要求严格大于0，950 AddRmsNormBias另检查finite。不同入口的guard强度不能合并成一条无条件规则。RmsNormCast Host用uint32存N/D/rows_per_core，不能从总shape能表示推导任意巨大尺寸都不会窄化。

RmsNormCast dispatcher用FP16 key1/BF16 key3；OpDef只注册910B和910_93，BF16还有特定架构编译排除。实际kernel每core分配输入/权重低精度buffer、两个FP32列buffer及64个FP32 reduction值，串行处理本core行，并显式安排搬运/Vector事件。FP16在norm后先cast再乘gamma，BF16路径先做FP32乘gamma再按RINT cast；随后FP32输出一律拓宽已经舍入的低精度结果。不能由这些路径推导它与任意框架RMSNorm实现逐位相同，仍需目标版本数值验收。

## 构建、图与验收顺序

三族CMake都经add_modules_sources和aclnn类型接入，build flags决定是否收集Host；部分族关闭cce-auto-sync，DynamicQuant还启用relocatable kernel binary选项。编译选项存在不证明已装出该算子，也不能据此删除Device中的显式事件。Root构建、生成aclnn executor、对应CANN版本及实际动态库仍需单独核对。

先确认模型实际层与patch路径，记录需要的residual、rstd、量化scale和routing语义；再核对dtype、shape、epsilon、可选参数、tiling key、UB与workspace。随后验证普通/融合、eager/compile、目标图、N/D边界、有无beta/smooth及实际支持平台的数值和输入不变性，最后测端到端时延与峰值。Meta dtype不一致、未知key、UB拒绝或归一化集合不同应先闭合正确性，不能靠改模型结构、丢scale或强制layout隐藏。

本卡此前Device阅读解释dispatcher和RmsNormCast输出语义；下文继续吸收DynamicQuant六份完整Device正文。AddRmsNormBias其他模板、完整primitive/编译执行族、CANN runtime与算子ABI没有完整Operator闭包。未执行Lint、上游UT、真机或性能实验，也未填写verified。


## DynamicQuant Device：数学、输出分支与访存合同

追加同一固定Main的base/helper/reduce及Normal、SingleRow、SliceD六份完整正文，使用去注释/空白的C++全文件投影，保留实际条件、数学、队列和指针运算。归一化先把输入转FP32，求`rstd=1/sqrt(sum(x*x)/D+epsilon)`，乘gamma、可选加beta，然后独立按smooth1/smooth2生成量化分支。名字中的Add不表示本族额外接收residual x2；其输入ABI仍以上文Torch/OpDef为准。

每行量化以目标127(INT8)或7(INT4)除以该分支abs最大值取得乘数，把倒数作为FP32输出scale；随后FP32→INT32 RINT→half→目标整数TRUNC。它不是直接向INT8截断，也不是MXFP的分组尺度。当前ScaleTensor没有amax=0或非有限值的显式保护：全零、NaN/Inf、极小值、饱和与ties必须单独验证，不能从epsilon>0推导量化阶段一定有限。epsilon约束的是RMS分母，不能保证gamma/beta/smooth之后amax非零。

旧协议由两flag均为-1标识；第一分支总交付，第二分支只在smooth1/smooth2均存在时交付。新协议按outQuant1/2Flag==1分别交付，beta和两组smooth各有存在标志。disabled输出不保证内容已初始化；不要从分配了四个底层Tensor推导四者都可消费。INT4通过半字节长度和偏移打包，DataCopyEx对INT4计算len/2字节；新D或奇数尾部不能照INT8的字节跨度直接移植。

| Device分支 | 资源/访问特点 | 优化时不能遗漏 |
|---|---|---|
| Normal key1 | 每loop多行，FP32 x/y列buffer、低精度权重、两组per-row scale；weights先加载，逐行reduce真D，copy按对齐stride排布 | 真D与DAligned不同；对齐padding不能进入归一化或amax。队列Tensor Free后才能安全复用 |
| SingleRow key2 | 每次处理一行，scale按128行分组后批量写出；可选beta/smooth复用输入队列 | 与Normal不是只改rowStep的同一实现，producer/consumer和gamma数据流需要独立核对 |
| SliceD key3 | 三轮：分片求平方和→分片norm/smooth与全行amax→从FP32 workspace再读并量化写出；每core一或两行D大小的workspace | slice不是独立归一化域；全D共享rstd和amax，多输出的workspace步长、tail与每行复用顺序必须一致 |

源码显式使用PIPE_V、V_S/S_V、MTE3_MTE2和队列EnQue/DeQue约束搬运与标量/向量交互。SliceD的FP32 workspace是跨轮状态，不能因为外部kernel参数未显式返回它而提前复用或跨stream消费；本地PipeBarrier也不是外部多stream的完成通知。

## key2/key3的静态缺口先于性能调优

固定ceac的SingleRow有两项明确需要回查的数据流：`xBufFp32`只InitBuffer了DAligned个float，ComputeRmsNorm却取`xLocalFp32[DAligned]`作为gammaLocal；当前CopyInXAndGamma把低精度x/gamma放进输入队列，而随后Cast只覆盖x的D元素，未见向该FP32 gamma view填充的步骤。不能把超出声明buffer范围的view当作已经转换好的gamma或依赖相邻分配碰巧含正确值。

同一SingleRow中，CopyInSmooth仅在oldDouble/newSingleSecond条件成立才EnQue smooth2，但ComputeDynamicQuant先无条件`DeQue<T>()`作为smooth2Local。没有第二smooth分支时，静态producer/consumer不配对；已有Host选择key2、旧协议默认flags和正常Tensor形状不能消除这项待验证条件。

SliceD的Process首轮调用CopyInX与ReduceSquareSumSlice；后者只完成cast、平方、reduce。第二轮CopyInTmpX从workspace读取原FP32 x，但本文件中负责写原x到workspace的CopyOutX只有定义，没有Process调用。后续norm/smooth虽会覆盖workspace，也不补上首次读取的数据来源。不能仅凭Host分配了足够workspace就认为其内容已准备好。

这些是完整静态正文中的缺口，尚未运行SDK/NPU复现，也未修改上游。适配Agent遇到key2/key3时应核对实际安装源码/二进制是否同版本、确认相关写入/队列是否已修复，并做gamma非单位、无smooth2、多行tail和跨slice的数值/内存验收；在这些事实未知时不要直接给出性能可用结论。Normal和其他融合RMS族仍须独立数值验证，不能因为这里指出局部风险就推导它们已经通过或同样失败。


## AddRmsNormBias Device：分支、舍入与归一化域

继续同一固定Main的12份AddRmsNormBias Device/header，整文件结构投影检查定义、条件、常量和调用，再直接展开legacy残差/归一化/输出、SplitD两轮、arch35全行与分片、Newton-Raphson和归约选段。来源表保留raw_full=false，表示已提炼下列具体facet而非逐行完整Device语义闭包；没有发布Operator、执行SDK/NPU或证明所有模板实例可达。

本族不只是`rmsnorm(x1+x2)`一个无舍入实数公式。三输出仍为归一化y、FP32 rstd和低精度/原dtype残差x；gamma和可选beta属于归一化后的仿射层，不能把beta融合到残差x2。理想归一化关系是`rstd=1/sqrt(sum(z*z)/D+epsilon)`、`y=z*rstd*gamma+beta`，但实际z取自哪次转换、何时舍入和归约树由具体分支决定。

| Device文件 | 真实职责与关键合同 |
| --- | --- |
| `add_rms_norm_bias.h` | Normal逐行处理，gamma/beta先装UB，按rowFactor聚合rstd写回；FP16先以half相加再拓宽归约，BF16先转FP32相加并另写回RINT残差，后者的当前FP32和仍用于该Normal归约 |
| `add_rms_norm_bias_merge_n.h` | 合并多行、区分列对齐与非对齐拷贝；rstd按真numCol归约，用row-broadcast乘回，repeat分组和尾行另处理 |
| `add_rms_norm_bias_multi_n.h` | 多行列buffer与rstd按块布局，Gather/广播恢复每行系数；body repeat、tail和实际numCol均参与运算，不能把numColAlign当归一化D |
| `add_rms_norm_bias_single_n.h` | 单行路径按FP16/FP32/BF16分别实现，使用固定195584字节unit buffer与显式事件；BF16残差相加后先RINT再拓宽用于归约，不能沿用Normal中未舍入FP32和的数值假设 |
| `add_rms_norm_bias_split_d.h` | 首轮逐slice写残差x并累积全D平方均值，得到一次rstd；第二轮从已写残差x读回分片，再乘gamma/可选beta并写y。不是各slice独立RMSNorm |
| `reduce_common.h`与`rms_norm_base.h` | 真D/尾部归约、半区折叠、FP32 repeat与block归约、对齐/非对齐DataCopy及架构guard；ReduceSumCustom当前委托ReduceSumFP32，不由名称推导固定二分树或跨架构逐位结果 |
| `arch35/add_rms_norm_bias_regbase.h` | 全行寄存器路线同时保存FP32残差和与T型残差输出，以FP32和求平方归约，再调用带avgFactor的Newton-Raphson rstd；按行/列mask及两行unroll生成y |
| `arch35/add_rms_norm_bias_regbase_split_d.h` | 先多级累积各slice平方和并取得全D rstd，第二轮重新读x1/x2形成FP32和，随后同时生成x与y；不同于legacy SplitD第二轮只读已舍入残差输出 |
| `arch35/add_rms_norm_bias_regbase_common.h` | x1/x2加载转换、主块/剩余块平方归约和含beta/无beta的y生成；powerSplit、tail和分级buffer不是任意hidden size可省略的细节 |
| `arch35/deps/reduce_common_regbase.h` | 寄存器load/cast/store、按向量长度选择归约、多级rstd与Newton-Raphson修正；FP32→B16 trait明确RINT/NO_SAT，分支还处理源码POS_INF与0条件，具体primitive语义须对齐目标SDK |
| `arch35/deps/rms_norm_regbase_common.h` | 对齐搬运、分层reduce、直接sqrt/div rstd和gamma/Gemma辅助模板；共享头存在Gemma/FP8名称不证明本AddBias caller实例化或开放这些额外协议 |

legacy的FP16 y在乘rstd后先cast回half，再以half乘gamma并按需加beta；BF16 y则先RINT到BF16、拓宽FP32乘gamma/加beta、最终再RINT。MergeN/MultiN也有先舍入残差再拓宽求rstd的分支。这些中间舍入、与Normal BF16未舍入FP32和的差别，意味着切tiling或替换为全程FP32后一次cast未被证明逐位等价。应使用非单位gamma、非零beta、接近舍入边界及大动态范围数据分别核验，而非只用零值或同一个实数公式判断融合正确。

SplitD的归约必须跨完整D：legacy先将每slice平方乘全D的avgFactor，再累加；arch35先累积平方和后统一乘avgFactor。两者epsilon只在整行归约后加入，不应每slice分别加epsilon。arch35全行使用Newton-Raphson辅助，而SplitD走所读ComputeRstd中的sqrt/div；不能把相同epsilon和输出dtype推导为相同中间精度。

legacy与arch35 SplitD还有显著生命周期差异：前者第二轮从输出x读回，后者重新读取x1/x2并在后半轮才输出残差。因此输入与输出存在alias、图重放中复用、跨stream读残差或将输出提前暴露给后层时，必须按选中key的真实读写序列验证，不能只看三输出shape相同。当前Torch adapter通常新分配输出并不自动给任意底层ACLNN调用者提供相同alias保证。

对齐padding只服务搬运和寄存器mask，不是额外归一化元素。arch35 SplitD对32字节搬运和512字节计算跨度间的尾部显式补零，分级reduce按tail所在半块选择组合；全行路径按真numCol更新mask。迁移新D/新UB策略须同时检查padding、reduceNum、gamma/beta地址、rstd行偏移与输出拷贝长度，不能仅调整Host字段或扩大一个buffer。

源码中的EnQue/DeQue/FreeTensor、MTE/V/S事件和LocalMemBar是局部生命周期协议，不是外部stream消费者已经完成的证据。特别是Normal FP32 Compute重新Alloc输入queue Tensor，以及MergeN/MultiN持有xLocal后将其输出queue交付并释放的模式，重排/增加分配前须核实队列存储重用假设；本次没有运行并据此宣布内存错误。完整模板可达性、外部primitive、alias合法性、NaN/Inf/溢出、尾块数值、图与性能均继续保持未执行边界。
