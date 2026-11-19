---
type: Guide
title: ATB分组路由：GroupTopk参数、原地输出与测试边界
description: 记录分组打分模式、整数窄化、固定索引输入、schema与原地输出差别，以及已跳过参考测试的实际范围。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/GroupTopkAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_group_topk.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/GroupTopkAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_group_topk.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py
  role: implementation
created_at: '2026-11-11T03:47:18Z'
updated_at: '2026-11-11T03:47:18Z'
platforms: []
---

# ATB分组路由：GroupTopk参数、原地输出与测试边界

两版固定提交分别为主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。下述CPP完整非注释token已逐对比较相同；测试只作静态参考，未导入或运行上游、加载ATB库或做设备测试。平台配套未完整确认，整卡保持draft与空平台，没有新增verified。

公共ParamSetter的contiguous、按请求转换ND、CPU clone、输出连续性检查，以及每次Setup、自动工作区、捕获分派和资源寿命复用[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。Input的format_trans=True表示请求，是否发生物理转换取决于实际Tensor；Output直接描述调用方对象。

## GroupTopk的参数窄化与原地输出

`atb::_npu_group_topk`注册PrivateUse1，schema为Tensor self、int k=0、group_num=1、n=1，返回()。CPP以self建立OptionalDeviceGuard，将group_num/k从int64窄化到int32_t，将n转uint16_t；groupMultiFlag先设UNDEFINED(0)，当原始int64 n>1才设SUM_MULTI_MAX(1)。本地没有范围或溢出检查，不能由enum/static_cast推导任意整数有效。

GroupTopkParam固定头声明：groupNum在[1,专家总数]，k在[1,groupNum]；SUM_MULTI_MAX表示每组取n个最大值求和，n范围[1,expert_num/groupNum]且只在该模式有效，UNDEFINED为每组最大值。schema的k默认0与头声明有效区间不同，调用者仍需给出有效组合。头中整除条款原文为“groupNum需要保证可以被inTensor0Desc.shape.dims[1]整除”；所选测试只生成expert_num的因子作为group_num，并reshape为[token,group_num,expert_num//group_num]，对应expert_num%group_num=0。保留该文字方向与参考实现的差异，实际组合按所配ATB核验。

包装层令out=self，没有新分配结果；另外每次构造arange(1024)，options继承self后明确设备为PrivateUse1、dtype为INT32。VariantPack依次Input(self,True)、Input(idx,True)、Output(out)。1024是这个临时索引向量的固定长度，不能单由这一常量宣布通用专家总数上限。连续化与格式转换可能产生输入准备成本，输出对象仍为self。

schema的Tensor self没有(a!)可写别名标记，而本地实现直接用self作输出，测试也检查调用后input0。应同时记录这个schema与实现差别；本次静态证据不能证明编译器的别名分析、自动求导或跨task更新已正确处理它。

OpParamCache<GroupTopkParam>以GroupTopkOperation取Operation；专用hash写groupNum/k/groupMultiFlag/n，再走RunAtbCmd。缓存的是Operation配置，不是这次self/idx的数据。Python API_LIST及转发/补丁把准确名字暴露为torch_npu._npu_group_topk。

## 测试参考覆盖什么

两版test_atb_group_topk.py完整AST相同，主线多许可证头。generalize_param枚举以下候选；group_num只取专家数因子，再滤掉k>group_num或n>expert_num//group_num的组合。

| 参数 | 候选 |
| --- | --- |
| token_num | 1、16、33 |
| expert_num | 1、4、15、16、17、32、65、128、257、1024 |
| k | 1、4、15、16、17、32、65、257、1024 |
| n（测试名k_inner） | 1、2、3、4、16、32、65、1024 |

golden_calc把输入reshape成分组，克隆原值，转FP32后在组内取top n再求和；以NumPy stable argsort按组分数降序排序，把top k以外整组原值置0，最后恢复[token_num,expert_num]。这是“保留选中组原元素、清零其它组”的参考，不是返回专家索引的接口。

设备测试遍历FP16/BF16，input0在[-2,2]均匀随机，调用后对input0与参考作assertRtolEqual；另分配output0但没有作为调用参数。整个测试明确标注unittest.skip("skip test_group_topk now")，同时带Ascend910B装饰器。文件导入numpy别名为nps，golden却引用np.argsort；当前文件没有np定义，因此取消skip前还需处理这个可见名字缺口。本次没有运行或修改测试，也没有把跳过用例当作数值验证或设备支持证明。

采用时核对实际self连续性/shape/dtype、窄化前后参数、输出原地行为、临时idx准备和准确schema；运行支持与数值/性能需要匹配配套的执行证据。

## 固定证据

- [来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/GroupTopkAtb.cpp)（primary）：1–57。
- [来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：292–340。
- [来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：89–97、142–148。
- [来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_group_topk.py)（example）：1–72。
- [来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py)（implementation）：11–30、103–132。
- [来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/GroupTopkAtb.cpp)（implementation）：1–62。
- [来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：293–341。
- [来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：91–100、149–156。
- [来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_group_topk.py)（example）：1–62。
- [来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py)（implementation）：11–27、102–131。
