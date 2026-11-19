---
type: Guide
title: ATB RoPE：静态cos/sin缓存、长度失效与原地输出
description: 分开记录位置编码表和Operation缓存、两种排布、只按token数更新的长度状态，以及aot_eager测试的真实范围。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/RopeAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_rope.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/RopeAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_rope.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py
  role: implementation
created_at: '2026-11-11T04:11:18Z'
updated_at: '2026-11-11T04:11:18Z'
platforms: []
---

# ATB RoPE：静态cos/sin缓存、长度失效与原地输出

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。所列CPP逐对完整非注释token一致，完整测试AST亦相同；均是静态审阅，没有导入/运行上游、加载ATB库或执行设备、编译、捕获、数值和性能验收。整卡产品与完整配套未确认，保持draft、空平台，无新增verified。

[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)解释ParamSetter的contiguous、按请求转换ND、CPU clone、直接输出描述符和每次Setup/工作区/捕获分派。format_trans请求不能直接计为一次物理复制，Input准备也不代替调用方Output对象的连续性与别名合同。

## 准确入口与一次缓存的两种排布

`atb::_npu_rotary_embedding`在PrivateUse1注册，schema接收positions、可写query(a!)/key(b!)、head_size、cos_sin_cache和is_neox_style，返回()；Python API_LIST将其绑定torch_npu顶层。入口的OptionalDeviceGuard取positions设备，不能改写为query设备guard，也没有在这里完整核验所有输入同设备、索引有效或head维组合。

文件内的sequenceLength、previousTokenCount和四份cos/sin Tensor是static状态；previousTokenCount初始−1。InitializeCosSinCache先将cos_sin_cache沿最后一维chunk成cos/sin两半。普通两表分别repeat_interleave(2,dim=1)形成相邻元素重复，NeoX两表分别repeat({1,2})形成整半重复。这是这段代码实际使用的轴和排布，不是任意rank的通用Cache变换。

_npu入口只在普通cosCache或sinCache未defined时调用初始化；两份NeoX表同时在该helper中建立。后续调用没有按cos_sin_cache的新内容、对象身份、shape、dtype或device重新校验/刷新，也没有本地锁或thread_local限定。业务若更换位置编码基数、缩放策略、模型或设备，需明确该static状态的实际使用协议；不能把“传了新cos_sin_cache”直接当作本入口已重建表。这里记录可见缓存键，没有宣称已复现跨模型/多设备/并发错误。

## 每次positions选择与长度状态

每次调用都flatten positions，flatPositions.size(0)赋给int32 currentTokenCount；cos/sin按is_neox_style选择对应表，再index_select第0维取本次位置。表复用并不省略每次按位置选择得到的cos/sin准备。

sequenceLength只在未defined或previousTokenCount不等于当前token数时重建：先更新previousTokenCount，再以at::tensor({currentTokenCount},at::kInt).to(query.device())产生单元素INT32长度。该失效条件只看token数，没有把query设备或dtype纳入；相同token数的下一调用不在本地重做.to。size到int32的窄化也没有额外本地范围检查，实际positions/index_select和ATB消费者仍各有合同。

## RopeParam与输入输出

RopeParam.rotaryCoeff实际取NeoX时2，否则head_size；接口head_size为int64，而字段是int32。cosFormat保持头默认0，默认rotaryCoeff=4在本入口被覆盖。固定头说明hiddenSizeQ应为hiddenSizeK整数倍且hiddenSizeQ=headDim×headNum；rotaryCoeff注释列2、4或headDim/2，cosFormat为训练参数0/1。将这些声明与入口实际赋值分别保留，不能擅自把非NeoX的head_size改写成headDim/2，或从参数名推出任意维度都通过。

固定头的operator==同时比较rotaryCoeff和cosFormat；所读HashOpParam<RopeParam>只写rotaryCoeff，本入口cosFormat固定0。它与上文Tensor表缓存是两层状态：Operation缓存取RopeOperation，Tensor状态决定本次cos/sin/长度输入，不是缓存注意力结果或位置编码输出。

VariantPack依次Input(query,True)、Input(key,True)、Input(cos,True)、Input(sin,True)、Input(sequenceLength,True)，随后Output(query)、Output(key)，再RunAtbCmd。包装层不分配新Q/K输出，准确schema声明两对象可写别名；不能由内部可能生成连续输入副本推导任意非连续Q/K都能直接写回。

## 完整测试的参考与未覆盖条件

两版test_atb_rope.py完整AST相同。固定theta=10000、headDim128、heads32、maxPosition8192、batch1、seq4。compute_inv_freq计算1/(base^(arange(0,headDim,2)/headDim))；compute_cos_sin_cache对位置与频率einsum，再拼cos/sin并上NPU，默认FP32。参考_apply_rotary_emb把cos/sin扩头轴并转x dtype，分别组合偶/奇项x1*cos−x2*sin、x2*cos+x1*sin，再stack/flatten。native_rope按flatten位置取表，将Q/K view为[token,heads,128]，处理旋转段并拼回remainder恢复原shape；该fixture已把最后维view为128，remainder为空，不能由这个拼接写法单独证明任意部分旋转尾段可用。

普通用例Q/K均[4,4096] FP16，positions是NPU arange(4)，cache为上述默认FP32表，is_neox=False；与该参考比较原地Q/K。参考本身也调用NPU上的Tensor算子，不是独立CPU高精度证明。

compile用例内部RopeModel.forward调用同一入口并返回原Q/K；backend明确为aot_eager、fullgraph=True，使用克隆Q/K与Eager比较。skipIf采用torch.__version__<'2.5.1'的字符串比较，另有Ascend910B装饰器；不能把这个测试当作TorchAir/GE或任意图捕获已支持。两个用例均保持同一theta、维度、device和is_neox=False，没有设计覆盖NeoX、更换Cache、同token数跨设备、并发或大token数的失效条件。本次未执行这些测试。

## 固定证据

- [来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/RopeAtb.cpp)（primary）：1–93。
- [来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：494–518。
- [来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：127–132、142–148。
- [来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_rope.py)（example）：1–103。
- [来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py)（implementation）：11–30、103–132。
- [来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/RopeAtb.cpp)（implementation）：1–90。
- [来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：493–518。
- [来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：132–138、149–156。
- [来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_rope.py)（example）：1–103。
- [来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py)（implementation）：11–27、102–131。
