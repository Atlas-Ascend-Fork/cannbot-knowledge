---
type: Guide
title: 使用高阶API时配套的Tiling实现
description: 本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 使用高阶API时配套的Tiling实现

本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。
本文构造一个简化的aclnn工程化算子MatmulCustom作为示例。该算子只计算C = A * B，用于说明MultiCoreMatmulTiling和TCubeTiling在算子工程中的接入流程，不包含Bias、激活函数或多分支逻辑。
## 高阶API Tiling的数据流
配套流程如下：
配套Tiling类负责计算高阶API内部使用的多核切分和核内切分参数，算子TilingData负责把计算结果传到Kernel侧。
## 定义包含TCubeTiling的TilingData
高阶API的Tiling结构体可以通过标准C++方式或宏定义方式组织。本例为了展示TILING_DATA_FIELD_DEF_STRUCT的使用方法，选择宏定义方式嵌套TCubeTiling：
TILING_DATA_FIELD_DEF_STRUCT只能嵌套由同类宏定义的Tiling结构体，因此选择该宏时，外层MatmulCustomTilingData也需要使用宏定义方式。使用标准C++方式时，可以在普通结构体中直接声明AscendC::tiling::TCubeTiling字段，不使用上述宏。
宏定义方式会生成SaveToBuffer()和GetDataSize()等接口，Host侧计算完成后需要显式序列化TilingData。
## 在TilingFunc中调用配套Tiling类
本例固定A为[512, 128]、B为[128, 512]，输出C为[512, 512]。A、B使用float16，C使用float，矩阵均为ND格式。
示例使用固定shape以突出配套Tiling类的接口。支持动态shape时，应从TilingContext读取M、N、K，并在调用GetTiling前校验rank、K维相等关系以及整数转换范围。
### 设置workspace
Matmul高阶API可能需要系统workspace。Host侧通过GetLibApiWorkSpaceSize()获取系统workspace大小，并与算子自定义workspace相加：
即使算子没有自定义临时数据，也需要检查高阶API是否使用系统workspace，不能直接把workspace设为0。
系统workspace和用户workspace的通用设置方法请参考如何使用workspace。
### 校验输入条件
实际算子还需要在调用GetTiling前校验：
- A、B是否为二维矩阵。
- A的K维与B的K维是否相等。
- 输入dtype和format是否与SetAType、SetBType配置一致。
- 输出shape、dtype和format是否与SetCType配置一致。
- M、N、K转换到int32_t前是否超出范围。
校验失败时返回ge::GRAPH_FAILED，不要继续使用无效shape计算Tiling。

<!-- cannbot:related:start -->
## 相关

- [GetLibApiWorkSpaceSize](../../../../../apis/utils_api/platform_info/platform_ascend_c/get_lib_api_work_space_size.md)（`explains`）：指南明确即使算子没有自定义临时数据，也要用 GetLibApiWorkSpaceSize 查询高阶 API 的系统 workspace 后再设置 Context。
- [GetTiling](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/get_tiling.md)（`explains`）：指南在 Host TilingFunc 配置完 Matmul 形状与类型后调用 GetTiling，并以返回 -1 判失败；目标接口给出这一收口调用与返回契约。
- [Matmul Tiling类](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/matmul_tiling.md)（`explains`）：指南使用的 MultiCoreMatmulTiling/TCubeTiling 流程属于 Matmul Host Tiling 类；目标总览把 SetA/B/CType、形状设置、切分控制和 GetTiling 串成同一接口对象。
- [SetAType](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_a_type.md)（`explains`）：SetAType 与《使用高阶API时配套的Tiling实现》的实质衔接是：SetB/SetA 类型、MatmulTiling 构造与 kernel 的 SetTensorA 共同约束矩阵位置、格式、dtype、转置在 host/kernel 两侧一致。
- [SetBType](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_b_type.md)（`explains`）：示例用 SetBType 将右矩阵 B 的位置、格式和 dtype 写入 Matmul Tiling 对象，K 维与格式校验依赖这份配置。
- [SetCType](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_c_type.md)（`explains`）：示例用 SetCType 声明输出矩阵的存储位置、格式和 dtype，使 Host 计算出的 TCubeTiling 与 Kernel 侧 C 类型保持一致。
- [TCubeTiling结构体](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/t_cube_tiling_struct.md)（`explains`）：指南把 TCubeTiling 嵌入算子 TilingData 并传到 Kernel 初始化 Matmul；结构体卡定义这份切块、搬运和计算参数载体。
- [低 rank 零填充致 count=0 用 td_->rank 非 RANK](../../../../../runbooks/precision/rank_count_0_td_rank_rank.md)（`related`）：低 rank 零填充致 count=0 用 td_->rank 非 RANK 与《使用高阶API时配套的Tiling实现》的实质衔接是：实际 rank 必须来自 tiling 而非模板容量；低 rank padding、NDDMA维度、shape/axes 和 blockDim 卡共同验证零填充维被误纳入循环后 count=0 的机制。
- [含有Matmul高阶API的算子精度问题](../../../appendix/faq/matmul_advanced_api_precision.md)（`related`）：《使用高阶API时配套的Tiling实现》给出“本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。”；该约束/探针可直接复现、解释或前置验证《含有Matmul高阶API的算子精度问题》中的“本节针对含有Matmul高阶API的算子，为排查算子精度问题是否为算子中Matmul高阶API调用方式导致，提供初步的问题定界和定位指导。如未特殊说明，下面均以Atlas A2 训练系列产品/Atlas A2 推理系列产品上的案例为例。”。
- [算子功能设计](operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《使用高阶API时配套的Tiling实现》说明本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [高级编程基本流程](host_tiling_implementation.md)（`related`）：Host Tiling 基本流程定义从 shape、平台资源到 TilingData/workspace/numBlocks 的通用输出，本卡在其上接入 MultiCoreMatmulTiling 与 TCubeTiling。
- [高级编程基本流程](kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《使用高阶API时配套的Tiling实现》说明本文属于扩展内容，介绍使用高阶API时配套的Host侧Tiling实现。Matmul、Conv等高阶API通常提供配套的Host侧Tiling类，用于根据shape、dtype计算切分参数。开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
<!-- cannbot:related:end -->
