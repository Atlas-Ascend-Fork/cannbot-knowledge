---
type: Guide
title: 高级编程基本流程
description: 本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global
  Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/kernel_operator_implementation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 基本流程

本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。
## Kernel函数格式
### 命名规则
Kernel入口函数名需要和算子类型对应。算子类型采用大驼峰命名，Kernel入口函数采用小写下划线命名，框架在编译和运行时根据命名规则完成匹配。
算子类型：Kernel入口函数名
AddCustom：add_custom
MatmulCustom：matmul_custom
ReduceMaxCustom：reduce_max_custom
Conv2DCustom：conv2_d_custom
GatherV2Custom：gather_v2_custom
完整转换规则和更多示例会在命名转换规则对照表中展开。
### 函数形式
Kernel入口函数可以使用非模板入口或模板化入口。
非模板入口使用extern "C"指定C语言链接规则，msOpGen生成的基础模板通常采用这种形式。
模板化入口通过模板参数承载dtype、Tile数量和分支选择信息。下面示例对应的算子类型是AddCustomTemplate，因此Kernel入口名为add_custom_template。在aclnn工程化算子开发方式中，需要先声明模板参数及其可用组合，再由Host侧Tiling通过ASCENDC_TPL_SEL_PARAM选择组合，编译工具根据配置实例化对应的Kernel。
上述代码使用REGISTER_TILING_DEFAULT注册默认TilingData结构体，并通过GET_TILING_DATA_WITH_STRUCT按指定类型解析Tiling数据。模板参数声明、Host侧选择和编译配置请参考多分支策略的Tiling模板编程章节。
### 参数顺序
Kernel入口函数参数需要按照“输入、输出、workspace、tiling”的顺序排列。框架调用Kernel时，会先按照算子原型定义中的输入输出顺序传入Tensor地址，再追加workspace和tiling两个参数。
参数含义如下：
x、y：算子原型中的输入：指向输入Tensor的Global Memory地址
z：算子原型中的输出：指向输出Tensor的Global Memory地址
workspace：框架追加：指向workspace内存地址
tiling：框架追加：指向Host侧Tiling写入的数据
> 说明：输入输出同名场景
>
> 如果算子原型中的输入和输出同名，msOpGen生成Kernel入口参数时会给输出参数增加ref后缀，用于区分输入和输出地址。
>
>
Kernel实现类的内部组织方式由算子计算逻辑和Ascend C编程模式决定。

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](tiling_with_advanced_api.md)（`related`）：配套Tiling类负责计算高阶API内部使用的多核切分和核内切分参数，算子TilingData负责把计算结果传到Kernel侧。；Kernel入口函数参数需要按照“输入、输出、workspace、tiling”的顺序排列。框架调用Kernel时，会先按照算子原型定义中的输入输出顺序传入Tensor地址，再追加workspace和tiling两个参数。前者生产 TilingData，后者规定 Kernel 入口如何接收其地址，闭合 Host 到 Device 的 ABI 交接。
- [高级编程基本流程](host_tiling_implementation.md)（`related`）：TilingData：Kernel执行时需要读取的参数，例如总元素数、单次处理的数据量、循环次数、尾块长度和分支参数。；tiling：框架追加：指向Host侧Tiling写入的数据。Host 生产的 TilingData 由 Kernel 入口最后一个参数直接消费。
<!-- cannbot:related:end -->
