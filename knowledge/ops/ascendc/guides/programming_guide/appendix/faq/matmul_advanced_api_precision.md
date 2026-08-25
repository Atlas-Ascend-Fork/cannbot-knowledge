---
type: Guide
title: 含有Matmul高阶API的算子精度问题
description: 本节针对含有Matmul高阶API的算子，为排查算子精度问题是否为算子中Matmul高阶API调用方式导致，提供初步的问题定界和定位指导。如未特殊说明，下面均以Atlas
  A2 训练系列产品/Atlas A2 推理系列产品上的案例为例。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/faq/matmul_advanced_api_precision.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 含有Matmul高阶API的算子精度问题

本节针对含有Matmul高阶API的算子，为排查算子精度问题是否为算子中Matmul高阶API调用方式导致，提供初步的问题定界和定位指导。如未特殊说明，下面均以Atlas A2 训练系列产品/Atlas A2 推理系列产品上的案例为例。
具体排查过程主要有如下六个步骤：
1.  CPU域调试，观察报错信息；
2.  Matmul Tiling是否有修改，修改是否合理；
3.  算子隐藏Vector计算，仅调用Matmul API，算子功能是否正确；
4.  单核执行，算子功能是否正确；
5.  排查Matmul API的使用是否正确；
6.  用于算子调测的golden脚本是否正确。
详细说明如下：
1.  CPU域调试，观察报错信息
在完成算子代码的开发后，优先通过Kernel直调中的CPU调测工程，调试算子的功能。在CPU域调试时，若编译或执行报错，日志中一般会有明显的报错信息。根据报错信息的提示内容，通常可以快速定位到问题所对应的代码位置。这种方法尤其对DataCopy参数设置错误导致的地址越界、算子Tiling参数设置不正确、其他内存越界访问等基础参数的使用问题，可以快速定位到具体原因。
1.  案例：
以下为matmul算子核函数的代码片段。该段代码实现了根据Global Memory上的A、B矩阵和Tiling信息，计算每个核要使用数据的地址偏移、创建Matmul对象，计算得到Matmul结果。
以下为上述代码在CPU域调试时输出的执行结果。以下示例中的路径请以实际情况为准。
本案例中的算子有精度问题，于是使用CPU调测该算子功能，CPU运行后，根据报错信息提示的矩阵B的transpose未定义，查看矩阵B的相关设置代码，发现Matmul对象定义时未设置矩阵B的B_TYPE::isTrans，而SetTensorB接口设置了isTransB = true，导致执行报错。所以，此问题的根因为SetTensorB设置的isTransB值与B_TYPE不符。
2.  Matmul Tiling是否有修改，修改是否合理
一般含有Matmul的算子Tiling实现中，通过调用GetTiling接口获取Matmul Tiling，其数据类型为TCubeTiling结构体，这时这组Tiling值是合法的。某些情况下，用户自定义了一组TCubeTiling参数值，或者，基于GetTiling接口返回的TCubeTiling，自行修改了其中的部分值，这样的修改需要满足参数间的制约条件。
为获取所有Tiling参数值，需要打印Tiling参数相关的日志。设置日志环境变量，获取MatmulTiling参数值。设置环境变量的命令如下：
在日志中搜索“MatmulTiling”关键字，参照TCubeTiling约束条件，检查Tiling取值是否合法。若不满足某条约束条件，需要修改对应的相关参数，使该组TCubeTiling参数值均合法。

<!-- cannbot:related:start -->
## 相关

- [GetMatmulApiTiling](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_matmul_api_tiling.md)（`explains`）：GetMatmulApiTiling 与《含有Matmul高阶API的算子精度问题》的实质衔接是：host 侧 GetMatmulApiTiling 把模板参数、MatmulConfig 与基础配置落成 tiling，随后决定 kernel Matmul 的注册、临时空间和精度/性能策略。
- [Batch Matmul基础功能](../../../operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md)（`related`）：Batch Matmul基础功能 与《含有Matmul高阶API的算子精度问题》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [使用高阶API时配套的Tiling实现](../../advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`related`）：《使用高阶API时配套的Tiling实现》给出“本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。”；该约束/探针可直接复现、解释或前置验证《含有Matmul高阶API的算子精度问题》中的“本节针对含有Matmul高阶API的算子，为排查算子精度问题是否为算子中Matmul高阶API调用方式导致，提供初步的问题定界和定位指导。如未特殊说明，下面均以Atlas A2 训练系列产品/Atlas A2 推理系列产品上的案例为例。”。
- [矩阵乘输出的量化/反量化](../../../operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_quant_dequant.md)（`related`）：该 FAQ 给出 Matmul 高阶 API 精度问题的调用方式定界，可验证量化/反量化模式和参数是否按契约配置。
- [稀疏反卷积精度误差源隔离配方](../../../../runbooks/precision/cube_simt_fp32_precision_error_source_isolation.md)（`related`）：配方的 Cube 分支需要先排除 Matmul 高阶 API 的输入格式、tiling 和累加精度问题；该 FAQ 给出对应验证顺序。
- [单次矩阵乘局部输出](../../../operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/single_matmul_local_output.md)（`same_topic`）：单次矩阵乘局部输出 与《含有Matmul高阶API的算子精度问题》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [矩阵乘输出的N方向对齐](../../../operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_n_alignment.md)（`same_topic`）：矩阵乘输出的N方向对齐 与《含有Matmul高阶API的算子精度问题》的实质衔接是：N 方向非对齐输出依赖 ND_ALIGN 布局和 GetTensorC 搬出；局部输出、Matmul 特性、多核对齐/非对齐切分与精度 FAQ直接约束输出形状和尾块。
<!-- cannbot:related:end -->
