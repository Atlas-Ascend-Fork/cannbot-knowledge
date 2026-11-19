---
type: Guide
title: TorchNPU原生分组GEMM的V5选择与布局成本
description: 说明原生_grouped_mm的四种布局、V5探测先后、编译期fallback、offset转换与有界测试。
tags:
- task.optimization
- topic.compute.composite
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMMKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_grouped_mm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T07:42:59Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU原生分组GEMM的V5选择与布局成本

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整GroupedMM包装和有界测试函数。Schema为 `_grouped_mm(self,mat2,offs=None,bias=None,out_dtype=None)` 登记op_api `[v2.9,newest]`；测试仅按hasattr(torch,"_grouped_mm")跳过，注释所写 2.8 不能替代来源 Schema。固定发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的同名CPP/测试路径及Schema符号缺失，只记录精确来源差异。

## 输入与输出条件

两个矩阵均只接FP16/BF16/FP32、dtype相同、各为2维或3维，并要求A最后一轴等于B倒数第二轴。只要任一输入为2维就必须提供offs；两者都是3维时禁止offs。offs须为1维INT32，bias必须None，out_dtype缺省A dtype且指定时也必须等于A dtype。这里没有完整的设备一致性、offset单调性/终值、组数与3维轴匹配检查，底层仍可能拒绝输入，不能把漏检解释成支持任意组合。

| 输入 | 输出与V5打包 |
| --- | --- |
| A(M,K)、B(G,K,N) | 输出(M,N)，按M划分；split_item=3、group_type=0，A/B各contiguous。 |
| A(G,M,K)、B(K,N) | 输出(M,N)，按N划分；先将B和A分别转置并contiguous，交换成V5的x/weight，分配(N,M)，算后transpose再contiguous成(M,N)。 |
| A(M,K)、B(K,N) | 输出(G,M,N)，G取offs长度，按K划分；split_item=2、group_type=2，A使用t().contiguous().t()形成所需转置步长，B contiguous。 |
| A(G,M,K)、B(G,K,N) | V5可用分支中调用at::bmm；没有在这个包装内按G循环V5。 |

offs表示累计边界而非每组长度，V5前转INT64并保证连续。原生累计边界与其他自定义GroupedMatmul的group_list_type等模式须分别对齐，不能只按参数名共用。

## 探测先于bmm，fallback不是失败重试

入口以static缓存 `check_aclnn_kernel_available("aclnnGroupedMatmulV5")`。探测发生在3D×3D的bmm分支之前，因此不能声称3D×3D完全绕开V5可用性判断。

若缺V5，则仅在编译时 `__has_include("ATen/native/GroupedMMUtils.h")` 成立时分配上述对应shape，并委托外部 `at::native::_grouped_mm_fallback`；否则直接报错，错误信息建议更新CANN或PyTorch≥2.9。实际编译开关依据头文件存在性，不是本地运行时解析版本号。fallback本体未在本组阅读，不能由注释推定所有执行成本、设备或正确性；也没有捕获V5执行错误再重试fallback的流程。

V5 helper还有独立static可用性检查作为防御。其group_list_type固定累计值0、act_type固定0、tuning_config为空；bias、量化scale/offset、antiquant、per_token_scale、activation输入及其量化参数均为空TensorList，act_out/dynamic_quant_scale_out同样为空，result只有本地分配的目标。原生_grouped_mm不能据自定义GMM的完整能力被宣传为已启用量化、激活或额外输出融合。

输入/offset类型转换、两次转置之间的contiguous和结果连续化都可能产生额外开销。是否优于逐组计算、何种形状命中实际Kernel，应按最终安装包与工作负载测量；本卡没有性能结果。

## 有界测试实际证明什么

本卡读取测试1–55的四种CPU参考和累计边界生成，以及四个FP16梯度方法、输出shape方法和五个负例方法；重复的其他前向方法没有据此提升成整测试文件完成。CPU参考分别沿M、N、K切块并cat，3D×3D直接bmm。累计边界由均分步长生成，并把最后值改为总长度。

四个梯度方法以小正态输入执行sum().backward()，与独立detach/clone的CPU参考比较前向和两个输入梯度，容差0.001；这只是所读拟测流程，未执行设备或autograd。shape方法列四种组合；负例只检查dtype不匹配、rank1、2维缺offs、3D×3D多offs、非None bias。没有据此认证非法offset内容、缺V5/无头文件构建、Kernel失败重试、FP32精度、量化、所有产品或图编译支持。

## Evidence

- [GroupedMMKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMMKernelNpuOpApi.cpp)（primary）：1–233；完整本地文件。
- [test_grouped_mm.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_grouped_mm.py)（example）：1–55、98–121、163–184、226–247、286–306、312–345、351–389；仅所列Schema或关键完整函数。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2337–2339；仅所列Schema或关键完整函数。
