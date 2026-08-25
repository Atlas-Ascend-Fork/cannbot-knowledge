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
