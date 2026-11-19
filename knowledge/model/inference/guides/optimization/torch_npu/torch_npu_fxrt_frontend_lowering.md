---
type: Guide
title: FXRT前端降级：Schema匹配与算子语义边界
description: 区分FXRT原生映射、custom/Python回退、索引分解和元数据适配，保留归约、归一化及动态符号的版本限制。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_backend.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/copy_elimination.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/full_decomposition.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/decompose_impl.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/getitem_impl.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/setitem_impl.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/symbolic_shape.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/config/ascend/op_precision.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/op_precision_conf.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/op_precision_conf.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_config.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/ascend_device_context.cpp
  role: implementation
created_at: '2026-11-10T06:06:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT前端降级：Schema匹配与算子语义边界

## 固定来源与采用范围

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的完整fx_backend.py（3293行）、12份前端/精度辅助实现和设备上下文Initialize精确范围。这里只有静态降级合同，没有完整产品、配套矩阵及设备验证，保持draft、空平台；不回推发布快照，也不将映射表当成底层全部kernel的数值、训练或性能认证。

本卡回答“一个FX调用如何转换，以及会丢弃/改写哪些语义”。执行模式、捕获地址、Storage别名及输出复制另见[FXRT推理运行时](torch_npu_fxrt_runtime.md)。compiled_kernel_adapter、DVM/AutoFuse ABI及设备kernel仍须按各自实现核对，不能只靠前端调用顺序认证。

## 降级顺序和回退条件

backend先移除匹配的_log_api_usage_once节点，恢复compiled kernel参数布局，再消除限定copy_、分解full和选中的getitem/setitem；随后注册参数、算子、输出及pre-flatten钩子，并从TorchNPU读取精度配置。call_module明确NotImplementedError。placeholder的example_value若为Parameter才建参数节点，get_attr沿点分路径取对象转Value；不能从变量名字认定所有lifted权重都被识别为Parameter。

call节点优先尝试DVM原生降级，然后仅FXRT_AUTOFUSE_NATIVE精确1时尝试AutoFuse，再尝试通用compiled kernel。其余先查显式_OP_MAP，再按callable.__name__寻找Op枚举，否则custom_call；这只决定候选路径，不是所有同名接口都满足同一ABI。

后端check_op_support返回非零时改为custom_call并重新准备参数；**检查抛异常时打印错误后返回原op**，与函数注释所说“检查失败回退”不同。custom_call、python_call、DVM/compiled/AutoFuse等特例不经过同一检查。不能把日志中的检查失败当作已安全回退，或把没有报错当作产品/数值支持证明。

custom_call根据dispatcher/自定义注册表判定；已注册的名称和扁平实参交给对应调用，未注册则尝试python_call。Python路径用inspect.signature绑定实参和默认值，最终按位置调用；显式keyword-only参数和带kwargs的**kwargs路径会拒绝，取不到signature时保留原扁平实参。它不是任意Python函数、关键字、mutation或别名的透明兼容层；图捕获中还受运行时custom call更新限制。

## Schema匹配和标量参数

ATen overload/packet、Python builtin及字符串方法有不同Schema发现路径；部分算术overload会先转torch函数重新取候选。匹配按缺少参数、额外关键字、未填None默认等因素排序，校验kwarg-only、类型和参数消耗；失败错误包含原始/钩子后参数及各Schema原因。无Schema时仅保留args和kwargs的值列表，不能据此认定关键字语义已保留。

Optional/List、设备字符串、固定长度列表和整数到float的转换由本地适配器处理；view/reshape/repeat/permute/new_empty/new_zeros/expand等白名单方法，以及部分factory的散列尺寸会先装成列表。未知类型、example_value缺失时倾向兼容；全部显式实参均为标量时还跳过部分类型检查。这是overload选择策略，不是完整参数合法性校验，最终ABI与元数据仍须核对。

add/mul/eq的scalar-first形式可在Schema前交换；sub/div/floor-div的scalar-first tensor-second形式明确拒绝，避免交换改变含义。标量识别包含Python bool/int/float及SymInt/SymFloat和相应Node元数据，部分masked_fill/inplace_add钩子却使用更窄的Python类型判断，不应据一条二元路径推广所有符号标量操作。

clone参数钩子只保留输入，empty_like也仅保留self并依赖输出元数据；long/float/int分别补INT64/FP32/INT32。调用中出现memory_format、dtype、device等参数不表示所有参数都作为运行时实参逐项转发；确认metadata和真实输出布局，不能把接口存在当作所有重载等价。

## 形状、归约和归一化适配

| 入口 | 此提交的前端行为和边界 |
| --- | --- |
| sum/mean、amax | None或空dim扩成全rank维度；单dim装列表。sum/mean未指定dtype时钩子取输入dtype，不据注释泛化为PyTorch所有整型提升规则；应与example输出及底层实际结果比较。 |
| var_mean | dim规范化；correction默认1后int化、keepdim默认false后bool化。不同旧重载的位置参数和符号correction不由此自动认证。 |
| index.Tensor、index_put_ | 前者只删除indices尾部None，保留中间占位；后者补accumulate/unsafe默认false。它们不是统一去除全部None或任意高级索引支持。 |
| arange、prims.iota | arange按原调用补start=0/step=1并保留显式部分kwargs；iota只传length/start/step，dtype/device来自输出元数据，requires_grad=True拒绝。 |
| log_softmax | _log_softmax的half_to_float=True拒绝；指定dtype与已知输入dtype不同也拒绝，要求先有显式cast，不把输出dtype提示当计算精度转换。 |
| layer_norm | 规范到x/normalized_shape/weight/bias/eps，丢弃cudnn_enable；不由该前端钩子推定所有native_layer_norm多输出与训练合同。 |
| rms_norm | torch形式丢normalized_shape，传x/gamma/epsilon；适配后端(y,rstd)并投影y，rstd为FP32的归一化轴保1形状。torch路径的输出钩子要求输入/输出/gamma均有Tensor元数据，weight=None等不能按通用torch签名默认认定可用。 |
| argsort | 规范stable/dim/descending顺序，用后端(values,indices)的索引1作为结果，不把values返回给torch argsort调用方。 |

permute/transpose/movedim根据example rank重排轴，movedim会规范负轴并检查重复和范围；t路径虽允许rank≤2，却统一返回[1,0]轴列表，0D/1D仍须单独核验，不由“≤2”检查宣称其等价恒等处理。squeeze默认dim扩全rank，真正是否去掉size1维由后端决定。

chunk没有独立runtime op，按example_value各输出的指定维尺寸构造split_sizes并保留SymInt尺寸；维度本身可能int化，输出个数和rank依赖元数据。split按第二实参为整数/SymInt选择split_tensor_view，否则保留split_with_size。view禁用开关仅对已注册非view回退的permute/split生效，不能当成任意reshape/slice零拷贝开关。

## CrossEntropy前向路线

cross_entropy的reduction字符串先转0/1/2匹配ATen Schema，再转none/mean/sum给后端；只支持class-index target，已知浮点概率/soft-label target拒绝。zloss相关参数固定0.0/false，不是开放的训练zloss接口。

二维logits直接使用；多维(N,C,D...)先将类轴置末，再展平到(batch,C)，target展平为(batch)，none reduction时loss再还原目标形状。多维路径将total count和类别数转int，需要可静态取得的元素量；后端四输出仅取loss，并不证明Autograd/反向已经接入。

源码一维分支在判断logits_dim==1前已经访问logits_example.shape[1]，与“支持1D”的注释不一致。本轮只记录这个静态路径，未运行触发；不能把注释直接作为(C,)输入的可运行方案。

## copy消除和索引分解的真实范围

eliminate_redundant_copy_只针对目的x是linear结果、非placeholder且不直接属于图输出集合的copy_。它把copy之后的x消费者改为源y，再erase copy节点；没有在这里完整处理所有alias、broadcast、dtype转换和copy结果自身的users。不能推广成“所有内部copy都冗余”，也不应靠该pass认证任意原地语义。

full.default只在至少有size/fill两个位置实参时改为zeros(size).fill_(fill_value)，dtype/device可从显式kwargs或example_value补，layout/pin_memory按已传项保留。该分解是支持路径转换，不是证明额外初始化没有成本或普遍比full更快。

FakeTensor分解白名单仅operator.getitem/setitem。tuple/list取项、元数据相同shape的getitem，以及同时含None/Ellipsis/slice的索引会跳过部分getitem分解。setitem的slice若含整数/SymInt边界或非恒定Node会强制分解；不能按注释把所有slice都直接交strided_slice_assign。

单op子图不接受kwargs，构建时就报错；make_fx追踪失败才保留原节点。内联主要支持单Node输出，复杂输出可能保留原节点；这个流程不自动证明所有复杂mutation和多输出结构都可下沉。实际过程依赖FakeTensor/example_value与PyTorch私有API，不能把静态检查成功写成设备执行。

直接getitem区分tuple/list、Tensor和索引类型：Node索引走axis0 gather；整数索引构造成slice范围并补尾维；slice/tuple使用begin/end/axes/steps。动态open end可用INT64_MAX表示，动态begin的int转换则可能专门化。None、负索引、降rank、Ellipsis及非连续Tensor是否完全保持Python语义仍由具体runtime算子与metadata共同决定，不凭前端构造的数组认证全部高级索引。

## 动态符号不是任意动态控制流

输入SymInt先注册，SymbolicShapeManager支持Symbol/Integer、Add/Mul/Mod/FloorDiv/CeilDiv及特化的Min，Floor/Ceil(IntTrueDiv)改整数形式；未识别表达式NotImplementedError。整数Pow按重复乘展开，不是任意幂/逆元实现。SymBool转成bool，SymFloat在utils中转float；这些结果可能是编译期值，不能当作运行时符号布尔/浮点控制流支持。

Tensor符号尺寸绑定IR symbolic_shape，嵌套list/tuple递归转Tuple；设备转换仅CPU/NPU/privateuse1的规范形式，layout和memory_format对象转空Value。缺失/未知元数据、符号算子和容器组合必须逐路径核对；符号维可表达不意味着捕获缓存键或所有shape guards已完整。

## 通信、MoE和FIA入口差异

utils只在torch.distributed已初始化时提取全局rank/world size、当前NPU及相关ProcessGroup，复用Torch的HCCL handle。vLLM all_gather要求常量字符串group_name、能解析到有效device_group；四参(tensor,dim,world_size,group)只接受dim=0并去掉dim，三参c10d形式保留。源注释对多机仍要求验证、只说明单机8卡的当前实现，不把获取handle当成任意拓扑/多机合同。

npu_moe_init_routing_v2映射到Op.moe_init_routing_v3，名字并非版本等价证明；GatingTopK重排bias/k等参数并把out_flag转bool，dispatch/combine v2按特定位置和关键字布局重排。dispatch输出钩子在第7输出expand_scales为空时按expand_x首维//tp_world_size重建metadata，无法解析或0的TP值按1处理；这是前端元数据修补，不代表任意TP、整除、量化或通信模式已被后端验证。

DequantSwiGLU原生钩子仅接quant_mode 0/1，并转static/dynamic字符串；swiglu_mode非0、clamp_limit/glu_alpha/glu_bias偏离7.0/1.702/1.0超过1e-6或无法解析时走custom_call。不能把V2控制参数存在理解为FXRT原生V2路径已完整支持。

FIA钩子把单份K/V包列表并按固定下标重排40个实参，RoPE钩子固定追加BSND布局标记1。它们不是任意新增dtype提示、layout、版本参数或公开算子产品矩阵的透传保证，须对照这个固定提交依赖的实际ABI，不与另一个主线头随意拼接。

## 精度选项和验证方式

backend从torch_npu.npu.matmul.allow_hf32及ACL_PRECISION_MODE读取并写入FXRT单例；设备上下文Initialize设置实际SocVersion。IsAllowFP32ToFP16默认按SocVersion<k910B1比较，must_keep_origin_dtype强制false、allow_fp32_to_fp16强制true，其他非空值只记录Unsupported后沿默认判断。该函数及枚举并非整卡产品支持表，也不说明所有op都消费同一精度选项。

采用前固定TorchNPU/PyTorch/CANN组合与完整FX图，核对实际原生/custom/Python路径、Schema和输出metadata；针对标量顺序、None默认、整数归约、cast、归一化辅助输出、多维loss、slice/tuple和动态符号逐项比较eager及参考结果，再测量pass前后节点、复制与性能。已有MLP前向例子不能覆盖本卡全部路线。本次没有导入源码、追踪模型或运行设备/分布式测试。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_backend.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/copy_elimination.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/full_decomposition.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/decompose_impl.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/getitem_impl.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/setitem_impl.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/symbolic_shape.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/utils.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/config/ascend/op_precision.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/op_precision_conf.h)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/op_precision_conf.cpp)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/common.h)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_config.cpp)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/ascend/ascend_device_context.cpp)（implementation）
