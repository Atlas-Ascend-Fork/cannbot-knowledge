---
type: Guide
title: vLLM Ascend融合GMM与SiTU接入：四种入口、分组与静态图门禁
description: 沿GroupedMatmulSituQuant的ND/NZ与TensorList四入口核对MXFP8激活、MXFP4权重、E8M0 scale、K及输出半宽64对齐、group_list编码和Meta与真实tiling差异；说明A5包装的SiTU融合选择、设备路由重放及尚未展开的Device实现边界。 已补入本仓SiTU epilogue、gmsq2与wqbmm程序的缩放/舍入、MX布局、双角色同步及模板支持边界。
aliases:
- GroupedMatmulSituQuant
- aclnnGroupedMatmulSituQuant
- torch.ops._C_ascend.grouped_matmul_situ_quant_weight_nz
- torch.ops._C_ascend.grouped_matmul_situ_quant_weight_nz.list
- A5DeviceAdaptor.npu_grouped_matmul_situ_quant
- Tiling4GroupedMatmulSituQuant
- GMMSQSituVecCompute SituEpilogue
- GmsqEpilogue ComputeVfSitu
- GMMSQWeightQuantVcvBasicBlock dualRoleMode
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.mixture_of_experts
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/grouped_matmul_situ_quant_torch_adpt.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/docs/aclnnGroupedMatmulSituQuant.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_host/grouped_matmul_situ_quant_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_host/grouped_matmul_situ_quant_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_host/grouped_matmul_situ_quant_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/grouped_matmul_situ_quant_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/grouped_matmul_situ_quant.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/gmsq_vcv_controller.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/ops.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_grouped_matmul_situ_quant_weight_nz.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/w4a8_mxfp4.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/situ_epilogue.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/gmsq2/basic_block_config.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/gmsq2/basic_block_vf_mx.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/gmsq2/gmmsq_quant_mx_vf.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/gmsq2/gmmsq_weight_quant_cube_compute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/gmsq2/gmmsq_weight_quant_cube_compute_tools.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/gmsq2/gmmsq_weight_quant_vcv_basic_block.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/gmsq2/gmmsq_weight_quant_vec_compute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/anti_quant_y_vf.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/basic_api/weight_quant_basic_api_v1.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/basic_block_config.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/basic_block_vf_mx.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/basic_block_vf_nd.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/basic_block_vf_nz.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/custom_policy/wqbmm_copy_cube_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/custom_policy/wqbmm_custom_policy.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/grouped_matmul_tiling_data_apt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/grouped_matmul_weight_quant_basic_controller.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/grouped_matmul_weight_quant_resplit_controller.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/mx_a8w4_scale_trans_id_constant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_basic_block.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_basic_block_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_cube_compute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_tool.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_vcv_basic_block.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_vcv_basic_block_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/op_kernel/vendor/wqbmm/weight_quant_vec_compute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/grouped_matmul_situ_quant/utils/torch_kernel_helper.h
  role: implementation
created_at: '2026-11-03T01:51:26Z'
updated_at: '2026-11-03T06:19:43Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend融合GMM与SiTU接入：四种入口、分组与静态图门禁

## 适配任务与证据边界

本卡用于MXFP4 MoE接入时判断GMM1、SiTU与动态MX量化能否走同一次launch，以及定位ND/NZ、TensorList、分组和图重放的接口差异。[MXFP4权重指南](vllm_ascend_mxfp4_weight_reload_contract.md)继续负责参数加载、后处理、MegaMoE活动存储与RL恢复；这里从已经准备好的激活、weight及scale进入C++适配和tiling，不把两个任务合并为完整加载证明。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。选定13份全文为该族README/API、adapter、3份Host实现、tiling结构、kernel入口、controller、ops声明、2份CMake及108行E2E；另有4份共享文件有界读取：torch_binding2845–2885、Meta1649–1715/1773–1777、device_op1352–1420、W4A8_MXFP方法345–397。共享来源保持原canonical owner。

README明确写Ascend950PR/arch35；Host注册和构建使用ascend950，kernel主体受`__NPU_ARCH__ == 3510`保护。A5包装存在、测试以A5枚举筛选，均不扩大README到所有A5型号或950DT。保持draft、空平台及framework=vllm部分Scope，尚无本次硬件验证。

本卡是模型接入的Host与调度接口facet。controller全文已读，但SiTU epilogue、vendored GMM/weight-quant基本块及完整CV同步/数值闭包未展开；不标完整Operator或source_closed，不声称性能收益、CANN跨版本ABI、图生命周期或真实NPU正确性已经验收。全部测试仅静态阅读，未导入或执行上游。

## 四种入口共享计算，不共享准备成本

四个`_C_ascend`入口最终均调用`aclnnGroupedMatmulSituQuant`，不是四套独立数学算子。

| 输入形态 | 入口末段 | adapter实际准备 |
| --- | --- | --- |
| 聚合ND Tensor | `grouped_matmul_situ_quant` | 要求ND format2及contiguous，将weight cast到NZ |
| 每专家ND列表 | `grouped_matmul_situ_quant.list` | 拼接weight和weightScale，再转换weight格式 |
| 聚合NZ Tensor | `grouped_matmul_situ_quant_weight_nz` | 接受format29或50，不统一强制contiguous |
| 每专家NZ列表 | `grouped_matmul_situ_quant_weight_nz.list` | 校对每专家scale元素数，直接传动态TensorList地址表 |

因此ND列表入口的cat和format_cast可能在每次调用发生，不能以“融合一次launch”推导整条调用没有额外准备或峰值分配。模型A5包装实际选择NZ入口；list或tuple选`.list`。它恢复UINT8 scale的E8M0语义，非contiguous聚合weight会transpose(1,2)，scale要求已经是N-major连续Tensor或可经指定转置得到该连续视图，不能任意reshape修复未知布局。

OpDef只声明一个NZ权重变体及IgnoreContiguous，这是ND入口先cast后的下游规格；API表中列ND不意味着底层kernel直接消费任意ND布局。非连续NZ也不等于所有stride都可用，必须核对实际逻辑shape、格式tag与物理存储对应关系。

## 形状、语义dtype与不完整的前置校验

记激活为`x[Mcap,K]`、专家数E、GMM1的gate/up合并宽为N，最终半宽为N/2。FP4打包每字节两个元素，adapter由聚合weight元素数除以`E*(K/2)`恢复N；列表由首专家weight恢复N。调用方必须提供匹配的专家布局，不能把packed物理字节当普通FP4浮点元素数。

| 对象 | 固定接口合同 |
| --- | --- |
| x / xScale | FP8 E4M3 / E8M0；xScale至少容纳`Mcap*(K/32)`个元素 |
| weight / weightScale | FP4 E2M1打包 / E8M0；所需scale元素数为`E*ceil(K/64)*N*2` |
| groupList | NPU int64，一维E项；type0为累计边界，type1为每专家行数 |
| 输出y | FP8 E4M3，`[Mcap,N/2]` |
| 输出yScale | E8M0，`[Mcap,ceil((N/2)/64),2]` |

RunV2Core检查E>0、K为64倍数、N/2为64倍数；真正launch时Host tiling进一步要求K>0、N为正偶数。聚合入口和NZ列表检查weightScale numel，ND列表却直接拼接scale后交核心，没有同样的逐专家scale数目校验。x与scale、weight是否为NPU以及scale numel还有若干独立检查，但adapter并未统一穷尽全部rank、dtype、列表和shape组合；部分入口在最终校验前就访问`x.sizes()[1]`或`weight[0]`。Agent应先检查二维激活、非空列表、各专家一致性和存储语义，不能把底层错误处理当作安全的任意输入探测器。

非空bias和smoothScale被拒；None、undefined或numel0视为空。非空weightAssistMatrix只发一次警告后忽略，tuningConfig也不参与计算。dequantMode必须1、dequantDtype必须0、quantMode必须1；这些枚举不是任意量化模式的开放入口。Mcap=0在核心元数据检查之后返回空形状输出，不代表空专家列表可绕过前面的首元素访问。

## Python融合选择比Meta推形更严格

`AscendW4A8MXFPDynamicFusedMoEMethod.apply_gmm1_act_quant`只在activation为SITU、group_list_type属于0/1、group_size=32且linear_beta>0时选择此融合。beta未指定时取1，linear_beta缺省按0处理。A5 adaptor还显式要求W4A8MXFP量化类型。其他组合走原有GMM后接SiTU量化分支，不能只看模型含SiTU便假定融合发生。

Host tiling仅检查beta和linearBeta非零，没有完整的正值/finite预检；源码这层与Python的正linear_beta选择不是同一合同，不能据“非零即可过此分支”宣称负值或NaN数值受支持。

Meta只计算输出形状/dtype，忽略groupList实际内容、bias、scale、模式和beta；Host InferShape也只要求K为正偶数，而真实tiling要求64对齐。因此Meta或编译推形成功不证明运行入口合法，更不证明scale布局、路由行数及执行正确。诊断时分别保存Meta输入、C++ adapter输入及tiling日志，不用其中一层的成功覆盖下一层失败。

## 固定网格读取设备分组，容量不等于有效行

Host header的activeCount在当前设备分组入口承载E，不是已剪枝的活跃专家数。Host取AIC核数作为静态blockDim，baseM=128；N/2可被128整除时选半宽128，否则选64，均保留合法64对齐范围。reserved低位记录type0/1，另一位记录TensorList；64字节header通过growable RawTiling.Append写入，不能照搬固定8字节初始容量的直接写法。

kernel以MIX_AIC_1_2进入controller.InitDev：分组仍是设备Tensor。每个核读取groupList，type0作相邻差、type1直接读计数，零行专家跳过，依次累加rowBase并设置输入/输出偏移。因此同shape图重放可读到更新的设备路由；“静态网格”不表示捕获时把专家行数固定成Host常量，也不额外证明图捕获、存储地址或跨stream更新生命周期已经成立。

当前所读Host没有把设备groupList复制回CPU并验证其非负、单调或总行数；controller把计数转成uint64后计算偏移。调用方须保证type0单调、type1非负且有效总行数不超过Mcap，并只消费有效前缀。输出按capacity分配，不应假设未写尾部是零或有效token。

controller还根据最大专家L1行块与relay容量统一选择双角色模式：行块至少34且`maxL1M*(mainBlockSize*2)<=16384`时进入该模式。宽N块在M块大于64时拆分子块；这些是当前调度/容量分支，源码注释中的实验收益不转写为本卡性能结论。改shape、分布或tiling后应重验边界，而不是只按总token数推断相同路径。

Host workspace字段仅设库API workspace大小；这不是整条ND转换、TensorList拼接、输出、Device基本块和框架缓存的总显存上界。完整Device同步、epilogue暂存和数值范围仍为后续Operator专项边界。

## 已有测试说明什么，Agent还需验证什么

108行E2E定义14/15专家、type0/1、Mcap17280但有效128行、K3584/N6144；先比拆分GMM+SiTU参考，再在同一图中更改均衡、零专家、集中路由并replay，只对有效128行按uint8位模式比较。测试存在及A5 skip条件不等于本次已经执行，也没有覆盖所有四入口、非法计数、空列表、所有形状或真实模型权重。

适配先核对[权重准备](vllm_ascend_mxfp4_weight_reload_contract.md)、实际adaptor/入口、FP4/E8M0语义、K/N与分组容量，再对同一输入分别比较非融合参考及融合输出/scale。图测试需要固定storage地址并覆盖路由变化和零专家；前后检查有效前缀及尾部消费。最后才测cat/cast准备、单launch、分配峰值与端到端性能，记录实际950PR、TorchNPU/CANN/框架版本及并行组合。

共享MLP在融合成功返回后dispose原hidden_states存储；这不等待所有潜在alias或异步消费者完成。模型适配不能因融合结果可用就提前复用原输入，更不能用Host层通过代替Device数值与生命周期验收。


## Device 与 vendor 程序补充：从 MX Cube 到 SiTU FP8 输出

本节补入同一固定提交的29份本地实现：`situ_epilogue.h`、gmsq2七份、wqbmm二十份及Torch launch helper。全部非注释程序行已按原行号投影读取；不是原文件逐字全文或SDK内建的展开。前文“尚未展开Device”是本节之前的生产边界：本节现在补齐这些**本仓程序的执行facet**，仍不表示完整Operator、外部AscendC库ABI、实机同步/精度/性能或所有模板实例已验收。

### 真实 SiTU 与中间舍入

`situ_epilogue.h::ComputeVfSitu` 用 FP32 计算 `beta*tanh(gate/beta)*sigmoid(gate)`，再乘 up；启用 hasLinearBeta 时 up 先变成 `linearBeta*tanh(up/linearBeta)`。tanh 在绝对值<0.6使用四级奇多项式，其他位置用exp等价式，不是普通 SwiGLU、clip 或直接调用框架 tanh。gate/up 输入及 SiTU 输出按 BF16 中间值保留，cast 为 RINT。主段64列与tail mask/padding分开，修改边界应同时验证两段。

gmsq2 的 `GMMSQSituVecCompute::SituEpilogue` 从 Cube FP32 relay 读取gate/up，先乘64恢复缩放并 RINT 到BF16，再进入上述 SiTU，最后从 BF16 结果按32元素组取最大指数、生成 E8M0 scale、量化 E4M3FN。输出 FP8 在数值cast前明确夹到[-448,448]；exponent特殊值、零、NaN、自定义0x7f81、共享指数特殊边界由位操作处理，不能换成未经比较的通用amax/448算法。每行scale按最终半宽N/2编址，而不是合并gate/up宽N。

gmsq2 仍包含名为 `GmmSwigluVf` 的旧辅助函数，它先将两输入乘64再做swish×gate；**当前 SiTU epilogue 调用的是 ComputeVfSitu**，不能凭vendor函数名认定融合选错activation。FP4展开的 paired Load→shift/and(0x9c)→interleave→双store 与Stock逐片版本布局相关，不能把“字节相等”检查换成普通int4有符号解码。

### 双角色与合作模式的同步

`gmmsq_weight_quant_vcv_basic_block.h` 区分 dualRoleMode：subblock0承担weight展开，subblock1处理上一块epilogue；合作模式两vector按K半块搬weight、按M半行处理epilogue。Cube先把上一块Fixpipe到relay，再发本块matmul；End必须冲刷最后一块并收回初始flag。双角色的等待只消费对应+16槽，合作模式等待两vector，不能统一删成一个flag。

VCV的relay与展开weight复用UB区域，按MTE3→FIX→V、V→MTE2等不同生产消费边建立顺序；不能因为跨核flag存在就删除本核的epilogue MTE3_V drain。该drain单独用event4并静态断言<6，防止下一row chunk重用out/scale buffer时写回未完成。合作模式还有 `IssueNextSliceCopy/ConsumePreIssuedSlice` 提前发起后再等待的状态；空slice也保留配对wait/set节奏，不能直接跳整个同步链。

rowChunk按64×64暂存预算缩小，nHalf>64时为4096/nHalf；当前Host只选择nHalf64/128，relay容量与模式门禁也限制M。若推广任意tiling，须重新证明rowChunk非零、64列cast循环覆盖、M拆分与输出offset，没有通用尾处理保证可直接扩到任意nHalf。

### MX Cube 的 layout、scale 和 K 尾

gmsq2配置为A不转置、B转置、MX A/W、NZ权重。Cube使用双32KiB L0A/B与FP32 L0C，K L0 tile在小M/N时256，否则128；M向2对齐、K向64对齐，firstK初始化，lastK启用结束unit flag。A与weight scale每4096 K分段装载、32值一组，并分别为gate/up半宽生成scale地址。非64对齐的真实K尾需要L1清零与相关MTE1/MTE2序列；“Host已要求K64对齐”与泛用helper的尾代码是不同层的证据。

L0C按连续tile累积并环绕，Fixpipe写UB时single-core与dual-dst split-M使用不同属性。不能把这个 NoQuant 的FP32 relay Fixpipe与 wqbmm basic API 的最终输出Fixpipe混用；后者对MX结果包含 deqScalar=64 的FP32→BF16/FP16转换。

### 通用 wqbmm 基本块提供什么

本地vendor还提供ND/NZ、KN/NK、per-tensor/channel/group/MX等通用weight-quant模板。`weight_quant_tiling_key.h` 的枚举/声明多于实际 `ASCENDC_TPL_SEL` 组合，头文件存在不能扩展当前SiTU入口的支持矩阵。配置中 wqbmm 的 MXA8W4 为quantType NONE，gmsq2 的同名配置为quantType MX，不能仅按符号名复用模板。

basic controller按group_list差分/直接count处理分组并分配M/N块，零M/N跳过；resplit controller按main/两级tail N块进行跨专家连续排程，双参数槽仅在派生VCV marker时交替。marker基类本身没有计算，作用是模板调度类型判断。group计数转uint64、表长度和总M仍依赖Host/caller，通用controller不额外校验坏路由。

resplit对MX A8W4按M/N选择K512/256，并在80KiB A保留预算内限制kaDepth；非MX的A预取另有M<=512、大小和cubeNumBlocksN整除条件。MX分支明确跳过该预取，不能把通用prefetch优化当当前SiTU已启用。L2 cache hint也只是policy，不是数据已驻留或实测收益。

`basic_block_config.h` 按dtype/format选择不同UB预算，ND反量化缓冲带65 stride，NZ常四缓冲、ND常双缓冲；buffer字段有元素单位和字节单位，不能直接相加为显存预算。weight_quant_tool 的int4/FP4 copy将长度/stride折半，GetKBUnit对packed类型为2048；大地址、对齐与向量mask须按语义元素和物理字节分别核对。

ND路径的反量化为 `(cast(weight)+offset)*scale`；per-tensor取标量，per-channel广播N，per-group随K group，MX E8M0先解到BF16/FP16，FP16目标可能经BF16中转。S8S4 VCV先重建int8、Cube累加int32，再乘per-channel和per-token scale、加bias、转换输出；不是SiTU的FP32 relay路径。NZ MX FP4在K尾按16/32对齐差异选择不同UB→L1 copy；MX A8W4 scale还有128项固定gather表和bank-conflict padding，不能删成普通transpose。

custom CopyCubeOut把UB的M高度补为偶数，ND_ALIGN按寄存器宽补stride，用dual-dst split-M；它支持ND/ND_ALIGN且对其他format断言，未提供任意格式输出。事件资源按实际分配和执行次数End等待后释放，KT_TEST下禁用的cross-core/writes也说明mock不能验证真实同步。

### Torch launch 和 Agent 验收

`utils/torch_kernel_helper.h` 将Host tensor先pin再复制到当前PrivateUse1设备，EXEC_KERNEL_CMD捕获当前NPU stream及转换后的参数，通过RunOpApi发起ACLRT launch，lambda返回0。这个返回值不是设备完成或异步错误已检查的证明，也不能据pin推导任意临时源/目标寿命都已延长。

先按四入口核对format、分组、tiling与实际选中实例，再逐段比较FP4展开、MX matmul、×64 BF16中间、SiTU、最大指数、scale和FP8位模式。覆盖小/大M模式切换、末专家零token、集中路由、64/128半宽、跨4096K scale边界、最后relay flush、row chunk复用及图重放更改device group_list。保持FP32→BF16→FP32的真实舍入参考，数学等价不代替位级一致性。还需在匹配950PR/CANN/TorchNPU环境进行数值、memcheck、图和性能验收；本次只完成知识生产。
