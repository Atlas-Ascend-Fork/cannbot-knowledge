---
type: Guide
title: ATB专家路由：FusedAddTopkDiv参数、映射与测试边界
description: 固定普通/out路由接口及14实参，核对专家映射文档冲突、Meta与被跳过完整测试的实际参考和比较范围。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/FusedAddDivAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_fused_add_topk_div.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/FusedAddDivAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_fused_add_topk_div.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
created_at: '2026-11-11T04:51:24Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# ATB专家路由：FusedAddTopkDiv参数、映射与测试边界

本卡限定OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布dedc316708372c9a8bfde4527abd2a94b74840f5的FusedAddDivAtb.cpp、对应Meta、docstring和完整测试文本。两版CPP完整非注释token相同，两版测试完整AST相同；格式、namespace尾注释和测试许可头差异不作为功能差异。未导入或执行上游、生成代码或设备测试，保持draft；厂商库行为仍按固定配套版本另核。

## 两个重载的输入、输出与动态调用

`npu_fused_add_topk_div`和`.out`均以x建立OptionalDeviceGuard。位置输入只有x、add_num；关键字mapping_num/mapping_table/activation_type默认None，group_num/group_topk/n/k均默认1，is_norm=True、scale=1、enable_expert_mapping=False。`.out`再要求Tensor(a!) y与Tensor(b!) indices并返回两个对应别名；PrivateUse1将这两个schema分别注册到普通/out实现。

本地activation map只有activation_sigmoid→8，None选择该默认键。get_op_mode用value_or、map.find和TORCH_CHECK，非法字符串立即报Unsupported activation_type，不自动忽略或转换其他激活。scale由double转float；映射Optional Tensor、分组整数及布尔值均原样交宏，没有根据enable_expert_mapping在此层生成或删除映射表。

普通入口取a=x.size(0)，按x.options分别申请[a,k]的Float权重y和Int索引indices；out入口直接使用传入对象，没有在本函数分配、调整shape、转换dtype或重新验证用户输出。普通返回make_tuple值，out返回forward_as_tuple引用。不能因为相同schema别名就把输出dtype检查归到本包装。

传入AtbFusedAddTopkDiv的14个实参（不含接口名）依次为：

| 序号 | 固定顺序 |
| --- | --- |
| 1–4 | x、add_num、mapping_num、mapping_table |
| 5–8 | group_num、group_topk、n、k |
| 9–12 | activation_type整数、is_norm、scale_float、enable_expert_mapping |
| 13–14 | y、indices |

动态执行宏的符号查找、转换和缓存复用[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。这里没有实现底层TopK、伪随机映射或归一化Kernel，也没有本地检查下述文档规格；参数顺序相同不等于任意参数组合都有效。

## 固定文档的路由算法与约束

docstring将其定位为DeepSeek MoE的Sigmoid→Add→GroupTopK→Gather→ReduceSum→RealDiv→Muls融合：加偏置后的分数用于组与专家选择，普通模式输出物理专家ID；逻辑模式用mapping_num计数及mapping_table将物理专家映射到逻辑专家，逻辑ID除以/模每卡专家数分别对应Rank和卡内位置。文档说使用伪随机逻辑选副本，这不是本包装或下述Python参考已经证明的随机分布。

文档输入为ND x[a,b]、add_num[b]，支持float16/float32/bf16；映射启用时mapping_num[b]及mapping_table[b,c]为int32，c≤128。输出y[a,k]为float32，indices[a,k]为int32。activation仅activation_sigmoid；n表示组内取n个最大值求和，group_topk选组，k选专家，is_norm控制归一化，scale为归一化后系数。

文档列出的规格为：b为group_num的整数倍、group_topk≤group_num、k≤b、b≥group_num×n、b≤group_num×32，b≥32时group_num=8；最大冗余专家数128。原文对mapping_num单值写0≤值<c，但自身样例用randint(1,c+1)，完整测试也把计数设为映射表宽度；这几处证据不一致，不能替底层选择哪一条才有效。

该固定文档的硬件表列Atlas800I A2推理/Atlas A2训练及Atlas A3训练支持，列Atlas200I/500 A2推理、Atlas推理系列、Atlas训练系列不支持。它是文档声明，不是这次运行验证；不外推所有带A2名称的产品或未列组合。其性能提升表述没有附在本段给出可复现测量环境，不能作为本次实测收益。

## Meta与完整测试能说明什么

Meta实现按x.device新建[a,k]的float32 y与int32 indices，k取调用参数；不计算路由、不验证映射内容、组数或精度。普通Meta与普通CPP的输出形状/dtype一致，不能据此证明底层输出值。

完整test_fused_add_topk_div.py的golden_calc把group_num=8、group_topk=4、n=2、k=8、is_norm=True、scale=1写死，输入及偏置先转CPU float32。Sigmoid结果加偏置后reshape为组，组分数取组内top2之和，用NumPy稳定argsort选4组，其余组置0；再稳定降序选8专家。权重从原始Sigmoid结果gather，归一化后乘scale；helper的非归一化分支仅返回gather，但当前固定常量不走该分支。稳定tie顺序是参考实现行为，不证明厂商Kernel同样实现。

参考映射只要两个表都存在且非空就执行，并没有读取enable_expert_mapping布尔参数作分支；选定物理专家后，以token行号bs % max(1,mapping_num[expert])选映射表列。它是确定性的参考规则，不是docstring所说的伪随机算法。OFFSET/PRIME/MAX_INT32/count_mapping在该参考中虽初始化，却没有参与这个列选择。调用方生成映射的循环里另有MAX_INT32名字，但它不在该测试方法的本地或模块定义；当前mapping_num总等于max_buffer，使写尾部的range为空，不能将该写尾分支当已验证。

四个测试均带“CANN过旧”unittest.skip，并有Ascend910B装饰；普通/out各覆盖a=16、b=256、k=8、float16、映射宽2..10及启用映射，另各有a=2048、b=256、不映射的模型形状。它们写有完整assertRtolEqual和索引assertEqual，但被skip不提供通过结果。

golden_compare将输入视为两个输出对象，第一项检查abs差≤2^-10×max(1,abs参考)，另检查归一差的均值≤2^-14，第二项容许索引差≤1。实际测试却分别把单个y Tensor和单个indices Tensor交给它，使[0]/[1]成为Tensor前两行；不能把这些额外res1/res2断言视为完整输出tuple的正确比较。源文件最后仅以run_tests启动，本次没有执行或移除skip。

## 固定证据

证据范围按原始字节SHA与splitlines坐标固定。两版FusedAddDivAtb.cpp和对应test_fused_add_topk_div.py均完整审阅；Meta只审50–55、模式helper只审Utils.h81–91、docstring只审_atb_api_docs.py475–537，未将这些选段扩大为整文件完成。

- [固定源码 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/FusedAddDivAtb.cpp)（primary）：1–119。
- [固定源码 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_fused_add_topk_div.py)（implementation）：1–219。
- [固定源码 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_meta_registrations.py)（implementation）：50–55。
- [固定源码 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py)（implementation）：475–537。
- [固定源码 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
- [固定源码 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/FusedAddDivAtb.cpp)（implementation）：1–72。
- [固定源码 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_fused_add_topk_div.py)（implementation）：1–211。
- [固定源码 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_meta_registrations.py)（implementation）：50–55。
- [固定源码 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py)（implementation）：475–537。
- [固定源码 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
