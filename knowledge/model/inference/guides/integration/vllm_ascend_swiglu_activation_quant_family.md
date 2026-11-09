---
type: Guide
title: vLLM Ascend独立SwiGLu激活量化族：分组、精度与UB执行合同
description: 对照固定Main的DequantSwigluQuant与SwigluGroupQuant，区分计数group_index、static/dynamic与FP8/MX模式、clamp和glu默认值、scale布局、UB整行及分列workspace、cast精度与ping-pong事件；识别950注释注册和缺失arch35实现边界，指导新MoE模型激活接入与性能诊断。
  3164固定delta修正GroupQuant同一行四个packed store共用tail计数，避免各自重新从整行宽度消费mask。
aliases:
- DequantSwigluQuantDskTiling
- DequantSwigluQuantTiling
- DequantSwigluQuantV35DskTiling
- SwigluGroupQuantTiling
- DequantSwigluQuantDynamicPerformance
- SwigluFp8QuantPerToken
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.mixture_of_experts
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/dequant_swiglu_quant_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/dequant_swiglu_quant_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/dequant_swiglu_quant_proto.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/dequant_swiglu_quant_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/dequant_swiglu_quant_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/dequant_swiglu_quant_tiling_arch35.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/dequant_swiglu_quant_tiling_base.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_host/swi_glu_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_cut_group.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_dynamic_base.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_dynamic_bf16.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_dynamic_bias_float.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_dynamic_bias_int32.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_dynamic_performance.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_static_base.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_static_bf16.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_static_bias_float.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant_static_bias_int32.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/tiling_base/error_log.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/tiling_base/static_register_symbol.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/tiling_base/tiling_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/tiling_base/tiling_templates_registry.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_swiglu_quant/tiling_base/tiling_util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_host/swiglu_group_quant_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_host/swiglu_group_quant_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_host/swiglu_group_quant_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_host/swiglu_group_quant_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_kernel/swiglu_fp8_quant_per_token.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_kernel/swiglu_group_quant.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_kernel/swiglu_group_quant_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_kernel/swiglu_group_quant_perf.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/swiglu_group_quant/op_kernel/swiglu_mx_quant_perf.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/version.info
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/moe/swiglu_group_quant/op_kernel/swiglu_group_quant_base.h
  role: primary
created_at: '2026-11-03T05:23:33Z'
updated_at: '2026-11-03T05:23:33Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---
# vLLM Ascend独立SwiGLu激活量化族：分组、精度与UB执行合同

## 接入前先固定实现和参数语义

本文提取vllm-ascend固定Main `ceac1a2`的两族独立激活量化实现。输入通常是前级GMM的`[...,2H]`结果，输出是后级GMM消费的`[...,H]`量化激活及scale。它们不包含前级矩阵乘，也不自动证明某个Python模型已调用此本地算子。GMM融合执行见[GMM与SwiGLu融合族](vllm_ascend_gmm_swiglu_execution_family.md)，SiTU的不同激活/scale合同见[SiTU接入](vllm_ascend_situ_quant_host_contract.md)。

| 固定Main实现 | 本地注册与输出 | 分组和选型重点 |
|---|---|---|
| `DequantSwigluQuant` | 活跃OpDef为`ascend910b/ascend910_93`，FP16/BF16/INT32输入，INT8输出和FP32 scale | 无group通常走legacy static/dynamic；有group或INT32且`swiglu_mode=1`走Dsk模板 |
| `SwigluGroupQuant` | OpDef只注册`ascend950`，FP16/BF16输入，FP8 E4/E5输出，FP32/E8M0 scale，可选y_origin | `quant_mode=1/2/3`为本地三条路线；group只裁剪有效token前缀 |
| `DequantSwigluQuantV35*`、APT router | 本地存在arch35 Host及156个编译期分派分支 | 950 OpDef配置在本commit整段注释，APT引用的五个`arch35/*.h`在该目录不存在，不能据此宣称可编译/可调用950实现 |

CANN自有Operator卡来自另一个固定ops-nn快照，模式编号和能力更广；例如[SwigluGroupQuant 950](../../../../ops/ascendc/operators/aclnn/nn/activation/swiglu_group_quant_950.md)中的mode 0/1和HiFp8路线，不能直接套到这里的mode 1/2/3。`csrc/version.info`声明源码构建输入为9.1.0且相关依赖要求>=9.1.0；这不是对本机SDK、实际安装算子或编译结果的验证。

## INT8族：路由、形状与参数顺序

`TilingForDequantSwigluQuant`调用本地`TilingRegistry`，按priority从小到大尝试Dsk=0、legacy=1、V35 last=1000、V35 non-last=2000。通常只有`GRAPH_PARAM_INVALID`继续下一模板；`GRAPH_FAILED`会中止。`TilingBaseClass::DoTiling`按shape/attrs、platform、IsCapable、具体tiling、workspace、PostTiling推进，不能把一次shape失败当作自动回退到安全实现。Dsk将真正参数检查放在其后续内部流程，IsCapable按是否存在group或INT32 mode1判断。

legacy按最后轴切成两半，要求rank>1且尾轴偶数。INT32必须有FP32 weight_scale，元素数2H；可选FP32 activation_scale每行一个；bias可INT32/FP32/FP16/BF16，元素数2H。quant_scale为FP32标量或H通道；static带scale时还要求FP32 quant_offset。legacy将quant_mode转小写，Dsk则使用大小写敏感的`static/dynamic`映射。输出shape不匹配的某些legacy检查只记日志，不能将Host返回成功视为完整输出验证。

Dsk只接受INT32/BF16，输入2H须可被64整除，不对H任意偶数直接兜底。INT32的weight_scale为`[2H]`、`[1,2H]`或每专家`[E,2H]`，activation_scale仍按全局有效行取值。BF16不执行INT32反量化，不能因此把INT32所有可选参数的效果类推到BF16。

INT32计算顺序取决于bias dtype：INT32 bias先加到整数累加值，再转FP32并乘weight_scale和可选token activation_scale；浮点bias在这些乘法之后相加。交换顺序会改变数学含义。BF16只转FP32后进入激活。参数按expert一次入队、转换并保留到该expert的各UB行块完成才释放，不能在处理同组期间覆盖scale/bias缓冲。

普通激活为`a/(1+exp(-a))*b`，`activate_left`决定哪半为a。Dsk mode1仍从左右半区Copy，不按POD注释自动改成奇偶交错布局；其数学为：a只截上限c，b夹到[-c,c]后加glu_bias，再计算`a/(1+exp(-glu_alpha*a))*(b+glu_bias)`；clamp_limit=0不裁剪。实际OpDef的glu_alpha/glu_bias默认值是1.0/0.0，proto注释和Host缺属性时fallback却是1.702/1.0。模型要求GPT-OSS式参数时应显式核对调用值，不能依赖名字相同就继承另一默认值。

### 分组编码与容量尾部

Dsk一维`group_index`直接当每专家的**行数count**；二维为`[expert_id,count]`对，使用expert_id索引scale/bias参数，按输入对的顺序累加数据行偏移。普通分核遇负count将其置0；二维遇非正count停止。cut-group模板按expert轮转分核，另一条路径把同一expert的行分到多核。两者对异常count的保护不完全相同。

这不是GMM V1/V2 `group_list_type=0`的累计边界编码。普通Dsk只检查开始偏移小于总容量，没有对整组count进行剩余容量截断；cut-group也没有完整容量检查。调用方必须保证非负计数、合法expert_id及总有效行不超输入，且确认未覆盖输出尾部由谁初始化/屏蔽，不能把未写尾部直接送入下一GMM。

### static与dynamic不能共用scale解释

Dsk dynamic可选quant_scale是激活之后的smoothScale，按`[H]`/`[E,H]`乘入，再逐行取absmax，输出scale=`amax/127`，最后除该scale。所读Dsk及legacy动态body没有SiTU K3的零scale置1保护；全零、NaN/Inf需独立参考验证。

static则执行`activation/quant_scale+quant_offset`，标量路径先计算scale倒数，通道路径向量除法；它不写动态scale输出。Dsk static要求scale/offset成对且dtype一致，可FP32/FP16/BF16，支持每组标量或每组H通道。Dsk无group编译入口向body传入nullptr bias/offset，不能因Host接受某组合便断言这些参数确实消费；尤其无group mode1叠加static或bias需要沿真实entry验证，不擅自补齐遗漏实参。

Dsk的最终cast链是FP32→INT32 RINT→FP16 ROUND→INT8 TRUNC；legacy静态/动态则为FP32→INT16 RINT→FP16 NONE→INT8 NONE。相同输出dtype不等于逐位一致，禁止用单一INT8参考替代各条实际舍入链。

## INT8族：UB、workspace与事件

legacy为每核分配连续若干行，整行可装UB时保留两半输入、FP32激活、归约和输出队列；大H时按列切片，先把每片SwiGLu写入本核独占workspace，求完整行amax，再读回各片统一量化。MTE3_MTE2事件保证中间写完成后才回读；这种额外GM流量只存在对应分列路线。

| 路线 | Host资源与执行约束 |
|---|---|
| legacy dynamic BF16/FP16 | 每输出元素基础UB预算25B；可整行多行装载 |
| legacy dynamic INT32 | 基础45B，FP16/BF16 bias额外4B；不能只按INT8输出估UB |
| legacy static BF16/FP16 / INT32 | 基础29B / 49B；16bit bias在INT32路径再加4B |
| legacy workspace | 16MiB系统预算；动态分列再加`usedCoreNum*H*4`用户中间区 |
| Dsk | 预留1024B UB，整行尺寸必须进入其预算；workspace固定32B，不能继承legacy的分列兜底 |
| legacy key30013 | 对齐、H<=1536、单行且整行载入、无bias、activation_scale存在等条件命中；名字Performance不是实测收益 |

key30013实际用输入A/B与输出的ping/pong TBuf和EVENT_ID0/1，按MTE3_MTE2→MTE2_V→V_MTE3顺序交接，最后排空两事件。它把weight/quant scale先搬到复用TBuf，依赖Host的窄门禁；不能去掉门禁后套到bias、列切分或任意多行。普通模板的queue实际多为深度1，POD里`isDoubleBuffer`字段不代表每条Device路线都真正双缓冲。

entry即使只计算UB，也先检查workspace和GetUserWorkspace非空；32B不是可以传nullptr的许可。图执行时输入、输出、tiling和workspace要覆盖stream实际使用期间；本文未证明外部executor分配和多stream并发生命周期。

## FP8/MX族：三模式和有效token裁剪

本地`SwigluGroupQuantTiling`要求2H为偶数，mode3额外要求2H%256=0。Host没有消费group_size来通用化tile，而是mode1/3固定128输出元素一scale、mode2固定32元素一MX scale。dst_type参与InferDtype，Host选路本身不据它生成任意精度实现；必须同时核对输出tensor dtype和编译实例。

| 本地quant_mode / key | 数值与scale | 附加约束 |
|---|---|---|
| 1 / 1 | FP32 SwiGLu，可clamp及乘token topkWeight；每128元素求scale，再转换FP8 E4/E5 | Host称STATIC_QUANT，但scale由当前激活计算，并非checkpoint静态量化；转换使用NO_SAT、RINT及特殊值选择逻辑 |
| 2 / 2 | SwiGLu先落FP16/BF16，再每32元素提取max exponent，E8M0 scale成对打包，FP8输出SAT、RINT | FP16路径用FP32逆scale乘法，BF16路径先以BF16乘，再转FP32；不能假设相同中间精度 |
| 3 / 31或32 | 名称PerToken，实际仍以128元素块归约；amax下限1e-4，除数固定448 | round_scale决定普通FP32 scale或按位构造2次幂；ue8m0影响scale类型；key32另写激活后的y_origin |

mode3不能因E5也在OpDef就把448改释为E5范围；`round_scale=false`与E8M0输出的组合在body里也没有充分类型安全证明。mode1/2不走key32的y_origin写入逻辑。y_origin是clamp、SwiGLu及可选topkWeight之后、量化之前的值，并非原始x或前级GMM结果。

`group_list_type`只允许0，Host明确其语义为count。各核先把group_index求和并V_S同步取标量，然后令`realBs=min(sum,bs)`重算分核；它只控制有效前缀，不按expert_id选不同量化参数。sum没有下限钳制，负count、溢出及输出有效区外尾部需要调用方约束。group求和缓冲释放后重置UB pool再分配主激活队列，两阶段复用同一UB。

主计算x0/x1/y/scale等队列按实际分配深度2，带topkWeight时按行载入并跨列片复用。mode1/2采用row/d双维tile，mode3将round/clamp/topkWeight编码成8组模板，并分别实例化是否写origin。入口保存overflow控制位、临时清0，结束恢复；无有效计算的核也应保留入口的控制状态恢复。

## 静态诊断缺口与适配验证顺序

所读本地源码有几处不能直接用Host放行覆盖的边界：

- GroupQuant的大行UB不足分支以`totalSize>ubSize`进入，却在`totalSize<ubSize`时才迭代扩大base，随后由`base-1`计算dFactor。应先检查实际tiling输出是否为0、后续除模是否有效；本次没有真机复现，不能称已确认崩溃或安全回退。
- GroupQuant InferShape先`SetDimNum(1)`再Append前导维，且动态末轴直接返回；y_origin缺少对应完整推导。不要将其逻辑scale shape意图等同于每种rank实际生成的descriptor。
- MX Device把局部scale列数补偶数，但GM基址/行步长仍使用原scaleCol；H不满足对应分组/配对对齐时，需核对scale tail实际布局，不能只验证FP8数值。
- Dequant arch35 Host虽检查rank2–8、activate_dim、FP8/FP4和HiFp8等，但registry优先级、被注释的OpDef及缺失Device头共同阻止“分支存在即支持”的结论。其last-axis全载阈值H=5120；动态分列预算16MiB+每核H个FP32，non-last workspace32B，仅可作为已读Host设计边界，不能移植成已运行承诺。

新模型适配先固定实际operator symbol/commit/OpDef和路由，再记录2H布局、激活左右位置、mode、clamp/alpha/bias、group编码、有效M、所有scale dtype/shape及传参是否被实际entry消费。用非零参考验证bias顺序、全零、极值、NaN/Inf、FP8 E4/E5和INT8舍入差异，再检查非对齐尾部、UB阈值两侧、workspace及图重放/多stream寿命。正确性通过后分别测前级GMM、独立激活量化、后级GMM和通信时间；本文没有给出性能收益或所有硬件/模型适用证明。

源码表内梯度POD/梯度类声明和通用FlashAttention tiling-key helper不构成此推理前向族的算法，单独标skip，未冒充梯度算子摄取。外部AscendC API、生成ACLNN executor、缺失arch35技术体及完整CV/VV Operator生产仍待对应来源闭合；本文只交付实际读到的框架集成和Device执行语义。

## 固定3164增量：GroupQuant连续packed store共用尾计数

3164adc8fe75892fbf7f99f524bb72fddf1e6efd相对ceac的VFComputeData修订把四个独立curColNum计数改为每行一份remainingCols，连续四次UpdateMask依次消耗同一行的剩余列；内层循环索引也改为j。四个packed store处理同一行连续片段，旧四份各从完整宽度起算的mask可能覆盖相邻UB存储，不能以每次store本身对齐就忽略联合尾部。

这是当前固定程序diff支持的边界，不是运行中已观测的越界结果或新版本已通过证明。回移时保持四mask的生成顺序、同一remainingCols引用及行指针步幅，分别验不足一完整packed组、跨组尾列和相邻UB哨兵；其余Host准入、scale与dtype语义沿原版本节。
