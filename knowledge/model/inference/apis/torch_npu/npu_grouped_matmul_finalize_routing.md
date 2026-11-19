---
type: API
title: npu_grouped_matmul_finalize_routing：专家GMM与按路由聚合
description: 区分count/cumsum、scatter-add回填和共享专家，限定固定发布与主线950 MX、BF16 Eager及Meta/GE边界。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_finalize_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_finalize_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_finalize_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulFinalizeRoutingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_finalize_routing.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulFinalizeRoutingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_finalize_routing.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_finalize_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_finalize_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-10T02:08:24Z'
updated_at: '2026-11-10T02:08:24Z'
platforms:
- a2
- a3
- '950'
---

# npu_grouped_matmul_finalize_routing：专家GMM与按路由聚合

## 固定版本与融合语义

接口将各专家的GroupedMatmul与MoeFinalizeRouting融合：GMM结果乘对应logit，再按row_index scatter-add到原token行，同一token可累加多个专家结果；共享专家输出还可乘shared_input_weight后叠加到指定输出区间。它不做SwiGLU或输出INT8动态量化，不能按同系列SwigluQuant接口处理返回值。

固定OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda与发布dedc316708372c9a8bfde4527abd2a94b74840f5，TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013分别核对。发布属于ascend_26_0_pt28来源组合，主线配套未知。发布产品页只有Atlas A2/A3，主线增加Ascend950系列（包含旧称Atlas A5）的PR/DT，不能回推发布950支持。

旧vLLM四算子融合链的256专家DeepSeek V3/R1门控属于其固定参考实现；这里不把该门控当成当前公开API的全局模型白名单。公开接口本身仍有下列产品、布局、量化与路由约束，接口存在也不意味着任意MoE模型能直接替换。

## 参数与路由顺序

必填位置参数依次为x、w、group_list；关键字参数为scale、bias、offset、pertoken_scale、shared_input、logit、row_index、dtype、shared_input_weight、shared_input_offset、output_bs、group_list_type，主线文档另列四个输入/尺度dtype覆盖。两固定Schema及C++还支持tuning_config，原型漏列不代表该参数不存在。返回单个二维浮点Tensor y。

x为专家排序后的[M,K]，w为对应专家权重，group_list为INT64[E]且长度与专家数一致。group_list_type默认1，表示独立行数，其总和不得超过M；=0表示累计边界，按末边界与M核对，不能对累计数组再按独立行数求和。最多1024组，但A2/A3 A8W8另限E<=256。不要沿用SwigluQuant V2默认0的假设。

logit形状[M]并与当前专家排序后的行一一对应；row_index[M]是scatter-add的目标行，不是专家ID，也不是排序置换的逆序号。必须共同核对分组、logit和row_index来自同一次路由及token展开，不能分别重排。索引须落入实际输出行范围，不能仅凭dtype合法认定路由正确。

output_bs默认0时第一维取x的M，不会自动推断原batch=M/topK；要聚合回原token数，应传所需行数并核对row_index。shared_input为BF16[batch/dp,N]，shared_input_weight默认1.0，shared_input_offset默认0，叠加区间不得越过输出第一维；页面给batch<=16384、batch/dp<=2048。共享专家是加到此区间，不按所有路由重复加一遍。

## A2/A3整数路径

A8W8的x/weight为INT8，权重真实NZ存储，文档写五维[E,N1,K1,16,32]，K为16倍、ceilDiv(K,16)=K1，N为32倍且至少256，E为1..256。scale为连续FP32[E,N]，pertoken_scale为FP32[M]。输出只FP32，bias/offset为None；组合表保留shared_input/logit同为None的分支，不把950的必填约束回写该表。

A8W4的x为INT8、权重为INT4/INT32打包，ND逻辑[E,K,N]，K仅2048、N仅7168，scale为INT64[E,1,N]编码尺度，bias为FP32[E,N]、offset为可选三维FP32，pertoken_scale为FP32[M]。不能把编码尺度当作普通整数乘子或把随机bias作为离线量化构造方法。普通接口的bias/offset协议也不能用SwigluQuant V1预留offset规则替代。

发布页大多数参数不支持非连续，M为1..131072；主线增加多处非连续支持，M范围从0起。主线英文仍把shared_input和logit写成不支持非连续，中文则写支持；保留差异，不能只据中文放宽部署。A2/A3的scale连续要求两种语言均保留。

## 950 per-token与MX分别限定

per-token可INT8、E4M3 FP8或HIFLOAT8激活/权重，按组合表配对；scale为FP32/BF16[E,1,N]，pertoken_scale可None或FP32[M]，bias可BF16[E,N]或None，offset不支持。logit与row_index必须提供，logit为FP32；INT8路径row_index可INT32/INT64，FP8/HIFLOAT8路径仅INT64。权重可ND或NZ，不从总类型列表生成任意组合。

MX支持E4M3/E5M2 FP8配对与E2M1 FP4配对。scale的E8M0承载按非转置[E,K/64,N,2]、转置[E,N,K/64,2]，pertoken_scale为必填E8M0[M,K/64,2]，对应dtype覆盖明确填E8M0。页面公式写K/64，但示例存在ceil(K/64)和K<64时整除为0的差异，不在此擅自把所有分支修成一个通用公式。实际合法尺度形状需要按该模式和版本核对。

FP4以8bit承载时一字节两个值，必须匹配实际K/N与dtype覆盖；K为大于2的偶数，非转置权重内轴N也须偶数。默认覆盖None意味着按输入自身dtype解释，文档w_dtype段误写成x，不按输出dtype重解释所有输入。主线PyTorch>=2.8实现也识别原生E2M1；发布只根据显式覆盖判断。

混合MxA8W4指E4M3激活配E2M1权重，权重必须NZ、x不转置、w转置，E<=1024、K和N为32倍；图模式另要求E!=1且K>64。它与整数A8W4的固定K/N和INT64尺度分开，不能混用两条协议。

主线950只明确支持x的M=0、w的N=0两类空维，其余空Tensor不支持。不要把这一条扩成任意空scale/logit/索引合法，发布也不能直接接收该主线扩展。

## FP32与新增BF16输出

主线文档dtype只允许公开值0/2，分别FP32/BF16，1对应FP16但明确不支持。BF16输出仅950 MX、权重NZ且bias=None，row_index必须INT32，logit可FP32/BF16，只支持Eager、不支持图。FP32 MX的row_index为INT64，bias可BF16/None。发布虽列0/1/2的解释，返回值及C++实际都只FP32，不能据枚举说明启用FP16或BF16。

主线C++新增公开数字0/2到Torch FP32/BF16归一化，且把底层dtype_real设0/2；发布只接受Torch Float类型。数字空间、dtype对象与绑定版本需配套，不能把公开2等同于任意Torch枚举2。

两版Meta与GE转换器仍只接受FP32，GE真实IR输出也仅DT_FLOAT。因此新增BF16 Eager能力不构成Meta/torch.compile路径支持；Meta成功更不能证明路由索引或尺度数值合法。两Meta的错误消息还引用未定义per_token_scale_dtype，但本次没有触发或运行该分支。

## 布局与底层版本选择

两C++都要求x恰二维、w恰三维，即使权重是NZ存储也检查逻辑view三维；不能把页面五维物理NZ示意直接当作该包装可接收的五维Tensor。format_cast后核对真实存储及逻辑view，单纯view不做格式转换。主线同时识别FRACTAL_NZ与FRACTAL_NZ_C0_16，发布仅前者。

INT32权重输出N按其末轴乘8；FP4未转置配对按承载尾轴乘2，转置则取原尾轴。C++用stride判断转置，Meta却用x尾轴是否等于w倒数第二轴判断，两种判断在打包、非方形或非连续情况下不必等价；迁移时核对真实输出描述，不能只看变量名N。

主线逐调用计算FP4类型，发布是依赖首次调用参数的static const。混合输入类型调用序列在旧包上需验收，这里只记录静态差异，没有报告已复现故障。

NZ优先调aclnnGroupedMatmulFinalizeRoutingWeightNzV2，缺失时回旧WeightNz；ND优先V3，缺失时回V2。tuning_config在旧分支只警告不支持；旧NZ调用还不转交offset，不能把有参数或成功回退视为语义、调优效果完全相同。底层符号存在也不代替公开产品/类型限定。

## GE转换与样例边界

两GE转换器默认output_bs=0时采用输入M，默认tuning_config规范为[0]，只接受dtype=None或torch.float32。INT32权重在CANN>=8.5用keep_dim Bitcast为INT4，较旧分支扩末轴8再Reshape；FP4配对采用相应解包，主线增加原生FP4识别和混合MxA8W4的E/K检查，发布没有同样的新分支。

主线转换器初始transpose_w=False，graph_pass仅在weight与scale都匹配Bitcast/Transpose模式时折叠并改True；不能仅根据Python转置就断言已融合消除。按实际图检查权重与尺度的共同轴，尤其MX最后的打包轴2不能作为N。

文档所谓“非量化场景”示例仍用INT8和反量化尺度，不据注释扩到普通FP16 GEMM。MXFP4图例K=32并用K//64形成零长尺度，不宜照抄；混合示例中的dynamic=True也不保证任意符号shape都通过E/K检查。所有示例只有调用或打印，不是独立数值与性能验收。

## 测试与验收建议

两版测试均7个方法。主线4个A2方法无条件skip；发布少一个skip，保留一个A8W8 CPU对比，其他3个A2仍skip。新增skip的文案说bias不支持，但该例实际未传bias，不能据此宣布全部bias路径不可用。数值参考的argsort+reshape(topK)只覆盖每token等次数的特定路由，不是任意row_index scatter-add黄金实现。

三个950方法仅调用、不接收结果作断言，不能证明数值或输出shape。参考还存在专家4而group_list仅2项、shared_input/bias的宽度2N与FP8权重N不符等配置差异；FP4承载中N另有打包含义，更不能按文件名视为全部合法覆盖。没有BF16输出、零维、任意路由、训练梯度或性能验证，本次没有执行上游代码。

实际替换需分别验证分组GMM反量化值、logit乘法、重复索引累加、共享专家仅加一次及偏移边界，并与明确的scatter-add参考比较。最后再测完整路由与通信后的模型输出及端到端延迟；不从融合名称或形状通过推断加速。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_finalize_routing.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_finalize_routing.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_finalize_routing.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulFinalizeRoutingKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_finalize_routing.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulFinalizeRoutingKernelNpuOpApi.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_finalize_routing.py)（example）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_finalize_routing.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_finalize_routing.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
