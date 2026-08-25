---
type: Guide
title: 通过TilingData传递属性信息
description: 本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 通过TilingData传递属性信息

本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。
本文以LeakyReluCustom的negative_slope属性为例，介绍如何通过TilingData将属性从Host侧传递至Kernel侧，包括在算子原型中声明属性、在Host侧读取属性并写入TilingData，以及在Kernel侧从TilingData中读取并使用该属性。TilingData的基础定义和写入方法见基本流程。
## 属性传递流程
属性传递流程如下：
只有Kernel运行时需要使用的结果才写入TilingData。如果属性只影响Host侧的切分、Block数量或TilingKey，Host侧完成计算后传递最终运行参数即可，不需要原样传递属性。
## 在算子原型中声明属性
LeakyReluCustom的计算语义为：当x>=0时y=x，当x<0时y=negative_slope*x。Host侧通过GetAttrs()返回本次调用的属性列表。GetAttrPointer(index)通过属性在列表中的位置读取对应的值，index按照原型中Attr的声明顺序从0开始编号。本例只声明了negative_slope一个属性，因此将它的索引定义为0。
negative_slope的取值在不同调用之间可能变化，因此TilingFunc需要读取本次调用的属性值，不能在Tiling实现中将其写成固定常量。
即使属性在原型中定义了默认值，读取后仍建议判空，避免索引、类型或工程版本不匹配时直接解引用无效指针。
### 属性类型对应关系
GetAttrPointer的模板参数需要与原型声明的属性类型一致。
原型属性接口：Host侧读取类型：适合写入TilingData的类型
.Bool(...)：bool：bool或明确宽度的整数
.Float(...)：float：float
.Int(...)：与接口约定一致的整数类型：按Kernel需求检查范围后转换
属性读取类型不匹配会导致数据解析错误。整数属性转换成uint32_t等更窄类型前，需要检查负数和溢出范围。
### 多属性场景
假设原型按以下顺序声明两个属性：
Host侧对应使用索引0和1：
新增、删除或调整属性顺序时，需要同步检查所有GetAttrPointer(index)调用。建议为索引定义具名常量，避免在Tiling函数中散落数字。
## Kernel侧使用属性
Kernel入口解析TilingData后，将属性字段传给Kernel实现类：
Init把negativeSlope保存为Kernel类成员。配套样例使用Maxs、Mins、Muls和Add组合实现LeakyRelu。
计算完成后再按Kernel基本流程把yLocal写回Global Memory。

<!-- cannbot:related:start -->
## 相关

- [Attr（OpDef）](../../../../../apis/utils_api/prototype_register_management/op_def/attr.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“Attr（OpDef）”明确注册算子属性参数。 当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [GET_TILING_DATA](../../../../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“GET_TILING_DATA”明确用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使…。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [GET_TILING_DATA_WITH_STRUCT](../../../../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data_with_struct.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“GET_TILING_DATA_WITH_STRUCT”明确使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [Muls（灵活标量位置）](../../../../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/muls_flexible_scalar.md)（`explains`）：Muls（灵活标量位置） 与《通过TilingData传递属性信息》的实质衔接是：灵活标量 Muls 的 scalarTensorIndex、LocalTensor 单点标量和 cyclic-repeat 语义会直接影响广播乘法、量化 scale 与标量位置。
- [OpAttrDef](../../../../../apis/utils_api/prototype_register_management/op_attr_def/op_attr_def.md)（`explains`）：OpAttrDef 与《通过TilingData传递属性信息》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [TilingData结构定义](../../../../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“TilingData结构定义”明确定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [TilingData结构注册](../../../../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_register.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“TilingData结构注册”明确注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [TilingData 须 host 与 kernel 各定义一份](../../../../../runbooks/compilation/tilingdata_host_kernel.md)（`related`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《通过TilingData传递属性信息》补充：本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`related`）：TilingKey 缓存 correction 致 tilingdata 复用 与《通过TilingData传递属性信息》的实质衔接是：该问题由 GE 按 TilingKey 缓存 correction 造成同 shape 调用复用旧 TilingData；属性传递指南和注册/判定宏共同说明如何让变化属性进入正确 tiling 分派。
- [aclnn TilingData 缓存致 runtime attr 陈旧](../../../../../runbooks/precision/aclnn_tilingdata_runtime_attr.md)（`related`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“aclnn TilingData 缓存致 runtime attr 陈旧”明确aclnn L2 executor 对可 repeat 算子按 (算子, shape, dtype) 缓存整块 TilingData；若算子把每次调用都不同的 runtime scalar attr（如 beta/threshold）写进 TilingData，则同 (op,shape,dtype) 的第二批调用会跳过 t…。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [多分支策略](multi_branch_strategy.md)（`related`）：多分支策略 与《通过TilingData传递属性信息》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [算子功能设计](operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《通过TilingData传递属性信息》说明本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [高级编程基本流程](kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《通过TilingData传递属性信息》说明本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [算子原型定义](operator_prototype_definition.md)（`same_topic`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“算子原型定义”明确本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [高级编程基本流程](host_tiling_implementation.md)（`same_topic`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“高级编程基本流程”明确本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
<!-- cannbot:related:end -->
